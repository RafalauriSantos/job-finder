"""
LLM Judge: camada semântica que roda em cima do scoring heurístico.
Só é chamado para vagas que já passaram no heurístico com um piso mínimo,
pra não gastar chamada de API em lixo óbvio (sênior, vaga não-dev, etc).

Suporta múltiplos provedores com fallback automático:
1. Google Gemini (100% GRÁTIS via Google AI Studio - GEMINI_API_KEY)
2. Anthropic Claude (ANTHROPIC_API_KEY)
3. Fallback Heurístico (se nenhuma chave estiver configurada ou se houver erro)
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)

_PROFILE_PATH = Path(__file__).parent.parent / "profile.json"
_HEURISTIC_FLOOR = 30  # abaixo disso, nem chama o LLM

_PROFILE_CACHE = None


def get_profile() -> dict:
    global _PROFILE_CACHE
    if _PROFILE_CACHE is None:
        if _PROFILE_PATH.exists():
            with open(_PROFILE_PATH, encoding="utf-8") as f:
                _PROFILE_CACHE = json.load(f)
        else:
            _PROFILE_CACHE = {}
    return _PROFILE_CACHE


JUDGE_PROMPT = """Você é um triador técnico de vagas para um candidato específico.
Analise se o texto abaixo é uma vaga real de desenvolvedor compatível com o perfil.

PERFIL DO CANDIDATO:
{profile_json}

TÍTULO: {title}
EMPRESA: {company}
DESCRIÇÃO:
{description}

Regras de julgamento:
- Se NÃO for uma oportunidade de vaga real (despedida, desabafo, notícia institucional, vaga não-dev), marque is_real_job_opportunity=false.
- Se exigir graduação completa OBRIGATÓRIA (não apenas preferencial), marque cv_compatibility_score <= 20.
- Se for vaga PCD exclusiva/afirmativa, marque is_real_job_opportunity=false.
- Se for sênior/lead/gerente/especialista, marque cv_compatibility_score <= 10.
- Se for Pleno, marque cv_compatibility_score <= 40 a menos que a stack seja fortemente alinhada ao perfil (React/TypeScript/Node/Postgres/Supabase).

Responda APENAS com o JSON abaixo, sem markdown, sem texto extra:
{{"is_real_job_opportunity": bool, "cv_compatibility_score": int, "reasoning": "string curta", "recommendation": "APPLY_NOW|MAYBE|SKIP"}}"""


def should_invoke_judge(heuristic_score: int) -> bool:
    return heuristic_score >= _HEURISTIC_FLOOR


def _call_gemini(api_key: str, prompt: str) -> Optional[Dict[str, Any]]:
    """Chama a API do Google Gemini (100% Grátis via Google AI Studio)."""
    for model in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]:
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                clean = text.strip().replace("```json", "").replace("```", "").strip()
                return json.loads(clean)
            else:
                logger.warning(f"Gemini API ({model}) retornou status {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            logger.warning(f"Erro ao chamar Gemini ({model}): {e}")
    return None


def _call_anthropic(api_key: str, prompt: str) -> Optional[Dict[str, Any]]:
    """Chama a API da Anthropic (Claude Haiku)."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def judge(title: str, company: str, description: str) -> Optional[Dict[str, Any]]:
    """
    Avalia a vaga usando o provedor de IA disponível (Gemini Grátis ou Claude).
    Retorna None em caso de ausência de chaves ou erro, ativando fallback heurístico.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not gemini_key and not anthropic_key:
        return None

    prompt = JUDGE_PROMPT.format(
        profile_json=json.dumps(get_profile(), ensure_ascii=False),
        title=title,
        company=company,
        description=(description or "")[:3000],
    )

    result = None
    try:
        if gemini_key:
            result = _call_gemini(gemini_key, prompt)
        elif anthropic_key:
            result = _call_anthropic(anthropic_key, prompt)

        if result:
            assert isinstance(result.get("is_real_job_opportunity"), bool)
            assert isinstance(result.get("cv_compatibility_score"), int)
            return result
    except Exception as e:
        logger.warning(f"LLM judge falhou ({type(e).__name__}: {e}) — fallback heurístico")

    return None
