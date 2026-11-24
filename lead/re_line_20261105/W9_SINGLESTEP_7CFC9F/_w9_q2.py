# -*- coding: utf-8 -*-
"""W9 / Q2 定谳探针 —— 0x7CFC9F 属于哪个函数（只读、独立跑完即退出）。

用法（在仓库根，stdout 由 shell 重定向到 _w9_q2_out.txt）：
  python -I -X utf8 lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q2.py

铁律：零真机、零采样注入、零活进程读取、只读磁盘 + ra2tool.Engine 反汇编。
Engine 口径：e.raw 是 bytes；读字节用 e.rd(va,n)；查指令起始用 va in e.by()。
"""
import sys
import os
import time
import hashlib
import datetime
import subprocess

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXC = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                   "lead", "boot_hang_triage_20261018",
                   "EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")


def P(*a):
    print(" ".join(str(x) for x in a), flush=True)


def hx(b):
    return b.hex(" ").upper()


t0 = time.time()

# ---------------------------------------------------------------- 强制头部自证
raw_exe = open(EXE, "rb").read()
raw_exc = open(EXC, "rb").read()
P("=" * 78)
P("[HEADER] 回件时刻 =", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
P("[HEADER] gamemd.exe SHA256 =", hashlib.sha256(raw_exe).hexdigest(),
  "字节数 =", len(raw_exe))
P("[HEADER] EXCEPT 件 SHA256 =", hashlib.sha256(raw_exc).hexdigest(),
  "字节数 =", len(raw_exc))

e = Engine()
cov, nins, resync = e.coverage          # 构建重同步流（by/func_rets 前置）
by = e.by()
P("[HEADER] Engine 自证 = COVERAGE %.4f%% (%d insns / resync_fails=%d) / IMAGEBASE 0x%X"
  % (cov, nins, resync, e.IB))
P("[HEADER] .text = 0x%X .. 0x%X (TSZ=0x%X)" % (e.TLO, e.THI, e.TSZ))
P("[HEADER] Engine.sha =", e.sha, "| 与目标镜像一致 =",
  e.sha == hashlib.sha256(raw_exe).hexdigest())
P("=" * 78)

TARGET = 0x7CFC9F
P("[Q2-0] 目标 EIP = 0x%X" % TARGET)
P("[Q2-0] 0x%X in e.by() = %s  (指令起始 := 重同步流内)" % (TARGET, TARGET in by))
P("[Q2-0] e.rd(0x%X, 32) = %s" % (TARGET, hx(e.rd(TARGET, 32))))

# ------------------------------------------------- Q2-(1) 向上回溯最近函数序言
P("")
P("=" * 78)
P("### Q2-(1) 向上回溯最近的函数序言")
P("=" * 78)

# 序言签名：push ebp; mov ebp,esp [; sub esp,imm8]  /  或 sub esp,imm 且前方 ret/int3 对齐
PROS = [
    (b"\x55\x8B\xEC\x83\xEC", "push ebp; mov ebp,esp; sub esp,imm8"),
    (b"\x55\x8B\xEC", "push ebp; mov ebp,esp"),
]
WIN_LO = 0x7CF000          # 向上 0xC9F 字节窗口（不扫全盘）
cands = []
for va in range(TARGET, WIN_LO - 1, -1):
    if va not in by:
        continue
    b5 = e.rd(va, 5)
    for sig, desc in PROS:
        if b5[:len(sig)] == sig:
            cands.append((va, desc, hx(e.rd(va, 8))))
            break
P("[回溯] 窗口 [0x%X,0x%X] 内全部 55 8B EC[83 EC] 序言候选（近→远）：" % (WIN_LO, TARGET))
for va, desc, b8 in cands:
    P("    0x%08X  %-22s  bytes=%s  Δ=0x%X" % (va, desc, b8, TARGET - va))
if not cands:
    P("[回溯] 未验：窗口内 0 命中")
    HEAD = None
else:
    HEAD = cands[0][0]
    P("[回溯] 最近序言 HEAD = 0x%X (Δ=+0x%X)" % (HEAD, TARGET - HEAD))

# 序言前方对齐验证：紧邻的前一字节应为 ret(C3/C2)/int3(CC)/leave(C9) 系列
if HEAD is not None:
    prev = e.rd(HEAD - 6, 6)
    P("[回溯] 序言前 6 字节 e.rd(0x%X,6) = %s" % (HEAD - 6, hx(prev)))
    P("[回溯] 紧邻前 1 字节 = %s  → %s" %
      (hx(e.rd(HEAD - 1, 1)),
       "ret(C3/C2)/int3(CC)/leave(C9) 对齐" if e.rd(HEAD - 1, 1)[0] in (0xC3, 0xC2, 0xCC, 0xC9)
       else "非 ret/int3（需注记）"))
    P("[回溯] 前一函数尾声 in by():",
      [(hex(a), by[a].mnemonic, by[a].op_str)
       for a in range(HEAD - 6, HEAD) if a in by])
    # 序言逐条反汇编（用 e.disasm，已确认在流内）
    P("[回溯] 序言逐条 e.disasm(0x%X, 0x10):" % HEAD)
    for a, b, m, o in e.disasm(HEAD, 0x10):
        P("    0x%08X  %-14s  %s %s" % (a, b.upper(), m, o))

# --------------------------------- Q2-(2) 函数起止 VA / 长度 / ret 数
P("")
P("=" * 78)
P("### Q2-(2) 函数起止 VA、长度、函数内 ret 数（e.func_rets）")
P("=" * 78)

if HEAD is None:
    P("[边界] 未验：无 HEAD，无法定界")
else:
    # 前向扫描：找本函数的 ret；并检查 ret 之后下一个函数起点
    ret_addrs = [a for a in sorted(by) if HEAD <= a < HEAD + 0x600
                 and by[a].mnemonic.startswith("ret")]
    P("[边界] 前向 0x600 窗口内全部 ret 指令起始：",
      [(hex(a), by[a].mnemonic, by[a].op_str) for a in ret_addrs])
    TAIL = ret_addrs[0] if ret_addrs else None
    if TAIL is None:
        P("[边界] 未验：窗口内无 ret")
    else:
        END = TAIL + by[TAIL].size          # ret 指令结束后的下一字节
        P("[边界] 函数起 START = 0x%X" % HEAD)
        P("[边界] 唯一/首个 ret @ 0x%X (%s %s, size=%d)" %
          (TAIL, by[TAIL].mnemonic, by[TAIL].op_str, by[TAIL].size))
        P("[边界] 函数止 END(不含) = 0x%X；含 ret 末字节 = 0x%X" % (END, END - 1))
        P("[边界] 长度（不含 ret 字节）= 0x%X = %d B" % (TAIL - HEAD, TAIL - HEAD))
        P("[边界] 长度（含 ret 1B）  = 0x%X = %d B" % (END - HEAD, END - HEAD))
        P("[边界] 0x%X 相对函数头 = +0x%X (+%d B)" % (TARGET, TARGET - HEAD, TARGET - HEAD))

        # 指令数
        ins_in = [a for a in by if HEAD <= a < END]
        P("[边界] 函数体指令数（by() 内 [START,END)）= %d" % len(ins_in))

        # ★ 任务书点名：e.func_rets
        rets, succ = e.func_rets(HEAD, END)
        P("[边界] e.func_rets(0x%X, 0x%X) → ret 数 = %d" % (HEAD, END, len(rets)))
        for r in rets:
            P("        ret @ 0x%08X  %s %s  bytes=%s" %
              (r.address, r.mnemonic, r.op_str, hx(e.rd(r.address, r.size))))
        # 交叉：更宽窗口，证明 END 之后才是下一处 ret
        rets_wide, _ = e.func_rets(HEAD, HEAD + 0x600)
        P("[边界] 交叉 e.func_rets(0x%X, 0x%X) → ret 数 = %d，地址 = %s" %
          (HEAD, HEAD + 0x600, len(rets_wide),
           [hex(r.address) for r in rets_wide]))

        # 下一函数起点：END 处的字节 + 该地址是否在 by()
        P("[边界] 下一函数起点候选 0x%X: in by()=%s, e.rd(...,8)=%s" %
          (END, END in by, hx(e.rd(END, 8))))
        if END in by:
            P("        0x%08X  %s" % (END, "%s %s" % (by[END].mnemonic, by[END].op_str)))
        P("[边界] 尾声 in by() [0x%X,0x%X]:" % (TAIL - 0xA, END))
        for a in sorted(a for a in by if TAIL - 0xA <= a < END):
            P("        0x%08X  %-14s  %s %s" %
              (a, hx(e.rd(a, by[a].size)), by[a].mnemonic, by[a].op_str))

# --------------------------------- Q2-(3) 既有分析覆盖：多口径搜索
P("")
P("=" * 78)
P("### Q2-(3) 既有分析覆盖情况 —— lead/ 与 docs/re/ 多口径搜索")
P("=" * 78)

SEARCH_DIRS = ["lead", "docs/re"]
SPELLS = [
    ("A", "7CFC9F", ["-r", "-I", "-i", "-l"]),          # 裸 VA，大小写不敏感
    ("B", "0x7CFC9F", ["-r", "-I", "-i", "-l"]),        # 0x 前缀
    ("C", "7cfc9f", ["-r", "-I", "-l"]),                # 全小写，大小写敏感
    ("D", "7CFC9F", ["-r", "-I", "-l"]),                # 全大写，大小写敏感
    ("E", "007CFC9F", ["-r", "-I", "-i", "-l"]),        # EIP 8 位写法
]
EXTRA = [
    ("F-HEAD", "7CFB13", ["-r", "-I", "-i", "-l"]),       # 函数起 VA
    ("F-HEAD0x", "0x7CFB13", ["-r", "-I", "-i", "-l"]),
    ("F-TAIL", "7CFE1B", ["-r", "-I", "-i", "-l"]),       # 函数止 VA
    ("F-NAME", "sbh_alloc_block", ["-r", "-I", "-i", "-l"]),
    ("F-WIN", "7CFC9B", ["-r", "-I", "-i", "-l"]),        # crashspec PW-1 窗
]


def run_grep(pattern, flags, dirs, extra=None):
    cmd = ["grep"] + flags + ([extra] if extra else []) + ["-e", pattern] + dirs
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    files = sorted(set(x.strip().replace("\\", "/") for x in r.stdout.splitlines() if x.strip()))
    return cmd, files, r.returncode


P("[搜索] cwd =", ROOT, "| dirs =", SEARCH_DIRS)
P("[搜索] 口径 A–E = 任务书点名的「至少两种写法」(7CFC9F / 0x7CFC9F / 7cfc9f)，另补 D/E")
P("")
for tag, pat, flags in SPELLS + EXTRA:
    cmd, files, rc = run_grep(pat, flags, SEARCH_DIRS)
    P("[%s] pattern=%-16s cmd=%s" % (tag, pat, " ".join(cmd)))
    P("      → 命中文件数 = %d (grep rc=%d)" % (len(files), rc))
    for f in files[:14]:
        P("        %s" % f)
    if len(files) > 14:
        P("        ... 其余 %d 个略" % (len(files) - 14))

# 排除 W9 本轮自身产物 + .mimosa hook 缓存 → 真正的「既有分析」净数
P("")
P("[搜索-净数] 排除本轮 W9_SINGLESTEP_7CFC9F/ 自产物与 .mimosa hook 缓存后的既有命中：")
for tag, pat, flags in [("A", "7CFC9F", ["-r", "-I", "-i", "-l"]),
                        ("F-HEAD", "7CFB13", ["-r", "-I", "-i", "-l"]),
                        ("F-NAME", "sbh_alloc_block", ["-r", "-I", "-i", "-l"])]:
    cmd, files, rc = run_grep(pat, flags, SEARCH_DIRS,
                              extra="--exclude-dir=W9_SINGLESTEP_7CFC9F")
    net = [f for f in files if ".mimosa" not in f]
    P("[%s] %s → 原始=%d，排除 W9 自产物后=%d，再排除 .mimosa 后=%d"
      % (tag, pat, len(files), len([f for f in files if "W9_SINGLESTEP_7CFC9F" not in f]), len(net)))
    P("      docs/re 净命中：", [f for f in net if f.startswith("docs/re/")])
    P("      lead 净命中：", [f for f in net if f.startswith("lead/")])

# 额外：真正 crashspec 语料（在 out/re_work/，不属任务书两个搜索目录，但 Q2 问「crashspec 工作范围」）
P("")
P("[搜索-crashspec] 任务书问「既有的 crashspec 工作范围」；该语料实际在 out/re_work/ 下：")
CS = ["out/re_work/work_chain/CONTINUE_20261003/crashspec",
      "out/re_work/work_chain/CONTINUE_20261003/crashspec_v3",
      "out/re_work/work_chain/CONTINUE_20261003/crashspec_v4"]
for pat in ("7CFC9F", "7CFB13", "sbh_alloc_block"):
    cmd, files, rc = run_grep(pat, ["-r", "-I", "-i", "-l"], CS)
    P("  pattern=%-16s → 命中文件 %d 个: %s" % (pat, len(files), [f for f in files]))

P("")
P("=" * 78)
P("[DONE] elapsed = %.2f s" % (time.time() - t0))
P("=" * 78)
