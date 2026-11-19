/** Explicit portable tokens. Preserve unknown and ambiguous references. */
function ingredientPlaceholderParts(text, ingredients, multiplier = 1, locale = document.documentElement.lang) {
  if (!Number.isFinite(multiplier) || multiplier <= 0) return [{text}];
  const parts = [];
  let index = 0;
  const format = new Intl.NumberFormat(locale, {maximumFractionDigits: 2, useGrouping: false});
  for (const match of text.matchAll(/\{\{([^{}|]+)\|([^{}|]+)\}\}/g)) {
    const timeMatch = match[1].trim() === 'time' && match[2].match(/^(?:(\d{1,3})h)?(?:(\d{1,4})m)?(?:(\d{1,5})s)?$/);
    if (timeMatch) {
      let seconds = Number(timeMatch[1] || 0) * 3600 + Number(timeMatch[2] || 0) * 60 + Number(timeMatch[3] || 0);
      if (seconds < 1 || seconds > 86400) continue;
      const durations = [];
      for (const [unit, count] of [['hour', 3600], ['minute', 60], ['second', 1]]) {
        const value = Math.floor(seconds / count);
        if (value) durations.push(new Intl.NumberFormat(locale, {style: 'unit', unit, unitDisplay: 'short'}).format(value));
        seconds %= count;
      }
      if (index < match.index) parts.push({text: text.slice(index, match.index)});
      parts.push({text: durations.join(' ')});
      index = match.index + match[0].length;
      continue;
    }
    if (!/^\d+(?:[.,]\d+)?%$/.test(match[2])) continue;
    const percent = Number(match[2].slice(0, -1).replace(',', '.'));
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
