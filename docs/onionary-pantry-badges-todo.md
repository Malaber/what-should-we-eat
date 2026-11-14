# Saved pantry badges

- [x] Reuse recipe tag badges for removable pantry entries and add a quick Reset action.
- [x] Keep pantry ingredients and quantities in the local kitchen for the active account and backend.
- [x] Verify quantity matching, badge removal, reopening, and reset locally.
- [ ] Record full CI results on PR #9.

All 42 Swift tests and both focused iPhone UI tests passed. The core suite
checks that older kitchen files load and that pantry quantities survive saving
and reading from disk. The iPhone suite covers live matching, saving entries,
removing one badge, reopening, and clearing the pantry.
