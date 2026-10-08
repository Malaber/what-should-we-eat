"""
test_recipe_import.py — Unit tests for the HTML recipe import parser.

Tests the pure parsing logic (no database or server needed).
"""

import pytest
from unittest.mock import patch

import httpx

from execution.api.recipe_import import fetch_recipe_html, parse_recipe_html


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
          { "@type": "HowToStep", "text": "Alles vermengen und servieren. Anmerkung: Mit extra Zitronenabrieb servieren." }
        ]
      }
    </script>
  </head>
  <body></body>
</html>
"""


class TestParseRecipeHtml:
    def test_parses_name(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML, "https://chefkoch.de/test")
        assert r.name == "Spaghetti al Limone"

    def test_parses_nutrition(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML)
        assert r.kcal_per_serving == 540.0

    def test_parses_times(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML)
        assert r.active_cooking_time_min == 15
        assert r.total_time_min == 25

    def test_parses_tags(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML)
        assert r.tags[:3] == ["Pasta", "Schnell", "Vegetarisch"]

    def test_parses_ingredients(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML)
        assert len(r.ingredients) == 5

        spaghetti = r.ingredients[0]
        assert spaghetti.name == "Spaghetti"
        assert spaghetti.quantity == 250
        assert spaghetti.unit == "g"

        zitrone = r.ingredients[1]
        assert zitrone.name == "Zitrone"
        assert zitrone.quantity == 1
        assert zitrone.unit is None

    def test_parses_fractions(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML)
        salz = r.ingredients[3]
        assert salz.name == "Salz"
        assert salz.quantity == 0.5
        assert salz.unit == "TL"

    def test_parses_unquantified_ingredient(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML)
        pfeffer = r.ingredients[4]
        assert pfeffer.name == "etwas Pfeffer"
        assert pfeffer.quantity is None
        assert pfeffer.unit is None

    def test_parses_instructions(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML)
        assert len(r.instruction_steps) == 3
        assert r.instruction_steps[0].step_number == 1
        assert r.instruction_steps[0].description == "Pasta in Salzwasser kochen."

    def test_extracts_notes_from_instructions(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML)
        # The "Anmerkung:" is extracted into notes, the step text is truncated
        assert r.instruction_steps[2].description == "Alles vermengen und servieren."
        assert r.notes == "Anmerkung: Mit extra Zitronenabrieb servieren."

    def test_source_and_url(self):
        r = parse_recipe_html("chefkoch", SAMPLE_HTML, "https://www.chefkoch.de/test")
        assert r.source == "chefkoch"
        assert r.source_url == "https://www.chefkoch.de/test"


class TestFetchRecipeHtml:
    def test_fetch_returns_html(self):
        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def get(self, url):
                return httpx.Response(
                    200,
                    text=SAMPLE_HTML,
                    request=httpx.Request("GET", url),
                )

        with patch("execution.api.recipe_import.httpx.Client", FakeClient):
            fetched_html = fetch_recipe_html("chefkoch", "https://www.chefkoch.de/rezepte/test")
            assert "Spaghetti al Limone" in fetched_html

    def test_fetch_rejects_unsupported_host(self):
        with pytest.raises(ValueError, match="Chefkoch"):
            fetch_recipe_html("chefkoch", "https://example.com/not-allowed")


class TestParseRecipeHtmlErrors:
    def test_unsupported_source_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            parse_recipe_html("unknown_source", "<html></html>")

    def test_no_recipe_data_raises(self):
        with pytest.raises(ValueError, match="No recipe data"):
            parse_recipe_html("chefkoch", "<html><body>No JSON-LD here</body></html>")

    def test_empty_html_raises(self):
        with pytest.raises(ValueError, match="No recipe data"):
            parse_recipe_html("chefkoch", "")
