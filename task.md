# what-should-we-eat — Tasks

## Backend: PostgreSQL + FastAPI
- [x] Database layer
- [x] API layer
- [x] Config & dependencies
- [x] Directive
- [x] Cleanup
- [x] Verification

## Recipe Image Extraction
- [x] Extract recipes from 93 HEIC images in `resources/`
  - [x] Group into batches (e.g. 5-10 at a time)
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

## User Management
- [x] Update `requirements.txt` and install dependencies (passlib, pyjwt, etc.)
- [x] Add `User` model to `execution/db/models.py`
- [x] Create authentication logic in `execution/api/auth.py`
- [x] Create endpoints for users in `execution/api/routers/users.py`
- [x] Add `UserBase`, `UserCreate`, `UserOut`, `Token` to schemas
- [x] Register router in `main.py`
- [x] Reset database and repopulate via `insert_chunk` scripts
- [x] Write and run tests for user features

## Household Architecture
- [x] Add `Household` model and update `Recipe` and `User` relations in `models.py`
- [x] Add schemas in `schemas.py`
- [x] Automatically provision default personal household on user registration
- [x] Filter `recipes.py` endpoints correctly to only use `active_household_id`
- [x] Implement `households.py` for joining/leaving households
- [x] Update testing logic and execute tests

## Frontend User Authentication
- [x] Add login button to top right of kitchen.html
- [x] Add sign up button to top right of kitchen.html
- [x] Build authentications modals (Login & Sign Up)
- [x] Implement API calls and token logic in JS
- [x] Load personal household recipes upon successful login
- [x] Refactor auth logic into shared `auth.js`
- [x] Add auth modals and buttons to `index.html`
- [x] Add auth modals and buttons to `recipes.html`
- [x] Link `auth.js` to all pages and remove duplicate auth logic from `kitchen.js`

