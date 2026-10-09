"""
recipe_import.py — Parse external recipe HTML into the app's recipe draft shape.
"""

from __future__ import annotations

import json
from urllib.parse import urlparse
import re
from typing import Any

from bs4 import BeautifulSoup
import httpx

from execution.api.schemas import IngredientCreate, InstructionStepCreate, RecipeDraftOut


FRACTION_MAP = {
    "¼": 0.25,
    "½": 0.5,
    "¾": 0.75,
    "⅐": 1 / 7,
    "⅑": 1 / 9,
    "⅒": 0.1,
    "⅓": 1 / 3,
    "⅔": 2 / 3,
    "⅕": 0.2,
    "⅖": 0.4,
    "⅗": 0.6,
    "⅘": 0.8,
    "⅙": 1 / 6,
    "⅚": 5 / 6,
    "⅛": 0.125,
    "⅜": 0.375,
    "⅝": 0.625,
    "⅞": 0.875,
}

KNOWN_UNITS = {
    "g", "kg", "mg", "ml", "l", "tl", "el", "cl", "dl",
    "prise", "prisen", "bund", "bundes", "zehe", "zehen",
    "stück", "stücke", "dose", "dosen", "päckchen", "becher",
    "glas", "gläser", "scheibe", "scheiben", "handvoll", "tasse",
    "tassen", "cup", "cups", "pkg", "paket", "päck.", "zweig", "zweige",
}


def parse_recipe_html(source: str, html: str, url: str | None = None) -> RecipeDraftOut:
    source_key = (source or "").strip().lower()
    if source_key != "chefkoch":
        raise ValueError(f"Unsupported import source: {source}")

    soup = BeautifulSoup(html, "html.parser")
    recipe_data = _extract_recipe_json_ld(soup)
    if recipe_data is None:
        raise ValueError("No recipe data found in the supplied HTML.")

    ingredients = [
        IngredientCreate(**_parse_ingredient_line(line))
        for line in recipe_data.get("recipeIngredient", [])
        if _clean_text(line)
    ]
    instructions, notes = _build_instruction_steps_and_notes(recipe_data.get("recipeInstructions"))
    tags = _extract_tags(recipe_data)

    nutrition = recipe_data.get("nutrition") or {}
    kcal = _parse_calories(nutrition.get("calories"))

    prep_min = _parse_duration_minutes(recipe_data.get("prepTime"))
    cook_min = _parse_duration_minutes(recipe_data.get("cookTime"))
    total_min = _parse_duration_minutes(recipe_data.get("totalTime"))
    if total_min is None and prep_min is not None and cook_min is not None:
        total_min = prep_min + cook_min

    return RecipeDraftOut(
        name=_clean_text(recipe_data.get("name")) or "Imported Recipe",
        notes=notes,
        servings=_parse_servings(recipe_data.get("recipeYield")),
        kcal_per_serving=kcal,
        active_cooking_time_min=prep_min,
        total_time_min=total_min,
        tags=tags,
        ingredients=ingredients,
        instruction_steps=instructions,
        source=source_key,
        source_url=url,
    )


def fetch_recipe_html(source: str, url: str) -> str:
    source_key = (source or "").strip().lower()
    if source_key != "chefkoch":
        raise ValueError(f"Unsupported import source: {source}")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https recipe URLs are supported.")
    if parsed.username or parsed.password:
        raise ValueError("Recipe URLs with embedded credentials are not allowed.")

    hostname = (parsed.hostname or "").lower()
    if not _is_allowed_chefkoch_host(hostname):
        raise ValueError("Only Chefkoch recipe URLs are supported right now.")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }

    try:
        with httpx.Client(follow_redirects=True, timeout=15.0, headers=headers) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        raise ValueError("Could not fetch the recipe page.") from exc

    final_host = (response.url.host or "").lower()
    if not _is_allowed_chefkoch_host(final_host):
        raise ValueError("Recipe URL redirected to an unsupported host.")
    if response.status_code >= 400:
        raise ValueError(f"Recipe source returned {response.status_code}.")

    return response.text


def _extract_recipe_json_ld(soup: BeautifulSoup) -> dict[str, Any] | None:
    for node in soup.select('script[type="application/ld+json"]'):
        raw = node.string or node.get_text(strip=True)
        if not raw:
            continue
        for payload in _load_json_candidates(raw):
            recipe = _find_recipe_object(payload)
            if recipe:
                return recipe
    return None


def _is_allowed_chefkoch_host(hostname: str) -> bool:
    return hostname == "chefkoch.de" or hostname.endswith(".chefkoch.de")


def _load_json_candidates(raw: str) -> list[Any]:
    candidates: list[Any] = []
    try:
        candidates.append(json.loads(raw))
    except json.JSONDecodeError:
        pass

    if candidates:
        return candidates

    cleaned = raw.strip()
    if cleaned.startswith("<!--"):
        cleaned = cleaned.removeprefix("<!--").removesuffix("-->").strip()
        try:
            candidates.append(json.loads(cleaned))
        except json.JSONDecodeError:
            pass
    return candidates


def _find_recipe_object(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, list):
        for item in payload:
            found = _find_recipe_object(item)
            if found:
                return found
        return None

    if not isinstance(payload, dict):
        return None

    payload_type = payload.get("@type")
    if _is_recipe_type(payload_type):
        return payload

    for key in ("@graph", "mainEntity", "itemListElement"):
        if key in payload:
            found = _find_recipe_object(payload[key])
            if found:
                return found

    return None


def _is_recipe_type(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "recipe"
    if isinstance(value, list):
        return any(isinstance(item, str) and item.lower() == "recipe" for item in value)
    return False


def _build_instruction_steps_and_notes(raw_instructions: Any) -> tuple[list[InstructionStepCreate], str | None]:
    flattened = _flatten_instruction_texts(raw_instructions)
    step_texts: list[str] = []
    note_chunks: list[str] = []

    for text in flattened:
        step, note = _split_step_and_note(text)
        if step:
            step_texts.append(step)
        if note:
            note_chunks.append(note)

    notes = "\n\n".join(chunk for chunk in note_chunks if chunk) or None
    return [
        InstructionStepCreate(step_number=index + 1, description=text, duration_min=None)
        for index, text in enumerate(step_texts)
        if text
    ], notes


def _flatten_instruction_texts(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = _clean_text(value)
        return [text] if text else []
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_flatten_instruction_texts(item))
        return items
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            text = _clean_text(value["text"])
            return [text] if text else []
        if isinstance(value.get("itemListElement"), list):
            return _flatten_instruction_texts(value["itemListElement"])
    return []


def _split_step_and_note(text: str) -> tuple[str, str | None]:
    cleaned = _clean_text(text)
    if not cleaned:
        return "", None

    for marker in ("Anmerkung:", "Nachtrag:", "Hinweis:"):
        if marker in cleaned:
            step_part, note_part = cleaned.split(marker, 1)
            step = step_part.strip(" \n:-")
            note = f"{marker} {note_part.strip()}".strip()
            return step, note

    lowered = cleaned.lower()
    if lowered.startswith(("anmerkung:", "nachtrag:", "hinweis:")):
        return "", cleaned

    return cleaned, None


def _extract_tags(recipe_data: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for key in ("keywords", "recipeCategory", "recipeCuisine"):
        value = recipe_data.get(key)
        if isinstance(value, str):
            candidates.extend(re.split(r"[,;|]", value))
        elif isinstance(value, list):
            candidates.extend(str(item) for item in value)

    seen: set[str] = set()
    tags: list[str] = []
    for candidate in candidates:
        cleaned = _clean_text(candidate)
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        tags.append(cleaned)
    return tags[:8]


def _parse_calories(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", str(value))
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _parse_duration_minutes(value: Any) -> int | None:
    if not value or not isinstance(value, str):
        return None
    match = re.fullmatch(r"P(?:\d+D)?T(?:(\d+)H)?(?:(\d+)M)?", value.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    total = hours * 60 + minutes
    return total or None


def _parse_ingredient_line(line: str) -> dict[str, Any]:
    text = _clean_text(line)
    if not text:
        return {"name": "", "quantity": None, "unit": None}

    tokens = text.split()
    quantity, consumed = _consume_quantity(tokens)
    if consumed == 0:
        return {"name": text, "quantity": None, "unit": None}

    unit = None
    if len(tokens) > consumed:
        unit_candidate = _normalize_unit(tokens[consumed])
        if unit_candidate.lower() in KNOWN_UNITS:
            unit = tokens[consumed].strip(" ,.")
            consumed += 1

    name = " ".join(tokens[consumed:]).strip(" ,-")
    if not name:
        name = text
        quantity = None
        unit = None

    return {"name": name, "quantity": quantity, "unit": unit}


def _consume_quantity(tokens: list[str]) -> tuple[float | None, int]:
    if not tokens:
        return None, 0

    values: list[float] = []
    consumed = 0
    for token in tokens[:2]:
        parsed = _parse_number_token(token)
        if parsed is None:
            break
        values.append(parsed)
        consumed += 1

    if not values:
        return None, 0

    return sum(values), consumed


def _parse_number_token(token: str) -> float | None:
    cleaned = token.strip().strip("(),;")
    if not cleaned:
        return None

    if cleaned in FRACTION_MAP:
        return FRACTION_MAP[cleaned]

    mixed_match = re.fullmatch(r"(\d+)([¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])", cleaned)
    if mixed_match:
        return float(mixed_match.group(1)) + FRACTION_MAP[mixed_match.group(2)]

    fraction_match = re.fullmatch(r"(\d+)/(\d+)", cleaned)
    if fraction_match:
        denominator = int(fraction_match.group(2))
        if denominator == 0:
            return None
        return int(fraction_match.group(1)) / denominator

    range_match = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", cleaned)
    if range_match:
        start = float(range_match.group(1).replace(",", "."))
        end = float(range_match.group(2).replace(",", "."))
        return (start + end) / 2

    number_match = re.fullmatch(r"\d+(?:[.,]\d+)?", cleaned)
    if number_match:
        return float(cleaned.replace(",", "."))

    return None


def _normalize_unit(token: str) -> str:
    return token.strip().strip(" ,.;:").lower()


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _parse_servings(value) -> float:
    """Schema.org recipeYield may be numeric, text or a list of labels."""
    for item in value if isinstance(value, list) else [value]:
        match = re.search(r"\d+(?:[.,]\d+)?", str(item or ""))
        if match:
            number = float(match.group().replace(',', '.'))
            if 0 < number <= 1_000_000:
                return number
    return 1
