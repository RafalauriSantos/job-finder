"""Loopback-only receiver used by the browser extension.

Run manually with: python tools/linkedin_ingest_server.py
It records captures as manual cases so the existing WorkHunter pipeline handles
deduplication, LLM scoring, fallback and Telegram delivery.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.linkedin_ingest import CapturedOpportunity, extract_post_body, looks_like_opportunity
from storage.sqlite_store import SQLiteStore

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/linkedin/captures":
            self.send_error(404)
            return
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 200_000)
            data = json.loads(self.rfile.read(length))
            capture = CapturedOpportunity(
                url=data.get("url", ""), text=data.get("text", ""),
                author=data.get("author", ""), source_type=data.get("source_type", "post"))
            body = (extract_post_body(capture.text) if capture.text.lstrip().startswith('Publicação no feed')
                    else capture.text)
            if not body or not looks_like_opportunity(body):
                self._reply(202, {"accepted": False, "reason": "not_an_opportunity_signal"})
                return
            capture = CapturedOpportunity(url=capture.url, text=body,
                                          author=capture.author, source_type=capture.source_type)
            store_path = os.environ.get("JOB_FINDER_DB", str(Path.home() / ".job-finder" / "state.db"))
            store = SQLiteStore(store_path)
            with store.connect() as db:
                existing = db.execute('''SELECT q.id FROM manual_analysis_queue q
                    JOIN manual_cases c ON c.id=q.manual_case_id
                    WHERE c.source='linkedin' AND c.native_id=?
                    ORDER BY q.id DESC LIMIT 1''', (capture.fingerprint,)).fetchone()
            if existing:
                self._reply(200, {"accepted": True, "duplicate": True,
                                  "queue_id": existing[0], "fingerprint": capture.fingerprint})
                return
            queue_id = store.record_manual_case(
                capture.url or "https://www.linkedin.com/", source="linkedin",
                native_id=capture.fingerprint, raw_text=capture.text, author=capture.author)
            self._reply(202, {"accepted": True, "queue_id": queue_id, "fingerprint": capture.fingerprint})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._reply(400, {"accepted": False, "error": type(exc).__name__})

    def _reply(self, status, body):
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self._reply(204, {})

    def log_message(self, *_):
        return


if __name__ == "__main__":
    print("LinkedIn capture receiver listening on 127.0.0.1:8765")
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
