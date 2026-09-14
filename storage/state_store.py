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
                        "recent_decisions": data.get("recent_decisions", []),
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

    def record_llm_call(self) -> int:
        """
        Registra uma chamada ao LLM no contador diário (RPD tracking).
        NOTA DE ARQUITETURA (Gatilho: ~700 chamadas/dia):
        O Google AI Studio reseta a cota diária à meia-noite do Horário do Pacífico (PT / UTC-8).
        Atualmente a margem é > 99% (< 20 calls/dia).
        TODO: Quando o volume diário se aproximar de 700 calls/dia, migrar para:
              from zoneinfo import ZoneInfo
              today_str = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
        """
        import datetime
        today_str = datetime.date.today().isoformat()
        usage = self.state.get("llm_usage", {})
        if usage.get("date") != today_str:
            usage = {"date": today_str, "calls": 0}

        usage["calls"] = usage.get("calls", 0) + 1
        self.state["llm_usage"] = usage
        return usage["calls"]

    def get_llm_usage(self) -> Dict[str, Any]:
        """Retorna o uso diário de chamadas ao LLM."""
        import datetime
        today_str = datetime.date.today().isoformat()
        usage = self.state.get("llm_usage", {})
        if usage.get("date") != today_str:
            return {"date": today_str, "calls": 0}
        return usage

    def record_decision(
        self,
        job_id: str,
        source: str,
        identity_fingerprint: str,
        content_hash: str,
        decision: str,
        decision_reason: str,
        heuristic_score: int = 0,
        llm_score: Any = None,
        final_score: int = 0,
        raw_url: str = "",
        canonical_url: str = "",
        evidence_level: str = "",
        max_history: int = 150,
    ):
        """Registra a trilha de auditoria para responder por que cada vaga foi aceita ou rejeitada (SPEC-008)."""
        import datetime
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "job_id": str(job_id),
            "source": source,
            "raw_url": raw_url,
            "canonical_url": canonical_url,
            "identity_fingerprint": identity_fingerprint,
            "content_hash": content_hash,
            "evidence_level": evidence_level,
            "decision": decision,
            "decision_reason": decision_reason,
            "heuristic_score": heuristic_score,
            "llm_score": llm_score,
            "final_score": final_score,
        }
        if "recent_decisions" not in self.state:
            self.state["recent_decisions"] = []
        self.state["recent_decisions"].append(entry)
        if len(self.state["recent_decisions"]) > max_history:
            self.state["recent_decisions"] = self.state["recent_decisions"][-max_history:]

    def prune(self, max_seen_ids: int = 2000, max_fingerprints: int = 2000, max_decisions: int = 100):
        """
        Mantém o tamanho do arquivo de estado sob controle estrito (ADR-001).
        Evita crescimento descontrolado no repositório Git descartando identificadores antigos (FIFO).
        """
        seen_ids = self.state.get("seen_ids", [])
        if len(seen_ids) > max_seen_ids:
            self.state["seen_ids"] = seen_ids[-max_seen_ids:]

        fps = self.state.get("seen_fingerprints", [])
        if len(fps) > max_fingerprints:
            self.state["seen_fingerprints"] = fps[-max_fingerprints:]

        decisions = self.state.get("recent_decisions", [])
        if len(decisions) > max_decisions:
            self.state["recent_decisions"] = decisions[-max_decisions:]

    def save(self):
        self.prune()
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

