#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""三份 RC-4 minidump 的**独立**现场校验（不依赖他人判读脚本的硬编码）。

★ 为什么要自己写：
  `lead/goal2_rc4_trigger_20261022/VERIFY_RC4_MINIDUMP.py` 头注写 `[--dump <path>]`，
  但全文件**零 argv 解析**（`--dump` 只出现在注释里），且 `DUMP`/`EXCEPT`/
  `REAL_STACK_BASE`/`REPORTED_ESP` 全是**第一份 dump 专属常量** ⇒
  传入第二份路径也只会重读第一份。实测坐实：`--dump …184212_t1` 仍报
  `size=381007524`（那是 t1 的 size，t212 应 381003428）。
  ⇒ 该脚本对 dump #2/#3 给不出有效结果；「19/19 PASS」只对 dump #1 成立。

★ 本件的判读方法（写域纪律：只读他人件，不改他人件）：
  上一轮用「x86 CONTEXT 固定偏移 0xB8=Eip」**失败**（读到垃圾 0x2B）：
  WOW64 转储里线程上下文是混合格式，偏移随 flavor 变——
  实测针值 `37477200` 落在 ctx+0xF8（两种 flavor 假设恰好同点，不可依赖巧合）。
  ⇒ 改用**三层交叉判据**，每层都可独立杀：
    L1 结构层：ThreadList 流尺寸 == 4 + 48×count（stride 48 被尺寸等式证实）；
    L2 唯一性层：崩溃 EIP 字节的 little-endian 针值在**整份 dump 恰好出现 1 次**；
    L3 归属层：该唯一偏移必须落在某线程 context 窗口 [rva, rva+size) 内，
        且该线程 ThreadId == PROBE_DBG 记录里 rc4_hit.thread（33096/29792/37180）。
  另记录辅助寄存器读值（x86 Eax=+0xA0=0 / Esi=+0xB0=0x87F7E8 /
  Edi=+0x98=0xF9A344）作旁证，**不作判据**（偏移未先验证实）。

★ 阳性对照（--self-mutation）：
  M1 针值改坏 ⇒ L2 命中数 0 ⇒ 三份全红（判据不是恒过）；
  M2 期望 tid 改坏 ⇒ L3 归属不匹配 ⇒ 三份全红。
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
PROBE_DIR = ROOT / "lead/goal2_rc4_trigger_20261022"
STREAM_THREAD_LIST = 3
STREAM_SYSTEM_INFO = 7
CTX_SIZE_ASSERT = 0x67F   # WOW64 混合上下文实测尺寸（三份一致）

# dump ↔ PROBE_DBG 记录配对（trip 序号 → 期望 tid / 申报 size）。
# 申报侧数据源=他人线 PROBE_DBG JSON（只读），期望由它**逐份**给出，非硬编码巧合。
PAIRINGS = [
    (Path(r"D:\ra2dumps\rc4dbg_20261022T183405_t1.dmp"),
     "PROBE_DBG_20261022T183425.json", 0),
    (Path(r"D:\ra2dumps\rc4dbg_20261022T184212_t1.dmp"),
     "PROBE_DBG_20261022T184255.json", 0),
    (Path(r"D:\ra2dumps\rc4dbg_20261022T184235_t2.dmp"),
     "PROBE_DBG_20261022T184255.json", 1),
]

RESULTS = []


def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("  [%s] %-58s %s" % ("PASS" if ok else "FAIL", name, detail))


def load_expectations():
    exp = []
    for dump, jf, trip_idx in PAIRINGS:
        rec = json.loads((PROBE_DIR / jf).read_text(encoding="utf-8"))
        t = rec["trips"][trip_idx]
        hit = t["rc4_hit"]
        exp.append({
            "dump": dump, "json": jf, "trip": t["trip"],
            "tid": hit["thread"], "addr": hit["address"],
            "code": hit["code"], "info": hit["info"],
            "singleton": hit["singleton_at_hit"],
            "decl_size": t["minidump"]["size"],
            "decl_sha16": t["minidump"]["sha256"][:16],
        })
    return exp


def parse_threads(data):
    """返回 (threads, sysinfo_arch)。threads: [{tid, ctx_rva, ctx_size}]"""
    if data[:4] != b"MDMP":
        raise ValueError("not MDMP header")
    n_streams, dir_rva = struct.unpack_from("<II", data, 8)
    st3 = st7 = None
    off = dir_rva
    for _ in range(n_streams):
        st, st_size, rva = struct.unpack_from("<III", data, off)
        if st == STREAM_THREAD_LIST:
            st3 = (st_size, rva)
        elif st == STREAM_SYSTEM_INFO:
            st7 = (st_size, rva)
        off += 12
    arch = struct.unpack_from("<H", data, st7[1])[0] if st7 else None
    size3, rva3 = st3
    count = struct.unpack_from("<I", data, rva3)[0]
    threads = []
    stride_ok = (size3 == 4 + count * 48)
    for i in range(count):
        base = rva3 + 4 + i * 48
        tid, = struct.unpack_from("<I", data, base)
        ctx_size, ctx_rva = struct.unpack_from("<II", data, base + 40)
        threads.append({"tid": tid, "ctx_rva": ctx_rva, "ctx_size": ctx_size})
    return threads, stride_ok, count, arch


def verify_one(e, needle_bytes, expect_eip=0x00724737):
    d = e["dump"]
    tag = d.name.replace("rc4dbg_", "").replace(".dmp", "")
    if not d.is_file():
        chk("%s dump 在盘" % tag, False, str(d))
        return False
    data = d.read_bytes()
    ok = True

    def c(name, cond, detail=""):
        nonlocal ok
        if not cond:
            ok = False
        chk("%s %s" % (tag, name), cond, detail)

    sha16 = hashlib.sha256(data).hexdigest()[:16]
    c("size/sha 与 PROBE_DBG 申报一致",
        len(data) == e["decl_size"] and sha16 == e["decl_sha16"],
        "size=%d(申报%d) sha=%s(申报%s)" % (len(data), e["decl_size"], sha16, e["decl_sha16"]))

    threads, stride_ok, count, arch = parse_threads(data)
    # L1 结构层：stride 等式 + 架构声明
    c("L1 ThreadList 尺寸==4+48×count", stride_ok,
        "count=%d stream_size=%d 声明arch=0x%x(9=UNKNOWN_WOW64)" % (count, 4 + count * 48, arch))

    # L2 唯一性层：崩溃 EIP 针值整份恰好 1 次
    occ = []
    pos = 0
    while True:
        j = data.find(needle_bytes, pos)
        if j < 0:
            break
        occ.append(j)
        pos = j + 1
    c("L2 崩溃EIP字节的针值整份恰 1 次", len(occ) == 1,
        "命中 %d 次 @%s" % (len(occ), [hex(o) for o in occ[:4]]))
    if len(occ) != 1:
        return ok

    # L3 归属层：唯一偏移 ∈ 崩溃线程 context 窗口，且 tid == PROBE_DBG rc4_hit.thread
    owner = None
    off_in_ctx = None
    for t in threads:
        if t["ctx_rva"] <= occ[0] < t["ctx_rva"] + t["ctx_size"]:
            owner, off_in_ctx = t["tid"], occ[0] - t["ctx_rva"]
            c("L3 归属线程 tid == PROBE_DBG tid", owner == e["tid"],
                "owner=%d expect=%d needle@ctx+0x%x ctx_size=0x%x"
                % (owner, e["tid"], off_in_ctx, t["ctx_size"]))
            break
    else:
        c("L3 归属线程存在", False, "needle 不在任何 context 窗口内")
        return ok

    # 辅助旁证（不作判据）：期望 EIP 值 + 同线程其它寄存器形态三份一致
    ctx_base = occ[0] - off_in_ctx
    eax = struct.unpack_from("<I", data, ctx_base + 0xA0)[0]
    esi = struct.unpack_from("<I", data, ctx_base + 0xB0)[0]
    edi = struct.unpack_from("<I", data, ctx_base + 0x98)[0]
    c("现场三重一致性（读值复算）",
        eax == 0 and esi == 0x87F7E8 and edi == 0xF9A344,
        "Ecx=%08X(0=空对象) Esi=%08X(0x87F7E8 单例全局) Edi=%08X(=except Esp)"
        % (eax, esi, edi))
    return ok


def main() -> int:
    mut_kind = None
    for a in sys.argv[1:]:
        if a.startswith("--mutate-"):
            mut_kind = a.split("--mutate-")[-1]
    print("=" * 78)
    print("三份 RC-4 minidump 独立校验（L1 结构 / L2 唯一 / L3 归属 三层判据）")
    if mut_kind:
        print("!! 变异模式 %s：M1=针值改坏(期望 L2 杀) M2=tid 改坏(期望 L3 杀)" % mut_kind)
    print("=" * 78)

    exps = load_expectations()
    for e in exps:
        print("\n--- %s (PROBE_DBG trip %d) ---" % (e["dump"].name, e["trip"]))
        addr_ok = (e["addr"] == 0x00724737 and e["code"] == 0xC0000005
                   and e["info"] == [0, 592] and e["singleton"] == 0)
        chk("PROBE_DBG 申报三元组 (addr=0x724737/code/info/singleton)", addr_ok,
            "addr=%08X code=%X info=%s singleton=%s"
            % (e["addr"], e["code"], e["info"], e["singleton"]))
        needle = struct.pack("<I", 0x12345678 if mut_kind == "M1" else e["addr"])
        e2 = dict(e)
        if mut_kind == "M2":
            e2["tid"] = e["tid"] + 1  # 错 tid ⇒ L3 必红
        verify_one(e2, needle)
    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok, dt in RESULTS:
        if not ok:
            print("  FAILED: %s | %s" % (n, dt))
    if mut_kind:
        return 0  # 变异模式看逐条红/绿，不卡 rc
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
