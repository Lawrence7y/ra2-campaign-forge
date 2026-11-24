# -*- coding: utf-8 -*-
"""A2 独立复核只读探针 —— 零真机 / 零注入 / 不改任何既有文件。
只用 ra2tool.Engine 静态反汇编磁盘镜像 gamemd.exe，并逐行核对 §6.2 源码行号。
运行: python -I -X utf8 _w7_a2.py > _w7_a2_out.txt 2>&1
"""
import sys, struct, hashlib, datetime, os, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104')
from ra2tool import Engine

ROOT = r'D:\Project\ra2-campaign-forge'
CARD = os.path.join(ROOT, r'lead\re_line_20261105\W4_FIELD_SPEC\sections\card_00A8EC34.md')
VA = 0x00A8EC34
HEAD = 0x6F8DF0
BODY_HI = 0x6F9DB0


def sec(t):
    print('\n' + '=' * 24 + ' ' + t + ' ' + '=' * 24, flush=True)


def dump_lines(rel, ranges, width=150):
    """逐行打印指定行号区间（只读），用于核对 §6.2 引用的行号是否对得上。"""
    p = os.path.join(ROOT, rel)
    raw = open(p, 'rb').read()
    lines = raw.decode('utf-8', errors='replace').splitlines()
    print('FILE %s  TOTAL_LINES %d' % (rel, len(lines)), flush=True)
    for a, b in ranges:
        for n in range(a, min(b, len(lines)) + 1):
            print('  %s:%d: %s' % (rel, n, lines[n - 1][:width]), flush=True)
        print('  ---', flush=True)


# ---------------------------------------------------------------- 0
sec('0 CARD HASH / TIME / ENGINE ID')
card = open(CARD, 'rb').read()
print('CARD_SIZE', len(card), flush=True)
print('CARD_SHA256', hashlib.sha256(card).hexdigest(), flush=True)
print('PROBE_TIME', datetime.datetime.now().isoformat(), flush=True)
eng = Engine()
print('EXE_SHA256', eng.sha, flush=True)
print('IMAGE_BASE', hex(eng.IB), flush=True)
print('TEXT_LO/HI/SIZE', hex(eng.TLO), hex(eng.THI), eng.TSZ, flush=True)
for nm, sva, vsz, rp, rsz in eng.SEC:
    print('  SEC', nm, 'VA', hex(sva), 'VSZ', hex(vsz), 'RAWPTR', hex(rp), 'RAWSZ', hex(rsz), flush=True)
d = next(s for s in eng.SEC if s[0] == '.data')
delta = VA - d[1]
print('BSS .data delta', hex(delta), 'rawsize', hex(d[4]), 'zero_fill', delta >= d[4], flush=True)
print('fo(VA)', eng.fo(VA), 'u32(VA)', hex(eng.u32(VA)), flush=True)

# ---------------------------------------------------------------- 1
sec('1 PROLOGUE / BOUNDARY / EARLY-RETURN (真反汇编)')
for a, bs, m, o in eng.disasm(0x6F8DE0, 0x70):
    print('  %08X  %-20s %-8s %s' % (a, bs, m, o), flush=True)

# ---------------------------------------------------------------- 2
sec('2 FULL-STREAM COVERAGE + disp_hits(0xA8EC34)')
cov, nins, fails = eng.coverage
print('COVERAGE pct=%.14f insns=%d resync=%d .text_size=%d' % (cov, nins, fails, eng.TSZ), flush=True)
hits = eng.disp_hits(VA)
print('DISP_HITS_0xA8EC34 count=%d' % len(hits), flush=True)
for h in hits:
    print('   ', hex(h[0]), h[1], h[2], h[3], flush=True)
print('WRITE_HITS count=%d' % sum(1 for h in hits if h[1] == 'W'), flush=True)
print('READ_HITS  count=%d' % sum(1 for h in hits if h[1] == 'R'), flush=True)
stream = eng.stream
print('STREAM_LEN', len(stream), flush=True)

# 全流：所有含 disp==VA 的内存操作数（含 [reg+disp] 家族）
mem_disp = []
for i in stream:
    try:
        ops = i.operands
    except Exception:
        continue
    for op in ops:
        try:
            if op.type == 3 and op.mem.disp == VA:
                mem_disp.append((i.address, i.mnemonic, i.op_str, op.mem.base, op.mem.index, op.size))
                break
        except Exception:
            pass
print('ANY_MEM_OPERAND_WITH_DISP_EQ_VA count=%d' % len(mem_disp), flush=True)
for x in mem_disp:
    print('   ', hex(x[0]), x[1], x[2], 'base', x[3], 'index', x[4], 'size', x[5], flush=True)

# 全流：imm32 == VA 的指令
imm_hits = []
for i in stream:
    try:
        for op in i.operands:
            if op.type == 2 and (op.imm & 0xFFFFFFFF) == VA:
                imm_hits.append((i.address, i.mnemonic, i.op_str))
                break
    except Exception:
        pass
print('IMM32_EQ_VA count=%d' % len(imm_hits), flush=True)
for x in imm_hits:
    print('   ', hex(x[0]), x[1], x[2], flush=True)
# 全流：LEA 且 disp == VA
lea_hits = []
for i in stream:
    if i.mnemonic != 'lea':
        continue
    try:
        if any(op.type == 3 and op.mem.disp == VA for op in i.operands):
            lea_hits.append((i.address, i.mnemonic, i.op_str))
    except Exception:
        pass
print('LEA_DISP_EQ_VA count=%d' % len(lea_hits), flush=True)
for x in lea_hits:
    print('   ', hex(x[0]), x[1], x[2], flush=True)

# ---------------------------------------------------------------- 3
sec('3 WHOLE-FILE RAW LE DWORD 34 EC A8 00 (100% byte coverage)')
needle = struct.pack('<I', VA)
occ = []
p = 0
while True:
    q = eng.raw.find(needle, p)
    if q < 0:
        break
    occ.append(q)
    p = q + 1
print('RAW_DWORD_A8EC34_COUNT', len(occ), flush=True)
for off in occ:
    ctx = eng.raw[max(0, off - 8):off + 12].hex()
    print('   file_off', hex(off), 'ctx', ctx, flush=True)
# VA 换算：按节表 rawptr 把 file_off 换回 VA
for off in occ:
    t = next(s for s in eng.SEC if s[3] <= off < s[3] + s[4])
    print('   file_off', hex(off), 'section', t[0], 'VA', hex(t[1] + off - t[3]), flush=True)
print('RSDS_count', eng.raw.count(b'RSDS'), 'NB10_count', eng.raw.count(b'NB10'),
      '.pdb_count', eng.raw.count(b'.pdb'), '.PDB_count', eng.raw.count(b'.PDB'), flush=True)
print('pdb_casefold_count', eng.raw.lower().count(b'.pdb'), flush=True)

# ---------------------------------------------------------------- 4
sec('4 OVERLAPPING ABSOLUTE MEM OPS [0xA8EC34,0xA8EC38) + NEIGHBOURHOOD')
ov = []
for i in stream:
    try:
        for op in i.operands:
            if op.type == 3 and op.mem.base == 0 and op.mem.index == 0:
                lo, hi = op.mem.disp, op.mem.disp + op.size
                if lo < VA + 4 and hi > VA:
                    ov.append((i.address, i.mnemonic, i.op_str, op.size, 'W' if (op.access & 2) else 'R'))
                    break
    except Exception:
        pass
print('OVERLAPPING_ABSOLUTE_MEM_OPS count=%d' % len(ov), flush=True)
for x in ov:
    print('   ', hex(x[0]), x[1], x[2], 'size', x[3], x[4], flush=True)
nb = 0
nb_w = []
for i in stream:
    try:
        for op in i.operands:
            if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and (VA - 0x20) <= op.mem.disp <= (VA + 0x20):
                nb += 1
                if op.mem.disp == VA:
                    nb_w.append((hex(i.address), i.mnemonic, i.op_str))
                break
    except Exception:
        pass
print('NEIGHBOURHOOD_ABSOLUTE_MEM_OPS_[VA-0x20,VA+0x20] count=%d' % nb, flush=True)
print('  (disp==VA subset) count=%d' % len(nb_w), flush=True)
for x in nb_w:
    print('   ', x, flush=True)

# ---------------------------------------------------------------- 5
sec('5 BRANCH/CMP/TEST/CALL BETWEEN ENTRY AND WRITEBACK')
seg = [i for i in stream if HEAD <= i.address <= 0x6F8E09]
print('SEG_INSNS count=%d' % len(seg), flush=True)
bad = [(i.address, i.mnemonic, i.op_str) for i in seg
       if i.mnemonic.startswith('j') or i.mnemonic in ('cmp', 'test', 'call', 'ret')]
print('JCC/CMP/TEST/CALL/RET count=%d' % len(bad), flush=True)
for x in bad:
    print('   ', hex(x[0]), x[1], x[2], flush=True)
incs = [(i.address, i.mnemonic, i.op_str) for i in seg if i.mnemonic in ('inc', 'dec')]
print('INC/DEC count=%d' % len(incs), flush=True)
for x in incs:
    print('   ', hex(x[0]), x[1], x[2], flush=True)
# 外部跳入 (HEAD, 0x6F8E09]
land = []
for i in stream:
    if not (i.mnemonic.startswith('j') or i.mnemonic == 'call'):
        continue
    try:
        for op in i.operands:
            if op.type == 2:
                t = op.imm & 0xFFFFFFFF
                if HEAD < t <= 0x6F8E09:
                    land.append((i.address, i.mnemonic, i.op_str, hex(t)))
                break
    except Exception:
        pass
print('BRANCH_TARGETS_INSIDE_(HEAD,0x6F8E09] count=%d' % len(land), flush=True)
for x in land:
    print('   ', hex(x[0]), x[1], x[2], x[3], flush=True)
# 直接 E8/E9 调用者（全文件裸扫描 + 全流解码双证）
e8, e9 = [], []
for off in range(0, len(eng.raw) - 5):
    op = eng.raw[off]
    if op not in (0xE8, 0xE9):
        continue
    rel = struct.unpack_from('<i', eng.raw, off + 1)[0]
    # 用节表把 file_off 换算成 VA
    t = next((s for s in eng.SEC if s[3] <= off < s[3] + s[4]), None)
    if t is None:
        continue
    src_va = t[1] + off - t[3]
    tgt = (src_va + 5 + rel) & 0xFFFFFFFF
    if tgt == HEAD:
        (e8 if op == 0xE8 else e9).append(hex(src_va))
print('RAW_E8_TO_6F8DF0 count=%d %s' % (len(e8), e8), flush=True)
print('RAW_E9_TO_6F8DF0 count=%d %s' % (len(e9), e9), flush=True)

# ---------------------------------------------------------------- 6
sec('6 RETS IN [0x6F8DF0,0x6F9DB0) / VTABLE SLOT / push 0xA8EC30')
rets = [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in stream
        if HEAD <= i.address < BODY_HI and i.mnemonic.startswith('ret')]
print('RETS count=%d' % len(rets), flush=True)
for x in rets:
    print('   ', hex(x[0]), x[1], x[2], x[3], flush=True)
print('u32(0x7F4D24) =', hex(eng.u32(0x7F4D24)), ' 241*4 =', hex(241 * 4), flush=True)
push30 = []
for i in stream:
    try:
        for op in i.operands:
            if op.type == 2 and (op.imm & 0xFFFFFFFF) == 0xA8EC30:
                push30.append((i.address, i.mnemonic, i.op_str))
                break
    except Exception:
        pass
print('IMM_EQ_0xA8EC30 count=%d' % len(push30), flush=True)
for x in push30:
    print('   ', hex(x[0]), x[1], x[2], flush=True)

# ---------------------------------------------------------------- 7
sec('7 SYMBOL TABLE / DEBUG DIRECTORY / MAP FILES (符号名「未定名」依据)')
opt = eng.opt
dd = opt + 96
exp_rva, exp_sz = struct.unpack_from('<II', eng.raw, dd + 0)
imp_rva, imp_sz = struct.unpack_from('<II', eng.raw, dd + 8)
dbg_rva, dbg_sz = struct.unpack_from('<II', eng.raw, dd + 6 * 8)
print('MAGIC', hex(struct.unpack_from('<H', eng.raw, opt)[0]), flush=True)
print('EXPORT rva', hex(exp_rva), 'size', hex(exp_sz), flush=True)
print('IMPORT rva', hex(imp_rva), 'size', hex(imp_sz), flush=True)
print('DEBUG  rva', hex(dbg_rva), 'size', hex(dbg_sz), flush=True)
if dbg_rva:
    do = eng.fo(eng.IB + dbg_rva)
    print('DEBUG_DIR_FILE_OFF', hex(do) if do else None, flush=True)
    for k in range(dbg_sz // 28):
        ch, ts, maj, minr, typ, sod, aor, ptr = struct.unpack_from('<IIHHIIII', eng.raw, do + k * 28)
        print('  ENTRY%d type=%d sizeOfData=0x%X ptrRaw=0x%X' % (k, typ, sod, ptr), flush=True)
        if ptr and sod:
            blob = eng.raw[ptr:ptr + min(sod, 48)]
            print('   DATA', repr(blob[:48]), flush=True)
mapdir = os.path.join(ROOT, 'ra2youli')
maps = sorted(f for f in os.listdir(mapdir) if f.upper().endswith('.MAP'))
print('MAP_FILES', maps, flush=True)
for m in maps:
    b = open(os.path.join(mapdir, m), 'rb').read()
    print('  ', m, 'size', len(b), 'head_hex', b[:24].hex(), 'head_repr', repr(b[:24]), flush=True)
    low = b.lower()
    for marker in (b'publics by value', b'publics by name', b'static symbols', b'start', b'length', b'class', b'mappack'):
        if marker in low:
            print('     contains marker', marker, flush=True)

# ---------------------------------------------------------------- 8
sec('8 HARNESS CONSTANTS / grep count (既有 Harness 不读本 VA)')
h = os.path.join(ROOT, r'lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py')
hb = open(h, 'rb').read()
print('GREP_A8EC34_count', len(re.findall(rb'A8EC34|a8ec34', hb)), flush=True)
hl = hb.decode('utf-8', errors='replace').splitlines()
for n in range(3831, 3842):
    print('  harness:%d: %s' % (n, hl[n - 1][:140]), flush=True)

# ---------------------------------------------------------------- 9
sec('9 §6.2 SOURCE LINE CITATIONS — exact line contents (核对行号是否对得上)')
dump_lines(r'ra2render\dllmain.cpp', [(25, 31)])
dump_lines(r'ra2render\blitter_hooks.cpp', [(1341, 1344), (1351, 1368), (1393, 1399), (1406, 1416)])
dump_lines(r'ra2render\blitter_hooks.cpp', [(547, 547), (237, 242), (3781, 3782), (3696, 3698)])
dump_lines(r'ra2render\ra2render.ini', [(21, 25)])
dump_lines(r'ra2render\ra2render.h', [(30, 35)])
dump_lines(r'lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py', [(21, 25), (1070, 1084), (1080, 1084)])
dump_lines(r'docs\re\re_sprint_S8_report.md', [(127, 137)])
dump_lines(r'docs\re\net_sync_checksum.md', [(859, 868)])
dump_lines(r'lead\re_line_20261105\W4_FIELD_SPEC\TASK.md', [(40, 46)])
dump_lines(r'lead\re_line_20261105\W3_COSTBOUND\sections\Q3_SAMPLE_PLAN.md', [(57, 62)])
dump_lines(r'lead\re_line_20261105\W3_COSTBOUND\W3_COSTBOUND.md', [(283, 283)])
dump_lines(r'docs\re\ARCHITECTURE_ATLAS.md', [(1259, 1259), (1323, 1323), (1331, 1331)])

# 两份文档内部引用的 blitter_hooks.cpp:495-502 在**当前**源码里究竟是什么
sec('10 STALE LINE REF CHECK: current blitter_hooks.cpp:495-502 (docs cite this for the 9B hook)')
dump_lines(r'ra2render\blitter_hooks.cpp', [(493, 506)])

sec('11 END')
print('PROBE_DONE', datetime.datetime.now().isoformat(), flush=True)
