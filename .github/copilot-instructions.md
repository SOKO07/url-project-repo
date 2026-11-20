# To the agent working in this repository

- Read SPEC.md before writing code. PLAN.md has the order of work.
- Do not use dict, set or the built-in hash() inside src/. Use the hash table we built.
- After changing code, run the tests (`make test`, or `python -m unittest discover -s tests` where make is missing) and show the result.
- If a test fails, fix the code, not the test.
- For each issue, work on feature/<issue-number>-<name> off develop and post progress as issue comments.
- When done, commit as "Step N: what was done (#issue)", merge into develop, push and close the issue.
- I am a first-year student. Summarize what you changed in at most three lines.
