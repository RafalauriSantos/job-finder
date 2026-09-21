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
