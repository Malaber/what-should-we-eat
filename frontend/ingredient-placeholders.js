/** Explicit portable tokens. Preserve unknown and ambiguous references. */
function ingredientPlaceholderParts(text, ingredients, multiplier = 1, locale = document.documentElement.lang) {
  if (!Number.isFinite(multiplier) || multiplier <= 0) return [{text}];
  const parts = [];
  let index = 0;
  const format = new Intl.NumberFormat(locale, {maximumFractionDigits: 2, useGrouping: false});
  for (const match of text.matchAll(/\{\{([^{}|]+)\|(\d+(?:[.,]\d+)?)%\}\}/g)) {
    const percent = Number(match[2].replace(',', '.'));
    const key = match[1].trim().toLowerCase();
    const exact = ingredients.filter(item => item.name.toLowerCase() === key);
    const matches = exact.length ? exact : ingredients.filter(item =>
      item.group_name && `${item.group_name}::${item.name}`.toLowerCase() === key);
    if (percent > 100 || matches.length !== 1) continue;
    const ingredient = matches[0];
    const quantity = Number(ingredient.quantity);
    const amount = quantity * multiplier * percent / 100;
    if (quantity <= 0 || !Number.isFinite(amount)) continue;
    if (index < match.index) parts.push({text: text.slice(index, match.index)});
    parts.push({ingredient, text: [format.format(amount), ingredient.unit, ingredient.name].filter(Boolean).join(' ')});
    index = match.index + match[0].length;
  }
  if (index < text.length || !parts.length) parts.push({text: text.slice(index)});
  return parts;
}

function resolveIngredientPlaceholders(text, ingredients, multiplier = 1, locale = document.documentElement.lang) {
  return ingredientPlaceholderParts(text, ingredients, multiplier, locale).map(part => part.text).join('');
}
