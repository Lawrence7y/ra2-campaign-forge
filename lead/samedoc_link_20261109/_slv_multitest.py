# -*- coding: utf-8 -*-
"""_slv_multitest.py — 复核员自建夹具，独立复核联查谓词的三态与「多命中不选一个」。
夹具全部落本写域 _slv_fix/（不动撰写人的 _sl_fixtures/）；
只读加载被核件 _sl_link.py（hash 已另验）。python -I -X utf8 运行。"""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

HERE = Path(r"D:\Project\ra2-campaign-forge\lead\samedoc_link_20261109")
FIX = HERE / "_slv_fix"

spec = importlib.util.spec_from_file_location("_sl_link_mod_v", HERE / "_sl_link.py")
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)

out = []


def check(name, cond, detail):
    out.append({"case": name, "pass": bool(cond), "detail": detail})
    print("[%s] %s :: %s" % ("PASS" if cond else "FAIL", name, detail))


def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


if FIX.exists():
    shutil.rmtree(FIX)

# ===== A. 多命中构造：同文档两个不同文件同 hash（含行号后缀引用变体）=====
payload = "_slv reviewer multi-hit fixture payload 2026-11-09 reviewer-GLM\n" * 3
fa = FIX / "mtest" / "part_a" / "dup_same.bin"
fb = FIX / "mtest" / "part_b" / "dup_same.bin"
fa.parent.mkdir(parents=True, exist_ok=True)
fa.write_text(payload, encoding="utf-8")
fb.parent.mkdir(parents=True, exist_ok=True)
fb.write_text(payload, encoding="utf-8")
sha_f, n_f = sha(fa)
sha_g, n_g = sha(fb)
check("A0 前置：两件路径不同且逐字节同 hash",
      fa != fb and sha_f == sha_g and n_f == n_g,
      "%s / %s 均 = %s…/%d B" % (fa.name, fb.name, sha_f[:12], n_f))
doc_a = FIX / "mtest" / "doc_multi.md"
write(doc_a, "# _slv 多命中构造\n\n"
      "对象一 `part_a/dup_same.bin`，对象二 `part_b/dup_same.bin`，"
      "另见行号后缀引用 `part_b/dup_same.bin:1-3`。\n\n"
      "被核对象 SHA256 = %s，字节数 = %d\n" % (sha_f, n_f))
r = sl.link(doc_a.read_text(encoding="utf-8"), doc_a.parent, sha_f, n_f, root=None)
paths = sorted(a["path"] for a in r["anchors"])
probs, warns, rec = sl.link_triple(doc_a.read_text(encoding="utf-8"), doc_a.parent,
                                   sha_f, n_f, root=None)
check("A1 两现盘文件同 hash → verdict=multi 且列出 2 锚",
      r["verdict"] == "multi" and len(r["anchors"]) == 2,
      "verdict=%s anchors=%d %s" % (r["verdict"], len(r["anchors"]), paths))
check("A2 多命中不选一个：link_triple 的 rec.path=None / rec.match=None / reverify 未设",
      rec.get("path") is None and rec.get("match") is None and r.get("reverify") is None,
      "rec.path=%r rec.match=%r reverify=%r" % (rec.get("path"), rec.get("match"), r.get("reverify")))
check("A3 多命中走 warning 且 problems 恒空",
      probs == [] and "多命中" in warns[0] and "放弃采集" in warns[0],
      "problems=%r warning=%s…" % (probs, warns[0][:70]))

# ===== B. 同一文件三种写法 → 文件级去重后 unique =====
t1 = FIX / "dtest" / "target_one.txt"
write(t1, "_slv dedup fixture target one\n")
sha_t, n_t = sha(t1)
doc_b = FIX / "dtest" / "doc_dedup.md"
write(doc_b, "| 件 | hash |\n| `target_one.txt` | `%s` |\n"
      "另见 `./target_one.txt` 与 `target_one.txt:5-7`。\n"
      "被核对象 SHA256 = %s，字节数 = %d\n" % (sha_t, sha_t, n_t))
r = sl.link(doc_b.read_text(encoding="utf-8"), doc_b.parent, sha_t, n_t, root=None)
check("B1 三种写法去重后唯一命中且回验 MATCH",
      r["verdict"] == "unique" and len(r["anchors"]) == 1 and r["reverify"]["ok"]
      and Path(r["reverify"]["path"]) == t1.resolve(),
      "verdict=%s anchor=%s tokens=%d" % (r["verdict"], r["reverify"]["path"],
                                          len(r["anchors"][0]["tokens"])))

# ===== B2. 声明字节数不符 → 不得命中（ok_len 生效）=====
r = sl.link(doc_b.read_text(encoding="utf-8"), doc_b.parent, sha_t, n_t + 1, root=None)
check("B2 hash 符但声明字节数不符 → 零命中（不误采）",
      r["verdict"] == "zero",
      "verdict=%s（hex 同值、bytes_decl=%d ≠ 现盘 %d）" % (r["verdict"], n_t + 1, n_t))

# ===== C. 绑定 hex 现盘不存在 → zero + 保留 R3-3b =====
marker = hashlib.sha256(b"_slv marker hex: fabricated, on-disk nowhere 2026-11-09").hexdigest()
doc_c = FIX / "dtest" / "doc_zero.md"
write(doc_c, "现盘另有他件 `target_one.txt`（hash 与绑定行无关）。\n"
      "被核对象 SHA256 = %s，字节数 = 1\n" % marker)
r = sl.link(doc_c.read_text(encoding="utf-8"), doc_c.parent, marker, 1, root=None)
check("C1 凭空 hex → zero 且保留原 R3-3b 警告",
      r["verdict"] == "zero" and "绑定行缺显式路径" in r["warning"] and "零命中" in r["warning"],
      "verdict=%s warning=%s…" % (r["verdict"], r["warning"][:60]))
probs, warns, rec = sl.link_triple(doc_c.read_text(encoding="utf-8"), doc_c.parent,
                                   marker, 1, root=None)
check("C2 zero 分支 problems 恒空",
      probs == [] and rec["tier"] is None and rec["match"] is None,
      "problems=%r tier=%r match=%r" % (probs, rec["tier"], rec["match"]))

# ===== D. doc_dir → root 解析顺序与同名遮蔽 =====
write(FIX / "ordr" / "docdir" / "decoy.txt", "DOC_DIR copy bytes\n")
write(FIX / "ordr" / "rootdir" / "decoy.txt", "ROOT copy bytes — different\n")
sha_dd, n_dd = sha(FIX / "ordr" / "docdir" / "decoy.txt")
sha_rt, n_rt = sha(FIX / "ordr" / "rootdir" / "decoy.txt")
doc_d = FIX / "ordr" / "docdir" / "doc_order.md"
write(doc_d, "对象以裸文件名给出：`decoy.txt`\n被核对象 SHA256 = %s，字节数 = %d\n" % (sha_dd, n_dd))
r = sl.link(doc_d.read_text(encoding="utf-8"), doc_d.parent, sha_dd, n_dd,
            root=FIX / "ordr" / "rootdir")
check("D1 doc_dir 优先命中",
      r["verdict"] == "unique"
      and Path(r["reverify"]["path"]) == (FIX / "ordr" / "docdir" / "decoy.txt").resolve(),
      "anchor=%s" % r["reverify"]["path"])
r = sl.link(doc_d.read_text(encoding="utf-8"), doc_d.parent, sha_rt, n_rt,
            root=FIX / "ordr" / "rootdir")
check("D2 doc_dir 同名件遮蔽 root 件 → 以 root 件 hex 绑定时如实判 zero（不偷换对象）",
      r["verdict"] == "zero",
      "verdict=%s（root 份在盘但被 doc_dir 同名件遮蔽）" % r["verdict"])

# ===== E. 三件同 hash、文档只引用其一 → unique（只锚被引用者，正确不扩大）=====
fx = FIX / "mtest" / "part_c" / "dup_third.bin"
fx.parent.mkdir(parents=True, exist_ok=True)
fx.write_text(payload, encoding="utf-8")
doc_e = FIX / "mtest" / "doc_only_one.md"
write(doc_e, "只提其一：`part_a/dup_same.bin`\n被核对象 SHA256 = %s，字节数 = %d\n" % (sha_f, n_f))
r = sl.link(doc_e.read_text(encoding="utf-8"), doc_e.parent, sha_f, n_f, root=None)
check("E1 三件同 hash 但同文档只引用一件 → unique 锚到被引用者",
      r["verdict"] == "unique" and Path(r["reverify"]["path"]).resolve() == fa.resolve(),
      "verdict=%s anchor=%s" % (r["verdict"], r["reverify"]["path"]))

n_pass = sum(1 for x in out if x["pass"])
print("=" * 90)
print("_slv_multitest: %d/%d PASS" % (n_pass, len(out)))
(FIX / "slv_multitest_out.json").write_text(
    json.dumps({"results": out}, ensure_ascii=False, indent=1), encoding="utf-8")
sys.exit(0 if n_pass == len(out) else 1)
