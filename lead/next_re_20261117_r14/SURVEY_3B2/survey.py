# -*- coding: utf-8 -*-
"""
SURVEY-3B2-GLOBAL — 全表 ③b② 可达性普查（只读普查，只写 SURVEY_3B2 目录）

卡片: lead/next_re_20261117_r14/_cards/SURVEY-3B2-GLOBAL.md

测量定义（与 COVERAGE/PANEL_CHK 口径逐条对齐）:
  n             = 该子系统且 entry 在 atlas 内的 coverage 行数（atlas entry 小写十六进制，
                  比对一律 %08X 大写归一）
  named_L       = 上述行中 name 非空且不以 'sub_' 开头
  named_S14     = named_L 再排除名字匹配 ::sub_[0-9A-Fa-f]+$（named_S(R14)，DoD 判定列）
  proved        = 上述行中 grade == [已证]
  proved_strict = proved 中语义栏不含裸子串「未证」（D-44 卡片口径，与 PANEL 现值同源）
  pool          = 上述行中 grade != [已证]（[未证] + [静态推断]）

p3b2（③b② 机械形态命中，可辩护候选，不是"已证实"）——对池中每个 entry 用
capstone 5.0.7 (skipdata=True) 按 atlas size 反汇编函数体，判定是否满足全部:
  (1) 函数体内存在 call，其后紧邻（允许 1–2 条无关指令内，即 +1..+3）出现
      test eax,eax / cmp eax,<imm> / or eax,eax
      —— 窗口内的指令必须可辩护地"无关"：可解码、非控制转移、不覆写 eax；
      遇 skipdata 垃圾字节/控制转移/写 eax 即断链；
  (2) 该比较后紧跟条件跳转（jcc 在比较后 +1..+2）；
      —— 比较==**陷阱**==：比较与跳转之间 eax 被覆写（mov eax,[…] 之类）或出现
      不可解码字节/控制转移的，不算（上一轮把 13 行打到 9 行的陷阱）；
  (3) 该跳转的失败路径与成功路径动作签名不同（直接 call 目标集 / 返回常量集 /
      是否 ret / 末端 eax 常量；同一处 call 只差参数 => 签名相同 => 不算）。

p3b2_named = p3b2 命中行中 name 非空且不匹配 ^(sub_|.*::sub_) 的数量。

派生: best_proved = proved + p3b2（上界，不是预测）；gap_now = ceil(0.5n) − proved；
      can_close = best_proved >= ceil(0.5n)；named_ok = named_S14 >= ceil(0.9n)；
      verdict ∈ {proved 可闭且 named 已够 / proved 可闭但 named 不够 / proved 不可闭}

输出（全部写入本目录）:
  survey.tsv        22 行数据（不含 TOTAL）
  base_rate.tsv     subsystem/population/pool/p3b2/rate + TOTAL 行
  hits_detail.tsv   每行池 entry 的命中明细（审计用）
  控制台摘要 + 与 COVERAGE/PANEL_CHK/recalc_all.tsv 的逐格核对（只读对照）
"""
import csv
import hashlib
import math
import os
import re
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import (
    X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_INS_TEST, X86_INS_OR, X86_INS_CMP,
    X86_INS_MOV, X86_INS_XOR, X86_INS_SUB, X86_INS_AND, X86_INS_XCHG,
    X86_OP_REG, X86_OP_IMM, X86_REG_EAX,
)

# ---------------------------------------------------------------- paths
BASE = os.path.dirname(os.path.abspath(__file__))            # ...\SURVEY_3B2
R14 = os.path.dirname(BASE)                                  # ...\next_re_20261117_r14
ROOT = os.path.dirname(os.path.dirname(R14))                 # 项目根
COVERAGE_TSV = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS_TSV = os.path.join(os.path.dirname(R14), "next_re_20261112_r10",
                         "W130_atlas", "function_atlas.tsv")
RECALC_TSV = os.path.join(R14, "COVERAGE", "PANEL_CHK", "recalc_all.tsv")
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXE_SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

SUBS = ["S%02d" % i for i in range(1, 23)]

# ---------------------------------------------------------------- helpers
def norm_entry(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    return e


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


# capstone 5.0.7 全部条件跳转常量（X86_INS_J*，排除 JMP）
JCC_IDS = set()
for _n in dir(cx86):
    if _n.startswith("X86_INS_J") and _n != "X86_INS_JMP":
        _v = getattr(cx86, _n)
        if isinstance(_v, int):
            JCC_IDS.add(_v)
CONTROL_IDS = ({X86_INS_JMP, X86_INS_RET, X86_INS_CALL,
                cx86.X86_INS_LOOP, cx86.X86_INS_LOOPE, cx86.X86_INS_LOOPNE}
               | JCC_IDS)

# eax 保值恒等式（两操作数均为 eax 时不覆写 call 返回值）
EAX_IDEMPOTENT = {X86_INS_OR, X86_INS_AND, X86_INS_MOV, X86_INS_XCHG, X86_INS_TEST}


def is_eax(op):
    return op.type == X86_OP_REG and op.reg == X86_REG_EAX


def writes_eax(ins):
    """该指令是否可能覆写 eax（skipdata/未知形态一律按覆写处理，保守）。"""
    if ins.id == X86_INS_CALL:
        return True  # 返回值即新 eax
    try:
        _, wr = ins.regs_access()
    except Exception:
        return True
    if X86_REG_EAX in wr:
        if (ins.id in EAX_IDEMPOTENT and len(ins.operands) == 2
                and is_eax(ins.operands[0]) and is_eax(ins.operands[1])):
            return False  # or/and/mov/xchg/test eax,eax —— 值不变
        return True
    return False


def test_kind(ins):
    """③b② 指定的三种比较形态。"""
    if (ins.id == X86_INS_TEST and len(ins.operands) == 2
            and is_eax(ins.operands[0]) and is_eax(ins.operands[1])):
        return ("TEST_EAX", 0)
    if (ins.id == X86_INS_OR and len(ins.operands) == 2
            and is_eax(ins.operands[0]) and is_eax(ins.operands[1])):
        return ("OR_EAX", 0)
    if (ins.id == X86_INS_CMP and len(ins.operands) == 2
            and is_eax(ins.operands[0]) and ins.operands[1].type == X86_OP_IMM):
        return ("CMP_IMM", ins.operands[1].imm & 0xFFFFFFFF)
    return None


def path_sig(insns, start_idx, maxn=16):
    """路径动作签名（沿用 S15S16_3B2 已过审实现）:
    直接 call 目标集 / ret 前 eax 常量集 / 是否 ret / 末端 eax 常量。"""
    calls, rets = set(), set()
    has_ret = False
    eax = None
    end_eax = None
    for j in range(start_idx, min(start_idx + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0:
            continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif (ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2
                and is_eax(ins.operands[0]) and is_eax(ins.operands[1])):
            eax = 0
        elif (ins.id == X86_INS_MOV and len(ins.operands) == 2
                and is_eax(ins.operands[0])):
            eax = ((ins.operands[1].imm & 0xFFFFFFFF)
                   if ins.operands[1].type == X86_OP_IMM else None)
        elif ins.id == X86_INS_RET:
            has_ret = True
            if eax is not None:
                rets.add(eax)
            end_eax = eax
            break
        elif ins.id == X86_INS_JMP:
            end_eax = eax
            break
        else:
            end_eax = eax
    return {"calls": sorted(calls), "rets": sorted(rets),
            "has_ret": has_ret, "end_eax": end_eax}


SIG_KEYS = ("calls", "rets", "has_ret", "end_eax")
OUT_OF_BODY_SIG = {"calls": [], "rets": [], "has_ret": False, "end_eax": "OUT_OF_BODY"}

# ---------------------------------------------------------------- 1. 输入自校验
print("[1] 输入自校验", flush=True)
exe_hash = sha256(EXE)
print("    gamemd.exe SHA-256 = %s  %s" % (
    exe_hash, "OK" if exe_hash == EXE_SHA256 else "MISMATCH(期望 %s)" % EXE_SHA256))

# atlas（entry 小写十六进制 -> size/n_instr）
atlas = {}
with open(ATLAS_TSV, encoding="utf-8") as f:
    lines = f.read().splitlines()
for ln in lines[1:]:  # 首行为逗号表头
    if not ln.strip():
        continue
    p = ln.split("\t")
    if len(p) < 3:
        continue
    try:
        atlas[norm_entry(p[0])] = (int(p[1]), int(p[2]))
    except ValueError:
        pass
print("    atlas 行: %d（唯一 entry %d）" % (len(lines) - 1, len(atlas)))

# coverage（首行逗号表头，数据行 8 列行内制表符）
coverage = []
with open(COVERAGE_TSV, encoding="utf-8") as f:
    lines = f.read().splitlines()
malformed = 0
for ln in lines[1:]:
    p = ln.split("\t")
    if len(p) < 8:
        malformed += 1
        continue
    coverage.append({"entry": norm_entry(p[0]), "subsystem": p[1], "name": p[2],
                     "semantics": p[3], "grade": p[4]})
print("    coverage 数据行: %d（畸形 %d）" % (len(coverage), malformed))

# ---------------------------------------------------------------- 2. 面板口径统计
print("[2] 面板口径统计（n/named_L/named_S14/named_strict/proved/proved_strict）", flush=True)
st = {s: dict(total=0, n=0, named_L=0, named_S14=0, named_strict=0,
              proved=0, proved_strict=0, pool=0, pool_unproven=0, pool_static=0)
      for s in SUBS}
pool_rows = []
for r in coverage:
    s = r["subsystem"]
    if s not in st:
        print("    !! 未知 subsystem: %r" % s)
        continue
    st[s]["total"] += 1
    if r["entry"] not in atlas:
        continue
    st[s]["n"] += 1
    name = r["name"]
    named_L = bool(name) and not name.startswith("sub_")
    named_S14 = named_L and not re.search(r"::sub_[0-9A-Fa-f]+$", name)
    named_strict = named_S14 and not re.search(r"::v?slot\d+$", name)
    proved = r["grade"] == "[已证]"
    proved_strict = proved and ("未证" not in r["semantics"])
    st[s]["named_L"] += named_L
    st[s]["named_S14"] += named_S14
    st[s]["named_strict"] += named_strict
    st[s]["proved"] += proved
    st[s]["proved_strict"] += proved_strict
    if not proved:
        st[s]["pool"] += 1
        st[s]["pool_unproven" if r["grade"] == "[未证]" else "pool_static"] += 1
        pool_rows.append({"entry": r["entry"], "subsystem": s, "name": name,
                          "grade": r["grade"],
                          "size": atlas[r["entry"]][0],
                          "n_instr": atlas[r["entry"]][1]})

print("    池行合计: %d" % len(pool_rows))

# 与 PANEL_CHK recalc_all.tsv 只读对照（输入指纹一致的现值）
drift = 0
if os.path.exists(RECALC_TSV):
    ref = {}
    with open(RECALC_TSV, encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if row and row[0].startswith("S") and row[0] != "S22" or (row and row[0] == "S22"):
                ref[row[0]] = row
    cols = {"n": 1, "named_L": 2, "named_S14": 3, "named_strict": 4,
            "proved": 5, "proved_strict": 6}
    for s in SUBS:
        if s not in ref:
            continue
        for k, ci in cols.items():
            if int(ref[s][ci]) != st[s][k]:
                drift += 1
                print("    DRIFT %s %s: survey=%d recalc=%s" % (s, k, st[s][k], ref[s][ci]))
    print("    recalc_all.tsv 对照: %s（drift=%d）" % ("PASS" if drift == 0 else "FAIL", drift))

# ---------------------------------------------------------------- 3. ③b② 机械形态判定
print("[3] ③b② 机械形态判定（skipdata=True，逐池行反汇编）", flush=True)
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text")
TEXT_VA = IB + sec.VirtualAddress
TEXT_DATA = sec.get_data()
TEXT_SIZE = max(sec.Misc_VirtualSize, sec.SizeOfRawData)
print("    ImageBase=0x%08X .text=[0x%X, 0x%X)" % (IB, TEXT_VA, TEXT_VA + TEXT_SIZE))

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True


def read_va(va, maxlen):
    off = va - TEXT_VA
    if off < 0 or off >= len(TEXT_DATA):
        return b""
    return TEXT_DATA[off:off + maxlen]


def scan_row(row):
    ea = int(row["entry"], 16)
    size = row["size"] or 0
    code = read_va(ea, size)
    if not code:
        return dict(n_call=0, n_cand=0, n_valid=0, n_trap=0, n_p2rej=0)
    insns = list(md.disasm(code, ea))
    idx_by_addr = {ins.address: i for i, ins in enumerate(insns)}
    n_call = 0
    n_cand = 0
    n_valid = 0
    n_trap = 0
    n_p2rej = 0
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL:
            continue
        n_call += 1
        # (1) call 后 +1..+3 内找比较；窗口内只允许可解码、非控制、不写 eax 的无关指令
        k = None
        for j in range(i + 1, min(i + 4, len(insns))):
            mid = insns[j]
            if mid.id == 0 or mid.id in CONTROL_IDS or writes_eax(mid):
                break
            tk = test_kind(mid)
            if tk:
                k = j
                break
        if k is None:
            continue
        # (2) 比较后 +1..+2 内找 jcc；比较与跳转之间 eax 被覆写/断链 => 陷阱，不算
        #     注意顺序：先判 JCC_IDS，再判非 jcc 的断链（CONTROL_IDS 包含全部 jcc，
        #     若先判 CONTROL 会把条件跳转吞掉——首跑 p3b2=0 的根因）
        for m in range(k + 1, min(k + 3, len(insns))):
            jc = insns[m]
            if jc.id in JCC_IDS:
                gap = insns[k + 1:m]
                bad_gap = any(g.id == 0 or g.id in CONTROL_IDS or writes_eax(g)
                              for g in gap)
                n_cand += 1
                if bad_gap:
                    n_trap += 1  # 陷阱：比较与分支之间 eax 被覆写再分支
                    break
                # (3) taken vs fall-through 动作签名必须不同
                tgt = None
                if jc.operands and jc.operands[0].type == X86_OP_IMM:
                    tgt = jc.operands[0].imm & 0xFFFFFFFF
                ti = idx_by_addr.get(tgt) if tgt is not None else None
                sig_t = path_sig(insns, ti) if ti is not None else OUT_OF_BODY_SIG
                sig_f = path_sig(insns, m + 1)
                if tuple(sig_t[x] for x in SIG_KEYS) != tuple(sig_f[x] for x in SIG_KEYS):
                    n_valid += 1
                else:
                    n_p2rej += 1
                break
            if writes_eax(jc) or jc.id == 0:
                # eax 链在比较与分支之间断掉；若紧跟其后的确是 jcc，构成卡片陷阱形态
                if m + 1 < len(insns) and insns[m + 1].id in JCC_IDS:
                    n_trap += 1  # 陷阱：比较与分支之间 eax 被覆写再分支
                break
            if jc.id in CONTROL_IDS:
                break  # jmp/ret 等控制转移：该比较的分支形态不成立（不计陷阱）
    return dict(n_call=n_call, n_cand=n_cand, n_valid=n_valid,
                n_trap=n_trap, n_p2rej=n_p2rej)


hits = []
tot = dict(rows=0, cand=0, trap=0, p2rej=0, valid_sites=0, call=0)
for idx, row in enumerate(pool_rows):
    res = scan_row(row)
    row.update(res)
    row["hit"] = res["n_valid"] > 0
    row["p3b2_named"] = bool(row["name"]) and not re.match(r"^(sub_|.*::sub_)", row["name"])
    tot["rows"] += 1
    tot["call"] += res["n_call"]
    tot["cand"] += res["n_cand"]
    tot["trap"] += res["n_trap"]
    tot["p2rej"] += res["n_p2rej"]
    tot["valid_sites"] += res["n_valid"]
    if row["hit"]:
        hits.append(row)
    if (idx + 1) % 1000 == 0:
        print("    ... %d/%d 池行已扫（现命中 %d）" % (idx + 1, len(pool_rows), len(hits)),
              flush=True)

print("    扫描完成: 池 %d 行，p3b2 命中 %d 行（站点 %d，候选对 %d，陷阱剔 %d，P2 剔 %d）"
      % (len(pool_rows), len(hits), tot["valid_sites"], tot["cand"], tot["trap"],
         tot["p2rej"]))

# ---------------------------------------------------------------- 4. 汇总与产出
print("[4] 汇总与产出", flush=True)
agg = {}
for s in SUBS:
    d = st[s]
    thr_n = math.ceil(0.9 * d["n"])
    thr_p = math.ceil(0.5 * d["n"])
    s_hits = [h for h in hits if h["subsystem"] == s]
    p3b2 = len(s_hits)
    p3b2_named = sum(1 for h in s_hits if h["p3b2_named"])
    best = d["proved"] + p3b2
    gap = thr_p - d["proved"]
    can_close = best >= thr_p
    named_ok = d["named_S14"] >= thr_n
    if not can_close:
        verdict = "proved 不可闭"
    elif named_ok:
        verdict = "proved 可闭且 named 已够"
    else:
        verdict = "proved 可闭但 named 不够"
    agg[s] = dict(n=d["n"], named_S14=d["named_S14"], proved=d["proved"],
                  proved_strict=d["proved_strict"], p3b2=p3b2, p3b2_named=p3b2_named,
                  best_proved=best, gap_now=gap, can_close=can_close,
                  named_ok=named_ok, verdict=verdict, thr_named=thr_n, thr_proved=thr_p,
                  pool=d["pool"], population=d["total"],
                  named_gap=max(0, thr_n - d["named_S14"]),
                  pool_unproven=d["pool_unproven"], pool_static=d["pool_static"],
                  trap=sum(h["n_trap"] for h in s_hits),
                  p2rej=sum(h["n_p2rej"] for h in s_hits))

out_survey = os.path.join(BASE, "survey.tsv")
with open(out_survey, "w", encoding="utf-8", newline="") as f:
    f.write("subsystem\tn\tnamed_S14\tproved\tproved_strict\tp3b2\tp3b2_named\t"
            "best_proved\tgap_now\tcan_close\tnamed_ok\tverdict\n")
    for s in SUBS:
        a = agg[s]
        f.write("\t".join([s, str(a["n"]), str(a["named_S14"]), str(a["proved"]),
                           str(a["proved_strict"]), str(a["p3b2"]), str(a["p3b2_named"]),
                           str(a["best_proved"]), str(a["gap_now"]),
                           str(a["can_close"]), str(a["named_ok"]), a["verdict"]]) + "\n")
print("    写出 %s（22 行数据，不含 TOTAL）" % out_survey)

out_rate = os.path.join(BASE, "base_rate.tsv")
tot_pop = sum(agg[s]["population"] for s in SUBS)
tot_pool = sum(agg[s]["pool"] for s in SUBS)
tot_p3b2 = sum(agg[s]["p3b2"] for s in SUBS)
with open(out_rate, "w", encoding="utf-8", newline="") as f:
    f.write("subsystem\tpopulation\tpool\tp3b2\trate\n")
    for s in SUBS:
        a = agg[s]
        rate = (a["p3b2"] / a["pool"]) if a["pool"] else 0.0
        f.write("%s\t%d\t%d\t%d\t%.6f\n" % (s, a["population"], a["pool"], a["p3b2"], rate))
    tr = (tot_p3b2 / tot_pool) if tot_pool else 0.0
    f.write("TOTAL\t%d\t%d\t%d\t%.6f\n" % (tot_pop, tot_pool, tot_p3b2, tr))
print("    写出 %s（含 TOTAL 行）" % out_rate)

out_detail = os.path.join(BASE, "hits_detail.tsv")
with open(out_detail, "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsubsystem\tname\tgrade\tsize\tn_insn\tn_call\tn_site\tn_valid\t"
            "n_trap\tn_p2rej\tp3b2_named\n")
    for h in hits:
        f.write("\t".join([h["entry"], h["subsystem"], h["name"], h["grade"],
                           str(h["size"]), str(h["n_instr"]), str(h["n_call"]),
                           str(h["n_cand"]), str(h["n_valid"]), str(h["n_trap"]),
                           str(h["n_p2rej"]), str(h["p3b2_named"])]) + "\n")
print("    写出 %s（命中 %d 行）" % (out_detail, len(hits)))

# ---------------------------------------------------------------- 5. 控制台摘要
print("\n=== 摘要 ===")
print("population=%d pool=%d p3b2=%d 整体基础率=%d/%d=%.4f（%.2f%%）" % (
    tot_pop, tot_pool, tot_p3b2, tot_p3b2, tot_pool, tr, tr * 100))
print("%-4s %5s %5s %5s %5s %5s %6s %5s %5s  %s" % (
    "S", "pool", "p3b2", "p2rej", "trap", "prov", "best", "gap", "named", "verdict"))
for s in SUBS:
    a = agg[s]
    print("%-4s %5d %5d %5d %5d %5d %6d %5d %5d  %s" % (
        s, a["pool"], a["p3b2"], a["p2rej"], a["trap"], a["proved"],
        a["best_proved"], a["gap_now"], a["named_S14"], a["verdict"]))
print("\npool 构成: [未证] %d + [静态推断] %d" % (
    sum(agg[s]["pool_unproven"] for s in SUBS),
    sum(agg[s]["pool_static"] for s in SUBS)))
print("p3b2 命中构成: [未证] %d + [静态推断] %d" % (
    sum(1 for h in hits if h["grade"] == "[未证]"),
    sum(1 for h in hits if h["grade"] == "[静态推断]")))
print("全量站点级: call %d → 候选(比较+分叉形态) %d → 陷阱剔 %d → P2 签名同剔 %d → 有效站点 %d"
      % (tot["call"], tot["cand"], tot["trap"], tot["p2rej"], tot["valid_sites"]))
print("完成。")
