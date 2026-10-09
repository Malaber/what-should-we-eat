# Onionary polish and import revisions

Commit this checklist first. Implement each item in its own commit with relevant
regression coverage, then run the complete applicable test suites and fix failures.
Use the Apple design skill for interaction, accessibility and layout work.

- [x] Dismiss iOS keyboard by tapping outside fields; retain accessible Done action.
- [x] Give populated numeric recipe fields persistent labels and units.
- [x] Store recipe base portions end-to-end, including Chefkoch import and editing.
- [x] Update portion adjustment live on field exit and +/-; remove redundant whole-recipe scaling section.
- [x] Add free-text Apple Intelligence recipe drafting with Hiinterval-style availability handling and draft review.
- [x] Accept Chefkoch app share-sheet payloads (URL and text links), including tracking query strings.
- [ ] Publish stable GitHub releases on main, minor bump by default, with merged PR title/body as release notes (Planini pattern).
- [ ] Format HTML with a pinned formatter and enforce it in CI, including GitHub Pages.
- [ ] Add appropriate web links to app.onionary.malaber.de.
- [ ] Move user passkeys, language and appearance to account settings; match Planini list/actions and prevent deleting the last passkey server-side.
- [ ] Fix dark-mode recipe-import panel contrast.
- [ ] Keep recipe-card actions visible with responsive wrapping or scrolling.
- [ ] Center and space recipe-share dialogs; provide responsive sizing, focus handling and reduced-motion support.
- [ ] Preserve umlauts in configured Impressum values, including the Ansible-to-Compose path.
- [ ] Run backend, web, iOS and affected deployment/release tests; fix regressions, inspect UI, push new PR. Leave GitHub CI follow-up to the user.
