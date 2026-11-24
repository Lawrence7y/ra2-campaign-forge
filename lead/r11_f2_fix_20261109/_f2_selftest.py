# -*- coding: utf-8 -*-
"""_f2_selftest.py — 第四步：证明增强版不引入新误报。

S1 剥行号后缀单元测试（含 Windows 盘符冒号 C:\\ 反例）。
S2 F2-b 正例：真实在盘文件 + `:行-行` 后缀 —— 原版误报 R3-3c（假阳性），
   增强版剥后缀后回验 MATCH（修原版误报，非放松）。
S3 引文语境反例检验（要求 c）：真违规必须仍 FAIL，仅显式标记降级。
S4 any-match-wins 反误伤检验：多候选（一个失配一个匹配）→ 验证成立不加 problem。
S5 原版行为保留：raw 可解析路径两者同为 MATCH；raw 不可解析时增强版 R3-3c
   消息原文与原版逐字一致；缺绑定行消息逐字一致。
S6 30 件无新误报清点：逐件 plus problems 与 orig problems 对比。
"""
import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
G7 = REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
F2PLUS = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_r11plus.py"

def sha_of(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

raw = G7.read_bytes()
assert hashlib.sha256(raw).hexdigest() == "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
spec = importlib.util.spec_from_file_location("_g7_predicates_st", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)
spec2 = importlib.util.spec_from_file_location("_f2_r11plus_st", F2PLUS)
f2p = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(f2p)

checks = []
def check(cid, ok, detail):
    checks.append({"id": cid, "ok": bool(ok), "detail": detail})
    print("%s  %s  %s" % ("PASS" if ok else "FAIL", cid, detail))

# ============ S1 剥行号后缀单元测试 ============
S = f2p.strip_line_suffixes
cases = [
    ("C:\\", ["C:\\"]),                                   # 盘符冒号：后无数字，不剥
    ("C:\\x", ["C:\\x"]),                                 # 盘符冒号后是目录名，不剥
    ("C:\\Users\\a\\f.md:18-19", ["C:\\Users\\a\\f.md"]), # 盘符路径 + 行号范围：剥行号、保盘符
    ("f.md:L18-L19", ["f.md"]),                           # :L18-L19 形态
    ("f.md#L18", ["f.md"]),                               # #L18 形态
    ("f.md:18", ["f.md"]),                                # :18 形态
    ("_x.txt:962/:963/:965", ["_x.txt"]),                 # 多段行号循环剥
    ("R2_FINAL_GRADE.md:68", ["R2_FINAL_GRADE.md"]),
    ("plain.md", ["plain.md"]),                           # 无后缀不剥
    ("lead/x/R2_FINAL_GRADE.md:58", ["lead/x/R2_FINAL_GRADE.md"]),
]
for inp, expect_tail in cases:
    got = S(inp)
    ok = got[0] == inp and got[-1] == expect_tail[-1]
    check("S1_strip[%s]" % inp, ok, "variants=%r" % (got,))

# ============ S2 F2-b 正例：原版假阳性被修 ============
plus_sha, plus_bytes = sha_of(F2PLUS)
rel = "lead/r11_f2_fix_20261109/_f2_r11plus.py"
t_suf = "被核对象 `%s:10-20` SHA256 = %s，字节数 = %d" % (rel, plus_sha, plus_bytes)
o_p, o_w, o_b = g7.r11_scan(t_suf, REPO / "lead", root=REPO)
n_p, n_w, n_b = f2p.r11_scan_plus(t_suf, REPO / "lead", root=REPO)
check("S2_F2b_原版误报R3-3c", len(o_p) == 1 and "R3-3c" in o_p[0],
      "orig problems=%r" % (o_p,))
check("S2_F2b_增强版回验MATCH",
      not n_p and n_b[0]["match"] is True and n_b[0].get("suffix_stripped") is True
      and n_b[0].get("tier") == "T1",
      "plus problems=%r match=%r stripped=%r" % (n_p, n_b[0].get("match"), n_b[0].get("suffix_stripped")))

# ============ S3 引文语境反例检验 ============
wrong_sha, wrong_bytes = sha_of(REPO / "lead" / "r11_f2_fix_20261109" / "_f2_repro.py")
def run(text):
    return f2p.r11_scan_plus(text, REPO / "lead", root=REPO)

anchor = "lead/r11_f2_fix_20261109/_f2_r11plus.py"
# (a) 真违规、无标记 → problem（增强版不得降级）
t = "被核对象 SHA256 = %s，字节数 = %d（见 `%s`）" % (wrong_sha, wrong_bytes, anchor)
n_p, n_w, _ = run(t)
check("S3a_真违规无标记仍FAIL", len(n_p) == 1 and "R3-3a" in n_p[0] and not n_w, "problems=%r warnings=%r" % (n_p, n_w))
# (b) 显式「原文照录」标记（命中点前 2 字符）→ 降级为警告，仍回验记录 match=False
t = "绑定行原文照录：「被核对象 SHA256 = %s，字节数 = %d（见 `%s`）」" % (wrong_sha, wrong_bytes, anchor)
n_p, n_w, nb = run(t)
check("S3b_显式照录降级为警告", not n_p and len(n_w) == 1 and "降级" in n_w[0] and nb[0]["match"] is False
      and nb[0]["citation"] is True, "problems=%r warnings=%r" % (n_p, n_w))
# (c) 对抗性伪标记不在白名单 → 仍 FAIL
for marker in ("引：", "引用锚已修复：", "引述待核："):
    t = "%s被核对象 SHA256 = %s，字节数 = %d（见 `%s`）" % (marker, wrong_sha, wrong_bytes, anchor)
    n_p, n_w, _ = run(t)
    check("S3c_伪标记不降级[%s]" % marker, len(n_p) == 1 and not n_w,
          "problems=%r warnings=%r" % (n_p, n_w))
# (d) 标记在命中点前 >24 字符（同行）→ 不算引文语境，仍 FAIL
t = "本轮实读「A」；间隔说明文字继续填充此处内容直至确保超过窗口宽度廿四。被核对象 SHA256 = %s，字节数 = %d（见 `%s`）" % (
    wrong_sha, wrong_bytes, anchor)
n_p, n_w, nb = run(t)
check("S3d_标记超24字不降级", len(n_p) == 1 and nb[0]["citation"] is False,
      "problems=%r citation=%r" % (n_p, nb[0]["citation"]))
# (e) 标记只在【前一行】→ 同行规则，不降级，仍 FAIL
t = "绑定行原文照录如下：\n被核对象 SHA256 = %s，字节数 = %d（见 `%s`）" % (wrong_sha, wrong_bytes, anchor)
n_p, n_w, nb = run(t)
check("S3e_标记仅在前行不降级", len(n_p) == 1 and nb[0]["citation"] is False,
      "problems=%r citation=%r" % (n_p, nb[0]["citation"]))

# ============ S4 any-match-wins 反误伤 ============
t = "被核对象 SHA256 = %s，字节数 = %d（见 `lead/r11_f2_fix_20261109/_f2_repro.py` 与 `%s`）" % (
    plus_sha, plus_bytes, anchor)
n_p, n_w, nb = run(t)
check("S4_多候选any-match-wins", not n_p and nb[0]["match"] is True
      and nb[0].get("verified_path", "").endswith("_f2_r11plus.py"),
      "problems=%r verified=%r" % (n_p, nb[0].get("verified_path")))

# ============ S5 原版行为保留 ============
# (a) raw 可解析（doc_dir 相对）→ 两版同 MATCH
t = "被核对象 `_f2_r11plus.py` SHA256 = %s，字节数 = %d" % (plus_sha, plus_bytes)
o_p, o_w, o_b = g7.r11_scan(t, F2PLUS.parent, root=REPO)
n_p, n_w, n_b = f2p.r11_scan_plus(t, F2PLUS.parent, root=REPO)
check("S5a_raw可解析行为一致",
      not o_p and not n_p and o_b[0]["match"] is True and n_b[0]["match"] is True
      and n_b[0].get("tier") == "T1" and n_b[0].get("suffix_stripped") is False,
      "orig match=%r plus match=%r" % (o_b[0]["match"], n_b[0]["match"]))
# (b) T1 raw 不在盘且无引文语境 → 消息原文逐字一致（纯后缀不可剥出在盘件的情形
#     用真实 L60 锚：文件全仓无同名可解析件时消息保持原样——此处用不存在件验证格式）
t = "被核对象 `_totally_absent_file.md:3-4` SHA256 = %s，字节数 = 1" % plus_sha
o_p, _, _ = g7.r11_scan(t, REPO / "lead", root=REPO)
n_p, _, _ = f2p.r11_scan_plus(t, REPO / "lead", root=REPO)
check("S5b_R3-3c消息原文一致", o_p == n_p and len(n_p) == 1, "orig=%r plus=%r" % (o_p, n_p))
# (c) 缺绑定行消息逐字一致
o_p, _, _ = g7.r11_scan("hello 无绑定", REPO / "lead", root=REPO)
n_p, _, _ = f2p.r11_scan_plus("hello 无绑定", REPO / "lead", root=REPO)
check("S5c_缺绑定行消息一致", o_p == n_p and len(n_p) == 1, "%r" % (n_p,))

# ============ S6 30 件无新误报清点 ============
reg = json.loads((REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json")
                 .read_text(encoding="utf-8"))
new_fp = []
for r in reg["results_30"]:
    p = Path(r["file"])
    text = p.read_bytes().decode("utf-8")
    o_p, _, _ = g7.r11_scan(text, p.parent, root=REPO)
    n_p, _, _ = f2p.r11_scan_plus(text, p.parent, root=REPO)
    if len(n_p) > len(o_p):
        new_fp.append({"file": str(p), "orig": o_p, "plus": n_p})
check("S6_30件零新增problem", not new_fp, "新增 problem 的文件数=%d %s" % (len(new_fp), new_fp))

n_fail = sum(1 for c in checks if not c["ok"])
print()
print("自检 %d 项，失败 %d 项" % (len(checks), n_fail))
(REPO / "lead" / "r11_f2_fix_20261109" / "_f2_selftest_out.json").write_text(
    json.dumps({"checks": checks, "fail": n_fail}, ensure_ascii=False, indent=2), encoding="utf-8")
raise SystemExit(1 if n_fail else 0)
