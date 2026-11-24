# -*- coding: utf-8 -*-
"""_rev_cases.py — J4 并入复核员·独立核脚本（④(c)(d) 自建样本 + ⑤ 三纪律 + ⑥ 越界）：
  ★ 不复用撰写人 _re_fixtures/ 里的任何夹具；本件自建 _rev_fixtures/，自有 blob 与自有模板。
  ★ 不 exec/import 原型件顶层（其顶层会写只读目录 _eq_proto_out.json；且被安全钩子拦截）。
      原型语义按实读 _eq_proto.py:50-92 逐行重写为 reviewer_proto()，仅用于交叉核对。
  (c) 部分覆盖三形态：声明行覆盖 1/N（条件 ii 不满足）、覆盖 2/3、两声明行并集 3/4
      （条件 iii 全或无）——都必须保持 multi；
  (d) 纯等同词三形态：「逐字节同一」「完全相同/逐字节相同/COPY_IDENTICAL = False」、
      以及「纯等同词行覆盖全体 + 溯源词行仅覆盖部分」——都必须保持 multi；
      并用运行方自抄的「假设扩词」正则证明：若扩词则 (d1) 会误合并（唯一拦点确为封闭集）。
  正控制：自建全覆盖夹具 3 成员 / 15 成员 → merged（证明负例不是空跑）。
  ⑤ 三纪律在 15 成员 merged 上实测：path=None / 禁授权推论 / members 全列（anchors 仅 12）。
  实件对照：条3 真件 merged 形状 + Q4 六趟纯等同词语料（两种 bytes 喂入）保持 multi。
  ⑥ 越界：_sl_link.py 指纹守卫 + DECL_RE 封闭集与原型逐字符一致 + git 状态（未 commit/push）。
  只读（除本写域 _rev_fixtures/ 夹具与 _rev_cases_out.json）。零真机、零采样代码。"""
import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
SL_DIR = ROOT / "lead" / "samedoc_link_20261109"
RE_DIR = ROOT / "lead" / "r33e_merge_20261109"
EQ_DIR = ROOT / "lead" / "equiv_class_20261109"
FXD = RE_DIR / "_rev_fixtures"
OUT = RE_DIR / "_rev_cases_out.json"

A = []
def chk(name, cond, detail=""):
    A.append({"name": name, "ok": bool(cond), "detail": str(detail)})

# ---------- ⑥ 守卫：只读原件指纹 ----------
slb = (SL_DIR / "_sl_link.py").read_bytes()
guard = {"sha256": hashlib.sha256(slb).hexdigest(), "bytes": len(slb),
         "expect_sha": "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5",
         "expect_bytes": 12475}
chk("guard_sl_link_untouched",
    guard["sha256"] == guard["expect_sha"] and guard["bytes"] == guard["expect_bytes"],
    "%s/%d" % (guard["sha256"], guard["bytes"]))

def loadmod(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
SL = loadmod("_rev_sl_link2", SL_DIR / "_sl_link.py")
RE = loadmod("_rev_re_linked2", RE_DIR / "_re_linked.py")

# ---------- ⑥ 声明词封闭集：与原型 :47 逐字符一致（ast 静态取值，不执行原型件） ----------
proto_src = (EQ_DIR / "_eq_proto.py").read_text(encoding="utf-8")
proto_tree = ast.parse(proto_src)
proto_decl_pat = None
for n in proto_tree.body:
    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DECL_RE" for t in n.targets):
        proto_decl_pat = n.value.args[0].value
chk("proto_decl_pat_found", proto_decl_pat is not None, proto_decl_pat)
chk("decl_vocab_closed_not_expanded", RE.DECL_RE.pattern == proto_decl_pat,
    "%r vs %r" % (RE.DECL_RE.pattern, proto_decl_pat))
chk("proto_decl_re_line47_verbatim",
    proto_src.splitlines()[46].strip() == 'DECL_RE = re.compile(r"复制自|复制为|COPY_IDENTICAL\\s*=\\s*True")',
    proto_src.splitlines()[46])

RUNNER_DECL = re.compile(proto_decl_pat)
EXPANDED_HYPOTHETICAL = re.compile(proto_decl_pat + r"|逐字节同一|逐字节相同|完全相同|完全一致|内容一致")

# 原型语义的独立重写（据实读 _eq_proto.py:50-92；★ 关键特征：members 取 res["anchors"]，
# 即受 max_detail=12 截断；并入版据称取全量 matches。二者在 >12 成员时必然分叉。）
def reviewer_proto(text, res, vocab=None):
    vocab = vocab or RUNNER_DECL
    if res.get("verdict") != "multi":
        return dict(res), {"applied": False, "reason": "not multi"}
    members = res["anchors"]
    kset = {m["key"] for m in members}
    cov = {}
    for m in members:
        for t in m["tokens"]:
            for ln in t["lines"]:
                cov.setdefault(ln, set()).add(m["key"])
    hits = []
    for i, lntext in enumerate(text.splitlines()):
        if vocab.search(lntext):
            ck = cov.get(i + 1, set())
            if len(ck) >= 2:
                hits.append({"line": i + 1, "covers": sorted(ck), "text": lntext.strip()[:160]})
    if not hits:
        return dict(res), {"applied": False, "reason": "no decl line covering >=2"}
    group = set()
    for d in hits:
        group |= set(d["covers"])
    if group != kset:
        return dict(res), {"applied": False, "reason": "partial coverage", "hits": hits}
    out = dict(res)
    out["verdict"] = "merged"
    return out, {"applied": True, "members_n": len(members), "decl_lines": [d["line"] for d in hits]}

# ---------- 运行方独立的覆盖图 / 词行分析（基于 link() 的 anchors） ----------
def analyze(text, res, vocab=RUNNER_DECL):
    kset = {m["key"] for m in res["anchors"]}
    cov = {}
    for m in res["anchors"]:
        for t in m["tokens"]:
            for ln in t["lines"]:
                cov.setdefault(ln, set()).add(m["key"])
    lines = text.splitlines()
    decl = [i + 1 for i, ln in enumerate(lines) if vocab.search(ln)]
    hits = [{"line": ln, "covers_n": len(cov.get(ln, set())),
             "covers_all": cov.get(ln, set()) == kset} for ln in decl if len(cov.get(ln, set())) >= 2]
    return {"kset_n": len(kset), "decl_word_lines": decl,
            "cover_ge2_lines": sorted(ln for ln, ks in cov.items() if len(ks) >= 2),
            "decl_hits_ge2": hits}

# 完全不依赖 link() 输出的覆盖重建：按文本行内出现的 token 字面量建覆盖集合
def independent_full_coverage(text, tokens, vocab):
    lines = text.splitlines()
    cov = {}
    for i, ln in enumerate(lines):
        present = [t for t in tokens if t in ln]
        if present:
            cov[i + 1] = set(present)
    hits = []
    for i, ln in enumerate(lines):
        if vocab.search(ln) and len(cov.get(i + 1, set())) >= 2:
            hits.append({"line": i + 1, "n": len(cov[i + 1]),
                         "covers_all": cov[i + 1] == set(tokens)})
    union = set()
    for i, ln in enumerate(lines):
        if vocab.search(ln) and len(cov.get(i + 1, set())) >= 2:
            union |= cov[i + 1]
    return {"n_tokens": len(tokens), "decl_hits": hits, "union_n": len(union),
            "union_covers_all": union == set(tokens),
            "would_merge": bool(hits) and union == set(tokens)}

# ---------- 自建夹具 ----------
BLOB = b"REV-J4-INDEPENDENT-FIXTURE-20261109\n"   # 与撰写人夹具不同的自有 blob
FH = hashlib.sha256(BLOB).hexdigest()
NB = len(BLOB)
BIND = "被核对象 SHA256 = %s，字节数 = %d\n\n"

def toks(n):
    return ["m%02d.py" % i for i in range(1, n + 1)]

def tokline(n):
    return " ".join("`%s`" % t for t in toks(n))

TEMPLATES = {
    # (c) 部分覆盖
    "c1_decl_covers_one_of_two": (2, "`m01.py`、`m02.py` 为两件产物。\n`m01.py` 复制自外部原件。\n"),
    "c2_decl_covers_2_of_3": (3, "`m01.py`、`m02.py`、`m03.py` 为三件产物。\n`m01.py` 复制自 `m02.py`（声明行仅覆盖两件）。\n"),
    "c3_two_decl_lines_cover_3_of_4": (4, tokline(4) + " 为四件产物。\n`m01.py` 复制自 `m02.py`。\n`m02.py` 复制自 `m03.py`。\n"),
    # (d) 纯等同词
    "d1_pure_word_zhuyijie": (2, "`m01.py` 与 `m02.py`，二者逐字节同一。\n"),
    "d2_pure_words_no_decl": (2, "`m01.py` 与 `m02.py`，二者完全相同，COPY_IDENTICAL = False。\n另注：`m01.py` 与 `m02.py` 逐字节相同。\n"),
    "d3_pure_word_all_plus_partial_decl": (3, tokline(3) + "，三者逐字节相同。\n`m01.py` 复制自 `m02.py`（仅两件）。\n"),
    # 正控制
    "e1_full_3_merged": (3, tokline(3) + " 三件产物；`m02.py` 复制自 `m01.py` 且 `m03.py` 复制为副本。\n"),
    "e2_full_15_merged": (15, tokline(15) + " 十五件副本，均复制自同一母本。\n"),
}
FXD.mkdir(parents=True, exist_ok=True)
made = {}
for name, (n, tail) in TEMPLATES.items():
    d = FXD / name
    d.mkdir(parents=True, exist_ok=True)
    for t in toks(n):
        (d / t).write_bytes(BLOB)
    text = BIND % (FH, NB) + tail
    (d / "doc.md").write_text(text, encoding="utf-8", newline="\n")
    made[name] = (d, text, n)

def run_fixture(name):
    d, text, n = made[name]
    ro = SL.link(text, d, FH, NB)
    rm = RE.link(text, d, FH, NB)
    proto_out, proto_info = reviewer_proto(text, json.loads(json.dumps(ro)))
    an = analyze(text, rm)
    full = independent_full_coverage(text, toks(n), RUNNER_DECL)
    full_exp = independent_full_coverage(text, toks(n), EXPANDED_HYPOTHETICAL)
    po, wo, recm = RE.link_triple(text, d, FH, NB)
    return {"name": name, "n_files": n, "orig": ro["verdict"], "new": rm["verdict"],
            "proto": proto_out["verdict"], "proto_info": proto_info,
            "identical_json": json.dumps(ro, ensure_ascii=False, sort_keys=True)
                              == json.dumps(rm, ensure_ascii=False, sort_keys=True),
            "anchors_orig": len(ro["anchors"]), "anchors_new": len(rm.get("anchors", [])),
            "decl_lines": (rm.get("eq") or {}).get("decl_lines"),
            "members_n": len((rm.get("eq") or {}).get("members", [])),
            "analysis": an, "independent_full_coverage": full,
            "independent_full_coverage_if_expanded": full_exp,
            "reverify": rm.get("reverify"),
            "triple": {"tier": recm["tier"], "match": recm["match"], "path": recm["path"],
                       "keys": sorted(recm.keys()), "members_n": len(recm.get("members", [])),
                       "decl_lines": recm.get("decl_lines")},
            "warning": rm.get("warning"), "eq": rm.get("eq"), "problems": rm["problems"]}

R = {name: run_fixture(name) for name in TEMPLATES}

# ---- (c) 部分覆盖：三种形态都必须 multi ----
C_CONDS = {
    "c1_decl_covers_one_of_two": lambda r: (r["independent_full_coverage"]["decl_hits"] == []
        and r["analysis"]["decl_word_lines"] != []),
    "c2_decl_covers_2_of_3": lambda r: (len(r["independent_full_coverage"]["decl_hits"]) == 1
        and r["independent_full_coverage"]["decl_hits"][0]["n"] == 2
        and r["independent_full_coverage"]["union_covers_all"] is False),
    "c3_two_decl_lines_cover_3_of_4": lambda r: (len(r["independent_full_coverage"]["decl_hits"]) == 2
        and r["independent_full_coverage"]["union_n"] == 3
        and r["independent_full_coverage"]["union_covers_all"] is False),
}
for nm, cond in C_CONDS.items():
    r = R[nm]
    chk(nm + "_stays_multi", r["orig"] == "multi" and r["new"] == "multi" and r["proto"] == "multi",
        "%s->%s proto=%s" % (r["orig"], r["new"], r["proto"]))
    chk(nm + "_output_identical_to_orig", r["identical_json"] and r["reverify"] is None)
    chk(nm + "_reason_is_partial_coverage", cond(r), json.dumps(r["independent_full_coverage"], ensure_ascii=False))
    chk(nm + "_no_eq_key", r["eq"] is None)

# ---- (d) 纯等同词：都必须 multi，且证明唯一拦点是封闭集 ----
D_CONDS = {
    "d1_pure_word_zhuyijie": lambda r: (r["analysis"]["decl_word_lines"] == []
        and r["analysis"]["cover_ge2_lines"] != []
        and r["independent_full_coverage"]["decl_hits"] == []
        and r["independent_full_coverage_if_expanded"]["would_merge"] is True),
    "d2_pure_words_no_decl": lambda r: (r["analysis"]["decl_word_lines"] == []
        and r["independent_full_coverage"]["decl_hits"] == []
        and r["independent_full_coverage_if_expanded"]["would_merge"] is True),
    "d3_pure_word_all_plus_partial_decl": lambda r: (r["analysis"]["decl_word_lines"] != []
        and not any(h["covers_all"] for h in r["analysis"]["decl_hits_ge2"])
        and r["independent_full_coverage"]["union_covers_all"] is False),
}
for nm, cond in D_CONDS.items():
    r = R[nm]
    chk(nm + "_stays_multi", r["orig"] == "multi" and r["new"] == "multi" and r["proto"] == "multi",
        "%s->%s proto=%s" % (r["orig"], r["new"], r["proto"]))
    chk(nm + "_output_identical_to_orig", r["identical_json"])
    chk(nm + "_vocab_is_the_blocker", cond(r),
        "full=%s expanded=%s" % (json.dumps(r["independent_full_coverage"], ensure_ascii=False),
                                json.dumps(r["independent_full_coverage_if_expanded"], ensure_ascii=False)))
    chk(nm + "_no_eq_key", r["eq"] is None)
chk("d1_expanded_vocab_would_falsely_merge",
    R["d1_pure_word_zhuyijie"]["independent_full_coverage_if_expanded"]["would_merge"] is True)
chk("pure_equiv_words_never_in_closed_vocab",
    all(not RE.DECL_RE.search(w) for w in ["逐字节同一", "逐字节相同", "完全相同", "完全一致", "内容一致", "COPY_IDENTICAL = False"]))

# ---- 正控制：自建全覆盖夹具必须 merged（证明负例不是空跑） ----
for nm, n in [("e1_full_3_merged", 3), ("e2_full_15_merged", 15)]:
    r = R[nm]
    chk(nm + "_merged", r["orig"] == "multi" and r["new"] == "merged",
        "%s->%s" % (r["orig"], r["new"]))
    chk(nm + "_members_full_%d" % n, r["members_n"] == n, r["members_n"])
    chk(nm + "_independent_coverage_all", r["independent_full_coverage"]["union_covers_all"] is True,
        json.dumps(r["independent_full_coverage"], ensure_ascii=False))
chk("e1_proto_agrees_merged", R["e1_full_3_merged"]["proto"] == "merged")

# ---- ⑤ 三纪律（在 15 成员 merged 上实测） ----
e2 = R["e2_full_15_merged"]
eq = e2["eq"]
mem = eq["members"]
chk("d1_path_none__link_reverify_none", e2["reverify"] is None)
chk("d1_path_none__triple_path_none", e2["triple"]["path"] is None)
chk("d1_path_none__no_single_object_fields",
    not ({"verified_path", "recomputed", "bytes", "reverify"} & set(e2["triple"]["keys"])),
    e2["triple"]["keys"])
chk("d1_path_none__warning_says_so", "未做单一对象主张（path=None）" in (e2["warning"] or ""))
chk("d3_members_full__anchors_truncated_12", e2["anchors_new"] == 12 and e2["anchors_orig"] == 12)
chk("d3_members_full__15_unique_paths", len(mem) == 15 and len({m["path"] for m in mem}) == 15)
chk("d3_members_full__format",
    all(set(m) == {"path", "sha", "bytes"} for m in mem)
    and all(re.fullmatch(r"[0-9a-f]{64}", m["sha"]) for m in mem)
    and all(m["bytes"] == NB for m in mem))
chk("d3_members_full__sha_recomputed_from_disk",
    all(hashlib.sha256(Path(m["path"]).read_bytes()).hexdigest() == m["sha"] == FH for m in mem)
    and all(Path(m["path"]).is_file() and Path(m["path"]).is_absolute() for m in mem))
chk("d3_members_full__triple_members_same_shape",
    e2["triple"]["members_n"] == 15 and e2["triple"]["decl_lines"] == eq["decl_lines"])
chk("d3_members_full__warning_lists_all_15",
    all(m["path"] in (e2["warning"] or "") for m in mem))
chk("d2_ban_auth__warning", "禁止由 merged 推导任何授权结论" in (e2["warning"] or ""))
chk("d2_ban_auth__no_grant_fields",
    not any(k in e2["triple"]["keys"] for k in ["authorized", "allowed", "granted", "released"]),
    e2["triple"]["keys"])
chk("problems_contract_empty", e2["problems"] == [])

# 纪律文本落地位置（实读文件行）
linked_lines = (RE_DIR / "_re_linked.py").read_text(encoding="utf-8").splitlines()
notes_lines = (RE_DIR / "_re_NOTES.md").read_text(encoding="utf-8").splitlines()
def blob(a, b):
    return "\n".join(linked_lines[a - 1:b])
chk("d2_ban_auth__module_docstring_L26_36", "禁止从 merged 推导授权结论" in blob(26, 36)
    and "path=None 不做单一对象主张" in blob(26, 36) and "members 全列" in blob(26, 36))
chk("d2_ban_auth__j4_block_comment_L254_256", "不构成任何授权结论" in blob(254, 256))
chk("d2_ban_auth__triple_comment_L322_325", "禁止由 merged 推导任何授权结论" in blob(322, 325))
chk("d2_ban_auth__notes_L38_49", "禁止从 merged 推导授权结论" in "\n".join(notes_lines[37:49])
    and "禁止由 merged 推导任何授权结论" in "\n".join(notes_lines[37:49]))
# AST：merged 分支不给 rec 写任何单对象字段
linked_ast = ast.parse((RE_DIR / "_re_linked.py").read_text(encoding="utf-8"))
lt = next(n for n in linked_ast.body if isinstance(n, ast.FunctionDef) and n.name == "link_triple")
def is_merged_if(n):
    return (isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
            and any(isinstance(c, ast.Constant) and c.value == "merged"
                    for c in n.test.comparators))
merged_branch = next(n for n in ast.walk(lt) if is_merged_if(n))
subscript_assigns = []
for n in ast.walk(merged_branch):
    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Subscript) for t in n.targets):
        for t in n.targets:
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == "rec":
                subscript_assigns.append(t.slice.value if isinstance(t.slice, ast.Constant) else "?")
chk("d1_path_none__ast_merged_branch_no_single_object_assign",
    not ({"path", "verified_path", "recomputed", "bytes", "reverify"} & set(subscript_assigns)),
    subscript_assigns)

# ---- 实件对照：条3 与 Q4 ----
doc3 = ROOT / "lead" / "b2b_isolated_20261107" / "_integ_INTEGRATION_REPORT.md"
t3 = doc3.read_bytes().decode("utf-8")
CAND = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
ro3 = SL.link(t3, doc3.parent, CAND, 412759)
rm3 = RE.link(t3, doc3.parent, CAND, 412759)
p3, w3, rec3 = RE.link_triple(t3, doc3.parent, CAND, 412759)
an3 = analyze(t3, rm3)
item3 = {"orig": ro3["verdict"], "new": rm3["verdict"],
         "decl_lines": (rm3.get("eq") or {}).get("decl_lines"),
         "decl_text": [d["text"] for d in (rm3.get("eq") or {}).get("decl_hits", [])],
         "line13_actual": t3.splitlines()[12].strip(),
         "members_n": len((rm3.get("eq") or {}).get("members", [])),
         "analysis": an3,
         "triple": {"tier": rec3["tier"], "match": rec3["match"], "path": rec3["path"],
                    "keys": sorted(rec3.keys())},
         "warning": rm3["warning"]}
chk("item3_multi_to_merged", ro3["verdict"] == "multi" and rm3["verdict"] == "merged")
chk("item3_decl_line13_verbatim", item3["decl_lines"] == [13]
    and item3["decl_text"] == [item3["line13_actual"]], item3["decl_text"])
chk("item3_members2_disciplines", item3["members_n"] == 2 and rec3["path"] is None
    and rec3["tier"] == "SAMEDOC_LINK_EQ" and rec3["match"] is True
    and not ({"verified_path", "recomputed", "bytes"} & set(rec3))
    and "禁止由 merged 推导任何授权结论" in rm3["warning"])
chk("item3_runner_coverage", an3["kset_n"] == 2 and an3["cover_ge2_lines"] == [13]
    and an3["decl_hits_ge2"] == [{"line": 13, "covers_n": 2, "covers_all": True}])

Q4HEX = "6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251"
q4path = ROOT / "lead" / "re_line_20261105" / "W9_SINGLESTEP_7CFC9F" / "Q4_RELATION.md"
q4 = q4path.read_bytes().decode("utf-8")
q4res = {}
for bd in (26405, None):
    roq = SL.link(q4, q4path.parent, Q4HEX, bd)
    rmq = RE.link(q4, q4path.parent, Q4HEX, bd)
    anq = analyze(q4, rmq)
    q4res["bytes_%s" % bd] = {"orig": roq["verdict"], "new": rmq["verdict"],
                              "anchors": len(rmq["anchors"]), "analysis": anq,
                              "identical": json.dumps(roq, ensure_ascii=False, sort_keys=True)
                                           == json.dumps(rmq, ensure_ascii=False, sort_keys=True)}
    chk("q4_bytes_%s_stays_multi" % bd,
        roq["verdict"] == "multi" and rmq["verdict"] == "multi" and q4res["bytes_%s" % bd]["identical"])
    chk("q4_bytes_%s_no_decl_words" % bd, anq["decl_word_lines"] == [])
chk("q4_pure_equiv_words_present_but_not_vocab",
    any("逐字节相同" in ln for ln in q4.splitlines())
    and all(not RE.DECL_RE.search(ln) for ln in q4.splitlines()))

# ---- 原型语义（anchors 截断）vs 并入版：记录 >12 成员的成员数分叉 ----
proto15_out, proto15_info = reviewer_proto(made["e2_full_15_merged"][1], json.loads(json.dumps(
    SL.link(made["e2_full_15_merged"][1], made["e2_full_15_merged"][0], FH, NB))))
proto15_members = proto15_info.get("members_n", 0)
chk("proto_reimpl_15_verdict_merged", proto15_out["verdict"] == "merged", proto15_out["verdict"])
chk("proto_reimpl_15_anchor_limited_12", proto15_members == 12, proto15_members)
chk("impl_15_full_matches_15", e2["members_n"] == 15)
proto_cross = [{"name": nm, "proto_verdict": R[nm]["proto"], "new_verdict": R[nm]["new"],
                "agree": R[nm]["proto"] == R[nm]["new"]} for nm in TEMPLATES]
chk("proto_reimpl_vs_impl_verdict_all_agree", all(x["agree"] for x in proto_cross))

# ---- ⑥ git 越界检查（只读命令） ----
gs = subprocess.run(["git", "status", "--porcelain", "--",
                     "lead/samedoc_link_20261109/_sl_link.py",
                     "lead/equiv_class_20261109/", "lead/f2d_rootcause_20261109/",
                     "lead/r11_f2_fix_20261109/", "lead/PENDING_DECISIONS.md",
                     "lead/GOAL_THREE_TARGETS_20261018.md"],
                    cwd=str(ROOT), capture_output=True, text=True)
head = subprocess.run(["git", "log", "-1", "--format=%H %s"], cwd=str(ROOT),
                      capture_output=True, text=True)
gitinfo = {"status_readonly_paths": gs.stdout.strip(), "head": head.stdout.strip()}
chk("git_head_unchanged_no_commit_in_session", head.stdout.strip().startswith("2657458"), gitinfo["head"])

out = {"guard": guard, "fixture": {"blob_sha": FH, "bytes": NB, "dir": str(FXD)},
       "decl_vocab": {"impl": RE.DECL_RE.pattern, "proto": proto_decl_pat,
                      "hypothetical_expanded": EXPANDED_HYPOTHETICAL.pattern},
       "cases": {k: {kk: vv for kk, vv in v.items() if kk not in ("warning", "eq")} for k, v in R.items()},
       "case_warnings": {k: v["warning"] for k, v in R.items()},
       "e2_members": mem, "item3": item3, "q4": q4res,
       "proto_cross": proto_cross, "proto15_members": proto15_members,
       "git": gitinfo, "assertions": A}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

print("GUARD _sl_link.py:", guard["sha256"][:12], "/", guard["bytes"])
print("DECL_RE closed:", repr(RE.DECL_RE.pattern))
print("SELF-BUILT BLOB:", FH[:12], "/", NB, "B | fixtures in", FXD.name)
for nm in TEMPLATES:
    r = R[nm]
    print("%-44s files=%-3d %s->%s(proto=%s) identical=%-5s anchors=%-3d members=%-3d decl=%-6s ge2=%s" % (
        nm, r["n_files"], r["orig"], r["new"], r["proto"], r["identical_json"],
        r["anchors_new"], r["members_n"], r["decl_lines"], r["analysis"]["cover_ge2_lines"]))
print("D1 WOULD_MERGE_IF_VOCAB_EXPANDED:",
      R["d1_pure_word_zhuyijie"]["independent_full_coverage_if_expanded"]["would_merge"])
print("E2 DISCIPLINES: reverify=%r triple.path=%r triple_keys=%s anchors=%d members=%d" % (
    e2["reverify"], e2["triple"]["path"], e2["triple"]["keys"], e2["anchors_new"], e2["members_n"]))
print("ITEM3:", item3["orig"], "->", item3["new"], "decl=", item3["decl_lines"], "line13=", item3["line13_actual"][:70])
for k, v in q4res.items():
    print("Q4", k, v["orig"], "->", v["new"], "anchors=", v["anchors"], "decl_word_lines=", v["analysis"]["decl_word_lines"])
print("PROTO-REIMPL15 members:", proto15_members, "| IMPL15 members:", e2["members_n"])
print("GIT:", gitinfo)
print("ASSERTIONS:", sum(1 for x in A if x["ok"]), "/", len(A), "passed")
for x in A:
    if not x["ok"]:
        print("  FAIL:", x["name"], x["detail"][:300])
print("OUT:", OUT)
sys.exit(0 if all(x["ok"] for x in A) else 1)
