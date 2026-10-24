"""Permanent self-service deletion; one transaction, no external services."""
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from execution.db.models import User, Household, HouseholdMember, Recipe, MealPlanItem, RecipeShare
from execution.db.passkeys import AuthFlow, AuthSession, Passkey, PasskeyAddLink


class DeleteAccount(BaseModel):
    email: str = Field(min_length=1, max_length=255)


def delete_account(db, user, confirmation):
    if confirmation.strip().casefold() != user.email.casefold():
        raise HTTPException(400, "Email confirmation does not match your account.")
    # Lock the account and affected kitchens before removing references.
    db.query(User).filter_by(id=user.id).with_for_update().one()
    household_ids = {m.household_id for m in db.query(HouseholdMember).filter_by(user_id=user.id)}
    household_ids.add(user.personal_household_id)
    for household in db.query(Household).filter(Household.id.in_(household_ids)).order_by(Household.id).with_for_update():
        others = db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household.id, HouseholdMember.user_id != user.id).count()
        references = db.query(User).filter(User.id != user.id, or_(
            User.personal_household_id == household.id, User.active_household_id == household.id)).count()
        if others or references:
            if household.id == user.personal_household_id:
                household.name = "Shared kitchen"
            continue
        db.query(RecipeShare).filter_by(household_id=household.id).delete()
        recipes = db.query(Recipe).filter_by(household_id=household.id).all()
        ids = [r.id for r in recipes]
        db.query(MealPlanItem).filter(or_(MealPlanItem.household_id == household.id, MealPlanItem.recipe_id.in_(ids))).delete(synchronize_session=False)
        for recipe in recipes:
            db.delete(recipe)
        db.flush()
    # AuthFlow uses JSON instead of an FK, so remove related ceremonies explicitly.
    for flow in db.query(AuthFlow).all():
        if str(flow.payload.get("user_id", "")) == str(user.id) or flow.payload.get("email") == user.email:
            db.delete(flow)
    db.query(PasskeyAddLink).filter_by(user_id=user.id).delete()
    db.query(PasskeyAddLink).filter_by(created_by=user.id).update({"created_by": None})
    db.query(AuthSession).filter_by(user_id=user.id).delete()
    db.query(Passkey).filter_by(user_id=user.id).delete()
    db.query(HouseholdMember).filter_by(user_id=user.id).delete()
    db.delete(user)
    db.flush()
    for hid in household_ids:
        if not db.query(HouseholdMember).filter_by(household_id=hid).count() and not db.query(User).filter(or_(User.personal_household_id == hid, User.active_household_id == hid)).count():
            db.query(Household).filter_by(id=hid).delete()
    db.commit()
