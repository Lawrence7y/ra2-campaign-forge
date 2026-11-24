# -*- coding: utf-8 -*-
"""_slv_count10.py — 复核员独立计数：F2D §2.3 十条绑定行的同文档联查三态。
独立实现（不复用 _sl_link.py / _f2_r11plus.py 代码）：自写正则、自写解析、自算 sha256。
输出每条：行位 hex 比对、命中文件清单、verdict；最后统计 8/10 口径。"""
import hashlib
import os
import re
import sys
import json
from pathlib import Path

REPO_ROOT = Path(r"D:\Project\ra2-campaign-forge")

# —— 我自己的正则（语义对齐被核规范 g7:152/154，代码独立重写）——
BIND_RE = re.compile(r"被核对象[^。\n]{0,160}?SHA256\s*=\s*`?([0-9a-fA-F]{64})`?")
BYTES_RE = re.compile(r"字节数\s*=\s*([\d,]+)")
COMMA = re.compile(r",")
BACKTICK_RE = re.compile(r"`([^`\n]{1,200})`")
PATHISH_RE = re.compile(
    r"(?:[A-Za-z0-9\u4e00-\u9fff_\-]+[/\\])+[A-Za-z0-9\u4e00-\u9fff_\-]+\.[A-Za-z0-9]{1,8}")
BARE_RE = re.compile(r"^[^\s`|*<>\"'\u201c\u201d\u2018\u2019\u2026]{1,200}\.[A-Za-z0-9]{1,8}$")
LNSUF_RE = re.compile(r"(?::|#)\s?L?\d+(?:\s*[-\u2013~]\s*(?::|#)?\s?L?\d+)*$")

# —— F2D_ROOT_CAUSE.md §2.3 十条（本会话实读照录，非转抄撰写人表格）——
ITEMS = [
    ("条1",  "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md", 130,
     "3343cfbe467d38f442cd9e422e691d0123fc046938c4d242f57c629bd41d4125", 26435),
    ("条2",  "lead/b2b_isolated_20261107/INTEGRATION_REPORT.md", 31,
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("条3",  "lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md", 5,
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("条4",  "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md", 51,
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    ("条5",  "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md", 52,
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("条6",  "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md", 53,
     "cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306", 22136),
    ("条7",  "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md", 228,
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    ("条8",  "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md", 229,
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("条9",  "lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md", 28,
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    ("条10", "lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md", 29,
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
]


def strip_suffixes(s):
    cands = [s]
    cur = s
    for _ in range(6):
        m = LNSUF_RE.search(cur)
        if not m:
            break
        cur = cur[: m.start()].rstrip().rstrip("/\\")
        if not cur or cur in cands:
            break
        cands.append(cur)
    return cands


def collect_tokens(text):
    """我自己的采集面：反引号整段裸路径形 + 跨度内 PATHISH 子串 + 空白分词片段
    + 全文 PATHISH 子串；含省略号的片段跳过。返回 token 集合。"""
    toks = set()

    def consider(t):
        t = t.strip()
        if not t or "\u2026" in t or "..." in t:
            return
        toks.add(t)

    for m in BACKTICK_RE.finditer(text):
        span = m.group(1)
        for v in strip_suffixes(span.strip()):
            if BARE_RE.match(v):
                consider(v)
                break
        for pm in PATHISH_RE.finditer(span):
            consider(pm.group(0))
        for frag in span.split():
            for v in strip_suffixes(frag):
                if BARE_RE.match(v):
                    consider(v)
                    break
    for pm in PATHISH_RE.finditer(text):
        consider(pm.group(0))
    return sorted(toks)


def resolve(token, doc_dir, root):
    for v in strip_suffixes(token.strip()):
        p = Path(v)
        cands = []
        if not p.is_absolute():
            cands.append(Path(doc_dir) / p)
            if root is not None:
                cands.append(Path(root) / p)
        cands.append(p)
        for c in cands:
            if c.is_file():
                return c
    return None


def main():
    cache = {}
    results = []
    for name, rel, ln, hex_exp, bytes_exp in ITEMS:
        doc = REPO_ROOT / rel
        text = doc.read_text(encoding="utf-8")
        lines = text.splitlines()
        line = lines[ln - 1] if ln - 1 < len(lines) else ""
        m = BIND_RE.search(line)
        line_hex = m.group(1) if m else None
        bm = BYTES_RE.search(line)
        bytes_line = int(COMMA.sub("", bm.group(1))) if bm else None
        row = {
            "item": name, "doc": rel, "line": ln,
            "line_is_binding": line_hex is not None,
            "line_hex_matches_F2D": (line_hex == hex_exp.lower()) if line_hex else False,
            "bytes_line": bytes_line, "bytes_matches_F2D": bytes_line == bytes_exp,
        }
        # 独立联查：全文采集 → 解析 → 去重 → 哈希比对
        toks = collect_tokens(text)
        files = {}   # normcase -> info
        for t in toks:
            hit = resolve(t, doc.parent, REPO_ROOT)
            if hit is None:
                continue
            key = os.path.normcase(os.path.abspath(str(hit)))
            if key not in files:
                b = hit.read_bytes()
                files[key] = {"path": str(hit), "sha": hashlib.sha256(b).hexdigest(),
                              "size": len(b), "tokens": []}
            files[key]["tokens"].append(t)
        matched = [f for f in files.values()
                   if f["sha"] == hex_exp.lower() and f["size"] == bytes_exp]
        row["resolved_files"] = len(files)
        row["distinct_tokens"] = len(toks)
        row["matched_files"] = [{"path": f["path"], "size": f["size"],
                                 "sha": f["sha"]} for f in matched]
        row["verdict"] = ("zero" if len(matched) == 0
                          else "unique" if len(matched) == 1 else "multi")
        results.append(row)
    n_unique = sum(1 for r in results if r["verdict"] == "unique")
    n_multi = [r["item"] for r in results if r["verdict"] == "multi"]
    n_zero = [r["item"] for r in results if r["verdict"] == "zero"]
    n_line_ok = sum(1 for r in results if r["line_hex_matches_F2D"] and r["bytes_matches_F2D"])
    out = {"line_position_check": "%d/10" % n_line_ok,
           "unique": n_unique, "multi": n_multi, "zero": n_zero,
           "auto_close": "%d/10" % n_unique, "items": results}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
