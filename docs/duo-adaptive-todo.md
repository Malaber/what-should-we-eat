# MISC-12: adaptive Onionary workspace

Sources: [MISC-12](https://turniere.atlassian.net/browse/MISC-12) and
[Tracy PR 31](https://github.com/Malaber/tracy/pull/31).
Keep the current PR and release objective; implement each item separately, then
run integrated checks. No retries, quota resets, or overwritten release tags.

- [ ] Keep recovery banners outside native tab containers; expose reachable navigation on Duo/iPad.
- [ ] Use compatible runtime/device selection and explicit iPhone, Duo and iPad test coverage with Xcode 27.1.
- [ ] Cooking: adaptive coordinated ingredients/instructions panes, one adventure, retained active step and scroll context, accessible controls.
- [ ] Recipes: adaptive list/detail preview; selection never starts cooking; explicit Cook/Resume, Edit and Share; retained selection when collapsing.
- [ ] Kitchen: adaptive plan/shopping panes, stable shopping identities and checks, explicit refresh, local-state disclosure.
- [ ] Editor: adaptive metadata/ingredients and instructions, preserve draft/focus when resizing; functional sheets and keyboard.
- [ ] Duo fold/resize continuity tests and compact/iPad regression; use typed accessibility queries and avoid unnecessary terminate/relaunch.
- [ ] Review screenshots and accessibility in light/dark, EN/DE, large text and Reduce Motion; record any unverified pose matrix honestly.
- [ ] Run full regression, publish a fresh tag/build and launch signed TestFlight delivery after fixes.

Tracy lessons: safeAreaInset outside TabView can obscure adaptive navigation;
use dedicated banner layout space. Select hittable navigation buttons and assert
destination. Scope queries to typed lists/fields, avoid lazy whole-tree queries.
Use one launch for fold/marketing scenarios. Explicit termination only for actual
persistence tests, after backgrounding to SpringBoard. Hinge changes must never
modify domain state; layout is driven by local geometry, not device model.

Banner implementation follows Tracy #31: dedicated VStack space, never a safe-area
inset wrapped around TabView. Geometry drives workspace changes; session state
stays owned by the existing store/editor. Compatibility-aware simulator selection
supports explicit Duo and iPad device types rather than removing those targets.

## Integration checkpoint

Xcode 27.1 `build-for-testing` passes for arm64 and x86_64 simulator targets,
including the Duo test harness. Python 3.14 runtime selection regression tests:
2 passed. Shell syntax, Python compilation and `git diff --check` pass.

Implementation commits cover all four adaptive workspaces. Final UI validation
remains pending; the checklist above deliberately stays open until execution and
visual review. Duo tests exercise 0/90/180-degree folds, cooking undo/redo,
non-mutating previews, editor drafts, shopping refresh/checks and auth navigation.
They attach host-captured outer/inner display images for inspection. Full iPhone
and iPad regression suites run separately. No retries or weakened assertions.

Follow-up integration fixes split editor expressions for Swift type checking,
restore step ordering controls, retain step focus anchors, refresh selected recipe
previews from the store, and fix actor isolation in the fold test harness. Release
and screenshot jobs select Xcode 27.1 and compatible simulator runtimes. Local
TestFlight delivery runs all three device profiles before signing/uploading.

Still unverified: final UI results, visual fold screenshots, VoiceOver, large text,
Reduce Motion, the complete language/theme matrix, and accepted TestFlight upload.
