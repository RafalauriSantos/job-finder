from typing import List

from models.job import Job


def order_for_alerts(jobs: List[Job]) -> List[Job]:
    """Ordena alertas por frescor, aderência e interesse de aprendizado."""
    return sorted(
        jobs,
        key=lambda job: (
            job.freshness_score,
            job.match_score,
            job.learning_interest_score,
        ),
        reverse=True,
    )
