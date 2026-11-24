# -*- coding: utf-8 -*-
# _sc_scan.py — 静态闭口扫描 v2（零真机、零采样、纯文件只读 + capstone 静态反汇编）
# 被核对象: ra2youli/gamemd.exe（磁盘镜像只读）。唯一写域: lead/spec_static_closure_20261108/。
# 用法: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/spec_static_closure_20261108/_sc_scan.py"
import struct, hashlib, time
from bisect import bisect_right

T0 = time.time()
PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(PATH, "rb").read()
SHA = hashlib.sha256(data).hexdigest()
SIZE = len(data)
EXP_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
print("R0 SHA256", SHA)
print("R0 BYTES", SIZE)
print("R0 SHA_MATCH_CORPUS_73201cc0", SHA == EXP_SHA)

# ---------- PE 解析 ----------
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0"
coff = e_lfanew + 4
machine, nsec, _ts, _pt, _nsym, optsize, _ch = struct.unpack_from("<HHIIIHH", data, coff)
opt = coff + 20
assert struct.unpack_from("<H", data, opt)[0] == 0x10B
imagebase = struct.unpack_from("<I", data, opt + 28)[0]
sec0 = opt + optsize
SECTIONS = []
for i in range(nsec):
    o = sec0 + 40 * i
    name = data[o:o + 8].rstrip(b"\0").decode("ascii", errors="replace")
    vsize, va, rsize, raw = struct.unpack_from("<IIII", data, o + 8)
    chars = struct.unpack_from("<I", data, o + 36)[0]
    SECTIONS.append((name, va, vsize, raw, rsize, chars))
print("R0 IMAGEBASE 0x%08X" % imagebase)
for nm, va, vsz, raw, rsz, ch in SECTIONS:
    print("R0 SEC %-8s RVA=0x%06X VA=0x%08X VSZ=0x%X RAW=0x%X RSZ=0x%X CH=0x%08X" % (nm, va, imagebase + va, vsz, raw, rsz, ch))

SEC = {nm: (imagebase + va, vsz, raw, rsz) for nm, va, vsz, raw, rsz, ch in SECTIONS}

def sec_of(va):
    rva = va - imagebase
    for nm, sva, vsz, raw, rsz, ch in SECTIONS:
        if sva <= rva < sva + max(vsz, rsz):
            return nm
    return None

def va2off(va):
    rva = va - imagebase
    for nm, sva, vsz, raw, rsz, ch in SECTIONS:
        if sva <= rva < sva + max(vsz, rsz):
            d = rva - sva
            return raw + d if d < rsz else None
    return None

def is_text(va):
    return sec_of(va) == ".text"

def u32(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<I", data, o)[0]

def u64q(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<Q", data, o)[0]

def f64(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<d", data, o)[0]

def bytes_at(va, n):
    o = va2off(va)
    return None if o is None else data[o:o + n]

TEXT_VA, TEXT_VSZ, TEXT_RAW, TEXT_RSZ = SEC[".text"]
TEXT_LO, TEXT_HI = TEXT_VA, TEXT_VA + TEXT_VSZ

def file_backed(va):
    """返回该 VA 所在段的文件映射覆盖信息"""
    rva = va - imagebase
    for nm, sva, vsz, raw, rsz, ch in SECTIONS:
        if sva <= rva < sva + max(vsz, rsz):
            return (nm, imagebase + sva, imagebase + sva + rsz, imagebase + sva + max(vsz, rsz))
    return None

def find_dword_in_text(val):
    pat = struct.pack("<I", val)
    out = []
    start = TEXT_RAW
    while True:
        i = data.find(pat, start, TEXT_RAW + TEXT_RSZ)
        if i < 0:
            break
        out.append(TEXT_VA + (i - TEXT_RAW))
        start = i + 1
    return out

# ---------- 已知值校验 ----------
print("\n== VAL 已知值校验（出处=既有材料）==")
VALS = [
    (0x7F5D94, 0x4D3780, "v[73]Unit =F7T:69"),
    (0x7EB17C, 0x4D3780, "v[73]Infantry =F7T:69"),
    (0x7E8DB8, 0x4D3780, "v[73]Foot =F7T:70"),
    (0x7F4D84, 0x6FB010, "v[265]槽 =F7T:101"),
    (0x7E4280, 0x445F00, "Building vtable头 =F7T:124"),
    (0x7E9058, 0x4D9920, "Foot vtable头 =F7T:125"),
    (0x7F6094, 0x736CA0, "Unit v265 =F7T:100"),
    (0x7F4348 + 0x5C, 0x6D2540, "Tactical vtable[23] =F6V:166"),
    (0x7E3354 + 0x104, 0x422C70, "vt0x7E3354槽65 =F8V:93"),
    (0x7F5C70 + 0x104, 0x73B0B0, "vt0x7F5C70槽65 =F8V:94"),
    (0x7F6318 + 0x104, 0x749B20, "vt0x7F6318槽65 =F8V:95"),
    (0x7F5C70 + 0x27C, 0x65A970, "Unit v[159] =F7_review:173"),
]
for va, exp, tag in VALS:
    got = u32(va)
    print("VAL %-26s VA=0x%08X got=0x%08X exp=0x%08X %s" % (tag, va, got, exp, "OK" if got == exp else "FAIL"))
d900 = f64(0x7E27F8)
print("VAL qword(0x7E27F8)==900.0 =F7T:165  got=%r %s" % (d900, "OK" if d900 == 900.0 else "FAIL"))
for sv in (0x7E2640, 0x7E4258, 0x7E9030, 0x7EB3F4, 0x7F4CFC, 0x7F600C):
    got = u32(sv)
    print("VAL u32(0x%08X)==0x709820 =_f7rev3:185-190  got=0x%08X %s" % (sv, got, "OK" if got == 0x709820 else "FAIL"))
for sv, exp in ((0x826260, b"RULESMD.INI"), (0x82626C, b"RULEMD*.INI"), (0x826838, b"CONQMD.MIX")):
    got = bytes_at(sv, len(exp))
    print("VAL str(0x%08X)==%r =_audit_task12.py:51  got=%r %s" % (sv, exp, got, "OK" if got == exp else "FAIL"))

# ---------- RTTI 表（先行构建，供全局使用） ----------
print("\n== RTTI TypeDescriptor/COL/vftable ==")
td_map = {}
for nm in (".data", ".rdata"):
    sva, vsz, raw, rsz = SEC[nm]
    blob = data[raw:raw + rsz]
    start = 0
    while True:
        i = blob.find(b".?A", start)
        if i < 0:
            break
        td_va = imagebase + sva + i - 8  # 注意: 本镜像 COL 存绝对 VA；此键=imagebase+绝对TD（与 rtti_of_vftable 的读取约定一致）
        j = blob.find(b"\0", i)
        td_map[td_va] = blob[i:j if j > 0 else i + 64].decode("ascii", errors="replace")
        start = i + 1
print("RTTI TD 名=%d" % len(td_map))
rdata_lo, rdata_vsz, rdata_raw, rdata_rsz = SEC[".rdata"]
rvals = {}
blob = data[rdata_raw:rdata_raw + rdata_rsz]
for k in range(0, len(blob) - 3, 4):
    rvals.setdefault(struct.unpack_from("<I", blob, k)[0], []).append(rdata_lo + k)
print("RTTI .rdata dword 索引: %d 个不同值" % len(rvals))

def rtti_of_vftable(vt):
    col = u32(vt - 4)
    if col is None or sec_of(col) != ".rdata":
        return None
    if u32(col) != 0:
        return None
    td_field = u32(col + 12)
    name = td_map.get(imagebase + td_field) if td_field is not None else None
    if name is None:
        return None
    return (col, u32(col + 4), name)

for vt, exp_sub in ((0x7F4348, "Tactical"), (0x7E85D4, "DSurface")):
    r = rtti_of_vftable(vt)
    print("RTTI VAL vt=0x%08X -> %s (期望含 %s) %s" % (vt, r, exp_sub, "OK" if r and exp_sub in r[2] else "FAIL"))

# ---------- capstone 线性解码 .text ----------
print("\n== DEC capstone 线性解码 .text ==")
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
tdec = time.time()
call_imm = {}
call_site = {}
mem_hits = {}   # disp -> [(va, mnemonic, op_str, base_reg)]
TARGET_DISPS = (0xB0CD48, 0x7E1738, 0x39C, 0x104, 0x3C4)
ins_starts = []          # 指令起点（升序）
ins_kind = []            # 0=其他 1=ret 2=jmp-imm 3=call 4=jcc
ins_sizes = []
total = 0
resync = 0
o = TEXT_RAW
endoff = TEXT_RAW + TEXT_RSZ
while o < endoff:
    got = False
    base_addr = TEXT_VA + (o - TEXT_RAW)
    for ins in md.disasm(data[o:endoff], base_addr):
        got = True
        total += 1
        va = ins.address
        m = ins.mnemonic
        ins_starts.append(va)
        ins_sizes.append(ins.size)
        if m == "ret":
            ins_kind.append(1)
        elif m == "jmp" and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
            ins_kind.append(2)
        elif m == "call":
            ins_kind.append(3)
        elif m[0] == "j":
            ins_kind.append(4)
        else:
            ins_kind.append(0)
        if m in ("call", "jmp") and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
            t = ins.operands[0].imm & 0xFFFFFFFF
            call_imm.setdefault(t, []).append((va, m))
            call_site[va] = (t, m)
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.index == 0:
                d = op.mem.disp & 0xFFFFFFFF
                if d in TARGET_DISPS:
                    mem_hits.setdefault(d, []).append((va, m, ins.op_str, op.mem.base))
        o = TEXT_RAW + (ins.address + ins.size - TEXT_VA)
    if not got:
        o += 1
        resync += 1
print("DEC insns=%d resync=%d decode_seconds=%.1f" % (total, resync, time.time() - tdec))
print("DEC corpus_ref=1394120/66 (=W8:44) — 差异如实登记")

for tgt, expn, tag in ((0x5F4B10, 3, "call 0x5F4B10 =F8V:36"), (0x6D2140, 139, "call 0x6D2140 =F8V:63")):
    sites = [va for va, mm in call_imm.get(tgt, []) if mm == "call"]
    print("VAL %-24s decoded_call=%d %s" % (tag, len(sites), "OK" if len(sites) == expn else "FAIL"))
sites104 = sorted(set(va for va, m, ops, b in mem_hits.get(0x104, []) if m in ("call", "jmp")))
print("VAL call/jmp [reg+0x104] 站点=%d expect7 =F8V:110-111" % len(sites104))
for va in sites104:
    print("   0x%08X" % va)
sites3c4 = sorted(set(va for va, m, ops, b in mem_hits.get(0x3C4, []) if m in ("call", "jmp")))
print("VAL call/jmp [reg+0x3C4](v241) 站点=%d expect14 =F7T:128-130" % len(sites3c4))
print("   %s" % [hex(v) for v in sites3c4])

def decode_range(va_lo, va_hi):
    out = []
    off0 = va2off(va_lo)
    end = va2off(va_hi)
    o = off0
    while o < end:
        got = False
        for ins in md.disasm(data[o:end], va_lo + (o - off0)):
            got = True
            tg = None
            disp = None
            if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                tg = ins.operands[0].imm & 0xFFFFFFFF
            for op in ins.operands:
                if op.type == capstone.x86.X86_OP_MEM:
                    disp = (op.mem.disp, op.mem.base, op.mem.index)
            out.append((ins.address, ins.mnemonic, ins.op_str, tg, disp, ins.size))
            o = off0 + (ins.address + ins.size - va_lo)
        if not got:
            o += 1
    return out

# ---------- P6: FPU 常量 ----------
print("\n== P6 FPU 常量数值（静态读）==")
for va in (0xB0CD48, 0x7E1738):
    info = file_backed(va)
    nm, fbl, fbh, vhi = info
    backed = va < fbh
    print("P6 VA=0x%08X sec=%s 文件映射域=[0x%08X,0x%08X) 文件映射=%s" % (va, nm, fbl, fbh, backed))
    if backed:
        q = u64q(va)
        d = f64(va)
        raw = bytes_at(va, 8)
        print("P6 qword=0x%016X double=%r raw=%s" % (q, d, raw.hex()))
    else:
        print("P6 数值不在文件镜像内（BSS 零初始化域）——写点指令恢复：")
        pat = struct.pack("<I", va)
        start = TEXT_RAW
        while True:
            i = data.find(pat, start, TEXT_RAW + TEXT_RSZ)
            if i < 0:
                break
            site = TEXT_VA + (i - TEXT_RAW)
            pre = bytes_at(site - 6, 6)
            post = bytes_at(site + 4, 8)
            print("   site=0x%08X pre6=%s post8=%s" % (site, pre.hex() if pre else "?", post.hex() if post else "?"))
            start = i + 1
    dec = sorted(mem_hits.get(va, []))
    print("P6 解码访存指令（含读写、含寄存器基址）=%d 条" % len(dec))
    for va2, m, ops, b in dec:
        print("   0x%08X %s %s" % (va2, m, ops))
print("P6 边界声明: 寄存器中转型写/rep movsd 不在本普查形态内（=F7T:283-286 同口径残余）")
print("P6 [0xB0CD48] 唯一解码写者 0x6D1BDD fstp 的宿主函数解码：")
g6 = decode_range(0x6D1B60, 0x6D1BE4)
for va, m, ops, tg, disp, sz in g6:
    print("   0x%08X %s %s" % (va, m, ops))

# ---------- P8: 三张 vtable 类名 ----------
print("\n== P8 三张 vtable 类名（RTTI 全链）==")
for vt in (0x7E3354, 0x7F5C70, 0x7F6318):
    r = rtti_of_vftable(vt)
    print("P8 vt=0x%08X COL=0x%08X COLoff=0x%X NAME=%s" % ((vt, r[0], r[1], r[2]) if r else (vt, None, None, None)))

# ---------- P7: vtable[65] 全集 ----------
print("\n== P7 vtable[65] (+0x104) 槽位全集（RTTI 可枚举范围）==")
BASE65 = 0x5F4B10
overwrites = {}
base_slots = []
for td_key, name in td_map.items():
    abs_td = td_key - imagebase
    for colp in rvals.get(abs_td, []):
        if u32(colp) != 0:
            continue
        if u32(colp + 12) != abs_td:
            continue
        col = colp
        for vtp in rvals.get(col, []):
            vt = vtp + 4
            s0 = u32(vt)
            if s0 is None or not is_text(s0):
                continue
            s64 = u32(vt + 0x100)
            s65 = u32(vt + 0x104)
            if not (is_text(s64) or s64 == 0):
                continue
            if s65 is None or not is_text(s65):
                continue
            rec = (vt, name, u32(col + 4))
            if s65 == BASE65:
                base_slots.append(rec)
            else:
                overwrites.setdefault(s65, []).append(rec)
print("P7 槽65==基实现 0x5F4B10 的 vftable 数=%d" % len(base_slots))
for vt, name, coff in sorted(base_slots):
    print("   base vt=0x%08X %s" % (vt, name))
print("P7 槽65!=基实现 的覆写值共 %d 个：" % len(overwrites))
for fn, recs in sorted(overwrites.items()):
    pad = bytes_at(fn - 4, 4)
    callers = call_imm.get(fn, [])
    print("   fn=0x%08X 头前4B=%s vftable数=%d E8直调者=%s" % (fn, pad.hex() if pad else "?", len(recs), ["0x%X" % v for v, m in callers]))
    for vt, name, coff in sorted(recs):
        print("      vt=0x%08X %s COLoff=0x%X" % (vt, name, coff))
rdata_5f = rvals.get(0x5F4B10, [])
print("P7 VAL .rdata 内 0x5F4B10 出现=%d 处（F8_review R6:230=16）" % len(rdata_5f))
print("P7 .rdata 内三覆写函数 dword 引用：")
for fn in (0x422C70, 0x73B0B0, 0x749B20):
    print("   0x%08X -> %s" % (fn, [hex(v) for v in rvals.get(fn, [])]))
print("P7 0x71CD7B 一带现场（F8V:224 W3 未展开项）bytes@0x71CD70..0x71CD88 = %s" % bytes_at(0x71CD70, 0x18).hex())

# ---------- 宿主定位（指令边界级） ----------
import array
from bisect import bisect_left
_starts = array.array("I", ins_starts)
_kinds = array.array("B", ins_kind)
_sizes = array.array("B", ins_sizes)
call_only_targets = set(t for t, lst in call_imm.items() if any(mm == "call" for _, mm in lst))

def plausible_prologue(va):
    o = va2off(va)
    if o is None:
        return False
    b0 = data[o]
    if 0x50 <= b0 <= 0x57:
        return True
    return b0 in (0x83, 0x81, 0x8B, 0x89, 0xA1, 0xB8, 0xB9, 0xBA, 0xBE, 0xBF, 0x33, 0x3B, 0x64, 0x6A, 0x68, 0x8A, 0x88, 0x0F, 0x66, 0x55, 0x53, 0x56, 0x57)

def find_host(site, maxback=0x8000):
    """指令边界级回扫（v3）：优先 ≥3 字节填充边界；其次最近 call 目标；再次最近 ret/jmp 后边界。
    返回 (host, kind, conf) conf: 2=call目标/vtable槽 1=序言形似"""
    k = bisect_left(_starts, site) - 1
    lo_va = site - maxback
    best_ret = None
    while k >= 0 and _starts[k] > lo_va:
        va = _starts[k]
        kind = _kinds[k]
        size = _sizes[k]
        nxt = _starts[k + 1] if k + 1 < len(_starts) else None
        if nxt is not None and nxt > va:
            pad = nxt - (va + size)
            cand = nxt
            conf = 2 if (cand in call_only_targets or cand in rvals) else 1
            if pad >= 3 and plausible_prologue(cand):
                return (cand, "after_pad%d" % pad, conf)
            if kind in (1, 2) and plausible_prologue(cand) and best_ret is None:
                best_ret = (cand, "after_ret/jmp", conf)
        k -= 1
    ct = [t for t in call_only_targets if lo_va <= t < site]
    if ct:
        t = max(ct)
        if plausible_prologue(t):
            return (t, "nearest_call_target", 2)
    return best_ret

def vtable_slot_of(fn):
    out = []
    for va in rvals.get(fn, []):
        for back in range(0, 0x800, 4):
            colv = u32(va - back)
            if colv and sec_of(colv) == ".rdata" and u32(colv) == 0:
                nm2 = td_map.get(imagebase + (u32(colv + 12) or 0))
                if nm2:
                    out.append((va, nm2, back - 4 if back >= 4 else 0))
                    break
    return out

KNOWN = {
    0x6D1C20: "TacticalClass::ctor", 0x7C8E17: "operator new", 0x6D5F60: "Tactical Rect装载",
    0x6D8B30: "Tactical 视口重算", 0x7C5F00: "double->int", 0x410170: "基类ctor",
    0x6D2140: "IsVisible", 0x5F4B10: "DrawIfVisible", 0x887324: "单例槽(数据)",
    0x886FA0: "源Rect全局(数据)", 0x6E53A0: "建筑回调", 0x6F8DF0: "Greatest_Threat",
    0x445F00: "Building v241包装", 0x4D9920: "Foot v241包装", 0x709820: "v[231]共享宿主",
    0x6ECCE0: "%14门宿主", 0x6EC9A0: "case转发目标", 0x6ECE60: "case转发目标",
    0x65AD40: "0x73B0B0所调", 0x565730: "坐标->CellClass", 0x6D2540: "Tactical AI",
    0x6DA980: "清场例程(card_00B0CE88)", 0x6D1A40: "屏幕Rect零初始化",
}

def report_host(site, tag, maxcalls=14):
    print("\n[%s] site=0x%08X" % (tag, site))
    r = find_host(site)
    if r is None:
        print("   host: 窗口内未找到指令边界 — 如实登记")
        return None
    host, kind, conf = r
    pro = bytes_at(host, 8)
    print("   host=0x%08X kind=%s conf=%d prologue=%s" % (host, kind, conf, pro.hex() if pro else "?"))
    calls = sorted((va, t, mm) for va, (t, mm) in call_site.items() if host <= va <= site + 0x30)
    print("   in-host call/jmp（截前 %d，共 %d）：" % (maxcalls, len(calls)))
    for va, t, mm in calls[:maxcalls]:
        print("     0x%08X %s -> 0x%08X %s" % (va, mm, t, KNOWN.get(t, "")))
    slots = vtable_slot_of(host)
    for va, nm2, off in slots:
        print("   vtable归属: 0x%08X = %s vftable+0x%X" % (va, nm2, off))
    refs_text = find_dword_in_text(host)
    if refs_text:
        print("   .text 内 dword 引用: %s" % [hex(v) for v in refs_text[:8]])
    callers = call_imm.get(host, [])
    print("   E8/E9 直调者: %d %s" % (len(callers), ["0x%X(%s)" % (v, m) for v, m in callers][:10]))
    return host

print("\n== S1 五创建点宿主 ==")
for s in (0x52C694, 0x599D80, 0x6853B4, 0x687617, 0x6BF84F):
    report_host(s, "S1")
print("\n[S1-附] 0x887324 W 点宿主（_w8_f6_out.txt:212-222 的 11 处）:")
for w in (0x52C69B, 0x52C6BC, 0x53498B, 0x599D8B, 0x67E8EE, 0x6853BF, 0x687627, 0x6BEA10, 0x6D1E1E, 0x6D1E9B, 0x6DC48E):
    r = find_host(w)
    print("   W@0x%08X host=%s" % (w, ("0x%08X(%s,c%d)" % (r[0], r[1], r[2])) if r else "未找到"))

print("\n== S2 v[231] 0x709820 调用方追链 ==")
print("S2 直接 E8/E9 -> 0x709820:", call_imm.get(0x709820, []))
sites39c = sorted(set(va for va, m, ops, b in mem_hits.get(0x39C, []) if m in ("call", "jmp")))
print("S2 call/jmp [reg+0x39C] (v[231] 派发) 站点=%d" % len(sites39c))
for va in sites39c:
    detail = [(m, ops) for (v, m, ops, b) in mem_hits[0x39C] if v == va and m in ("call", "jmp")][0]
    print("   site=0x%08X %s %s" % ((va,) + detail))
for va in sites39c:
    report_host(va, "S2-site")
print("S2 0x709820 虚表槽归属（RTTI）：")
for va in rvals.get(0x709820, []):
    got_name = None
    for back in range(0, 0x800, 4):
        colv = u32(va - back)
        if colv and sec_of(colv) == ".rdata" and u32(colv) == 0:
            nm2 = td_map.get(imagebase + (u32(colv + 12) or 0))
            if nm2:
                got_name = (nm2, back - 4)
                break
    if got_name:
        print("   slot=0x%08X = %s vftable+0x%X" % (va, got_name[0], got_name[1]))
    else:
        print("   slot=0x%08X (RTTI 回溯未中)" % va)

print("\n== S3 0x6E962A switch 宿主 ==")
s3host = report_host(0x6E962A, "S3")
if s3host:
    hend = None
    k = bisect_right(_starts, 0x6EA078) - 1
    hend = 0x6EA078
    ins3 = decode_range(s3host, hend)
    print("S3 host 解码条数=%d 区间=[0x%08X,0x%08X)" % (len(ins3), s3host, hend))
    n_ind = 0
    tbl_base = None
    for va, m, ops, tg, disp, sz in ins3:
        if m in ("jmp", "call") and disp and disp[2] != 0:
            n_ind += 1
            print("   间接分支 0x%08X %s %s mem={base:%d,index:%d,disp:0x%X}" % (va, m, ops, disp[1], disp[2], disp[0] & 0xFFFFFFFF))
            if m == "jmp" and disp[1] == 0:
                tbl_base = disp[0] & 0xFFFFFFFF
    if n_ind == 0:
        print("   host 内未解码出 [reg*4+disp] 型间接分支——如实登记")
    offh = va2off(s3host)
    offen = va2off(hend)
    seg = data[offh:offen]
    idx = 0
    found_ff24 = False
    while True:
        i = seg.find(b"\xff\x24", idx)
        if i < 0:
            break
        found_ff24 = True
        print("   FF24 现场 0x%08X: %s" % (s3host + i, seg[i:i + 8].hex()))
        idx = i + 2
    if not found_ff24:
        print("   host 区间内无 FF 24 字节现场——如实登记")
    # 全 .text 找引用跳转表的间接 jmp（FF 24 xx + disp32 == tbl_base）
    if tbl_base:
        print("S3 全 .text 内 disp32==表基 0x%08X 的 FF 24 间接跳转：" % tbl_base)
        i = TEXT_RAW
        cnt = 0
        while True:
            i = data.find(b"\xff\x24", i, TEXT_RAW + TEXT_RSZ)
            if i < 0:
                break
            b2 = data[i + 2]
            if (b2 & 0xC7) == 0x85 and i + 6 <= TEXT_RAW + TEXT_RSZ:
                d = struct.unpack_from("<I", data, i + 3)[0]
                if d == tbl_base:
                    cnt += 1
                    print("   dispatcher=0x%08X: %s (表基=0x%08X)" % (TEXT_VA + (i - TEXT_RAW), data[i:i + 7].hex(), d))
            i += 2
        if cnt == 0:
            print("   0 条——如实登记")
        n = 0
        ents = []
        while n < 96:
            v = u32(tbl_base + 4 * n)
            if v is None or not is_text(v):
                break
            ents.append(v)
            n += 1
        print("S3 跳转表 0x%08X 条目数=%d（0x6E961E 在表中=%s）首8项=%s 尾2项=%s" % (
            tbl_base, n, (0x6E961E in ents) if ents else None,
            [hex(x) for x in ents[:8]], [hex(x) for x in ents[-2:]] if len(ents) > 2 else []))
    print("S3 .text 内对 0x6E961E（case 块）的 dword 引用: %s" % [hex(v) for v in find_dword_in_text(0x6E961E)])
    # 检查 0x6E9FB4 邻域是否为跳转表
    tbl_region = []
    v = 0x6E9FB4
    lo = v
    while True:
        x = u32(lo - 4)
        if x is None or not (TEXT_LO <= x < TEXT_HI):
            break
        lo -= 4
    hi = v
    while True:
        x = u32(hi)
        if x is None or not (TEXT_LO <= x < TEXT_HI):
            break
        hi += 4
    print("S3 0x6E9FB4 邻域 .text 值 dword 区=[0x%08X,0x%08X) 共 %d 项，首尾=%s..%s" % (lo, hi, (hi - lo) // 4, hex(u32(lo)), hex(u32(hi - 4))))

# ---------- P11 GT 体统计 ----------
print("\n== P11 Greatest_Threat 体统计 [0x6F8DF0,0x6F9DB0) ==")
gt = decode_range(0x6F8DF0, 0x6F9DB0)
print("P11 insns=%d" % len(gt))
seen = {}
for va, m, ops, tg, disp, sz in gt:
    if m in ("call", "jmp") and tg is not None:
        seen.setdefault(tg, []).append(va)
print("P11 call/jmp-imm 总数=%d 目标集合：" % sum(len(v) for v in seen.values()))
for tg, vas in sorted(seen.items()):
    print("   -> 0x%08X ×%d %s" % (tg, len(vas), KNOWN.get(tg, "")))
bwd = [(va, m, tg) for va, m, ops, tg, disp, sz in gt if m[0] == "j" and tg is not None and tg < va]
print("P11 后向 jcc/jmp（循环边候选）=%d：%s" % (len(bwd), [(hex(va), m, hex(tg)) for va, m, tg in bwd]))
memops = [(va, m, ops) for va, m, ops, tg, disp, sz in gt if m in ("inc", "dec", "add", "sub") and disp is not None and disp[0] is not None]
print("P11 体内 inc/dec/add/sub 带内存操作数=%d" % len(memops))
for va, m, ops in memops:
    print("   0x%08X %s %s" % (va, m, ops))
a8 = [(va, m, ops) for va, m, ops, tg, disp, sz in gt if disp is not None and disp[0] is not None and (disp[0] & 0xFFFFFFFF) == 0xA8EC34]
print("P11 体内 0xA8EC34 访存=%d：%s" % (len(a8), [(hex(va), m) for va, m, ops in a8]))
pro = [x for x in gt if x[0] < 0x6F8E41]
print("P11 入口段 [0x6F8DF0,0x6F8E41) insns=%d" % len(pro))
fpu = [(va, m, ops) for va, m, ops, tg, disp, sz in gt if m[0] == "f"]
print("P11 FPU 指令条数=%d（样例前 10）：%s" % (len(fpu), [(hex(va), m) for va, m, ops in fpu[:10]]))

print("\n== RUN TIME %.1fs ==" % (time.time() - T0))

# ---------- 出口聚合（只追加：以上原件 562 行零改动） ----------
# 本脚本对自身的检查结果原先只走 stdout 与 assert，无写盘裁决：
#   :16  SHA_MATCH_CORPUS_73201cc0 打印布尔；:20/:24 两条 assert 守卫（失败即 AssertionError -> EXIT=1）；
#   :115(12 项) / :117 / :120(6 项) / :123(3 项) / :162(2 项) / :219(2 项) 打印 "OK"/"FAIL"。
# 下面用同一批仍存活的只读全局量（data/SHA/EXP_SHA/VALS/d900/u32/bytes_at/rtti_of_vftable/call_imm）
# 重算完全相同的比较式并逐项喂 check()；原始 print 一行不改，故原有 stdout 逐字保留。
ok = True
def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)          # 合取聚合：任一项为假即把 ok 置假
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ((" | " + detail) if detail else ""))

check("R0 SHA_MATCH_CORPUS_73201cc0 (:16)", SHA == EXP_SHA)
check("assert PE 签名 (:20)", data[e_lfanew:e_lfanew + 4] == b"PE\0\0")
check("assert PE32 magic 0x10B (:24)", struct.unpack_from("<H", data, opt)[0] == 0x10B)
for va, exp, tag in VALS:
    check("VAL %s (:115)" % tag.strip(), u32(va) == exp)
check("VAL qword(0x7E27F8)==900.0 (:117)", d900 == 900.0)   # 复用原件 :116 算出的同一 d900
for sv in (0x7E2640, 0x7E4258, 0x7E9030, 0x7EB3F4, 0x7F4CFC, 0x7F600C):
    check("VAL u32(0x%08X)==0x709820 (:120)" % sv, u32(sv) == 0x709820)
for sv, exp in ((0x826260, b"RULESMD.INI"), (0x82626C, b"RULEMD*.INI"), (0x826838, b"CONQMD.MIX")):
    check("VAL str(0x%08X)==%r (:123)" % (sv, exp), bytes_at(sv, len(exp)) == exp)
for vt, exp_sub in ((0x7F4348, "Tactical"), (0x7E85D4, "DSurface")):
    r = rtti_of_vftable(vt)
    check("RTTI VAL vt=0x%08X 期望含 %s (:162)" % (vt, exp_sub), r and exp_sub in r[2])
for tgt, expn, tag in ((0x5F4B10, 3, "call 0x5F4B10 =F8V:36"), (0x6D2140, 139, "call 0x6D2140 =F8V:63")):
    sites = [va for va, mm in call_imm.get(tgt, []) if mm == "call"]
    check("VAL %-24s decoded_call==%d (:219)" % (tag, expn), len(sites) == expn)

print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
