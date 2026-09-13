import re
from typing import Tuple, List

# Dicionários canônicos de normalização
KNOWN_TECHNOLOGIES = [
    ("typescript", ["typescript", "ts"]),
    ("javascript", ["javascript", "js", "es6"]),
    ("react", ["react", "react.js", "reactjs", "react native"]),
    ("node.js", ["node.js", "nodejs", "node"]),
    ("postgresql", ["postgresql", "postgres", "psql"]),
    ("java", ["java", "spring", "spring boot", "springboot"]),
    ("python", ["python", "django", "fastapi", "flask"]),
    ("tailwind", ["tailwind", "tailwindcss"]),
    ("cloudflare", ["cloudflare", "workers", "pages"]),
    ("supabase", ["supabase"]),
    ("docker", ["docker", "containers"]),
    ("git", ["git", "github", "gitlab"]),
]

ALLOWED_REGIONAL_CITIES = [
    "tatuí", "tatui", "sorocaba", "votorantim", "boituva", "itapetininga"
]


import unicodedata

def normalize_title(raw_title: str) -> str:
    """Limpa ruídos, acentuação, emojis e caracteres especiais do título para evitar duplicidade entre plataformas."""
    if not raw_title:
        return ""
    # Remove emojis e tags HTML
    clean = re.sub(r"<[^>]+>", "", raw_title)
    clean = re.sub(r"[\U00010000-\U0010ffff]", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    # Normalização unicode (ex: Júnior -> Junior)
    clean = "".join(c for c in unicodedata.normalize("NFD", clean) if unicodedata.category(c) != "Mn")
    return clean


def normalize_workplace(raw_workplace: str, location_text: str = "", title_text: str = "") -> str:
    """
    Classifica a modalidade em: 'remote', 'hybrid', 'on-site' ou 'unknown'.
    """
    combined = f"{raw_workplace} {location_text} {title_text}".lower()
    if any(k in combined for k in ["remoto", "remote", "home office", "home-office", "teletrabalho"]):
        return "remote"
    if any(k in combined for k in ["híbrido", "hibrido", "hybrid"]):
        return "hybrid"
    if any(k in combined for k in ["presencial", "on-site", "onsite"]):
        return "on-site"
    return "unknown"


def is_location_allowed(workplace: str, location_text: str = "", title_text: str = "") -> Tuple[bool, str]:
    """
    Aplica a regra estrita de localidade:
    - Remoto: 100% Permitido em qualquer lugar.
    - Híbrido / Presencial: Permitido APENAS se for Tatuí, Sorocaba, Votorantim, Boituva ou Itapetininga.
    Retorna (is_allowed, reason).
    """
    if workplace == "remote":
        return True, "Trabalho 100% Remoto permitido"

    combined = f"{location_text} {title_text}".lower()
    for city in ALLOWED_REGIONAL_CITIES:
        if city in combined:
            return True, f"Localidade compatível na região: {city.capitalize()}"

    if workplace in ["hybrid", "on-site"]:
        return False, f"Vaga {workplace} fora da região atendida (Tatuí/Sorocaba/Boituva/Itapetininga)"

    # Se a modalidade for desconhecida, aceita para análise de descrição
    return True, "Modalidade a confirmar"


def is_pcd_exclusive(title: str) -> Tuple[bool, str]:
    """
    Heurística: detecta se a vaga é afirmativa/exclusiva para PCD com base no título.
    Não usa disabilities flag da Gupy (muitas empresas marcam todas as vagas por compliance).
    Não analisa description (disclaimers de diversidade seriam falsos positivos).
    Retorna (is_blocked, reason). O sinal é registrado no Job.pcd_signal para auditoria.
    """
    # Normaliza: minúsculo, remove pontos e acentos
    clean = title.lower().replace(".", "")
    clean = "".join(c for c in unicodedata.normalize("NFD", clean)
                    if unicodedata.category(c) != "Mn")

    if re.search(r"\bpcd\b", clean):
        return True, "Titulo contem 'PCD' (heuristica: vaga afirmativa/exclusiva)"
    if re.search(r"pessoas?\s+com\s+deficiencia", clean):
        return True, "Titulo contem 'Pessoa com Deficiencia'"
    return False, ""


def extract_technologies(text: str) -> List[str]:
    """Varre o texto da vaga e extrai tecnologias conhecidas da stack do candidato."""
    if not text:
        return []
    text_lower = f" {text.lower()} "
    detected = []
    for canonical_name, aliases in KNOWN_TECHNOLOGIES:
        for alias in aliases:
            # Busca como palavra isolada para evitar falsos positivos (ex: "js" dentro de "jobs")
            pattern = rf"(?:\b|\W){re.escape(alias)}(?:\b|\W)"
            if re.search(pattern, text_lower):
                detected.append(canonical_name)
                break
    return detected
