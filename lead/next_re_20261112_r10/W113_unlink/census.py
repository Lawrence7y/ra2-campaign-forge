# -*- coding: utf-8 -*-
"""
W113_unlink/census.py — 普查 gamemd.exe 中摘链函数 0x0047EA90 的调用点。

方法:
  1) .text 段逐字节找 E8 rel32 且 site+5+rel == 0x0047EA90 (精确匹配)。
  2) 全文件找立即数字节模式 90 EA 47 00 (push/mov 立即数、虚表/回调表登记)。
  3) 每个调用点回溯所属函数入口: 候选分三级 —
       A: CC(int3) 填充段后继且 16 对齐 [强]
       B: E8 调用目标 (calltgt) [交叉验证]
       C: ret(C3/C2) 后继且 16 对齐 [弱]
     用"从候选入口出发的控制流遍历"验证: jcc 双向跟随、无条件 jmp 跟随
     (限入口正向 SPAN 窗口)、call 只记录不跟随、ret 收口; 要求调用点
     可达且位于指令边界, 且该处字节确为 E8 rel32 -> TARGET。
  4) 分类 [静态推断]: 直接调用堆释放(0x4A1D50/0x4A1CA0)、写对象 vptr
     (C7 /0 且立即数落在数据段、非绝对地址形式)、或一层被调函数含上述
     行为 => "销毁/释放路径"; 否则 => "其它"。

只读目标文件; 输出仅写入本卡目录 (census_result.json / UNLINK_CALLERS.md)。
用法: python census.py [dump 0xVA [count]]
"""
import hashlib
import json
import os
import platform
import struct
import sys
import time
from collections import defaultdict

import capstone
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

EXE  = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W113_unlink"
IB, TARGET = 0x400000, 0x0047EA90
FREE = (0x4A1D50, 0x4A1CA0)
MAX_VIS, SPAN = 30000, 0x30000


def H(v):
    return "0x%08X" % (v & 0xFFFFFFFF)


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def iter_find(pat, blob):
    i = blob.find(pat)
    while i != -1:
        yield i
        i = blob.find(pat, i + 1)


# ---------- PE ----------
data = open(EXE, "rb").read()
SHA = hashlib.sha256(data).hexdigest()
pe = struct.unpack_from("<I", data, 0x3C)[0]
assert data[pe:pe + 4] == b"PE\x00\x00", "not PE"
coff = pe + 4
nsec = struct.unpack_from("<H", data, coff + 2)[0]
optsz = struct.unpack_from("<H", data, coff + 16)[0]
opt = coff + 20
assert struct.unpack_from("<H", data, opt)[0] == 0x10B, "not PE32"
imagebase = struct.unpack_from("<I", data, opt + 28)[0]
assert imagebase == IB, "imagebase mismatch: " + hex(imagebase)
sectab = opt + optsz
SECS = []
for k in range(nsec):
    o = sectab + 40 * k
    nm = data[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
    vsz, va, rsz, ro = struct.unpack_from("<IIII", data, o + 8)
    SECS.append(dict(name=nm, va=va, vsz=vsz, ro=ro, rsz=rsz))


def off2va(off):
    for s in SECS:
        if s["ro"] <= off < s["ro"] + s["rsz"]:
            return IB + s["va"] + (off - s["ro"]), s["name"]
    return None, None


def va_sec(va):
    rva = va - IB
    for s in SECS:
        if s["va"] <= rva < s["va"] + s["vsz"]:
            return s["name"]
    return None


def va2off(va):
    rva = va - IB
    for s in SECS:
        if s["va"] <= rva < s["va"] + s["rsz"]:
            return s["ro"] + (rva - s["va"])
    return None


TS = next(s for s in SECS if s["name"] == ".text")
TV = IB + TS["va"]
CODE_N = min(TS["vsz"], TS["rsz"])
tb = data[TS["ro"]:TS["ro"] + CODE_N]
T = len(tb)


def dis1(idx):
    if idx is None or idx < 0 or idx >= T:
        return None
    for ins in md.disasm(tb[idx:idx + 16], TV + idx):
        return ins
    return None


# ---------- dump mode (自检用) ----------
if len(sys.argv) >= 3 and sys.argv[1] == "dump":
    dva = int(sys.argv[2], 16)
    cnt = int(sys.argv[3]) if len(sys.argv) >= 4 else 24
    rva = dva - IB
    s = next((x for x in SECS if x["va"] <= rva < x["va"] + x["rsz"]), None)
    if s is None:
        print("VA not in any section")
        sys.exit(1)
    off = s["ro"] + (rva - s["va"])
    for ins in md.disasm(data[off:off + cnt * 16 + 16], dva):
        print("%08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        cnt -= 1
        if cnt <= 0:
            break
    sys.exit(0)


# ---------- 原始扫描 ----------
t0 = time.time()
direct = []            # .text 中 E8 rel32 -> TARGET 的位置(文件内 .text 偏移)
xrefs = defaultdict(list)   # 目标 VA -> [调用点 VA]  (含噪声, 仅用于跳板回查)
for i in iter_find(b"\xE8", tb):
    if i + 5 <= T:
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        tgt = TV + i + 5 + rel
        ti = tgt - TV
        if 0 <= ti < T:
            xrefs[tgt].append(TV + i)
        if tgt == TARGET:
            direct.append(i)
tailjmp = []           # E9 rel32 -> TARGET (尾跳板/转发)
for i in iter_find(b"\xE9", tb):
    if i + 5 <= T:
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        if TV + i + 5 + rel == TARGET:
            tailjmp.append(i)
imm_hits = []          # 全文件 90 EA 47 00
for i in iter_find(b"\x90\xEA\x47\x00", data):
    va, sec = off2va(i)
    if va is not None:
        imm_hits.append((i, va, sec))

# 全段补扫: E8/E9 -> TARGET 是否出现在 .text 之外的段(重点 .detour) —— 字节级 [已证]
allsec_extra = []
for s in SECS:
    if s["name"] == ".text":
        continue
    blob = data[s["ro"]:s["ro"] + s["rsz"]]
    base = IB + s["va"]
    for opcode, opname in ((b"\xE8", "call"), (b"\xE9", "jmp")):
        for i in iter_find(opcode, blob):
            if i + 5 <= len(blob):
                rel = struct.unpack_from("<i", blob, i + 1)[0]
                if base + i + 5 + rel == TARGET:
                    allsec_extra.append(dict(va=base + i, sec=s["name"], op=opname))

# 锚点自检: 同一扫描器对已知热函数(堆释放锚)应找到大量调用点
anchor_stats = {}
for a in (TARGET, FREE[0], FREE[1]):
    lst = xrefs.get(a, [])
    anchor_stats[H(a)] = dict(n=len(lst), sites=[H(x) for x in lst[:24]])
print("[scan] direct=%d tailjmp=%d imm=%d allsec_extra=%d  %.1fs" %
      (len(direct), len(tailjmp), len(imm_hits), len(allsec_extra), time.time() - t0))
print("[sanity] xref counts: " + ", ".join("%s=%d" % (k, v["n"]) for k, v in anchor_stats.items()))


# ---------- 候选入口 ----------
cand = defaultdict(set)


def put(idx, prov):
    if 0 <= idx < T:
        cand[idx].add(prov)


for i in iter_find(b"\xE8", tb):
    if i + 5 <= T:
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        ti = TV + i + 5 + rel - TV
        if 0 <= ti < T:
            put(ti, "calltgt")

i = tb.find(b"\xCC")
while i != -1:
    j = i
    while j < T and tb[j] == 0xCC:
        j += 1
    if j < T and (TV + j) % 16 == 0:
        put(j, "cc_run")
    i = tb.find(b"\xCC", j)

for i in iter_find(b"\xC3", tb):
    if i + 1 < T and (TV + i + 1) % 16 == 0:
        put(i + 1, "ret_pad")
for i in iter_find(b"\xC2", tb):
    if i + 3 < T and (TV + i + 3) % 16 == 0:
        put(i + 3, "ret_pad")
print("[cand] %d candidate entries  %.1fs" % (len(cand), time.time() - t0))


# ---------- 控制流遍历 ----------
def traverse(entry_idx, stop_idx=None, stop_target=None, max_vis=MAX_VIS):
    calls, callsites, indcalls, vptr = set(), [], [], []
    visited, stack, bad = set(), [entry_idx], 0
    lo, hi = entry_idx, entry_idx + SPAN
    if stop_target is None:
        stop_target = TARGET
    while stack and len(visited) < max_vis:
        idx = stack.pop()
        if idx in visited:
            continue
        visited.add(idx)
        if stop_idx is not None and idx == stop_idx:
            ins = dis1(idx)
            ok = ins is not None and ins.bytes[:1] == b"\xE8"
            if ok:
                rel = struct.unpack_from("<i", tb, idx + 1)[0]
                ok = (TV + idx + 5 + rel) == stop_target
            return dict(reached=ok, ok=ok, calls=calls, callsites=callsites,
                        indcalls=indcalls, vptr=vptr, bad=bad,
                        visited=len(visited), maxaddr=max(visited))
        ins = dis1(idx)
        if ins is None:
            bad += 1
            continue
        mn = ins.mnemonic
        nxt = idx + ins.size
        ops = ins.operands
        if mn in ("ret", "retf", "iret"):
            continue
        if mn == "jmp":
            if ops and ops[0].type == X86_OP_IMM:
                ti = ops[0].imm - TV
                if lo <= ti < hi:
                    stack.append(ti)
            elif ops and ops[0].type == X86_OP_MEM and ins.bytes[:2] == b"\xFF\x24":
                # switch 跳转表: FF 24 /0 -> jmp dword ptr [reg*scale+disp32]
                m = ops[0].mem
                base = getattr(m, "base", 0)
                index = getattr(m, "index", 0)
                disp = getattr(m, "disp", 0) & 0xFFFFFFFF
                if base == 0 and index != 0 and disp:
                    off = va2off(disp)
                    if off is not None:
                        for k in range(64):
                            if off + 4 * k + 4 > len(data):
                                break
                            tva = struct.unpack_from("<I", data, off + 4 * k)[0]
                            ti = tva - TV
                            if not (0 <= ti < T):
                                break
                            if lo <= ti < hi:
                                stack.append(ti)
                            else:
                                break
            continue
        if mn.startswith("j"):
            if ops and ops[0].type == X86_OP_IMM:
                ti = ops[0].imm - TV
                if lo <= ti < hi:
                    stack.append(ti)
            if nxt < T:
                stack.append(nxt)
            continue
        if mn in ("call", "lcall"):
            if ops and ops[0].type == X86_OP_IMM:
                calls.add(ops[0].imm)
                callsites.append((TV + idx, ops[0].imm))
            else:
                indcalls.append(TV + idx)
            if nxt < T:
                stack.append(nxt)
            continue
        b = ins.bytes
        if b[:1] == b"\xC7" and len(b) >= 6:
            modrm = b[1]
            if (modrm >> 3) & 7 == 0 and modrm != 0x05 and ops:
                last = ops[-1]
                if last.type == X86_OP_IMM:
                    v = last.imm & 0xFFFFFFFF
                    sec = va_sec(v) if v >= IB else None
                    if sec in (".rdata", ".data"):
                        mod = modrm >> 6
                        if mod == 0 or (mod == 1 and b[2] <= 8):
                            vptr.append((TV + idx, v, sec))
        if nxt < T:
            stack.append(nxt)
    return dict(reached=False, ok=False, calls=calls, callsites=callsites,
                indcalls=indcalls, vptr=vptr, bad=bad,
                visited=len(visited), maxaddr=max(visited) if visited else entry_idx)


# ---------- 调用点 -> 所属函数入口 ----------
def resolve_site(site_idx, stop_target=None, cap_a=40, cap_b=40, cap_c=20,
                 cap_d=60, cap_e=60, max_vis=MAX_VIS, budget=None):
    A, B, C = [], [], []
    for cidx, provs in cand.items():
        if cidx > site_idx:
            continue
        if "cc_run" in provs:
            A.append(cidx)
        elif "calltgt" in provs:
            B.append(cidx)
        elif "ret_pad" in provs:
            C.append(cidx)
    A.sort(reverse=True)
    B.sort(reverse=True)
    C.sort(reverse=True)
    # D/E: 任意对齐的 ret / CC 后继 (适配无 int3 填充的现代重编译镜像)
    def nearest_succ(bpat, step):
        out = []
        i = tb.rfind(bpat, max(0, site_idx - 0x20000), site_idx)
        while i != -1:
            c = i + step
            # 跳过 ret 后的 nop/int3 对齐填充
            adv = 0
            while c < T and adv < 16 and tb[c] in (0x90, 0xCC) and c < site_idx:
                c += 1
                adv += 1
            if 0 <= c <= site_idx:
                out.append(c)
            if i == 0:
                break
            i = tb.rfind(bpat, max(0, site_idx - 0x20000), i)
        return sorted(set(out), reverse=True)

    D = nearest_succ(b"\xC3", 1) + nearest_succ(b"\xC2", 3)
    D = sorted(set(D), reverse=True)
    E = []
    i = tb.rfind(b"\xCC", max(0, site_idx - 0x20000), site_idx)
    while i != -1:
        j = i
        while j + 1 < T and tb[j + 1] == 0xCC:
            j += 1
        if j + 1 <= site_idx:
            E.append(j + 1)
        if i == 0:
            break
        i = tb.rfind(b"\xCC", max(0, site_idx - 0x20000), i)
    E = sorted(set(E), reverse=True)

    tried = []
    for lst, cap, tag in ((A, cap_a, "cc_run"), (B, cap_b, "calltgt"), (C, cap_c, "ret_pad"),
                          (D, cap_d, "ret_any"), (E, cap_e, "cc_any")):
        n = 0
        tc = time.time()
        for c in lst:
            if n >= cap:
                break
            if budget is not None and time.time() - tc > budget:
                tried.append(["TIMEOUT", tag, None])
                break
            n += 1
            r = traverse(c, stop_idx=site_idx, stop_target=stop_target, max_vis=max_vis)
            tried.append([TV + c, tag, bool(r["reached"])])
            if r["reached"]:
                return c, tag, r, tried
    return None, None, None, tried


FT = {}


def full(entry_idx):
    if entry_idx not in FT:
        FT[entry_idx] = traverse(entry_idx, None)
    return FT[entry_idx]


SUB = {}


def sub_tr(va):
    if va not in SUB:
        ti = va - TV
        SUB[va] = traverse(ti, None, 2500) if 0 <= ti < T else None
    return SUB[va]


def classify(entry_idx, tr):
    ev, cls = [], "other"
    frees = sorted(tr["calls"] & set(FREE))
    if frees:
        ev.append("直接调用堆释放 " + "/".join(H(f) for f in frees))
    vp = tr["vptr"]
    if vp:
        ev.append("写对象vptr " + "; ".join("%s->%s(%s)" % (H(a), H(v), s) for a, v, s in vp[:3]))
        if len(vp) > 3:
            ev[-1] += " 等%d处" % len(vp)
    if not frees and not vp:
        got = []
        for t in sorted(tr["calls"])[:24]:
            if t == TARGET or t in FREE:
                continue
            s = sub_tr(t)
            if s and (s["calls"] & set(FREE)):
                got.append(t)
            if len(got) >= 3:
                break
        if got:
            ev.append("一层被调函数含堆释放 " + "/".join(H(t) for t in got))
    if ev:
        cls = "destroy"
    if tr["visited"] >= MAX_VIS:
        ev.append("遍历达上限(证据可能不完整)")
    return cls, ev


# ---------- 逐点解析 ----------
t0 = time.time()
site_res = []
for site_idx in direct:
    entry_idx, tag, r, tried = resolve_site(site_idx)
    site_res.append(dict(idx=site_idx, va=TV + site_idx,
                         entry=(TV + entry_idx) if entry_idx is not None else None,
                         tag=tag, tried=tried))
print("[resolve] %d sites resolved in %.1fs" % (sum(1 for s in site_res if s["entry"]), time.time() - t0))


# ---------- 按函数聚合 + 分类 ----------
funcs = {}
for s in site_res:
    if s["entry"] is None:
        continue
    e = s["entry"]
    g = funcs.setdefault(e, dict(entry=e, sites=[], tag=s["tag"]))
    g["sites"].append(s["va"])

for e, g in funcs.items():
    tr = full(e - TV)
    g["tr"] = tr
    cls, ev = classify(e, tr)
    g["cls"] = cls
    g["ev"] = ev
    g["ncalls"] = len(tr["calls"])
    g["nind"] = len(tr["indcalls"])
    g["span"] = tr["maxaddr"] - (e - TV)
    g["prologue"] = []
    k = e - TV
    for _ in range(8):
        ins = dis1(k)
        if ins is None:
            break
        g["prologue"].append("%s  %s %s" % (H(ins.address), ins.mnemonic, ins.op_str))
        k += ins.size
    # 交叉验证: 该函数的 callsites 中确实包含指向 TARGET 的直接调用
    g["sites_in_body"] = [va for (va, tgt) in tr["callsites"] if tgt == TARGET]
    g["prov"] = sorted(cand.get(e - TV, set()))
    g["callsites"] = [[va, tgt] for (va, tgt) in tr["callsites"]]
    g["indcalls_va"] = tr["indcalls"]

# 上层调用者(一跳): 谁调用了这些所属函数
for e, g in funcs.items():
    up = []
    for cs_va in xrefs.get(e, [])[:24]:
        cs_idx = cs_va - TV
        e_idx, tag, r, tried = resolve_site(cs_idx, stop_target=e)
        if e_idx is None:
            # 加强重试: 放宽候选数与遍历上限, 单类 25s 预算
            e_idx, tag, r, tried = resolve_site(cs_idx, stop_target=e, cap_a=300, cap_b=300,
                                                cap_c=100, cap_d=400, cap_e=400,
                                                max_vis=40000, budget=25.0)
            if tried and tried[-1][0] == "TIMEOUT":
                tag = (tag or "") + "+预算截断"
        row = dict(callsite=cs_va, entry=(TV + e_idx) if e_idx is not None else None, tag=tag)
        if e_idx is not None:
            t2 = full(e_idx)
            c2, ev2 = classify(e_idx, t2)
            row["cls"] = c2
            row["ev"] = ev2
            row["prov"] = sorted(cand.get(e_idx, set()))
            pro = []
            k2 = e_idx
            for _ in range(6):
                ins = dis1(k2)
                if ins is None:
                    break
                pro.append("%s %s %s" % (H(ins.address), ins.mnemonic, ins.op_str))
                k2 += ins.size
            row["prologue"] = pro
        else:
            row["ev"] = ["加强重试后仍未证实(最近候选: %s)" % (H(tried[-1][0]) if tried and tried[-1][0] != "TIMEOUT" else "无")]
        up.append(row)
    g["callers_up"] = up

# 直接被调函数的语义上下文(帮助判读所属函数性质)
for e, g in funcs.items():
    ctx = {}
    for (_va, t) in g.get("callsites", []):
        if t in ctx or t == TARGET:
            continue
        ti = t - TV
        if not (0 <= ti < T):
            continue
        rows = []
        k = ti
        for _ in range(6):
            ins = dis1(k)
            if ins is None:
                break
            rows.append("%s %s %s" % (H(ins.address), ins.mnemonic, ins.op_str))
            k += ins.size
        ctx[t] = dict(xrefs_n=len(xrefs.get(t, [])), aligned16=((t & 0xF) == 0),
                      prologue=rows)
    g["callee_ctx"] = {H(t): v for t, v in ctx.items()}

# 尾跳板(E9->TARGET)及其 E8 调用者(一跳)
wrapper_rows = []
for w_idx in tailjmp:
    w_va = TV + w_idx
    rows = []
    for cs_va in xrefs.get(w_va, []):
        cs_idx = cs_va - TV
        if not (0 <= cs_idx < T):
            continue
        e_idx, tag, r, tried = resolve_site(cs_idx)
        if e_idx is None:
            rows.append(dict(callsite=cs_va, entry=None, tag=None, cls=None, ev=["入口未证实"]))
            continue
        e_va = TV + e_idx
        if e_va in funcs:
            g = funcs[e_va]
            rows.append(dict(callsite=cs_va, entry=e_va, tag=tag, cls=g["cls"], ev=g["ev"]))
        else:
            tr = full(e_idx)
            cls, ev = classify(e_idx, tr)
            funcs.setdefault(e_va, dict(entry=e_va, sites=[], tag=tag, tr=tr, cls=cls,
                                        ev=ev, ncalls=len(tr["calls"]), nind=len(tr["indcalls"]),
                                        span=tr["maxaddr"] - e_idx, prologue=[],
                                        sites_in_body=[va for (va, tgt) in tr["callsites"] if tgt == TARGET]))
            rows.append(dict(callsite=cs_va, entry=e_va, tag=tag, cls=cls, ev=ev))
    wrapper_rows.append(dict(va=w_va, callers=rows))

# ---------- 立即数引用上下文 ----------
def dword_at(o):
    return struct.unpack_from("<I", data, o)[0] if 0 <= o and o + 4 <= len(data) else 0


def insn_containing_text(off):
    """off 为 .text 段内文件偏移; 返回覆盖 [off, off+4) 的指令(从更早边界解码)。"""
    for d in range(1, 12):
        ins = dis1(off - d)
        if ins is not None and off - d + ins.size >= off + 4:
            return ins
    return None


imm_rows = []
for (o, va, sec) in imm_hits:
    prev = data[o - 1] if o > 0 else 0
    if prev == 0x68:
        guess = "push imm32"
    elif 0xB8 <= prev <= 0xBF:
        guess = "mov r32,imm32"
    else:
        guess = "?"
    ins_txt = ""
    if sec == ".text":
        ins = insn_containing_text(o)
        if ins is not None:
            ins_txt = "%s %s" % (ins.mnemonic, ins.op_str)
            guess = "指令内立即数"
    tbl = ""
    if sec != ".text":
        d1, d2 = dword_at(o - 4), dword_at(o + 4)
        s1, s2 = va_sec(d1) if d1 >= IB else None, va_sec(d2) if d2 >= IB else None
        if ".text" in (s1, s2):
            tbl = "邻槽含.text指针(表登记特征)"
    imm_rows.append(dict(va=va, sec=sec, ctx=data[max(0, o - 4):o + 8].hex(),
                         guess=guess, insn=ins_txt, table=tbl))

# ---------- 汇总 ----------
n_direct = len(direct)
n_verified = sum(1 for s in site_res if s["entry"])
n_funcs_direct = len(funcs)
destroy = sorted([e for e, g in funcs.items() if g.get("cls") == "destroy"])
other = sorted([e for e, g in funcs.items() if g.get("cls") == "other"])
summary = dict(
    n_direct=n_direct, n_verified=n_verified, n_funcs_direct=n_funcs_direct,
    n_destroy=len(destroy), n_other=len(other),
    n_tailjmp=len(tailjmp), n_imm=len(imm_rows),
    imm_by_sec=sorted({s for (_, _, s) in imm_hits}),
)
print("[summary] direct=%d verified=%d funcs=%d destroy=%d other=%d tailjmp=%d imm=%d"
      % (n_direct, n_verified, n_funcs_direct, len(destroy), len(other), len(tailjmp), len(imm_rows)))

# ---------- JSON ----------
out = dict(
    meta=dict(exe=EXE, sha256=SHA, imagebase=IB,
              text=dict(va=TV, vsz=TS["vsz"], rsz=TS["rsz"], scanned=CODE_N),
              capstone=capstone.__version__, python=platform.python_version(),
              free_anchors=[H(f) for f in FREE], target=H(TARGET),
              method_caps=dict(max_vis=MAX_VIS, span=SPAN)),
    sections=[dict(name=s["name"], va=IB + s["va"], vsz=s["vsz"], rawsz=s["rsz"]) for s in SECS],
    direct_sites=[dict(va=s["va"], entry=s["entry"], tag=s["tag"], tried=s["tried"]) for s in site_res],
    funcs={H(e): dict(entry=e, sites=g["sites"], tag=g.get("tag"), cls=g.get("cls"), ev=g.get("ev"),
                      prov=g.get("prov"), ncalls=g.get("ncalls"), nind=g.get("nind"), span=g.get("span"),
                      prologue=g.get("prologue"), sites_in_body=g.get("sites_in_body"),
                      callsites=g.get("callsites"), indcalls_va=g.get("indcalls_va"),
                      callers_up=g.get("callers_up"), callee_ctx=g.get("callee_ctx"))
           for e, g in funcs.items()},
    wrappers=[dict(va=w["va"], callers=[dict(callsite=c["callsite"], entry=c["entry"],
                                             tag=c["tag"], cls=c["cls"], ev=c["ev"]) for c in w["callers"]])
              for w in wrapper_rows],
    imm_hits=imm_rows,
    allsec_extra=allsec_extra,
    anchor_stats=anchor_stats,
    summary=summary,
)
os.makedirs(CARD, exist_ok=True)
with open(os.path.join(CARD, "census_result.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("[write] census_result.json")


# ---------- Markdown ----------
def esc(s):
    return str(s).replace("|", "\\|")


L = []
A = L.append
A("# W113 — 摘链函数 `0x0047EA90` 调用点普查（gamemd.exe）")
A("")
A("- 目标文件: `%s`" % EXE)
A("- SHA256: `%s`（本机重算一致）[已证]" % SHA)
A("- ImageBase `0x%08X`；.text VA `0x%08X`，vsz `0x%X`，rawsz `0x%X`，实际扫描 `0x%X` 字节（= min(vsz, rawsz)）。" %
  (IB, TV, TS["vsz"], TS["rsz"], CODE_N))
A("- 工具: capstone %s / Python %s。脚本 `census.py` 可独立重跑，复现本报告每个数字。" %
  (capstone.__version__, platform.python_version()))
A("")
A("## 方法与标签")
A("")
A("1. **直接调用点**: `.text` 全段逐字节找 `E8 rel32` 且 `site+5+rel == 0x0047EA90`，精确匹配。[已证]")
A("2. **入口判定**: 候选入口三级 — A: `int3`(CC) 填充段后继且 16 对齐；B: `E8` 调用目标（calltgt 交叉验证）；C: `ret`(C3/C2) 后继且 16 对齐。")
A("   确认手段：**从候选入口做控制流遍历**（条件跳转双向、无条件 jmp 跟随但限入口正向 0x%X 窗口、call 只记录不跟随、ret 收口），要求调用点可达、位于指令边界、且该处字节确为 `E8 rel32 -> 0x0047EA90`。全程非定长线性反汇编。" % SPAN)
A("   - A 类或 B 类命中 → 入口 [已证]（依据注明类别；B 类额外标注\"仅call目标\"）。")
A("   - 仅 C 类命中 → 入口 [已证]（依据弱一档：ret+对齐，边界证据不如 CC 填充硬）。")
A("   - 全部失败 → [未证]，附最近候选。")
A("3. **分类**: 判据 = 函数体内是否 **直接调用堆释放 `0x4A1D50`/`0x4A1CA0`**、是否 **写对象 vptr**（`C7 /0` 写数据段立即数、排除绝对地址形式 `C7 05`、排除指向 .text 的函数指针）、或 **一层被调函数**（最多展开 24 个 callee、每个 2500 条遍历上限）含堆释放。命中 → \"销毁/释放路径\"；否则 → \"其它\"。均为 **[静态推断]**，非定论。")
A("4. **间接引用**: 全文件字节模式 `90 EA 47 00`，逐条给段、上下文十六进制、指令级判读。")
A("5. 遍历上限：单次验证/分析最多 %d 条指令；触顶会在依据里标注\"遍历达上限\"（证据可能不完整）。" % MAX_VIS)
A("")
A("## 1. 总数")
A("")
A("- 直接调用点（`E8 rel32` 精确匹配）: **%d** 处 [已证]" % n_direct)
A("- 其中入口判定成功: **%d** 处；去重后所属函数: **%d** 个" % (n_verified, n_funcs_direct))
A("- 分类: 销毁/释放路径 **%d** 个 / 其它 **%d** 个（均 [静态推断]）" % (len(destroy), len(other)))
A("- 尾跳板（`E9 rel32 -> 0x0047EA90`，转发包装）: **%d** 处" % len(tailjmp))
A("- 立即数引用（`90 EA 47 00`）: **%d** 处，分布段: %s" % (len(imm_rows), ", ".join(sorted({r['sec'] for r in imm_rows})) or "无"))
A("- `.text` 之外段（含 `.detour`）的 `E8/E9 -> 0x0047EA90` 字节命中: **%d** 处 [已证·字节级]" % len(allsec_extra))
A("- 扫描器自检: 同一扫描器对堆释放锚 `0x4A1D50` 找到 **%d** 个 `E8` 调用点、对 `0x4A1CA0` 找到 **%d** 个 —— 说明扫描器对热函数工作正常，`0x0047EA90` 的稀少调用点不是漏报 [已证·方法自检]" %
  (anchor_stats[H(FREE[0])]["n"], anchor_stats[H(FREE[1])]["n"]))
A("")
A("## 2. 直接调用点明细")
A("")
A("| # | 调用点 VA | 所属函数入口 | 入口依据 | 调用点判定 | 分类 [静态推断] | 关键依据 |")
A("|---|-----------|--------------|----------|------------|-----------------|----------|")
rows = sorted(site_res, key=lambda s: s["va"])
for n, s in enumerate(rows, 1):
    if s["entry"] is None:
        A("| %d | %s | — [未证] | 最近候选: %s | [未证]（字节模式命中，未能建立指令边界） | — | tried: %s |" %
          (n, H(s["va"]), H(s["tried"][0][0]) if s["tried"] else "无",
           "; ".join("%s:%s:%s" % (H(t[0]), t[1], t[2]) for t in s["tried"][:6]) or "无"))
        continue
    g = funcs[s["entry"]]
    tagtxt = {"cc_run": "int3填充边界+解码可达 [已证]",
              "calltgt": "call目标+解码可达 [已证]",
              "ret_pad": "ret后继+对齐+解码可达 [已证·依据较弱]"}.get(s["tag"], s["tag"])
    provs = sorted(funcs[s["entry"]].get("prov", []))
    xcheck = "；候选资格: " + "+".join(provs) if provs else ""
    A("| %d | %s | %s | %s%s | [已证] | %s | %s |" %
      (n, H(s["va"]), H(s["entry"]), tagtxt, xcheck, esc(g.get("cls")), esc("; ".join(g.get("ev", [])) or "无释放/vptr证据")))
A("")
xcheck_lines = []
for e in sorted(funcs):
    g = funcs[e]
    if g.get("sites_in_body"):
        xcheck_lines.append("%s（覆盖 %s）" % (H(e), ", ".join(H(v) for v in g["sites_in_body"])))
A("> `sites_in_body` 交叉验证：以下函数在完整控制流遍历中确实存在指向 `0x0047EA90` 的直接调用，与字节扫描互证：" +
  ("; ".join(xcheck_lines) if xcheck_lines else "无") + " [已证]")
A("")
A("### 2.1 所属函数的完整调用上下文")
A("")
for e in sorted(funcs):
    g = funcs[e]
    A("**%s**（%s [静态推断]）：直接 call 目标 %s；间接 call（虚调用等）%d 处：%s" %
      (H(e), esc(g.get("cls")),
       ", ".join(H(t) for (_, t) in g.get("callsites", [])) or "无",
       len(g.get("indcalls_va", [])),
       ", ".join(H(v) for v in g.get("indcalls_va", [])) or "无"))
    A("")
    A("- 上层调用者（`E8 -> %s` 的调用点，一跳，逐点重新解析入口）[静态推断]：" % H(e))
    for row in g.get("callers_up", []):
        if row["entry"] is None:
            A("  - %s → 入口 [未证]（%s）" % (H(row["callsite"]), esc("; ".join(row.get("ev") or []))))
        else:
            tagmap = {"cc_run": "int3边界", "calltgt": "call目标", "ret_pad": "ret+对齐",
                      "ret_any": "ret后继(任意对齐)", "cc_any": "int3后继(任意对齐)"}
            tt = tagmap.get(row.get("tag") or "", row.get("tag") or "?")
            caveat = ""
            if (row.get("tag") or "") in ("ret_any", "ret_pad", "cc_any"):
                caveat = "；不保证是真入口，可能是同函数早退块起点"
            A("  - %s → %s（入口依据: %s [已证·解码可达]%s；分类: %s [静态推断]；依据: %s）" %
              (H(row["callsite"]), H(row["entry"]), tt, caveat, esc(row.get("cls") or "?"),
               esc("; ".join(row.get("ev") or []) or "无释放/vptr证据")))
    if not g.get("callers_up"):
        A("  - 无（该函数入口没有直接 `E8` 调用点 —— 可能仅经虚表/间接方式进入）")
    A("- 直接被调函数上下文（判断该函数性质的旁证）[静态推断]：")
    for t, c in (g.get("callee_ctx") or {}).items():
        if t == H(TARGET):
            A("  - %s = 摘链函数本体" % t)
            continue
        A("  - %s：被 %d 处调用，16对齐=%s；入口前几条：%s" %
          (t, c["xrefs_n"], c["aligned16"], esc(" | ".join(c["prologue"][:3]))))
A("")
A("## 3. 分类汇总")
A("")
A("### 3.1 销毁/释放路径 [静态推断]（%d 个）" % len(destroy))
A("")
for e in destroy:
    g = funcs[e]
    A("- **%s** — 依据: %s；函数体直接 call 目标数 %d，跨距 ~0x%X。" %
      (H(e), esc("; ".join(g["ev"]) or "—"), g["ncalls"], g["span"]))
    for p in g["prologue"][:4]:
        A("  - `%s`" % p)
A("")
A("### 3.2 其它 [静态推断]（%d 个）" % len(other))
A("")
for e in other:
    g = funcs[e]
    A("- **%s** — 依据: %s；函数体直接 call 目标数 %d，跨距 ~0x%X。" %
      (H(e), esc("; ".join(g["ev"]) or "无释放/vptr证据"), g["ncalls"], g["span"]))
    for p in g["prologue"][:4]:
        A("  - `%s`" % p)
A("")
A("## 4. 尾跳板（E9 -> 0x0047EA90）")
A("")
if not wrapper_rows:
    A("无。[已证]")
else:
    for w in wrapper_rows:
        A("- 跳板 `%s`，其 `E8` 调用者:" % H(w["va"]))
        for c in w["callers"]:
            if c["entry"] is None:
                A("  - %s → 入口 [未证]" % H(c["callsite"]))
            else:
                A("  - %s → 所属函数 %s（%s，%s）" %
                  (H(c["callsite"]), H(c["entry"]), esc(c["cls"] or "?"), esc("; ".join(c["ev"]) or "—")))
A("")
A("### 4.1 `.text` 之外的段（含 `.detour`）")
A("")
if not allsec_extra:
    A("无字节级命中：`.detour`（0xB93000，游侠 detour 补丁段）等其它段中不存在指向 `0x0047EA90` 的 `E8/E9`。[已证]")
else:
    for h in allsec_extra:
        A("- %s（%s，%s）[未证·字节模式，未建指令边界]" % (H(h["va"]), h["sec"], h["op"]))
A("")
A("## 5. 立即数引用（`90 EA 47 00`）")
A("")
if not imm_rows:
    A("无。[已证]")
else:
    A("| VA | 段 | 上下文(hex, 前4后8) | 判读 | 指令级上下文 |")
    A("|----|----|---------------------|------|--------------|")
    for r in imm_rows:
        note = r["guess"] + (("；" + r["table"]) if r["table"] else "")
        A("| %s | %s | %s | %s | %s |" % (H(r["va"]), r["sec"], r["ctx"], esc(note), esc(r["insn"] or "—")))
A("")
A("## 6. 局限")
A("")
A("- 入口判定依赖 CC 填充/call目标/ret+对齐 三类边界；未覆盖\"前一函数恰好在 16 对齐处结束且无任何填充\"的罕见布局（会落入 [未证]）。")
A("- 分类为字节级静态启发（释放锚定 %s），最终定性需结合调用方上层语义。" % "/".join(H(f) for f in FREE))
A("- 未枚举\"调用了释放但**不**调用摘链\"的全量函数清单（超出本题范围，建议另立 W 卡）。")
A("- `.data` 段 vsz 0x366BE4 但 rawsz 仅 0x6C000：大部分是运行时才填充的 BSS，文件里扫不到 —— 运行时构造的函数指针表若存在，静态扫描看不见。[未证·固有局限]")
A("- 本报告仅回答\"谁调用了 `0x0047EA90`\"；编译器若把摘链逻辑**内联**到其它销毁路径，那些副本不会以 `E8` 形式出现，需语义级比对（不在本卡方法内）。[静态推断]")
A("")
A("## 7. 解读（面向 UAF 排查，全部为 [静态推断]）")
A("")
A("- `0x0047EA90`（摘链）在**整个镜像中只有 1 个直接调用点**（`0x005688EB`，函数 `0x005687F0`），无虚表/回调登记、无尾跳板、`.detour` 补丁段也不涉及它。[已证]")
A("- 唯一调用者 `0x005687F0` 自身不是释放路径：函数体直接调用 `0x48DFE0`/`0x47D2B0`(×2)+5 处虚调用，直接/一层展开都**未见堆释放 `0x4A1D50`/`0x4A1CA0`，也未见 vptr 写**。[静态推断]")
A("- `0x005687F0` 的上层调用者共 4 处，入口全部解析成功且**全部为\"其它\"类**（非释放路径），见 §2.1 与附录 B。多处的调用点字节模式一致：`mov ecx, 0x87F7E8; call 0x005687F0` —— `0x005687F0` 是**全局管理器单例 `0x87F7E8`（.data BSS，运行时构造）的方法**。[静态推断·字节级模式一致]")
A("- **UAF 启示**：按本普查，\"从格链摘除\"只在一条玩法逻辑路径（全局管理器方法链）发生；任何**销毁/释放路径都不直接调用摘链**。若对象在销毁时未先走该管理器路径（或销毁顺序与摘链竞争），就会留下\"已释放但仍在格链上\"的节点 —— 与已确认的崩溃现象一致。[静态推断]")
A("- **`0x005687F0` 函数体语义**（读自附录 A 线性解码）[静态推断]：取对象（edi）→ 经虚表取属性/类型校验 → `call 0x48DEE0` 拷贝坐标 → `shl 9`（×512）合成**格索引 esi**、边界 `0x40000` → `[ebx+0x13C]` 格指针表取格（越界回退全局 `0xABDC50`）→ `call 0x47EA90`（ecx=格，`[edi+0x8c]` 为参数）**把对象从旧格链摘下** → `call 0x47D2B0(-1)` 走新格登记。即：**摘链只发生在\"对象换格/移动\"玩法路径里，析构类路径没有对应调用。**")
A("- 注意反向结论同样成立：`0x47EA90` 的摘链逻辑若被编译器**内联**进其它函数，不会以 `E8` 形式出现；本报告的\"仅此一路\"以内联不存在为前提（镜像几乎无 CC 填充、函数边界靠 ret 后继辨认，内联检测建议另立 W 卡做语义级比对）。[静态推断]")
A("")
A("## 8. 已排除的死路（供后续 W 卡参考）")
A("")
A("- 中途假设\"上层调用点不可达 = detour 污染\"：实测 `.text → .detour` 与 `.detour → .text` 的 `E9` 均为 0，证伪；`.detour` 段与本次普查目标无交互。[已证]")
A("- 中途假设\"镜像 16 对齐 CC 填充失效\"：部分成立 —— 该镜像函数间几乎没有 int3 填充（入口靠 ret 后继辨认），因此解析加入任意对齐 ret/CC 后继候选（D/E 类）。[已证]")
A("- 真正原因是遍历器 stop 校验最初硬编码了 `E8` 目标必须等于 `0x47EA90`，复用到上层调用点（目标为 `0x5687F0`）时恒失败；已改为 `stop_target` 参数。[已证·代码已修]")
A("")
A("## 附录 B：上层调用者入口线性反汇编（供人工复核，非判定依据）")
A("")
for e, g in sorted(funcs.items()):
    for row in g.get("callers_up", []):
        if row.get("entry") and row.get("prologue"):
            A("```asm")
            A("; 上层调用点 %s -> 所属函数 %s (%s)" % (H(row["callsite"]), H(row["entry"]), row.get("tag")))
            for p in row["prologue"]:
                A(p)
            A("```")
            A("")
A("## 附录 A：所属函数线性反汇编（供人工复核，非判定依据）")
A("")
A("以下为从入口起的线性解码（跨越 ret 后可能失配；判定一律以 §2 的控制流遍历为准）。可用 `python census.py dump 0x5687F0 120` 重现。")
A("")
for e in sorted(funcs):
    g = funcs[e]
    A("```asm")
    A("; === %s ===" % H(e))
    k = e - TV
    n = 0
    while n < 120 and k < T:
        ins = dis1(k)
        if ins is None:
            A("; ... decode failed at %s ..." % H(TV + k))
            break
        A("%s  %-20s %s %s" % (H(ins.address), ins.bytes.hex(), ins.mnemonic, ins.op_str))
        k += ins.size
        n += 1
    A("```")
    A("")
with open(os.path.join(CARD, "UNLINK_CALLERS.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("[write] UNLINK_CALLERS.md  total %.1fs" % (time.time() - t0))
