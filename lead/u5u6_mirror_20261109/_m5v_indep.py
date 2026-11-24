# -*- coding: utf-8 -*-
# _m5v_indep.py —— 复核员独立比对：源件逐字抽取 → 白名单剥离 → 回件 B2B 侧硬比对（只读）
import json, re

BASE = r"D:\Project\ra2-campaign-forge"
def rd(rel):
    with open(BASE + "\\" + rel.replace("/", "\\"), encoding="utf-8") as f:
        return f.read().splitlines()

b2b = rd("lead/b2b_design_20261106/B2B_DESIGN.md")
sm  = rd("lead/b2b_design_20261106/STATE_MATRIX.json")
pf2 = rd("lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md")
row5 = rd("lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md")
list_ = rd("lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md")
fixmd = "\n".join(rd("lead/u5u6_mirror_20261109/_m5_U5U6U7_FIX_20261109.md"))
cells = json.load(open(BASE + r"\lead\u5u6_mirror_20261109\_m5_cells.json", encoding="utf-8"))

R = []
def ck(name, ok, detail=""):
    R.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"\n        {detail}" if detail and not ok else ""))

def inner_quotes(line):
    a, b = line.find("「"), line.rfind("」")
    return line[a+1:b] if a != -1 and b != -1 and b > a else None

norm = lambda s: s.replace("`", "")

# ---- 回件侧文本（硬编码自待核回件 texts 字段）----
HJ_U5_OLD = "| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |"
HJ_U7_OLD = "| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |"
HJ_U6_OLD = "| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |"
HJ_U5_C3 = "`pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后读取正常（`post.read_error` 为空）；`post.read_error` 非空时先落 `post_read_error`（码序 `read_error` 出口先于 `unknown` 出口，见 :5 行）"
HJ_U6_C3 = "跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口（★ N1 码序 `read_error` 出口先于一切 pre 分支；pre 任意态——`unknown`/`absent_confirmed`/`present`/`error`——+ `read_error` 均落本行，`preState` 列的 `present` 为最常见登记态，匹配以本 condition 为准）"
HJ_U7_C3 = "跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行）"
HJ_U5_AFTER = "| `unknown` | `unknown` | " + HJ_U5_C3 + " | `unknown` | `none` | `None` | `false` |"
HJ_U7_AFTER = "| `error` | `error` | " + HJ_U7_C3 + " | `error_pre_snapshot` | `none` | `None` | `false` |"
HJ_U6_AFTER = "| `post_read_error` | `present` | " + HJ_U6_C3 + " | `post_read_error` | `none` | `None` | `false` |"

# ---- 源件逐字抽取（不经撰写人 cells）----
SRC_JSON2 = pf2[192].strip()                      # pf2 = V2_PRECISION_FIX_PROPOSAL.md :193
SRC_JSON5 = inner_quotes(row5[131])               # row5 :132 内侧（去外侧「」）
SRC_ADD   = inner_quotes(row5[134])               # row5 :135 内侧
WL_U5 = ["候选 :4643 先于 :4648，", "跑前快照"]
WL_U6 = ["：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支"]
WL_U7 = ["，不降级、不静默、不给 high"]

ck("② :148 原文整行与回件逐字一致", b2b[147] == HJ_U5_OLD, repr(b2b[147]))
ck("② :150 原文整行与回件逐字一致", b2b[149] == HJ_U7_OLD, repr(b2b[149]))
ck("② :151 原文整行与回件逐字一致", b2b[150] == HJ_U6_OLD, repr(b2b[150]))
jrows = json.loads("\n".join(sm))
ck("JSON:2 现状 condition（含 跑后任意文件状态）", jrows[0]["condition"] == "pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后任意文件状态")
ck("JSON:4 现状 condition（含既有尾句）", jrows[2]["condition"] == "跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口，不降级、不静默、不给 high")
ck("JSON:5 现状 condition", jrows[3]["condition"] == "跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口")

# ---- 源件 ↔ cells 正本 ----
ck("pf2:193 == cells.json2_new", SRC_JSON2 == cells["json2_new"], repr(SRC_JSON2))
ck("row5:132 内侧 == cells.json5_new", SRC_JSON5 == cells["json5_new"], repr(SRC_JSON5))
ADD = "（post.read_error 非空时仍先落 post_read_error，见 :5 行）"
ck("row5:135 内侧 == U4/U7 加句", SRC_ADD == ADD, repr(SRC_ADD))
ck("清单:83 转载加句一致（剥代码跨接反引号）", list_[82].strip().strip("`") == ADD, repr(list_[82].strip()))
ck("清单:111 转载加句一致（剥代码跨接反引号）", list_[110].strip().strip("`") == ADD, repr(list_[110].strip()))
HJ_U5_JSON = "pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后读取正常（post.read_error 为空）；post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行）"
ck("③ 回件 U5 的 JSON 侧对照引文 == pf2:193 逐字（无漏词）", HJ_U5_JSON == SRC_JSON2, repr(HJ_U5_JSON))
recon_json4 = jrows[2]["condition"].replace("独立 error 出口", "独立 error 出口" + ADD, 1)
ck("JSON:4 推荐拼后（独立 error 出口 后插句）== cells.json4_new_recommended", recon_json4 == cells["json4_new_recommended"], repr(recon_json4))
HJ_U7_JSON = "跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行），不降级、不静默、不给 high"
ck("③ 回件 U7 的 JSON 侧拼后全文 == 源件加句按推荐点拼入", HJ_U7_JSON == recon_json4, repr(HJ_U7_JSON))
ck("_pf2_findings:35 转引 JSON:2 改文与 pf2:193 一致", SRC_JSON2 in rd("lead/v2_precision_fix_20261108/_pf2_findings_20261109.md")[34])

# ---- ★④ 核心语义对应：源件剥白名单 == 回件 B2B 侧（去反引号）----
def strip_wl(s, wl):
    for d in wl:
        assert d in s, f"白名单片段不在源文本中: {d!r}"
        s = s.replace(d, "", 1)
    return s
ck("U5: pf2:193 − 白名单 == 回件:148 第3列（去反引号）", strip_wl(SRC_JSON2, WL_U5) == norm(HJ_U5_C3),
   f"src-wl={strip_wl(SRC_JSON2, WL_U5)!r}\n        b2b        ={norm(HJ_U5_C3)!r}")
ck("U6: row5:132 内侧 − 白名单 == 回件:151 第3列（去反引号）", strip_wl(SRC_JSON5, WL_U6) == norm(HJ_U6_C3),
   f"src-wl={strip_wl(SRC_JSON5, WL_U6)!r}\n        b2b        ={norm(HJ_U6_C3)!r}")
ck("U7: JSON:4拼后 − 既有尾句 == 回件:150 第3列（去反引号）", strip_wl(recon_json4, WL_U7) == norm(HJ_U7_C3),
   f"src-wl={strip_wl(recon_json4, WL_U7)!r}\n        b2b        ={norm(HJ_U7_C3)!r}")
# 判别谓词双侧同在（B2B 侧去反引号）
PRED = {
 "U5": (SRC_JSON2, HJ_U5_C3, ["跑后读取正常（post.read_error 为空）", "post.read_error 非空时先落 post_read_error", "码序 read_error 出口先于 unknown 出口", "见 :5 行"]),
 "U6": (SRC_JSON5, HJ_U6_C3, ["★ N1 码序 read_error 出口先于一切 pre 分支", "pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行", "preState 列的 present 为最常见登记态，匹配以本 condition 为准"]),
 "U7": (recon_json4, HJ_U7_C3, ["（post.read_error 非空时仍先落 post_read_error，见 :5 行）"]),
}
for k, (js, bs, ps) in PRED.items():
    miss = [p for p in ps if p not in js or p not in norm(bs)]
    ck(f"④ {k} 判别谓词 JSON 侧与 B2B 侧（去反引号）逐段同文", not miss, f"缺失: {miss}")
    ck(f"④ {k} B2B 侧无「任意」类旧语义残留", not any(t in norm(bs) for t in ("跑后任意", "任意文件状态")))
# B2B 侧未引入 JSON 之外的新语义：B2B 改文（去反引号）必须 ⊆ JSON 改文 − 白名单（即上三条等式已覆盖；反向再验 B2B ⊆ JSON）
ck("④ U5/U6/U7 B2B 改文是 JSON 改文的子串（剥白名单后完全等号，无 B2B 独有语句）",
   all(strip_wl(js, wl) == norm(bs) for (js, bs, _), wl in
       zip(PRED.values(), (WL_U5, WL_U6, WL_U7))))

# ---- 回件 ↔ 落盘正本/交付件 ----
ck("回件 U5 第3列 == cells.U5.new_condition_cell", HJ_U5_C3 == cells["U5"]["new_condition_cell"])
ck("回件 U6 第3列 == cells.U6.new_condition_cell", HJ_U6_C3 == cells["U6"]["new_condition_cell"])
ck("回件 U7 第3列 == cells.U7.new_condition_cell", HJ_U7_C3 == cells["U7"]["new_condition_cell"])
ck("交付件 FIX.md 含 U5 改后整行", HJ_U5_AFTER in fixmd)
ck("交付件 FIX.md 含 U6 改后整行", HJ_U6_AFTER in fixmd)
ck("交付件 FIX.md 含 U7 改后整行", HJ_U7_AFTER in fixmd)

# ---- 行长复算 ----
def after_line(old, c3):
    parts = old.split("|"); parts[3] = " " + c3 + " "; return "|".join(parts)
for ln, old, c3, exp in ((148, HJ_U5_OLD, HJ_U5_C3, 226), (150, HJ_U7_OLD, HJ_U7_C3, 159), (151, HJ_U6_OLD, HJ_U6_C3, 318)):
    nl = after_line(old, c3)
    ck(f"行长 :{ln} {len(old)}→{len(nl)}（回件称 118/112/155 → 226/159/318）", len(nl) == exp, f"实测 {len(nl)}")
    ck(f":{ln} 改后行不含新增管道符且仍 7 列", "|" not in c3 and len(nl.split("|")) == 9)

# ---- 结构与惯例 ----
ck("B2B 表头定位唯一（「| state |」仅 :146 一处）", [i+1 for i, l in enumerate(b2b) if l.startswith("| state |")] == [146])
ck("B2B :144 含「下表与之逐行一致」", "下表与之逐行一致" in b2b[143])
ck("B2B :142/:168 含母本 :439-440 口径（is_new 依据）", ":439-440" in b2b[141] and ":439-440" in b2b[167])
cnt = lambda t, doc: sum(l.count(t) for l in doc)
ck("「跑后任意」B2B=1@:148 / JSON=1@:2", cnt("跑后任意", b2b) == 1 and "跑后任意" in b2b[147] and cnt("跑后任意", sm) == 1 and "跑后任意" in sm[1])
ck("「任意文件状态」B2B=0 / JSON=1@:2", cnt("任意文件状态", b2b) == 0 and cnt("任意文件状态", sm) == 1 and "任意文件状态" in sm[1])
jl = [i+1 for i, l in enumerate(sm) if "「" in l]
bl = [i+1 for i, l in enumerate(b2b[147:161], start=148) if "「" in l]
print(f"    [事实] STATE_MATRIX.json 含「」的行: {jl}（回件判读依据称『JSON 14 行 condition 均无「」』）")
print(f"    [事实] B2B :148-:161 含「」的行: {bl}")
ck("批内未改行 = 11（回件称『本表 13 个未改行』）", 14 - 3 == 11)
ptr_b2b = {i+1: re.findall(r"（:\d+", l) for i, l in enumerate(b2b[147:161], start=148) if re.findall(r"（:\d+", l)}
ptr_json = {i+2: re.findall(r"（:\d+", jrows[i]["condition"]) for i in range(14) if re.findall(r"（:\d+", jrows[i]["condition"])}
print(f"    [事实] B2B 14 行内含「（:行号」指针的行: {ptr_b2b or '无'}；JSON 14 行内: {ptr_json}")
print(f"\n结论: {sum(R)}/{len(R)} PASS")
