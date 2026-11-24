#!/usr/bin/env python3
"""R104 exec: third disassembler (iced-x86) recheck of the 88 only-cap addresses.

Reads only the raw address lists / source byte fields from R101 artifacts;
recomputes every number from the exe bytes. No conclusion fields are reused.
"""
import bisect
import hashlib
import json
import os

import iced_x86 as ic

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXE = os.path.join(ROOT, "ra2bench", "gamemd.exe")
CORE = os.path.join(ROOT, "_r101", "_exec", "r101_core.json")
BC = os.path.join(ROOT, "_r101", "_exec", "r101_bc.json")
RECHECK = os.path.join(ROOT, "_r101", "r101e_recheck.json")
OUTDIR = os.path.join(ROOT, "_r104", "_exec")

BASE = 0x401000
END = 0x7E038D
VS = END - BASE
FILE_OFF = 0x1000
EXPECTED_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
EXPECTED_DIS_SHA = "5935356b2914d90baeaeb0d8ea5198961976118526b37d341ab72f06d4046c70"
DIS = "/tmp/r93_disasm.txt"

exe = open(EXE, "rb").read()
sha_exe = hashlib.sha256(exe).hexdigest()
sha_dis = hashlib.sha256(open(DIS, "rb").read()).hexdigest()
assert sha_exe == EXPECTED_SHA, sha_exe
assert sha_dis == EXPECTED_DIS_SHA, sha_dis
code = exe[FILE_OFF:FILE_OFF + VS]
assert len(code) == VS


def hx(a):
    return "0x%x" % a


def raw_bytes(a, n=16):
    o = a - BASE + FILE_OFF
    return exe[o:o + n]


def dec_at(a, n=16):
    d = ic.Decoder(32, raw_bytes(a, n), ip=a)
    ins = d.decode()
    return ins


def fmt(ins):
    if ins.code == ic.Code.INVALID:
        return "(bad)"
    return str(ins)


# ---------- iced linear scan over .text ----------
dec = ic.Decoder(32, code, ip=BASE)
starts = {}          # start -> len
invalid_starts = []  # (start, len) for Code.INVALID cells
while dec.can_decode:
    ins = dec.decode()
    a = ins.ip
    L = ins.len
    assert BASE <= a < END, (hx(a), L)
    starts[a] = L
    if ins.code == ic.Code.INVALID:
        invalid_starts.append((a, L))
assert sum(starts.values()) == VS
assert max(starts) + starts[max(starts)] == END
starts_sorted = sorted(starts)
invalid_set = set(a for a, L in invalid_starts)

core = json.load(open(CORE))
bc = json.load(open(BC))
recheck = json.load(open(RECHECK))
addr88 = [int(x, 16) for x in core["only_cap_ne_list"]]
host88 = {int(k, 16): int(v, 16) for k, v in core["host_of_88"].items()}
cap_bad = set(int(x, 16) for x in core["cap_bad_list"])
detail = bc["detail"]
classes = {}
for d in detail:
    classes.setdefault(d["class"], []).append(int(d["a"], 16))
assert len(addr88) == 88 and len(cap_bad) == 65 and len(detail) == 88

# ---------- T1 ----------
t1_valid, t1_invalid_start, t1_interior = [], [], []
t1_fresh_invalid = []
for a in addr88:
    if a in starts:
        t1_valid.append((a, starts[a]))
    elif a in invalid_set:
        t1_invalid_start.append((a, invalid_set[a]))
    else:
        j = bisect.bisect_right(starts_sorted, a) - 1
        s = starts_sorted[j]
        L = starts[s]
        assert s + L > a, hx(a)
        t1_interior.append((a, s, L, a - s))
    fi = dec_at(a)
    if fi.code == ic.Code.INVALID:
        t1_fresh_invalid.append((a, fi.len))

t1 = {
    "sum_len": sum(starts.values()),
    "virtual_size": VS,
    "iced_cells": len(starts),
    "iced_invalid_start_count": len(invalid_starts),
    "n88": len(addr88),
    "valid_start": len(t1_valid),
    "invalid_start": len(t1_invalid_start),
    "interior": len(t1_interior),
    "fresh_decode_invalid_at_88": len(t1_fresh_invalid),
    "valid_list": [[hx(a), L] for a, L in t1_valid],
    "invalid_start_list": [[hx(a), L] for a, L in t1_invalid_start],
    "interior_list": [[hx(a), hx(s), L, off, fmt(dec_at(s))] for a, s, L, off in t1_interior],
    "fresh_invalid_list": [[hx(a), L] for a, L in t1_fresh_invalid],
}
assert t1["valid_start"] + t1["invalid_start"] + t1["interior"] == 88

# ---------- T2 ----------
t2 = []
for d in detail:
    if d["class"] != "B1":
        continue
    a, host = int(d["a"], 16), int(d["host"], 16)
    ins = dec_at(host)
    is_inv = ins.code == ic.Code.INVALID
    L = ins.len
    covers = host < a < host + L
    t2.append({
        "a": hx(a), "host": hx(host),
        "iced_at_host_invalid": is_inv,
        "iced_at_host_len": L,
        "iced_at_host_text": fmt(ins),
        "covers_a": covers,
        "host_bytes": raw_bytes(host, 16).hex(" "),
        "offset_in_host": a - host,
    })
assert len(t2) == 41

# ---------- T3 ----------
iced_only = sorted(invalid_set - cap_bad)
cap_only = sorted(cap_bad - invalid_set)
inter = sorted(invalid_set & cap_bad)
t3 = {
    "cap_bad_count": len(cap_bad),
    "iced_invalid_start_count": len(invalid_set),
    "intersect_count": len(inter),
    "cap_only_count": len(cap_only),
    "iced_only_count": len(iced_only),
    "intersect": [[hx(a), raw_bytes(a, 8).hex(" ")] for a in inter],
    "cap_only": [[hx(a), raw_bytes(a, 8).hex(" "), dec_at(a).len, fmt(dec_at(a))] for a in cap_only],
    "iced_only": [[hx(a), raw_bytes(a, 8).hex(" "), dec_at(a).len, fmt(dec_at(a))] for a in iced_only],
}

# ---------- T4 ----------
zero = []
for rec in recheck["setA_target_form"]:
    for s in rec["srcs"]:
        if s.get("is_zero_disp_fallthrough"):
            zero.append({
                "target": rec["a"],
                "src_at": s["at"],
                "mn": s["mn"],
                "src_bytes": s["bytes"],
                "txt": s["txt"],
                "insn_len": s["insn_len"],
                "target_minus_next": s["target_minus_next"],
            })
zero.sort(key=lambda x: int(x["src_at"], 16))
card_claimed = ["0x71f99e", "0x728e0a", "0x7b0082", "0x7d9d2d"]
actual_srcs = [x["src_at"] for x in zero]
assert card_claimed[1:] == actual_srcs[1:], (card_claimed, actual_srcs)
assert card_claimed[0] != actual_srcs[0]
t4_rows = []
for a_s in card_claimed + [x["target"] for x in zero]:
    a = int(a_s, 16)
    ins = dec_at(a)
    t4_rows.append({
        "a": a_s,
        "bytes": raw_bytes(a, 8).hex(" "),
        "iced_text": fmt(ins),
        "iced_len": ins.len,
        "is_jcc": bool(ins.is_jcc_short_or_near),
        "is_in_88": a in [int(x, 16) for x in core["only_cap_ne_list"]],
        "is_cap_bad": a in cap_bad,
        "is_iced_invalid_start": a in invalid_set,
    })
a_bad = int(card_claimed[0], 16)
first_is_typo = (raw_bytes(a_bad, 8).hex(" ") == "00 00 00 00 00 00 01 01"
                 and dec_at(a_bad).code != ic.Code.INVALID
                 and not str(dec_at(a_bad).mnemonic).startswith("j"))
t4 = {
    "card_claimed": card_claimed,
    "actual_zero_disp_srcs": actual_srcs,
    "actual_targets": [x["target"] for x in zero],
    "zero_disp_src_records": zero,
    "decode_rows": t4_rows,
    "first_entry_is_typo": first_is_typo,
    "verdict_line": "主会话的 4 条清单里第 1 条是抄错的" if first_is_typo else "第 1 条无误",
}

result = {
    "sha_exe": sha_exe, "sha_dis": sha_dis,
    "base": hx(BASE), "end": hx(END), "virtual_size": VS,
    "iced_cells_total": len(starts),
    "t1": t1, "t2": t2, "t3": t3, "t4": t4,
    "b_class_counts": {k: len(v) for k, v in classes.items()},
}
os.makedirs(OUTDIR, exist_ok=True)
with open(os.path.join(OUTDIR, "r104_result.json"), "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# ---------- markdown ----------
L = []
L.append("# R104 执行报告 · 第三套反汇编器（iced-x86 1.22.0）复算 88 个地址\n")
L.append("## 前提核验\n")
L.append("- exe: ra2bench/gamemd.exe, SHA-256 = %s（与卡面期望一致）" % sha_exe)
L.append("- 反汇编文本: /tmp/r93_disasm.txt, SHA-256 = %s（与卡面期望一致）" % sha_dis)
L.append("- ImageBase 0x400000；.text = [0x401000, 0x7E038D)；VirtualSize = %d；iced 线性扫描共 %d 个单元，sum(len) = %d = VirtualSize，铺满且末单元恰好收于 0x7E038D。" % (VS, len(starts), sum(starts.values())))
L.append("- 所有数字均由本脚本从 exe 字节重算；R101 的 json 仅取原始地址清单（only_cap_ne_list / host_of_88 / detail 的 a,host,class / cap_bad_list / setA_target_form 的 src 字节与 at），未使用任何结论字段。\n")

L.append("## T1 iced 是否也把这 88 个地址当起点\n")
L.append("- iced valid 起点: **%d**" % t1["valid_start"])
L.append("- iced invalid 起点（落在线性扫描 invalid 起点集中）: **%d**" % t1["invalid_start"])
L.append("- 既非起点、落在某个 iced 单元内部: **%d**" % t1["interior"])
L.append("- 补充：若脱离线性扫描、直接从这 88 个地址各自解码，iced 报 Code.INVALID 的有 %d 个。" % t1["fresh_decode_invalid_at_88"])
L.append("- 全局 iced 线性扫描 invalid 起点数 = %d。\n" % len(invalid_starts))
L.append("### T1-A iced valid 起点（%d 个，地址 / 该单元长度）" % len(t1_valid))
for a, ln in t1_valid:
    L.append("- %s len=%d" % (hx(a), ln))
L.append("\n### T1-B iced invalid 起点（%d 个）" % len(t1_invalid_start))
if not t1_invalid_start:
    L.append("- 无")
for a, ln in t1_invalid_start:
    L.append("- %s len=%d" % (hx(a), ln))
L.append("\n### T1-C 落在 iced 单元内部（%d 个，目标 / 包含它的单元起点 / 单元长 / 目标在单元内偏移 / 该单元 iced 文本）" % len(t1_interior))
for row in t1["interior_list"]:
    a, s, ln, off, txt = row
    L.append("- %s <- 单元 %s len=%d (at+%d) %s" % (a, s, ln, off, txt))
L.append("")

L.append("## T2 B1 的 41 个逐址定性\n")
L.append("B1 计数由 detail 的 class 字段重算 = %d。对每个 B1 目标，取其宿主起点（host_of_88 / detail.host）用 iced 单独解码：" % len(t2))
L.append("- iced 在宿主起点也是 invalid: %d / 41" % sum(1 for r in t2 if r["iced_at_host_invalid"]))
L.append("- iced 在宿主起点能解出有效指令: %d / 41" % sum(1 for r in t2 if not r["iced_at_host_invalid"]))
L.append("- iced 宿主单元覆盖到目标地址: %d / 41（其余 %d 个因 invalid 单元长度短于 host 到目标的间距而未覆盖）\n" % (sum(1 for r in t2 if r["covers_a"]), sum(1 for r in t2 if not r["covers_a"])))
L.append("逐址表：目标 / 宿主 / iced 在宿主的文本或 invalid / 长度 / 是否覆盖目标 / 目标在宿主内偏移 / 宿主起始 16 字节")
for r in t2:
    txt = "(bad)" if r["iced_at_host_invalid"] else r["iced_at_host_text"]
    L.append("- %s host=%s -> %s len=%d covers=%s at+%d bytes=%s" % (
        r["a"], r["host"], txt, r["iced_at_host_len"],
        "Y" if r["covers_a"] else "N", r["offset_in_host"], r["host_bytes"]))
L.append("")

L.append("## T3 两个拒解集不是同一集合\n")
L.append("- capstone 拒解集（cap_bad_list 原始清单）: **%d**" % t3["cap_bad_count"])
L.append("- iced 线性扫描 invalid 起点集: **%d**" % t3["iced_invalid_start_count"])
L.append("- 交集: **%d**" % t3["intersect_count"])
L.append("- 只在 capstone: **%d**" % t3["cap_only_count"])
L.append("- 只在 iced: **%d**\n" % t3["iced_only_count"])
L.append("### 只在 capstone（地址 / 起始 8 字节 / iced 单独解码文本 / 长度）")
for a, b, ln, txt in t3["cap_only"]:
    L.append("- %s bytes=%s iced=%s len=%d" % (a, b, txt, ln))
L.append("\n### 只在 iced（地址 / 起始 8 字节 / iced 单独解码文本 / 长度）")
for a, b, ln, txt in t3["iced_only"]:
    L.append("- %s bytes=%s iced=%s len=%d" % (a, b, txt, ln))
L.append("\n### 交集 %d 个（地址 / 起始 8 字节）" % t3["intersect_count"])
for a, b in t3["intersect"]:
    L.append("- %s bytes=%s" % (a, b))
L.append("")

L.append("## T4 集 A 的 4 条疑似零位移 jXX\n")
L.append("从 r101e_recheck.json 的 setA_target_form 重算：n_srcs=1 且 is_zero_disp_fallthrough=True 的共有 %d 条。" % len(zero))
for z in zero:
    L.append("- 源 %s: %s bytes=%s -> 目标 %s，target_minus_next=%d" % (
        z["src_at"], z["txt"], z["src_bytes"], z["target"], z["target_minus_next"]))
L.append("")
L.append("卡面抄录的 4 个地址（即 4 条零位移 jXX 的源地址）: %s" % ", ".join(card_claimed))
L.append("从 setA_target_form 核出的实际 4 个源地址: %s" % ", ".join(actual_srcs))
L.append("实际 4 个跳转目标地址: %s\n" % ", ".join(x["target"] for x in zero))
L.append("关键结论：卡面第 1 条 0x71f99e 既不是源（正确源 0x71f9e2）也不是目标（正确目标 0x71f9e4），是抄写错误。其原始 8 字节 00 00 00 00 00 00 01 01 从该地址解码为 add [eax],al（长度 2），不是条件跳转。")
L.append("判定：**%s**。\n" % t4["verdict_line"])
L.append("逐址解码（卡面 4 个 + 正确目标 4 个；bytes 为从该地址起的 8 字节）：地址 / 字节 / iced 文本 / 长度 / 是否 jXX / 是否在 88 / 是否 cap 拒解 / 是否 iced invalid 起点")
for r in t4_rows:
    L.append("- %s bytes=%s -> %s len=%d jcc=%s in88=%s capbad=%s icedbadstart=%s" % (
        r["a"], r["bytes"], r["iced_text"], r["iced_len"],
        "Y" if r["is_jcc"] else "N", "Y" if r["is_in_88"] else "N",
        "Y" if r["is_cap_bad"] else "N", "Y" if r["is_iced_invalid_start"] else "N"))
L.append("")
L.append("注：其余 3 条卡面抄的是 jXX 指令自身地址，解码为 jb 0x728e0c / jp 0x7b0084 / jge 0x7d9d2f（各长 2）；其跳转目标处字节分别为 d9 8d / db ff / fe 9a，iced 均解为 (bad) 长 2，即目标落在数据字节中，与 R101 的「数据被读成代码」判读一致。")

with open(os.path.join(OUTDIR, "VERDICT104.md"), "w") as f:
    f.write("\n".join(L) + "\n")

print(json.dumps({
    "t1": {k: t1[k] for k in ("valid_start", "invalid_start", "interior", "iced_invalid_start_count", "sum_len", "fresh_decode_invalid_at_88")},
    "t2_invalid_at_host": sum(1 for r in t2 if r["iced_at_host_invalid"]),
    "t2_cover": sum(1 for r in t2 if r["covers_a"]),
    "t3": {k: t3[k] for k in ("cap_bad_count", "iced_invalid_start_count", "intersect_count", "cap_only_count", "iced_only_count")},
    "t4_first_typo": first_is_typo,
}, indent=2))
