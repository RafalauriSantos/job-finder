package com.jobfinder.matching;

import java.util.Set;

public record Job(String id, String title, String description, String company, String level,
                  String workMode, String location, Set<String> skills, boolean closed) {
    public Job { skills = skills == null ? Set.of() : Set.copyOf(skills); }
}
