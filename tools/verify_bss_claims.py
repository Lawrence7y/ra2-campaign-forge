#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_bss_claims.py —— .data BSS 悬空 VA 断言替代方案（v1）

背景：
  gamemd.exe `.data` VirtualSize=0x367BE4 > SizeOfRawData=0x6C000，
  raw 覆盖 VA 上界 = 0x0087E000，其上无文件字节（BSS）。
  docs/re/va_claims_p1.md §2.5 的 65 条悬空 VA 全部落在 BSS，
  无法做「对象本体」hex 断言。本工具提供两类可机器化的替代断言：

  A. bss-region（区域断言）—— 从节表推导「虚拟存在但无 raw」：
       bss 0xVA = virtual
     只要 VA 落在任一节的 [base+SizeOfRawData, base+max(VS,RS)) 内即 PASS。
     这类断言证明「该地址在映像中真实预留」，但不含运行时初值。

  B. text-xref（写点/读点指令断言）—— 扫描 .text 中对该 BSS VA 的绝对地址引用，
     对引用点指令字节做常规 hex 断言：
       0xTEXTVA = HEX…  # bss-xref -> 0xBSSVA | kind=write|read|lea|push|imm
     这类断言把「对象本体」降级为「引用它的代码锚点」，仍可离线复算。

用法：
  python tools/verify_bss_claims.py
  python tools/verify_bss_claims.py --vas-file out/re_work/audit_toolfix/bss65_vas.txt
  python tools/verify_bss_claims.py --emit-claims out/re_work/audit_toolfix/claims_bss_p1.txt
  python tools/verify_bss_claims.py --json out/re_work/audit_toolfix/bss_coverage.json

产出：
  - claims 文件（可直接喂 tools/audit_bytes.py）
  - 覆盖统计 JSON
  - 逐条覆盖表（stdout）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
IMAGE_BASE = 0x400000

# 默认 65 条 BSS 悬空 VA（docs/re/va_claims_p1.md §2.5）
DEFAULT_VAS = [
    0x0087E180, 0x0087E28C, 0x0087E2A8, 0x0087E75C, 0x0087E7F8,
    0x0087E828, 0x0087E82C, 0x0087E848, 0x0087E8A4, 0x0087E8B8,
    0x0087F658, 0x0087F770, 0x0087F778, 0x0087F7E8, 0x0087F7EC,
    0x0087F7F0, 0x0087F7F4, 0x00884D90, 0x00886B88, 0x00886FA8,
    0x008871E0, 0x00887314, 0x00887324, 0x00887330, 0x00887640,
    0x00887644, 0x00887888, 0x0089C568, 0x0089C8E8, 0x0089C900,
    0x0089E3A0, 0x0089E790, 0x0089E794, 0x0089E7C6, 0x0089EA40,
    0x0089F688, 0x0089F68C, 0x0089F690, 0x0089F694, 0x0089F698,
    0x0089F69C, 0x0089F6A0, 0x0089F6A4, 0x008A0000, 0x008A0360,
    0x008A0370, 0x008A0394, 0x008A03A0, 0x008A0E88, 0x008A0E8C,
    0x008A0E98, 0x008A38E0, 0x008B40C8, 0x008B40CC, 0x008B40D8,
    0x008B40E8, 0x008B40EC, 0x008B40F8, 0x008B4108, 0x008B4120,
    0x008B413C, 0x008B4178, 0x008B41A8, 0x008B41FC, 0x008B4204,
]


# ---------- PE helpers（与 tools/audit_bytes.py v3 同口径） ----------

def load_exe(path=EXE):
    with open(path, "rb") as f:
        return f.read()


def sections(d: bytes):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    optsz = struct.unpack_from("<H", d, pe + 20)[0]
    size_headers = struct.unpack_from("<I", d, pe + 24 + 60)[0] or 0x200
    off = pe + 24 + optsz
    out = [("PE-header", IMAGE_BASE, size_headers, size_headers, 0)]
    for i in range(nsec):
        o = off + i * 40
        name = d[o : o + 8].rstrip(b"\0").decode("ascii", "replace")
        vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
        out.append((name, IMAGE_BASE + va, vs, rs, rp))
    return out


def va2off(secs, va):
    for name, base, vs, rs, rp in secs:
        if base <= va < base + max(vs, rs):
            delta = va - base
            if delta < rs:
                return rp + delta, name
            return None, name + "(虚拟段/无文件数据)"
    return None, "未映射"


def va_in_bss(secs, va):
    for name, base, vs, rs, rp in secs:
        if base <= va < base + max(vs, rs):
            delta = va - base
            if delta >= rs:
                return True, name
            return False, name
    return False, "未映射"


# ---------- xref 扫描与分类（capstone 线性反汇编验证） ----------

def find_text_section(secs):
    for name, base, vs, rs, rp in secs:
        if name == ".text":
            return base, vs, rs, rp
    return None


def scan_text_xrefs(d, secs, bss_vas):
    """扫描 .text 中对 BSS VA 的绝对地址引用（字节定位 + capstone 验证）。

    策略：先用 4 字节 LE 模式定位候选命中，再从命中点回溯反汇编，
    验证该 4 字节确实是一条指令的 mem.disp 或非 call/jmp 的 imm 操作数。
    这样既不依赖线性反汇编同步，又杜绝 rel32 等伪命中。

    返回 {bss_va: [ {insn_va, insn_hex, kind, asm}, ... ]}
    """
    text = find_text_section(secs)
    if text is None:
        return {}
    text_base, text_vs, text_rs, text_rp = text
    text_bytes = d[text_rp : text_rp + text_rs]

    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        from capstone.x86 import X86_OP_MEM, X86_OP_IMM
    except Exception:
        print("FATAL: capstone required for xref scan")
        return {}

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    hits = defaultdict(list)
    # 每条指令只记录一次，避免同一指令对同一 VA 重复
    seen_insn = defaultdict(set)

    for bss_va in bss_vas:
        pat = struct.pack("<I", bss_va)
        start = 0
        while True:
            idx = text_bytes.find(pat, start)
            if idx < 0:
                break
            # 在 .text 内的文件偏移
            fileoff = text_rp + idx
            hit_va = text_base + idx  # 地址字段的 VA
            start = idx + 1

            # 回溯 1..15 字节找指令起点
            best = None
            for back in range(0, 16):
                insn_start_off = fileoff - back
                if insn_start_off < text_rp:
                    break
                insn_va = text_base + (insn_start_off - text_rp)
                # 最多反汇编 15 字节
                chunk = d[insn_start_off : insn_start_off + 15]
                for insn in md.disasm(chunk, insn_va):
                    # 该指令必须覆盖 hit 字节
                    insn_end_off = insn_start_off + insn.size
                    if insn_start_off <= fileoff < insn_end_off:
                        # 验证操作数
                        kind = _match_operand(insn, bss_va, X86_OP_MEM, X86_OP_IMM)
                        if kind:
                            if best is None or insn.size < best[0].size:
                                best = (insn, kind)
                    break  # 只取第一条（从该起点的唯一解码）
            if best is not None:
                insn, kind = best
                if insn.address not in seen_insn[bss_va]:
                    seen_insn[bss_va].add(insn.address)
                    hits[bss_va].append(
                        dict(
                            insn_va=insn.address,
                            insn_hex=bytes(insn.bytes).hex(),
                            kind=kind,
                            asm=f"{insn.mnemonic} {insn.op_str}".strip(),
                        )
                    )
    return hits


def _match_operand(insn, bss_va, X86_OP_MEM, X86_OP_IMM):
    """检查指令是否有操作数等于 bss_va，返回 kind 或 None。"""
    for op in insn.operands:
        if op.type == X86_OP_MEM:
            if op.mem.base == 0 and op.mem.index == 0 and (op.mem.disp & 0xFFFFFFFF) == bss_va:
                ops = insn.op_str
                if "," in ops:
                    dest = ops.split(",", 1)[0]
                    return "write" if "[" in dest else "read"
                return "read"
        elif op.type == X86_OP_IMM:
            # call/jmp 的 imm 是相对目标，排除
            if insn.mnemonic.startswith(("call", "jmp", "j", "loop")):
                continue
            if (op.imm & 0xFFFFFFFF) == bss_va:
                if insn.mnemonic.startswith("lea"):
                    return "lea"
                if insn.mnemonic.startswith("push"):
                    return "push"
                return "imm"
    return None


# ---------- 断言生成 ----------

def run(vas, exe_path=EXE, emit_claims=None, json_out=None, verbose=True, max_xrefs_per_va=8):
    d = load_exe(exe_path)
    secs = sections(d)

    # capstone 线性反汇编扫描 .text 真引用
    if verbose:
        print("扫描 .text 中对 BSS VA 的绝对地址引用（capstone 线性反汇编）...")
    xref_map = scan_text_xrefs(d, secs, vas)

    results = []
    all_xref_claims = []  # (va, hexbytes, label)

    for bss_va in vas:
        is_bss, secname = va_in_bss(secs, bss_va)
        classified = xref_map.get(bss_va, [])
        # 限制每个 VA 的断言条数：写点优先，其次读点，再次 lea/push/imm
        pri = {"write": 0, "read": 1, "lea": 2, "push": 3, "imm": 4, "other": 5}
        classified_sorted = sorted(classified, key=lambda c: pri.get(c["kind"], 9))
        selected = classified_sorted[:max_xrefs_per_va]

        has_write = any(c["kind"] == "write" for c in classified)
        has_read = any(c["kind"] == "read" for c in classified)
        has_any = len(classified) > 0

        for c in selected:
            label = f"bss-xref -> {bss_va:#010x} | kind={c['kind']} | {c['asm']}"
            all_xref_claims.append((c["insn_va"], c["insn_hex"], label))

        results.append(
            dict(
                bss_va=hex(bss_va),
                region_ok=is_bss,
                section=secname,
                xref_count=len(classified),
                write_count=sum(1 for c in classified if c["kind"] == "write"),
                read_count=sum(1 for c in classified if c["kind"] == "read"),
                lea_count=sum(1 for c in classified if c["kind"] == "lea"),
                push_count=sum(1 for c in classified if c["kind"] == "push"),
                imm_count=sum(1 for c in classified if c["kind"] == "imm"),
                covered=has_any or is_bss,
                xrefs=selected,
            )
        )

        if verbose:
            tag = "BSS-OK" if is_bss else "BSS-FAIL"
            w = sum(1 for c in classified if c["kind"] == "write")
            r = sum(1 for c in classified if c["kind"] == "read")
            print(
                f"{bss_va:#010x}  region={tag:8}  xrefs={len(classified):3}  "
                f"write={w:2} read={r:2}  {secname}"
            )

    # 覆盖统计
    n = len(results)
    n_region = sum(1 for r in results if r["region_ok"])
    n_xref = sum(1 for r in results if r["xref_count"] > 0)
    n_write = sum(1 for r in results if r["write_count"] > 0)
    n_read = sum(1 for r in results if r["read_count"] > 0)
    n_covered = sum(1 for r in results if r["covered"])
    total_xref_claims = len(all_xref_claims)

    summary = dict(
        total_bss_vas=n,
        region_ok=n_region,
        region_fail=n - n_region,
        with_text_xref=n_xref,
        with_write_point=n_write,
        with_read_point=n_read,
        covered_region_or_xref=n_covered,
        total_xref_insn_claims=total_xref_claims,
        coverage_region_pct=round(100.0 * n_region / n, 1) if n else 0,
        coverage_xref_pct=round(100.0 * n_xref / n, 1) if n else 0,
        coverage_write_pct=round(100.0 * n_write / n, 1) if n else 0,
        coverage_any_pct=round(100.0 * n_covered / n, 1) if n else 0,
    )

    if verbose:
        print()
        print("=" * 72)
        print(f"BSS 悬空 VA 覆盖统计  (共 {n} 条)")
        print(f"  区域断言 bss-region PASS : {n_region}/{n}  ({summary['coverage_region_pct']}%)")
        print(f"  存在 .text xref         : {n_xref}/{n}  ({summary['coverage_xref_pct']}%)")
        print(f"  存在写点 (write)        : {n_write}/{n}  ({summary['coverage_write_pct']}%)")
        print(f"  存在读点 (read)         : {n_read}/{n}")
        print(f"  区域或 xref 至少一项     : {n_covered}/{n}  ({summary['coverage_any_pct']}%)")
        print(f"  生成 xref 指令字节断言   : {total_xref_claims} 条")

    # 写 claims 文件
    if emit_claims:
        os.makedirs(os.path.dirname(emit_claims) or ".", exist_ok=True)
        with open(emit_claims, "w", encoding="utf-8") as f:
            f.write("# claims_bss_p1.txt —— .data BSS 悬空 VA 断言替代方案（verify_bss_claims.py 生成）\n")
            f.write("# 基线: ra2youli/gamemd.exe (YR 1.001) MD5 4f37486e5b0dbe2ae5f45aeee0f98367\n")
            f.write("# 断言类型:\n")
            f.write("#   bss 0xVA = virtual          —— 区域断言（虚拟存在但无 raw，从节表推导）\n")
            f.write("#   0xTEXTVA = HEX…             —— .text 引用点指令字节（写点/读点降级锚定）\n")
            f.write(f"# 覆盖: region {n_region}/{n}  xref {n_xref}/{n}  write {n_write}/{n}\n")
            f.write("\n")
            f.write("## A. bss-region 区域断言\n")
            for r in results:
                f.write(f"bss {r['bss_va']} = virtual  # region={r['section']} xrefs={r['xref_count']} write={r['write_count']} read={r['read_count']}\n")
            f.write("\n## B. text-xref 写点/读点指令断言\n")
            for va, hx, label in all_xref_claims:
                # 格式化 hex 为空格分隔
                pretty = " ".join(hx[i : i + 2] for i in range(0, len(hx), 2))
                f.write(f"{va:#010x} = {pretty}  # {label}\n")
        print(f"\nclaims -> {emit_claims}")

    if json_out:
        os.makedirs(os.path.dirname(json_out) or ".", exist_ok=True)
        json.dump(
            dict(summary=summary, results=results),
            open(json_out, "w", encoding="utf-8"),
            ensure_ascii=False,
            indent=2,
        )
        print(f"json   -> {json_out}")

    return 0


def main():
    ap = argparse.ArgumentParser(description="BSS 悬空 VA 断言替代方案")
    ap.add_argument("--vas-file", help="每行一个 0xVA 的清单文件")
    ap.add_argument("--vas", help="逗号分隔的 VA 列表，如 0x87e180,0x87e28c")
    ap.add_argument("--exe", default=EXE)
    ap.add_argument("--emit-claims", help="输出 claims 文件路径")
    ap.add_argument("--json", dest="json_out", help="输出覆盖统计 JSON")
    ap.add_argument("--max-xrefs", type=int, default=8, help="每个 BSS VA 最多生成多少条 xref 断言（默认 8）")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    vas = list(DEFAULT_VAS)
    if a.vas_file:
        vas = []
        for line in open(a.vas_file, encoding="utf-8"):
            s = line.split("#", 1)[0].strip()
            if s:
                vas.append(int(s, 16))
    elif a.vas:
        vas = [int(x.strip(), 16) for x in a.vas.split(",") if x.strip()]

    sys.exit(run(vas, a.exe, a.emit_claims, a.json_out, verbose=not a.quiet, max_xrefs_per_va=a.max_xrefs))


if __name__ == "__main__":
    main()
