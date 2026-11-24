# -*- coding: utf-8 -*-
# _p11_stations_scan.py — P11 残余开口：12 个无门 v[241] 派发站的静态归属推断（只读）
# 依据: lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md:128（12 无门站未命名）
#       lead/re_line_20261105/W8_STATIC_LOCATE/F7_TARGETING.md:129-130（14 站清单）/ :244-246（门分类）
#       lead/re_line_20261105/W8_STATIC_LOCATE/_w8_f7_out.txt:879-896（14 站启发式窗口）
# 方法: 纯磁盘镜像字节解析 + capstone 反汇编。RTTI/vtable 口径照抄 _sc_p7.py:55-92（TD=串址-8、
#       COL=TD引用位-12、vtable基=COL指针位+4）。零真机/零采样/零注入/零进程 API/本脚本零写盘。
# 用法: python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\p11_stations_20261108\_p11_stations_scan.py" > 同目录_p11_stations_out.txt
import struct, hashlib, time
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

T0 = time.time()
PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(PATH, "rb").read()
SHA = hashlib.sha256(data).hexdigest()
EXP_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
print("R0 SHA256", SHA)
print("R0 SHA_MATCH", SHA == EXP_SHA)
print("R0 BYTES", len(data))

# ---------- PE 解析（口径同 _sc_scan.py:16-30） ----------
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0"
coff = e_lfanew + 4
machine, nsec, _ts, _pt, _nsym, optsize, _ch = struct.unpack_from("<HHIIIHH", data, coff)
opt = coff + 20
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
SEC = {nm: (imagebase + va, vsz, raw, rsz) for nm, va, vsz, raw, rsz, ch in SECTIONS}
TEXT_VA, TEXT_VSZ, TEXT_RAW, TEXT_RSZ = SEC[".text"]

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

def u32(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<I", data, o)[0]

def is_text(va):
    return sec_of(va) == ".text"

# ---------- RTTI TypeDescriptor 名表（口径同 _sc_p7.py:50-60：TD 基址 = 串址-8） ----------
td_map = {}
for nm in (".data", ".rdata"):
    sva, vsz, raw, rsz = SEC[nm]
    blob = data[raw:raw + rsz]
    start = 0
    while True:
        i = blob.find(b".?A", start)
        if i < 0:
            break
        j = blob.find(b"\0", i)
        td_map[sva + i - 8] = blob[i:j if j > 0 else i + 64].decode("ascii", errors="replace")
        # 注: _sc_p7.py:59 键=imagebase+sva+i-8 配合 :73 abs_td=td_key-imagebase，等价于真 TD VA；
        #     本件直接存真 TD VA，避免二次换算。
        start = i + 1
print("RTTI TD count", len(td_map))

# ---------- .rdata/.data 全 dword 绝对值索引（value -> [va,...]） ----------
rvals = {}
for nm in (".rdata", ".data"):
    sva, vsz, raw, rsz = SEC[nm]
    for off in range(0, rsz - 3, 4):
        v = struct.unpack_from("<I", data, raw + off)[0]
        if 0x401000 <= v < 0x8A0000:  # 只留像 VA 的值
            rvals.setdefault(v, []).append(sva + off)  # sva 已含 imagebase（SEC 值首元=VA）
print("RVALS distinct", len(rvals))

# ---------- vtable 枚举（口径同 _sc_p7.py:79-95：COL=u32 引用且 sig==0；vt=COL指针位+4） ----------
def vt_len(vt, maxn=4096):
    n = 0
    while n < maxn:
        v = u32(vt + 4 * n)
        if v is None:
            break
        if v == 0 or is_text(v):
            n += 1
        else:
            break
    return n

VTABLES = []  # (vt_base, class_name, length)
for td_key, name in td_map.items():
    for pos in rvals.get(td_key, []):   # rvals 键域 = 原始 dword 值；td_key = 真 TD VA
        col = pos - 12          # 命中位置 = COL+12 (pTypeDescriptor 字段)，COL 基址 = pos-12
        if col < SEC[".rdata"][0]:
            continue
        if u32(col) != 0:
            continue
        if u32(col + 12) != td_key:
            continue
        for vtp in rvals.get(col, []):
            vt = vtp + 4
            L = vt_len(vt)
            s0 = u32(vt)
            if s0 is None or not is_text(s0):
                continue
            VTABLES.append((vt, name, L))
print("RTTI VTABLES", len(VTABLES))

# 函数起始 -> [(class, vt_base, slot)]
func_slots = {}
for vt, name, L in VTABLES:
    for k in range(L):
        v = u32(vt + 4 * k)
        if v and is_text(v):
            func_slots.setdefault(v, []).append((name, vt, k))
print("FUNC_SLOTS distinct func starts", len(func_slots))

# ---------- .text E8/E9 直调普查（一次全扫） ----------
callers = {}   # target -> [(site, 'call'|'jmp')]
tlo, thi = TEXT_RAW, TEXT_RAW + TEXT_RSZ
for i in range(tlo, thi - 5):
    b = data[i]
    if b == 0xE8 or b == 0xE9:
        rel = struct.unpack_from("<i", data, i + 1)[0]
        tgt = imagebase + TEXT_VA - imagebase  # placeholder
        tgt = (TEXT_VA + (i - TEXT_RAW)) + 5 + rel
        callers.setdefault(tgt, []).append((TEXT_VA + (i - TEXT_RAW), "call" if b == 0xE8 else "jmp"))
print("CALLERS targets", len(callers))

# ---------- 已命名函数表（全部来自既有材料，逐条注明出处） ----------
KNOWN = {
    0x6F8DF0: "Greatest_Threat 本体(v[241]=+0x3C4 槽值, F7T:131)",
    0x445F00: "BuildingClass v[241] 包装(F7T:124/:132, u32(0x7E4280))",
    0x4D9920: "FootClass v[241] 包装(F7T:125/:132, u32(0x7E9058))",
    0x51E140: "InfantryClass v[241] 包装(F7T:132)",
    0x743190: "UnitClass v[241] 包装(F7T:132)",
    0x709820: "v[231] 五虚表共享函数(+0x39C), 0x709932 状态门站宿主(F7T:185-196)",
    0x6ECCE0: "%14 宏观门宿主(0x6ECE06 站宿主, F7T:158-183)",
    0x6E9050: "S3 switch 宿主(0x6E962A 所在, _sc_scan_out.txt:977)",
    0x740B10: "UnitClass v[151] 槽函数(u32(0x7F5ECC)=0x740B10, F7T:137)",
    0x4D4280: "GT 派发宿主之一(UnitClass v[151] 链, F7T:136-138/:241-242)",
    0x736CA0: "UnitClass v[265] 包装(F7T:230)",
    0x6FB010: "v[265] 槽值目标(F7T:230/:337)",
    0x4A51D0: "0x740B10 内调用(查+0x350对象+0x18/+0x19, F7T:235)",
    0x4A5240: "0x740B10 内调用(CurrentFrame 戳 +0x350 对象+0x8, F7T:236)",
    0x7C5F00: "double→int 转换(F7T:166)",
    0x772A90: "Building v[241] 包装内 2 次调用(F7T:147)",
    0x412B40: "空间桶查询(GT 体 ×1, _sc_scan_out.txt:1006)",
    0x50B730: "GT 体 ×2 / S3 宿主 0x6E9245 直调(_sc_scan_out.txt:984/:1010)",
    0x4F9A50: "GT 体 ×7(_sc_scan_out.txt:1008)",
    0x4F9A90: "GT 体 ×3(_sc_scan_out.txt:1009)",
    0x5F4B10: "vtable[65] 基实现(STATIC_GAP_CLOSURE.md:107)",
    0x6E53A0: "建筑回调(S3 宿主 0x6E9304 直调 _sc_scan_out.txt:986; F7T:212)",
    0x578540: "S3 宿主直调(_sc_scan_out.txt:979)",
    0x6EA3E0: "S3 宿主直调(_sc_scan_out.txt:980)",
    0x6EA0D0: "S3 宿主直调(_sc_scan_out.txt:981)",
    0x691590: "S3 宿主直调(_sc_scan_out.txt:982)",
    0x6EAEE0: "S3 宿主直调(_sc_scan_out.txt:983)",
    0x6EAA90: "S3 宿主直调(_sc_scan_out.txt:985)",
    0x6915B0: "S3 宿主直调(_sc_scan_out.txt:989)",
    0x70C610: "S3 宿主直调(_sc_scan_out.txt:992)",
    0x4068E0: "S3 宿主 0x6E93C3 直调(_sc_scan_out.txt:990)",
    0x5657A0: "GT 体 ×2(_sc_scan_out.txt:1011)",
    0x568300: "GT 体 ×4(_sc_scan_out.txt:1012)",
    0x56D230: "GT 体 ×1(_sc_scan_out.txt:1013)",
    0x6F3970: "GT 体 ×4(_sc_scan_out.txt:1014)",
    0x6F7CA0: "GT 体 ×3(_sc_scan_out.txt:1015)",
    0x6F8960: "GT 体 ×4(_sc_scan_out.txt:1016)",
    0x6F8C10: "GT 体 ×4(_sc_scan_out.txt:1017)",
    0x4137A0: "GT 体 ×2(_sc_scan_out.txt:1007)",
    0x717880: "GT 体 ×1(_sc_scan_out.txt:1028)",
    0x578540: "S3 宿主直调(_sc_scan_out.txt:979)",
    0x4CAD00: "double 取整/对齐例程(dis_004CAD00.txt:1 fld qword[esp+4] fmul 0x8223b4)",
    0x445F68: "Building 包装内 GT 直调点(F7T:124)",
    0x4D9942: "Foot 包装内 GT 直调点(F7T:125)",
}

SITES = [0x414B24, 0x414B64, 0x417481, 0x4D4314, 0x4D4686, 0x4D49A3,
         0x4D4E3E, 0x4DE056, 0x50D1D2, 0x51F382, 0x6ED15E, 0x6F0253]
GATED = {0x6ECE06: "%14 宏观门站(宿主0x6ECCE0, F7T:158)", 0x709932: "状态门站(宿主0x709820 v[231], F7T:185)"}

cs = Cs(CS_ARCH_X86, CS_MODE_32)

def disasm_range(start_va, end_va):
    o = va2off(start_va)
    if o is None:
        return []
    n = end_va - start_va
    return list(cs.disasm(data[o:o + n], start_va))

def cstr(va, maxlen=80):
    o = va2off(va)
    if o is None:
        return None
    end = data.find(b"\0", o, o + maxlen)
    if end < 0:
        return None
    s = data[o:end]
    if len(s) >= 4 and all(0x20 <= c < 0x7F for c in s):
        return s.decode("ascii")
    return None

def heur_start(site, back=0x900):
    """最近前置 C3/C2/CC 边界（同 F7 探针 D 段启发式, _w8_f7_out.txt:878）"""
    o = va2off(site)
    for k in range(1, back):
        b = data[o - k]
        if b in (0xC3, 0xC2, 0xCC):
            return site - k + 1, site - k, data[o - k - 1]
    return None, None, None

def heur_end(site, fwd=0x3000):
    """向前最近 C3/C2/CC 边界（宿主体近似上界）"""
    o = va2off(site)
    for k in range(1, fwd):
        b = data[o + k]
        if b in (0xC3, 0xC2, 0xCC):
            return site + k
    return site + fwd

def vtable_hits(func_va, lo=None, hi=None):
    """func_va 的 vtable 归属：精确值命中；再给出 (lo,hi] 内落在某虚表条目上的 VA（真起点候选）"""
    exact = []
    for pos in rvals.get(func_va, []):
        if sec_of(pos) not in (".rdata", ".data"):
            continue
        # 反向走 text 指针连续段找表基
        base = pos
        for k in range(1, 4096):
            prev = u32(base - 4)
            if prev is None or (prev != 0 and not is_text(prev)):
                break
            base -= 4
        col = u32(base - 4)
        cls = None
        if col and u32(col) == 0 and u32(col + 12) in td_map:
            cls = td_map[u32(col + 12)]
        exact.append((pos, base, (pos - base) // 4, cls))
    inner = []
    if lo is not None:
        a, b_ = lo, (hi if hi else func_va)
        for vt, cls, L in VTABLES:
            for k in range(L):
                v = u32(vt + 4 * k)
                if v and a <= v <= b_:
                    inner.append((v, cls, vt, k))
    return exact, inner

# ---------- 真起点解析（升级 v2）：候选 = rvals 引用值 ∪ E8/E9 目标 ∪ 对齐填充起点 ----------
# 线性流验证 + 硬边界: 途中遇 ret-imm(C2)/int3 → 终止（函数界）；C3 后随 >=1 字节 90/CC/00 → 终止。
# 校准: 两已知门站必须解出已知宿主（0x6ECE06→0x6ECCE0、0x709932→0x709820）。
def resolve_start(site, span=0x1400):
    lo = site - span
    cands = set()
    for v in rvals:
        if lo <= v <= site:
            cands.add(v)
    for t in callers:
        if lo <= t <= site:
            cands.add(t)
    o_site = va2off(site)
    for k in range(1, span):
        b = data[o_site - k]
        if b in (0x90, 0xCC) and data[o_site - k - 1] in (0x90, 0xCC):
            cands.add(site - k + 1)
    valid = []
    for c in sorted(cands, reverse=True):
        if c == site:
            continue
        o = va2off(c)
        if o is None:
            continue
        crossed = False
        ok = False
        for ins in cs.disasm(data[o:o + (site - c) + 16], c):
            if ins.address == site:
                ok = True
                break
            if ins.address + ins.size > site:
                break
            m = ins.mnemonic
            if m == "int3":
                crossed = True
                break
            if m == "ret":
                if ins.op_str != "":        # C2 ret imm16 → 必为函数终止
                    crossed = True
                    break
                nxt = va2off(ins.address + ins.size)
                b1 = data[nxt] if nxt is not None else 0
                if b1 in (0x90, 0xCC, 0x00):  # C3+填充 → 函数终止
                    crossed = True
                    break
        if ok and not crossed:
            valid.append(c)
    if not valid:
        return None, []
    anchored = [c for c in valid if c in callers or c in func_slots or c in rvals]
    best = anchored[-1] if anchored else valid[-1]
    return best, valid

print()
print("#" * 78)
print("# PASS2 真起点解析（硬边界版；自校准=两已知门站）")
print("#" * 78)
RESOLVED = {}
for site in SITES + sorted(GATED):
    best, valid = resolve_start(site)
    RESOLVED[site] = best
    vs = valid[-6:]
    print("SITE 0x%08X -> start=0x%08X valid_chain=%s" % (
        site, best if best else 0,
        [hex(v) for v in vs]))

print()
print("#" * 78)
print("# PASS2 真起点解析")
print("#" * 78)
RESOLVED = {}
for site in SITES + sorted(GATED):
    best, valid = resolve_start(site)
    RESOLVED[site] = best
    vs = valid[-6:]
    print("SITE 0x%08X -> start=0x%08X valid_chain=%s" % (
        site, best if best else 0,
        [hex(v) for v in vs]))

for site in SITES + sorted(GATED):
    print()
    print("=" * 78)
    print("== SITE 0x%08X  %s" % (site, GATED.get(site, "无门(对照/待命名)")))
    print("=" * 78)
    hs, hb, pre = heur_start(site)
    he = heur_end(site)
    print("HEUR start=0x%08X boundary_byte@0x%08X=0x%02X prev=0x%02X  heur_end=0x%08X"
          % (hs, hb, data[va2off(hb)], pre, he))
    rs = RESOLVED.get(site)
    if rs:
        he = heur_end(rs)
        start, start_src = rs, "pass2-resolved"
    else:
        start, start_src = hs, "heur"
    print("PASS2 start=0x%08X (src=%s)" % (start, start_src))
    exact, inner = vtable_hits(start, hs, site)
    print("VTABLE exact-for-heur-start:", [(hex(p), hex(b), "slot%d" % s, c) for p, b, s, c in exact])
    if inner:
        inner.sort(key=lambda t: -t[0])
        print("VTABLE inner-candidates in [heur_start, site]:",
              [(hex(v), c, "slot%d" % k, hex(vt)) for v, c, vt, k in inner[:8]])
    # 真起点以 PASS2 为准（上面已设），这里只做 vtable 内点提示输出
    slots = func_slots.get(start, [])
    print("FUNC start=0x%08X src=%s slots=%s" % (start, start_src,
          [(c, hex(vt), "vslot%d" % s) for c, vt, s in slots]))
    # E8/E9 直调者
    cl = callers.get(start, [])
    print("DIRECT callers E8/E9: %d  %s" % (len(cl), [(hex(a), t) for a, t in cl[:14]]))
    # 宿主体内 call/jmp-imm 目标
    body = disasm_range(start, min(he + 1, start + 0x4000))
    tgts = {}
    for ins in body:
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            tgts[t] = tgts.get(t, 0) + 1
    print("BODY call/jmp-imm targets(%d):" % len(tgts))
    for t in sorted(tgts):
        tag = KNOWN.get(t, "")
        sl = func_slots.get(t, [])
        slt = (" ; " + ",".join("%s vslot%d" % (c, s) for c, vt, s in sl[:3])) if sl else ""
        print("   -> 0x%08X x%d %s%s" % (t, tgts[t], tag, slt))
    # 站点前后指令（真起点起解码保证对齐）
    lo_va = max(site - 0x40, start)
    insns = disasm_range(lo_va, site + 0x30)
    print("CONTEXT around site:")
    for ins in insns:
        mark = " >>>" if ins.address <= site < ins.address + ins.size else "    "
        print("   %s %08x  %-8s %s" % (mark, ins.address, ins.mnemonic, ins.op_str))
    # 字符串立即数线索（宿主体近似范围内）
    strs = []
    for ins in disasm_range(start, min(he + 1, start + 0x4000)):
        for tok in ins.op_str.replace(",", " ").split():
            if tok.startswith("0x"):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if 0x6A0000 <= v < 0x8A0000:
                    s = cstr(v)
                    if s:
                        strs.append((ins.address, ins.mnemonic, v, s))
    if strs:
        print("STRING imm refs:")
        for a, m, v, s in strs[:20]:
            print("   %08x %s 0x%08x  %r" % (a, m, v, s))
    else:
        print("STRING imm refs: none in heur body")

print()
print("RUN TIME %.1fs" % (time.time() - T0))
