import json
import os
from typing import Dict, Any, List


class StateStore:
    """
    Persistência do estado do monitor (fingerprints vistas, datas e heartbeat).
    """
    def __init__(self, filepath: str = "seen_jobs.json"):
        self.filepath = filepath
        self.state: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        default_state = {"seen_ids": [], "seen_fingerprints": [], "last_heartbeat": ""}
        if not os.path.exists(self.filepath):
            return default_state
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    result = {"seen_ids": data, "seen_fingerprints": [], "last_heartbeat": ""}
                elif isinstance(data, dict):
                    result = {
                        "seen_ids": data.get("seen_ids", []),
                        "seen_fingerprints": data.get("seen_fingerprints", []),
                        "last_heartbeat": data.get("last_heartbeat", ""),
                    }
                else:
                    return default_state

                # Normaliza IDs para string (corrige inconsistência int/str de versões anteriores)
                result["seen_ids"] = [str(x) for x in result.get("seen_ids", [])]
                # Remove duplicatas causadas pela normalização (ex: 12184580 e "12184580")
                result["seen_ids"] = list(dict.fromkeys(result["seen_ids"]))

                return result
        except Exception:
            return default_state

    def is_seen(self, fingerprint: str, source_id: str = "") -> bool:
        """Verifica se a vaga já foi vista por fingerprint ou por ID específico."""
        if fingerprint in self.state.get("seen_fingerprints", []):
            return True
        if source_id and source_id in self.state.get("seen_ids", []):
            return True
        return False

    def mark_seen(self, fingerprint: str, source_ids: List[str]):
        if "seen_fingerprints" not in self.state:
            self.state["seen_fingerprints"] = []
        if "seen_ids" not in self.state:
            self.state["seen_ids"] = []

        if fingerprint not in self.state["seen_fingerprints"]:
            self.state["seen_fingerprints"].append(fingerprint)

        for sid in source_ids:
            sid_str = str(sid)
            if sid_str not in self.state["seen_ids"]:
                self.state["seen_ids"].append(sid_str)

    def get_last_heartbeat(self) -> str:
        return self.state.get("last_heartbeat", "")

    def set_last_heartbeat(self, date_str: str):
        self.state["last_heartbeat"] = date_str

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
