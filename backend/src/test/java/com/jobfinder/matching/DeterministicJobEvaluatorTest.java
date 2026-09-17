package com.jobfinder.matching;

import org.junit.jupiter.api.Test;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;

class DeterministicJobEvaluatorTest {
    private final JobEvaluator evaluator = new DeterministicJobEvaluator();
    private final CandidateProfile profile = new CandidateProfile(
            Set.of("java", "react", "typescript"), Set.of("sorocaba", "remoto"),
            Set.of("goomer", "gft"), Set.of("junior", "estágio", "internship"), Set.of("remote", "hybrid"));

    @Test void compatibleJobIsEligibleWithExplainedScore() {
        EvaluationResult result = evaluator.evaluate(job("Java Intern", "Java Spring remoto", "Goomer", "internship", "remote", "Sorocaba", Set.of("Java")), profile);
        assertEquals(EvaluationStatus.ELIGIBLE, result.status());
        assertTrue(result.score() > 0 && result.score() <= 100);
        assertTrue(result.evidences().stream().anyMatch(e -> e.rule().equals("skills")));
    }

    @Test void incompatibleLevelIsIneligible() {
        EvaluationResult result = evaluator.evaluate(job("Senior Java", "Java", "GFT", "senior", "remote", "Sorocaba", Set.of("Java")), profile);
        assertEquals(EvaluationStatus.INELIGIBLE, result.status());
        assertTrue(result.evidences().stream().anyMatch(e -> e.message().contains("senioridade")));
    }

    @Test void unknownModeNeedsReview() {
        EvaluationResult result = evaluator.evaluate(job("Java Junior", "Java", "GFT", "junior", "unknown", "", Set.of("Java")), profile);
        assertEquals(EvaluationStatus.NEEDS_REVIEW, result.status());
        assertTrue(result.evidences().stream().anyMatch(e -> e.message().contains("modalidade")));
    }

    @Test void learningInterestDoesNotCountAsSkillExperience() {
        EvaluationResult result = evaluator.evaluate(job("Java Intern", "Quero aprender Java", "GFT", "internship", "remote", "Sorocaba", Set.of()), profile);
        assertTrue(result.score() < 100);
        assertFalse(result.evidences().stream().anyMatch(e -> e.message().contains("competência(s) compatível(is)")));
        assertTrue(result.evidences().stream().anyMatch(e -> e.message().contains("aprender")));
    }

    @Test void sameInputProducesSameResult() {
        Job job = job("React Junior", "React TypeScript", "GFT", "junior", "hybrid", "Sorocaba", Set.of("React", "TypeScript"));
        assertEquals(evaluator.evaluate(job, profile), evaluator.evaluate(job, profile));
    }

    private static Job job(String title, String description, String company, String level, String mode, String location, Set<String> skills) {
        return new Job("job-1", title, description, company, level, mode, location, skills, false);
    }
}
