# Manage Users & Auth — Directive

## Goal
Register users, authenticate with JWT, and retrieve user profiles.

## Prerequisites
- Stack running (see `directives/local_development.md`)

## Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/users/register` | Create a new user (auto-creates personal household) |
| `POST` | `/users/token` | Login — exchange email/password for JWT (OAuth2 password flow) |
| `GET` | `/users/me` | Get current user profile with household memberships |

## Auth Flow

1. **Register** — `POST /users/register` with `{ email, name, password }`
   - Creates a `Household` named `"{name}'s Kitchen"` with a unique 6-char invite code
   - Creates the `User` with `personal_household_id` and `active_household_id` pointing to that household
   - Auto-adds user to household via `HouseholdMember`
2. **Login** — `POST /users/token` with form-data `username=<email>&password=<password>`
   - Returns `{ access_token, token_type: "bearer" }`
   - Token is JWT signed with `SECRET_KEY`, contains `sub: email` and `exp`
3. **Use token** — Pass `Authorization: Bearer <token>` header on all authenticated requests
4. **Frontend** — Auth modals in `frontend/auth.js`, token stored in `localStorage`

## Tools / Scripts
- `execution/api/auth.py` — Password hashing (bcrypt), JWT creation/validation, `get_current_user` dependency
- `execution/api/routers/users.py` — Registration, login, profile endpoints
- `execution/api/schemas.py` — `UserCreate`, `UserOut`, `Token`, `TokenData`
- `execution/db/models.py` — `User` model
- `frontend/auth.js` — Shared login/signup/logout logic (all pages)

## Edge Cases & Learnings
- Passwords are hashed with bcrypt (via `bcrypt` library directly, not passlib).
- JWT algorithm is HS256. Default expiry is 1440 minutes (24h), configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`.
- The `tokenUrl` is `users/token` (relative), which is what Swagger's "Authorize" button uses.
- Email uniqueness is enforced at the DB level (`unique=True`).
- Inactive users (`is_active=False`) are rejected by `get_current_active_user`.
- The `{{ }}` guard in `auth.py` catches unresolved template variables from deployment configs.
