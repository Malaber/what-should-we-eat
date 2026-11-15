# Onionary iOS feedback for build 28

- [x] Fade unselected tags during filtering and put Clear filter beside Browse by tag.
- [x] Show the real color of every accent and mark the active color.
- [x] Style the recipe preview’s cooking action with a visible flame and readable text.
- [x] Move ingredient and step ordering to a dedicated list with native drag handles.
- [x] Edit tags as removable chips and offer matching suggestions while typing, including multiword tags.
- [x] Accept a single typed emoji as the recipe icon and render it in recipe rows.
- [ ] Verify the changed interactions, run the full PR checks, and record the results.
- [ ] Upload a fresh TestFlight build after the PR checks pass.

Local iPhone verification passed all 28 cases, including tag suggestions,
multiword chips, filter clearing, and accent selection. The separate native
reorder regression dragged an ingredient and verified its order after reopening
the sheet. The core suite also passed its single-emoji input cases.
