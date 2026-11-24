from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
INDEX = ROOT / "lead" / "next_re_20261117_r14" / "R17_R42_F23_FIX" / "FACT_INDEX.tsv"
OUT = ROOT / "lead" / "next_re_20261117_r14" / "R17_R43_INDEX_INTEGRITY" / "paths.tsv"


def split_top(s: str):
    out, depth, start = [], 0, 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            out.append(s[start:i].strip())
            start = i + 1
    out.append(s[start:].strip())
    return [x for x in out if x]


def base_path(raw: str):
    i = raw.find("(")
    return (raw[:i] if i >= 0 else raw).strip()


def main():
    lines = [ln for ln in INDEX.read_text(encoding="utf-8").split("\n") if ln]
    out = ["fact_id\t路径\t是否存在\t实际绝对路径"]
    for ln in lines[1:]:
        cols = ln.split("\t")
        fact, ev = cols[0], cols[3]
        for raw in split_top(ev):
            bp = base_path(raw)
            p = (ROOT / bp).resolve()
            mark = "NO"
            if p.exists():
                mark = "YES:DIR" if p.is_dir() else "YES:FILE"
            out.append("\t".join([fact, raw, mark, str(p)]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = ("\n".join(out) + "\n").encode("utf-8")
    assert b"\r" not in payload
    OUT.write_bytes(payload)
    print(f"wrote {OUT} ({len(out)-1} path checks)")


if __name__ == "__main__":
    main()
