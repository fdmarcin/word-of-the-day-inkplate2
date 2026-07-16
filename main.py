"""
Render today's word and copy the output to the Apache2 serving directory.
"""

import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_PNG = BASE_DIR / "output" / "today.png"
SERVE_PNG = Path("/var/www/html/today.png")


def main():
    result = subprocess.run(
        [sys.executable, BASE_DIR / "render" / "render.py"],
        check=False,
    )

    if result.returncode != 0:
        print("Render failed, aborting.")
        sys.exit(result.returncode)

    shutil.copy(OUTPUT_PNG, SERVE_PNG)
    print(f"  Copied to {SERVE_PNG}")


if __name__ == "__main__":
    main()
