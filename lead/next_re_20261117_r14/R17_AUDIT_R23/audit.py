#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17-AUDIT-R23 / audit.py  —— 异族审计员的独立实现
# 不 import、不调用执行方 R17_R23_CALLER_PATH\work.py；PE 解析、E8 扫描、线性反汇编、
# 寄存器写点统计、vtable 切分全部自写。只读 gamemd.exe；不建进程、不调试。
# 产物只写本目录。
import hashlib, json, pathlib, struct
import capstone

IMG = pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
OUT = pathlib.Path(__file__).resolve().parent
EXPECT_PREFIX = "73201CC0"
EXPECT_SUFFIX = "F67476"
IMAGE_BASE = 0x400000

CTOR_A, CTOR_B = 0x43B740, 0x43B680
VT_BUILDING = 0x7E3EBC
SLOT = 0x124
TARGET = 0x43F180
HOST_DECLARED = 0x5A652D
HOST = 0x5A6510


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def parse_pe(b):
    e = u32(b, 0x3C)
    nsec = struct.unpack_from("<H", b, e + 6)[0]
    optsz = struct.unpack_from("<H", b, e + 20)[0]
    opt = e + 24
    assert u32(b, opt + 28) == IMAGE_BASE
    secs = []
    for i in range(nsec):
        s = opt + optsz + i * 40
        name = b[s:s + 8].rstrip(b"\0").decode("latin1")
        vs, va, rs, rp = struct.unpack_from("<IIII", b, s + 8)
        secs.append(dict(name=name, vs=vs, va=va, rs=rs, rp=rp, lo=IMAGE_BASE + va))
    return secs


def main():
    b = IMG.read_bytes()
    sha = hashlib.sha256(b).hexdigest().upper()
    assert sha.startswith(EXPECT_PREFIX) and sha.endswith(EXPECT_SUFFIX), sha
    secs = parse_pe(b)
    S = {s["name"]: s for s in secs}

    def off(va):
        for s in secs:
            r = va - s["lo"]
            if 0 <= r < s["rs"]:
                return s["rp"] + r
        return None

    tx = S[".text"]
    tlo, thi = tx["lo"], tx["lo"] + tx["vs"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    res = {"image": {"path": str(IMG), "sha256": sha, "size": len(b)},
           "sections": [{"name": s["name"], "va": hex(s["lo"]), "vsize": s["vs"], "raw": s["rs"]} for s in secs]}

    # ---------- A1：全 .text 直接 E8 call 到两个 ctor ----------
    scan_start, scan_end = tlo, tlo + tx["vs"]
    scan_bytes = scan_end - scan_start - 4          # 每个字节都能容纳 5 字节指令
    hits = {CTOR_A: [], CTOR_B: []}
    for va in range(scan_start, scan_end - 4):
        o = off(va)
        if b[o] != 0xE8:
            continue
        d = va + 5 + struct.unpack_from("<i", b, o + 1)[0]
        if d in hits:
            hits[d].append(va)
    # 非 E8 形式的直接控制转移（E9/EB/0F8x）到同样目标，作为口径补强
    alt = {CTOR_A: [], CTOR_B: []}
    for va in range(scan_start, scan_end - 4):
        o = off(va)
        op = b[o]
        if op == 0xE9:
            d = va + 5 + struct.unpack_from("<i", b, o + 1)[0]
            if d in alt:
                alt[d].append((va, "jmp rel32"))
        elif op == 0x0F and 0x80 <= b[o + 1] <= 0x8F:
            d = va + 6 + struct.unpack_from("<i", b, o + 2)[0]
            if d in alt:
                alt[d].append((va, "jcc rel32"))
    res["A1"] = {"scan_bytes": scan_bytes, "text_va": [hex(scan_start), hex(scan_end)],
                 "call_43B740": {"n": len(hits[CTOR_A]), "sites": [hex(x) for x in hits[CTOR_A]]},
                 "call_43B680": {"n": len(hits[CTOR_B]), "sites": [hex(x) for x in hits[CTOR_B]]},
                 "nonE8_transfers": {hex(k): [[hex(a), t] for a, t in v] for k, v in alt.items()},
                 "ctor_A_first_bytes": b[off(CTOR_A):off(CTOR_A) + 8].hex()}

    # ---------- 函数边界：从 host 线性反汇编到最后一条 ret 的 end ----------
    def function_at(h):
        ins = list(md.disasm(b[off(h):off(h) + 0x8000], h))
        rets = [x for x in ins if x.mnemonic.startswith("ret")]
        fn_end = rets[0].address + rets[0].size
        return [x for x in ins if x.address < fn_end], fn_end

    # ---------- 独立判定“函数起点”：向前跳过 0xCC/0x90 填充，且其前一条指令必须是 ret/jmp ----------
    def hva(fo_):
        return tlo + (fo_ - tx["rp"])

    def discover_start(va, max_back=0x200):
        o = off(va); p = o
        while p > 0 and b[p - 1] in (0x90, 0xCC) and (o - p) < max_back:
            p -= 1
        if p == o:
            return None   # 前一字节不是填充：不向前扩，不认作起点
        # 反向解：从 p 前的窗口内找一条 ret/jmp，其 end 恰为 p，且它本身是线性解码的指令起点
        for back in range(1, 24):
            st = p - back
            if st <= 0:
                break
            cand = list(md.disasm(b[st:p], hva(st)))
            if cand and cand[-1].address + cand[-1].size == hva(p) and (cand[-1].mnemonic.startswith("ret") or cand[-1].mnemonic == "jmp"):
                return hva(p)
        return None

    # ---------- 每个 ctor 调用点的 host / fn_end（与执行方按字节对齐比对）----------
    def host_of(site):
        # 独立口径：从 site 向前找“上一字节是 ret/填充/本函数首字节”的边界，再用线性反汇编验证 site 落在指令边界
        # 这里采用可验证性最强的口径：执行方所报 host 全部用线性反汇编复核（A4）
        return None

    # ---------- A2/A4：链条逐指令 ----------
    host_disc = discover_start(HOST_DECLARED)   # None = 声明值不是函数入口
    # 填充区间长度（字节实测）
    PRED_RET_END = 0x5A6502     # 字节实测：0x5A64FF c2 04 00 (ret 4) 之后
    PRED_PAD = 0x5A6510 - PRED_RET_END   # 14 字节 0x90 填充
    assert b[off(0x5A64FF):off(0x5A64FF) + 3].hex() == "c20400"
    assert set(b[off(PRED_RET_END):off(0x5A6510)]) == {0x90}
    if host_disc is None:
        # 声明值不是入口：以真实入口 0x5A6510 继续，同时记录不一致
        host_disc = 0x5A6510
        real_start_evidence = "0x5A64FF ret 4;0x5A6502..0x5A650F 14x NOP;0x5A6510 sub esp,0x70 序言"
    else:
        real_start_evidence = "declared==discovered"
    ins, fn_end = function_at(host_disc)
    # 0x5A652D 是否落在一条指令内部（=不是函数入口）
    probe_start = max(tlo, HOST_DECLARED - 8)
    lin = list(md.disasm(b[off(probe_start):off(HOST_DECLARED) + 8], probe_start))
    # 从更早的确定边界（前一条 ret）起线性解，看 0x5A652D 是否出现为指令起点
    res["A4"] = {"host_declared": hex(HOST_DECLARED), "host_discovered": hex(host_disc),
                 "start_evidence": real_start_evidence,
                 "bytes_before_declared": b[off(HOST_DECLARED) - 8:off(HOST_DECLARED)].hex(),
                 "padding_run_len": PRED_PAD, "padding_va": [hex(PRED_RET_END), hex(HOST_DECLARED)], "padding_bytes": b[off(PRED_RET_END):off(PRED_RET_END)+PRED_PAD].hex(),
                 "predecessor_ret_end": hex(PRED_RET_END), "predecessor_bytes": b[off(PRED_RET_END)-8:off(PRED_RET_END)].hex(),
                 "predecessor_insns": [ (hex(x.address), x.bytes.hex(), x.mnemonic, x.op_str) for x in list(md.disasm(b[off(PRED_RET_END)-12:off(PRED_RET_END)], PRED_RET_END-12)) ],
                 "declared_insn_start_in_linear_from_discovered": any(x.address == HOST_DECLARED for x in ins),
                 "fn_end": hex(fn_end), "nfns_decoded": 1, "insn_count": len(ins),
                 "first_insn": [hex(ins[0].address), ins[0].bytes.hex(), ins[0].mnemonic, ins[0].op_str],
                 "site_in_range": host_disc <= 0x5A6860 < fn_end,
                 "range": [hex(host_disc), hex(fn_end)]}
    by_addr = {x.address: i for i, x in enumerate(ins)} if False else None
    idx = {x.address: i for i, x in enumerate(ins)}

    def row(x):
        return {"va": hex(x.address), "bytes": x.bytes.hex(), "mnemonic": x.mnemonic, "op_str": x.op_str}

    chain_addrs = [0x5A66D4, 0x5A66D9, 0x5A684D, 0x5A6860]
    chain = []
    for a in chain_addrs:
        i = idx.get(a)
        chain.append(row(ins[i]) if i is not None else {"va": hex(a), "missing": True})
    # 0x5A66D4 的 rel32 独立解算
    o = off(0x5A66D4)
    rel = struct.unpack_from("<i", b, o + 1)[0]
    call_dst = 0x5A66D4 + 5 + rel
    # 0x5A6860 的 FF 92 disp32
    o2 = off(0x5A6860)
    disp = struct.unpack_from("<I", b, o2 + 2)[0]
    res["A2"] = {"chain": chain,
                 "call_rel32": {"site": "0x5A66D4", "bytes": b[o:o + 5].hex(), "rel32": rel, "dst": hex(call_dst)},
                 "ff92_disp32": {"site": "0x5A6860", "bytes": b[o2:o2 + 6].hex(), "disp": hex(disp),
                                 "modrm_rm": "edx"}}

    # ebp/edx 写点全量统计（函数体内）
    def writes(reg):
        w = []
        for x in ins:
            if not x.operands:
                continue
            d = x.operands[0]
            if d.type == capstone.CS_OP_REG and md.reg_name(d.reg) == reg:
                # 判断是否真写
                if x.mnemonic in ("cmp", "test"):
                    continue
                w.append(row(x) | {"effect": "write"})
            elif x.mnemonic == "pop" and d.type == capstone.CS_OP_REG and md.reg_name(d.reg) == reg:
                w.append(row(x) | {"effect": "write"})
            elif x.mnemonic in ("push",) and d.type == capstone.CS_OP_REG and md.reg_name(d.reg) == reg:
                w.append(row(x) | {"effect": "read"})
        return w

    ebp_w = writes("ebp")
    edx_w = [x for x in writes("edx")]
    res["reg_writes"] = {"ebp": ebp_w, "edx": edx_w}

    # 关键窗口 1：0x5A66D9(8B E8) 之后，到 0x5A6860 之前，ebp 的写点
    win = [x for x in ebp_w if 0x5A66D9 < int(x["va"], 16) <= 0x5A6860 and x["effect"] == "write"]
    # 关键窗口 2：0x5A684D(8B 55 00) 之后，到 0x5A6860 之前，edx 的写点
    win2 = [x for x in edx_w if 0x5A684D < int(x["va"], 16) < 0x5A6860 and x["effect"] == "write"]
    # 两个窗口内是否存在“可以进入窗口内部”的分支目标（可跳过写点/可改变 ebp）
    branches = []
    for x in ins:
        if x.mnemonic.startswith("j") and x.op_str.startswith("0x"):
            t = int(x.op_str, 16)
            if 0x5A66D9 <= t <= 0x5A6860 or 0x5A684D < t < 0x5A6860:
                branches.append(row(x) | {"target": hex(t)})
    res["A2"]["ebp_writes_between_5A66D9_and_5A6860"] = win
    res["A2"]["edx_writes_between_5A684D_and_5A6860"] = win2
    res["A2"]["branches_into_windows"] = branches

    # 跨窗口可达性（正向图，BFS）：从 0x5A66D9 出发，哪些栈帧内 PC 可达
    reach = {}
    imports = []
    for x in ins:
        imports.append(x)

    def successors(i):
        x = ins[i]
        out = []
        if x.mnemonic.startswith("ret"):
            return out
        if x.mnemonic.startswith("j"):
            if x.op_str.startswith("0x"):
                t = int(x.op_str, 16)
                if t in idx:
                    out.append(idx[t])
            if x.mnemonic == "jmp":
                return out
        if i + 1 < len(ins):
            out.append(i + 1)
        return out

    seen = set()
    stack = [idx[0x5A66D9]]
    while stack:
        i = stack.pop()
        if i in seen or i >= len(ins):
            continue
        seen.add(i)
        stack.extend(successors(i))
    reach_addrs = sorted(ins[i].address for i in seen)
    res["A2"]["reach_from_5A66D9"] = {"n_insn": len(reach_addrs), "min": hex(min(reach_addrs)), "max": hex(max(reach_addrs)),
                                      "contains_5A684D": 0x5A684D in reach_addrs,
                                      "contains_5A6860": 0x5A6860 in reach_addrs}

    # ---------- A3：ctor 序言 vptr 写入 与 vtable 槽值 ----------
    cins, cend = function_at(CTOR_A)
    vtw = []
    for x in cins:
        if x.mnemonic == "mov" and x.op_str.startswith("dword ptr [esi],"):
            vtw.append(row(x) | {"imm": x.op_str.split(", ")[-1]})
    vt_reads = []
    for x in cins:
        if "0x7e3ebc" in x.op_str.lower():
            vt_reads.append(row(x))
    vals = [u32(b, off(VT_BUILDING + 4 * k)) for k in range(80)]
    res["A3"] = {"ctor_entry_bytes": b[off(CTOR_A):off(CTOR_A) + 8].hex(),
                 "ctor_fn_end": hex(cend), "ctor_insn_count": len(cins),
                 "esi_vptr_writes": vtw, "imm_7e3ebc_refs_in_ctor": vt_reads,
                 "vtable_va": hex(VT_BUILDING),
                 "slot73_value": hex(vals[73]), "slot72": hex(vals[72]), "slot74": hex(vals[74]),
                 "slot73_equals_target": vals[73] == TARGET,
                 "all_slots_equal_target_in_first80": [k for k, v in enumerate(vals) if v == TARGET]}
    # 0x7E3EBC 在 .rdata/.data 中作为 dword 指针被引用的次数（RTTI/COL 侧佐证）
    refs = []
    for s in secs:
        if s["name"] not in (".rdata", ".data"):
            continue
        for a in range(s["rp"], s["rp"] + s["rs"] - 4, 4):
            if u32(b, a) == VT_BUILDING:
                refs.append(s["lo"] + (a - s["rp"]))
    res["A3"]["dword_refs_to_vtable"] = [hex(x) for x in refs]

    # ---------- A5：全 .text 扫描 call [reg+0x124]，找替代对象候选 ----------
    allsites = []
    lins = list(md.disasm(b[off(tlo):off(tlo) + tx["vs"]], tlo))
    for i, x in enumerate(lins):
        if x.mnemonic == "call" and "+ 0x124]" in x.op_str:
            base = x.op_str.split("[")[1].split(" ")[0]
            ctx = []
            for y in lins[max(0, i - 10):i]:
                if y.operands and base in y.op_str:
                    ctx.append(row(y))
            allsites.append({"va": hex(x.address), "bytes": x.bytes.hex(), "op_str": x.op_str, "base": base, "ctx": ctx})
    res["A5"] = {"n_call_reg_0x124_in_text": len(allsites), "sites": allsites,
                 "host_members": [s["va"] for s in allsites if host_disc <= int(s["va"], 16) < fn_end]}

    # 所有把 0x7E3EBC 写进内存的立即数点（谁可能造出同 vptr 对象）
    imm_pts = []
    for va in range(scan_start, scan_end - 6):
        o = off(va)
        if b[o] in (0xC7,):
            if b[o + 1] == 0x06 and u32(b, o + 2) == VT_BUILDING:
                imm_pts.append(hex(va))
            if (b[o + 1] & 0xC7) == 0x06 and (b[o + 1] & 0x38) == 0x00:
                pass
    # 通用：搜索 .text 内所有包含立即数 0x007E3EBC 的位置，并判定指令归属
    imm_all = []
    for va in range(scan_start, scan_end - 4):
        o = off(va)
        if u32(b, o) == VT_BUILDING:
            imm_all.append(hex(va))
    res["A5"]["imm_vptr_sites"] = imm_all
    res["A5"]["mov_esi_imm_vptr"] = imm_pts

    (OUT / "_audit_result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("image",)}, ensure_ascii=False))
    print("A1", res["A1"]["call_43B740"]["n"], res["A1"]["call_43B680"]["n"], "scan", res["A1"]["scan_bytes"])
    print("A2 chain", [(c["va"], c["bytes"], c["mnemonic"], c.get("op_str")) for c in chain])
    print("A2 ebp writes in window", win)
    print("A2 edx writes in window", win2)
    print("A2 branches into window", branches)
    print("A2 reach", res["A2"]["reach_from_5A66D9"])
    print("A3 vptr writes", vtw, "slot73", res["A3"]["slot73_value"])
    print("A4", res["A4"])
    print("A5 n sites", len(allsites), "imm vptr sites", imm_all)


if __name__ == "__main__":
    main()
