from models.job import Job
from core.scope_analyzer import analyze_scope


def test_title_does_not_overrule_junior_scope():
    job = Job(
        title="Desenvolvedor Pleno",
        company="Empresa",
        workplace_type="remote",
        description="Apoiar o desenvolvimento, fazer correcoes simples e testes basicos sob orientacao. Desejavel conhecer Java.",
    )
    result = analyze_scope(job, {"stack_core": ["Java"], "stack_secundaria": []})
    assert result["declared_level"] == "mid"
    assert result["operational_level"] == "junior_to_mid"
    assert result["category"] in {"COMPATIVEL", "POTENCIALMENTE_COMPATIVEL"}


def test_senior_scope_is_not_hidden_by_a_mid_title():
    job = Job(
        title="Desenvolvedor Pleno",
        company="Empresa",
        workplace_type="remote",
        description="Liderar time, definir arquitetura, garantir alta disponibilidade e atuar com autonomia. Requer 5 anos.",
    )
    result = analyze_scope(job, {"stack_core": [], "stack_secundaria": []})
    assert result["operational_level"] == "senior"
    assert result["category"] == "INCOMPATIVEL"
    assert result["hard_barriers"]


def test_requirements_are_split_and_explained():
    job = Job(
        title="Backend Java Junior",
        company="Empresa",
        workplace_type="remote",
        description="Requisitos obrigatorios\n- Java e Git\nDiferenciais\n- Docker e AWS",
    )
    result = analyze_scope(job, {"stack_core": ["Java"], "stack_secundaria": ["Git"]})
    assert len(result["mandatory_requirements"]) == 1
    assert len(result["desirable_requirements"]) == 1
    assert result["category"] != "INCOMPATIVEL"


def test_scope_extracts_skills_only_from_requirement_sections():
    job = Job(
        title="Pessoa Desenvolvedora React Junior",
        company="Empresa",
        workplace_type="remote",
        description=(
            "Sobre a empresa: criamos produtos com Python e AWS. "
            "O que buscamos: experiência prática com React e Node.js. "
            "Diferenciais: Docker."
        ),
    )
    result = analyze_scope(job, {"stack_core": ["React", "Node.js"], "stack_secundaria": ["Docker"]})

    assert len(result["mandatory_requirements"]) <= 2
    assert all(len(item) < 100 for item in result["mandatory_requirements"])
    assert "python" not in " ".join(result["mandatory_requirements"]).lower()


def test_scope_recognizes_accented_portuguese_requirement_headers():
    job = Job(
        title="Desenvolvedor React Junior", company="Empresa", workplace_type="remote",
        description="Sobre a empresa: produto digital. O que você precisa ter: experiência com React. Diferenciais: Docker.",
    )
    result = analyze_scope(job, {"stack_core": ["React"], "stack_secundaria": []})

    assert any("React" in item for item in result["mandatory_requirements"])
    assert any("Docker" in item for item in result["desirable_requirements"])


def test_unmet_explicit_mandatory_requirement_blocks_compatibility():
    job = Job(
        title="Desenvolvedor Java Junior",
        company="Empresa",
        workplace_type="remote",
        description="Requisitos obrigatórios: 1+ ano de experiência prática com Java e inglês avançado.",
    )
    result = analyze_scope(job, {
        "stack_core": ["React", "Node.js"],
        "stack_secundaria": ["Git"],
        "english_level": "basic-intermediate",
    })

    assert result["category"] == "INCOMPATIVEL"
    assert result["hard_barriers"]


def test_project_level_skill_does_not_satisfy_required_years_of_experience():
    job = Job(
        title="Desenvolvedor Python Junior", company="Empresa", workplace_type="remote",
        description="Requisitos obrigatórios: 1+ ano de experiência prática com Python.",
    )
    result = analyze_scope(job, {
        "stack_core": ["React"], "stack_secundaria": ["Python"],
        "skills_evidence": {"python": {"level": "project"}},
    })

    assert any("python" in item.lower() for item in result["hard_barriers"])


def test_company_fifteen_years_is_not_five_year_candidate_experience():
    job = Job(
        title="Desenvolvedor Java Junior",
        company="Empresa",
        workplace_type="remote",
        description="A empresa atua há mais de 15 anos. Requisitos obrigatórios: experiência com Java.",
    )
    result = analyze_scope(job, {"stack_core": ["React"], "stack_secundaria": ["Git"]})

    assert not any("5 anos" in item for item in result["hard_barriers"])
