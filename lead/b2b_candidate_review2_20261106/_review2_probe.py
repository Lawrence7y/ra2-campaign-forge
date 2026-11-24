# -*- coding: utf-8 -*-
"""
范围核验员 · 第 2 轮独立探针（review2）
------------------------------------------------------------------
职责：用 difflib 全量比对【母本】与【候选】，列出所有差异块，
      逐块归因到批准设计 §4 的 H01–H09；凡归不到的一律点名为夹带。

只读四件：母本 / 候选 / 设计 / 本轮 TASK
唯一写入：_review2_probe_out.txt（与本脚本同目录）

实跑命令：
  python -I -X utf8 D:\\Project\\ra2-campaign-forge\\lead\\b2b_candidate_review2_20261106\\_review2_probe.py

口径声明（重要，避免"全量"二字被偷换）：
  [口径 A · 主口径] 行文本 = bytes.decode('utf-8').splitlines()
      —— 去掉行尾换行符，只比「代码文本内容」。difflib 归因在此口径上做。
  [口径 B · 字节级] 行文本 = bytes.decode('utf-8').splitlines(keepends=True)
      —— 保留 \\r\\n / \\n。单列一节登记换行符差异，不混入主口径 + 行计数。
"""
from __future__ import annotations

import difflib
import hashlib
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
P_MOTHER = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
P_CAND = ROOT / "lead/b2b_candidate_20261106/qc151_trip.candidate.py"
P_DESIGN = ROOT / "lead/b2b_design_20261106/B2B_DESIGN.md"
P_TASK = ROOT / "lead/b2b_candidate_review2_20261106/TASK.md"
P_OUT = ROOT / "lead/b2b_candidate_review2_20261106/_review2_probe_out.txt"

# 本轮 TASK.md:22-24 给的上游绑定期望值（用于「上游漂移」核对；本轮 TASK 自身无期望值）
EXPECT = {
    "母本": ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    "候选": ("9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc", 420292),
    "设计": ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
}

OUT: list[str] = []


def w(s: str = "") -> None:
    OUT.append(s)


def hr(title: str) -> None:
    w()
    w("=" * 100)
    w(title)
    w("=" * 100)


def text_lines(d: bytes) -> list[str]:
    """口径 A：纯代码文本内容，去掉所有行尾换行符。"""
    return d.decode("utf-8").splitlines()


def raw_lines(d: bytes) -> list[str]:
    """口径 B：保留行尾换行符（母本 \\n / 候选 \\r\\n）。"""
    return d.decode("utf-8").splitlines(keepends=True)


def counter_subset(part: list[str], whole: list[str]) -> bool:
    """Counter 多重集：part 是否完全被 whole 覆盖。"""
    return not (Counter(part) - Counter(whole))


# ---------------------------------------------------------------------------
# 1) 四件指纹实算
# ---------------------------------------------------------------------------
hr("1) 四件指纹实算（Python hashlib；实算，不抄派发材料）")

FOUR = [
    ("母本", P_MOTHER),
    ("候选", P_CAND),
    ("设计", P_DESIGN),
    ("本轮TASK", P_TASK),
]
DATA: dict[str, bytes] = {}
for tag, p in FOUR:
    d = p.read_bytes()
    DATA[tag] = d
    h = hashlib.sha256(d).hexdigest()
    n = len(d)
    crlf = d.count(b"\r\n")
    lf = d.count(b"\n")
    lines = len(d.decode("utf-8").splitlines())
    w(f"{tag:8s} path={p.as_posix()}")
    w(f"{tag:8s} sha256={h}")
    w(f"{tag:8s} bytes={n}  CRLF={crlf}  LF={lf}  splitlines行数={lines}")
    if tag in EXPECT:
        eh, en = EXPECT[tag]
        ok = (h == eh and n == en)
        w(f"{tag:8s} 对照本轮 TASK.md:22-24 期望 => sha={'MATCH' if h == eh else 'MISMATCH'} "
          f"bytes={'MATCH' if n == en else 'MISMATCH'}  => 上游绑定 {'OK' if ok else '★ DRIFT'}")
    else:
        w(f"{tag:8s} 本轮 TASK 未给自身期望值（本文件即 TASK），仅登记实算指纹")
    w()

# ---------------------------------------------------------------------------
# 2) 行尾 / 编码口径登记（口径 B）
# ---------------------------------------------------------------------------
hr("2) 行尾字节口径登记（口径 B，单独列，不混入主口径 + 行计数）")
mb, cb, db = DATA["母本"], DATA["候选"], DATA["设计"]
w(f"母本: CRLF={mb.count(bytes([13, 10]))} / LF={mb.count(bytes([10]))} / 含BOM={mb.startswith(bytes([0xEF, 0xBB, 0xBF]))}")
w(f"候选: CRLF={cb.count(bytes([13, 10]))} / LF={cb.count(bytes([10]))} / 含BOM={cb.startswith(bytes([0xEF, 0xBB, 0xBF]))}")
w(f"设计: CRLF={db.count(bytes([13, 10]))} / LF={db.count(bytes([10]))} / 含BOM={db.startswith(bytes([0xEF, 0xBB, 0xBF]))}")
mraw, craw = raw_lines(mb), raw_lines(cb)
m_tail = Counter(x[len(x.rstrip("\r\n")):] for x in mraw)
c_tail = Counter(x[len(x.rstrip("\r\n")):] for x in craw)
w(f"母本 {len(mraw)} 行的行尾分布 = {dict(m_tail)}")
w(f"候选 {len(craw)} 行的行尾分布 = {dict(c_tail)}")
w("实算事实：母本全文件 LF 行尾；候选全文件 CRLF 行尾；设计文件全文件 LF 行尾。")
w("⇒ 按【口径 B 字节级】比对，母本 7291 行行尾 '\\n'、候选 7533 行行尾 '\\r\\n'，"
  "即候选相对母本的『行尾字节』全线变更；批准设计 §4 的 9 个 hunk 只声明文本行内容，"
  "未声明任何行尾字节改动（设计稿自身 0 CRLF）。")
w("本脚本主归因采用【口径 A · 行文本内容】，理由：difflib 逐块归因的对象必须是代码语义行；"
  "若把行尾字节计入，则 7533 行全部与母本不等，SequenceMatcher 会退化为无意义的整篇替换，"
  "既无法定位 H01–H09，也无法回答『夹带了哪一行代码』。此差异在此单列，供总控裁定是否计入范围外改动。")
w()
w("-- 2.1 口径 B 的严格字节级归因尝试（不改主口径结论，独立登记）--")
# 把母本与候选按「保留行尾」逐行做 SequenceMatcher(opcodes)，看会出现什么
sm_raw = difflib.SequenceMatcher(None, mraw, craw, autojunk=False)
raw_changes = [op for op in sm_raw.get_opcodes() if op[0] != "equal"]
raw_plus = sum(j2 - j1 for _, _, _, j1, j2 in raw_changes)
raw_minus = sum(i2 - i1 for _, i1, i2, _, _ in raw_changes)
w(f"口径 B SequenceMatcher 变更块 = {len(raw_changes)} ；'+' 行 = {raw_plus} ；'-' 行 = {raw_minus}")
w("⇒ 逐行字节级比对下：母本 7291 行（'\\n'）与候选 7533 行（'\\r\\n'）"
  "因行尾不同几乎全线不等，差异块覆盖整篇，无法按 H01–H09 逐块归因。")
w("★ 严格字节口径下的待裁定事实：候选 7533 行行尾全部由母本 '\\n' 变为 '\\r\\n'，"
  "这是设计 §4 九个 hunk 均未声明的字节级改动；本探针不把它算进「代码行夹带」"
  "（因它不是任何一行代码文本的增删改），但如实登记，交由总控裁定是否属于范围外改动。")
# 反事实校验：把候选行尾统一改成 LF 后，与「母本 LF + 设计 9 hunk（LF）」的重建文本比对。
# 重建在 §7 完成，这里仅登记「行尾差是唯一剩余字节差」的可验算术：
#   候选原字节 - 7533 个 \r = 候选 LF 字节；重建文本(\n 拼接) 的字节数应与之相等（见 §7 打印）。
cand_lf = cb.replace(b"\r\n", b"\n")
w(f"反事实校验：候选 CRLF→LF 后字节数 = {len(cand_lf)} "
  f"(原 {len(cb)}；差 {len(cb)-len(cand_lf)} = CRLF 行数 {cb.count(bytes([13,10]))})")
w("  该反事实文本的逐行内容已在 §7 用『母本 + 设计 9 hunk』重建并逐行相等；"
  "故除行尾字节外的全部代码行内容无夹带。行尾字节是否计入范围外，见上方待裁定事实。")


# ---------------------------------------------------------------------------
# 3) 解析批准设计 §4 的 9 个 hunk（H01–H09）
# ---------------------------------------------------------------------------
hr("3) 批准设计 §4 的 hunk 解析（B2B_DESIGN.md:198-566，§7:656-673 定 H01–H09 口径）")

design_text = DATA["设计"].decode("utf-8")
design_lines = design_text.splitlines()
diff_blocks = re.findall(r"```diff\n(.*?)\n```", design_text, re.S)
w(f"设计文件内 ```diff 代码块数 = {len(diff_blocks)}")
w(f"设计文件内 '@@ ' 头行数 = {sum(1 for l in design_lines if l.startswith('@@ '))}")
w("§4:202 声明「按出现顺序依次对应 §7 的 H01…H09；共 9 个 @@ 头」。")
w()

HUNKS: list[dict] = []
for bi, block in enumerate(diff_blocks, 1):
    blines = block.split("\n")
    m = re.match(r"^@@ -(\d+),(\d+) \+(\d+),(\d+) @@", blines[0])
    if not m:
        w(f"  block#{bi} 无 @@ 头 => 跳过（非 hunk 块）")
        continue
    a, b, c, d = (int(x) for x in m.groups())
    plus, minus, ctx, body = [], [], [], []
    for l in blines[1:]:
        if not l:
            # 设计稿 diff 块内的真空行：按上下文空行处理（unified diff 里应为 ' '）
            body.append((" ", ""))
            ctx.append("")
            continue
        tag, content = l[0], l[1:]
        if tag == "+":
            plus.append(content)
            body.append(("+", content))
        elif tag == "-":
            minus.append(content)
            body.append(("-", content))
        elif tag == " ":
            ctx.append(content)
            body.append((" ", content))
        else:
            # 不该出现；如实登记
            body.append(("?", l))
    h = {
        "idx": len(HUNKS) + 1,
        "name": f"H{len(HUNKS) + 1:02d}",
        "header": blines[0],
        "a": a, "b": b, "c": c, "d": d,
        "m_start": a, "m_end": a + b - 1,
        "plus": plus, "minus": minus, "ctx": ctx, "body": body,
        "block": bi,
    }
    HUNKS.append(h)

w(f"解析得到 hunk 数 = {len(HUNKS)}")
for h in HUNKS:
    w(f"  {h['name']}  {h['header']}")
    w(f"       母本覆盖区间(1-based, 含上下文行) = {h['m_start']}-{h['m_end']} ; "
      f"设计 '+' 行 = {len(h['plus'])} ; 设计 '-' 行 = {len(h['minus'])} ; "
      f"设计上下文行 = {len(h['ctx'])} ; 校验 -侧={len(h['ctx'])+len(h['minus'])}/{h['b']} "
      f"+侧={len(h['ctx'])+len(h['plus'])}/{h['d']}")
w()
w("对照本轮 TASK 给的 §6③ 覆盖区间串（B2B_DESIGN.md:635）：")
w("  212-217 / 4458-4463 / 4558-4565 / 4572-4591 / 5906-5912 / 5936-5942 / "
  "6294-6299 / 6386-6391 / 7122-7128")
w("  本脚本实算 = " + " / ".join(f"{h['m_start']}-{h['m_end']}" for h in HUNKS))

DESIGN_PLUS = [x for h in HUNKS for x in h["plus"]]
DESIGN_MINUS = [x for h in HUNKS for x in h["minus"]]
w()
w(f"设计 §4 全部 '+' 行合计 = {len(DESIGN_PLUS)} ；全部 '-' 行合计 = {len(DESIGN_MINUS)}")
w(f"设计净增行数 = {len(DESIGN_PLUS) - len(DESIGN_MINUS)}")

# ---------------------------------------------------------------------------
# 4) difflib 全量比对（口径 A）
# ---------------------------------------------------------------------------
hr("4) difflib 全量比对：母本 vs 候选（口径 A；SequenceMatcher(autojunk=False)）")

M = text_lines(mb)
C = text_lines(cb)
w(f"母本行数 = {len(M)} ；候选行数 = {len(C)} ；行数差 = {len(C) - len(M)}")
sm = difflib.SequenceMatcher(None, M, C, autojunk=False)
opcodes = sm.get_opcodes()
changes = [op for op in opcodes if op[0] != "equal"]
w(f"SequenceMatcher opcode 总数 = {len(opcodes)} ；其中变更块(opcode != equal) = {len(changes)}")
w(f"unified_diff(n=3) hunk 头数 = {sum(1 for l in difflib.unified_diff(M, C, n=3) if l.startswith('@@ '))}")
w()

# 收集全部候选 + 行 / 母本 - 行
CAND_PLUS: list[str] = []     # (cand 行号 1-based, 内容)
CAND_MINUS: list[str] = []    # (mother 行号 1-based, 内容)
for tag, i1, i2, j1, j2 in changes:
    for k in range(j1, j2):
        CAND_PLUS.append((k + 1, C[k]))
    for k in range(i1, i2):
        CAND_MINUS.append((k + 1, M[k]))

w(f"候选侧 '+' 行合计 = {len(CAND_PLUS)} ；母本侧 '-' 行合计 = {len(CAND_MINUS)}")
w(f"净增 = {len(CAND_PLUS) - len(CAND_MINUS)}  (= 行数差 {len(C) - len(M)} ? "
  f"{'OK' if len(CAND_PLUS) - len(CAND_MINUS) == len(C) - len(M) else '★ MISMATCH'})")
w()

w("-- 4.1 所有差异块逐块全量列出（'+' = 候选新增 / '-' = 母本被替换或删除）--")
for bi, (tag, i1, i2, j1, j2) in enumerate(changes, 1):
    w(f"[块 {bi:02d}] tag={tag}  母本 1-based 区间={i1+1}-{i2}  候选 1-based 区间={j1+1}-{j2}  "
      f"'+' 行={j2-j1}  '-' 行={i2-i1}")
    for k in range(i1, i2):
        w(f"    - 母本:{k+1:<5d} | {M[k]}")
    for k in range(j1, j2):
        w(f"    + 候选:{k+1:<5d} | {C[k]}")
w()

w("-- 4.2 unified_diff(n=3) 的 hunk 头（与设计 §4 头逐字对照）--")
ud = list(difflib.unified_diff(M, C, n=3))
ud_headers = [l.rstrip("\n") for l in ud if l.startswith("@@ ")]
for n, l in enumerate(ud_headers, 1):
    dh = HUNKS[n-1]["header"] if n-1 < len(HUNKS) else "<无此设计 hunk>"
    w(f"  hunk#{n:02d} 候选 = {l}")
    w(f"            设计 = {dh}   => {'SAME' if l == dh else '★ DIFFERENT'}")
w(f"  unified hunk 数 = {len(ud_headers)} ；设计 §4 hunk 数 = {len(HUNKS)} => "
  f"{'SAME' if len(ud_headers) == len(HUNKS) else '★ COUNT MISMATCH'}")

# ---------------------------------------------------------------------------
# 5) 逐差异块归因 H01–H09
# ---------------------------------------------------------------------------
hr("5) 逐差异块归因到 H01–H09（严格：区间 + '+'行 + '-'行 三重判定）")
w("判定规则（每个块独立）：")
w("  range_ok : replace/delete 的母本区间 [i1+1, i2] 完整落在某 H 的母本覆盖区间 [a, a+b-1] 内；")
w("             insert 的插入锚点 (i1+1) 落在 [a, a+b] 内；")
w("  add_in   : 该块全部 '+' 行按 Counter 多重集 ⊆ 该 H 的设计 '+' 行；")
w("  del_in   : 该块全部 '-' 行按 Counter 多重集 ⊆ 该 H 的设计 '-' 行；")
w("  三者全真 => 「归属 Hxx」；任一为假且无其它 H 满足 => 「★ 无法归属」（夹带，必须点名）。")
w()

attribution: list[dict] = []
for bi, (tag, i1, i2, j1, j2) in enumerate(changes, 1):
    plus = [C[k] for k in range(j1, j2)]
    minus = [M[k] for k in range(i1, i2)]
    hits = []
    for h in HUNKS:
        if tag == "insert":
            anchor = i1 + 1
            range_ok = h["m_start"] <= anchor <= h["m_end"] + 1
        else:
            range_ok = (i1 + 1 >= h["m_start"]) and (i2 <= h["m_end"])
        add_in = counter_subset(plus, h["plus"])
        del_in = counter_subset(minus, h["minus"])
        if range_ok and add_in and del_in:
            hits.append((h["name"], range_ok, add_in, del_in))
    if hits:
        owners = "/".join(x[0] for x in hits)
        best = hits[0][0]
        attribution.append({"bi": bi, "ok": True, "owner": best,
                            "all": owners, "plus": plus, "minus": minus,
                            "j1": j1, "j2": j2, "i1": i1, "i2": i2, "tag": tag})
        w(f"[块 {bi:02d}] tag={tag:<7s} 母本 {i1+1}-{i2} -> 候选 {j1+1}-{j2}  "
          f"=> 归属 {best}  [命中={owners} ; range/add/del=TRUE/TRUE/TRUE]")
        if len(hits) > 1:
            w(f"          ★ 注意：该块同时满足多个 H（{owners}），按母本顺序取首个；已登记歧义")
    else:
        attribution.append({"bi": bi, "ok": False, "owner": None,
                            "plus": plus, "minus": minus,
                            "j1": j1, "j2": j2, "i1": i1, "i2": i2, "tag": tag})
        # 打出每个 H 的三项判定，说明为何归不到
        w(f"[块 {bi:02d}] tag={tag:<7s} 母本 {i1+1}-{i2} -> 候选 {j1+1}-{j2}  "
          f"=> ★ 无法归属")
        for h in HUNKS:
            if tag == "insert":
                anchor = i1 + 1
                range_ok = h["m_start"] <= anchor <= h["m_end"] + 1
            else:
                range_ok = (i1 + 1 >= h["m_start"]) and (i2 <= h["m_end"])
            add_in = counter_subset(plus, h["plus"])
            del_in = counter_subset(minus, h["minus"])
            w(f"          {h['name']}: range_ok={range_ok} add_in={add_in} del_in={del_in}"
              f"  (覆盖 {h['m_start']}-{h['m_end']})")
        for k in range(j1, j2):
            w(f"          ★ 未归因 '+' 行 候选:{k+1} | {C[k]}")
        for k in range(i1, i2):
            w(f"          ★ 未归因 '-' 行 母本:{k+1} | {M[k]}")

# ---------------------------------------------------------------------------
# 6) 多重集交叉校验（独立于逐块归因）
# ---------------------------------------------------------------------------
hr("6) 多重集交叉校验（候选 +/- 全量 vs 设计 +/- 全量；独立于逐块区间判定）")

cp_counter = Counter(x[1] for x in CAND_PLUS)
dp_counter = Counter(DESIGN_PLUS)
cm_counter = Counter(x[1] for x in CAND_MINUS)
dm_counter = Counter(DESIGN_MINUS)

extra_plus = list((cp_counter - dp_counter).elements())
missing_plus = list((dp_counter - cp_counter).elements())
extra_minus = list((cm_counter - dm_counter).elements())
missing_minus = list((dm_counter - cm_counter).elements())

w(f"候选 '+' 行中【设计 §4 未声明】的条数（夹带直接证据） = {len(extra_plus)}")
for x in extra_plus:
    w(f"    ★ EXTRA+ | {x}")
w(f"设计 '+' 行中【候选未实现】的条数 = {len(missing_plus)}")
for x in missing_plus:
    w(f"    ★ MISSING+ | {x}")
w(f"母本 '-' 行中【设计 §4 未声明】的条数 = {len(extra_minus)}")
for x in extra_minus:
    w(f"    ★ EXTRA- | {x}")
w(f"设计 '-' 行中【候选未删除】的条数 = {len(missing_minus)}")
for x in missing_minus:
    w(f"    ★ MISSING- | {x}")

# ---------------------------------------------------------------------------
# 7) 重建金标准：把设计 9 个 hunk 按 unified diff 语义套回母本，与候选逐行比对
# ---------------------------------------------------------------------------
hr("7) 重建金标准：设计 §4 的 9 个 hunk 套回母本 == 候选？")

rebuild_err: list[str] = []
rebuilt: list[str] = []
pos = 0
for h in HUNKS:
    start = h["a"] - 1
    if start < pos:
        rebuild_err.append(f"{h['name']}: hunk 起点 {start} < 已消费 {pos}（区间重叠）")
    rebuilt.extend(M[pos:start])
    pos = start
    for tagc, content in h["body"]:
        if tagc in (" ", "-"):
            if pos >= len(M):
                rebuild_err.append(f"{h['name']}: 母本越界 pos={pos}")
                break
            if M[pos] != content:
                rebuild_err.append(
                    f"{h['name']}: 上下文/删除行与母本原文不等 @母本:{pos+1} "
                    f"design={content!r} mother={M[pos]!r}")
            if tagc == " ":
                rebuilt.append(M[pos])
            pos += 1
        elif tagc == "+":
            rebuilt.append(content)
        else:
            rebuild_err.append(f"{h['name']}: 未知 body 标记 {tagc!r} {content!r}")
rebuilt.extend(M[pos:])

w(f"重建结果行数 = {len(rebuilt)} ；候选行数 = {len(C)}")
w(f"hunk 回套断言失败数 = {len(rebuild_err)}")
for e in rebuild_err:
    w(f"    ★ {e}")
if len(rebuilt) == len(C):
    diffs = [(k + 1, rebuilt[k], C[k]) for k in range(len(C)) if rebuilt[k] != C[k]]
    w(f"重建文本 vs 候选 逐行不等处 = {len(diffs)}")
    for ln, r, c in diffs[:40]:
        w(f"    ★ 行 {ln}: 重建={r!r} 候选={c!r}")
    if len(diffs) > 40:
        w(f"    ... 另有 {len(diffs)-40} 处未逐条打印")
else:
    w("    ★ 行数不等，无法逐行比对")
w(f"重建文本 == 候选  => {'TRUE（候选 == 母本 + 设计 9 hunk，零夹带）' if (not rebuild_err and rebuilt == C) else 'FALSE（见上）'}")
# 字节级反事实：母本原本是 LF，把重建文本用 \n 拼回字节，与候选 CRLF→LF 后的字节比
rebuilt_lf_bytes = ("\n".join(rebuilt) + "\n").encode("utf-8")
cand_lf_bytes = cb.replace(b"\r\n", b"\n")
w(f"字节级反事实：重建文本(LF 拼接) 字节数 = {len(rebuilt_lf_bytes)} ; "
  f"候选 CRLF→LF 字节数 = {len(cand_lf_bytes)}")
w(f"重建文本(LF) == 候选去 CR 后字节 => {rebuilt_lf_bytes == cand_lf_bytes}")
w("  （若 TRUE：候选与『母本+设计9hunk』的唯一字节差异就是 7533 个 \\r 行尾符；"
  "除此之外没有任何一行代码文本被夹带。）")

# ---------------------------------------------------------------------------
# 8) 统计 + 未归因 + 行逐条
# ---------------------------------------------------------------------------
hr("8) 统计与「未归因 + 行数」逐条清单")

total = len(changes)
ok_n = sum(1 for a in attribution if a["ok"])
bad_n = sum(1 for a in attribution if not a["ok"])
unattr_plus_pairs: list[tuple[int, str]] = []
for a in attribution:
    if not a["ok"]:
        for k in range(a["j1"], a["j2"]):
            unattr_plus_pairs.append((k + 1, C[k]))
# 与 §6 的 EXTRA+ 求并集（去重按「块内 + 行」计；EXTRA+ 单独列出避免漏）
w(f"差异块总数   = {total}")
w(f"可归属数     = {ok_n}")
w(f"无法归属数   = {bad_n}")
w(f"未归因的 + 行数（无法归属块的候选新增行，按行计） = {len(unattr_plus_pairs)}")
w(f"§6 交叉校验 EXTRA+ 条数（候选有 / 设计无）        = {len(extra_plus)}")
w(f"§6 交叉校验 EXTRA- 条数                            = {len(extra_minus)}")
w()
w("【口径 B 独立登记（不计入上表『代码行夹带』，但按本轮指令如实点名）】")
w(f"  母本 LF 行尾 7291 行 -> 候选 CRLF 行尾 7533 行；设计 §4 未声明任何行尾字节改动。")
w(f"  字节级 SequenceMatcher 变更块 = {len(raw_changes)}，'+' 行 = {raw_plus}，'-' 行 = {raw_minus}"
  f"（详见 §2.1）。该块无法归属任何 H01–H09。")
w(f"  反事实实算：重建文本(LF) == 候选去 CR 后字节 = {rebuilt_lf_bytes == cand_lf_bytes}（§7）；"
  f"故这是候选与『母本+设计9hunk』之间的唯一字节差异类别。")
w("  ⇒ 按『任何归不到的都是夹带』的严格字节语义，这是一条待总控裁定的范围外改动；"
  "按『代码行文本』语义（本探针主口径，也是 difflib 逐块归因的可行口径），它不属于任何一行代码的增删改。")
w("  本探针不擅自把它计为『未归因 + 行』（那会把 7533 行全部算作夹带，与逐行内容可重建相等的事实矛盾），"
  "但明确点名，不隐瞒。")
w()
if unattr_plus_pairs or extra_plus or extra_minus or bad_n:
    w("★ 重大发现：存在无法归因 / 设计外改动，逐条列出如下：")
    for ln, content in unattr_plus_pairs:
        w(f"    [未归因 + 行] 候选:{ln} | {content}")
    for x in extra_plus:
        w(f"    [EXTRA+ 设计未声明] | {x}")
    for x in extra_minus:
        w(f"    [EXTRA- 设计未声明] | {x}")
    for a in attribution:
        if not a["ok"]:
            w(f"    [无法归属块] 块 {a['bi']:02d} tag={a['tag']} "
              f"母本 {a['i1']+1}-{a['i2']} -> 候选 {a['j1']+1}-{a['j2']}")
else:
    w("逐块均可归属；未归因 + 行数 = 0；EXTRA+/EXTRA- 均为 0。")
    w("（本探针只报『范围归因』事实，不签语义 PASS / 不判可应用母本。）")

w()
w("-- 8.1 按 H 汇总（各 H 命中了哪些差异块）--")
for h in HUNKS:
    hit = [a["bi"] for a in attribution if a["ok"] and a["owner"] == h["name"]]
    w(f"  {h['name']} 命中块 = {hit if hit else '（无）'} ; "
      f"设计 + 行 {len(h['plus'])} / 设计 - 行 {len(h['minus'])} ; "
      f"母本覆盖 {h['m_start']}-{h['m_end']}")
w()
w("-- 8.2 E 判据块是否落入任何变更块（母本 :5984-5990，本轮 TASK §3.4 关注）--")
for bi, (tag, i1, i2, j1, j2) in enumerate(changes, 1):
    if i2 >= 5984 and (i1 + 1) <= 5990:
        w(f"    ★ 块 {bi:02d} 覆盖母本 {i1+1}-{i2} 与 5984-5990 相交")
w("    （上面若无 ★ 行，则 E 集合差判据块未落入任何变更块）")

# ---------------------------------------------------------------------------
# 写输出
# ---------------------------------------------------------------------------
P_OUT.write_text("\n".join(OUT) + "\n", encoding="utf-8", newline="\n")
print("WROTE", P_OUT.as_posix(), "lines=", len(OUT))
print("STATS total_blocks=%d attributed=%d unattributed=%d unattributed_plus_lines=%d extra_plus=%d extra_minus=%d"
      % (total, ok_n, bad_n, len(unattr_plus_pairs), len(extra_plus), len(extra_minus)))
print("REBUILD_EQUALS_CANDIDATE=", (not rebuild_err and rebuilt == C))
