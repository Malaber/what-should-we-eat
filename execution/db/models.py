"""
models.py — SQLAlchemy ORM models for the recipe management system.

Tables:
    recipes           — core recipe metadata
    instruction_steps — ordered cooking steps with optional duration
    ingredients       — recipe ingredients with quantity and unit
    tags              — reusable property tags (e.g. "high protein")
    recipe_tags       — many-to-many junction between recipes and tags
"""

from datetime import datetime, timezone
import secrets
import string

def _generate_invite_code(length=6):
    """Generate a random alphanumeric invite code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from execution.db.database import Base


# ---------- households ----------
class Household(Base):
    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    invite_code = Column(String(6), unique=True, index=True, nullable=False, default=_generate_invite_code)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    members = relationship("HouseholdMember", back_populates="household")


def generate_unique_invite_code(db, length=6, max_attempts=10):
    """Generate an invite code guaranteed unique in the households table."""
    for _ in range(max_attempts):
        code = _generate_invite_code(length)
        exists = db.query(
            db.query(Household).filter(Household.invite_code == code).exists()
        ).scalar()
        if not exists:
            return code
    raise RuntimeError("Failed to generate a unique invite code after multiple attempts")


# ---------- household_members ----------
class HouseholdMember(Base):
    __tablename__ = "household_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    household_id = Column(Integer, ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "household_id", name="uq_user_household"),
    )

    household = relationship("Household", back_populates="members")
# ---------- users ----------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    personal_household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    active_household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------- meal_plan_items ----------
class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    is_cooked = Column(Boolean, default=False)
    added_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("household_id", "recipe_id", name="uq_household_recipe_plan"),
    )

    recipe = relationship("Recipe")


# ---------- recipes ----------
class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    name = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    kcal_per_serving = Column(Float, nullable=True)
    active_cooking_time_min = Column(Integer, nullable=True)
    total_time_min = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # relationships
    instruction_steps = relationship(
        "InstructionStep",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="InstructionStep.step_number",
    )
    ingredients = relationship(
        "Ingredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )
    tags = relationship(
        "Tag",
        secondary="recipe_tags",
        back_populates="recipes",
    )


# ---------- instruction_steps ----------
class InstructionStep(Base):
    __tablename__ = "instruction_steps"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    duration_min = Column(Integer, nullable=True)

    recipe = relationship("Recipe", back_populates="instruction_steps")


# ---------- ingredients ----------
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)

    recipe = relationship("Recipe", back_populates="ingredients")


# ---------- tags ----------
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    recipes = relationship(
        "Recipe",
        secondary="recipe_tags",
        back_populates="tags",
    )


# ---------- recipe_tags (junction) ----------
class RecipeTag(Base):
    __tablename__ = "recipe_tags"

    recipe_id = Column(
        Integer,
        ForeignKey("recipes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        UniqueConstraint("recipe_id", "tag_id", name="uq_recipe_tag"),
    )
