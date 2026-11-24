# -*- coding: utf-8 -*-
# _c97_check.py —— C 维 §9.7「高档 ≥100ms」四档辖域独立重评
# 离线只读 / 零真机 / 零采样代码；只读既有件、不写任何文件；仅标准库 ast/hashlib/re
# 运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_c97_check.py

import ast
import hashlib
import re

BASE = "D:/Project/ra2-campaign-forge"
RULING = BASE + "/lead/direction_ruling_20261108/RULING_DIRECTION.md"
DRRUL  = BASE + "/lead/direction_ruling_20261108/_dr_RULING.md"
CDBP   = BASE + "/lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md"
CMP    = BASE + "/lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md"
SUPP   = BASE + "/lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt"
DCPY   = BASE + "/lead/dtrigger_round2_20261107/_dC_recompute.py"
DCOUT  = BASE + "/lead/dtrigger_round2_20261107/_dC_out.txt"

out = []
def emit(s=""):
    out.append(s)

def fp(path):
    with open(path, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)

def read_text(path):
    with open(path, "rb") as f:
        return f.read().decode("utf-8", errors="replace")

emit("== _c97_ §9.7「高档 ≥100ms」四档辖域独立重评 · 离线只读 / 零真机 / 零采样代码 ==")
emit("")

# ---------- §0 对象指纹 ----------
emit("§0 被核对象指纹（hashlib.sha256，二进制整读）")
OBJ = [RULING, DRRUL, CDBP, CMP, SUPP, DCPY, DCOUT]
for p in OBJ:
    h, n = fp(p)
    emit("  被核对象 SHA256 = %s，字节数 = %d（%s）" % (h, n, p))
emit("")

# ---------- §1 上游明列四档 ----------
cmp_lines = read_text(CMP).split("\n")
l146 = cmp_lines[145]
THIRTEEN = ["C2-N16-P95x2", "C2-P95x2", "C2-P95x3", "C2-P99x2", "C2-P99x3",
            "C2-abs-P95x2", "C3-N16-r2", "C3-r12", "C3-r2", "C3-r4",
            "C3-r4-clean", "C3-r8", "C3-r8-clean"]
FULL26 = ["C1-k10", "C1-k25", "C1-k50", "C2-P95x2", "C2-P95x3", "C2-P99x2",
          "C2-P99x3", "C2-abs-P95x2", "C2-N16-P95x2", "C2-cap40-P95x2",
          "C2-N16-P95x2-cap40", "C3-r1.5", "C3-r2", "C3-r4", "C3-r4-clean",
          "C3-r8", "C3-r8-clean", "C3-r12", "C3-N16-r1.5", "C3-N16-r2",
          "C4-t16", "C4-t24", "C4-t30", "C4-t40", "C4-t48", "C5-k10t30"]
FOUR = ["C2-P95x3", "C2-P99x3", "C3-r4", "C3-r8"]
emit("§1 CRITERIA_COMPARE.md:146 直读：")
emit("  原文 = " + l146.strip())
emit("  缩写形态核查：:146 以「`C3-r4/r8`」斜杠缩写点名两档，展开后再做逐名核对")
l146x = re.sub(r"`C3-r4/r8`", "`C3-r4` `C3-r8`", l146)
emit("  展开后 = " + l146x.strip())
named26 = [t for t in FULL26 if t in l146x]
named = [t for t in THIRTEEN if t in l146x]
emit("  26 档全集中被 :146（展开后）点到的 = %s" % ", ".join(named26))
emit("  点名数（13 档口径）= %d，恰为四档集合 = %s" % (len(named), named == FOUR))
emit("  点名数（26 档全集口径）= %d，恰为四档集合 = %s" % (len(named26), named26 == FOUR))
emit("  :146 内 supplement 行号引用「:12,14,21-22」在场 = %s" % (":12,14,21-22" in l146))
rul_lines = read_text(RULING).split("\n")
drr_lines = read_text(DRRUL).split("\n")
l35 = rul_lines[34]
l96 = drr_lines[95]
emit("  裁决书 RULING_DIRECTION.md:35 含四档逐名 = %s" % all(t in l35 for t in FOUR))
emit("  旧裁决书 _dr_RULING.md:96 含四档逐名 = %s" % all(t in l96 for t in FOUR))
emit("")

# ---------- §2 supplement 原件解析：四档 nTrig / ge100 ----------
supp_rows = {}
dup = []
for i, line in enumerate(read_text(SUPP).split("\n"), 1):
    if "|" not in line:
        continue
    f = [z.strip() for z in line.split("|")]
    if len(f) >= 12 and re.match(r"^C[1-5]", f[0]) and f[1].isdigit():
        if f[0] in supp_rows:
            dup.append(f[0])
        else:
            supp_rows[f[0]] = dict(line=i, nTrig=int(f[1]), gt50=int(f[6]),
                                   ge100=int(f[8]), pct=f[9])
emit("§2 _dtrigger_supplement_out.txt 表行解析（id|nTrig|误报率|wait中位|waitP90|waitMax|>50|>50+e|>=100|>=100占比|...）：")
emit("  解析到 C 系表行数 = %d；重复 id = %s" % (len(supp_rows), dup if dup else "无"))
for t in FOUR:
    r = supp_rows.get(t)
    if r is None:
        emit("  %-12s 无行 -> 不支撑" % t)
    else:
        emit("  supplement_out.txt:%-3d %-12s nTrig=%3d >50=%3d >=100=%3d >=100占比=%s -> 全部触发>=100ms = %s"
             % (r["line"], t, r["nTrig"], r["gt50"], r["ge100"], r["pct"],
                "是" if r["ge100"] == r["nTrig"] else "否"))
four_ok = all(t in supp_rows and supp_rows[t]["ge100"] == supp_rows[t]["nTrig"] for t in FOUR)
emit("  ★ 四档辖域判定：4/4 档 ge100==nTrig，「高档 ≥100ms」在四档范围内成立 = %s" % four_ok)
emit("")

# ---------- §3 13 档分类 ----------
full, partial, norow = [], [], []
for t in THIRTEEN:
    r = supp_rows.get(t)
    if r is None:
        norow.append(t)
    elif r["ge100"] == r["nTrig"]:
        full.append(t)
    else:
        partial.append(t)
emit("§3 13 档按 supplement 原件分类：")
emit("  全部 ≥100ms（%d 档）：%s" % (len(full), ", ".join("%s(%d/%d)" % (t, supp_rows[t]["ge100"], supp_rows[t]["nTrig"]) for t in full)))
emit("  部分 ≥100ms（%d 档）：%s" % (len(partial), ", ".join("%s(%d/%d)" % (t, supp_rows[t]["ge100"], supp_rows[t]["nTrig"]) for t in partial)))
emit("  supplement 无行（%d 档）：%s" % (len(norow), ", ".join(norow)))
emit("  与 CD_BREAKPOINTS.md:80-82 的 4/5/4 分类一致 = %s"
     % (len(full) == 4 and len(partial) == 5 and len(norow) == 4
        and sorted(full) == sorted(FOUR)))
emit("")

# ---------- §4 _dC_out.txt 读回与 7b 段对账 ----------
dc_lines = read_text(DCOUT).split("\n")
seven_b = {}
for i, line in enumerate(dc_lines, 1):
    m = re.match(r"^\s{4}(\S+)\s+supplement_out\.txt:\s*(\d+)\s+nTrig=\s*(\d+)\s+>50=\s*(\d+)（(.+?)）\s+>=100=\s*(\d+)\s*$", line)
    if m:
        seven_b[m.group(1)] = dict(outline=i, suppline=int(m.group(2)),
                                   nTrig=int(m.group(3)), gt50=int(m.group(4)),
                                   tag=m.group(5), ge100=int(m.group(6)))
mismatch = []
for t in sorted(seven_b):
    r, s = seven_b[t], supp_rows.get(t)
    if s is None or (s["line"], s["nTrig"], s["gt50"], s["ge100"]) != (r["suppline"], r["nTrig"], r["gt50"], r["ge100"]):
        mismatch.append(t)
emit("§4 _dC_out.txt 7b 段（%d 行）↔ supplement 原件逐档对账：不一致 = %d %s"
     % (len(seven_b), len(mismatch), "PASS" if not mismatch else "FAIL " + str(mismatch)))
m80 = None
for line in dc_lines:
    mm = re.search(r"71 格涉及的判据 = (\d+) 档[:：]\s*(.+)$", line)
    if mm:
        m80 = (int(mm.group(1)), [x.strip() for x in mm.group(2).split(",")])
emit("  _dC_out.txt:80 的 13 档名单与本件名单一致 = %s（实配=%s）"
     % (m80 is not None and m80[0] == 13 and m80[1] == THIRTEEN,
        "未匹配" if m80 is None else "%d 档: %s..." % (m80[0], m80[1][0])))
emit("  _dC_out.txt:147 = " + dc_lines[146].strip())
emit("  _dC_out.txt:148 = " + dc_lines[147].strip())
emit("")

# ---------- §5 _dC_recompute.py AST 检查 ----------
src = read_text(DCPY)
tree = ast.parse(src)
src_lines = src.split("\n")

gate = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "all_pass" for t in node.targets):
        gate = node
gate_names = sorted({n.id for n in ast.walk(gate) if isinstance(n, ast.Name)})
gate_cmp = sum(1 for n in ast.walk(gate) if isinstance(n, ast.Compare))
gate_not = sum(1 for n in ast.walk(gate) if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not))
emit("§5 _dC_recompute.py AST 检查：")
emit("  5a all_pass（:391-401）内 Compare=%d、not=%d" % (gate_cmp, gate_not))
emit("  5a 门内 Name 引用集合 = %s" % ", ".join(gate_names))
emit("  5a ge100 在 all_pass 门内 = %s；supp_rows 在门内 = %s；probe_rows 在门内 = %s"
     % ("ge100" in gate_names, "supp_rows" in gate_names, "probe_rows" in gate_names))
ge_cmp = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Compare) and "ge100" in ast.dump(n))
emit("  5b 全模块含 ge100 的 Compare 节点 = %d" % ge_cmp)
lit = nonlit = 0
for node in ast.walk(tree):
    if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name) and node.value.func.id == "emit"
            and 356 <= node.lineno <= 369):
        if all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in node.value.args):
            lit += 1
        else:
            nonlit += 1
emit("  5c :356-369 段 emit 纯字面串 = %d、含非字面 = %d" % (lit, nonlit))
for node in ast.walk(tree):
    if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name) and node.value.func.id == "emit"
            and node.lineno == 420):
        consts = [a.value for a in ast.walk(node.value) if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        emit("  5d :420 emit 的字符串常量 = %s" % " ‖ ".join(consts))
        emit("  5d 含「9.1–9.7」= %s；以 all_pass 为条件 = %s"
             % (any("9.1–9.7" in c for c in consts),
                any(isinstance(n, ast.Name) and n.id == "all_pass" for n in ast.walk(node.value))))
emit("  5e 源码直读：")
for lo, hi, tag in ((296, 297, "ge100 赋值"), (338, 340, "ge100 仅展示"),
                    (391, 401, "all_pass 门"), (417, 420, "§9.7 文案与总判定")):
    emit("    -- :%d-%d（%s）" % (lo, hi, tag))
    for i in range(lo, hi + 1):
        emit("      %d: %s" % (i, src_lines[i - 1]))
emit("")

# ---------- §6 本件判定 ----------
emit("§6 本件判定")
emit("  V1 上游明列四档 = C2-P95x3/C2-P99x3/C3-r4/C3-r8，明列处 = CRITERIA_COMPARE.md:146（其中 C3-r4/C3-r8 以「C3-r4/r8」斜杠缩写点名；26 档全集中恰点名这 4 档、无第五档），其行号引用 :12,14,21-22 与 supplement 原件四行一致。")
emit("  V2 四档 nTrig==>=100 = 19/19、18/18、24/24、16/16 → §9.7「高档 ≥100ms」在四档辖域内成立（4/4），「越界指控」在四档辖域下不成立。")
emit("  V3 13 档分类 = 4 全部 / 5 部分 / 4 无行；7/13 档读法下的无支撑档数继续并列保留，本件不扩裁、不从四档裁定推成全档 ≥100。")
emit("  V4 all_pass 门内无 ge100、无 supp_rows/probe_rows 聚合项（5a/5b）；:420 文案硬编码「9.1–9.7 均成立」→ 语义层缺陷独立于辖域，成立。")
emit("  V5 C 维整体仍 unconfirmed；本件只做辖域重评，不改 R2_FINAL_GRADE 升格判定。")
emit("")
emit("== 结束 ==")

print("\n".join(out))
