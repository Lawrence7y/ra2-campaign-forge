# -*- coding: utf-8 -*-
"""R73 · 探针 vs live 直跑：把 R68 那句「口径偏差、不是等价物」变成测量结果。

R68 的原话（盘上，_r68/write_lock_r68.py:34）：
  「Linux 上 check_disc.py 无法直接运行（ROOT 硬编码 D:\\、rel.replace('/','\\\\') 反向转换）。
    用只替换这两处的探针复现出与 Windows 一致的 ok=0 fail=5 frozen=12 none=11，
    这是口径偏差、不是等价物。」
—— 「不是等价物」是**没测过的限定语**。它若为真，R68/R71/R72 用探针得出的数要打折。

本轮 live 已修（pathfix_r73），故可测量：
  探针 = **R73 之前的原版源码**（取自 R17_LEAD_BASELINE 的 .bak）+ 两处内存替换（R68 的做法）
  live = 直跑子进程（本轮修好的文件）
两者各跑一遍，逐行比对 stdout。

【本脚本第一版的三个自错，全部由它自己的反控抓出，如实记录】
  ① 把探针的替换方向写反了（默认套上旧缺陷）⇒ S1-c FAIL：探针报 R1 missing、live 报 R4。
  ② 因此 N1「只换 ROOT」那格实际是**修好的**配置 ⇒ 与 live 恒等，零信息格。
  ③ N2 变异打在第 57 行窗口端点，而 5 条目标全落在**第 55 行**窗口 ⇒ 变异未落到被测判据上。
  修法：探针基线改成「原版 .bak 源码」，N1 改成「原版 + 只换 ROOT」，N2 变异打到 r55。

反控（否则「逐行相同」无意义）：
  N3 同一方式连跑两次逐字相同（无可变因素）
  N1 原版 + 只换 ROOT（缺分隔符替换）⇒ 必须**不等于** live，且必须复现旧缺陷形态
  N2 修好版 + r55 窗口端点挪 1 秒 ⇒ 必须**不等于** live，且 reason 文本必须变
"""
import io, os, re, sys, types, glob, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
BASE = os.path.join(R14, "R17_LEAD_BASELINE")

FAILS = []


def P(s=""):
    print(s)


def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c:
        FAILS.append(n)
    return c


# ---- 原版源码（R73 之前的 .bak）----
def orig(name):
    pat = os.path.join(BASE, "SUPERSEDED.before_r73_pathfix_%s_*.bak" % name)
    hits = sorted(glob.glob(pat))
    assert hits, "找不到 %s 的原版备份" % name
    return io.open(hits[-1], encoding="utf-8").read(), os.path.basename(hits[-1])


ORIG_CD, CD_BAK = orig("check_disc.py")
ORIG_RV, RV_BAK = orig("recheck_verify.py")


def run_live(gate_path, cwd=None):
    r = subprocess.run([sys.executable, gate_path], cwd=cwd or R14,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.stdout.decode("utf-8", "replace"), r.returncode


def run_mem(cd_src, rv_src, tag):
    """内存 exec：rv_src 先注册进 sys.modules，check_disc 源码再 exec（R68 探针的做法）。"""
    m = types.ModuleType("recheck_verify")
    m.__file__ = os.path.join(R14, "recheck_verify.py")
    exec(compile(rv_src, m.__file__, "exec"), m.__dict__)
    sys.modules["recheck_verify"] = m
    g = {"__name__": "__main__", "__file__": os.path.join(R14, "check_disc.py")}
    buf = []
    g["print"] = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
    code = None
    try:
        exec(compile(cd_src, g["__file__"], "exec"), g)
    except SystemExit as e:
        code = e.code
    finally:
        sys.modules.pop("recheck_verify", None)
    return "\n".join(buf) + "\n", (0 if code in (0, None) else 1)


def norm(t):
    return t.replace("\r\n", "\n").rstrip("\n")


def diff_lines(a, b):
    la, lb = norm(a).split("\n"), norm(b).split("\n")
    out = []
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "<MISSING>"
        y = lb[i] if i < len(lb) else "<MISSING>"
        if x != y:
            out.append((i + 1, x, y))
    return out


# ---- R68 式两处替换（作用在**原版**源码上）----
OLD_ROOT = "ROOT = r'D:\\Project\\ra2-campaign-forge'"
OLD_REL = "ap = rel.replace('/', '\\\\')"
NEW_REL = "ap = rel.replace('\\\\', os.sep).replace('/', os.sep)"
ck("原版 check_disc 含 Windows ROOT", OLD_ROOT in ORIG_CD, CD_BAK)
ck("原版 recheck_verify 含反向替换", OLD_REL in ORIG_RV, RV_BAK)

PROBE_CD = ORIG_CD.replace(OLD_ROOT, "ROOT = %r" % ROOT)
PROBE_RV = ORIG_RV.replace(OLD_REL, NEW_REL)
N1_CD = ORIG_CD.replace(OLD_ROOT, "ROOT = %r" % ROOT)   # 只换 ROOT，缺分隔符替换
N1_RV = ORIG_RV                                        # 保持旧缺陷

P("=== S1 · live 直跑 vs R68 式探针（原版 + 两处替换）===")
live_out, live_rc = run_live(os.path.join(R14, "check_disc.py"))
probe_out, probe_rc = run_mem(PROBE_CD, PROBE_RV, "probe")
P("  [live]  exit=%d  %d 行" % (live_rc, len(norm(live_out).split("\n"))))
P("  [probe] exit=%d  %d 行" % (probe_rc, len(norm(probe_out).split("\n"))))

# N3：可比对的前提
live_out2, _ = run_live(os.path.join(R14, "check_disc.py"))
probe_out2, _ = run_mem(PROBE_CD, PROBE_RV, "probe2")
ck("N3 反控 · live 连跑两次逐字相同", norm(live_out) == norm(live_out2))
ck("N3 反控 · 探针连跑两次逐字相同", norm(probe_out) == norm(probe_out2))

d = diff_lines(live_out, probe_out)
P("  [比对] 不同行 %d 条" % len(d))
for ln, x, y in d[:8]:
    P("        L%-3d live : %s" % (ln, x[:96]))
    P("             probe: %s" % y[:96])
ck("S1-a 退出码相同", live_rc == probe_rc, "%d vs %d" % (live_rc, probe_rc))
ck("S1-b 输出逐行相同（探针 ≡ live 直跑）", len(d) == 0, "%d 行不同" % len(d))

KEY = ("C11 col7 machine-check", "C7 live-checks passed", "C8 section-exists passed",
       "C10 self-check", "discipline defs")


def grab(t, k):
    for l in t.split("\n"):
        if k in l:
            return l.strip()
    return "<NOT FOUND>"


for k in KEY:
    ck("S1-c 关键行一致 · %s" % k, grab(live_out, k) == grab(probe_out, k),
       grab(live_out, k)[:66])

# ---- 反控 N1：原版 + 只换 ROOT（缺分隔符替换）⇒ 必须不同，且复现旧形态 ----
P("")
P("=== S2 · 反控 N1：原版 + 只换 ROOT ⇒ 必须与 live 不同 ===")
n1_out, n1_rc = run_mem(N1_CD, N1_RV, "n1")
dn1 = diff_lines(live_out, n1_out)
ck("N1-a 残缺探针输出与 live 不同（否则 S1-b 是恒真）", len(dn1) > 0, "%d 行不同" % len(dn1))
ck("N1-b 残缺探针的失败原因落在 R1（旧缺陷形态）",
   all("R1 product file missing" in y for _, _, y in dn1) and len(dn1) == 5,
   "%d 行，首条=%s" % (len(dn1), dn1[0][2][:70] if dn1 else "-"))
ck("N1-c live 侧同 5 条失败原因落在 R4（证两态可分辨）",
   sum(1 for l in live_out.split("\n") if "R4 at outside" in l) == 5,
   str(sum(1 for l in live_out.split("\n") if "R4 at outside" in l)))

# ---- 反控 N2：修好版 + r55 窗口**起点**回到 17:39:19 ⇒ 判据必须翻转 ----
# R73 自错修正（第二次）：初版把 r55 的**终点** 174645 挪到 174644 —— 但 5 条的 at 是
# 17:39:19 / 17:40:02，都**早于**起点 17:41:46，拒绝点是**起点**、终点根本没被读到。
# 那格是零信息格（与 R72 的 W_only 同族）。
# R73 自错修正（第三次）：把变异体写成 _r73/_mut/recheck_verify.py 落到盘上 —— 该模块的
# _HERE 随之变成 _r73/_mut，DISC_ESTABLISH.tsv 找不到，于是它先死在 R3、根本没测到窗口。
# 又是一格「测了别的东西」。修法：改走**内存注册**（rv.__file__ 仍指真目录），不落盘。
P("")
P("=== S3 · 反控 N2：r55 窗口起点挪到 17:39:19 ⇒ 判据必须翻转 ===")
live_rv = io.open(os.path.join(R14, "recheck_verify.py"), encoding="utf-8").read()
live_cd = io.open(os.path.join(R14, "check_disc.py"), encoding="utf-8").read()
ANCHOR = "(55, '174146', '174645'"
ck("N2-0 变异锚点存在（r55 行）", ANCHOR in live_rv)
mut_rv = live_rv.replace(ANCHOR, "(55, '173919', '174645'")   # 起点提前到 17:39:19
ck("N2-0b 变异确实改了字节", mut_rv != live_rv)

mut_out, mut_rc = run_mem(live_cd, mut_rv, "mut")
P("  [mutant] exit=%d" % mut_rc)
ck("N2-a 变异门禁输出与 live 不同", norm(mut_out) != norm(live_out))


def c11line(t):
    return grab(t, "C11 col7 machine-check")


P("        live   %s" % c11line(live_out))
P("        mutant %s" % c11line(mut_out))
# 强判据：变异必须把 5 条从 FAIL 翻成 PASS —— 这才证明「窗口端点是 live 的决定性条件」
ck("N2-b 变异使 C11 ok=0/fail=5 翻成 ok=5/fail=0（判据确实被触达）",
   "ok=0 fail=5" in c11line(live_out) and "ok=5 fail=0" in c11line(mut_out),
   c11line(mut_out))
ck("N2-c 变异体退出码为 0（C11 全绿则无 FAIL）", mut_rc == 0, str(mut_rc))
ck("N2-d 边界声明 · 这只证明「端点决定判据」，不证明「端点该取哪个值」",
   True, "改表/改行仍不可区分（R72 C3 已记），本轮不裁")

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
