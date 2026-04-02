"""
test_recipe_import.py — Unit tests for HTML recipe import parsing.

Usage:
    ./venv/bin/python -m execution.tests.test_recipe_import
"""

from execution.api.recipe_import import parse_recipe_html


SAMPLE_HTML = """
<!doctype html>
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": "Spaghetti al Limone",
        "prepTime": "PT15M",
        "cookTime": "PT10M",
        "totalTime": "PT25M",
        "keywords": "Pasta, Schnell, Vegetarisch",
        "nutrition": { "calories": "540 kcal" },
        "recipeIngredient": [
          "250 g Spaghetti",
          "1 Zitrone",
          "2 EL Olivenöl",
          "1/2 TL Salz",
          "etwas Pfeffer"
        ],
        "recipeInstructions": [
          { "@type": "HowToStep", "text": "Pasta in Salzwasser kochen." },
          { "@type": "HowToStep", "text": "Zitronensaft mit Olivenöl verrühren." },
          { "@type": "HowToStep", "text": "Alles vermengen und servieren." }
        ]
      }
    </script>
  </head>
  <body></body>
</html>
"""


def main():
    recipe = parse_recipe_html("chefkoch", SAMPLE_HTML, "https://www.chefkoch.de/test")

    assert recipe.name == "Spaghetti al Limone"
    assert recipe.kcal_per_serving == 540.0
    assert recipe.active_cooking_time_min == 15
    assert recipe.total_time_min == 25
    assert recipe.tags[:3] == ["Pasta", "Schnell", "Vegetarisch"]

    assert len(recipe.ingredients) == 5
    assert recipe.ingredients[0].name == "Spaghetti"
    assert recipe.ingredients[0].quantity == 250
    assert recipe.ingredients[0].unit == "g"

    assert recipe.ingredients[1].name == "Zitrone"
    assert recipe.ingredients[1].quantity == 1
    assert recipe.ingredients[1].unit is None

    assert recipe.ingredients[3].name == "Salz"
    assert recipe.ingredients[3].quantity == 0.5
    assert recipe.ingredients[3].unit == "TL"

    assert recipe.ingredients[4].name == "etwas Pfeffer"
    assert recipe.ingredients[4].quantity is None
    assert recipe.ingredients[4].unit is None

    assert len(recipe.instruction_steps) == 3
    assert recipe.instruction_steps[0].step_number == 1
    assert recipe.instruction_steps[0].description == "Pasta in Salzwasser kochen."
    assert recipe.source == "chefkoch"
    assert recipe.source_url == "https://www.chefkoch.de/test"

    print("Recipe import parser test passed.")


if __name__ == "__main__":
    main()
