from typing import List, Tuple
from models.job import Job

# Empresas prioritárias de monitoramento
PRIORITY_COMPANIES = ["goomer", "gft", "flavia nasser", "flávia nasser"]

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
    Calcula o Match Score (0 a 100) da vaga contra o perfil técnico do Rafael Lauri:
    - Base: React, TypeScript, Node.js, PostgreSQL, Supabase, Cloudflare.
    - Expansão: Java (Spring Boot) e Python (FastAPI).
    - Trava: Tatuí / Sorocaba / Remoto.
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
        score -= 30
        reasons.append("Nível Pleno detectado (-30 pts)")

    if has_junior:
        score += 35
        reasons.append("Nível Júnior / Entrada identificado (+35 pts)")
        job.seniority = "junior"

    # 2. Localidade & Modalidade
    if job.workplace_type == "remote":
        score += 20
        reasons.append("Vaga 100% Remota (+20 pts)")
    elif job.workplace_type in ["hybrid", "on-site"]:
        # Se for na região permitida
        for city in ["tatuí", "tatui", "sorocaba", "votorantim", "boituva", "itapetininga"]:
            if city in (job.location + " " + job.title).lower():
                score += 20
                reasons.append(f"Região de Tatuí/Sorocaba atendida: {city.capitalize()} (+20 pts)")
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

    # Core Stack Atual (React, TypeScript, Node.js, PostgreSQL)
    core_matches = [t for t in techs if t in ["react", "typescript", "node.js", "postgresql", "tailwind", "supabase"]]
    if core_matches:
        pts = min(25, len(core_matches) * 10)
        score += pts
        reasons.append(f"Stack Core do seu CV: {', '.join(core_matches)} (+{pts} pts)")

    # Stack de Expansão / Alvo GFT (Java / Python)
    target_matches = [t for t in techs if t in ["java", "python", "docker", "git"]]
    if target_matches:
        pts = min(15, len(target_matches) * 5)
        score += pts
        reasons.append(f"Stack Estratégica: {', '.join(target_matches)} (+{pts} pts)")

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

    # 1. Sinais de vaga no título (+30)
    job_matches = [s for s in RSS_JOB_SIGNALS if s in title_clean]
    if job_matches:
        score += 30
        reasons.append(f"Sinal de vaga no titulo: {', '.join(job_matches[:3])} (+30 pts)")

    # 2. Sinais de ruído/notícia no título (-30)
    noise_matches = [s for s in RSS_NOISE_SIGNALS if s in title_clean]
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
    if has_junior:
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

    final_score = max(-100, min(100, score))
    return final_score, reasons


def evaluate_job(job: Job, is_rss: bool = False) -> Tuple[int, List[str]]:
    """
    Ponto único de entrada do funil. Roda o heurístico primeiro (sempre, é grátis)
    e só chama o LLM Judge se o heurístico não descartou a vaga de cara.
    """
    from core import llm_judge

    heuristic_score, reasons = (
        calculate_rss_relevance(job) if is_rss else calculate_match_score(job)
    )

    if not llm_judge.should_invoke_judge(heuristic_score):
        return heuristic_score, reasons

    result = llm_judge.judge(job.title, job.company, job.description)

    if result is None:
        return heuristic_score, reasons

    if not result["is_real_job_opportunity"]:
        reasons.append(f"LLM Judge: não é vaga real — {result.get('reasoning', '')} (score zerado)")
        return 0, reasons

    llm_score = result["cv_compatibility_score"]
    combined = int(heuristic_score * 0.3 + llm_score * 0.7)
    reasons.append(f"LLM Judge: {result.get('reasoning', '')} (compat={llm_score}, combinado={combined})")
    return max(0, min(100, combined)), reasons

