# Word of the day (PT)

Display a Portuguese word a day on an Inkplate 2.

Fetches definitions from [FreeDictionaryAPI](https://freedictionaryapi.com) (Wiktionary data) and example sentences from [Tatoeba](https://tatoeba.org) as a fallback.
Renders a 212×104 PNG served over HTTP, which the Inkplate fetches on a daily schedule.

## Prerequisites

- Python 3.14+
- [mise-en-place](https://mise.jdx.dev) (optional, for Python version and virtualenv management)
- Apache2 (for serving the output image)

## Setup

### Python environment

With mise:

```sh
mise install
pip install -r requirements.txt
```

Without mise, create and activate a virtualenv manually, then install dependencies:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Word list

The word list (`data/wordlist.txt`) is sourced from [Linguee's top 201-800 Portuguese words](https://www.linguee.com/portuguese-english/topportuguese/201-1000.html), saved manually and trimmed to have one word/phrase per line.
Parse it once to generate `data/words.json`:

```sh
python render/parse_wordlist.py
```

### Fonts

Font files are expected in `render/fonts/`. The active font is configured at the top of `render/render.py`.
See the commented-out alternatives in that file for the available options.

### Apache2

TODO: document vhost configuration and output directory setup.

## Running

Generate today's image:

```sh
python render/render.py
```

Output is written to `output/today.png`.

### Cron

Schedule daily generation at 03:00:

```sh
0 3 * * * /path/to/.venv/bin/python /path/to/render/render.py
```

## Inkplate configuration

TODO: document Arduino sketch, Wi-Fi setup, image URL, and deep sleep interval.

## Overrides

Some words may have missing, incorrect, or Brazilian Portuguese example sentences. Add manual substitutions to `data/overrides.json`:

```json
{
  "saudade": {
    "pos": "noun",
    "definition": "A deep emotional state of nostalgic longing for something absent.",
    "example": "Ela olhou o mar com saudade do filho."
  }
}
```

Any word present in `overrides.json` bypasses the API entirely. All three fields must be provided; `example` can be an empty string if no example is available.

```json
{
  "saudade": {
    "pos": "noun",
    "definition": "A deep emotional state of nostalgic longing for something absent.",
    "example": "Ela olhou o mar com saudade do filho."
  }
}
```

TODO: support partial overrides, where only some fields replace the API response.

## Adapting for another language

The project has minimal language-specific hardcoding.
To adapt it:

1. Replace `data/wordlist.txt` with a word list for your target language, one word or phrase per line, and run `parse_wordlist.py`.
2. In `render/render.py`, update the two API language codes at the top of the file:
   - `API_DICT` uses an ISO 639-1 code (for example, `pt` for Portuguese).
     FreeDictionaryAPI's supported languages are listed in its [documentation](https://freedictionaryapi.com).
   - The Tatoeba (used as backup source for examples) call in `fetch_tatoeba_example()` uses an ISO 639-3 code (for example, `por` for Portuguese).
     Tatoeba's supported languages are listed on their [statistics page](https://tatoeba.org/en/stats/sentences_by_language).
3. Choose a font that covers your target script, and update the font constants accordingly.

Note that FreeDictionaryAPI coverage varies significantly by language, and the Tatoeba minimum word length heuristic (`TATOEBA_MIN_CHARS`) was chosen for Portuguese.
You might want to adjust it for languages with different word length distributions.

## License

This project is licensed under the MIT license.
See [LICENSE](./LICENSE).

Font licenses are in `render/fonts/license/`.
