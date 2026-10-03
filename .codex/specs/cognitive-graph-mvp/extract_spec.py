"""Extract authoritative sections without rewriting approved requirements."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[3]
source = root / "Cognitive_Graph_MVP_Codex_Team.md"
text = source.read_text(encoding="utf-8")
sections = {int(m.group(1)): m.group(0) for m in re.finditer(
    r"^## (\d+)\. .*?(?=^## \d+\. |\Z)", text, re.M | re.S
)}
target = Path(__file__).parent
for name, numbers in {
    "requirements.md": [2], "spec.md": [3, 4, 5, 6, 7, 8, 10],
    "design.md": [9, 11],
}.items():
    path = target / name
    if path.exists():
        raise SystemExit(f"Refusing to overwrite {path}")
    path.write_text(f"# Cognitive Graph MVP — {name[:-3]}\n\n"
                    "Authority: Cognitive_Graph_MVP_Codex_Team.md v1.1, 2026-10-03.\n"
                    "Sections below are preserved verbatim. No research gate is closed by extraction.\n\n"
                    + "\n".join(sections[n] for n in numbers), encoding="utf-8")
