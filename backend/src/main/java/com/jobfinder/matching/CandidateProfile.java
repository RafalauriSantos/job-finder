package com.jobfinder.matching;

import java.util.Set;

public record CandidateProfile(Set<String> skills, Set<String> preferredLocations,
                               Set<String> preferredCompanies, Set<String> acceptableLevels,
                               Set<String> acceptableModes) {
    public CandidateProfile {
        skills = copy(skills); preferredLocations = copy(preferredLocations);
        preferredCompanies = copy(preferredCompanies); acceptableLevels = copy(acceptableLevels);
        acceptableModes = copy(acceptableModes);
    }
    private static Set<String> copy(Set<String> value) { return value == null ? Set.of() : Set.copyOf(value); }
}
