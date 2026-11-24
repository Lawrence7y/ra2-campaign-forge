"""Read-only D-26 gate. Run from the repository root: python -I <this script>."""

from pathlib import Path
import re
import sys


DIRECTORY = Path("lead/d26_ruling_20261106")
REQUIRED_HEADINGS = (
    "D-13 理由",
    "D-14 理由",
    "授权边界",
    "执行顺序与后续",
    "对条目的更正",
    "未背书",
    "诚实账",
)
REFERENCE = re.compile(r"[A-Za-z0-9_./-]+\.(md|py|json):\d+")


def sections(text):
    """Collect level-two heading bodies, allowing optional numeric prefixes."""
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
            current.append(line)
    return {title: ["\n".join(body).strip() for body in bodies]
            for title, bodies in result.items()}


def main():
    paths = {name: DIRECTORY / name for name in ("RULING_D26.md", "FACTCHECK.md")}
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

    ruling = documents["RULING_D26.md"]
    lines = ruling.splitlines()
    for key, choices in (("d13", "A|C|PAUSE"), ("d14", "A|B|C")):
        pattern = re.compile(rf"{key}:\s*({choices})\s*")
        valid = sum(pattern.fullmatch(line) is not None for line in lines)
        declarations = sum(re.match(rf"^{key}:", line) is not None for line in lines)
        if valid != 1 or declarations != 1:
            errors.append(f"[2] {key} 须有且仅有一行合法裁决 ({choices}); "
                          f"合法行数={valid}, 声明行数={declarations}")

    bodies = sections(ruling)
    for title in REQUIRED_HEADINGS:
        if title not in bodies:
            errors.append(f"[3] 缺少二级标题: {title}")

    if not any("本次不授权" in body for body in bodies.get("授权边界", [])):
        errors.append("[4] 授权边界小节正文须包含「本次不授权」")
    if not any("勘误" in body and "挂账" in body
               for body in bodies.get("执行顺序与后续", [])):
        errors.append("[5] 执行顺序与后续小节正文须同时包含「勘误」与「挂账」")
    if not any(bodies.get("未背书", [])):
        errors.append("[6] 未背书小节正文须非空")
    count = len(REFERENCE.findall(ruling))
    if count < 8:
        errors.append(f"[7] 裁决书引用须至少 8 处，实际 {count} 处")
    factcheck = documents["FACTCHECK.md"]
    if "selfBias" not in factcheck and "自省" not in factcheck:
        errors.append("[8] FACTCHECK.md 须包含 selfBias 或「自省」")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS: D-26 八项机械检查通过")
    return 0


if __name__ == "__main__":
    # Keep Chinese diagnostics readable under redirected Windows console output.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
