# -*- coding: utf-8 -*-
"""_slw_fix4.py — 联查报告撰写员的四情形误绑检验重放。
自建夹具于写域 _slw_fix4/（全新目录，不触碰 _sl_fixtures/ 与任何既有件），
只读 import 已验指纹的 _sl_link（a4ae4dc1…/12475），四情形各断言关键判定。
运行：python -I -X utf8 D:\\Project\\ra2-campaign-forge\\lead\\samedoc_link_20261109\\_slw_fix4.py
"""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(r"D:\Project\ra2-campaign-forge\lead\samedoc_link_20261109")
FX = HERE / "_slw_fix4"
LINK_PY = HERE / "_sl_link.py"

# 前置：被驱动的谓词件指纹必须仍为复核绑定值
h = hashlib.sha256(LINK_PY.read_bytes()).hexdigest()
assert h == "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5", h
assert LINK_PY.stat().st_size == 12475

spec = importlib.util.spec_from_file_location("_sl_link_readonly", LINK_PY)
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)

if FX.exists():
    shutil.rmtree(FX)
FX.mkdir(parents=True)

def w(rel, content: bytes):
    p = FX / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest(), Path(p).stat().st_size

results = []

def check(tag, cond, detail):
    results.append((tag, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + tag + " :: " + detail)

# ---------- 情形一：多命中（同字节双件）→ 必须放弃采集 ----------
pa = w("mtest/part_a/dup.txt", b"SAME BYTES alpha\r\n")
pb = w("mtest/part_b/dup.txt", b"SAME BYTES alpha\r\n")
sha_a, n_a = sha(pa)
sha_b, n_b = sha(pb)
check("(一)0 前置", pa != pb and sha_a == sha_b and n_a == n_b,
      f"两件路径不同 {pa.name}@part_a/part_b，hash 同值 {sha_a[:12]}…/{n_a} B")
doc1 = (f"# 多命中构造\n\n对象甲 `mtest/part_a/dup.txt`、对象乙 `mtest/part_b/dup.txt`。\n\n"
        f"被核对象 SHA256 = {sha_a}，字节数 = {n_a}\n")
r1 = sl.link(doc1, FX, sha_a, n_a)
check("(一) 多命中→放弃采集",
      r1["verdict"] == "multi" and len(r1["anchors"]) == 2
      and r1["reverify"] is None and r1["problems"] == []
      and "放弃采集" in r1["warning"] and "不采任何一者" in r1["warning"],
      f"verdict={r1['verdict']} anchors={len(r1['anchors'])} reverify={r1['reverify']} "
      f"problems={r1['problems']} warning头={r1['warning'][:48]}…")

# ---------- 情形二：重复路径（同一文件三种写法）→ 去重后唯一命中 ----------
pt = w("dedup/t_one.txt", b"dedup target body\r\n")
sha_t, n_t = sha(pt)
doc2 = (f"# 去重构造\n\n表格列 `t_one.txt`、相对列 `./t_one.txt`、行号列 `t_one.txt:5-7`。\n\n"
        f"被核对象 SHA256 = {sha_t}，字节数 = {n_t}\n")
r2 = sl.link(doc2, FX / "dedup", sha_t, n_t)
toks = [t["token"] for a in r2["anchors"] for t in a["tokens"]]
check("(二) 重复路径去重→唯一",
      r2["verdict"] == "unique" and len(r2["anchors"]) == 1
      and len(r2["anchors"][0]["tokens"]) >= 2
      and r2["reverify"]["ok"] is True and r2["problems"] == [],
      f"verdict={r2['verdict']} 不同现盘文件=1 写法={sorted(set(toks))} "
      f"回验={r2['reverify']['sha'][:12]}…/{r2['reverify']['bytes']}B ok={r2['reverify']['ok']}")

# ---------- 情形三：零命中（凭空 hex）→ 保留 R3-3b，不升级 ----------
ghost = "e" * 64
doc3 = (f"# 零命中构造\n\n唯一在盘路径 `dedup/t_one.txt`（现盘 {sha_t[:12]}…）。\n\n"
        f"被核对象 SHA256 = {ghost}，字节数 = 99\n")
r3 = sl.link(doc3, FX, ghost, 99)
check("(三) 凭空hex→零命中保留R3-3b",
      r3["verdict"] == "zero" and r3["anchors"] == [] and r3["reverify"] is None
      and r3["problems"] == [] and "绑定行缺显式路径，需人工锚定" in r3["warning"]
      and "零命中" in r3["warning"],
      f"verdict={r3['verdict']} anchors={len(r3['anchors'])} problems={r3['problems']} "
      f"warning头={r3['warning'][:44]}…")

# ---------- 情形四：相对路径解析（doc_dir → root → 原样） ----------
pl = w("rel/sub/local.txt", b"doc-dir local\r\n")
pr = w("rel/rootonly.txt", b"root-only file\r\n")
pd = w("rel/sub/both.txt", b"doc-dir wins\r\n")          # doc_dir 同名件
pro = w("rel/both.txt", b"root-side body\r\n")           # root 同名件（内容不同）
sha_l, _ = sha(pl)
sha_r, _ = sha(pr)
sha_d, n_d = sha(pd)
sha_ro, n_ro = sha(pro)
check("(四)0 前置", sha_d != sha_ro,
      f"rel/sub/both.txt={sha_d[:12]}… vs rel/both.txt={sha_ro[:12]}… 内容不同")
base = FX / "rel" / "sub"
root4 = FX / "rel"
NL = len(b"doc-dir local\r\n"); NR = len(b"root-only file\r\n")
r41 = sl.link(f"(d1) 同目录裸名 `local.txt`。\n\n被核对象 SHA256 = {sha_l}，字节数 = {NL}\n",
              base, sha_l, NL, root=root4)
r42 = sl.link(f"(d2) 根回退名 `rootonly.txt`。\n\n被核对象 SHA256 = {sha_r}，字节数 = {NR}\n",
              base, sha_r, NR, root=root4)
r43 = sl.link(f"(d3) 同名件 `both.txt`。\n\n被核对象 SHA256 = {sha_d}，字节数 = {n_d}\n",
              base, sha_d, n_d, root=root4)
r44 = sl.link(f"(d3) 同名件 `both.txt`。\n\n被核对象 SHA256 = {sha_ro}，字节数 = {n_ro}\n",
              base, sha_ro, n_ro, root=root4)
cond4 = (r41["verdict"] == "unique" and r41["anchors"][0]["path"].endswith("rel\\sub\\local.txt")
         and r42["verdict"] == "unique" and r42["anchors"][0]["path"].endswith("rel\\rootonly.txt")
         and r43["verdict"] == "unique" and r43["anchors"][0]["path"].endswith("rel\\sub\\both.txt")
         and r44["verdict"] == "zero" and r44["problems"] == [])
check("(四) 相对路径三级顺序", cond4,
      f"(d1)doc_dir→{Path(r41['anchors'][0]['path']).name} "
      f"(d2)root回退→{Path(r42['anchors'][0]['path']).name} "
      f"(d3a)同名件doc_dir优先→{Path(r43['anchors'][0]['path']).name} "
      f"(d3b)以root件hex绑定→verdict={r44['verdict']}（被doc_dir同名件遮蔽，不偷换对象）")

# problems 恒空全分支总断言（link_triple 契约）
for rr in (r1, r2, r3, r41, r42, r43, r44):
    assert rr["problems"] == [], rr
print("problems 恒为空：7/7 分支断言通过")

n_pass = sum(1 for _, ok, _ in results if ok)
print(f"RESULT {n_pass}/{len(results)} PASS")
json.dump({"results": [{"tag": t, "pass": ok, "detail": d} for t, ok, d in results],
           "driven_module": {"path": str(LINK_PY), "sha256": h, "bytes": 12475}},
          sys.stdout, ensure_ascii=False, indent=1)
print()
sys.exit(0 if n_pass == len(results) else 1)
