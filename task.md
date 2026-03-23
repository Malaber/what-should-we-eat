# what-should-we-eat — Tasks

## Backend: PostgreSQL + FastAPI
- [x] Database layer
- [x] API layer
- [x] Config & dependencies
- [x] Directive
- [x] Cleanup
- [x] Verification

## Recipe Image Extraction
- [/] Extract recipes from 93 HEIC images in `resources/`
  - [ ] Group into batches (e.g. 5-10 at a time)
  - [x] Extract ingredients, steps (with times), active/total time
  - [x] Assign tags from: Pasta, Reis, Kartoffeln, Tacos, Viel Gemüse, Fleisch, Fisch, Gesund, Schnell, Vegetarisch
  - [x] Write SQL insert statements to the database

## Frontend: Manage Recipes
- [x] Create `frontend/recipes.html` layout
- [x] Add navigation linking `index.html` and `recipes.html`
- [x] Build recipe list view (name, tags, kcal, times)
- [x] Build robust edit/create form (ingredients, steps, tag selector)
- [x] Build custom styled confirmation dialog for deletion
- [x] Implement `frontend/manage.js` logic to interface with the API
