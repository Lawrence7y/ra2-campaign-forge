"""Read-only D-30 format gate; run from the repository root with python -I."""

import re
from pathlib import Path


REQUIRED_SECTIONS = (
    "三档权衡的实质",
    "选择与理由",
    "配额覆盖率的可接受性",
    "触发判据的下一步",
    "授权边界",
    "未背书",
    "诚实账",
)


def section_bodies(text):
    """Extract ATX heading bodies, ending at a heading of equal/lower level."""
    headings = []
    fence = None
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = None
        elif fence is None:
            match = re.match(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*$", line)
            if match:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2))
                title = re.sub(r"^\d+[.、]?\s+", "", title)
                headings.append((len(match.group(1)), title, offset, offset + len(line)))
        offset += len(line)
    bodies = {}
    for index, (level, title, _, start) in enumerate(headings):
        end = len(text)
        for next_level, _, next_start, _ in headings[index + 1:]:
            if next_level <= level:
                end = next_start
                break
        bodies.setdefault(title, []).append(text[start:end])
    return bodies


def main():
    directory = Path(__file__).resolve().parent
    names = ("RULING_D30.md", "FACTCHECK.md")
    texts = {}
    missing = []
    failures = []
    for name in names:
        path = directory / name
        try:
            texts[name] = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            missing.append(f"[1] Missing file: {path}")
        except (OSError, UnicodeError) as exc:
            failures.append(f"[1] Cannot read UTF-8 file {path}: {exc}")
        else:
            if not texts[name].strip():
                failures.append(f"[1] Empty file: {path}")

    if "RULING_D30.md" in texts:
        ruling = texts["RULING_D30.md"]
        if not re.search(r"^q1:\s*(甲|乙|丙|丁|戊)\s*$", ruling, re.MULTILINE):
            failures.append("[2] RULING_D30.md: missing valid q1 line (甲/乙/丙/丁/戊)")
        sections = section_bodies(ruling)
        for title in REQUIRED_SECTIONS:
            if title not in sections:
                failures.append(f"[3] RULING_D30.md: missing section: {title}")
        requirements = (
            (4, "三档权衡的实质", ("93.98", "AKV_ZERO_HIT_NEEDLE_20261109"), False),
            (5, "授权边界", ("本次不授权",), True),
            (6, "未背书", ("外推", "栈采样"), True),
        )
        for number, title, words, require_all in requirements:
            bodies = sections.get(title, [])
            matches = [
                all(word in body for word in words) if require_all
                else any(word in body for word in words)
                for body in bodies
            ]
            if not any(matches):
                operator = " AND " if require_all else " OR "
                failures.append(f"[{number}] Section {title}: body must contain {operator.join(words)}")
        citations = re.findall(r"[A-Za-z0-9_./-]+\.(md|py|json):\d+", ruling)
        if len(citations) < 8:
            failures.append(f"[7] RULING_D30.md: found {len(citations)} citations; need at least 8")

    if "FACTCHECK.md" in texts and "selfBias" not in texts["FACTCHECK.md"]:
        failures.append("[8] FACTCHECK.md: missing selfBias")

    for reason in missing + failures:
        print(reason)
    if missing:
        print("FAIL (missing files)")
        return 2
    if failures:
        print("FAIL (content)")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
