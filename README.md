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

## License

This project is licensed under the MIT license.
See [LICENSE](./LICENSE).

Font licenses are in `render/fonts/license/`.
