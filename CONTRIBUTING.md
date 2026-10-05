# Contributing

Job Finder is a personal, local-first project. Contributions should preserve
the separation between public source code and machine-local state.

Before opening a change:

1. create a virtual environment and install `requirements.txt`;
2. run `pytest -q`;
3. inspect `git diff --check`;
4. confirm that no `.env`, database, log, browser profile or runtime state is staged.

Changes should include focused tests when behavior changes. Collectors must
respect their source's public access boundaries and must not embed credentials.
CI validates code only; production collection runs on the owner's local host.
