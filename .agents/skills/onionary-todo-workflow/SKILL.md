---
name: onionary-todo-workflow
description: Implement a batch of Onionary changes with a committed todo list, one feature per commit, integrated regression tests, PR updates and immutable TestFlight releases. Use for multi-item feature or bug-fix requests in this repository.
---

# Onionary batch workflow

1. Read repository instructions, current branch/status and relevant existing todo documents. Preserve unrelated work. Check whether the request continues an open PR or explicitly requires a new branch from latest main.
2. Write a scoped checklist in `docs/` and **commit it before implementation**. Include reported failures, regression coverage and authorized delivery steps. Record uncertain requirements without inventing extra features.
3. Implement each item in its own commit with appropriate regression tests. Use existing execution scripts and directives. Keep dependent work ordered; do not mix unrelated items. For UI changes, verify labels, light/dark appearance and narrow layouts; follow the repository's HTML-first accessibility rule.
4. After implementing the batch, run the integrated checks matching changed behavior. Use Python 3.14 for backend tests and `ios/Onionary/Scripts/test.sh` for Swift and simulator tests. Inspect CI configuration for additional required checks. Diagnose actual failures and commit fixes separately; do not mask failures with retries, skips or weaker assertions. Bound stalled tests and preserve diagnostics.
5. Update checklist with evidence: commands, passed tests, limitations and remaining external work. Update the PR title/body for the final scope. Push when authorized; never merge without authorization. Do not poll GitHub while idle; the user supplies CI results unless they explicitly request monitoring.
6. For an authorized release, follow AGENTS.md's immutable release policy and existing release scripts. Inspect existing tags/builds, choose a fresh version tag and build number, commit/test code, then run `execution/tag_release.py`. Never overwrite or move a tag. Validate the archived app and all extensions share the intended version/build before using `ios/Onionary/Scripts/upload_testflight.sh`. Changed code needs a new tag/build; only an unchanged archive may resume an interrupted upload.
7. Report PR, validation results and actual release state. Distinguish upload accepted from Apple processing complete or tester availability. Never claim success from a launched background process alone. Do not reset Codex quotas or delete App Store Connect records.

Keep checklist completion honest: blocked or unverified delivery remains unchecked. This skill does not authorize deployments, paid services or changes outside the user's request.
