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


def calculate_match_score(job: Job) -> Tuple[int, List[str]]:
    """
    Calcula o Match Score (0 a 100) da vaga contra o perfil técnico do Rafael Lauri:
    - Base: React, TypeScript, Node.js, PostgreSQL, Supabase, Cloudflare.
    - Expansão: Java (Spring Boot) e Python (FastAPI).
    - Trava: Tatuí / Sorocaba / Remoto.
    """
    score = 0
    reasons = []

    text_to_analyze = f"{job.title} {job.description}".lower()

    # 1. Checagem de Senioridade (Penalidade / Bônus)
    has_senior = any(k in job.title.lower() for k in SENIOR_KEYWORDS)
    has_mid = any(k in job.title.lower() for k in MID_KEYWORDS)
    has_junior = any(k in job.title.lower() for k in JUNIOR_KEYWORDS)

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
