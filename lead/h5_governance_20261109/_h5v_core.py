# -*- coding: utf-8 -*-
r"""_h5v_core.py — 独立复核 ②③⑤：自己生成修后副本（不采信撰写人 _h5_v12_patched.py），
自己跑九条、自构边界样本、两条回退。脚本/产物只落写域，前缀 _h5v_。
用 python -I -X utf8 + 绝对路径运行。"""
import sys, json, hashlib, importlib.util
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(r"D:\Project\ra2-campaign-forge\lead\h5_governance_20261109")
ROOT = HERE.parent.parent
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
PASTE = HERE / "_h5_pasteable.py"
WRITER_PATCHED = HERE / "_h5_v12_patched.py"
MY_PATCHED = HERE / "_h5v_patched.py"


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_my_patched():
    """独立施加：四处锚点自己写，pasteable 片段自己截取，不调用撰写人 _h5_patch.py。"""
    rule_src = RULE.read_text(encoding="utf-8")
    paste_src = PASTE.read_text(encoding="utf-8")
    first = paste_src.find('"""')
    second = paste_src.find('"""', first + 3)
    snippet = paste_src[second + 3:].lstrip("\n")

    a1 = ('    adj_neg = bool(pre) and (pre[-1] in ADJ_NEG_CHARS or bool(ADJ_NEG_RE.search(pre)))\n'
          '    prohibit_U = any(k in U_bare for k in PROHIBIT)')
    b1 = ('    gov = h5_govern(pre, post)\n'
          '    adj_neg = gov["adj_neg"]\n'
          '    prohibit_U = gov["prohibit_governs"]\n'
          '    double_neg = gov["double_neg"]')
    a2 = ('    if adj_neg or prohibit_U or "无已填" in U:\n'
          '        hard.append("H5_否定禁止管辖")')
    b2 = ('    if (adj_neg or prohibit_U or "无已填" in U) and not double_neg:\n'
          '        hard.append("H5_否定禁止管辖")')
    a3 = ('    if hard:\n'
          '        return {"verdict": "V1", "hard": hard, "weak": [], "override": "",\n'
          '                "unit": U, "line": line, "review_flag": False,\n'
          '                "reason": "HARD_V1 结构：" + ",".join(hard) + "（完成词不可能充当断言谓语）"}')
    b3 = ('    if double_neg:\n'
          '        return {"verdict": "V2", "hard": [], "weak": [],\n'
          '                "override": "H5_DOUBLE_NEG:" + gov["dn_hit"],\n'
          '                "unit": U, "line": line, "review_flag": False,\n'
          '                "reason": "H5 双重否定=肯定：管辖前缀内含双重否定构式，完成词为真断言"}\n') + a3
    a4 = '    if hit_override and not adj_neg and not prohibit_U:'
    b4 = '    if hit_override and not adj_neg and not prohibit_U and not double_neg:'
    for i, a in enumerate([a1, a2, a3, a4], 1):
        assert rule_src.count(a) == 1, "anchor %d not unique (count=%d)" % (i, rule_src.count(a))
    out = (rule_src.replace(a1, b1).replace(a2, b2).replace(a3, b3).replace(a4, b4))
    marker = "def classify_v12(text, start, end, token):"
    assert out.count(marker) == 1
    out = out.replace(marker, snippet + "\n\n" + marker)
    MY_PATCHED.write_text(out, encoding="utf-8")
    return out


OLD = _import("_h5v_old_rule", RULE)
build_my_patched()
NEW = _import("_h5v_new_rule", MY_PATCHED)
PASTE_MOD = _import("_h5v_paste", PASTE)


def run(mod, text, token, occ=0):
    """occ: 第几次出现（自构样本可能同 token 多次）。"""
    p = -1
    for _ in range(occ + 1):
        p = text.find(token, p + 1)
    assert p >= 0, (text, token, occ)
    r = mod.classify_v12(text, p, p + len(token), token)
    return {"verdict": r["verdict"], "hard": r["hard"], "weak": r["weak"],
            "override": r["override"], "review": r["review_flag"],
            "unit": r["unit"], "reason": r["reason"]}


def dec(r):
    return "PASS" if r["verdict"] == "V1" else "CATCH"


def gov_of(text, token, occ=0):
    p = -1
    for _ in range(occ + 1):
        p = text.find(token, p + 1)
    line = text[text.rfind("\n", 0, p) + 1:]
    le = line.find("\n")
    if le >= 0:
        line = line[:le]
    rel = p - (text.rfind("\n", 0, p) + 1)
    # 复刻 _v12_rule._unit_and_line 的 _segment：按 。！？；\n 切
    import re
    cuts = [0] + [m.end() for m in re.finditer(r"[。！？；\n]", line)] + [len(line)]
    cuts = sorted(set(cuts))
    U = line
    for a, b in zip(cuts, cuts[1:]):
        if a <= rel < b:
            U = line[a:b]
            rel -= a
            break
    pre, post = U[:rel], U[rel + len(token):]
    g = PASTE_MOD.h5_govern(pre, post)
    return {"U": U, "pre": pre, "post": post, **g}


# ---------------- ② 九条（自己写，不采信 _h5_repro9.py 的结果） ----------------
NINE = [
    ("REGRESS1", "本笔已入账 0 命中不得写成未入账", "已入账", "V1", "H5", "V1"),
    ("REGRESS2", "审阅不得不承认本候选已生效。", "已生效", "V1", "H5", "V1"),
    ("CTRL_OK", "本件已生效，可应用母本", "已生效", "V2", "review=True", "CATCH"),
    ("TRUE_NEG", "本节登记不宣告 N-4 正式绑定已生效", "已生效", "V2", "review=True", "CATCH"),
    ("TRAIL_NEG", "已入账不得重复登记", "已入账", "V1", "H5", "V1"),
    ("LEAD_NEG", "不得写成已入账", "已入账", "V1", "H5", "V1"),
    ("DOUBLE_1", "并非不宣告已生效", "已生效", "V1", "H5", "V1"),
    ("DOUBLE_2", "不能不说本笔已入账", "已入账", "V2", "V2_OVERRIDE:已入账", "CATCH"),
    ("DOUBLE_3", "无不认为本件已生效", "已生效", "V2", "review=True", "CATCH"),
]
print("=== ② 九条：原 _v12_rule.py 实跑 ===")
nine_rows = []
for cid, text, tok, wverd, wnote, wdec in NINE:
    r = run(OLD, text, tok)
    h5 = any("H5" in h for h in r["hard"])
    note = ("H5" if h5 else ("V2_OVERRIDE:" + r["override"].split(":", 1)[1]
                             if r["override"].startswith("V2_OVERRIDE")
                             else ("review=True" if r["review"] else r["override"] or "-")))
    ok = (r["verdict"] == wverd) and ((wnote == "H5" and h5) or
                                      (wnote == "review=True" and r["review"]) or
                                      (wnote.startswith("V2_OVERRIDE") and r["override"].startswith("V2_OVERRIDE")))
    print("%-10s verdict=%s hard=%r override=%r review=%s weak=%r | 宣称 %s/%s -> %s" %
          (cid, r["verdict"], r["hard"], r["override"], r["review"], r["weak"], wverd, wnote,
           "MATCH" if ok else "MISMATCH"))
    nine_rows.append(dict(id=cid, text=text, token=tok, verdict=r["verdict"], hard=r["hard"],
                          override=r["override"], review=r["review"], weak=r["weak"],
                          claimed_verdict=wverd, claimed_note=wnote, match=ok))
print("② nine MATCH count =", sum(x["match"] for x in nine_rows), "/ 9")

# ---------------- ③ 自构边界样本（≥5 条） ----------------
# expect 口径：PASS=真否定/禁止管辖应放行；CATCH=真断言应抓。
# 每条给出语义说明；全部为隔离 H5 的形状（避开 H1/H2/H3/H4/H6/W1 词，除非注明）。
BOUND = [
    # --- 应 PASS：真否定/禁止管辖 ---
    ("B1", "不宣告 N-4 正式绑定已生效", "已生效", "PASS",
     "真否定管辖：前向桥接，算子不+宣告+补语（撰写人三情形之一）"),
    ("B2", "不得把 N-4 写成已入账", "已入账", "PASS",
     "真禁止管辖：不得+把字桥接（G3 形状b）"),
    ("B3", "本笔不放行 N-5，但不得写成未入账", "放行 N-5", "PASS",
     "紧邻否定管辖（形状a）；后向禁止在 post，按 G1 不该反向取消豁免"),
    # --- 应 CATCH：后向禁止 / 双重否定 / 跨子句 ---
    ("B4", "本笔已入账，不得改写成未入账", "已入账", "CATCH",
     "后向禁止：禁止词全在 post，pre 干净；G1 要求不豁免"),
    ("B5", "不，已入账", "已入账", "CATCH",
     "「不，」为独立否定叹词，后接肯定断言；测试形状a 是否按 G2 只认同微句"),
    ("B6", "不可能/未覆盖：本笔已入账不得写成未入账", "已入账", "CATCH",
     "现盘 s604 形态 + 后向禁止；测形状c 是否误把 post 里的「未」当谓语否定"),
    ("B7", "非写成已入账不可", "已入账", "CATCH",
     "分离式双重否定「非…不可」= 必须写成；测试 G5 只看 pre 的局限"),
    ("B8", "不得把「N-4」写成已入账", "已入账", "CATCH",
     "G4 引证屏蔽后把字桥接是否被空格撑断；此条语义应为 PASS（见下注）"),
]
# 注：B8 语义 = 禁止管辖（应 PASS）。此处先按 PASS 判定，脚本会单列。
B8_EXPECT = "PASS"

print("\n=== ③ 自构边界样本：OLD vs 我独立生成的 NEW ===")
bound_rows = []
for cid, text, tok, exp, why in BOUND:
    e = B8_EXPECT if cid == "B8" else exp
    o, n = run(OLD, text, tok), run(NEW, text, tok)
    g = gov_of(text, tok)
    ok_old = dec(o) == e
    ok_new = dec(n) == e
    print("%-3s exp=%-5s old=%-5s new=%-5s  newOK=%-5s  hard_new=%r ov_new=%r" %
          (cid, e, dec(o), dec(n), ok_new, n["hard"], n["override"]))
    print("     why: %s" % why)
    print("     gov: adj=%s prohibit=%s double=%s dn=%r shapes=%r scope=%r pre=%r post=%r" %
          (g["adj_neg"], g["prohibit_governs"], g["double_neg"], g["dn_hit"],
           g["shapes"], g["scope"], g["pre"], g["post"]))
    bound_rows.append(dict(id=cid, text=text, token=tok, expect=e, why=why,
                           old=dec(o), new=dec(n), old_ok=ok_old, new_ok=ok_new,
                           new_hard=n["hard"], new_override=n["override"],
                           new_reason=n["reason"], gov=g))
print("③ NEW correct =", sum(x["new_ok"] for x in bound_rows), "/", len(bound_rows))
wrong = [x["id"] for x in bound_rows if not x["new_ok"]]
print("③ NEW WRONG ids =", wrong)

# ---------------- ⑤ 两条回退（撰写人点名 REGRESS1/REGRESS2） ----------------
print("\n=== ⑤ 两处确凿回退：OLD vs NEW ===")
regress_rows = []
for cid in ("REGRESS1", "REGRESS2"):
    rec = next(x for x in NINE if x[0] == cid)
    o, n = run(OLD, rec[1], rec[2]), run(NEW, rec[1], rec[2])
    print("%-10s old=%s(%s) new=%s(%s) new_override=%r hard_new=%r" %
          (cid, dec(o), o["verdict"], dec(n), n["verdict"], n["override"], n["hard"]))
    regress_rows.append(dict(id=cid, old=dec(o), new=dec(n), expect="CATCH",
                             fixed=dec(o) != dec(n) and dec(n) == "CATCH",
                             new_override=n["override"], new_hard=n["hard"]))
print("⑤ both fixed =", all(x["fixed"] for x in regress_rows))

# ---------------- 与撰写人副本的忠实度核对 ----------------
wb, mb = WRITER_PATCHED.read_bytes(), MY_PATCHED.read_bytes()
print("\n=== 修后副本忠实度 ===")
print("writer _h5_v12_patched.py sha=%s bytes=%d" % (hashlib.sha256(wb).hexdigest(), len(wb)))
print("mine   _h5v_patched.py     sha=%s bytes=%d" % (hashlib.sha256(mb).hexdigest(), len(mb)))
print("IDENTICAL =", wb == mb)

out = {"nine": nine_rows, "boundary": bound_rows, "regress": regress_rows,
       "patched_identical": wb == mb,
       "writer_patched_sha": hashlib.sha256(wb).hexdigest(),
       "my_patched_sha": hashlib.sha256(mb).hexdigest()}
(HERE / "_h5v_core_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _h5v_core_out.json")
