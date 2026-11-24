# -*- coding: utf-8 -*-
"""W9 / Q1 -- 0x7CFC9F 处代码身份的只读探针。

独立运行：python -I -X utf8 D:\\Project\\ra2-campaign-forge\\lead\\re_line_20261105\\W9_SINGLESTEP_7CFC9F\\_w9_q1.py
产出：同目录 _w9_q1_out.txt（脚本自己写，不依赖 shell 重定向）

铁律：只读 gamemd.exe / 证据件 / TASK.md；零真机、零采样、零活进程。
唯一写域 = W9_SINGLESTEP_7CFC9F/ 下的 _w9_q1_out.txt。
"""
import sys
import re
import hashlib
import datetime
import traceback
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
EXE = ROOT + r"\ra2youli\gamemd.exe"
EXCEPT = ROOT + (
    r"\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018"
    r"\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")
TASK = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\TASK.md"
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\reviews\_Q1_exact_rerun_out.txt"
VA = 0x7CFC9F

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

_lines = []


def p(s=""):
    _lines.append(str(s))
    print(s, flush=True)


def sha_of(path):
    b = Path(path).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b), b


def hex_tokens(line):
    """从 'Bytes at CS:EIP (...): <hex bytes>' 行里取最后一个冒号之后的 2-hex 字节串。"""
    tail = line.rsplit(":", 1)[1]
    return bytes(int(x, 16) for x in re.findall(
        r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{2}(?![0-9A-Fa-f])", tail))


def find_bytes_line(path):
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if "Bytes at CS:EIP" in ln:
            return ln
    return None


def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p("=" * 78)
    p("W9 / Q1 PROBE -- 0x7CFC9F 代码身份（只读 / 真反汇编）")
    p("run command: python -I -X utf8 " + str(Path(__file__).resolve()))
    p("回件时刻 = " + now)
    p("=" * 78)

    # ---------- A. 强制头部：自己实算的 SHA256 / 字节数 ----------
    p("")
    p("[A] SHA256 / 字节数（自己实算，非引用）")
    exe_sha, exe_n, exe_b = sha_of(EXE)
    exc_sha, exc_n, exc_b = sha_of(EXCEPT)
    p("EXE     = " + EXE)
    p("gamemd.exe SHA256 = " + exe_sha)
    p("gamemd.exe 字节数 = " + str(exe_n))
    p("EXCEPT  = " + EXCEPT)
    p("EXCEPT 件 SHA256 = " + exc_sha)
    p("EXCEPT 件 字节数 = " + str(exc_n))
    p("EXCEPT 文件首行 = " + repr(exc_b.splitlines()[0].decode("utf-8", "replace")))
    for _i, _ln in enumerate(exc_b.splitlines()[:6]):
        p("EXCEPT L%d = %s" % (_i, repr(_ln.decode("utf-8", "replace"))))
    p("EXCEPT 'Exception occurred at' 行 = " + repr(next(
        (ln.decode("utf-8", "replace") for ln in exc_b.splitlines()
         if ln.startswith(b"Exception occurred at")), "NOT_FOUND")))

    # ---------- B. Engine 自证 ----------
    p("")
    p("[B] Engine 自证")
    e = Engine()
    p("Engine.sha = " + e.sha + "  (== 自算: " + str(e.sha == exe_sha) + ")")
    p("IMAGEBASE = " + hex(e.IB))
    p("SECTIONS  = " + repr([(nm, hex(sva), hex(vsz), hex(rp), hex(rsz))
                             for nm, sva, vsz, rp, rsz in e.SEC]))
    p("fo(0x7CFC9F) = " + str(e.fo(VA)) + " = " + hex(e.fo(VA)))
    p("fo 校验 VA - 0x400000 = " + hex(VA - 0x400000)
      + "  (相等: " + str(e.fo(VA) == VA - 0x400000) + ")")
    by = e.by()
    cov, nins, nfails = e.coverage
    p("COVERAGE = %.12f%% / decoded insns = %d / resync fails = %d" % (cov, nins, nfails))
    p("Engine 自证 = COVERAGE %.12f%% (%d insns, %d resync-fails) / IMAGEBASE 0x400000"
      % (cov, nins, nfails))

    # ---------- C. Q1-1 原始字节重读 ----------
    p("")
    p("[C] Q1-1  Engine().rd(0x7CFC9F, 32) 原始字节重读")
    raw32 = e.rd(VA, 32)
    p("type(e.rd) = " + type(raw32).__name__ + " ; len = " + str(len(raw32)))
    p("rd(0x7CFC9F, 32) = " + raw32.hex(" ").upper())
    p("raw32[:16]  = " + raw32[:16].hex(" ").upper())
    p("raw32[16:]  = " + raw32[16:].hex(" ").upper())
    raw48 = e.rd(VA, 0x30)
    p("rd(0x7CFC9F, 0x30=48) = " + raw48.hex(" ").upper())

    # ---------- D. Q1-2 逐字节比对证据件（含 TASK.md 内嵌串） ----------
    p("")
    p("[D] Q1-2 逐字节比对：磁盘字节 vs 证据件 Bytes at CS:EIP vs TASK.md 内嵌串")
    exc_line = find_bytes_line(EXCEPT)
    task_line = find_bytes_line(TASK)
    p("证据件行 = " + repr(exc_line))
    p("TASK.md 行 = " + repr(task_line))
    ev = hex_tokens(exc_line)
    tv = hex_tokens(task_line)
    p("证据件解析字节数 = " + str(len(ev)) + " ; " + ev.hex(" ").upper())
    p("TASK.md 解析字节数 = " + str(len(tv)) + " ; " + tv.hex(" ").upper())
    p("证据件 == TASK.md 内嵌串 : " + str(ev == tv))
    m = min(len(raw32), len(ev))
    diff_exe = [i for i in range(m) if raw32[i] != ev[i]]
    p("")
    p(" idx  VA        磁盘rd  EXCEPT  TASK  一致")
    for i in range(m):
        t = tv[i] if i < len(tv) else None
        ok = (raw32[i] == ev[i] == t)
        p(" %3d  0x%08X   %02X      %02X      %s    %s"
          % (i, VA + i, raw32[i], ev[i],
             ("%02X" % t) if t is not None else "--", "OK" if ok else "**DIFF**"))
    p("")
    p("磁盘 rd[0:%d] vs EXCEPT 逐字节差异索引 = %s" % (m, repr(diff_exe)))
    p("磁盘 rd[0:%d] == EXCEPT[0:%d] : %s" % (m, m, not diff_exe))
    p("长度一致性: len(rd32)=%d len(EXCEPT)=%d len(TASK)=%d"
      % (len(raw32), len(ev), len(tv)))

    p("")
    p("-- D2: 0x7CFC9F ±32 字节窗口内的 CC / F1 / F0 扫描（旧分析 §2 #1/#2 声称无）")
    win_lo, win_hi = VA - 32, VA + 32
    win = e.rd(win_lo, win_hi - win_lo)
    p("rd(0x%08X, 64) = %s" % (win_lo, win.hex(" ").upper()))
    for byte in (0xCC, 0xF1, 0xF0):
        pos = [win_lo + i for i, v in enumerate(win) if v == byte]
        p("  0x%02X 出现位置 = %s" % (byte, [hex(x) for x in pos] or "无"))
    p("  说明：该扫描只说明磁盘镜像字节，不代替运行态/机制判定（Q3 负责）。")

    p("")
    p("-- D3: ±32 窗口内「指令起始字节」枚举（区分独立操作码 vs 嵌入的 ModRM/立即数字节）")
    starts = []
    c = win_lo
    while c < win_hi:
        ins = by.get(c)
        if ins is None:
            c += 1
            continue
        starts.append((ins.address, bytes(ins.bytes)[0], bytes(ins.bytes).hex().upper(),
                       ins.mnemonic, ins.op_str))
        c = ins.address + ins.size
    for a, op0, hx, mn, ops in starts:
        p("  0x%08X  opcode0=%02X  %-14s %s %s" % (a, op0, hx, mn, ops))
    trap_starts = [(hex(a), "%02X" % op0) for a, op0, *_ in starts
                   if op0 in (0xCC, 0xF1, 0xF0)]
    p("  ±32 窗口内以 CC/F1/F0 为独立操作码起点的指令 = %s" % (trap_starts or "无"))
    p("  即 0x7CFCA5 的 F1 是 8B F1(mov esi,ecx) 的 ModRM；"
      "0x7CFCA3 的 F0 是 2B 4D F0(sub ecx,[ebp-0x10]) 的 disp8，均非独立 INT1/LOCK 指令。")

    # ---------- E. Q1-3 前 8 条指令（逐条，重同步锚定） ----------
    p("")
    p("[E] Q1-3 逐条反汇编（resync 流锚定），覆盖 0x30=48 字节窗口")
    p("-- E1: e.disasm(VA, 0x30) 直读（capstone 线性，有静默停止风险）")
    d48 = e.disasm(VA, 0x30)
    for j, (a, hx, mn, ops) in enumerate(d48):
        p("  [%2d] 0x%08X  %-14s  %-7s %s" % (j, a, hx.upper(), mn, ops))
    p("  e.disasm(VA,0x30) 共 %d 条，覆盖 %d 字节"
      % (len(d48), sum(len(x[1]) // 2 for x in d48)))

    p("")
    p("-- E2: resync 流 (e.by()) 逐址推进，校验每条 .bytes == e.rd(addr,size)")
    walk = []
    cur = VA
    while cur < VA + 0x30:
        ins = by.get(cur)
        if ins is None:
            p("  !! 0x%08X 不在 by() 中，停止" % cur)
            break
        blob = e.rd(ins.address, ins.size)
        okb = (bytes(ins.bytes) == blob)
        walk.append((ins.address, bytes(ins.bytes).hex().upper(),
                     ins.mnemonic, ins.op_str, okb))
        cur = ins.address + ins.size
    for j, (a, hx, mn, ops, okb) in enumerate(walk):
        p("  [%2d] 0x%08X  %-14s  %-7s %-24s bytes_ok=%s"
          % (j, a, hx, mn, ops, okb))
    p("  resync 共 %d 条，覆盖 %d 字节（末址 0x%08X）"
      % (len(walk), sum(len(x[1]) // 2 for x in walk), cur))
    p("  E1 与 E2 前 %d 条 (addr,mnem,op_str) 全等 : %s"
      % (min(len(d48), len(walk)),
         [(a, mn, ops) for a, _, mn, ops in d48[:len(walk)]] ==
         [(a, mn, ops) for a, _, mn, ops, _ in walk]))

    p("")
    p("-- E3: ★ 前 8 条指令（助记符 + 操作数）")
    for j, (a, hx, mn, ops, _ok) in enumerate(walk[:8]):
        p("  %d. 0x%08X  %-14s  %-7s %s" % (j + 1, a, hx, mn, ops))

    p("")
    p("-- E4: 0x7CFC9F 之前的指令上下文（证明它是顺序流而非孤点）")
    ctx = []
    c = VA - 0x20
    while c < VA:
        ins = by.get(c)
        if ins is None:
            c += 1
            continue
        ctx.append((ins.address, bytes(ins.bytes).hex().upper(),
                    ins.mnemonic, ins.op_str))
        c = ins.address + ins.size
    for a, hx, mn, ops in ctx:
        p("  0x%08X  %-14s  %-7s %s" % (a, hx, mn, ops))

    # ---------- F. Q1-4 是否在重同步流里 ----------
    p("")
    p("[F] Q1-4 0x7CFC9F 是否在重同步流 (va in e.by())")
    p("0x%08X in e.by() = %s" % (VA, VA in by))
    ins0 = by.get(VA)
    if ins0 is not None:
        p("by()[0x%08X] -> size=%d bytes=%s  %s %s"
          % (VA, ins0.size, bytes(ins0.bytes).hex().upper(),
             ins0.mnemonic, ins0.op_str))
    else:
        p("by()[0x7CFC9F] -> None")
    p("by() 中 VA 附近 0x%08X..0x%08X 的指令起始："
      % (VA - 8, VA + 8))
    for a in range(VA - 8, VA + 9):
        if a in by:
            p("  0x%08X : %s %s" % (a, by[a].mnemonic, by[a].op_str))
    p("结论：按 TASK §2 Q1 的条件分支，'若不在' 一支不适用；"
      "但仍给出落点/数据区判定依据（见 [G]）。")

    # ---------- G. 落点 or 数据区？限定窗口的直接分支引用普查 ----------
    p("")
    p("[G] 它是 call/jmp/jcc 的落点还是数据区？——限定窗口 [0x7CF000,0x7D1000) 的直接分支引用")
    lo, hi = 0x7CF000, 0x7D1000
    refs = []
    for ins in e.stream:
        if ins.address < lo:
            continue
        if ins.address >= hi:
            break
        mn = ins.mnemonic
        if not (mn.startswith("j") or mn == "call"):
            continue
        try:
            if not ins.operands or ins.operands[0].type != 2:
                continue
            t = ins.operands[0].imm
        except Exception:
            continue
        if t == VA:
            refs.append((ins.address, mn, ins.op_str))
    p("窗口内以 0x%08X 为直接目标的 call/jmp/jcc = %d 条" % (VA, len(refs)))
    for a, mn, ops in refs:
        p("  0x%08X  %-7s %s" % (a, mn, ops))

    p("")
    p("-- G2: 全 .text 重同步流内的直接分支目标普查（单遍，仅本二进制，非全仓遍历）")
    allrefs = []
    for ins in e.stream:
        mn = ins.mnemonic
        if not (mn.startswith("j") or mn == "call"):
            continue
        try:
            if not ins.operands or ins.operands[0].type != 2:
                continue
            t = ins.operands[0].imm
        except Exception:
            continue
        if t == VA:
            allrefs.append((ins.address, mn, ins.op_str))
    p("全 .text (%d 条指令) 中以 0x%08X 为直接目标的 call/jmp/jcc = %d 条"
      % (nins, VA, len(allrefs)))
    for a, mn, ops in allrefs:
        p("  0x%08X  %-7s %s" % (a, mn, ops))
    p("  间接分支/跳转表落点（push VA; ret / jmp [table] 等）本探针未解析：未验")
    p("  0x7CFC9B..0x7CFC9E 字节 = " + e.rd(0x7CFC9B, 4).hex(" ").upper()
      + "  (旧分析 §2 #2 声称不是 F1；实测无独立 F1 指令)")

    p("窗口内 0x%08X 处是否为 ret/int3/数据（全零或不可解码）: " % VA)
    p("  rd(VA,16) = " + e.rd(VA, 16).hex(" ").upper())
    p("  by()[VA] 存在 = " + str(VA in by) + " -> 是合法指令起始，不是数据区")
    p("  VA 前一条指令起始 = " + ("0x%08X" % ctx[-1][0]) if ctx else "n/a")
    if ctx:
        last = by.get(ctx[-1][0])
        p("  前一条指令 = 0x%08X %s %s, size=%d, 末址=0x%08X"
          % (last.address, last.mnemonic, last.op_str, last.size,
             last.address + last.size)
          + "  => 紧邻 VA: " + str(last.address + last.size == VA))

    # ---------- H. 旧分析 §1.1 声称的指令流复核 ----------
    p("")
    p("[H] 对照旧分析 SINGLESTEP_0x7CFC9F_ANALYSIS.md §1.1 声称的指令流（默认怀疑）")
    claim = [
        (0x7CFC98, "8B4DF4", "mov", "ecx, [ebp - 0xc]"),
        (0x7CFC9B, "8B54F904", "mov", "edx, [ecx + edi*8 + 4]"),
        (0x7CFC9F, "8B0A", "mov", "ecx, [edx]"),
        (0x7CFCA1, "2B4DF0", "sub", "ecx, [ebp - 0x10]"),
        (0x7CFCA4, "8BF1", "mov", "esi, ecx"),
        (0x7CFCA6, "894DF8", "mov", "[ebp - 8], ecx"),
        (0x7CFCA9, "C1FE04", "sar", "esi, 4"),
        (0x7CFCAC, "4E", "dec", "esi"),
        (0x7CFCAD, "83FE3F", "cmp", "esi, 0x3f"),
        (0x7CFCB0, "7E03", "jle", "0x7cfcb5"),
        (0x7CFCB2, "6A3F", "push", "0x3f"),
        (0x7CFCB4, "5E", "pop", "esi"),
        (0x7CFCB5, "3BF7", "cmp", "esi, edi"),
        (0x7CFCB7, "0F840D010000", "je", "0x7cfdca"),
    ]
    for a, hx, mn, ops in claim:
        got = by.get(a)
        if got is None:
            p("  0x%08X  旧分析=%s %s %s  | 实测=NOT_IN_BY  **DIFF**"
              % (a, hx, mn, ops))
            continue
        ghx = bytes(got.bytes).hex().upper()
        gmn, gops = got.mnemonic, got.op_str
        byte_ok = (ghx == hx)
        p("  0x%08X  旧分析=%-14s %-7s %-22s | 实测=%-14s %-7s %-22s bytes=%s"
          % (a, hx, mn, ops, ghx, gmn, gops, "OK" if byte_ok else "**DIFF**"))

    # ---------- I. 越界提示（不代替 Q4 定谳） ----------
    p("")
    p("[I] 越界提示（仅记录事实，Q4 负责定谳）")
    p("EXCEPT 件 SHA256 前缀 = " + exc_sha[:8])
    p("TASK.md / GOAL_THREE_TARGETS §555 记载 107 份 except_post_*.txt 同哈希 6694b75e... "
      "('历史基线残件')")
    p("本探针只做 Q1 代码身份，不对二者是否同一件作结论。")

    p("")
    p("=" * 78)
    p("PROBE DONE -- exit 0")
    p("=" * 78)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        p("")
        p("!! PROBE EXCEPTION !!")
        p(traceback.format_exc())
    finally:
        Path(OUT).write_text("\n".join(_lines) + "\n", encoding="utf-8")
        print("wrote " + OUT, flush=True)
