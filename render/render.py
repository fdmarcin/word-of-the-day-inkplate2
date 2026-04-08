"""
Daily render script: pick a Portuguese word, fetch its definition from
FreeDictionaryAPI, and render a 212x104 PNG for the Inkplate 2.
"""

import json
import random
import re
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
FONTS_DIR = Path(__file__).parent / "fonts"
OUTPUT_DIR = BASE_DIR / "output"

WORDS_JSON = DATA_DIR / "words.json"
HISTORY_JSON = DATA_DIR / "history.json"
OVERRIDES_JSON = DATA_DIR / "overrides.json"
OUTPUT_PNG = OUTPUT_DIR / "today.png"

FONT_ROMAN = FONTS_DIR / "Literata-VariableFont_opsz,wght.ttf"
FONT_PIXEL = FONTS_DIR / "PixelOperator.ttf"

# ---------------------------------------------------------------------------
# Display constants
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 212, 104
PADDING = 4
DIVIDER_MARGIN = 3   # gap between word bottom and divider
CONTENT_MARGIN = 4   # gap between divider and definition top

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

FONT_SIZE_WORD = 26
FONT_SIZE_POS = 13
FONT_SIZE_DEF = 13
FONT_SIZE_EXAMPLE = 13

WGHT_BOLD = 700

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

API_DICT = "https://freedictionaryapi.com/api/v1/entries/pt"
API_TATOEBA = "https://api.tatoeba.org/v1/sentences"
MAX_RETRIES = 10
TATOEBA_MIN_WORDS = 2   # ignore very short sentences
TATOEBA_MAX_WORDS = 12  # ignore sentences too long to fit the screen
TATOEBA_MIN_CHARS = 5   # don't query Tatoeba for short/ambiguous words

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def strip_parens(text: str) -> str:
    """Remove parenthetical and bracketed qualifiers from definitions and examples.
    - Leading tag: '(formal) definition text'
    - Trailing tag: 'some text (Portugal).' or 'some text [usage note]'
    Only targets short phrases (≤30 chars) to avoid stripping legitimate content."""
    # Remove leading qualifier
    text = re.sub(r"^\([^)]{1,30}\)\s*", "", text)
    # Remove trailing parenthetical or bracketed content (any length)
    text = re.sub(r"\s*\([^)]+\)\.?$", "", text)
    text = re.sub(r"\s*\[[^\]]+\]\.?$", "", text)
    return text.strip()


def pick_word(words: list, history: set) -> str | None:
    remaining = [w for w in words if w not in history]
    if not remaining:
        return None
    return random.choice(remaining)


def load_variable_font(path: Path, size: int, wght: int) -> ImageFont.FreeTypeFont:
    """Load a variable font and set its weight axis."""
    font = ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.BASIC)
    axes = font.get_variation_axes()
    values = []
    for axis in axes:
        tag = axis["name"].decode() if isinstance(axis["name"], bytes) else axis["name"]
        if tag == "wght":
            values.append(wght)
        else:
            values.append(axis["default"])
    font.set_variation_by_axes(values)
    return font


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Load a static font."""
    return ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.BASIC)


def fetch_entry(word: str) -> dict | None:
    """Fetch the first Portuguese entry for a word. Returns None on failure."""
    try:
        resp = requests.get(f"{API_DICT}/{word}", timeout=10)
    except requests.RequestException as e:
        print(f"  Network error for '{word}': {e}")
        return None

    if resp.status_code == 404:
        print(f"  '{word}' not found in FreeDictionaryAPI")
        return None
    if resp.status_code != 200:
        print(f"  Unexpected status {resp.status_code} for '{word}'")
        return None

    entries = resp.json().get("entries", [])
    if not entries:
        print(f"  No entries for '{word}'")
        return None

    return entries[0]


def extract_content(entry: dict) -> tuple[str, str, str] | None:
    """Extract (part_of_speech, definition, example) from an entry.
    Returns None if the entry lacks a usable definition."""
    pos = entry.get("partOfSpeech", "")
    senses = entry.get("senses", [])
    if not senses:
        return None

    sense = senses[0]
    definition = strip_parens(sense.get("definition", ""))
    if not definition:
        return None

    examples = sense.get("examples", [])
    example = ""
    for ex in examples:
        ex = strip_parens(ex)
        if len(ex.split()) <= TATOEBA_MAX_WORDS:
            example = ex
            break

    return pos, definition, example


def fetch_tatoeba_example(word: str) -> str:
    """Fetch a random approved example sentence from Tatoeba. Returns empty string on failure."""
    try:
        resp = requests.get(
            API_TATOEBA,
            params={"lang": "por", "q": word, "sort": "relevance", "limit": 10},
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"  Tatoeba network error for '{word}': {e}")
        return ""

    if resp.status_code != 200:
        print(f"  Tatoeba returned status {resp.status_code} for '{word}'")
        return ""

    sentences = [
        s["text"] for s in resp.json().get("data", [])
        if not s.get("is_unapproved")
        and TATOEBA_MIN_WORDS <= len(s["text"].split()) <= TATOEBA_MAX_WORDS
    ]

    if not sentences:
        print(f"  No usable Tatoeba sentences for '{word}'")
        return ""

    return random.choice(sentences)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_png(word: str, pos: str, definition: str, example: str):
    img = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(img)

    font_word = load_variable_font(FONT_ROMAN, FONT_SIZE_WORD, WGHT_BOLD)
    font_pos = load_font(FONT_PIXEL, FONT_SIZE_POS)
    font_def = load_font(FONT_PIXEL, FONT_SIZE_DEF)
    font_ex = load_font(FONT_PIXEL, FONT_SIZE_EXAMPLE)

    max_width = WIDTH - PADDING * 2

    # Word (red, bold)
    draw.text((PADDING, PADDING), word, font=font_word, fill=RED)

    # Part of speech (black, pixel, baseline-aligned with word)
    word_bbox = font_word.getbbox(word)
    pos_bbox = font_pos.getbbox(pos)
    pos_x = PADDING + word_bbox[2] + 5
    pos_y = PADDING + word_bbox[3] - pos_bbox[3]
    draw.text((pos_x, pos_y), pos, font=font_pos, fill=BLACK)

    # Divider — positioned below the word's actual rendered bottom
    divider_y = PADDING + word_bbox[3] + DIVIDER_MARGIN
    draw.line([(PADDING, divider_y), (WIDTH - PADDING, divider_y)], fill=(170, 170, 170), width=1)

    # Definition
    y = divider_y + CONTENT_MARGIN
    line_h_def = FONT_SIZE_DEF + 3
    for line in wrap_text(draw, definition, font_def, max_width):
        if y + line_h_def > HEIGHT:
            break
        draw.text((PADDING, y), line, font=font_def, fill=BLACK)
        y += line_h_def

    # Example
    if example:
        y += 2
        line_h_ex = FONT_SIZE_EXAMPLE + 2
        for line in wrap_text(draw, f"\u201c{example}\u201d", font_ex, max_width):
            if y + line_h_ex > HEIGHT:
                break
            draw.text((PADDING, y), line, font=font_ex, fill=BLACK)
            y += line_h_ex

    OUTPUT_DIR.mkdir(exist_ok=True)
    img.save(OUTPUT_PNG)
    print(f"  Saved to {OUTPUT_PNG}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    words = load_json(WORDS_JSON, [])
    history = set(load_json(HISTORY_JSON, []))
    overrides = load_json(OVERRIDES_JSON, {})

    if not words:
        print("words.json is empty. Run parse_wordlist.py first.")
        sys.exit(1)

    for attempt in range(MAX_RETRIES):
        word = pick_word(words, history)
        if word is None:
            print("All words have been shown. Clear history.json to restart.")
            sys.exit(0)

        print(f"Trying '{word}' (attempt {attempt + 1}/{MAX_RETRIES})")

        if word in overrides:
            print("  Using override")
            o = overrides[word]
            pos, definition, example = o.get("pos", ""), o["definition"], o.get("example", "")
        else:
            entry = fetch_entry(word)
            if entry is None:
                history.add(word)
                save_json(HISTORY_JSON, list(history))
                continue

            result = extract_content(entry)
            if result is None:
                print(f"  No usable content for '{word}', skipping")
                history.add(word)
                save_json(HISTORY_JSON, list(history))
                continue

            pos, definition, example = result

        if not example:
            if len(word) >= TATOEBA_MIN_CHARS:
                print(f"  No example from Wiktionary, trying Tatoeba")
                example = fetch_tatoeba_example(word)
            else:
                print(f"  No example from Wiktionary, skipping Tatoeba (word too short)")

        render_png(word, pos, definition, example)
        history.add(word)
        save_json(HISTORY_JSON, list(history))
        print(f"Done: '{word}' | {pos} | {definition}")
        if example:
            print(f"      {example}")
        sys.exit(0)

    print(f"Failed to find a usable word after {MAX_RETRIES} attempts.")
    sys.exit(1)


if __name__ == "__main__":
    main()
