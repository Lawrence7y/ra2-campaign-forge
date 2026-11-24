"""Read-only mechanical checks for the D-25 ruling (standard library only)."""

import re
from pathlib import Path


HEADINGS = (
    "## 1 理由",
    "## 2 授权边界",
    "## 3 执行顺序",
    "## 4 附带三问",
    "## 5 对条目的更正",
    "## 6 未背书",
    "## 7 诚实账",
)


def section_body(text, heading):
    """Return body up to the next level-one or level-two heading."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line == heading:
            end = index + 1
            while end < len(lines) and not re.match(r"^#{1,2}(?:\s|$)", lines[end]):
                end += 1
            return "\n".join(lines[index + 1:end]).strip()
    return ""


def main():
    directory = Path(__file__).resolve().parent
    names = ("RULING_D25.md", "FACTCHECK.md")
    documents = {}
    errors = []
    missing = False

    for name in names:
        path = directory / name
        try:
            documents[name] = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"FAIL [1] 文件缺失：{path.as_posix()}")
            missing = True
        except (OSError, UnicodeError) as exc:
            errors.append(f"[1] {name} 无法读取为 UTF-8 文本：{exc}")
        else:
            if not documents[name].strip():
                errors.append(f"[1] {name} 内容为空")

    ruling = documents.get("RULING_D25.md")
    if ruling is not None:
        if not re.search(r"^verdict:\s*(A|B|C|D|SPLIT)\s*$", ruling, re.MULTILINE):
            errors.append("[2] RULING_D25.md 缺少合法 verdict 行（A/B/C/D/SPLIT）")
        lines = ruling.splitlines()
        for heading in HEADINGS:
            if heading not in lines:
                errors.append(f"[3] RULING_D25.md 缺少二级标题：{heading}")
        if "本次不授权" not in section_body(ruling, HEADINGS[1]):
            errors.append("[4] 授权边界小节正文缺少「本次不授权」")
        if not section_body(ruling, HEADINGS[5]):
            errors.append("[5] 未背书小节正文为空或小节缺失")
        count = len(re.findall(r"[A-Za-z0-9_./-]+\.(md|py|json):\d+", ruling))
        if count < 8:
            errors.append(f"[6] RULING_D25.md 引用不足 8 处（实际 {count} 处）")

    factcheck = documents.get("FACTCHECK.md")
    if factcheck is not None:
        if not factcheck.strip() or not ("selfBias" in factcheck or "自省" in factcheck):
            errors.append("[7] FACTCHECK.md 必须非空且含「selfBias」或「自省」")

    for error in errors:
        print(f"FAIL {error}")
    if missing:
        print("RESULT: FAIL (exit 2: 文件缺失)")
        return 2
    if errors:
        print("RESULT: FAIL (exit 1: 内容不合格)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
