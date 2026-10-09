"""SQLAdmin is the operator UI; user passkey settings remain Onionary UI."""
import hashlib
import hmac
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqladmin import Admin, ModelView, expose
from sqladmin.authentication import AuthenticationBackend, login_required
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response

from execution.api.auth import SECRET_KEY
from execution.api.routers.passkeys import COOKIE, digest, now, origin, session_user
from execution.db.database import SessionLocal, engine
from execution.db.models import User, Household, HouseholdMember, generate_unique_invite_code
from execution.db.passkeys import PasskeyAddLink
from execution.passkey_links import issue_link


class AdminHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        return response


class AdminAuth(AuthenticationBackend):
    def __init__(self):
        self.middlewares = []  # Reuse revocable database passkey sessions, not another cookie.

    async def login(self, request):
        return RedirectResponse('/auth/login?next=admin', status_code=303)

    async def logout(self, request):
        return RedirectResponse('/auth/security', status_code=303)

    async def authenticate(self, request):
        with SessionLocal() as db:
            try:
                user = session_user(request, db)
            except HTTPException:
                return await self.login(request)
            if not user.is_admin:
                return Response('Administrator access required', status_code=403)
            request.state.admin_id = user.id
        csrf = hmac.new(SECRET_KEY.encode(), ('onionary-admin:' + digest(request.cookies.get(COOKIE, ''))).encode(), hashlib.sha256).hexdigest()
        request.state.admin_csrf = csrf
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            form = await request.form()
            supplied = form.get('csrf', '')
            if request.headers.get('origin') != origin() or not isinstance(supplied, str) or not hmac.compare_digest(csrf, supplied):
                return Response('Invalid form token. Reload the admin page.', status_code=403)
        return True


class OnionaryAdmin(Admin):
    @login_required
    async def index(self, request):
        return RedirectResponse(request.url_for('admin:list', identity='user'), status_code=303)


class NewAccount(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)


class UserAdmin(ModelView, model=User):
    name, name_plural = 'Account', 'Accounts'
    column_list = [User.email, User.name, User.is_admin, User.is_active, User.created_at]
    column_details_list = [User.id, *column_list]
    column_searchable_list = [User.email, User.name]
    column_sortable_list = column_list
    column_default_sort = [(User.email, False), (User.id, False)]
    form_columns = [User.email, User.name]
    page_size = 25
    page_size_options = [25, 50, 100]
    can_view_details = True
    can_edit = can_delete = can_export = False
    create_template = 'onionary_admin/create.html'
    details_template = 'onionary_admin/user_details.html'

    async def insert_model(self, request, data):
        values = NewAccount(email=data['email'].strip(), name=data['name'].strip())
        with SessionLocal() as db:
            household = Household(name=f"{values.name}'s Kitchen", invite_code=generate_unique_invite_code(db))
            db.add(household); db.flush()
            user = User(email=str(values.email).lower(), name=values.name, hashed_password='!passkey-only',
                        is_admin=False, is_active=True, personal_household_id=household.id, active_household_id=household.id)
            db.add(user)
            try:
                db.flush(); db.add(HouseholdMember(user_id=user.id, household_id=household.id)); db.commit(); db.refresh(user)
            except IntegrityError as exc:
                db.rollback(); raise ValueError('An account with this email already exists.') from exc
            db.expunge(user)
            return user

    @expose('/{pk}/passkey-add-link', methods=['POST'])
    async def generate_link(self, request):
        form = await request.form()
        with SessionLocal() as db:
            user = db.get(User, int(request.path_params['pk']))
            if user is None:
                raise HTTPException(404)
            error, link_url = None, None
            try:
                token, link = issue_link(db, user, admin_id=request.state.admin_id, hours=int(str(form.get('hours', ''))))
                link_url = f'{origin()}/auth/login#enroll={token}&identifier={link.id}'
            except ValueError as exc:
                error = str(exc)
            db.refresh(user); db.expunge(user)
        return await self.templates.TemplateResponse(request, self.details_template,
            {'model_view': self, 'model': user, 'link_url': link_url, 'error': error}, status_code=400 if error else 200)


class LinkAdmin(ModelView, model=PasskeyAddLink):
    name, name_plural = 'Passkey link', 'Passkey links'
    column_list = [PasskeyAddLink.id, PasskeyAddLink.user_id, PasskeyAddLink.created_by,
                   PasskeyAddLink.created_at, PasskeyAddLink.expires_at, PasskeyAddLink.used_at, PasskeyAddLink.revoked_at]
    column_details_list = column_list  # Never show token hashes, even in detail views.
    column_searchable_list = [PasskeyAddLink.id]
    column_sortable_list = column_list
    column_default_sort = [(PasskeyAddLink.created_at, True), (PasskeyAddLink.id, False)]
    can_create = can_edit = can_delete = can_export = False
    can_view_details = True
    page_size = 25
    page_size_options = [25, 50, 100]
    details_template = 'onionary_admin/link_details.html'

    @expose('/{pk}/revoke', methods=['POST'])
    async def revoke_link(self, request):
        with SessionLocal() as db:
            db.execute(update(PasskeyAddLink).where(PasskeyAddLink.id == request.path_params['pk'],
                PasskeyAddLink.used_at.is_(None), PasskeyAddLink.revoked_at.is_(None)).values(revoked_at=now()))
            db.commit()
        return RedirectResponse(request.url_for('admin:details', identity=self.identity, pk=request.path_params['pk']), status_code=303)


def configure_admin(app):
    admin = OnionaryAdmin(app, engine, title='Onionary administration', authentication_backend=AdminAuth(),
        templates_dir=str(Path(__file__).parent / 'admin_templates'), middlewares=[Middleware(AdminHeaders)])
    admin.add_view(UserAdmin); admin.add_view(LinkAdmin)
    return admin
