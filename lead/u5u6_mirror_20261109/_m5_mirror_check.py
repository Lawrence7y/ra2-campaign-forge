# -*- coding: utf-8 -*-
# _m5_mirror_check.py —— B2B_DESIGN 表 ↔ STATE_MATRIX.json 逐行镜像校验（对两件被核对象只读）
# 用法：
#   python -I -X utf8 _m5_mirror_check.py           # 现状（改前）：不变式校验 + 三处现状取证
#   python -I -X utf8 _m5_mirror_check.py --after   # 改后模拟：内存中应用 U2-U7 全部六处，跑完整门禁（不落盘）
# 改文正本 = 同目录 _m5_cells.json；改文实际落盘后用本脚本（不带 --after）复跑即为正式门禁。
import json, sys

BASE = "D:/Project/ra2-campaign-forge/"
B2B_REL = "lead/b2b_design_20261106/B2B_DESIGN.md"
SM_REL = "lead/b2b_design_20261106/STATE_MATRIX.json"
CELLS = json.load(open(BASE + "lead/u5u6_mirror_20261109/_m5_cells.json", encoding="utf-8"))

CHECKS = []
def check(name, ok, detail=""):
    CHECKS.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f"\n        {detail}"))

def parse_b2b_table(text):
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("| state |"))
    assert lines[start + 1].startswith("|:--"), "表分隔线未找到"
    rows, i = [], start + 2
    while i < len(lines) and lines[i].startswith("|"):
        c = [x.strip() for x in lines[i].split("|")]
        rows.append({"line": i + 1, "state": c[1].strip("`"), "preState": c[2].strip("`"),
                     "condition": c[3], "verdict": c[4].strip("`"), "confidence": c[5].strip("`"),
                     "is_new": c[6].strip("`"), "usable": c[7].strip("`")})
        i += 1
    return rows

def norm(s):
    return s.replace("`", "")

def strip_deletes(s, deletes):
    for d in deletes:
        assert d in s, f"白名单片段不在 JSON 侧文本中: {d!r}"
        s = s.replace(d, "", 1)
    return s

after = "--after" in sys.argv
b2b_text0 = open(BASE + B2B_REL, encoding="utf-8").read()
sm_text0 = open(BASE + SM_REL, encoding="utf-8").read()
json_rows0 = json.loads(sm_text0)

if after:
    # 内存模拟 U5/U6/U7（B2B 侧）与 U2/U3/U4（JSON 侧），不落盘
    b2b_lines = b2b_text0.splitlines()
    old_cells = {}
    for idx, key in ((0, "U5"), (2, "U7"), (3, "U6")):
        ln = 148 + idx
        cells = b2b_lines[ln - 1].split("|")
        old_cells[idx] = cells[3].strip()
        cells[3] = " " + CELLS[key]["new_condition_cell"] + " "
        b2b_lines[ln - 1] = "|".join(cells)
    # 拼接位置守卫：确认改的是预期的三格
    assert old_cells[0].endswith("，跑后任意"), f":148 现状格异常: {old_cells[0]!r}"
    assert old_cells[2] == "跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口", f":150 现状格异常"
    assert old_cells[3] == "跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口", f":151 现状格异常"
    b2b_text = "\n".join(b2b_lines)
    sm_lines = sm_text0.splitlines()
    for j, newc in ((0, CELLS["json2_new"]), (2, CELLS["json4_new_recommended"]), (3, CELLS["json5_new"])):
        assert json_rows0[j]["condition"] in sm_lines[j + 1], f"JSON:{j+2} 现状 condition 与预期不符"
        sm_lines[j + 1] = sm_lines[j + 1].replace(json_rows0[j]["condition"], newc)
    sm_text = "\n".join(sm_lines)
else:
    b2b_text, sm_text = b2b_text0, sm_text0

b2b_rows = parse_b2b_table(b2b_text)
json_rows = json.loads(sm_text)

# 1) 结构不变式：14 行、逐行对齐
check("行数 14/14", len(b2b_rows) == 14 and len(json_rows) == 14,
      f"b2b={len(b2b_rows)} json={len(json_rows)}")

# 2) 五个共用字段逐行全等（:148+i ↔ JSON:{2+i}）
mm = []
for idx, (b, j) in enumerate(zip(b2b_rows, json_rows)):
    pairs = [("state", b["state"], j["state"]), ("preState", b["preState"], j["preState"]),
             ("verdict", b["verdict"], j["verdict"]), ("confidence", b["confidence"], j["confidence"]),
             ("usableAsCrashEvidence", {"true": True, "false": False}.get(b["usable"], b["usable"]),
              j["usableAsCrashEvidence"])]
    for fname, bv, jv in pairs:
        if bv != jv:
            mm.append(f":{b['line']}↔JSON:{idx+2} {fname}: b2b={bv!r} json={jv!r}")
check("五枚举字段（state/preState/verdict/confidence/usableAsCrashEvidence）14 行逐行全等", not mm, "; ".join(mm))
check("is_new 为 B2B 独有列（STATE_MATRIX.json 各行无 is_new 键）", all("is_new" not in j for j in json_rows))

# 3) 三处改文的判别谓词双侧同在 / 禁词双侧同无（B2B 侧归一化去反引号后比对）
TOKENS = {
    0: (["跑后读取正常（post.read_error 为空）", "post.read_error 非空时先落 post_read_error",
         "码序 read_error 出口先于 unknown 出口", "见 :5 行"], ["跑后任意", "任意文件状态"]),
    2: (["（post.read_error 非空时仍先落 post_read_error，见 :5 行）"], []),
    3: (["★ N1 码序 read_error 出口先于一切 pre 分支",
         "pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行",
         "匹配以本 condition 为准"], []),
}
tf = []
for idx, (musts, bans) in TOKENS.items():
    jc, bc = json_rows[idx]["condition"], norm(b2b_rows[idx]["condition"])
    for t in musts:
        if t not in jc or t not in bc:
            tf.append(f"JSON:{idx+2}/:{b2b_rows[idx]['line']} 谓词双侧不齐 {t!r} (json={t in jc}, b2b={t in bc})")
    for t in bans:
        if t in jc or t in bc:
            tf.append(f"JSON:{idx+2}/:{b2b_rows[idx]['line']} 禁词仍在一侧 {t!r}")
if after:
    check("U5/U6/U7 判别谓词双侧同在、旧语义词（跑后任意/任意文件状态）双侧清零", not tf, "; ".join(tf))
else:
    print(f"[现状取证·改前预期不齐] 判别谓词/禁词: " + ("；".join(tf) if tf else "（无）"))

# 4) 白名单残差：JSON 条件 = B2B 条件 + 且仅加白名单片段（白名单=候选行号指针/既有缩写/JSON 既有尾句）
WL = {0: ["候选 :4643 先于 :4648，", "跑前快照"],
      2: ["，不降级、不静默、不给 high"],
      3: ["：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支"]}
if after:
    wf = []
    for idx, wl in WL.items():
        jc, bc = json_rows[idx]["condition"], norm(b2b_rows[idx]["condition"])
        try:
            stripped = strip_deletes(jc, wl)
            if stripped != bc:
                wf.append(f"JSON:{idx+2} 白名单外残差:\n        json-白名单={stripped!r}\n        b2b          ={bc!r}")
        except AssertionError as e:
            wf.append(f"JSON:{idx+2} {e}")
    check("三处条件列：JSON = B2B + 白名单片段（白名单外零残差）", not wf, "\n        ".join(wf))

# 5) 全文级旧词清零（正式门禁在真实落盘后跑本模式）
if after:
    check("全文「跑后任意」清零（B2B_DESIGN.md + STATE_MATRIX.json）",
          "跑后任意" not in b2b_text and "跑后任意" not in sm_text,
          f"b2b={b2b_text.count('跑后任意')} json={sm_text.count('跑后任意')}")
else:
    print(f"[现状取证] 「跑后任意」计数: B2B_DESIGN.md={b2b_text.count('跑后任意')}（行"
          f"{[i+1 for i,l in enumerate(b2b_text.splitlines()) if '跑后任意' in l]}）, STATE_MATRIX.json={sm_text.count('跑后任意')}")

# 6) 行长对照（可读性）
print("\n----- 行长（字符数）-----")
for idx in (0, 2, 3):
    ln = 148 + idx
    old_line = b2b_text0.splitlines()[ln - 1]
    new_line = b2b_text.splitlines()[ln - 1]
    print(f":{ln}  改前 {len(old_line)} → 改后 {len(new_line)}  (Δ{len(new_line)-len(old_line):+d})")

# 7) condition 逐行并列（人工核对用）
print("\n----- condition 逐行并列（人工核对表）-----")
for idx, (b, j) in enumerate(zip(b2b_rows, json_rows)):
    mark = " ◀ 改" if idx in (0, 2, 3) else ""
    print(f":{b['line']}↔JSON:{idx+2} [{b['state']}/{b['preState']}]{mark}")
    print(f"   JSON: {j['condition']}")
    print(f"   B2B : {b['condition']}")

print(f"\n结论（{'--after 内存模拟' if after else '现状改前'}）: {sum(CHECKS)}/{len(CHECKS)} PASS")
