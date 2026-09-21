from core.eligibility import classify_location
from core.scope_analyzer import analyze_scope
from models.job import Job


def test_completed_degree_is_a_hard_barrier():
    job = Job('Desenvolvedor Junior', 'Empresa', 'remote',
              description='Requisitos: ensino superior completo obrigatório. Java.')
    result = analyze_scope(job, {'stack_core': ['React'], 'stack_secundaria': ['Java']})
    assert result['education_barriers']
    assert result['category'] == 'INCOMPATIVEL'


def test_degree_in_progress_is_not_a_completed_degree_barrier():
    job = Job('Desenvolvedor Junior', 'Empresa', 'remote',
              description='Graduação em andamento ou curso técnico em TI. Java.')
    result = analyze_scope(job, {'stack_core': ['React'], 'stack_secundaria': ['Java']})
    assert result['education_barriers'] == []


def test_degree_listed_as_desirable_is_not_a_hard_barrier():
    job = Job('Desenvolvedor Junior', 'Empresa', 'remote',
              description='Requisitos desejáveis: ensino superior completo. Java.')
    result = analyze_scope(job, {'stack_core': ['React'], 'stack_secundaria': ['Java']})
    assert result['education_barriers'] == []


def test_explicit_unknown_city_is_rejected_even_when_source_misses_workplace():
    job = Job('Desenvolvedor Junior', 'Empresa', 'unknown', location='São Paulo, SP')
    decision, reason = classify_location(job)
    assert decision == 'LOCATION_REJECTED'
    assert 'fora da região' in reason.lower()


def test_remote_description_overrides_missing_workplace_field():
    job = Job('Desenvolvedor Pleno', 'Empresa', 'unknown', location='Brasil',
              description='Atuação 100% remota para todo o Brasil.')
    decision, _ = classify_location(job)
    assert decision == 'APPROVED'
