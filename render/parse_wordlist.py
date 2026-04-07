"""
One-time script: convert data/wordlist.txt to data/words.json.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
WORDLIST_TXT = DATA_DIR / "wordlist.txt"
WORDS_JSON = DATA_DIR / "words.json"


def main():
    words = [
        line.strip()
        for line in WORDLIST_TXT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    WORDS_JSON.write_text(
        json.dumps(words, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {len(words)} words to {WORDS_JSON}")


if __name__ == "__main__":
    main()
