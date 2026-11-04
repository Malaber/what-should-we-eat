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
