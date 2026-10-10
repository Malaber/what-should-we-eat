/** Explicit portable tokens; never infer percentages from ordinary recipe prose. */
function resolveIngredientPlaceholders(text, ingredients, multiplier = 1, locale = document.documentElement.lang) {
  if (!Number.isFinite(multiplier) || multiplier <= 0) return text;
  return text.replace(/\{\{([^{}|]+)\|(\d+(?:[.,]\d+)?)%\}\}/g, (token, name, raw) => {
    const percent = Number(raw.replace(',', '.'));
    const matches = ingredients.filter(i => i.name.toLowerCase() === name.trim().toLowerCase());
    if (percent > 100 || matches.length !== 1) return token;
    const ingredient = matches[0];
    if (ingredient.quantity == null || !Number.isFinite(Number(ingredient.quantity)) || Number(ingredient.quantity) <= 0) return token;
    const amount = Number(ingredient.quantity) * multiplier * percent / 100;
    if (!Number.isFinite(amount)) return token;
    return [new Intl.NumberFormat(locale, {maximumFractionDigits: 2, useGrouping: false}).format(amount), ingredient.unit, ingredient.name].filter(Boolean).join(' ');
  });
}
