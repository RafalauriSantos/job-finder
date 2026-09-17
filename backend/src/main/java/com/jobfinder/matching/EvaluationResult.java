package com.jobfinder.matching;

import java.util.List;

public record EvaluationResult(EvaluationStatus status, int score, List<Evidence> evidences) {
    public EvaluationResult { evidences = List.copyOf(evidences == null ? List.of() : evidences); }
}
