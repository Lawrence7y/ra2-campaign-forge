"""Read-only D-27 gate. From the repository root: python -I <this script>."""

from pathlib import Path
import re
import sys


DIRECTORY = Path("lead/d27_ruling_20261106")
REQUIRED_HEADINGS = (
    "新证据是否成立",
    "它改变了什么前提",
    "授权边界",
    "附带两问",
    "对条目的更正",
    "未背书",
    "诚实账",
)
REFERENCE = re.compile(r"[A-Za-z0-9_./-]+\.(md|py|json):\d+")


def sections(text):
    """Collect level-two bodies; accept numeric prefixes and skip fenced code."""
    result = {}
    current = None
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        heading = re.match(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*$", line)
        if heading and len(heading.group(1)) <= 2:
            current = None
            if len(heading.group(1)) == 2:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(2))
                title = re.sub(r"^\d+(?:[.、．])?[ \t]+", "", title).strip()
                current = []
                result.setdefault(title, []).append(current)
        elif current is not None:
            # Subheadings are titles, not body text.
            if not heading:
                current.append(line)
    return {title: ["\n".join(body).strip() for body in bodies]
            for title, bodies in result.items()}


def main():
    paths = {name: DIRECTORY / name for name in ("RULING_D27.md", "FACTCHECK.md")}
    missing = [path for path in paths.values() if not path.is_file()]
    if missing:
        for path in missing:
            print(f"FAIL [1] 文件缺失或不是普通文件: {path.as_posix()}")
        return 2

    errors = []
    documents = {}
    for name, path in paths.items():
        try:
            documents[name] = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            errors.append(f"[1] 无法读取 UTF-8 文件 {path.as_posix()}: {exc}")
            documents[name] = ""
        if not documents[name].strip():
            errors.append(f"[1] 文件为空或仅含空白: {path.as_posix()}")

    ruling = documents["RULING_D27.md"]
    if not re.search(r"^main:\s*(A|B|C)\s*$", ruling, re.MULTILINE):
        errors.append("[2] 裁决书须含匹配 ^main:\\s*(A|B|C)\\s*$ 的一行")

    bodies = sections(ruling)
    for title in REQUIRED_HEADINGS:
        if title not in bodies:
            errors.append(f"[3] 缺少二级标题: {title}")

    for number, title, keywords in (
        (4, "新证据是否成立", ("循环论证",)),
        (5, "授权边界", ("本次不授权",)),
        (6, "未背书", ("卡顿不存在",)),
    ):
        if not any(keyword in body for body in bodies.get(title, [])
                   for keyword in keywords):
            errors.append(f"[{number}] {title}小节正文须包含: " + " 或 ".join(keywords))

    count = len(REFERENCE.findall(ruling))
    if count < 8:
        errors.append(f"[7] 裁决书引用须至少 8 处，实际 {count} 处")
    if "selfBias" not in documents["FACTCHECK.md"]:
        errors.append("[8] FACTCHECK.md 须包含 selfBias")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"PASS: D-27 八项机械检查通过；裁决书引用 {count} 处")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
