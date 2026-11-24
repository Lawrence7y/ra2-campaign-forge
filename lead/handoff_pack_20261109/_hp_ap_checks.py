# -*- coding: utf-8 -*-
# _hp_ap_checks.py — 批准包交付轮（APPROVAL_PACK.md 撰写员）只读核验脚本
# 对九条改文做逐字节三方同文比对、14 行映射、复核三瑕疵复验、counterpart 域探针、复核绑定行复现。
# 只读不写源域；输出到 stdout。运行: python -I -X utf8 _hp_ap_checks.py
import hashlib, os, json, re, difflib

ROOT = r"D:\Project\ra2-campaign-forge"
def P(rel): return os.path.join(ROOT, rel.replace("/", os.sep))
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()
def rd(p):
    with open(p, "rb") as f: return f.read().decode("utf-8")
def L(p): return rd(p).splitlines()
def blocks(path):
    out, cur = [], None
    for ln in rd(path).splitlines():
        s = ln.strip()
        if s.startswith("```"):
            if cur is None: cur = []
            else: out.append("\n".join(cur)); cur = None
        elif cur is not None: cur.append(ln)
    return out

# ---------- B. 复核绑定行复现 ----------
hp = P("lead/handoff_pack_20261109")
names15 = ["_hp_OVERVIEW.md"] + ["_hp_U%d.md" % i for i in range(1, 10)] + \
          ["_hp_PENDING_AND_SIGNOFFS.md", "_hp_APPROVER_RUNBOOK.md", "_hp_APPENDIX_FINGERPRINTS.md", "_hp_HANDOFF_DECLARATION.md", "_hp_fp_verify.py"]
tot = sum(os.path.getsize(os.path.join(hp, n)) for n in names15)
print("[B] sum15 =", tot, "(target 55567)")
target = "ac8bc70519c506359cab77a3b27f2c1275c2d8c5083071e2a3e5399a4047de8d"
def cath(ns):
    h = hashlib.sha256()
    for n in ns: h.update(open(os.path.join(hp, n), "rb").read())
    return h.hexdigest()
m14 = [n for n in names15 if n != "_hp_fp_verify.py"]
for k, o in [("manifest15", names15), ("sorted15", sorted(names15)), ("manifest14", m14), ("sorted14", sorted(m14))]:
    h = cath(o)
    print("[B]", k, h, "MATCH" if h == target else "no")

# ---------- 改文正本常量（任务下发【改文正本】逐字转录） ----------
J2 = "pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后读取正常（post.read_error 为空）；post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行）"
J5 = "跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）"
J4 = "跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行），不降级、不静默、不给 high"
C5 = "`pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后读取正常（`post.read_error` 为空）；`post.read_error` 非空时先落 `post_read_error`（码序 `read_error` 出口先于 `unknown` 出口，见 :5 行）"
C6 = "跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口（★ N1 码序 `read_error` 出口先于一切 pre 分支；pre 任意态——`unknown`/`absent_confirmed`/`present`/`error`——+ `read_error` 均落本行，`preState` 列的 `present` 为最常见登记态，匹配以本 condition 为准）"
C7 = "跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行）"

cells = json.loads(rd(P("lead/u5u6_mirror_20261109/_m5_cells.json")))
print("[C] cells==ask:", cells["json2_new"] == J2, cells["json5_new"] == J5, cells["json4_new_recommended"] == J4,
      cells["U5"]["new_condition_cell"] == C5, cells["U6"]["new_condition_cell"] == C6, cells["U7"]["new_condition_cell"] == C7)

sm = L(P("lead/b2b_design_20261106/STATE_MATRIX.json"))
smj = json.loads(rd(P("lead/b2b_design_20261106/STATE_MATRIX.json")))
print("[C] STATE_MATRIX strict json, items =", len(smj))
cond2 = smj[0]["condition"]; cond4 = smj[2]["condition"]; cond5 = smj[3]["condition"]
pf2 = L(P("lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md"))
r5 = L(P("lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md"))
pf2f = L(P("lead/v2_precision_fix_20261108/_pf2_findings_20261109.md"))
b2b = L(P("lead/b2b_design_20261106/B2B_DESIGN.md"))
w2 = L(P("lead/w2_samecause_20261109/W2_SAME_CAUSE.md"))
rc = L(P("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md"))
v2 = L(P("lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md"))

# ---------- U1 ----------
bU1 = blocks(P("lead/handoff_pack_20261109/_hp_U1.md"))
REP = pf2[103]
new91 = v2[90].replace("删除行数 0", REP)
print("[U1] pack原文==V2:91:", bU1[0] == v2[90], "| pack替换文本==pf2:104:", bU1[1] == REP, "| 拼装行==pack拼装:", new91 == bU1[2], "| replace次数:", v2[90].count("删除行数 0"))
l27 = pf2f[26]
i0 = l27.find("→「") + 2; i1 = l27.find("」，行内其余文字不动")
seg = l27[i0:i1]
print("[U1] findings:27 变体去粗体==pf2:104:", seg.replace("**", "") == REP, "| 粗体对数:", seg.count("**") // 2)

# ---------- U2 ----------
bU2 = blocks(P("lead/handoff_pack_20261109/_hp_U2.md"))
print("[U2] pack原文==JSON:2整行:", bU2[0] == sm[1], "| pf2:126整行含cond2:", cond2 in pf2[125], "| pack改后==J2==pf2:193:", bU2[1] == J2 == pf2[192], "| 拼装整行==pack拼装:", sm[1].replace(cond2, J2) == bU2[2], "| replace次数:", sm[1].count(cond2))

# ---------- U3 ----------
bU3 = blocks(P("lead/handoff_pack_20261109/_hp_U3.md"))
l132 = r5[131]; inner = l132[l132.find("「") + 1:l132.rfind("」")]
print("[U3] pack原文==JSON:5整行:", bU3[0] == sm[4], "| J5==cond5+追加:", J5.startswith(cond5), "| 追加段==pack追加块:", J5[len(cond5):] == bU3[1], "| pack全文块==J5:", bU3[2] == J5, "| row5:132去「」==J5:", inner == J5)

# ---------- U4 ----------
bU4 = blocks(P("lead/handoff_pack_20261109/_hp_U4.md"))
l135 = r5[134]
CLAUSE = l135[l135.find("「") + 1:l135.rfind("」")]
k = cond4.find("独立 error 出口") + len("独立 error 出口")
mid = J4[J4.find("独立 error 出口") + len("独立 error 出口"):J4.find("，不降级")]
print("[U4] row5:135子句==J4中段:", CLAUSE == mid, "| pack原文==JSON:4整行:", bU4[0] == sm[3], "| pack加句块==CLAUSE:", bU4[1] == CLAUSE, "| pack推荐块==J4:", bU4[2] == J4, "| J4==拼接装配:", J4 == cond4[:k] + CLAUSE + cond4[k:])

# ---------- U5/U6/U7 ----------
bU5 = blocks(P("lead/handoff_pack_20261109/_hp_U5.md"))
bU6 = blocks(P("lead/handoff_pack_20261109/_hp_U6.md"))
bU7 = blocks(P("lead/handoff_pack_20261109/_hp_U7.md"))
mt = rd(P("lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md"))
def colswap(orig, cell):
    parts = orig.split("|")
    return "|".join(parts[:3] + [" " + cell + " "] + parts[4:])
n148 = colswap(bU5[0], C5); n150 = colswap(bU7[0], C7); n151 = colswap(bU6[0], C6)
print("[U5] pack原文==B2B:148:", bU5[0] == b2b[147], "| 改后==列3换cell:", bU5[1] == n148, "| 镜像件含改后行:", mt.count(n148) >= 1)
print("[U6] pack原文==B2B:151:", bU6[0] == b2b[150], "| 改后==列3换cell:", bU6[1] == n151, "| 镜像件含改后行:", mt.count(n151) >= 1)
print("[U7] pack原文==B2B:150:", bU7[0] == b2b[149], "| 改后==列3换cell:", bU7[1] == n150, "| 镜像件含改后行:", mt.count(n150) >= 1)

# ---------- 映射 14 行 ----------
bad = []
for i in range(2, 16):
    j = smj[i - 2]
    cols = [c.strip().strip("`") for c in b2b[147 + (i - 2)].split("|")]
    ok = (j["state"] == cols[1] and j["preState"] == cols[2] and j["verdict"] == cols[4] and j["confidence"] == cols[5]
          and str(j["usableAsCrashEvidence"]).lower() == cols[7].strip("`"))
    if not ok: bad.append(i)
print("[MAP] JSON i ↔ B2B 148+(i-2) 14 行五字段:", "ALL EQUAL" if not bad else ("MISMATCH " + str(bad)))

# ---------- U8 ----------
bU8 = blocks(P("lead/handoff_pack_20261109/_hp_U8.md"))
l154 = rc[153]
print("[U8] 受核件:154 前缀:", l154.startswith("2. **W2**："))
a, b = bU8[0], l154
if len(a) == len(b):
    d = [(i, repr(a[i]), repr(b[i])) for i in range(len(a)) if a[i] != b[i]]
    print("[U8] pack原文引文 vs 实:154 等长, diff数 =", len(d), d[:4])
else:
    sm2 = difflib.SequenceMatcher(None, a, b).get_opcodes()
    print("[U8] 长度不等", len(a), len(b), sm2[:6])
w122 = w2[121]; assert w122.startswith(">"), w122[:5]
w122c = w122[2:]
print("[U8] pack改后==W2:122引用块内容:", bU8[1] == w122c, "| 改后与实:154链体不同（应不同）:", bU8[1] != l154[len("2. **W2**："):])

# ---------- U9 ----------
bU9 = blocks(P("lead/handoff_pack_20261109/_hp_U9.md"))
l146 = rc[145]; l147 = rc[146]
w124 = w2[123]; mk = "建议注记："
u9full = w124[w124.find(mk) + len(mk):]
print("[U9] pack评级格原文在实:146:", bU9[0] in l146, "| 实:147含O1格(不在九条):", "**罕见**（句柄残留/AV 锁/磁盘满；评级为推理）" in l147)
print("[U9] W2:124建议注记以。结尾:", u9full.endswith("。"), "| 去。后==pack改后块:", (u9full[:-1] if u9full.endswith("。") else u9full) == bU9[1])

# ---------- P1 / P10 / grep ----------
print("[P1] pf2:196 含最小修复只动一行:", "最小修复只动一行" in pf2[195],
      "| row5「可接受但不完整」行:", [i + 1 for i, x in enumerate(r5) if "可接受但不完整" in x],
      "| row5:138 含同步:148+登记残留:", ("必须同步 :148" in r5[137] and "如实登记 W2/O1 残留" in r5[137]))
print("[P10] 受核件:90 含旧措辞:", "同一持续根因（句柄/ACL 横跨两时点）可一次造成两半" in rc[89])
hits = sorted(i + 1 for i, x in enumerate(rc) if re.search(r"W2|同一持续根因|罕见", x))
print("[P10] 受核件 grep 命中行:", hits)
v2t = rd(P("lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md"))
rst = rd(P("lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md"))
pat = r"B2B_DESIGN\.md:1[45][0-9]|STATE_MATRIX\.json:[0-9]"
print("[V2] 行级引用命中:", len(re.findall(pat, v2t)),
      "| V2/重签件 含 MATRIX_DEFECT|matrix_reach:", len(re.findall(r"MATRIX_DEFECT|matrix_reach", v2t)), len(re.findall(r"MATRIX_DEFECT|matrix_reach", rst)))

# ---------- counterpart 域 ----------
cd = P("lead/counterpart_fix_20261109")
fs = sorted(os.listdir(cd))
print("[CF] 域内件数 =", len(fs), fs)
cfmd = rd(os.path.join(cd, "COUNTERPART_FIX.md"))
cftg = rd(os.path.join(cd, "_cf_counterpart_vs_tighten_20261109.md"))
frags = {"F1九hunk实测": "九 hunk 内实测", "F2码序unknown": "码序 read_error 出口先于 unknown 出口", "F3★N1": "★ N1 码序",
         "F4不降级": "不降级、不静默、不给 high", "F5仍先落": "post.read_error 非空时仍先落 post_read_error",
         "F6源读面": "源读面持续阻断", "F7跑后读取正常": "跑后读取正常", "F8极罕见档": "（均极罕见档；全部为推理、未验）", "F9同趟收尾": "同趟收尾复制"}
for nm, t in [("COUNTERPART_FIX", cfmd), ("_cf_tighten", cftg)]:
    print("[CF]", nm, {k: t.count(v) for k, v in frags.items()})
w122c2 = w122c
u9c = u9full
fulls = {"J2": J2, "J5": J5, "J4": J4, "C5": C5, "C6": C6, "C7": C7, "REP": REP, "U8new": w122c2, "U9new": u9c}
for nm, t in [("COUNTERPART_FIX", cfmd), ("_cf_tighten", cftg)]:
    print("[CF]", nm, {k: (v in t) for k, v in fulls.items()})
print("[CF] COUNTERPART_FIX.md sha =", sha(os.path.join(cd, "COUNTERPART_FIX.md")), "bytes =", os.path.getsize(os.path.join(cd, "COUNTERPART_FIX.md")))
print("[CF] UNIFIED_TEXT_FIX.md sha =", sha(P("lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md")), "bytes =", os.path.getsize(P("lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md")), "(转引值 ec0fb8ec…/42172)")

# ---------- S. 本交付件 APPROVAL_PACK.md 逐字块自检 ----------
apb = blocks(P("lead/handoff_pack_20261109/APPROVAL_PACK.md"))
# 顺序：U1(0原,1改) U2(2原,3改) U3(4原,5追加,6全文) U4(7原,8加句,9全文) U5(10原,11改) U6(12原,13改) U7(14原,15改) U8(16原,17改) U9(18原,19改)
chk = [
    ("U1原", apb[0] == v2[90]), ("U1改", apb[1] == REP),
    ("U2原", apb[2] == sm[1]), ("U2改", apb[3] == J2),
    ("U3原", apb[4] == sm[4]), ("U3追加", apb[5] == J5[len(cond5):]), ("U3全文", apb[6] == J5),
    ("U4原", apb[7] == sm[3]), ("U4加句", apb[8] == CLAUSE), ("U4全文", apb[9] == J4),
    ("U5原", apb[10] == b2b[147]), ("U5改", apb[11] == n148),
    ("U6原", apb[12] == b2b[150]), ("U6改", apb[13] == n151),
    ("U7原", apb[14] == b2b[149]), ("U7改", apb[15] == n150),
    ("U8原", apb[16] == rc[153]), ("U8改", apb[17] == w122c),
    ("U9原", apb[18] == "**罕见**（同根因双时点；评级为推理）"), ("U9改", apb[19] == u9full),
]
print("[S] APPROVAL_PACK 逐字块 == 源件实文:", chk)
print("[S] 全部成立:", all(x[1] for x in chk), "| 块总数:", len(apb))
