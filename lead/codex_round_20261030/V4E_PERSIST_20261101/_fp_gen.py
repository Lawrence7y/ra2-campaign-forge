# -*- coding: utf-8 -*-
"""V4E_PERSIST fingerprints 生成器 v2（纯只读；stdout 由 Bash 重定向落盘 fingerprints.txt）。

流式纪律：文件按 64KB 块读入 I/O 缓冲、逐字节喂给状态机消费，任何时刻内存中至多一块；
绝不整文件载入。计数逻辑为逐字节状态机（含括号深度/子串匹配阶段），不依赖块对齐，
无跨界 token 缺陷（v1 的 core/tail 切分法已废弃——其对跨块边界 token 会丢前缀漏计）。

登记项（任务书产出 2 之 3）：
  A. 两个分析脚本（sha256+行数）
  A2. 等待轨迹分解输出件（原件 v4b/v4c 版 + v4d 内联复算 tee）
  B. XVERIFY_A p01 两个输出（sha256+行数）
  C. l3_1101v4b/v4c/v4d 三趟 h8_wait_trace.json（sha256+元数据 n+实测样本数+首末样本）
  D. v4-d 三窗 measure JSON（sha256+len(samples.t)+len(samples.f)）
说明：任务点名的 _h8_waittrace_decomp_v4d.py 已不存在（§508：v4-d 复算改最短内联参数化，
副本件已删）；以原件 _h8_waittrace_decomp.py + 输出 waittrace_decomp_v4d_20261101.txt 登记。
"""
import hashlib
import io
import os
import re
import sys

CH = 1 << 16
ROOT = r"D:\Project\ra2-campaign-forge"
TRIP = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                    "lead", "qc161_u0400_trip")
LB = os.path.join(ROOT, "lead", "codex_round_20261030", "LEADER_battle")
XA = os.path.join(ROOT, "lead", "codex_round_20261030", "XVERIFY_A_20261101")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def stream_hash_lines(path):
    """sha256（流式）+ 行数（\\n 计数，末尾无换行补 1）+ 字节数。"""
    h = hashlib.sha256()
    nl = 0
    size = 0
    last = b""
    with open(path, "rb") as f:
        while True:
            b = f.read(CH)
            if not b:
                break
            h.update(b)
            nl += b.count(b"\n")
            size += len(b)
            last = b
    if size and not last.endswith(b"\n"):
        nl += 1
    return h.hexdigest(), nl, size


def waittrace_stream(path):
    """h8_wait_trace.json 逐字节状态机：元数据 n、实测样本数、首末样本、sha256。

    结构：{"n":N,...,"samples":[[t,f],[t,f],...]}。样本数= samples 顶层数组的顶层逗号数+1。
    阶段：0=找 '"samples"' 子串 → 1=找下一个 '[' → 2=数组内（depth 计数，depth==1 的
    逗号=顶层逗号）。数字数组内无字符串字面量，']' '[' 可靠。
    """
    h = hashlib.sha256()
    size = 0
    n_meta = None
    state = 0
    pat = b'"samples"'
    pat_i = 0
    depth = 0
    top_commas = 0
    first = last = b"?"
    with open(path, "rb") as f:
        head = f.read(400)
        m = re.search(rb'"n"\s*:\s*(\d+)', head)
        if m:
            n_meta = int(m.group(1))
        f.seek(0)
        done = False
        while not done:
            b = f.read(CH)
            if not b:
                break
            h.update(b)
            size += len(b)
            for c in b:
                if state == 0:
                    if c == pat[pat_i]:
                        pat_i += 1
                        if pat_i == len(pat):
                            state = 1
                    else:
                        pat_i = 1 if c == pat[0] else 0
                elif state == 1:
                    if c == 0x5B:            # '['
                        state = 2
                        depth = 1
                elif state == 2:
                    if c == 0x5B:            # '['
                        depth += 1
                    elif c == 0x5D:          # ']'
                        depth -= 1
                        if depth == 0:
                            done = True
                            break
                    elif c == 0x2C and depth == 1:   # ',' 顶层
                        top_commas += 1
    total = top_commas + 1 if done else 0
    with open(path, "rb") as f:
        h4 = f.read(400)
        m = re.search(rb'"samples"\s*:\s*\[\s*(\[[^\]]*\])', h4)
        if m:
            first = m.group(1)
    with open(path, "rb") as f:
        f.seek(max(0, size - 300), 0)
        t4 = f.read()
        mm = re.findall(rb"\[[^\[\]]*\]", t4)
        if mm:
            last = mm[-1]
    return n_meta, total, first.decode("utf-8", "replace"), last.decode("utf-8", "replace"), h.hexdigest(), size


def measure_stream(path):
    """measure_w*.json 逐字节状态机：len(samples.t)、len(samples.f)、sha256。

    结构：..."samples":{"t":[数字...],"f":[数字...]},... 数字数组内无嵌套/无字符串。
    阶段：0=找 '"samples"' → 1=找 '"t"' → 2=t 数组（数逗号，']' 收口 nt）→
    3=找 '"f"' → 4=f 数组（数逗号，']' 收口 nf）→ 完成返回。
    """
    h = hashlib.sha256()
    size = 0
    state = 0
    key_t = b'"t"'
    key_f = b'"f"'
    key_samples = b'"samples"'
    ki = 0
    commas = 0
    nt = nf = None
    with open(path, "rb") as f:
        while True:
            b = f.read(CH)
            if not b:
                break
            h.update(b)
            size += len(b)
            for c in b:
                if state == 0:
                    if c == key_samples[ki]:
                        ki += 1
                        if ki == len(key_samples):
                            state = 1
                            ki = 0
                    else:
                        ki = ki + 1 if ki and c == key_samples[ki] else (1 if c == key_samples[0] else 0)
                elif state == 1:
                    if c == key_t[ki]:
                        ki += 1
                        if ki == len(key_t):
                            state = 2
                            ki = 0
                            commas = 0
                    else:
                        ki = ki + 1 if ki and c == key_t[ki] else (1 if c == key_t[0] else 0)
                elif state == 2:
                    # 等 '[' 进入数组
                    if c == 0x5B:
                        state = 3
                    elif c == 0x7D:          # '}' 防御：samples 内未遇 t 数组（不应发生）
                        state = 0
                        ki = 0
                elif state == 3:
                    if c == 0x2C:
                        commas += 1
                    elif c == 0x5D:
                        nt = commas + 1
                        state = 4
                        ki = 0
                        commas = 0
                elif state == 4:
                    if c == key_f[ki]:
                        ki += 1
                        if ki == len(key_f):
                            state = 5
                            ki = 0
                            commas = 0
                    else:
                        ki = ki + 1 if ki and c == key_f[ki] else (1 if c == key_f[0] else 0)
                elif state == 5:
                    if c == 0x5B:
                        state = 6
                elif state == 6:
                    if c == 0x2C:
                        commas += 1
                    elif c == 0x5D:
                        nf = commas + 1
                        state = 7
                if state == 7:
                    break
            if state == 7:
                break
    return nt, nf, h.hexdigest(), size


def main():
    P = lambda s: print(s)
    P("# V4E_PERSIST fingerprints —— 2026-11-01")
    P("# 生成器：_fp_gen.py v2（本目录）；命令：python -I -X utf8 _fp_gen.py > fingerprints.txt")
    P("# 流式纪律：64KB 块 I/O + 逐字节状态机计数，不整文件载入内存（v1 块对齐 token 法已废弃：")
    P("#   对跨块边界的 '], [' 会丢前缀漏计，v4c/v4d 各漏 1-2 个，v2 逐字节法无此缺陷）。")
    P("# 登记说明：任务点名的 _h8_waittrace_decomp_v4d.py 现场不存在（§508：v4-d 复算改")
    P("#   最短内联参数化、副本件已删），以原件 _h8_waittrace_decomp.py + 输出件")
    P("#   waittrace_decomp_v4d_20261101.txt 登记替代；详见 ANALYSIS_AUDIT_20261101.md §1。")
    P("")
    P("== A. 分析脚本（sha256  行数  字节  路径）")
    for p in [os.path.join(LB, "_h8_waittrace_decomp.py"),
              os.path.join(XA, "_xva_p01_stall.py")]:
        h, nl, sz = stream_hash_lines(p)
        P("%s  lines=%-5d bytes=%-7d %s" % (h, nl, sz, p))
    P("")
    P("== A2. 等待轨迹分解输出件（原版 v4b/v4c 与 v4d 内联复算 tee）")
    for p in [os.path.join(LB, "waittrace_decomp_20261101.txt"),
              os.path.join(LB, "waittrace_decomp_v4d_20261101.txt")]:
        h, nl, sz = stream_hash_lines(p)
        P("%s  lines=%-5d bytes=%-7d %s" % (h, nl, sz, p))
    P("")
    P("== B. XVERIFY_A p01 两个输出（sha256  行数  字节  路径）")
    for p in [os.path.join(XA, "_xva_p01_out.txt"),
              os.path.join(XA, "_xva_p01_out.json")]:
        h, nl, sz = stream_hash_lines(p)
        P("%s  lines=%-5d bytes=%-7d %s" % (h, nl, sz, p))
    P("")
    P("== C. 等待轨迹三件套 h8_wait_trace.json（sha256  元数据n  实测样本数  首样本  末样本）")
    for trip in ["l3_1101v4b", "l3_1101v4c", "l3_1101v4d"]:
        p = os.path.join(TRIP, trip, "h8_wait_trace.json")
        n_meta, total, first, last, h, sz = waittrace_stream(p)
        P("%s  bytes=%-7d %s" % (h, sz, p))
        P("   元数据n=%s 实测样本数=%d 首样本=%s 末样本=%s" % (n_meta, total, first, last))
    P("")
    P("== D. v4-d 三窗 measure JSON（sha256  bytes  len(samples.t)  len(samples.f)）")
    for w in [0, 1, 2]:
        p = os.path.join(TRIP, "l3_1101v4d", "measure_w%d.json" % w)
        nt, nf, h, sz = measure_stream(p)
        P("%s  bytes=%-7d %s" % (h, sz, p))
        P("   len(samples.t)=%s len(samples.f)=%s" % (nt, nf))
    P("")
    P("== 交叉核对锚（文献值，供抽验）")
    P("# v4b 实测样本数应=9989（§501/§507 poll_count）；v4c=24712（§507 复核注）；v4d=17030（V4D_RECOMPUTE W4）。")
    P("# v4d 三窗样本数应各=12501（V4D_RECOMPUTE M7）。")


if __name__ == "__main__":
    main()
