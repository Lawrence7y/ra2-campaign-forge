# -*- coding: utf-8 -*-
"""R73 · 补 DISC_RECHECK.tsv 两行（纪律 32/33），修我本轮自己引入的 C1/C2 回归。

事实：我在 §2.78 里新增了「纪律 32 ·」与「纪律 33 ·」两个正式定义，
门禁按定义数 C1/C2 校验，于是 28 行 vs 30 定义 ⇒ 门禁从 **5 FAIL 变 7 FAIL**。
**这是我本轮改动造成的回归，必须当场修**，不能留着。

纪律要求（DISC_RECHECK.tsv 的 7 列）：
  1 纪律号 / 2 节 / 3 可执行判据（逐字截取）/ 4 必查的现有数据锚 / 5 产物路径 / 6 校验式 / 7 立条之后是否回跑过

两行的设计原则（如实声明，避免"为了绿而填"）：
  * 纪律 32 的产物是本轮 **recheckA_r73.py**，它里面就有「零信息格」这批评测结论原文
    ⇒ 校验式用 grep=<正文里逐字存在的串>，与其它纪律同族。
  * 纪律 33 的产物是 **probeequiv_r73.py**，里面写死了 norm() 与 stdout 捕获
    ⇒ 校验式用 grep=def norm。
  * 第 7 列**如实写「无」**：这两条是**本轮刚立**，还没有"后续轮回跑"。
    写「有」会立刻触发 C11 要求自描述行，而我没资格声称回跑过 —— 那是造假。
    写「无」⇒ C11 计入 claims-none，不 FAIL。

硬闸：wx 打包 + 断言旧 sha/CR + 纯追加（不重排行）+ 回读校验 + C1/C2 必须回到 28 行前的状态。
"""
import io, os, sys, hashlib, time

DRY = "--dry" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, "R17_LEAD_BASELINE")
DR = os.path.join(R14, "DISC_RECHECK.tsv")

EXP_LEN, EXP_CR, EXP_SHA = 8967, 0, "39af22f0f65f9a12"

FAILS = []


def P(s=""):
    print(s)


def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c:
        FAILS.append(n)
    return c


def need(n, c, d=""):
    ck(n, c, d)
    if not c:
        P("")
        P("[ABORT] 硬闸：%s —— 不写 live" % n)
        sys.exit(3)


def sha(b):
    return hashlib.sha256(b).hexdigest()


raw = io.open(DR, "rb").read()
P("=== S0 · 旧状态 ===")
P("  [before] DISC_RECHECK.tsv %d B CR=%d LF=%d sha=%s"
  % (len(raw), raw.count(b"\r"), raw.count(b"\n"), sha(raw)[:16]))
need("旧字节数 == %d" % EXP_LEN, len(raw) == EXP_LEN, str(len(raw)))
need("旧 CR == 0", raw.count(b"\r") == EXP_CR, str(raw.count(b"\r")))
need("旧 sha 前缀 == %s" % EXP_SHA, sha(raw)[:16] == EXP_SHA, sha(raw)[:16])

txt = raw.decode("utf-8")
need("行尾为 LF（末字符是 \\n）", txt.endswith("\n"))
rows = [l for l in txt.split("\n") if l]
P("  数据行（含表头）= %d" % len(rows))
need("现有行数 == 29（表头 1 + 28 条）", len(rows) == 29, str(len(rows)))
ids = [l.split("\t")[0] for l in rows[1:]]
need("现有纪律号 1..28 连续", ids == [str(i) for i in range(1, 29)], str(ids[:3]) + "...")
need("前置守卫：尚无纪律 32 行", "32\t" not in txt and not any(i == "32" for i in ids))
need("前置守卫：尚无纪律 33 行", not any(i == "33" for i in ids))

# ---- 校验式必须先在产物里实测命中（不许写完再指望它对）----
P("")
P("=== S1 · 校验式在产物里实测命中（写前先验）===")
import re as _re
P32 = os.path.join(R14, "_r73", "recheckA_r73.py")
P33 = os.path.join(R14, "_r73", "probeequiv_r73.py")
need("纪律 32 产物存在", os.path.isfile(P32), os.path.basename(P32))
need("纪律 33 产物存在", os.path.isfile(P33), os.path.basename(P33))
t32 = io.open(P32, encoding="utf-8").read()
t33 = io.open(P33, encoding="utf-8").read()
# R73 自错修正（第十二次）：初版判据串写成「零信息格（与 R72 的 W_only 同族」——
# 实测产物里那条串跨了 P(...) 的引号边界，逐字不存在（命中 0 次）。硬闸当场拦下。
# 改用产物第 113 行逐字存在的整句（含前缀 ⇒ 唯一命中）。
# 再修（第十三次）：门禁 C7 用 re.findall 编译该串 ⇒ 判据里**不能有正则元字符**。
# 上面那句含 ** 与 ⇒，re 报 multiple repeat。改用无元字符且唯一命中的整句。
PAT32 = "A1-a \u00b7 \u6211 S2 \u7684"
BS = chr(92)   # R73 自错（第十五次）：r"..." 之外再经一层拼接/写入时反斜杠易丢；显式用 chr(92)
PAT33 = "def norm" + BS + "(t" + BS + ")"
h32 = len(_re.findall(PAT32, t32))
h33 = len(_re.findall(PAT33, t33))
P("  纪律 32 判据串命中 %d 次" % h32)
P("  纪律 33 判据串命中 %d 次" % h33)
need("纪律 32 判据串在产物里恰好 1 次", h32 == 1, str(h32))
need("纪律 33 判据串在产物里恰好 1 次", h33 == 1, str(h33))

# 判据串不得含 tab / 换行（否则列会错位）
for nm, pat in (("32", PAT32), ("33", PAT33)):
    need("纪律 %s 判据串不含 tab/换行" % nm, "\t" not in pat and "\n" not in pat)

ROW32 = "\t".join([
    "32",
    "§2.78",
    "⇒ **纪律 32 · 反控必须落在「判据真正会被读到的那一格」上。** 本轮三次自我实证：反控取 `03:00:00` 先死 R3（R72）、终点扫描固定在红区起点（R73）、变异打到第 57 行而目标全在第 55 行（R73）。三次都不是「反控失败」，是**反控没打在判据上** —— 它测的是别的东西，因此无论结果如何都不携带信息。判据：**先证明这格能让判据翻转，再说它证明了什么**。",
    "零信息格（与 R72 的 W_only 同族",
    "lead\\next_re_20261117_r14\\_r73\\recheckA_r73.py",
    "grep=" + PAT32,
    "无（仅立条当轮自带）",
])

ROW33 = "\t".join([
    "33",
    "§2.78",
    "**纪律 33 · 「等价」必须带输出通道限定语。** 本轮证明的是 stdout 文本逐行一致（经 CRLF 归一化），不是字节级等价、不覆盖 stderr 与写盘副作用。凡写「探针与直跑等价」，必须同时写这条边界。",
    "等价判定经 norm() 归一化（非字节级）",
    "lead\\next_re_20261117_r14\\_r73\\probeequiv_r73.py",
    "grep=" + PAT33,
    "无（仅立条当轮自带）",
])

for nm, r in (("32", ROW32), ("33", ROW33)):
    cols = r.split("\t")
    need("纪律 %s 行恰好 7 列" % nm, len(cols) == 7, str(len(cols)))
    need("纪律 %s 第 7 列以「无」开头" % nm, cols[6].startswith("无"), cols[6])
    need("纪律 %s 第 5 列路径存在" % nm,
         os.path.isfile(os.path.join(R14, cols[4].replace("lead\\next_re_20261117_r14\\", "").replace("\\", "/"))),
         cols[4])

new_txt = txt + ROW32 + "\n" + ROW33 + "\n"
P("")
P("[after] 预计 %d B（+%d B）CR=0 LF=%d"
  % (len(new_txt.encode("utf-8")), len(new_txt.encode("utf-8")) - len(raw),
     new_txt.count("\n")))

# ---- 写前模拟门禁的 C7 判据（grep= 至少命中 1 次）----
P("")
P("=== S2 · 模拟 C7/C1/C2 ===")
for nm, pat, prod in (("32", PAT32, t32), ("33", PAT33, t33)):
    n = len(_re.findall(pat, prod, _re.M))
    need("C7 预演 · 纪律 %s 的 grep 命中 >= 1" % nm, n >= 1, "%d" % n)
newlines = [l for l in new_txt.split("\n") if l]
newids = [l.split("\t")[0] for l in newlines[1:]]
# R73 自错修正（第十四次）：初版把期望写成 30，漏了表头。非空行 = 表头 1 + 纪律 30 = 31。
need("C1 预演 · 新行数 == 31（表头 1 + 纪律 30）", len(newlines) == 31, str(len(newlines)))
need("C2 预演 · 编号 1..28 + 32 + 33", newids == [str(i) for i in range(1, 29)] + ["32", "33"],
     str(newids))

# R73 新增硬闸（第十五次自错后加）：把整行**拼进新文件文本再解析回来**，
# 确认第 6 列原样是 PAT33（而不是被某一层转义吃掉反斜杠）。
_rt = (txt + ROW32 + "\n" + ROW33 + "\n").split("\n")
for nm, pat in (("32", PAT32), ("33", PAT33)):
    col6 = [l for l in _rt if l.startswith(nm + "\t")][0].split("\t")[5]
    need("往返解析 · 纪律 %s 第 6 列逐字 == 预期判据串" % nm, col6 == "grep=" + pat,
         repr(col6))
    need("往返解析 · 纪律 %s 第 6 列在产物里真能命中" % nm,
         len(_re.findall(col6[len("grep="):], t32 if nm == "32" else t33, _re.M)) >= 1,
         col6)

P("")
P("=== S3 · 备份 / 写入 / 回读 ===")
ts = time.strftime("%Y%m%d_%H%M%S")
bp = os.path.join(BASE, "SUPERSEDED.before_r73_discrecheck_%s.bak" % ts)
if DRY:
    P("  [DRY-RUN] 跳过备份与写入")
else:
    with open(bp, "xb") as f:
        f.write(raw)
    need("备份 sha 一致", sha(io.open(bp, "rb").read()) == sha(raw), os.path.basename(bp))
    with open(DR, "wb") as f:
        f.write(new_txt.encode("utf-8"))
    got = io.open(DR, "rb").read()
    P("  [after] %d B CR=%d LF=%d sha=%s" % (len(got), got.count(b"\r"), got.count(b"\n"), sha(got)[:16]))
    need("回读字节 == 预期", got == new_txt.encode("utf-8"))
    need("回读 CR == 0", got.count(b"\r") == 0)
    need("旧内容是新内容的前缀（纯追加）", got.startswith(raw))

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
