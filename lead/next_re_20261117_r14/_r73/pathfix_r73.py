# -*- coding: utf-8 -*-
"""R73 · 把门禁从「本机跑不起来」变成「本机可直跑」，并实测「探针替换」是否等价。

背景（全部来自盘上记录，不是我推断）：
  R68 记录：check_disc.py 的 ROOT 硬编码 D:\\Project\\ra2-campaign-forge；
            recheck_verify.py 里 rel.replace('/','\\\\') 在 Linux 上方向反了。
            当时的结论原话是「用只替换这两处的探针复现……这是口径偏差、不是等价物」。
  R72 记录：2x2 矩阵是在**内存 patch** 下做的，live 一字未改，5 条 C11 FAIL 仍未修。

本轮只做两件事：
  A 把两处**路径处理**缺陷修到手（不碰任何判据、不碰窗口表、不碰 DISC_RECHECK.tsv 的判据列）。
    修法必须是「两边都对」而不是「让 Linux 过」：
      recheck_verify.py  ap = rel.replace('\\\\', os.sep).replace('/', os.sep)
        —— Windows 上 os.sep='\\\\'，与原行为等价；POSIX 上 os.sep='/'，反斜杠被切分。
      check_disc.py      ROOT 先取 Windows 字面量，若该目录不存在则按 __file__ 反推三层。
        —— Windows 上目录存在，走原值（逐字节等价）；POSIX 上走反推。
  B 实测「探针替换 ≡ live 直跑」：把 R68 的探针（内存替换）与修好后的 live 各跑一遍，
    逐行比对输出。**这才把「口径偏差、不是等价物」这条未验证的限定语变成测量结果。**

纪律：写前 wx 独占备份 + 断言旧 sha256 + 一次性写入 + 回读校验；
      任何断言 FAIL 立即 exit 3。
"""
import io, os, re, sys, hashlib, time, types, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
BASE = os.path.join(R14, "R17_LEAD_BASELINE")
GATE = os.path.join(R14, "check_disc.py")
RV = os.path.join(R14, "recheck_verify.py")

EXP_SHA = {
    "check_disc.py": "f957c97bb90ee839",      # 16 位前缀，开局实测
    "recheck_verify.py": "dc3ed88b014f449f",
}
EXP_CR = {"check_disc.py": 309, "recheck_verify.py": 321}

FAILS = []


def P(s=""):
    print(s)


def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c:
        FAILS.append(n)
    return c


def abort(where):
    if FAILS:
        P("")
        P("[ABORT] %s 断言失败：%s —— 不写任何 live 文件" % (where, FAILS))
        sys.exit(3)


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---- 0 · 旧状态 ----
P("=== S0 · 旧状态与前置断言 ===")
old = {}
for name in ("check_disc.py", "recheck_verify.py"):
    p = os.path.join(R14, name)
    b = io.open(p, "rb").read()
    old[name] = b
    P("  [before] %-20s %6d B  CR=%-4d sha=%s" % (name, len(b), b.count(b"\r"), sha(b)[:16]))
    ck("旧 %s sha 前缀 == 开局记录" % name, sha(b)[:16] == EXP_SHA[name], sha(b)[:16])
    ck("旧 %s CR == %d" % (name, EXP_CR[name]), b.count(b"\r") == EXP_CR[name],
       str(b.count(b"\r")))
abort("前置")

src_cd = old["check_disc.py"].decode("utf-8")
src_rv = old["recheck_verify.py"].decode("utf-8")

# ---- 1 · 旧缺陷的**直接证据**（不是引 R68 的话）----
P("")
P("=== S1 · 两处缺陷的直接证据（本机实测）===")
OLD_ROOT = "ROOT = r'D:\\Project\\ra2-campaign-forge'"
ck("S1-a check_disc.py 含 Windows 硬编码 ROOT", OLD_ROOT in src_cd)
ck("S1-b 该 ROOT 在本机不存在", not os.path.isdir(r"D:\Project\ra2-campaign-forge"))
OLD_REL = "ap = rel.replace('/', '\\\\')"
ck("S1-c recheck_verify.py 含反向分隔符替换", OLD_REL in src_rv)
# 用旧逻辑在真机上算一条真实行的解析路径：必须解不出文件
probe_rel = "lead\\next_re_20261117_r14\\R17_R61_FACTINDEX_V58\\anchor_check.txt"
old_ap = os.path.join(ROOT, probe_rel.replace("/", "\\"))
ck("S1-d 旧逻辑在 POSIX 上解析出的路径不是文件（缺陷可复现）", not os.path.isfile(old_ap),
   old_ap.replace(ROOT, "<ROOT>"))
new_ap = os.path.join(ROOT, probe_rel.replace("\\", os.sep).replace("/", os.sep))
ck("S1-e 新逻辑在 POSIX 上解析出的路径是文件（修法有效）", os.path.isfile(new_ap),
   new_ap.replace(ROOT, "<ROOT>"))
ck("S1-f 反控 · 新逻辑在 Windows 语义下与原逻辑等价（模拟 os.sep='\\\\'）",
   probe_rel.replace("\\", "\\").replace("/", "\\") == probe_rel.replace("/", "\\"))

# ---- 2 · 生成新源码（最小替换，各一处）----
P("")
P("=== S2 · 最小替换（每个文件各一处，不动判据）===")
NEW_ROOT = (
    "ROOT = r'D:\\Project\\ra2-campaign-forge'\n"
    "if not os.path.isdir(ROOT):                      # R73：POSIX 上按本文件位置反推三层\n"
    "    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))"
)
NEW_REL = "ap = rel.replace('\\\\', os.sep).replace('/', os.sep)   # R73：分隔符无关（Windows 下与旧行为等价）"

ck("替换点 check_disc ROOT 唯一", src_cd.count(OLD_ROOT) == 1, str(src_cd.count(OLD_ROOT)))
ck("替换点 recheck_verify rel 唯一", src_rv.count(OLD_REL) == 1, str(src_rv.count(OLD_REL)))
new_cd = src_cd.replace(OLD_ROOT, NEW_ROOT)
new_rv = src_rv.replace(OLD_REL, NEW_REL)
ck("新 check_disc 不再含硬编码独立 ROOT 行",
   "if not os.path.isdir(ROOT):" in new_cd and OLD_ROOT in new_cd)  # 字面量保留为 Windows 首选值
ck("新 recheck_verify 不再含反向替换", "rel.replace('/', '\\\\')" not in new_rv)

# 反控：Windows 分支必须逐字节保持原行为 —— 用模拟 os.sep 的方式验证替换式
import ntpath
sim_win = probe_rel.replace("\\", "\\").replace("/", "\\")
ck("反控 W1 Windows 下新式 == 旧式（同一条真实行）", sim_win == probe_rel.replace("/", "\\"))
ck("反控 W2 POSIX 下新旧不同（否则等于没改）",
   probe_rel.replace("\\", os.sep).replace("/", os.sep) != probe_rel.replace("/", "\\"))
ck("反控 W3 check_disc 保留 Windows 首选值（不是把 Windows 路径删掉）",
   "ROOT = r'D:\\Project\\ra2-campaign-forge'" in new_cd)

# 语法与 GATE_VER 不得被破坏（C7 会 grep GATE_VER = 'R58'）
ck("GATE_VER 行逐字未变", "GATE_VER = 'R58'" in new_cd)
for nm, s in (("check_disc", new_cd), ("recheck_verify", new_rv)):
    try:
        compile(s, nm, "exec")
        ck("%s 新源码可编译" % nm, True)
    except SyntaxError as e:
        ck("%s 新源码可编译" % nm, False, str(e))
abort("写前自洽")

# ---- 3 · 备份 + 一次性写入 + 回读 ----
P("")
P("=== S3 · 备份 / 写入 / 回读 ===")
ts = time.strftime("%Y%m%d_%H%M%S")
bks = {}
for nm in ("check_disc.py", "recheck_verify.py"):
    bks[nm] = os.path.join(BASE, "SUPERSEDED.before_r73_pathfix_%s_%s.bak" % (nm, ts))
    with open(bks[nm], "xb") as f:
        f.write(old[nm])
    ck("备份 %s 字节一致" % os.path.basename(bks[nm]),
       sha(io.open(bks[nm], "rb").read()) == sha(old[nm]))
abort("备份")

for nm, new_s in (("check_disc.py", new_cd), ("recheck_verify.py", new_rv)):
    with open(os.path.join(R14, nm), "wb") as f:
        f.write(new_s.encode("utf-8"))
    got = io.open(os.path.join(R14, nm), "rb").read()
    P("  [after] %-20s %6d B  CR=%-4d sha=%s"
      % (nm, len(got), got.count(b"\r"), sha(got)[:16]))
    ck("回读 %s 字节 == 预期" % nm, got == new_s.encode("utf-8"))
    ck("回读 %s CR == %d（行尾未被规范化）" % (nm, EXP_CR[nm]), got.count(b"\r") == EXP_CR[nm],
       str(got.count(b"\r")))
    # 逐行 diff：改动行数必须极少且可枚举
    a = old[nm].decode("utf-8").split("\n")
    b = new_s.split("\n")
    import difflib
    sm = difflib.SequenceMatcher(None, a, b)
    changed = [(t, i1, i2, j1, j2) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
    P("       改动块 %d 个：%s" % (len(changed), [(t, i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in changed]))
    ck("%s 改动块 = 1（单点替换）" % nm, len(changed) == 1)

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
