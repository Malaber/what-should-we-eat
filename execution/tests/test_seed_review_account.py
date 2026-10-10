import pytest
from execution.db.database import SessionLocal
from execution.db.models import User, Recipe, MealPlanItem
from execution.db.seed_recipes import RECIPES
from execution.seed_review_account import seed_review_account


def test_seed_is_scoped_repeatable_and_populates_plan(client, auth_headers, second_user_headers):
    with SessionLocal() as db:
        alice = db.query(User).filter_by(email='alice@test.com').one()
        bob = db.query(User).filter_by(email='bob@test.com').one()
        assert seed_review_account(db, alice.email) == len(RECIPES)
        assert seed_review_account(db, alice.email) == 0
        assert db.query(Recipe).filter_by(household_id=bob.personal_household_id).count() == 0
        assert db.query(MealPlanItem).filter_by(household_id=alice.personal_household_id).count() == 4
        recipe = db.query(Recipe).first()
        assert recipe.ingredients and recipe.instruction_steps and recipe.tags and recipe.servings == 2
        recipe.notes = 'My edits'
        db.commit()
        with pytest.raises(ValueError, match='not empty'):
            seed_review_account(db, alice.email)
        assert recipe.notes == 'My edits'


def test_admin_missing_and_other_active_kitchen_rejected(client, auth_headers, second_user_headers):
    with SessionLocal() as db:
        with pytest.raises(ValueError, match='non-admin'):
            seed_review_account(db, 'missing@test.com')
        user = db.query(User).filter_by(email='alice@test.com').one()
        user.is_admin = True
        db.commit()
        with pytest.raises(ValueError, match='non-admin'):
            seed_review_account(db, user.email)
        user.is_admin = False
        user.active_household_id = db.query(User).filter_by(email='bob@test.com').one().personal_household_id
        db.commit()
        with pytest.raises(ValueError, match='dedicated'):
            seed_review_account(db, user.email)
        assert db.query(Recipe).count() == 0
