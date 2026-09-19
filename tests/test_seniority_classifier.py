from core.scoring import classify_seniority


def test_classifies_junior_title():
    assert classify_seniority("Desenvolvedor Frontend Junior") == "junior"


def test_classifies_mid_title():
    assert classify_seniority("Desenvolvedor Pleno React") == "mid"


def test_classifies_explicit_senior_title():
    assert classify_seniority("Tech Lead Backend") == "senior"


def test_does_not_treat_pl_as_senior_fragment():
    assert classify_seniority("Analista de Plataforma") == "unknown"
