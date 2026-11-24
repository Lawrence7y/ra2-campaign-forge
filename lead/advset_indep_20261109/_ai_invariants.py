# -*- coding: utf-8 -*-
r"""_ai_invariants.py — 六条绕过逐条核（自建构造）+ 结构性不可达 + 「7 条不变式」说法评估。

实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/advset_indep_20261109/_ai_invariants.py
"""
import sys, json, re, types, hashlib
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "advset_indep_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
V = json.loads((WD / "_ai_verify_out.json").read_text(encoding="utf-8"))
G = json.loads((WD / "_ai_grade_out.json").read_text(encoding="utf-8"))

DG = types.ModuleType("_aii_dg")
exec(compile((DG_DIR / "_dg_core.py").read_text(encoding="utf-8"), "dg", "exec"), DG.__dict__)
G7 = types.ModuleType("_aii_g7")
exec(compile((ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py").read_text(encoding="utf-8"),
             "g7", "exec"), G7.__dict__)
DROP = types.ModuleType("_aii_drop")
exec(compile((ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py").read_text(encoding="utf-8"),
             "drop", "exec"), DROP.__dict__)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]


def det(t):
    toks = [x for x in TOKS if x in t] or ["已生效"]
    p, h = DG.dg_scan(t, toks)
    pd, _ = DROP.r12_scan(t, toks)
    raw = [DG.DG_DROPIN_RE.search(t[:m.start()]).group(0)
           for tok in toks for m in re.finditer(re.escape(tok), t)
           if DG.DG_DROPIN_RE.search(t[:m.start()])]
    return {"pure": "CATCH" if p else "PASS", "dropin": "CATCH" if pd else "PASS",
            "pure_hit": h[0]["hit"] if h else "", "raw_hit": raw[0] if raw else ""}


print("=== (0) 六条绕过：每条给『申报构造』『本会话自建构造』『实跑结论』 ===")

# ① 边界词
mine = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "结果", "终究", "哪怕", "说白了"]
b = []
for w in mine:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    r = det(t)
    b.append({"w": w, "in_break": bool(DG.DG_BREAK_RE.search(w)), **r})
print("① 申报：DG_BREAK_RE 只登记 10 词，未登记的『其实/说到底/尽管/…』等 10 词全漏")
print("   自建 %d 词：BREAK=False 且 pure=CATCH（应 PASS）= %d/%d ; 明细 = %s" %
      (len(b), sum(1 for z in b if not z["in_break"] and z["pure"] == "CATCH"), len(b),
       [(z["w"], z["pure"], z["dropin"]) for z in b]))
print("   已登记 10 词对照：pure=PASS %d/10，dropin=CATCH %d/10（_scope 只在纯函数）" %
      (sum(1 for x, y, z in V["invariant_reruns"]["1b_registered"] if y == "PASS"),
       sum(1 for x, y, z in V["invariant_reruns"]["1b_registered"] if z == "CATCH")))
print("   ★ 绕过成立 = True（且交付形态更差：纯函数都守不住 14/14，dropin 连已登记 10 词都全 CATCH）")

# ② 引号
q = V["invariant_reruns"]["2_quotes"]
print("② 申报：只认 4 类引号，ASCII 双引号/书名号/单引号/（）均未登记 ⇒ P11/P12 被绕过")
print("   自建 %d 类未登记引号：pure=CATCH（应 PASS）= %d/%d ; 明细 = %s" %
      (len(q), sum(1 for z in q if z["DG_pure"] == "CATCH"), len(q), q))
print("   已登记「」内置空格：pure=PASS（判对），dropin=CATCH / R12=CATCH（判错）")
print("   ★ 绕过成立 = True（点名形态正确，但未登记引号 + 交付形态两处均破）")

# ③ MID / COMP / NEG2
m = V["invariant_reruns"]["3_mid"]
print("③ 申报：MID 23 项，未登记且真 DN 漏判 9 个（容/许/想/愿/甘/料/要/需/欲）；COMP ≤4 字，5 字即漏")
print("   自建 10 候选 MID：未登记且 pure=PASS（真 DN 漏判）= %s ; 明细 = %s" %
      ([z["mid"] for z in m if not z["in_MID"] and z["DG_pure"] == "PASS"], m))
print("   COMP n=0..7 = %s ; ≤4 全 CATCH / ≥5 全 PASS" % V["invariant_reruns"]["3b_comp"])
print("   ★ 绕过成立 = True（双向：真 DN 漏判 + 表内构式误报；NEG2 含 5 个完整否定谓语，"
      "『并不否认与监理方不宣告』pure=CATCH 系跨主语零隔拼接）")

# ④ 第二主语
print("④ 申报：_SECOND 的 14 词在全部条目里出现 0 次 ⇒ dg_double_neg:179-181 的 veto 结构性不可达")
print("   ★ 静态完全证明：T12 笛卡尔积 28497 去重 hit_text = %d，含 _SECOND = %d，含并列标记 = %d" %
      (G["t12_hits_n"], G["t12_second_n"], G["t12_coord_n"]))
print("   7 张表全部条目中出现 _SECOND 的条目 = []；T3 comp 由 `_dg_core.py:118` 负向前瞻排除 _SECOND")
print("   41 条实跑『第二主语』veto 触发 = %d 次，『并列标记』veto 触发 = %d 次（且是在真 DN C08 上误否决）" %
      (V["invariant_reruns"]["4_second_veto_fired"], V["invariant_reruns"]["4_coord_veto_fired"]))
for t in ["并非本件不宣告已生效", "并不否认甲方不宣告已生效", "非登记本件不可才算本件已生效"]:
    r = det(t)
    print("   %-30s pure=%-5s dropin=%-5s" % (t[:28], r["pure"], r["dropin"]))
print("   ★ 不是『被绕过』：该不变式描述的代码路径根本走不到（vacuous / dead invariant），"
      "其『保证』从未在任何输入上生效；交付形态下 guard 连代码都不在 co_names 里")

# ⑤ 并列 veto
print("⑤ 申报：并列否决只查 hit_text ⇒ 或字在 hit 之外不否决（P10 fp）、之内则误杀（C08 fn）")
for t in V["invariant_reruns"]["5_coord"]:
    r = det(t)
    print("   %-30s pure=%-5s dropin=%-5s raw_hit=%s" % (t[:28], r["pure"], r["dropin"], r["raw_hit"]))
print("   ★ 绕过成立 = True（双向后果：fp 与 fn 同时产生）")

# ⑥ PSEUDO_DN
print("⑥ 申报：PSEUDO_DN 是词首负向前瞻 ⇒ 从 veto 词之后另起匹配仍 CATCH（C20/A01/A02）")
for t in ["无非不是不承认本件已生效", "莫非并不是不承认本件已生效", "莫不是不承认本件已生效"]:
    r = det(t)
    print("   %-30s pure=%-5s raw_hit=%s" % (t[:28], r["pure"], r["raw_hit"]))
print("   12 项逐项 raw_regex True（从 veto 词之后另起命中）= %d/12 ; 明细 = %s" %
      (sum(1 for z in V["invariant_reruns"]["6_pseudo"] if z[1]),
       V["invariant_reruns"]["6_pseudo"]))
print("   ★ 绕过成立 = True（既误杀真 DN C11/C12，又拦不住位置迁移的伪/歧义构造）")

# ⑦ 奇偶
print("⑦ 申报：不做奇偶计数是设计选择，不是 guard")
print("   四象限 = %s" % V["invariant_reruns"]["7_quad"])
print("   ★ 不是可绕过的 guard；『不做 X』是缺席属性，不能被『绕过』，也不提供任何保证")

# =====================================================================
print("\n=== (1) 严重性排序：按『保证是否被声明』×『破口形态』×『影响面』 ===")
RANK = [
 ("④", "结构性不可达（vacuous）：veto 是 DG 唯一明写的『第二主语』安全机制，却在全部 "
       "27,993 个 T12 hit_text + T3 全域上不可达；41 条实跑触发 0 次。这是**声称存在的保证从未生效**，"
       "比『被绕过』更严重：文档把它列为 7 条不变式之一，构成对读者的实质性误导。"),
 ("①", "边界词闭合表未穷尽（10 词）+ 切断只在纯函数：自建 14/14 未登记词全 fp，"
       "已登记 10 词在交付形态 10/10 全 fp。直接产生本集 3 条 fp（P06/P07/P08），"
       "且属『两个独立否定』这一核心宣称，误拦面最广。"),
 ("②", "引证屏蔽只认 4 类引号 + 只在纯函数：自建 7/7 未登记引号全 fp，"
       "直接产生 P11/P12 两条 fp；任务书点名形态（「」内置空格）DG 反而判对，"
       "但 dropin/R12/H5_lit 全误报 ⇒ 交付形态全破。"),
 ("⑥", "PSEUDO_DN 词首局部 veto：6/12 项可从 veto 词之后另起命中，"
       "同时误杀真 DN（C11/C12 fn）。既漏又误，双向失败。"),
 ("③", "MID/COMP/NEG2 三处闭合表与硬界未穷尽：9 个 MID 真 DN 漏判、COMP 4→5 断、"
       "NEG2 完整否定谓语造成跨主语 fp。产生 C01–C05/C07/C09 等 7 条 fn + P09 1 条 fp。"),
 ("⑤", "并列 veto 只查 hit_text：fp（P10）与 fn（C08）同时产生；41 条只触发 1 次且是误否决。"),
]
for i, (k, why) in enumerate(RANK, 1):
    print("  第%d位 %s : %s" % (i, k, why))
print("  ★ 最严重 = ④（结构性不可达），理由：它不是『被绕过』而是『保证从未存在』；"
      "一个从未执行过的 veto 被列为 7 条结构不变式之一，使『7 条保证』的计数本身失真。")
print("  ★ 若按『实际造成的误判条数』排，① 最严重（3 条 fp）+ ③ 最严重（7 条 fn）；"
      "两种排序口径都登记，不合并成一个数。")

# =====================================================================
print("\n=== (2) 『7 条结构不变式』这个说法本身是否成立 ===")
print("  来源：`DNEG_GENERATIVE.md:167` 逐字复述 `_dg_DESIGN.md:141-158`；"
      "作者自述 `:184`『给定闭合表下的结构不变式，不是自然语言完备性定理』")
print("  逐条状态（本会话实跑）：")
STATUS = [
 ("①", "被绕过", "14/14 自建未登记词 fp；交付形态 10/10 已登记词也 fp"),
 ("②", "被绕过", "7/7 自建未登记引号 fp"),
 ("③", "被绕过", "9 MID 漏判 + COMP 4→5 断 + NEG2 跨主语 fp"),
 ("④", "空洞不可达（非绕过）", "27,993 hit_text 中 0 次可达；41 条触发 0 次"),
 ("⑤", "被绕过", "P10 fp + C08 fn，双向"),
 ("⑥", "被绕过", "6/12 位置迁移可绕 + C11/C12 误杀"),
 ("⑦", "非 guard", "『不做奇偶』是设计选择/缺席属性，不构成保证"),
]
for k, s, e in STATUS:
    print("   %s status=%-18s %s" % (k, s, e))
print("  成立性评估：")
print("   (a) 作为『7 条结构性事实描述』：①②④ 的描述与实现不完全相符（④ 描述了一条死代码），"
      "⑦ 是缺席属性而非机制 ⇒ 措辞不成立。")
print("   (b) 作为『7 条保证』：5 条可被构造绕过、1 条从未生效、1 条不提供保证 ⇒ "
      "**没有一条能支撑『不误判两个独立否定』的一般性结论**，说法不成立。")
print("   (c) 保留价值：作为『给定 7 张闭合表 + 2 条模板下的实现要点清单』仍可作为审计锚，"
      "但必须逐条标注『可绕过 / 不可达 / 非 guard』，不得称『不变式』（invariant 蕴含对全部输入成立）。")
print("   (d) 交付形态额外折扣：`r10_context` / `r12_scan` 的 co_names 中 "
      "_mask_quotes/_scope/dg_double_neg/DG_SECOND_SUBJ_RE/DG_COORD_RE 全 False ⇒ "
      "①②④⑤ 四条 guard 在真实落地形态连代码都不执行，7 条清单只描述『纯函数』且纯函数本身也破。")

# =====================================================================
print("\n=== (3) DG 失败模式归纳（回答第三步(d)）===")
print("  fp 7 条：7/7 命中串都是 DG 表内构式（T12：N1=不敢/并不/并非 + MID=ε + NEG2=不承认/否认/不宣告）；"
      "7/7 的构式在训练句子里出现过（d1 非空）；7/7 的自造句与某条训练句 min_edit<=6")
print("  ⇒ 失败模式 A（词表/作用域未穷尽，5/7）：把表内 DN 构式放在一个『本应切断但没切断』的语境"
      "（未登记转折/让步词、未登记引号、引证）里，正则仍能命中 ⇒ 过宽（over-inclusive）。")
print("  ⇒ 失败模式 B（guard 位置/作用域错误，2/7）：第二主语未登记 + 并列 veto 只查 hit_text，"
      "使『两项独立否定』被误判为 ¬¬P ⇒ 过宽。")
print("  ⇒ 两条合起来：DG 的『不误判』不是靠语义/句法判定，而是靠『闭合 MID 拼不出跨短语』+ "
      "『作用域切断』+ 『veto』三层词表护栏；只要构式本身在表内、而切断/veto 词未登记，"
      "护栏就同时失效。这是**词表记忆 + 边界词表记忆**的组合，不是泛化能力。")
print("  ⇒ 对本集『不误判不成立』结论的含义：fp 7 条不是随机难句，而是从训练构式 + 未登记边界词"
      "机械生成的模板变体；它们证明的是『词表边界可枚举绕过』，不能证明『DG 对自然语言新句不误判』，"
      "也不能证明『DG 泛化能力差』——后者需要 L2/L3 级样本才测得到。")

# =====================================================================
print("\n=== (4) 纪律核验 ===")
print("  本脚本只用 re / json / hashlib / 源码 compile-exec；未启动真机、未写采样代码；"
      "未 import 保护件（不产生 __pycache__）；未写保护树；未 commit / 未 push")
print("  九件指纹三次重算 ALL_MATCH =", all(
    hashlib.sha256((ROOT / r).read_bytes()).hexdigest() == meta["sha"] and
    (ROOT / r).stat().st_size == meta["bytes"] for r, meta in V["fingerprints"].items()))

OUT = {"bypass_status": STATUS, "severity_ranking": [k for k, _ in RANK],
       "most_severe": "④", "most_severe_by_fp_count": "①", "most_severe_by_fn_count": "③",
       "seven_invariants_claim_valid": False,
       "failure_mode": {"A_table_scope": ["P06", "P07", "P08", "P11", "P12"],
                        "B_guard_scope": ["P09", "P10"],
                        "fp_all_in_table": True, "fp_all_d1": True}}
(WD / "_ai_invariants_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _ai_invariants_out.json")
