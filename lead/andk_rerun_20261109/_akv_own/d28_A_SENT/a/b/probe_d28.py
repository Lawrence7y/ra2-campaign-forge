"""Read-only D-28 mechanical gate; run from the repository root with python -I."""

from pathlib import Path
import re
import sys


SECTIONS = (
    "B 链下一步",
    "D 链处置",
    "优先级与并行",
    "本轮更该做的事",
    "授权边界",
    "未背书",
    "诚实账",
)
REFERENCE = re.compile(r"[A-Za-z0-9_./-]+\.(md|py|json):\d+")
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")


def section_bodies(text):
    """Collect named ATX sections, including their nested subsections."""
    lines = text.splitlines()
    headings = []
    in_fence = None
    for index, line in enumerate(lines):
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)
            if in_fence is None:
                in_fence = marker
            elif marker[0] == in_fence[0] and len(marker) >= len(in_fence):
                in_fence = None
            continue
        if in_fence is not None:
            continue
        match = HEADING.fullmatch(line)
        if match:
            title = re.sub(r"^\d+[ \t]*[.、)）:：-]?[ \t]*", "", match[2])
            headings.append((index, len(match[1]), title))
    bodies = {}
    for position, (start, level, title) in enumerate(headings):
        if title not in SECTIONS:
            continue
        end = next(
            (index for index, depth, _ in headings[position + 1:] if depth <= level),
            len(lines),
        )
        bodies.setdefault(title, []).append("\n".join(lines[start + 1:end]))
    return bodies


def main():
    root = Path(__file__).resolve().parents[2]
    directory = root / "lead" / "d28_ruling_20261106"
    texts = {}
    failures = []
    missing = []
    for name in ("RULING_D28.md", "FACTCHECK.md"):
        path = directory / name
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            missing.append(f"[1] 文件缺失：{path.relative_to(root).as_posix()}")
            continue
        except (OSError, UnicodeError) as error:
            failures.append(f"[1] {name} 无法以 UTF-8 读取：{error}")
            continue
        texts[name] = text
        if not text.strip():
            failures.append(f"[1] {name} 为空或仅含空白")

    ruling = texts.get("RULING_D28.md")
    if ruling is not None:
        lines = ruling.splitlines()
        for key, choices in (("q1", "A|B|C"), ("q2", "甲|乙|丙|丁")):
            pattern = re.compile(rf"{key}:\s*({choices})\s*")
            valid = sum(pattern.fullmatch(line) is not None for line in lines)
            declarations = sum(re.match(rf"^{key}:", line) is not None for line in lines)
            if valid != 1 or declarations != 1:
                failures.append(
                    f"[2] {key} 须恰有一行合法声明（{choices}）；"
                    f"合法 {valid} 行，声明 {declarations} 行"
                )
        bodies = section_bodies(ruling)
        for title in SECTIONS:
            if title not in bodies:
                failures.append(f"[3] 缺少小节：{title}")
        requirements = (
            (4, "D 链处置", ("AKV_ZERO_HIT_NEEDLE_20261109",), False),
            (5, "授权边界", ("本次不授权",), True),
            (6, "未背书", ("外推", "口径 B"), True),
        )
        for number, title, words, require_all in requirements:
            body = "\n".join(bodies.get(title, []))
            present = [word in body for word in words]
            if not (all(present) if require_all else any(present)):
                relation = "同时包含" if require_all else "至少包含其一"
                failures.append(f"[{number}] {title} 小节正文须{relation}：{'、'.join(words)}")
        count = len(REFERENCE.findall(ruling))
        if count < 8:
            failures.append(f"[7] RULING_D28.md 全文引用须至少 8 处，实际 {count} 处")

    factcheck = texts.get("FACTCHECK.md")
    if factcheck is not None and "selfBias" not in factcheck:
        failures.append("[8] FACTCHECK.md 缺少 selfBias 字样")
    for reason in missing + failures:
        print(f"FAIL {reason}")
    if missing:
        print("RESULT: FILE MISSING (exit 2)")
        return 2
    if failures:
        print("RESULT: FAIL (exit 1)")
        return 1
    print("PASS: D-28 全部 8 项机械检查通过 (exit 0)")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
