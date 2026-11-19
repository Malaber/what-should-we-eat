"""Exercise the shipped browser resolver, including unsafe/missing references."""
from pathlib import Path


def test_ingredient_placeholders(page):
    page.goto('about:blank')
    page.add_script_tag(path=str(Path(__file__).parents[3] / 'frontend/ingredient-placeholders.js'))
    rendered = page.evaluate('''() => {
      const ingredients = [{name: 'Milk', quantity: 100, unit: 'ml'}];
      return [
        resolveIngredientPlaceholders('Use {{Milk|80%}} then {{Milk|20%}}.', ingredients, 1, 'en'),
        resolveIngredientPlaceholders('{{Milk|80%}}', ingredients, 1.583945, 'en'),
        resolveIngredientPlaceholders('{{Milk|101%}} {{Unknown|20%}}', ingredients, 1, 'en'),
        resolveIngredientPlaceholders('{{Milk|80%}}', [...ingredients, ...ingredients], 1, 'en'),
        resolveIngredientPlaceholders('Heat {{Milk|80%}} for {{time|2m30s}}.', ingredients, 2, 'en')
      ];
    }''')
    assert rendered == ['Use 80 ml Milk then 20 ml Milk.', '126.72 ml Milk',
                        '{{Milk|101%}} {{Unknown|20%}}', '{{Milk|80%}}',
                        'Heat 160 ml Milk for 2 min 30 sec.']
