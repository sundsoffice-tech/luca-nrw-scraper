"""
Repair script for scriptname.py:
- Remove all occurrences of the bad db_router FIX block injected by auto-fix.
- Insert a single correctly indented FIX block after the db_router import block
  (inside the top-level try: that ends with `except ImportError:`).
"""

import re
from pathlib import Path

TARGET = Path("scriptname.py")
BACKUP = TARGET.with_suffix(TARGET.suffix + ".bak")

# Bad block that was duplicated and broke the syntax (unindented).
OLD_FIX_BLOCK = """# === FIX:  Ensure db_router imports are available ===
try:
    _start_scraper_run_router
except NameError:
    from luca_scraper.db_router import start_scraper_run as _start_scraper_run_router
    print("[WARN] _start_scraper_run_router was not imported, re-importing...")

try:
    _finish_scraper_run_router
except NameError:
    from luca_scraper.db_router import finish_scraper_run as _finish_scraper_run_router
    print("[WARN] _finish_scraper_run_router was not imported, re-importing...")
# === END FIX ==="""

# Correctly indented replacement block that sits inside the try: suite.
NEW_FIX_BLOCK = """
    # === FIX:  Ensure db_router imports are available ===
    try:
        _test = _start_scraper_run_router
    except NameError:
        from luca_scraper.db_router import start_scraper_run as _start_scraper_run_router
        print("[WARN] _start_scraper_run_router was not imported, re-importing...")

    try:
        _test = _finish_scraper_run_router
    except NameError:
        from luca_scraper.db_router import finish_scraper_run as _finish_scraper_run_router
        print("[WARN] _finish_scraper_run_router was not imported, re-importing...")
    # === END FIX ===

"""


def remove_bad_blocks(content: str) -> tuple[str, int]:
    """Strip every occurrence of the broken FIX block (with optional surrounding blank lines)."""
    pattern = re.compile(r"\n*" + re.escape(OLD_FIX_BLOCK) + r"\n*", flags=re.MULTILINE)
    cleaned, count = pattern.subn("\n", content)
    return cleaned, count


def insert_new_block(content: str) -> str:
    """
    Insert NEW_FIX_BLOCK after the db_router import block.
    Anchor: closing line of the import block containing finish_scraper_run and the trailing paren.
    """
    anchor = "        finish_scraper_run as _finish_scraper_run_router,\n    )"
    if NEW_FIX_BLOCK.strip() in content:
        return content  # Already inserted once.

    idx = content.find(anchor)
    if idx == -1:
        raise RuntimeError("Anchor for db_router imports not found.")

    insert_at = idx + len(anchor)
    return content[:insert_at] + NEW_FIX_BLOCK + content[insert_at:]


def main() -> None:
    content = TARGET.read_text(encoding="utf-8")

    cleaned, removed = remove_bad_blocks(content)
    if removed == 0:
        print("No bad FIX blocks were found; continuing.")
    else:
        print(f"Removed {removed} bad FIX block(s).")

    try:
        updated = insert_new_block(cleaned)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        raise

    BACKUP.write_text(content, encoding="utf-8")
    TARGET.write_text(updated, encoding="utf-8")
    print(f"Written fixed file to {TARGET} (backup: {BACKUP})")


if __name__ == "__main__":
    main()
