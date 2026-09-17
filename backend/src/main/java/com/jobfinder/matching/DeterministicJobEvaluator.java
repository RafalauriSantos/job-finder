package com.jobfinder.matching;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class DeterministicJobEvaluator implements JobEvaluator {
    @Override public EvaluationResult evaluate(Job job, CandidateProfile profile) {
        List<Evidence> evidence = new ArrayList<>();
        if (job.closed()) return result(EvaluationStatus.INELIGIBLE, 0, evidence, "closed", "vaga encerrada");
        String level = text(job.level());
        if (level.isBlank()) return result(EvaluationStatus.NEEDS_REVIEW, 0, evidence, "level", "senioridade desconhecida");
        if (!profile.acceptableLevels().stream().map(this::norm).anyMatch(level::equals))
            return result(EvaluationStatus.INELIGIBLE, 0, evidence, "level", "senioridade incompatível: " + job.level());
        evidence.add(new Evidence("level", "senioridade compatível", "job.level"));

        String mode = text(job.workMode());
        if (mode.isBlank() || mode.equals("unknown")) return result(EvaluationStatus.NEEDS_REVIEW, 0, evidence, "mode", "modalidade desconhecida");
        if (!profile.acceptableModes().stream().map(this::norm).anyMatch(mode::equals))
            return result(EvaluationStatus.INELIGIBLE, 0, evidence, "mode", "modalidade incompatível: " + job.workMode());
        evidence.add(new Evidence("location", "modalidade compatível", "job.workMode"));

        int score = 0;
        String description = norm(job.description());
        long skills = profile.skills().stream().filter(s -> containsSkill(job, s)).count();
        if (skills > 0) { score += 40; evidence.add(new Evidence("skills", skills + " competência(s) compatível(is)", "job.skills/description")); }
        else if (!description.contains("aprender") && !job.skills().isEmpty()) evidence.add(new Evidence("skills", "nenhuma competência compatível", "job.skills"));
        else evidence.add(new Evidence("skills", "interesse em aprender não conta como experiência", "job.description"));
        score += 30;
        evidence.add(new Evidence("seniority", "nível aceito pelo perfil", "job.level"));
        score += 20;
        evidence.add(new Evidence("location", "localização/modalidade aceita", "job.location/job.workMode"));
        if (profile.preferredCompanies().stream().map(this::norm).anyMatch(norm(job.company())::equals)) { score += 10; evidence.add(new Evidence("preference", "empresa prioritária", "job.company")); }
        return new EvaluationResult(EvaluationStatus.ELIGIBLE, score, evidence);
    }
    private boolean containsSkill(Job job, String skill) { String s = norm(skill); return job.skills().stream().map(this::norm).anyMatch(s::equals) && !norm(job.description()).contains("quero aprender " + s); }
    private EvaluationResult result(EvaluationStatus status, int score, List<Evidence> evidence, String rule, String message) { evidence.add(new Evidence(rule, message, "job")); return new EvaluationResult(status, score, evidence); }
    private String text(String value) { return norm(value); }
    private String norm(String value) { return value == null ? "" : value.trim().toLowerCase(Locale.ROOT); }
}
