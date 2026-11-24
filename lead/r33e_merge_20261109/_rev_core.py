# -*- coding: utf-8 -*-
"""_rev_core.py — J4 并入复核员·独立核脚本（核心）：
  ① 十件只读基线指纹 hashlib 重算（含 _sl_link.py 必须 = a4ae4dc1…/12475）；
  ② 三分支/原型理解的独立比对（原文逐块复制检查 + difflib 差异面）；
  ③ 自己跑 F2-d 十条（+2 附加 +1 invalid_hex），原实现 vs 并入版逐条双跑，
     断言 unique/zero 无退化、唯一允许变化为 multi→merged；
  ⑥ 声明词封闭集未扩：DECL_RE.pattern 与 _eq_proto.py:47 逐字符一致（ast 静态解析，
     ★ 绝不 exec 原型件——其顶层会写只读目录的 _eq_proto_out.json）；
  另：被核对象绑定行 hashlib 实算（_re_linked.py 全字节）。
  只读；唯一写 = 本写域 _rev_core_out.json。零真机、零采样代码。"""
import ast
import difflib
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
SL_DIR = ROOT / "lead" / "samedoc_link_20261109"
RE_DIR = ROOT / "lead" / "r33e_merge_20261109"
EQ_DIR = ROOT / "lead" / "equiv_class_20261109"
OUT = RE_DIR / "_rev_core_out.json"

EXPECT = {
    "lead/samedoc_link_20261109/_sl_link.py": ("a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5", 12475),
    "lead/samedoc_link_20261109/SAMEDOC_LINK.md": ("7e55c03861ea5eeff0adf9c02f74e2286134af2c52e507eae2216921d5b9b340", 27995),
    "lead/samedoc_link_20261109/_sl_run10_out.json": ("ed031e01e90e004dab43552085f5f6e5b5d184e7d1efa6f5699d6f76b5da454c", 36749),
    "lead/equiv_class_20261109/_eq_criteria.md": ("30355f3764242e6ad684db8ccb5c11d20fd42a8ad24d3cbf0ae7f0640f0e9a64", 19143),
    "lead/equiv_class_20261109/_eq_proto.py": ("dcb01858955f9b236f0a430430f8172bd5539a82b0aeb7014932c42c4fda4458", 7645),
    "lead/equiv_class_20261109/_eq_proto_out.json": ("c5e19d798c46ee53e5fccafbb1e082ed38f22d1aaa508061d6e617c6d30959f7", 7519),
    "lead/f2d_rootcause_20261109/_f2d_ROOTCAUSE.md": ("d12efd856c0aebe5dc8a882cb7cbd486154c7bb8602028e83a6f3ef290668b05", 21424),
    "lead/r11_f2_fix_20261109/_f2_r11plus.py": ("83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

A = []
def chk(name, cond, detail=""):
    A.append({"name": name, "ok": bool(cond), "detail": str(detail)})

# ---------- ① 十件指纹 ----------
fps = []
for rel, (sha, nb) in EXPECT.items():
    b = (ROOT / rel).read_bytes()
    got = (hashlib.sha256(b).hexdigest(), len(b))
    fps.append({"file": rel, "sha256": got[0], "bytes": got[1],
                "expect_sha": sha, "expect_bytes": nb, "match": got == (sha, nb)})
    chk("fp_" + rel.split("/")[-1], got == (sha, nb), "%s/%d" % got)
chk("ALL_TEN_FP_MATCH", all(f["match"] for f in fps))

# _sl_link.py 未被改（硬门槛）
chk("sl_link_untouched", fps[0]["match"], "%s/%d" % (fps[0]["sha256"], fps[0]["bytes"]))

# ---------- 被核对象绑定行独立实算 ----------
obj = (RE_DIR / "_re_linked.py").read_bytes()
obj_sha, obj_bytes = hashlib.sha256(obj).hexdigest(), len(obj)
chk("binding_sha", obj_sha == "7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52", obj_sha)
chk("binding_bytes", obj_bytes == 19481, obj_bytes)
notes_lines = (RE_DIR / "_re_NOTES.md").read_text(encoding="utf-8").splitlines()
bind_line = next((ln for ln in notes_lines if ln.startswith("被核对象 SHA256 = ")), None)
m = re.fullmatch(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)", bind_line or "")
chk("notes_binding_line_format_and_value",
    bool(m) and m.group(1) == obj_sha and int(m.group(2)) == obj_bytes,
    "notes_line_no=%s text=%r" % (notes_lines.index(bind_line) + 1 if bind_line else None, bind_line))

# ---------- ② 三分支 / 原型理解：原文逐块复制 + difflib ----------
orig_txt = (SL_DIR / "_sl_link.py").read_text(encoding="utf-8")
new_txt = (RE_DIR / "_re_linked.py").read_text(encoding="utf-8")
ol, nl = orig_txt.splitlines(), new_txt.splitlines()
oj, nj = "\n".join(ol), "\n".join(nl)

BLOCKS = [
    ("regex_consts", 34, 48),          # HEX64_RE.._COMMA
    ("helpers", 51, 135),              # strip_line_suffixes/_line_of/iter_path_items/resolve
    ("link_init", 142, 145),
    ("invalid_hex_early_return", 146, 149),
    ("link_body_loop", 150, 176),
    ("link_aux_stats", 177, 194),
    ("unique_branch", 195, 203),
    ("multi_branch", 204, 210),
    ("zero_branch_and_return", 211, 221),
    ("triple_rec_head", 227, 228),
    ("triple_rec_tail", 230, 230),
    ("triple_unique_branch", 231, 236),
    ("triple_return", 237, 238),
    ("main_after_usage", 244, 255),
]
for nm, s, e in BLOCKS:
    blk = "\n".join(ol[s - 1:e])
    chk("verbatim_" + nm, blk in nj, "orig %d-%d len=%d" % (s, e, len(blk)))

# 三分支行号按撰写人声称的区间做字面核对（文件:行）
chk("claimed_unique_lines", ol[194].strip() == "if len(matches) == 1:" and ol[202].strip().startswith("% (a["), "195=%r 203=%r" % (ol[194], ol[202]))
chk("claimed_multi_lines", ol[203].strip() == "elif len(matches) >= 2:" and ol[209].strip().startswith("len(matches))"), "204=%r 210=%r" % (ol[203], ol[209]))
chk("claimed_zero_lines", ol[210].strip() == "else:" and "（同文档带路径项现盘重算无一等于绑定 hex）" in ol[219], "211=%r 220=%r" % (ol[210], ol[219]))
chk("claimed_invalid_hex_lines", ":146-149" and "HEX64_RE.match" in ol[145] and ol[148].strip() == "return out", "146=%r 149=%r" % (ol[145], ol[148]))

sm = difflib.SequenceMatcher(None, ol, nl, autojunk=False)
hunks = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    hunks.append({"tag": tag, "orig": [i1 + 1, i2], "new": [j1 + 1, j2],
                  "deleted": ol[i1:i2], "added": nl[j1:j2]})
ALLOW_ORIG = [(2, 24), (140, 141), (226, 226), (229, 229), (243, 243)]  # 模块 docstring / link docstring / link_triple docstring / tier 行 / usage 行
# 纯插入 opcode 的 orig 区间为 (i1+1, i2) 的空区间（如 (49, 48)），表示"原件无删除"，
# 其插入点必须落在白名单规定的三处并入位置：原件 :75 之后（改动1）、:210 之后（改动2）、
# :236 之后（改动3）。
ALLOW_INSERT_AFTER = {48, 210, 236}
def in_allowed(h):
    tag, i1, i2 = h["tag"], h["orig"][0], h["orig"][1]
    if tag == "insert" and i2 < i1:
        return i1 - 1 in ALLOW_INSERT_AFTER or i2 in ALLOW_INSERT_AFTER
    return i2 == i1 or any(i1 >= s and i2 <= e for s, e in ALLOW_ORIG)
chk("diff_no_deletion_outside_whitelist", all(in_allowed(h) for h in hunks),
    "hunks=%d bad=%s" % (len(hunks), [h["orig"] for h in hunks if not in_allowed(h)]))
# J4 块确在 multi 分支内（warning 赋值之后、else 之前），unique/zero/invalid_hex 内无 DECL_RE 调用
j4 = [(i + 1, ln) for i, ln in enumerate(nl) if "DECL_RE.search" in ln]
chk("decl_re_search_only_in_j4_block", len(j4) == 1 and 246 <= j4[0][0] <= 289, j4)
chk("j4_block_after_multi_warning_before_else",
    "；".join(nl[241:245]).find("同文档联查多命中") >= 0 and nl[289].strip() == "else:", "L290=%r" % nl[289])

# ---------- ⑥ 声明词封闭集未扩（ast 静态解析，不执行原型件） ----------
proto_src = (EQ_DIR / "_eq_proto.py").read_text(encoding="utf-8")
proto_pat = None
for node in ast.walk(ast.parse(proto_src)):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DECL_RE" for t in node.targets):
        proto_pat = node.value.args[0].value
chk("proto_decl_re_found", proto_pat is not None, proto_pat)
chk("proto_decl_re_line47", proto_src.splitlines()[46].strip() == 'DECL_RE = re.compile(r"复制自|复制为|COPY_IDENTICAL\\s*=\\s*True")',
    proto_src.splitlines()[46])

def loadmod(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

SL = loadmod("_rev_sl_link", SL_DIR / "_sl_link.py")
RE = loadmod("_rev_re_linked", RE_DIR / "_re_linked.py")
chk("decl_vocab_identical", RE.DECL_RE.pattern == proto_pat, "%r vs %r" % (RE.DECL_RE.pattern, proto_pat))
chk("decl_vocab_source_line_identical",
    nl[80].strip() == proto_src.splitlines()[46].strip(), "%r vs %r" % (nl[80], proto_src.splitlines()[46]))
# 纯等同词/非封闭词都不命中
for w in ["逐字节同一", "逐字节相同", "完全相同", "内容一致", "完全一致", "同一内容", "COPY_IDENTICAL = False"]:
    chk("vocab_reject_" + w, not RE.DECL_RE.search(w))
for w in ["复制自", "复制为", "COPY_IDENTICAL = True", "COPY_IDENTICAL=True"]:
    chk("vocab_accept_" + w, bool(RE.DECL_RE.search(w)))

# ---------- ③ 自己跑 10 条（+2 附加 +1 invalid_hex） ----------
MOTHER = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
CAND = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
SPEC = "cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306"
R1 = "3343cfbe467d38f442cd9e422e691d0123fc046938c4d242f57c629bd41d4125"
A_RES = ROOT / "lead" / "a_residual_n1_20261108" / "A_RESIDUAL_REFERENCES.md"
IR = ROOT / "lead" / "b2b_isolated_20261107" / "INTEGRATION_REPORT.md"
IE = ROOT / "lead" / "b2b_isolated_20261107" / "_integ_INTEGRATION_REPORT.md"
BE = ROOT / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md"
N4 = ROOT / "lead" / "bexec_n4_20261108" / "_n4_SPEC_N4_B2B_MATRIX.md"
TEN = [
    ("t1", A_RES, 130, R1), ("t2", IR, 31, CAND), ("t3", IE, 5, CAND),
    ("t4", BE, 51, MOTHER), ("t5", BE, 52, CAND), ("t6", BE, 53, SPEC),
    ("t7", BE, 228, MOTHER), ("t8", BE, 229, CAND),
    ("t9", N4, 28, MOTHER), ("t10", N4, 29, CAND),
]
EXTRA = [("exA", IR, 147, CAND), ("exB", IE, 6, MOTHER)]
HEX_RE = re.compile(r"[0-9a-fA-F]{64}")

def run_one(tag, doc, line_no, hexv):
    raw = doc.read_bytes()
    text = raw.decode("utf-8")
    line = text.splitlines()[line_no - 1]
    hx = HEX_RE.findall(line)
    align = "MATCH" if hx and hx[0].lower() == hexv.lower() else "MISMATCH"
    bm = SL.BYTES_RE.search(line)
    bd = int(SL._COMMA.sub("", bm.group(1))) if bm else None
    ro = SL.link(text, doc.parent, hexv, bd)
    rm = RE.link(text, doc.parent, hexv, bd)
    so = json.dumps(ro, ensure_ascii=False, sort_keys=True)
    sm2 = json.dumps(rm, ensure_ascii=False, sort_keys=True)
    po, wo, reco = SL.link_triple(text, doc.parent, hexv, bd)
    pm, wm, recm = RE.link_triple(text, doc.parent, hexv, bd)
    return {"tag": tag, "doc": str(doc), "line": line_no, "hex": hexv, "bytes_decl": bd,
            "hex_align": align, "line_excerpt": line[:110],
            "orig": ro["verdict"], "new": rm["verdict"],
            "identical": so == sm2,
            "sha_json_orig": hashlib.sha256(so.encode("utf-8")).hexdigest(),
            "sha_json_new": hashlib.sha256(sm2.encode("utf-8")).hexdigest(),
            "triple_rec_identical": json.dumps(reco, sort_keys=True) == json.dumps(recm, sort_keys=True),
            "triple_orig_tier": reco["tier"], "triple_new_tier": recm["tier"],
            "triple_new_path": recm["path"],
            "members_n": len(rm.get("eq", {}).get("members", [])),
            "decl_lines": rm.get("eq", {}).get("decl_lines"),
            "reverify_new": rm.get("reverify")}

rows = [run_one(*t) for t in TEN]
extras = [run_one(*t) for t in EXTRA]
bad = run_one("invalid_hex", IE, 5, "zzzz-not-hex")
allrows = rows + extras + [bad]

for r in allrows:
    if r["orig"] in ("unique", "zero", "invalid_hex"):
        chk(r["tag"] + "_verdict_unchanged", r["orig"] == r["new"], r["orig"] + "->" + r["new"])
        chk(r["tag"] + "_json_identical", r["identical"])
        chk(r["tag"] + "_triple_rec_identical", r["triple_rec_identical"])
    elif r["orig"] == "multi" and r["new"] == "multi":
        chk(r["tag"] + "_multi_kept_identical", r["identical"] and r["triple_rec_identical"])
    elif r["orig"] == "multi" and r["new"] == "merged":
        chk(r["tag"] + "_multi_to_merged_only", True)
    else:
        chk(r["tag"] + "_ILLEGAL_CHANGE", False, r["orig"] + "->" + r["new"])

uq_o = [r["tag"] for r in rows if r["orig"] == "unique"]
uq_n = [r["tag"] for r in rows if r["new"] == "unique"]
z_o = [r["tag"] for r in rows if r["orig"] == "zero"]
z_n = [r["tag"] for r in rows if r["new"] == "zero"]
chk("unique_set_unchanged", uq_o == uq_n, "%s vs %s" % (uq_o, uq_n))
chk("zero_set_unchanged", z_o == z_n, "%s vs %s" % (z_o, z_n))
changed = [r["tag"] for r in allrows if not r["identical"]]
chk("only_allowed_change_multi_to_merged",
    all((r["orig"], r["new"]) == ("multi", "merged") for r in allrows if not r["identical"]),
    "changed=%s" % changed)

hist = json.loads((SL_DIR / "_sl_run10_out.json").read_text(encoding="utf-8"))
hv = {r["tag"]: r["verdict"] for r in hist["ten"]}
hk = {"t%d" % i: "条%d" % i for i in range(1, 11)}
hist_cross = [{"tag": r["tag"], "historical": hv.get(hk[r["tag"]]),
               "live_orig": r["orig"], "live_new": r["new"]} for r in rows]
chk("history_cross_all_orig", all(h["historical"] == h["live_orig"] for h in hist_cross))

summary = {"unique_orig": len(uq_o), "unique_new": len(uq_n),
           "zero_orig": len(z_o), "zero_new": len(z_n),
           "changed_rows": changed,
           "multi_to_merged": [r["tag"] for r in rows if (r["orig"], r["new"]) == ("multi", "merged")],
           "multi_kept_multi": [r["tag"] for r in rows if (r["orig"], r["new"]) == ("multi", "multi")]}

out = {"fingerprints": fps, "binding": {"sha256": obj_sha, "bytes": obj_bytes,
       "notes_line": bind_line, "notes_line_no": notes_lines.index(bind_line) + 1 if bind_line else None},
       "diff_hunks": hunks, "blocks_checked": [{"name": n, "orig_lines": [s, e]} for n, s, e in BLOCKS],
       "decl_vocab": {"re_linked": RE.DECL_RE.pattern, "proto_ast": proto_pat},
       "rows": [{k: v for k, v in r.items() if k != "reverify_new"} for r in rows],
       "extras": [{k: v for k, v in r.items() if k != "reverify_new"} for r in extras + [bad]],
       "history_cross": hist_cross, "summary": summary, "assertions": A}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

print("FINGERPRINTS:", "ALL_MATCH" if all(f["match"] for f in fps) else "MISMATCH",
      "| _sl_link.py =", fps[0]["sha256"][:12], "/", fps[0]["bytes"])
print("BINDING:", obj_sha, obj_bytes, "| notes_line_no =", out["binding"]["notes_line_no"])
print("DIFF HUNKS:", len(hunks), [(h["tag"], tuple(h["orig"]), tuple(h["new"])) for h in hunks])
print("DECL_RE:", repr(RE.DECL_RE.pattern), "| proto:", repr(proto_pat))
for r in allrows:
    print("%-11s %-34s:%-4s bd=%-7s %s->%s identical=%s triple_eq=%s members=%s decl=%s"
          % (r["tag"], Path(r["doc"]).name, r["line"], r["bytes_decl"], r["orig"], r["new"],
             r["identical"], r["triple_rec_identical"], r["members_n"], r["decl_lines"]))
print("SUMMARY:", json.dumps(summary, ensure_ascii=False))
print("ASSERTIONS:", sum(1 for a in A if a["ok"]), "/", len(A), "passed")
for a in A:
    if not a["ok"]:
        print("  FAIL:", a["name"], a["detail"])
print("OUT:", OUT)
sys.exit(0 if all(a["ok"] for a in A) else 1)
