# Auction Marketplace API

A backend API for a simple auction marketplace, built with Django, Django REST Framework, and PostgreSQL. Supports user authentication, role-based permissions, auction listings, and a full bidding system with automatic auction completion.

This was built as a technical assessment with a focus on clean architecture, sound engineering decisions, and maintainable code — not a production-ready system.

---

## Tech Stack

- Python 3
- Django
- Django REST Framework
- SQLite (Django's default databse, more inpo below)
- JWT Authentication (`djangorestframework-simplejwt`)
- API Docs: `drf-spectacular` (Swagger / OpenAPI)

---

Note on databse: The brief specifies PostgresSQL as the required stack. Given the timeline, this submissions runs on Django's default SQLite database for local development ratther tha PostgresSQL. The cosebase already inculdes psycopg2-binary in requirements.txt and is staructured application code depends on SQLite-specific behaviour, so the swap is a configuration change, not a  rewrite. This is the first thing I'd fix given more.

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd auction_marketplace
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   venv/Scripts/activate  
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```

4* **Create the PostgreSQL database**
   ```bash
   createdb auction_marketplace
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional, for Django admin access)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **API Documentation**

   Once running, interactive API docs are available at:
   - Swagger UI: `http://127.0.0.1:8000/api/docs/`
   - ReDoc: `http://127.0.0.1:8000/api/redoc/`
   - Raw OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

---

## Database Design Overview

Three core models:

**User** (custom user model, `accounts` app)
- Authenticates via `email` instead of username.
- `role` field (`user` / `admin`) drives business-level permission checks.
- `is_staff` is kept separate from `role` — it preserves normal Django admin-site access without conflating it with the marketplace's own permission logic.

**Listing** (`auctions` app)
- Belongs to one `owner` (the user who created it).
- Stores `starting_price` and `current_price` as separate fields. `current_price` is denormalized (stored directly, not computed from bids on every read) so that "what's the price to beat" is a single fast read rather than an aggregation over bid history each time a listing is viewed.
- `status` (`active` / `completed` / `cancelled`) tracks auction lifecycle.
- `winner` is a nullable FK to User, set when the auction closes. Uses `SET_NULL` on delete so a listing's history isn't destroyed if a user account is later removed.

**Bid** (`auctions` app)
- Belongs to one `listing` and one `bidder`.
- Every bid is stored permanently — this *is* the bid history; there's no separate history table. Ordered by `amount` descending, so the highest bid is always `listing.bids.first()`.

**Relationships:** One `User` → many `Listings` (as owner) → many `Bids`. One `User` → many `Bids` (as bidder).

---

## Authentication Approach

JWT authentication via `djangorestframework-simplejwt`.

- **Register** (`POST /api/auth/register/`) — creates a user, no auth required.
- **Login** (`POST /api/auth/login/`) — returns an `access` and `refresh` token pair.
- **Refresh** (`POST /api/auth/login/refresh/`) — exchanges a valid refresh token for a new access token.
- **Logout** (`POST /api/auth/logout/`) — accepts a `refresh` token in the body and blacklists it via `token_blacklist`. Since JWTs are stateless by default, blacklisting the refresh token is the standard way to make "logout" actually mean something server-side — without it, a stolen token would remain valid until natural expiry regardless of logout.
- **Me** (`GET /api/auth/me/`) — returns the authenticated user's profile.

Access tokens are short-lived (30 minutes); refresh tokens last 1 day and rotate on use, with old ones blacklisted automatically (`ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`).

`role` is read-only on the user-facing serializer — a user cannot promote themselves to `admin` through the API. Admin role assignment is intentionally a manual/superuser action only (see Assumptions).

---

## Permission Model

A single custom permission class, `IsOwnerOrAdminOrReadOnly`, applied to listing detail endpoints:

- **Read access** (`GET`) — open to any authenticated user, regardless of ownership.
- **Write access** (`PATCH`, `PUT`, `DELETE`) — allowed only if the requesting user is the object's owner, or the user is an admin (`role == "admin"` or `is_staff`).

This directly implements the two stated rules: users manage only their own listings, and admins have full access. The same class is structured so it could be reused on other owned resources without modification.

Bid creation has its own validation layer (in `BidSerializer.validate()`, not the permission class) since "can this user place this bid" depends on business state — auction status, expiry, ownership, price — not just on resource ownership.

---

## Business Logic Notes

**Bidding rules** (enforced in `BidSerializer.validate()`):
1. Auction must be `active` and not expired.
2. The auction owner cannot bid on their own listing.
3. Bid amount must exceed the listing default current price.
4. On a successful bid, `Listing.current_price` updates to the new bid amount.

**Auction completion** is handled by `Listing.close_if_expired()`, called lazily whenever a listing is read or bid on. If the end time has passed and the listing is still `active`, it:
- Finds the highest bid (if any) and assigns that bidder as `winner`.
- Sets `current_price` to the winning bid amount.
- Changes `status` to `completed`.

This lazy-check approach satisfies "manual implementation is acceptable" without needing a background task scheduler. The same method is also exposed via management command (`python manage.py close_expired_auctions`) so the logic can run independently of a request, e.g. on a cron job — the duplication-free design means both call paths share identical completion logic.

---

## Assumptions Made

- Admin role assignment is a manual action (Django admin / superuser creation), not exposed through any public API endpoint, since allowing self-assignment of admin would be a real security gap.
- "Manual implementation" of auction completion was interpreted as: correct without requiring Celery/cron infrastructure for this assessment, with a documented path to a scheduled-task version (see "Future Improvements").
- A listing with zero bids that expires is simply marked `completed` with no `winner` — there is no fallback "reserve not met" behavior since the spec didn't define one.
- Cancelling a listing (`status = cancelled`) is supported in the model but does not yet have a dedicated endpoint beyond the standard `DELETE`/`PATCH`.

---

## Testing

Core test coverage focuses on the highest-risk logic — the parts that are genuinely "mine" to get wrong, rather than DRF's generic CRUD machinery:
- Ownership permissions (non-owner blocked from editing, owner allowed).
- All four bidding rules (price validation, owner-cannot-bid, expired-auction rejection, current_price updates correctly).

Run with:
```bash
python manage.py test
```

---

## If Given Another Week, I Would Improve

- **Switch To PostgreSQL** Already said it all above

- **Scheduled auction closing** — replace the lazy per-request `close_if_expired()` check with a proper background task (Celery beat or `django-crontab`), so auctions close exactly on time rather than on next read/bid.
- **Expand test coverage** — add tests for serializer-level edge cases, the management command, and auction-completion winner assignment specifically (currently verified manually, not yet automated).
- **Notifications** — notify the auction owner and winning bidder when an auction completes.
- **Soft delete for listings** — preserve bid history even if a listing is later removed, instead of cascading deletes.
-