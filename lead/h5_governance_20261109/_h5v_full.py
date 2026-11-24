# -*- coding: utf-8 -*-
r"""_h5v_full.py — 独立复核 ③④⑥⑦⑧（自己写实现、自己造样本、自己读盘）。
只写 _h5v_* 到写域；不改任何既有件。python -I -X utf8 + 绝对路径。"""
import sys, json, hashlib, importlib.util, re, subprocess
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = ROOT / "lead" / "h5_governance_20261109"
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
BASELINE = ROOT / "lead" / "gate_rejudge32_20261109" / "_rj_delivery_baseline.json"
SHADOW = ROOT / "lead" / "v12_impact_20261109" / "_vi_shadow_out.json"
MY_PATCHED = HERE / "_h5v_patched.py"       # 由 _h5v_core.py 独立生成
IMPACT = ROOT / "lead" / "v12_impact_20261109" / "V12_FULL_IMPACT.md"


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OLD = _import("_h5v_old2", RULE)
NEW = _import("_h5v_new2", MY_PATCHED)
PASTE = _import("_h5v_paste2", HERE / "_h5_pasteable.py")
G7M = _import("_h5v_g7", G7)
SAMPLES = _import("_h5v_samples", HERE / "_h5_samples.py").SAMPLES


def run(mod, text, token, pos=None):
    p = text.find(token) if pos is None else pos
    assert p >= 0, (text, token, pos)
    r = mod.classify_v12(text, p, p + len(token), token)
    return {"verdict": r["verdict"], "hard": r["hard"], "weak": r["weak"],
            "override": r["override"], "review": r["review_flag"], "reason": r["reason"]}


def dec(r):
    return "PASS" if r["verdict"] == "V1" else "CATCH"


# ==================== ③ 精修边界样本（10 条，两侧都有） ====================
BOUND = [
 ("V01", "不宣告 N-4 正式绑定已生效", "已生效", "PASS",
  "真否定管辖基准（铁律点名样本）；形状b 前向桥接"),
 ("V02", "不得把 N-4 写成已入账", "已入账", "PASS",
  "真禁止管辖：把字宾语为 5 字 ' N-4 '；与撰写人 P09『不得把本笔写成已入账』同构"),
 ("V03", "不得把「N-4」写成已入账", "已入账", "PASS",
  "真禁止管辖：G4 引证屏蔽后把字宾语被空格撑长；撰写人 G4 自述要保住桥接"),
 ("V04", "不宣告 N-4 已生效，但本笔已入账", "已入账", "CATCH",
  "跨微句否定（，但）：撰写人三情形之一"),
 ("V05", "本笔已入账，不得改写成未入账", "已入账", "CATCH",
  "后向禁止：禁止词全在 post（G1 硬条件）"),
 ("V06", "不，本笔已入账", "已入账", "CATCH",
  "『不，』为独立否定叹词/另起微句，后接肯定断言；测 G2 是否真作用于形状a"),
 ("V07", "不得写成未入账，本笔已入账", "已入账", "CATCH",
  "『不得』与 token 相距且支配另一动词；后半为真断言（G1/G3 与 W1 词表交互）"),
 ("V08", "非写成已入账不可", "已入账", "CATCH",
  "分离型双重否定『非…不可』= 必须；与 REGRESS2『不得不承认…已生效』同属双重否定=肯定"),
 ("V09", "没法不宣告本件已生效", "已生效", "CATCH",
  "双重否定『没法不』：R12 十式与 H5 超集均未列"),
 ("V10", "不可能/未覆盖：本笔已入账不得写成未入账", "已入账", "CATCH",
  "现盘 s604 辖域框头 + 后向禁止；测形状c 的 post[:40] 是否把补语里的『未』误当谓语否定"),
]
print("=== ③ 精修边界样本 10 条：OLD vs 我独立生成的 NEW ===")
bound = []
for cid, text, tok, exp, why in BOUND:
    o, n = run(OLD, text, tok), run(NEW, text, tok)
    ok = dec(n) == exp
    print("%-4s exp=%-5s old=%-5s new=%-5s newOK=%-5s hard=%r ov=%r" %
          (cid, exp, dec(o), dec(n), ok, n["hard"], n["override"]))
    print("      %s" % why)
    bound.append(dict(id=cid, text=text, token=tok, expect=exp, why=why,
                      old=dec(o), new=dec(n), new_ok=ok,
                      new_hard=n["hard"], new_override=n["override"], new_reason=n["reason"]))
print("③ NEW = %d/%d ; 误拦(真否定被 CATCH) = %s ; 放过(真断言被 PASS) = %s" %
      (sum(x["new_ok"] for x in bound), len(bound),
       [x["id"] for x in bound if x["expect"] == "PASS" and x["new"] == "CATCH"],
       [x["id"] for x in bound if x["expect"] == "CATCH" and x["new"] == "PASS"]))

# ==================== ④ R12 正则独立找漏 ====================
print("\n=== ④ 独立读 DOUBLE_NEG_RE 并枚举漏式 ===")
print("R12 pattern =", G7M.DOUBLE_NEG_RE.pattern)
print("H5  pattern =", PASTE.H5_DOUBLE_NEG_RE.pattern)
# 我自己列举的候选双重否定构式（不采信撰写人的 19 式）
CAND = [
 "不得不", "并非不", "并不是不", "不是不", "无不", "没有不", "不无", "不能不", "不可不", "未曾不",  # R12 十式对照
 "亦非不", "未尝不", "莫不", "不敢不", "并非没有", "并不否认",                                  # 撰写人已登记
 "何尝不", "何尝不是", "岂不是", "安能不", "岂敢不", "没法不", "没法不说",
 "不否认", "绝不否认", "从未否认", "不排除", "并不排除", "并非否认", "并非未", "并非无",
 "不由得不", "忍不住不", "未必不", "不见得不", "不一定不", "不会没有", "不是没",
 "非写成已入账不可", "非登记不可", "非说不", "非但不", "谁说不是", "没说不",
 "不得不承认", "不能不承认", "未尝不是", "莫不是", "无不是", "岂能不", "焉能不", "哪能不",
]
print("\n%-22s %6s %6s %8s | %-30s" % ("构式", "R12", "H5", "r12prob", "NEW 判定(构式+本件已生效)"))
gaps_r12, gaps_both = [], []
for c in CAND:
    r12 = bool(G7M.DOUBLE_NEG_RE.search(c))
    h5 = bool(PASTE.H5_DOUBLE_NEG_RE.search(c))
    text = c + "本件已生效" if not c.endswith("已生效") else c
    # 保证 token 唯一且在末尾
    tok = "已生效"
    p = text.find(tok)
    probs, hits = G7M.r12_scan(text, [tok])
    rr = run(NEW, text, tok, p)
    v = dec(rr)
    if not r12:
        gaps_r12.append(c)
    if not r12 and not h5:
        gaps_both.append(c)
    print("%-22s %6s %6s %8d | %-5s hard=%r ov=%r" %
          (c, str(r12), str(h5), len(probs), v, rr["hard"], rr["override"]))
print("\n④ R12 漏式共 %d 条；R12 与 H5 超集【都】漏 = %d 条：%s" %
      (len(gaps_r12), len(gaps_both), gaps_both))

# 分离型：第二个「不」落在 post（G5 只查 scope=pre）
print("\n--- ④b 第二个否定词落在 post 的分离型双重否定 ---")
SPLIT = ["非写成已入账不可", "不宣告已生效不行", "非登记已入账不可", "不写成已入账不成"]
for text in SPLIT:
    tok = "已入账" if "已入账" in text else "已生效"
    o, n = run(OLD, text, tok), run(NEW, text, tok)
    print("%-22s tok=%-5s old=%-5s new=%-5s hard_new=%r ov=%r" %
          (text, tok, dec(o), dec(n), n["hard"], n["override"]))

# ==================== ⑥ 32 域 26 处独立重跑 ====================
print("\n=== ⑥ 32 域现盘重跑（自己读盘、自己算 old/new） ===")
bl = json.loads(BASELINE.read_text(encoding="utf-8"))
sh = json.loads(SHADOW.read_text(encoding="utf-8"))
by_dom = {d["domain"]: d for d in sh["rows"]}
rows, counts = [], {"hits": 0, "old_V1": 0, "new_V1": 0, "changed": 0,
                    "fp_mismatch": 0, "both_wrong_or_right": 0}
for r in bl["rows"]:
    dom, main = r["domain"], r["main"]
    path = ROOT / dom / main
    raw = path.read_bytes()
    fp_ok = (hashlib.sha256(raw).hexdigest() == r["mainSha256"] and len(raw) == r["mainBytes"])
    if not fp_ok:
        counts["fp_mismatch"] += 1
    text = raw.decode("utf-8")
    rec = by_dom.get(dom)
    for h in (rec["hits"] if rec else []):
        pos, tok = h["pos"], h["token"]
        assert text[pos:pos + len(tok)] == tok, (dom, pos, tok)
        o, n = run(OLD, text, tok, pos), run(NEW, text, tok, pos)
        changed = o["verdict"] != n["verdict"]
        counts["hits"] += 1
        counts["old_V1"] += o["verdict"] == "V1"
        counts["new_V1"] += n["verdict"] == "V1"
        counts["changed"] += changed
        rows.append(dict(domain=dom, main=main, pos=pos, token=tok, fp_ok=fp_ok,
                         old=o["verdict"], new=n["verdict"], changed=changed,
                         old_hard=o["hard"], new_hard=n["hard"], new_ov=n["override"]))
        if changed:
            print("  CHANGED %s pos=%d %s %s->%s" % (dom, pos, tok, o["verdict"], n["verdict"]))
print("⑥ counts =", json.dumps(counts, ensure_ascii=False))
print("⑥ 说明：该检查只比 old-vs-new，无逐处人工真值标签，不能发现『两者都错』。")

# ==================== 44 样本独立复算（分 A 九条 / B 全 44） ====================
print("\n=== 撰写人 44 样本独立复算（用我的修后副本，自己记分） ===")
scores = {"old": {"correct": 0, "fp": 0, "fn": 0}, "new": {"correct": 0, "fp": 0, "fn": 0}}
for s in SAMPLES:
    for key, mod in (("old", OLD), ("new", NEW)):
        d = dec(run(mod, s["text"], s["token"]))
        if d == s["expect"]:
            scores[key]["correct"] += 1
        elif s["expect"] == "PASS" and d == "CATCH":
            scores[key]["fp"] += 1
        else:
            scores[key]["fn"] += 1
print("44 样本 old =", scores["old"], " new =", scores["new"], " n =", len(SAMPLES))

# ==================== ⑦ 是否考虑其它缺陷（读 §5 与 IMPACT 关键行） ====================
print("\n=== ⑦ 第五步(a)：核对是否把其它缺陷也考虑了 ===")
design = (HERE / "_h5_DESIGN.md").read_text(encoding="utf-8")
impact = IMPACT.read_text(encoding="utf-8")
for kw in ["仍然不能全局插入", "可插", "冒名", "自指词", "S3", "fail-closed",
           "提前 return", "双标记", "影子", "未重跑", "未验", "替代方案", "白名单"]:
    print("  DESIGN 含 %-14s : %s" % (kw, kw in design))
ilines = impact.splitlines()
for ln in [226, 242, 260, 287, 296, 314, 324, 333, 335, 344, 348]:
    if ln <= len(ilines):
        print("  IMPACT:%-4d %s" % (ln, ilines[ln - 1][:160]))
print("  DESIGN 总闸门句 =", [l for l in design.splitlines() if "总闸门" in l][:3])

# ==================== ⑧ 越界检查 ====================
print("\n=== ⑧ 越界检查：指纹 / mtime / 写域文件清单 ===")
WATCH = {
 "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
 "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
 "lead/gate_pipeline_20261109/_gp_pipeline.py": ("25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7", 15811),
 "lead/v12_impact_20261109/_vi_REPORT.md": ("9375f37c0ecc81851944fa5383679ce0f02090b2bce6156a5f31396140bdc085", 32956),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
import time
for rel, (sha, n) in WATCH.items():
    p = ROOT / rel
    b = p.read_bytes()
    print("  %-56s sha_ok=%s mtime=%s" %
          (rel, hashlib.sha256(b).hexdigest() == sha and len(b) == n,
           time.strftime("%H:%M:%S", time.localtime(p.stat().st_mtime))))
wf = sorted(p.name for p in HERE.iterdir() if p.is_file())
print("  写域文件 n =", len(wf))
print("  写域非 _h5_/_h5v_ 前缀 =", [x for x in wf if not (x.startswith("_h5_") or x.startswith("_h5v_"))])
for d in ["lead/gate_v1v2_20261109", "lead/v12_impact_20261109",
          "lead/gate_n13_20261109", "lead/gate_fp7_20261108", "lead/gate_pipeline_20261109"]:
    pyc = list((ROOT / d).rglob("*.pyc"))
    print("  %-42s pyc=%s" % (d, [(str(x.relative_to(ROOT)).replace("\\", "/"),
                                   time.strftime("%H:%M:%S", time.localtime(x.stat().st_mtime)))
                                  for x in pyc]))

out = {"boundary": bound, "r12_pattern": G7M.DOUBLE_NEG_RE.pattern,
       "h5_pattern": PASTE.H5_DOUBLE_NEG_RE.pattern,
       "r12_gaps": gaps_r12, "gaps_both": gaps_both,
       "C_counts": counts, "C_rows": rows, "scores44": scores, "n_samples": len(SAMPLES),
       "write_domain_files": wf}
(HERE / "_h5v_full_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _h5v_full_out.json")
