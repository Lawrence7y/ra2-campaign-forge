# -*- coding: utf-8 -*-
"""_ocv_binding.py - reconstruct the 20 CLAIMS lines from the archived workflow
task book (payload.lowered JSON string) and hash them. Independent of _oc_binding.py.
Read-only outside stdout."""
import json, hashlib, re

P = "D:/Project/ra2-campaign-forge/.zcode/workflow-runs/dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs"
src = open(P, encoding="utf-8").read()
tail = src[src.index("export const payload = ") + len("export const payload = "):]
payload, end = json.JSONDecoder().raw_decode(tail)
lowered = payload["lowered"]
assert isinstance(lowered, str), "lowered is not a string"

# CLAIMS is built as an array of double-quoted JS string literals, joined with \n
m = re.search(r"const CLAIMS = \[(.*?)\]\.join\(\"\\n\"\)", lowered, re.S)
assert m, "CLAIMS array not found"
body = m.group(1)

lits, cur, in_str, esc = [], [], False, False
for ch in body:
    if not in_str:
        if ch == '"':
            in_str, cur = True, []
        continue
    if esc:
        cur.append(ch); esc = False; continue
    if ch == "\\":
        esc = True; cur.append(ch); continue
    if ch == '"':
        lits.append("".join(cur)); in_str = False; continue
    cur.append(ch)

def unesc(x):
    o, i = [], 0
    while i < len(x):
        if x[i] == "\\" and i + 1 < len(x):
            n = x[i + 1]
            if n == "n": o.append("\n"); i += 2
            elif n == '"': o.append('"'); i += 2
            elif n == "\\": o.append("\\"); i += 2
            elif n == "u": o.append(chr(int(x[i+2:i+6], 16))); i += 6
            else: o.append(n); i += 2
        else:
            o.append(x[i]); i += 1
    return "".join(o)

decoded = [unesc(x) for x in lits]
numbered = [x for x in decoded if re.match(r"^\d+\.\s", x)]
text = "\n".join(numbered)
raw = text.encode("utf-8")

# Also independently hash the 20 lines from the ask's CLAIMS field (verbatim copy)
ASK = [
'1「三件在 PENDING:92,105,129」→ 实为 4 行（+:117 d28）；错（数错）·数少。据 lead/PENDING_DECISIONS.md:92/105/117/129、STALE_PASS_INVENTORY.md:69/:107、本会话 _oc_ledger_scan_out.json。',
'2「四件在两台账共 3 行」→ 实为台账 4 行 + 交付件 3 行（REFSYNC_SCOPE_FIX.md:251/252/253），GOAL 0 行；错（数错）·数少+口径混淆。据 STALE_PASS_INVENTORY.md:57/:67/:107、_oc_ledger_scan_out.json。',
'3「indep_wrong_prob=0.0」→ 用 fp_rate 相乘(0.571429×0×0=0)；正确 q_i=fn_i/39 ⇒ q_r10×q_n13=0.037475345；错（口径错）·口径混淆。据 KEFF_CALC.md:110-112、_ke_calc.py:37、_oc_recompute_out.json。',
'4「3.75% 是三层连乘」→ 两层；三层=0.033631720(3.3632%)；错（数错）·数多+口径混淆。据 KEFF_CALC.md:102-104、_oc_recompute_out.json。',
'5「2.05 倍是后验口径」→ 2.0526 是似然；后验 1.8772/2.0727 倍；4.4474 类别错误；错（口径错）·口径混淆。据 KEFF_CALC.md:106-109/:256-258、_oc_recompute_out.json（本会话自纠一次 post2 写法后重跑）。',
'6「GP-A1 从 PASS→CATCH」→ 74 版 chain=PASS（漏判），PASS→CATCH 仅见于 DG 内存 Shim 设计实验；错（对象错）·把设计实验当实跑。据 CHAIN_VS_SINGLE.md:147、_cs_align_out.txt:19、DNEG_GENERATIVE.md:20/:362-368/:463。归档任务书只作假设性表述，无此断言。',
'7「c07_slot R10 多报的是真断言」→ 全是新误报（标题/表头/清单/条件式/占位符）；错（对象错）·串对象。据 GATE_REJUDGE_32.md:77/:91-94/:137。归档原句为「可能有…真断言，最值得查的方向」的假设。',
'8「门禁四条问题」→ 只复现 2 条，另 2 条未验；编排方串了 n4 域四条 FAIL；错（数错）·数多+串对象。据 GATE_N13_QUOTED_ASSERTION.md:390-404/:499、_gpv_n13_reg_out.txt:132/:138、N4_GATE_VERDICT.md:94/:201/:210。',
'9「三层共用同一套字面词表」→ 模块级常量不共用；共用的是运行时输入契约（55/74 行 tokens 相同）；【表述不精确但实质对】（20 条里唯一一条）。据 CHAIN_VS_SINGLE.md:93/:184。',
'10「r10×n13 高一致」→ 38/74=51.35%，φ=0.0293、MI=0.00062 bit；错（对象错）·串对象+口径混淆。据 EVIDENCE_INDEPENDENCE.md:127-128/:142、_ei_03_corr_out.json:19-26、_oc_recompute_out.json。归档任务书的 90% 是假设值。',
'11「n4_yi_final 是门禁挑错中稿」→ 该域 startswith(\'CANDIDATE_RESIGN\') 只匹配 1 件、无大小竞争；错（对象错）·串对象。据 GATE_DOC_NAME_FIX.md:234/:275/:302。归档任务书未找到该断言原件（未验）。',
'12「10 个域 / 5 个 bindings=0」→ 实为 13 域 / 6 域；错（数错）·数少。据 GATE_REJUDGE_32.md:51-53/:56/:161/:289。',
'13「最小硬项 4 件」→ 严格交集 2 件、全 lead/ 6 件、其它口径 3/4/6/7/8 件；错（对象错）·口径混淆。据 MINHARD_SET_CHECK.md:173-183、_mhv_verify_out.txt:42-44。',
'14「:22 同时逐字含两个 needle」→ 只含 N2(pos=172)，N1 find=-1（「」U+300C/D vs『』U+300E/F）；错（数错）·数多。据 MASKING_EFFECT_AUDIT.md:78-79/:87、_me_analyze_out.txt:6-7。',
'15「SELF_TEST=FAIL 是脚本缺陷」→ 跑的是非登记口径单 needle；登记口径双 needle 且 PASS 属掩蔽效应（坏针仍 PASS，判测试设计缺陷/不可信）；错（口径错）·口径混淆。据 MASKING_EFFECT_AUDIT.md:63-64/:104/:109-110/:373-377、REFSYNC_SCOPE_FIX.md:251-253。归档任务书未找到该断言（未验）。',
'16「按生成器式 any() 筛同族」→ 漏 check_d28（:96-97 先绑布尔列表再 any(present)）；错（对象错）·串对象。据 CHECK_FAMILY_LINEAGE.md:336/:410/:431/:439；注意 :336 把「漏判叙事」标 unconfirmed，本会话只采信代码级事实。',
'17「H5 修好就能插生产门禁」→ 仍不能插（四条前置条件只满足半条，11 条反例门槛未达标）；错（对象错）·口径混淆。据 _h5_DESIGN.md:283-288、H5_GOVERNANCE_FIX.md:460-464。★CLAIMS 里「仍有 4 项缺陷」这个数字在盘不匹配：§5.2 给 6 条、§6.3 给 8 条，标未验；归档任务书原为提问且复核规则⑦预设了防错闸门。',
'18「18 条增益可归因算法改进」→ 可归因算法=0 分；18 分是实现替换（in-sample）；错（口径错）·口径混淆。据 _sd_report.md:152/:161-163/:217/:219/:262/:373、COMPARABILITY_AUDIT.md:310/:340/:344；SCORE_DECOMP.md:18 的「不可归因=0 分」是另一口径，已注明勿混。',
'19「族级/全单元=32768 倍」→ 真值 32768.0=2^15、log10=4.51545；「心算成 16384」是代数错（少一个 2 因子）；错（数错）·代数错。据 PVALUE_RECALC.md:113、_pv_PVALUE_RECALC.md:65、_oc_recompute_out.json。★主断言「32768」本身是对的；错的是本次自述的复算。',
'20「ρ̄<0.8599」→ 真值 ρ̄<0.14013134380964332（log2_40=5.321928）；0.8599=round(1−ρ̄,4) 是取了补数；错（数错）·代数错。据 PVALUE_RECALC.md:165-166、_pv_PVALUE_RECALC.md:63-64、_oc_recompute_out.json + 本会话补数实算。★更正后的主断言「<0.14013」是对的。',
]
ask_raw = "\n".join(ASK).encode("utf-8")

print(json.dumps({
    "archive_literals": len(decoded),
    "archive_numbered": len(numbered),
    "archive_first": numbered[0][:40] if numbered else None,
    "archive_last": numbered[-1][:40] if numbered else None,
    "claim_lines_bytes": len(raw),
    "claim_lines_sha256": hashlib.sha256(raw).hexdigest(),
    "ask_claims_bytes": len(ask_raw),
    "ask_claims_sha256": hashlib.sha256(ask_raw).hexdigest(),
    "note": "claim_lines = archived CLAIMS array (the object bound by the report); ask_claims = the 20 condensed claims lines in the review ask (different text, info only)",
}, ensure_ascii=False, indent=2))
