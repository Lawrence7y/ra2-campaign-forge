#!/usr/bin/env python3
"""Q2 定稿 v4：全文读，逐件给"为什么两种信号都弱"的可复算证据。

分类按卡 §二 Q2 字面口径（互斥、按序）：
  ① 空文件/仅表头  ② 纯 JSON（无地址）  ③ 纯日志行（无地址无横幅）  ④ 含地址 <60%  ⑤ 其他
地址行 = 行内含 0x[0-9A-F]{6,8} 或 行首为 8 位裸十六进制（004A80D0）。
"""
import csv, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R91_T1_TIE152")
CAP = 512 * 1024

ADDR = re.compile(r"0x[0-9A-Fa-f]{6,8}")
BARE8 = re.compile(r"^\s*[0-9A-F]{8}\s")
PROC_HINT = re.compile(
    r"pass(ed)?\s*[=:]\s*(True|False|OK)|\bPASS\b|\bFAIL\b|exit\s*code|returncode|Traceback|"
    r"run_id|RUN_ID|elapsed|\bseconds\b|ms/frame|cpu/frame|duration|\[PROGRESS|"
    r"20\d\d[-/]\d\d[-/]\d\d|^\[\d{2}:\d{2}", re.I | re.M)
SEP = re.compile(r"^\s*(=|#|-|\*|~|\+){3,}\s*$")
CN = re.compile(r"[\u4e00-\u9fff]")


def read_all(rel):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    n = os.path.getsize(p)
    with open(p, "rb") as f:
        return f.read(CAP), n


def try_json(txt, truncated):
    s = txt.lstrip("\ufeff \t\r\n")
    if not s:
        return False
    try:
        json.loads(s)
        return True
    except Exception:
        pass
    if truncated:
        # 被截断：以 { 或 [ 起，且括号方向净正（未闭合）视为 JSON 文本
        if s[:1] in "{[" and (s.count("{") + s.count("[") - s.count("}") - s.count("]")) > 0:
            return True
    ls = [l.strip() for l in s.splitlines() if l.strip()]
    if len(ls) >= 2 and all(l[:1] in "{[" for l in ls):
        try:
            for l in ls:
                json.loads(l)
            return True
        except Exception:
            return False
    return False


def classify(rel):
    raw, nb = read_all(rel)
    truncated = nb > CAP
    txt = raw.decode("utf-8", errors="replace")
    al = txt.splitlines()
    lines = [l for l in al if l.strip()]
    fl = next((l.strip() for l in al if l.strip()), "")
    addr_lines = sum(1 for l in al if ADDR.search(l) or BARE8.search(l))
    f = {
        "bytes": nb, "nlines": len(lines),
        "cn_lines": sum(1 for l in al if CN.search(l)),
        "addr_lines": addr_lines,
        "proc_hint_lines": sum(1 for l in lines if PROC_HINT.search(l)),
        "first_line": fl[:150],
        "truncated": int(truncated),
    }
    if not lines or all(SEP.match(l) for l in lines):
        return "1_empty_or_header", f, f"非空行={len(lines)}，全为分隔线或无内容"
    if f["addr_lines"] == 0 and try_json(txt, truncated):
        return "2_json_noaddr", f, "内容可 json 解析，且 0 个地址行"
    if f["addr_lines"] == 0 and f["proc_hint_lines"] > 0:
        return "3_log_noaddr", f, f"0 地址行 + 过程迹象 {f['proc_hint_lines']} 行"
    r = addr_lines / max(1, len(lines))
    f["addr_ratio"] = round(r, 4)
    if addr_lines > 0 and r < 0.60:
        return "4_addr_lt60pct", f, f"地址行 {addr_lines}/{len(lines)} = {r:.0%}"
    return "5_other", f, f"地址行 {addr_lines}/{len(lines)} = {r:.0%} ; 过程迹象 {f['proc_hint_lines']} 行"


def main():
    src = list(csv.DictReader(open(os.path.join(OUT, "tie152.tsv"), encoding="utf-8", newline=""), delimiter="\t"))
    out = []
    for r in src:
        cls, f, why = classify(r["rel"])
        rec = {"rel": r["rel"], "bytes": f["bytes"], "class": cls, "nlines": f["nlines"],
               "cn_lines": f["cn_lines"], "addr_lines": f["addr_lines"],
               "addr_ratio": f.get("addr_ratio", 0.0),
               "proc_hint_lines": f["proc_hint_lines"], "truncated": f["truncated"],
               "why": why, "first_line": f["first_line"]}
        out.append(rec)
    with open(os.path.join(OUT, "q2_classes.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, delimiter="\t", fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0, []])
    for x in out:
        a = agg[x["class"]]
        a[0] += 1
        a[1] += int(x["bytes"])
        a[2].append(x)
    order = ["1_empty_or_header", "2_json_noaddr", "3_log_noaddr", "4_addr_lt60pct", "5_other"]
    print(f"TOTAL {len(out)} 件 / {sum(int(x['bytes']) for x in out)} B")
    for k in order:
        n, b, items = agg.get(k, [0, 0, []])
        print(f"{k:18s} {n:4d} 件 / {b:>9d} B")
        for rep in sorted(items, key=lambda z: -int(z["bytes"]))[:2]:
            print(f"    {rep['rel']}  {rep['bytes']} B")
            print(f"      | {rep['first_line'][:110]}")


if __name__ == "__main__":
    main()
