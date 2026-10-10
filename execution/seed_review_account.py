"""Populate an existing dedicated review account, without replacing real data."""
import argparse

from execution.db.database import SessionLocal
from execution.db.models import User, HouseholdMember, Recipe, Ingredient, InstructionStep, Tag, MealPlanItem
from execution.db.seed_recipes import RECIPES

MARKER = 'Onionary App Review sample recipe (demo data).'


def seed_review_account(db, email):
    user = db.query(User).filter_by(email=email.strip().lower(), is_active=True).one_or_none()
    if user is None or user.is_admin:
        raise ValueError('Create an active, non-admin review account in SQLAdmin first.')
    household = user.personal_household_id
    if user.active_household_id != household or db.query(HouseholdMember).filter(
        HouseholdMember.household_id == household, HouseholdMember.user_id != user.id
    ).count():
        raise ValueError('Use a dedicated personal kitchen with no other members.')
    # Serialize concurrent seed attempts on PostgreSQL; SQLite serializes writes.
    db.query(User).filter_by(id=user.id).with_for_update().one()
    existing = db.query(Recipe).filter_by(household_id=household).all()
    if existing:
        if len(existing) == len(RECIPES) and all(r.notes == MARKER for r in existing):
            return 0
        raise ValueError('Kitchen is not empty. Existing recipes will not be replaced.')
    if db.query(MealPlanItem).filter_by(household_id=household).count():
        raise ValueError('Kitchen already has planned meals; nothing changed.')
    created = []
    for sample in RECIPES:
        recipe = Recipe(household_id=household, name=sample['name'], notes=MARKER,
                        servings=2, kcal_per_serving=sample['kcal_per_serving'],
                        active_cooking_time_min=sample['active_cooking_time_min'],
                        total_time_min=sample['total_time_min'])
        recipe.ingredients = [Ingredient(name=name, quantity=quantity, unit=unit)
                              for name, quantity, unit in sample['ingredients']]
        recipe.instruction_steps = [InstructionStep(step_number=i + 1, description=description, duration_min=minutes)
                                    for i, (description, minutes) in enumerate(sample['steps'])]
        db.add(recipe)
        for name in sample['tags']:
            tag = db.query(Tag).filter_by(name=name).one_or_none()
            if tag is None:
                tag = Tag(name=name)
                db.add(tag)
                db.flush()
            recipe.tags.append(tag)
        db.flush()
        created.append(recipe)
    for index, recipe in enumerate(created[:4]):
        db.add(MealPlanItem(household_id=household, recipe_id=recipe.id, is_cooked=index == 0))
    db.commit()
    return len(created)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('email', help='Exact existing review account email')
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            count = seed_review_account(db, args.email)
        except ValueError as error:
            db.rollback()
            parser.error(str(error))
    print(f'Created {count} sample recipes.' if count else 'Sample kitchen already populated; nothing changed.')


if __name__ == '__main__':
    main()
