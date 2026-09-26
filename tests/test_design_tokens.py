"""Design-system rule (F1): raw color values live only in static/css/tokens.css."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")


def test_no_raw_colors_outside_tokens():
    hits = []
    files = [p for p in (ROOT / "static" / "css").glob("*.css") if p.name != "tokens.css"]
    files += [p for p in (ROOT / "templates").rglob("*.html") if "_preview" not in p.parts]
    for path in files:
        for n, line in enumerate(path.read_text().splitlines(), 1):
            # ignore HTML entities like &#9651; and URL fragments like url(#id-arrow)
            scrub = re.sub(r"&#\d+;|url\(#[^)]*\)|href=\"#[^\"]*\"", "", line)
            if RAW_COLOR.search(scrub):
                hits.append(f"{path.relative_to(ROOT)}:{n}: {line.strip()[:100]}")
    assert not hits, "raw colors outside tokens.css:\n" + "\n".join(hits)
