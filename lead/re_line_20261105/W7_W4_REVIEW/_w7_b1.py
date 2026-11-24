# -*- coding: utf-8 -*-
# W7 · B1 独立复核探针（只读；零真机；零注入）
# 被核对象 = lead/re_line_20261105/W4_FIELD_SPEC/sections/Q2_ALPHA.md
# 用法: python -I -X utf8 D:/.../W7_W4_REVIEW/_w7_b1.py > D:/.../W7_W4_REVIEW/_w7_b1_out.txt 2>&1
import hashlib
import os
import sys
import datetime
from fractions import Fraction

ROOT = r"D:\Project\ra2-campaign-forge"
OBJ = os.path.join(ROOT, r"lead\re_line_20261105\W4_FIELD_SPEC\sections\Q2_ALPHA.md")
W3 = os.path.join(ROOT, r"lead\re_line_20261105\W3_COSTBOUND\sections\Q3_SAMPLE_PLAN.md")
D19_RULING = os.path.join(ROOT, r"lead\re_line_20261105\D19_RULING\RULING_D19.md")
D19_FACT = os.path.join(ROOT, r"lead\re_line_20261105\D19_RULING\FACTBASE_D19.md")
C_GEN = os.path.join(ROOT, r"lead\re_line_20261105\W4_FIELD_SPEC\sections\card_0087E8E0.md")
C_THREAT = os.path.join(ROOT, r"lead\re_line_20261105\W4_FIELD_SPEC\sections\card_00A8EC34.md")
C_DIRTY = os.path.join(ROOT, r"lead\re_line_20261105\W4_FIELD_SPEC\sections\card_00B0CE88.md")
C_BULLET = os.path.join(ROOT, r"lead\re_line_20261105\W4_FIELD_SPEC\sections\card_00A8ED50.md")


def sec(t):
    print("\n" + "=" * 78)
    print("### " + t)
    print("=" * 78)


def sha(p):
    b = open(p, "rb").read()
    return len(b), hashlib.sha256(b).hexdigest()


def lines(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def grep(p, pat, label=None):
    """打印 (行号, 文本) 命中；返回命中行号列表。"""
    import re
    out = []
    for i, ln in enumerate(lines(p), 1):
        if re.search(pat, ln):
            out.append(i)
            print("  %s:%d| %s" % (os.path.basename(p), i, ln.strip()[:230]))
    if not out:
        print("  (0 命中) %s" % (label or pat))
    return out


# ---------------------------------------------------------------- 0 绑定
sec("0. B1 被核对象 SHA256 / 字节数 / 复核时刻（本人实算）")
n, h = sha(OBJ)
print("被核对象 = Q2_ALPHA.md")
print("绝对路径 =", OBJ)
print("SIZE =", n)
print("SHA256 =", h)
print("复核时刻 =", datetime.datetime.now().astimezone().isoformat())
print("文件 mtime =", datetime.datetime.fromtimestamp(os.path.getmtime(OBJ)).astimezone().isoformat())
TASK_REF_SHA = "27055e6b94f892c6a53facc07adf908688c151eca82cfe56da8133cee8507663"
TASK_REF_SIZE = 31712
print("任务书参照 SHA256 =", TASK_REF_SHA, " 一致 =", h == TASK_REF_SHA)
print("任务书参照 字节数 =", TASK_REF_SIZE, " 一致 =", n == TASK_REF_SIZE)
print("OBJECT_CHANGED =", (h != TASK_REF_SHA or n != TASK_REF_SIZE))

# ---------------------------------------------------------------- 1 Engine
sec("1. ra2tool.Engine 装载 + 目标二进制哈希（TASK.md:120/111 指定读法）")
sys.path.insert(0, os.path.join(ROOT, r"lead\goal3t_nightwatch_20261102\swarm_20261104"))
from ra2tool import Engine

e = Engine()
print("Engine().sha =", e.sha)
exe = os.path.join(ROOT, r"ra2youli\gamemd.exe")
en, eh = sha(exe)
print("gamemd.exe SIZE/SHA256 (本人实算) =", en, eh)
print("Q2_ALPHA.md:93 自报 SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")
print("三者一致 =", e.sha == eh == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")
print(".text coverage(%, insns, resync_fails) =", e.coverage)
print("节表:")
for s in e.SEC:
    print("   %-8s VA=0x%08X vsize=0x%X raw_ptr=0x%X raw_size=0x%X" % (s[0], s[1], s[2], s[3], s[4]))

# ---------------------------------------------------------------- 2 反汇编复核 §2.2
sec("2. 独立反汇编复核 Q2_ALPHA.md §2.2 的四段（逐字节比对自报输出）")
RANGES = [
    ("[1] 0x42A5F0..0x42A610 GenerationStamp inc/写回", 0x42A5F0, 0x20),
    ("[2] 0x42CC70..0x42CC90 同步重试再次调用 0x42A5B0", 0x42CC70, 0x20),
    ("[3] 0x55B93F..0x55B965 Bullet +0x98 活跃门控", 0x55B93F, 0x26),
    ("[4] 0x6F8DF0..0x6F8E10 索敌入口 inc/写回", 0x6F8DF0, 0x20),
]
for name, va, ln in RANGES:
    print("\n-- %s --" % name)
    for r in e.disasm(va, ln):
        print("0x%08x %-18s %-6s %s" % (r[0], r[1], r[2], r[3]))

sec("2b. 复核 §4.1/§4.4 反例所需的「回绕/构造初值/重置」字节")
for name, va, ln in [
    ("0x42A5F9..0x42A610 (inc + jne 回绕分支)", 0x42A5F9, 0x18),
    ("0x42A67F..0x42A68D (回绕后再自增跳过 0)", 0x42A67F, 0x12),
    ("0x42A6D0..0x42A710 (构造体: ecx=-1, [esi+0x28]=-1)", 0x42A6D0, 0x42),
    ("0x40AFA0..0x40AFAF (静态构造 thunk call 0x42A6D0)", 0x40AFA0, 0x10),
    ("0x6F8E09 写点附近", 0x6F8E00, 0x14),
]:
    print("\n-- %s --" % name)
    for r in e.disasm(va, ln):
        print("0x%08x %-18s %-6s %s" % (r[0], r[1], r[2], r[3]))

sec("2c. 全镜像绝对地址访存普查（写点 / 是否有清零指令）")
for va, nm in [(0xA8EC34, "0x00A8EC34 (ΔThreatCalls)"),
               (0x87E8E0, "0x0087E8E0 (ΔGenStamp)"),
               (0xB0CE88, "0x00B0CE88 (DirtyAreas.Count)"),
               (0xA8ED50, "0x00A8ED50 (BulletCount)")]:
    hits = e.disp_hits(va)
    print("\n%s : disp_hits 共 %d 条" % (nm, len(hits)))
    for x in hits:
        print("   0x%08x %s %-8s %s" % (x[0], x[1], x[2], x[3]))

sec("2d. BSS 几何：0x00A8EC34 是否零填充（进程重启 ⇒ 向下跳变）")
datasec = next(s for s in e.SEC if s[0] == ".data")
print(".data VA=0x%X vsize=0x%X raw_size=0x%X" % (datasec[1], datasec[2], datasec[4]))
for va in (0xA8EC34, 0x87E8E0, 0xB0CE88, 0xA8ED50):
    delta = va - datasec[1]
    print("   VA=0x%08X  delta=0x%X  in_raw=%s  (delta>=raw_size ⇒ 文件侧零填充)" %
          (va, delta, delta < datasec[4]))
print("Engine().u32(0xA8EC34) 文件侧 =", e.u32(0xA8EC34))

# ---------------------------------------------------------------- 3 数学复核
sec("3. §5.2 构造性反证：任给观测，任意 T 分解都能自洽（用 Fraction 精确验算）")
y = [Fraction(120), Fraction(7), Fraction(45), Fraction(310)]
DT = Fraction(200)
print("固定观测 y =", [str(v) for v in y], " ΔT_deficit =", DT)
cases = [
    ("C1 占 98.5%", [Fraction(197), Fraction(1), Fraction(1), Fraction(1)]),
    ("C2 占 98.5%", [Fraction(1), Fraction(197), Fraction(1), Fraction(1)]),
    ("均分", [Fraction(50), Fraction(50), Fraction(50), Fraction(50)]),
    ("偏 C3/C4", [Fraction(1), Fraction(1), Fraction(99), Fraction(99)]),
]
allok = True
for label, T in cases:
    assert sum(T) == DT, label
    a = [y[i] / T[i] for i in range(4)]
    eq = [a[i] * T[i] == y[i] for i in range(4)]
    eq.append(sum(T) == DT)  # ε = 0
    ok = all(eq)
    allok &= ok
    print("  %-12s T=%s  ΣT=%s  alpha=%s  5式全成立(+ε=0)=%s" %
          (label, [str(v) for v in T], sum(T), [str(v) for v in a], ok))
print("=> 4/4 组分解全部精确成立; 五个方程对 T 的分解零约束 =", allok)

sec("3b. W3 :177 矩阵的秩（sympy 符号/数值双算）")
import sympy as sp
a1, a2, a3, a4 = sp.symbols("a1 a2 a3 a4", nonzero=True)
M = sp.Matrix([[a1, 0, 0, 0], [0, a2, 0, 0], [0, 0, a3, 0], [0, 0, 0, a4], [1, 1, 1, 1]])
print("符号矩阵 M(5x4) ="); sp.pprint(M)
print("rank(M) 当 alpha_i 为已知非零常数 =", M.rank())
Mn = sp.Matrix([[2, 0, 0, 0], [0, 3, 0, 0], [0, 0, 5, 0], [0, 0, 0, 7], [1, 1, 1, 1]])
print("数值实例 rank =", Mn.rank(), " (W3 所称 Rank=4 对该【已知系数】矩阵成立)")
print("若 alpha_i 还原为未知 ⇒ 未知量 4(T)+4(alpha)+1(eps)=9, 方程 4+1=5; "
      "y_i=alpha_i*T_i 为双线性，rank 只是对假定矩阵的性质，不足以推出 T 可辨识。")
# 未知量/方程计数
print("计数核验: 4+4+1 =", 4 + 4 + 1, " 未知; 4+1 =", 4 + 1, " 方程; 自由度(泛称) =", 9 - 5)

# ---------------------------------------------------------------- 4 文本复核 ③
sec("4. 批评③：W3 :177 是否把 alpha 当已知常数、Rank=4 是否「前提不是结论」")
print("\n[W3 Q3_SAMPLE_PLAN.md] alpha / Rank / 唯一解 / 超定 命中:")
grep(W3, r"alpha|\\alpha|Rank|满秩|唯一解|超定|校准|标定")
print("\n[W3 :144-178 原文（逐行）]")
for i in range(143, 179):
    txt = lines(W3)[i - 1]
    print("  :%d| %s" % (i, txt.strip()[:220]))
print("\n[Q2_ALPHA.md] 是否出现字面「前提不是结论」:")
grep(OBJ, r"前提不是结论|前提是|不是结论")
print("\n[Q2_ALPHA.md] 批评③相关原句:")
grep(OBJ, r"已知常数|假设了待求|Rank = 4|双线性|零约束")
print("\n[W3 全文 + D19_RULING 目录] 是否存在 alpha 数值/测量方法/配对样本:")
import glob
for p in sorted(glob.glob(os.path.join(ROOT, r"lead\re_line_20261105\W3_COSTBOUND\sections\*.md")) +
                glob.glob(os.path.join(ROOT, r"lead\re_line_20261105\D19_RULING\*.md"))):
    hits = grep(p, r"alpha|\\alpha", label=os.path.basename(p))
    if hits:
        print("   -> %s : %d 行含 alpha" % (os.path.basename(p), len(hits)))
print("\n[D19 定谳对同一批评的表述]")
grep(D19_RULING, r"满秩|alpha|映射未校准|地址彼此不同")
print("\n[FACTBASE_D19.md:47]")
for i in (46, 47, 48):
    print("  :%d| %s" % (i, lines(D19_FACT)[i - 1].strip()[:600]))

# ---------------------------------------------------------------- 5 文本复核 ②
sec("5. 反例②：重置/进程重启 ⇒ Δy ≤ 0 的字节与底稿依据")
print("\n[Q2_ALPHA.md] 反例②原句:")
grep(OBJ, r"Δy ≤ 0|Δ y_1 ≤ 0|重置/进程重启|连这个都保不住|连非负性")
print("\n[card_0087E8E0.md] 回绕/构造初值/重置:")
grep(C_GEN, r"回绕跳 0|\+2|首次调用即|0xFFFFFFFF|重置点|跨进程|不可判", )
print("\n[card_00A8EC34.md] 进程重启/BSS/无清零:")
grep(C_THREAT, r"进程重启|重新零填充|重置 / 清零|未发现任何|BSS|跨进程")
print("\n[FACTBASE_D19.md:37] 生命周期告诫:")
for i in (37,):
    print("  :%d| %s" % (i, lines(D19_FACT)[i - 1].strip()[:1400]))

# ---------------------------------------------------------------- 6 文本复核 ④
sec("6. 量纲分层④：文件自述是否前后一致 + 与四张卡/W3 是否一致")
print("\n[Q2_ALPHA.md] 全部 差分/水位/流量/瞬时 分类行:")
grep(OBJ, r"窗口差分|瞬时水位|流量型|水位型|\*\*水位\*\*|差分（")
print("\n[Q2_ALPHA.md §1 表 :28-33 与 §4.5 表 :272-277 原文]")
for i in list(range(28, 34)) + list(range(272, 280)):
    print("  :%d| %s" % (i, lines(OBJ)[i - 1].strip()[:250]))
print("\n[card_00B0CE88.md] 自述量纲:")
grep(C_DIRTY, r"双向变化的瞬时|每帧可归零|不是单调累加器|瞬时条目数")
print("\n[card_00A8ED50.md] 自述量纲:")
grep(C_BULLET, r"双向变化的瞬时|是否累加计数器|瞬时容器长度")
print("\n[W3 Q3_SAMPLE_PLAN.md:177 矩阵左端 y 记号]")
for i in (176, 177, 178):
    print("  :%d| %s" % (i, lines(W3)[i - 1].strip()[:400]))

# ---------------------------------------------------------------- 7 诚实账
sec("7. Q2_ALPHA.md 诚实账（§7 :331-347）原文比对")
for i in range(331, 348):
    print("  :%d| %s" % (i, lines(OBJ)[i - 1].strip()[:260]))

sec("8. 结论摘要（探针自动给出的事实）")
print("A. SHA256 绑定与任务书一致 =", h == TASK_REF_SHA and n == TASK_REF_SIZE)
print("B. 目标二进制 SHA 与 Q2_ALPHA 自报一致 =", eh == e.sha)
print("C. §5.2 构造性反证 4/4 组成立 =", allok)
print("D. W3 :177 矩阵在 alpha 已知非零时 rank =", M.rank())
print("E. Q2_ALPHA 字面是否写「前提不是结论」 =", bool(grep(OBJ, r"前提不是结论")) if False else
      any("前提不是结论" in x for x in lines(OBJ)))
print("\nDONE")
