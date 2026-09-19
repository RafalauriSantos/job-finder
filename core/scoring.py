from typing import List, Tuple
from models.job import Job

import json
from pathlib import Path

_PROFILE_PATH = Path(__file__).parent.parent / "profile.json"


def _load_priority_companies() -> List[str]:
    default_companies = ["goomer", "gft", "flavia nasser", "flávia nasser"]
    if _PROFILE_PATH.exists():
        try:
            with open(_PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                companies = data.get("empresas_prioritarias", [])
                if companies:
                    result = []
                    for comp in companies:
                        c_lower = comp.strip().lower()
                        result.append(c_lower)
                        if "flavia" in c_lower and "flávia nasser" not in result:
                            result.append("flávia nasser")
                    return result
        except Exception:
            pass
    return default_companies


# Empresas prioritárias de monitoramento
PRIORITY_COMPANIES = _load_priority_companies()

# Dicionários de Senioridade
SENIOR_KEYWORDS = [
    "senior", "sênior", "sr", "lead", "especialista", "arquiteto", "tech lead",
    "coordenador", "gerente", "diretor", "principal", "staff"
]
MID_KEYWORDS = ["pleno", "pl"]
JUNIOR_KEYWORDS = [
    "junior", "júnior", "jr", "estagio", "estágio", "intern", "trainee",
    "starter", "entry level", "entry-level", "software engineer i", "developer i",
    "desenvolvedor i"
]


import re

def matches_any(keywords: List[str], text: str) -> bool:
    for kw in keywords:
        pattern = rf"(?:\b|\W){re.escape(kw)}(?:\b|\W)"
        if re.search(pattern, text):
            return True
    return False

def calculate_match_score(job: Job) -> Tuple[int, List[str]]:
    """
    Calcula o Match Score (0 a 100) da vaga contra o perfil técnico configurado em profile.json:
    - Base: Stack Core (React, TypeScript, Node.js, PostgreSQL, etc.)
    - Expansão: Stack Secundária (Java, Python, Docker, etc.)
    - Trava: Modalidade Remota ou Cidades Regionais Permitidas.
    """

    score = 0
    reasons = []

    title_lower = job.title.lower()
    text_to_analyze = f"{job.title} {job.description}".lower()

    # 1. Checagem de Senioridade usando Word Boundaries para evitar falsos positivos (ex: "pl" em "Implementation")

    has_senior = matches_any(SENIOR_KEYWORDS, title_lower)
    has_mid = matches_any(MID_KEYWORDS, title_lower)
    has_junior = matches_any(JUNIOR_KEYWORDS, title_lower)

    if has_senior:
        score -= 60
        reasons.append("Senioridade alta detectada (-60 pts)")
        return max(0, score), reasons

    if has_mid:
        score += 10
        job.seniority = "mid"
        reasons.append("Nível Pleno compatível; requisitos serão avaliados (+10 pts)")

    if has_junior:
        score += 35
        reasons.append("Nível Júnior / Entrada identificado (+35 pts)")
        job.seniority = "junior"

    # 2. Localidade & Modalidade
    if job.workplace_type == "remote":
        score += 20
        reasons.append("Vaga 100% Remota (+20 pts)")
    elif job.workplace_type in ["hybrid", "on-site"]:
        from core.normalizer import ALLOWED_REGIONAL_CITIES
        for city in ALLOWED_REGIONAL_CITIES:
            if city in (job.location + " " + job.title).lower():
                score += 20
                reasons.append(f"Região atendida: {city.capitalize()} (+20 pts)")
                break

    # 3. Empresa Monitorada
    comp_lower = job.company.lower()
    if any(p in comp_lower for p in PRIORITY_COMPANIES):
        score += 15
        reasons.append(f"Empresa-alvo prioritária: {job.company} (+15 pts)")

    # 4. Compatibilidade com a Stack do Currículo (Até 30 pts)
    techs = job.technologies
    if not techs:
        from core.normalizer import extract_technologies
        techs = extract_technologies(text_to_analyze)
        job.technologies = techs

    # Carrega stacks dinamicamente do profile
    from core.llm_judge import get_profile
    profile = get_profile()
    core_list = [t.lower() for t in profile.get("stack_core", ["react", "typescript", "node.js", "postgresql", "tailwind", "supabase"])]
    secondary_list = [t.lower() for t in profile.get("stack_secundaria", ["java", "python", "docker", "git"])]

    core_matches = [t for t in techs if t.lower() in core_list]
    if core_matches:
        pts = min(25, len(core_matches) * 10)
        score += pts
        reasons.append(f"Stack Core do perfil: {', '.join(core_matches)} (+{pts} pts)")

    target_matches = [t for t in techs if t.lower() in secondary_list]
    if target_matches:
        pts = min(15, len(target_matches) * 5)
        score += pts
        reasons.append(f"Stack Secundária: {', '.join(target_matches)} (+{pts} pts)")

    # Garante teto de 100 e piso de 0
    final_score = max(0, min(100, score))
    return final_score, reasons



# Sinais de relevância para itens RSS (título é a única fonte de dados)
RSS_JOB_SIGNALS = [
    "vaga", "vagas", "contratando", "contrata", "oportunidade", "oportunidades",
    "processo seletivo", "selecao", "seleção", "hiring", "aberto",
    "desenvolvedor", "developer", "programador", "analista", "engenheiro",
    "estagio", "estágio", "trainee",
]
RSS_NOISE_SIGNALS = [
    "lança", "lanca", "recurso", "feature", "atualização", "atualizacao",
    "cliente", "cardápio", "cardapio", "pedido", "receita", "restaurante",
    "review", "avaliação", "avaliacao", "resultado financeiro", "investidor",
]


# Sinais que indicam papéis de comércio, culinária, saúde, recepção que não pertencem a TI
NON_TECH_ROLES = [
    "padaria", "confeitaria", "balconista", "atendente", "caixa", "cozinha",
    "garcom", "garçom", "copeiro", "limpeza", "farmacia", "farmácia", "enfermagem",
    "odontologia", "recepcionista", "vendedor", "vendedora", "auxiliar de loja"
]

# Sinais mínimos de computação/desenvolvimento
TECH_ROLE_SIGNALS = [
    "desenvolvedor", "developer", "programador", "programacao", "programação",
    "software", "frontend", "front-end", "backend", "back-end", "fullstack", "full stack",
    "web", "ti", "sistemas", "computacao", "computação", "informatica", "informática",
    "dados", "qa", "devops", "engenharia de software", "react", "node", "python", "java"
]


def calculate_rss_relevance(job: Job) -> Tuple[int, List[str]]:
    """
    Scoring dedicado para itens RSS/Google News.
    RSS não tem campos estruturados (description, workplaceType, salary),
    então avalia relevância pelo título: parece uma vaga real ou é notícia/produto?
    """
    score = 0
    reasons = []
    title_lower = job.title.lower()

    # Remove acentos para matching
    import unicodedata
    title_clean = "".join(c for c in unicodedata.normalize("NFD", title_lower)
                         if unicodedata.category(c) != "Mn")

    # 0. Trava de Papéis Não-Tecnológicos (Padaria, Recepção, Balcão, etc)
    non_tech_matches = [s for s in NON_TECH_ROLES if matches_any([s], title_clean)]
    if non_tech_matches:
        reasons.append(f"Cargo não-tecnológico detectado ({', '.join(non_tech_matches)}): veto imediato (-100 pts)")
        return 0, reasons

    # 1. Sinais de vaga no título (+30)
    job_matches = [s for s in RSS_JOB_SIGNALS if matches_any([s], title_clean)]
    if job_matches:
        score += 30
        reasons.append(f"Sinal de vaga no titulo: {', '.join(job_matches[:3])} (+30 pts)")

    # 2. Sinais de ruído/notícia no título (-30)
    noise_matches = [s for s in RSS_NOISE_SIGNALS if matches_any([s], title_clean)]
    if noise_matches:
        score -= 30
        reasons.append(f"Sinal de noticia/produto: {', '.join(noise_matches[:3])} (-30 pts)")

    # 3. Senioridade
    has_senior = matches_any(SENIOR_KEYWORDS, title_lower)
    has_junior = matches_any(JUNIOR_KEYWORDS, title_lower)

    if has_senior:
        score -= 60
        reasons.append("Senioridade alta detectada (-60 pts)")
        return 0, reasons

    # Trava de Estágio: Se for estágio, EXIGE contexto explícito de TI/desenvolvimento
    has_tech_signal = matches_any(TECH_ROLE_SIGNALS, title_clean)
    if has_junior:
        if "estag" in title_clean and not has_tech_signal:
            score -= 50
            reasons.append("Estágio sem menção explícita a TI/desenvolvimento (-50 pts)")
        else:
            score += 20
            reasons.append(f"Nivel Junior / Entrada identificado (+20 pts)")


    # 4. Empresa Monitorada prioritária
    comp_lower = job.company.lower()
    if any(p in comp_lower for p in PRIORITY_COMPANIES):
        score += 20
        reasons.append(f"Empresa-alvo prioritaria: {job.company} (+20 pts)")

    # 5. Stack do CV no título
    from core.normalizer import extract_technologies
    techs = extract_technologies(job.title)
    if techs:
        pts = min(25, len(techs) * 10)
        score += pts
        reasons.append(f"Tecnologias detectadas: {', '.join(techs)} (+{pts} pts)")
        job.technologies = techs

    final_score = max(0, min(100, score))
    return final_score, reasons



def evaluate_job(job: Job, is_rss: bool = False) -> Tuple[int, List[str]]:
    """
    Ponto único de entrada do funil (SPEC-008). Roda o heurístico primeiro (sempre, é grátis).
    Só chama o LLM Judge se:
    1. O score heurístico não descartou a vaga;
    2. O perfil de evidência indicar que há contexto suficiente (should_route_to_llm).
    """
    from core import llm_judge
    from core.evidence import should_route_to_llm

    heuristic_score, reasons = (
        calculate_rss_relevance(job) if is_rss else calculate_match_score(job)
    )

    if not llm_judge.should_invoke_judge(heuristic_score):
        return heuristic_score, reasons

    # SPEC-008: Evidence Profiling — poupa LLM se evidência for rasa (ex: RSS sem descrição)
    if not should_route_to_llm(job):
        reasons.append("Heurística Conclusiva: contexto textual insuficiente para LLM (LOW_EVIDENCE)")
        return heuristic_score, reasons

    result = llm_judge.judge(job.title, job.company, job.description)

    if result is None:
        reasons.append("Fallback Heurístico Ativado (LLM indisponível/429)")
        return heuristic_score, reasons

    if not result["is_real_job_opportunity"]:
        reasons.append(f"LLM Judge: não é vaga real — {result.get('reasoning', '')} (score zerado)")
        return 0, reasons

    llm_score = result["cv_compatibility_score"]
    combined = int(heuristic_score * 0.3 + llm_score * 0.7)
    reasons.append(f"LLM Judge: {result.get('reasoning', '')} (compat={llm_score}, combinado={combined})")
    return max(0, min(100, combined)), reasons

