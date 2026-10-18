# Codex Flow v1 Acceptance

1. New Workflow — Verification: both
2. Create multiple Task Nodes — Verification: both
3. Node accepts a complete Prompt — Verification: both
4. Node sets Working Directory — Verification: both
5. Drag edges to define Dependency — Verification: both
6. Save Workflow — Verification: both
7. Run Workflow — Verification: both
8. Scheduler automatically determines READY — Verification: automated test
9. Create a Codex Thread only after READY — Verification: automated test
10. Automatically send the complete Prompt — Verification: automated test
11. Identify completed / failed / interrupt — Verification: automated test
12. Predecessor failure blocks downstream — Verification: automated test
13. Predecessor success releases downstream — Verification: automated test
14. Independent tasks run concurrently — Verification: automated test
15. Prevent dangerous same-workspace writes — Verification: automated test
16. Pause / Resume / Retry / Cancel — Verification: both
17. Recover after app restart — Verification: both
18. Run History — Verification: both
19. Human attention notification — Verification: both
20. Open the corresponding thread in Codex — Verification: manual UX check
21. No master LLM control — Verification: automated test
22. No manual Enter between tasks — Verification: manual UX check
