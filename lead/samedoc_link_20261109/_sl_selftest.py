# -*- coding: utf-8 -*-
"""_sl_selftest.py — 联查谓词误绑风险四情形构造验证（第四步）。

(a) 同文档两个不同文件恰好同 hash（人为构造同字节副本）→ 应判 multi、放弃采集；
(b) 同一路径在同文档出现多次（表格+正文+行号后缀引用）→ 去重后应判 unique；
(c) 绑定 hex 在同文档任何带路径项现盘重算中都不存在 → 应判 zero、保留 R3-3b；
(d) 相对路径按文档所在目录解析：d1 同目录裸文件名；d2 仅在 root 参数下存在的文件
    （root 回退）；d3 同名文件同目录与 root 各有一份、内容不同 → doc_dir 优先，
    且同目录件对 root 件构成遮蔽（root 件 hash 作绑定 hex 时判 zero——如实登记）；
    d4 仓库根回退（真实件 lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py）。
另验 (e) 行号后缀剥除（并入 b 的 `target_one.txt:5-7` 引用）。
夹具全部落本写域 _sl_fixtures/；断言全部以实跑返回值比对，输出 _sl_selftest_out.json。"""

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

HERE = Path(r"D:\Project\ra2-campaign-forge\lead\samedoc_link_20261109")
FIX = HERE / "_sl_fixtures"
REPO = Path(r"D:\Project\ra2-campaign-forge")

spec = importlib.util.spec_from_file_location("_sl_link_mod", HERE / "_sl_link.py")
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)

results = []


def check(name, cond, detail):
    results.append({"case": name, "pass": bool(cond), "detail": detail})
    print("[%s] %s :: %s" % ("PASS" if cond else "FAIL", name, detail))


def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


if FIX.exists():
    shutil.rmtree(FIX)

# ---------- (a) 两个不同文件同 hash → multi ----------
payload = "同文档联查自测夹具：双胞胎副本载荷 twin payload for multi-hit construction\n"
d1 = FIX / "multi" / "dup_alpha.txt"
d2 = FIX / "multi" / "dup_beta.txt"
d1.parent.mkdir(parents=True, exist_ok=True)
d1.write_text(payload, encoding="utf-8")
d2.write_text(payload, encoding="utf-8")
sha_a, n_a = sha(d1)
sha_b, n_b = sha(d2)
check("(a)0 前置：两构造件路径不同、hash 相同",
      d1 != d2 and sha_a == sha_b and n_a == n_b,
      "%s / %s 均 = %s…/%d B" % (d1.name, d2.name, sha_a[:12], n_a))
doc_a = FIX / "multi" / "doc_multi.md"
write(doc_a, """# 联查自测件 A：同文档两个不同文件恰好同 hash（人为构造）
被核对象 SHA256 = %s，字节数 = %d
- 候选一 `dup_alpha.txt`
- 候选二 `dup_beta.txt`
""" % (sha_a, n_a))
r = sl.link(doc_a.read_text(encoding="utf-8"), doc_a.parent, sha_a, n_a)
check("(a) multi→放弃采集", r["verdict"] == "multi" and len(r["anchors"]) == 2
      and "多命中" in r["warning"],
      "verdict=%s anchors=%d warning=%s…" % (r["verdict"], len(r["anchors"]), r["warning"][:60]))

# ---------- (b)+(e) 同一路径多次出现 → 去重后 unique ----------
t1 = FIX / "uniq" / "target_one.txt"
write(t1, "same-doc link selftest target one\n")
sha_t, n_t = sha(t1)
doc_b = FIX / "uniq" / "doc_uniq.md"
write(doc_b, """# 联查自测件 B：同路径三次出现（表格 + ./ 前缀 + 行号后缀引用）
| 件 | hash |
| `target_one.txt` | `%s` |
另见 `./target_one.txt` 与 `target_one.txt:5-7`（行号后缀引用）。
被核对象 SHA256 = %s，字节数 = %d
""" % (sha_t, sha_t, n_t))
r = sl.link(doc_b.read_text(encoding="utf-8"), doc_b.parent, sha_t, n_t)
paths = {a["path"] for a in r["anchors"]}
toks = [t["token"] for a in r["anchors"] for t in a["tokens"]]
occ = sum(len(t["lines"]) for a in r["anchors"] for t in a["tokens"])
check("(b)+(e) 同路径三次出现文件级去重后唯一命中",
      r["verdict"] == "unique" and len(paths) == 1 and r["reverify"]["ok"]
      and occ == 3,
      "verdict=%s 去重后不同现盘文件=%d 原始写法=%s 引用次数=%d 回验ok=%s"
      % (r["verdict"], len(paths), toks, occ, r["reverify"] and r["reverify"]["ok"]))

# ---------- (c) hex 无现盘对应 → zero ----------
o1 = FIX / "zero" / "other.txt"
write(o1, "zero-hit scenario other file\n")
sha_o, n_o = sha(o1)
marker = hashlib.sha256(b"_sl zero-hit marker: never on disk 2026-11-09").hexdigest()
doc_c = FIX / "zero" / "doc_zero.md"
write(doc_c, """# 联查自测件 C：绑定 hex 在同文档无任何现盘对应
现盘件 `other.txt`（hash %s…，与绑定 hex 不同）。
被核对象 SHA256 = %s，字节数 = 999999
""" % (sha_o[:12], marker))
r = sl.link(doc_c.read_text(encoding="utf-8"), doc_c.parent, marker)
check("(c) 零命中保留 R3-3b",
      r["verdict"] == "zero" and "绑定行缺显式路径" in r["warning"]
      and "零命中" in r["warning"],
      "verdict=%s warning=%s…" % (r["verdict"], r["warning"][:50]))

# ---------- (d1) 同目录裸文件名（doc_dir 解析） ----------
l1 = FIX / "res" / "sub" / "local.txt"
write(l1, "doc_dir local target d1\n")
sha_l, n_l = sha(l1)
doc_d1 = FIX / "res" / "sub" / "doc_d1.md"
write(doc_d1, "被核对象 SHA256 = %s，字节数 = %d（对象 `local.txt`）\n" % (sha_l, n_l))
r = sl.link(doc_d1.read_text(encoding="utf-8"), doc_d1.parent, sha_l, n_l)
got = r["reverify"]["path"] if r["reverify"] else None
check("(d1) doc_dir 解析", r["verdict"] == "unique" and got
      and Path(got) == l1.resolve(),
      "verdict=%s resolved=%s" % (r["verdict"], got))

# ---------- (d2) 仅 root 参数下存在 → root 回退 ----------
ro = FIX / "rootonly.txt"
write(ro, "exists only under fixture root\n")
sha_r, n_r = sha(ro)
doc_d2 = FIX / "res" / "sub" / "doc_d2.md"
write(doc_d2, "被核对象 SHA256 = %s，字节数 = %d（对象 `rootonly.txt`）\n" % (sha_r, n_r))
r = sl.link(doc_d2.read_text(encoding="utf-8"), doc_d2.parent, sha_r, n_r, root=FIX)
got = r["reverify"]["path"] if r["reverify"] else None
check("(d2) root 回退", r["verdict"] == "unique" and got
      and Path(got) == ro.resolve(),
      "verdict=%s resolved=%s" % (r["verdict"], got))

# ---------- (d3) 同名件 doc_dir 与 root 各一份、内容不同 → doc_dir 优先 + 遮蔽 ----------
write(FIX / "res" / "sub" / "both.txt", "SUB copy content\n")
write(FIX / "both.txt", "ROOT copy content — different bytes\n")
sha_sub, n_sub = sha(FIX / "res" / "sub" / "both.txt")
sha_root, n_root = sha(FIX / "both.txt")
doc_d3 = FIX / "res" / "sub" / "doc_d3.md"
write(doc_d3, "被核对象 SHA256 = %s，字节数 = %d（对象 `both.txt`）\n"
      % (sha_sub, n_sub))
r = sl.link(doc_d3.read_text(encoding="utf-8"), doc_d3.parent, sha_sub, n_sub, root=FIX)
got = r["reverify"]["path"] if r["reverify"] else None
check("(d3a) doc_dir 优先", r["verdict"] == "unique" and got
      and Path(got) == (FIX / "res" / "sub" / "both.txt").resolve(),
      "verdict=%s resolved=%s" % (r["verdict"], got))
r = sl.link(doc_d3.read_text(encoding="utf-8"), doc_d3.parent, sha_root, n_root, root=FIX)
check("(d3b) 同目录件遮蔽 root 件 → 如实判 zero（不越 doc_dir 反查）",
      r["verdict"] == "zero",
      "以 root 件 hex 绑定 → verdict=%s（root 件被 doc_dir 同名件遮蔽，联查不偷换对象）"
      % r["verdict"])

# ---------- (d4) 仓库根回退（真实件） ----------
cand = REPO / "lead" / "b2b_candidate_lf_20261107" / "qc151_trip.candidate_lf.py"
sha_c, n_c = sha(cand)
doc_d4 = FIX / "res" / "sub" / "doc_d4.md"
write(doc_d4, "被核对象 SHA256 = %s，字节数 = %d（对象 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`）\n"
      % (sha_c, n_c))
r = sl.link(doc_d4.read_text(encoding="utf-8"), doc_d4.parent, sha_c, n_c, root=REPO)
got = r["reverify"]["path"] if r["reverify"] else None
check("(d4) 仓库根回退（真实候选件，只读）",
      r["verdict"] == "unique" and got and Path(got) == cand.resolve(),
      "verdict=%s resolved=%s" % (r["verdict"], got))

n_pass = sum(1 for x in results if x["pass"])
print("=" * 90)
print("selftest: %d/%d PASS" % (n_pass, len(results)))
(HERE / "_sl_selftest_out.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
sys.exit(0 if n_pass == len(results) else 1)
