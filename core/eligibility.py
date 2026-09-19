from typing import Literal


Decision = Literal["VETO", "LOW_SCORE", "APPROVED"]


def classify_score(score: int, minimum_score: int) -> Decision:
    """Classifica o resultado final do scoring em uma decisão do funil."""
    if score <= 0:
        return "VETO"
    if score < minimum_score:
        return "LOW_SCORE"
    return "APPROVED"
