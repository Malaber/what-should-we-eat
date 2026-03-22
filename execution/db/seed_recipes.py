"""
seed_recipes.py — Seed the database with sample recipes for development.

Usage:
    python -m execution.db.seed_recipes
"""

from execution.db.database import SessionLocal
from execution.db.models import Ingredient, InstructionStep, Recipe, Tag


RECIPES = [
    {
        "name": "Chicken Stir-Fry",
        "kcal_per_serving": 420,
        "active_cooking_time_min": 15,
        "total_time_min": 25,
        "tags": ["high protein", "quick", "asian"],
        "ingredients": [
            ("chicken breast", 300, "g"),
            ("soy sauce", 2, "tbsp"),
            ("bell pepper", 1, "piece"),
            ("garlic", 2, "cloves"),
            ("sesame oil", 1, "tbsp"),
            ("rice", 200, "g"),
        ],
        "steps": [
            ("Slice chicken breast into thin strips", 5),
            ("Mince garlic and slice bell pepper", 3),
            ("Stir-fry chicken on high heat until golden", 7),
            ("Add vegetables and garlic, cook 3 more min", 3),
            ("Drizzle soy sauce and sesame oil, toss", 2),
            ("Serve over steamed rice", None),
        ],
    },
    {
        "name": "Pasta Pomodoro",
        "kcal_per_serving": 510,
        "active_cooking_time_min": 10,
        "total_time_min": 25,
        "tags": ["vegetarian", "quick", "italian"],
        "ingredients": [
            ("spaghetti", 250, "g"),
            ("canned tomatoes", 400, "g"),
            ("garlic", 3, "cloves"),
            ("fresh basil", 10, "leaves"),
            ("olive oil", 2, "tbsp"),
            ("parmesan", 30, "g"),
        ],
        "steps": [
            ("Boil spaghetti in salted water until al dente", 10),
            ("Sauté garlic in olive oil until fragrant", 2),
            ("Add canned tomatoes, simmer 10 min", 10),
            ("Toss pasta with sauce, garnish with basil and parmesan", 3),
        ],
    },
    {
        "name": "Greek Salad Bowl",
        "kcal_per_serving": 320,
        "active_cooking_time_min": 10,
        "total_time_min": 10,
        "tags": ["low calorie", "vegetarian", "quick", "mediterranean"],
        "ingredients": [
            ("cucumber", 1, "piece"),
            ("tomatoes", 3, "pieces"),
            ("red onion", 0.5, "piece"),
            ("feta cheese", 100, "g"),
            ("kalamata olives", 50, "g"),
            ("olive oil", 2, "tbsp"),
            ("dried oregano", 1, "tsp"),
        ],
        "steps": [
            ("Dice cucumber, tomatoes and red onion", 5),
            ("Combine in bowl with olives and crumbled feta", 3),
            ("Drizzle with olive oil and sprinkle oregano", 2),
        ],
    },
    {
        "name": "Beef Tacos",
        "kcal_per_serving": 580,
        "active_cooking_time_min": 20,
        "total_time_min": 30,
        "tags": ["high protein", "mexican"],
        "ingredients": [
            ("ground beef", 400, "g"),
            ("taco seasoning", 1, "packet"),
            ("tortillas", 8, "pieces"),
            ("lettuce", 100, "g"),
            ("sour cream", 100, "g"),
            ("cheddar cheese", 80, "g"),
            ("salsa", 100, "g"),
        ],
        "steps": [
            ("Brown ground beef in a skillet", 8),
            ("Add taco seasoning with a splash of water", 2),
            ("Simmer until sauce thickens", 5),
            ("Warm tortillas in a dry pan", 3),
            ("Assemble tacos with toppings", 5),
        ],
    },
    {
        "name": "Salmon Teriyaki",
        "kcal_per_serving": 460,
        "active_cooking_time_min": 15,
        "total_time_min": 35,
        "tags": ["high protein", "asian", "omega-3"],
        "ingredients": [
            ("salmon fillets", 2, "pieces"),
            ("soy sauce", 3, "tbsp"),
            ("mirin", 2, "tbsp"),
            ("honey", 1, "tbsp"),
            ("ginger", 1, "tsp"),
            ("broccoli", 200, "g"),
            ("rice", 200, "g"),
        ],
        "steps": [
            ("Mix soy sauce, mirin, honey and ginger for glaze", 3),
            ("Marinate salmon for 15 minutes", 15),
            ("Pan-sear salmon skin-side down, 4 min per side", 8),
            ("Brush with glaze while cooking", 2),
            ("Steam broccoli and serve with rice", 5),
        ],
    },
    {
        "name": "Mushroom Risotto",
        "kcal_per_serving": 490,
        "active_cooking_time_min": 30,
        "total_time_min": 40,
        "tags": ["vegetarian", "italian", "comfort food"],
        "ingredients": [
            ("arborio rice", 300, "g"),
            ("mixed mushrooms", 250, "g"),
            ("vegetable broth", 1, "l"),
            ("white wine", 100, "ml"),
            ("parmesan", 50, "g"),
            ("butter", 30, "g"),
            ("shallot", 1, "piece"),
        ],
        "steps": [
            ("Sauté sliced mushrooms until golden, set aside", 5),
            ("Cook shallot in butter until translucent", 3),
            ("Toast arborio rice for 2 minutes", 2),
            ("Deglaze with white wine", 2),
            ("Add broth one ladle at a time, stirring", 20),
            ("Fold in mushrooms and parmesan", 3),
        ],
    },
    {
        "name": "Overnight Oats",
        "kcal_per_serving": 380,
        "active_cooking_time_min": 5,
        "total_time_min": 5,
        "tags": ["quick", "vegetarian", "meal prep", "breakfast"],
        "ingredients": [
            ("rolled oats", 80, "g"),
            ("milk", 200, "ml"),
            ("greek yogurt", 100, "g"),
            ("honey", 1, "tbsp"),
            ("mixed berries", 100, "g"),
            ("chia seeds", 1, "tbsp"),
        ],
        "steps": [
            ("Combine oats, milk, yogurt and chia seeds in a jar", 3),
            ("Stir in honey, top with berries", 2),
            ("Refrigerate overnight (at least 4h)", None),
        ],
    },
    {
        "name": "Thai Green Curry",
        "kcal_per_serving": 530,
        "active_cooking_time_min": 20,
        "total_time_min": 30,
        "tags": ["asian", "spicy"],
        "ingredients": [
            ("chicken thighs", 400, "g"),
            ("green curry paste", 3, "tbsp"),
            ("coconut milk", 400, "ml"),
            ("bamboo shoots", 100, "g"),
            ("thai basil", 15, "leaves"),
            ("jasmine rice", 250, "g"),
            ("fish sauce", 1, "tbsp"),
        ],
        "steps": [
            ("Fry curry paste in a wok until fragrant", 2),
            ("Add coconut milk and bring to simmer", 3),
            ("Add sliced chicken, cook through", 10),
            ("Stir in bamboo shoots and fish sauce", 3),
            ("Garnish with thai basil, serve over rice", 2),
        ],
    },
    {
        "name": "Caprese Flatbread",
        "kcal_per_serving": 440,
        "active_cooking_time_min": 10,
        "total_time_min": 20,
        "tags": ["vegetarian", "italian", "quick"],
        "ingredients": [
            ("flatbread", 2, "pieces"),
            ("mozzarella", 200, "g"),
            ("cherry tomatoes", 200, "g"),
            ("fresh basil", 10, "leaves"),
            ("balsamic glaze", 2, "tbsp"),
            ("olive oil", 1, "tbsp"),
        ],
        "steps": [
            ("Preheat oven to 200°C", None),
            ("Top flatbreads with sliced mozzarella and halved tomatoes", 5),
            ("Bake until cheese melts, about 8 min", 8),
            ("Drizzle with balsamic glaze, add fresh basil", 2),
        ],
    },
    {
        "name": "Lentil Soup",
        "kcal_per_serving": 290,
        "active_cooking_time_min": 15,
        "total_time_min": 40,
        "tags": ["low calorie", "vegetarian", "high protein", "comfort food"],
        "ingredients": [
            ("red lentils", 200, "g"),
            ("carrots", 2, "pieces"),
            ("onion", 1, "piece"),
            ("garlic", 3, "cloves"),
            ("cumin", 1, "tsp"),
            ("vegetable broth", 800, "ml"),
            ("lemon juice", 1, "tbsp"),
        ],
        "steps": [
            ("Dice onion, carrots and garlic", 5),
            ("Sauté in olive oil with cumin until soft", 5),
            ("Add lentils and broth, bring to boil", 3),
            ("Simmer 20 min until lentils are tender", 20),
            ("Blend partially, season with lemon juice", 3),
        ],
    },
]


def seed():
    db = SessionLocal()
    try:
        # Skip seeding if recipes already exist
        existing = db.query(Recipe).count()
        if existing > 0:
            print(f"Database already has {existing} recipes — skipping seed.")
            return

        tag_cache: dict[str, Tag] = {}

        for data in RECIPES:
            recipe = Recipe(
                name=data["name"],
                kcal_per_serving=data["kcal_per_serving"],
                active_cooking_time_min=data["active_cooking_time_min"],
                total_time_min=data["total_time_min"],
            )
            recipe.ingredients = [
                Ingredient(name=name, quantity=qty, unit=unit)
                for name, qty, unit in data["ingredients"]
            ]
            recipe.instruction_steps = [
                InstructionStep(step_number=i + 1, description=desc, duration_min=dur)
                for i, (desc, dur) in enumerate(data["steps"])
            ]

            tags = []
            for tag_name in data["tags"]:
                if tag_name not in tag_cache:
                    existing_tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if existing_tag:
                        tag_cache[tag_name] = existing_tag
                    else:
                        new_tag = Tag(name=tag_name)
                        db.add(new_tag)
                        db.flush()
                        tag_cache[tag_name] = new_tag
                tags.append(tag_cache[tag_name])
            recipe.tags = tags

            db.add(recipe)

        db.commit()
        print(f"Seeded {len(RECIPES)} recipes.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
