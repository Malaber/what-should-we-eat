# Manage Households — Directive

## Goal
Create, join, switch, and leave households. Households scope recipes, meal plans, and shopping lists so multiple users can share a kitchen.

## Prerequisites
- Stack running (see `directives/local_development.md`)
- Authenticated user

## Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/households` | List the current user's households |
| `POST` | `/households` | Create a new household (auto-join the creator) |
| `POST` | `/households/join/{invite_code}` | Join a household by its 6-char alphanumeric invite code |
| `POST` | `/households/switch/{household_id}` | Switch active household (must already be a member) |
| `POST` | `/households/leave/{household_id}` | Leave a household (cannot leave personal household) |
| `DELETE` | `/households/cleanup` | Remove orphaned households with no members and no recipes |

## How Invite Codes Work
- Every household gets a unique 6-character code (`A-Z0-9`) generated at creation time.
- Codes are stored uppercase and lookups are case-insensitive (input is `.upper()`'d).
- Collision safety: `generate_unique_invite_code()` retries up to 10 times if a code already exists.
- Users share the code verbally or via text; the UI shows it on each household card.

## Data Model
- `Household` — `id`, `name`, `invite_code`, `created_at`
- `HouseholdMember` — junction table: `user_id` + `household_id` (unique constraint)
- `User.personal_household_id` — immutable, auto-created on registration
- `User.active_household_id` — determines current recipe/meal scope

## Frontend
- `frontend/households.html` — Household management page
- `frontend/households.js` — Create, join, switch, leave, copy invite code to clipboard, import recipes

## Tools / Scripts
- `execution/api/routers/households.py` — All household endpoints
- `execution/api/schemas.py` — `HouseholdCreate`, `HouseholdOut`, `HouseholdMembershipOut`
- `execution/db/models.py` — `Household`, `HouseholdMember`, `generate_unique_invite_code()`

## Edge Cases & Learnings
- Joining a household you're already a member of is a no-op (no duplicate membership created), but still switches your active household.
- Leaving your personal household is blocked (400 error).
- Leaving your active household auto-switches you back to your personal household.
- Orphan cleanup only deletes households with zero members AND zero recipes.
- Switching to a household you're not a member of returns 403.
