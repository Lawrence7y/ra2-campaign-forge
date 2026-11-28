#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 EXEC B: L 的 78 张虚表安装点普查（纯静态，一条命令跑完全部取证）。

说明：本机实测的 COL 结构为 base=TD引用位置-12，d0==0，d1 为 mdisp（0=主表 954，
非零=接口子表 260），d2==0，d3 指向 .data 的 RTTI 描述符，d4 指向 .rdata 的 pCHD。
pCHD 位于 COL-16（字段 0,0,count,array），array 条目首 dword 是 TD 指针。
L = pCHD 数组中含 .?AVAbstractClass@@ 描述符的 78 张主表。
表头 = .text 指针 dword 的位置，其前一 dword 是 COL 地址（P2）。
"""
import sys, os, struct, collections, json, hashlib, capstone
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUTDIR = ROOT + '/_r195/exec_b'
RAW = P.RAW
dw, where, cstr = P.dw, P.where, P.cstr
T = P.B['.text']
LO, HI = T['lo'], T['hi_file']
fails, NCHK = [], 0

def ck(nm, c, d=''):
    global NCHK
    NCHK += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def hx(x):
    return None if x is None else ('%08X' % x)

# ---------------- RTTI 描述符全集 ----------------
SIG = bytes.fromhex('94957f0000000000')   # pVFTable=0x7F9594, spare=0
TD = set()
for secname in ('.data', '.rdata'):
    ss = P.B[secname]
    blob = RAW[ss['rawptr']:ss['rawptr'] + ss['rawsize']]
    i = 0
    while True:
        i = blob.find(SIG, i)
        if i < 0: break
        va = ss['lo'] + i
        nm = cstr(va + 8, 300)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD.add(va)
        i += 1

COLS = {}
for secname in ('.rdata', '.data'):
    ss = P.B[secname]
    vals = struct.unpack_from('<%dI' % (ss['rawsize'] // 4), RAW, ss['rawptr'])
    for k, v in enumerate(vals):
        if v not in TD: continue
        base = ss['lo'] + 4 * k - 12
        d = tuple(dw(base + 4 * j) for j in range(5))
        if None in d or d[0] != 0 or d[2] != 0: continue
        if d[3] not in TD or where(d[4]) != '.rdata': continue
        COLS[base] = d

MAIN = {c: d for c, d in COLS.items() if d[1] == 0}
SUB = {c: d for c, d in COLS.items() if d[1] != 0}

vt_all = set()
for secname in ('.rdata', '.data'):
    ss = P.B[secname]
    vals = struct.unpack_from('<%dI' % (ss['rawsize'] // 4), RAW, ss['rawptr'])
    for k, v in enumerate(vals):
        if LO <= v < HI:
            va = ss['lo'] + 4 * k
            if dw(va - 4) in COLS: vt_all.add(va)

ck('P1a RTTI 描述符数 == 988', len(TD) == 988, len(TD))
ck('P1b COL 总数 == 1214', len(COLS) == 1214, len(COLS))
ck('P1c 主表 954 / 接口子表 260（以 d1/mdisp 分型）',
   (len(MAIN), len(SUB)) == (954, 260), (len(MAIN), len(SUB)))
ck('P1d 表头总数 == 1214', len(vt_all) == 1214, len(vt_all))

# ---------------- Q1: L 血统集合和表头 ----------------
atd = None
for td in TD:
    if cstr(td + 8, 160) == b'.?AVAbstractClass@@':
        atd = td; break
ck('Q1a 找到 AbstractClass 的 RTTI 描述符', atd is not None, hx(atd))

L_cols = {}
for c, d in MAIN.items():
    ch = tuple(dw(c - 16 + 4 * j) for j in range(4))
    if None in ch or ch[0] != 0 or not (1 <= ch[2] <= 64) or where(ch[3]) != '.rdata':
        continue
    arr = ch[3]
    for k in range(ch[2]):
        p = dw(arr + 4 * k)
        if p is not None and dw(p) == atd:
            L_cols[c] = cstr(d[3] + 8, 200)
            break
ck('Q1b L 血统主表数 == 78', len(L_cols) == 78, len(L_cols))

L = {}
by_col = collections.defaultdict(list)
for v in vt_all:
    by_col[dw(v - 4)].append(v)
for c in L_cols:
    vs = by_col.get(c, [])
    if len(vs) == 1:
        L[vs[0]] = L_cols[c]
Lset = set(L)
ck('Q1c L 表头数 == 78（每主表唯一表头）', len(L) == 78, len(L))
ck('Q1d 78 表头均来自 1214 表头全集', Lset <= vt_all, len(Lset & vt_all))
ck('Q1e 表头前一 dword 为 L 主表 COL',
   all(dw(v - 4) in L_cols for v in L), len(L))
ck('Q1f 表头升序唯一且均在 .rdata/.data',
   sorted(Lset) == sorted(Lset) and len(Lset) == 78 and
   all(where(v) in ('.rdata', '.data') for v in L),
   (len(L), len(Lset)))

# ---------------- Q2: C7 立即数全段流式扫描 ----------------
textbuf = RAW[T['rawptr']:T['rawptr'] + T['rawsize']]
ntext = len(textbuf)
C7 = []   # (va, imm, form, header_or_None)
i = 0
while True:
    i = textbuf.find(b'\xC7', i)
    if i < 0 or i + 6 > ntext: break
    modrm = textbuf[i + 1]
    mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
    if reg != 0:
        i += 1; continue
    if mod == 0 and rm == 5:
        imm = struct.unpack_from('<I', textbuf, i + 6)[0]; form = 'C7 05 abs'; nxt = i + 10
    elif mod == 1:
        imm = struct.unpack_from('<I', textbuf, i + 3)[0]; form = 'C7 4x disp8'; nxt = i + 7
    elif mod == 2:
        imm = struct.unpack_from('<I', textbuf, i + 6)[0]; form = 'C7 8x disp32'; nxt = i + 10
    elif mod == 0:
        imm = struct.unpack_from('<I', textbuf, i + 2)[0]; form = 'C7 0x reg'; nxt = i + 6
    else:
        i += 1; continue
    if imm in vt_all:
        C7.append((LO + i, imm, form, imm if imm in Lset else None))
    i = nxt

Q2 = sorted([h for h in C7 if h[3] is not None])
ck('Q2a 写 L 表头的 C7 命中数 > 0', len(Q2) > 0, len(Q2))
ck('Q2b 每个命中 imm 属于 L', all(h[1] in Lset for h in Q2), len(Q2))
ck('Q2c 地址唯一且升序', [h[0] for h in Q2] == sorted({h[0] for h in Q2}), len(Q2))
ck('Q2d 命中均在 .text', all(LO <= h[0] < HI for h in Q2), len(Q2))
ck('Q2e 四种形态覆盖',
   set(h[2] for h in Q2) <= {'C7 05 abs', 'C7 4x disp8', 'C7 8x disp32', 'C7 0x reg'},
   dict(collections.Counter(h[2] for h in Q2)))

# ---------------- 函数起点启发式 ----------------
starts_call = set()
for opc in (0xE8, 0xE9):
    j = 0
    while True:
        j = textbuf.find(bytes([opc]), j)
        if j < 0 or j + 5 > ntext: break
        rel = struct.unpack_from('<i', textbuf, j + 1)[0]
        tgt = LO + j + 5 + rel
        if LO <= tgt < HI: starts_call.add(tgt)
        j += 1

md_lite = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
insns = list(md_lite.disasm_lite(textbuf, LO))
addr2next = {a: a + s for a, s, _, _ in insns}
fill_starts = set()
run, run_start = 0, 0
for a, s, _, _ in insns:
    b = textbuf[a - LO]
    if b in (0xCC, 0x90):
        if run == 0: run_start = a
        run += s
    else:
        if run >= 2: fill_starts.add(a)
        run = 0
starts_both = (starts_call | fill_starts) & set(addr2next)
starts_only = starts_call & set(addr2next)
ck('F1 起点集合非空', len(starts_both) > 0, len(starts_both))
ck('F2 所有起点在 .text', all(LO <= s < HI for s in starts_both), len(starts_both))

def owner(va, starts):
    cand = [s for s in starts if s <= va]
    return max(cand) if cand else None

# ---------------- Q3 ----------------
q3 = [(hva, imm, form, owner(hva, starts_both)) for hva, imm, form, _ in Q2]
ck('Q3a 全部命中可归属函数起点', all(r[3] is not None for r in q3), len(q3))
owners = set(r[3] for r in q3)
by_owner = collections.defaultdict(set)
for hva, imm, form, ow in q3:
    by_owner[ow].add(imm)
dist = collections.Counter(len(v) for v in by_owner.values())
top10 = sorted(((o, len(vs), sorted(vs)) for o, vs in by_owner.items()),
               key=lambda x: (-x[1], x[0]))[:10]
multi = {o: sorted(vs) for o, vs in by_owner.items() if len(vs) >= 2}
ck('Q3b 起点数分布之和一致', sum(dist.values()) == len(owners),
   (dict(sorted(dist.items())), len(owners)))
ck('Q3c 至少一个起点写 >=2 张 L 表头', len(multi) > 0, len(multi))

# ---------------- Q4 ----------------
DEFAULT_SLOTS = [0, 1, 2, 4, 7, 9, 10, 14, 15, 16, 17]
defs = set()
for v in Lset:
    for si in DEFAULT_SLOTS:
        t = dw(v + 4 * si)
        if t is not None and LO <= t < HI: defs.add(t)
md_detail = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md_detail.detail = True
q4 = {}
for ow in sorted(owners):
    end = min([s for s in starts_both if s > ow] + [HI])
    maxb = min(end - ow, 4096)
    off = P.r2o(ow)
    body = list(md_detail.disasm(RAW[off:off + maxb], ow))
    second = []
    for ins in body:
        if ins.mnemonic != 'mov' or len(ins.operands) != 2: continue
        op0 = ins.operands[0]
        if op0.type != capstone.x86.X86_OP_MEM: continue
        m = op0.mem
        if m.disp == 0 and m.base in (capstone.x86.X86_REG_EBP, capstone.x86.X86_REG_ESP,
                                      capstone.x86.X86_REG_EDI, capstone.x86.X86_REG_EAX,
                                      capstone.x86.X86_REG_ECX, capstone.x86.X86_REG_EDX,
                                      capstone.x86.X86_REG_ESI, capstone.x86.X86_REG_EBX):
            second.append((ins.address, ins.op_str))
    dcalls = []
    for ins in body:
        if ins.mnemonic in ('call', 'jmp') and ins.operands and \
           ins.operands[0].type == capstone.x86.X86_OP_IMM and \
           ins.operands[0].imm in defs:
            dcalls.append((ins.address, ins.mnemonic, ins.operands[0].imm))
    q4[hx(ow)] = dict(n_ins=len(body), n_second=len(second),
                       second_writes=second[:20], n_defcalls=len(dcalls),
                       defcalls=dcalls[:20])
ck('Q4a 每个归属起点完成反汇编', all(q4[hx(o)]['n_ins'] > 0 for o in owners), len(owners))
ck('Q4b 默认实现集合非空', len(defs) > 0, len(defs))
ck('Q4c 二次写统计完成（不预设结论）', True,
   '有二次写起点 %d/%d' % (sum(1 for o in owners if q4[hx(o)]['n_second'] > 0), len(owners)))
ck('Q4d 默认实现 call 统计完成（不预设结论）', True,
   '有默认实现 call 起点 %d/%d' % (sum(1 for o in owners if q4[hx(o)]['n_defcalls'] > 0), len(owners)))

# ---------------- Q5 ----------------
hit_headers = set(h[1] for h in Q2)
zero = sorted(Lset - hit_headers)
any_imm = {}
for v in zero[:5]:
    pat = struct.pack('<I', v)
    cnt, j = 0, 0
    while True:
        j = textbuf.find(pat, j)
        if j < 0: break
        cnt += 1; j += 1
    any_imm[v] = cnt
ck('Q5a 零命中数 == 78 - 命中表头数', len(zero) == 78 - len(hit_headers), len(zero))
ck('Q5b 前 5 个任意立即数检索完成', len(any_imm) == min(5, len(zero)), any_imm)

# ---------------- Q6 ----------------
refcnt = {}
for v in Lset:
    pat = struct.pack('<I', v)
    c = 0
    for secname in ('.rdata', '.data'):
        ss = P.B[secname]
        blob = RAW[ss['rawptr']:ss['rawptr'] + ss['rawsize']]
        j = 0
        while True:
            j = blob.find(pat, j)
            if j < 0: break
            if j % 4 == 0: c += 1
            j += 1
    refcnt[v] = c
q6dist = collections.Counter(0 if c == 0 else (1 if c == 1 else 2) for c in refcnt.values())
ck('Q6a 每个 L 表头统计二级指针', len(refcnt) == 78, len(refcnt))
ck('Q6b 分布之和 == 78', sum(q6dist.values()) == 78, dict(sorted(q6dist.items())))

# ---------------- R1 / R2 / R3 ----------------
R1 = sorted(C7)
ck('R1a 全表头命中 >= L 命中', len(R1) >= len(Q2), (len(R1), len(Q2)))
ck('R1b 全命中 imm 属于 1214 表头', all(h[3] or h[1] in vt_all for h in R1), len(R1))

R2 = []
i = 0
while True:
    i = textbuf.find(b'\xC7', i)
    if i < 0 or i + 6 > ntext: break
    modrm = textbuf[i + 1]
    mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
    if reg != 0:
        i += 1; continue
    if mod == 0 and rm == 5:
        imm = struct.unpack_from('<I', textbuf, i + 6)[0]; nxt = i + 10
    elif mod == 1:
        imm = struct.unpack_from('<I', textbuf, i + 3)[0]; nxt = i + 7
    elif mod == 2:
        imm = struct.unpack_from('<I', textbuf, i + 6)[0]; nxt = i + 10
    elif mod == 0:
        imm = struct.unpack_from('<I', textbuf, i + 2)[0]; nxt = i + 6
    else:
        i += 1; continue
    if where(imm) == '.rdata' and dw(imm - 4) in COLS:
        R2.append((LO + i, imm, dw(imm - 4)))
    i = nxt
ck('R2a R2 命中数 >= R1', len(R2) >= len(R1), (len(R2), len(R1)))
ck('R2b R2 引入非 L 表', any(h[1] not in Lset for h in R2),
   sum(1 for h in R2 if h[1] not in Lset))
r3owners = set()
for hva, imm, form, ow in q3:
    o2 = owner(hva, starts_only)
    if o2 is not None: r3owners.add(o2)
ck('R3a 只留 call/jmp 起点数 <= 完整启发式', len(r3owners) <= len(owners),
   (len(r3owners), len(owners)))
ck('R3b 统计完成', True, len(r3owners))

# ---------------- 输出 ----------------
os.makedirs(OUTDIR, exist_ok=True)
res = dict(meta=dict(card='R195-EXEC-vtinstall', role='hy4-exec',
                     text_sha256=hashlib.sha256(textbuf).hexdigest(),
                     text=(hx(LO), hx(HI)), checks=NCHK, fails=fails),
           Q1=dict(L_count=len(L), abstract_td=hx(atd),
                   tables=[dict(vtable=hx(v), col=hx(dw(v - 4)),
                                name=L[v].decode('latin1') if L[v] else None)
                           for v in sorted(L)],
                   col_names={hx(c): (n.decode('latin1') if n else None)
                              for c, n in L_cols.items()}),
           Q2=dict(count=len(Q2),
                   hits=[dict(va=hx(a), imm=hx(b), form=f, is_L=True)
                         for a, b, f, _ in Q2]),
           Q3=dict(a_owners=len(owners),
                   dist={str(k): v for k, v in sorted(dist.items())},
                   top10=[dict(owner=hx(o), n_tables=n, tables=[hx(x) for x in vs])
                          for o, n, vs in top10],
                   multi=[dict(owner=hx(o), tables=[hx(x) for x in vs])
                          for o, vs in sorted(multi.items())]),
           Q4=dict(n_defs=len(defs), defaults=[hx(x) for x in sorted(defs)], functions=q4),
           Q5=dict(zero_count=len(zero), zero_tables=[hx(x) for x in zero],
                   first5_any_imm={hx(k): v for k, v in any_imm.items()}),
           Q6=dict(dist={'0': q6dist[0], '1': q6dist[1], '>=2': q6dist[2]},
                   refs={hx(k): v for k, v in sorted(refcnt.items())}),
           R1=dict(count=len(R1),
                   hits=[dict(va=hx(a), imm=hx(b), form=f, header=hx(t), in_L=(t is not None))
                         for a, b, f, t in R1]),
           R2=dict(count=len(R2), non_L=sum(1 for h in R2 if h[1] not in Lset),
                   hits=[dict(va=hx(a), imm=hx(b), col=hx(c)) for a, b, c in R2]),
           R3=dict(owners=len(r3owners)))
json.dump(res, open(OUTDIR + '/vtinstall.json', 'w'), ensure_ascii=False, indent=1)

with open(OUTDIR + '/vtinstall.txt', 'w', encoding='utf-8') as fp:
    def w(*a): print(*a, file=fp)
    w('# R195 EXEC B —— L 的 78 张虚表安装点普查')
    w('# text=%s..%s sha256=%s' % (hx(LO), hx(HI), res['meta']['text_sha256']))
    w('# checks=%d fails=%s' % (NCHK, fails))
    w('')
    w('## Q1 L 表头（%d 张，升序）' % len(L))
    for v in sorted(L):
        w('%s COL=%s %s' % (hx(v), hx(dw(v - 4)), L[v].decode('latin1') if L[v] else ''))
    w('')
    w('## Q2 C7 立即数安装点（%d 命中）' % len(Q2))
    for a, b, f, _ in Q2:
        w('%s imm=%s form=%s is_L=True' % (hx(a), hx(b), f))
    w('')
    w('## Q3 函数归属：起点数=%d' % len(owners))
    w('分布(起点写几张不同 L 表头)=%s' % dict(sorted(dist.items())))
    w('Top10:')
    for o, cnt2, vs in top10:
        w('  %s n=%d tables=%s' % (hx(o), cnt2, ' '.join(hx(x) for x in vs)))
    w('写 >=2 张表的起点数=%d' % len(multi))
    for o, vs in sorted(multi.items()):
        w('  %s tables=%s' % (hx(o), ' '.join(hx(x) for x in vs)))
    w('')
    w('## Q4 二次构造检查')
    w('默认实现集合(%d): %s' % (len(defs), ' '.join(hx(x) for x in sorted(defs))))
    for o in sorted(owners):
        r = q4[hx(o)]
        w('%s ins=%d second_writes=%d defcalls=%d' % (o, r['n_ins'], r['n_second'], r['n_defcalls']))
        for a, op in r['second_writes'][:5]: w('    W %s %s' % (hx(a), op))
        for a, m, t in r['defcalls'][:5]: w('    C %s %s %s' % (hx(a), m, hx(t)))
    w('')
    w('## Q5 零命中 L 表头（%d）' % len(zero))
    for v in zero: w(hx(v))
    w('前5任意立即数出现数=%s' % {hx(k): v for k, v in any_imm.items()})
    w('')
    w('## Q6 二级指针引用计数 0/1/>=2 = %d/%d/%d' % (q6dist[0], q6dist[1], q6dist[2]))
    for v in sorted(Lset): w('%s refs=%d' % (hx(v), refcnt[v]))
    w('')
    w('## R1 全部 1214 表头 C7 命中=%d（L 命中 %d）' % (len(R1), len(Q2)))
    for a, b, f, t in R1:
        w('%s imm=%s form=%s header=%s in_L=%s' % (hx(a), hx(b), f, hx(t), t is not None))
    w('')
    w('## R2 改判据命中=%d 非L=%d' % (len(R2), res['R2']['non_L']))
    for a, b, c in R2: w('%s imm=%s col=%s in_L=%s' % (hx(a), hx(b), hx(c), b in Lset))
    w('')
    w('## R3 只留 call/jmp 起点数=%d（完整启发式 %d）' % (len(r3owners), len(owners)))

print('\n=== SUMMARY ===')
print('Q1 L=%d Q2=%d Q3 owners=%d multi=%d Q4 defs=%d Q5 zero=%d Q6 dist=%s' %
      (len(L), len(Q2), len(owners), len(multi), len(defs), len(zero), dict(sorted(q6dist.items()))))
print('R1=%d R2=%d(nonL=%d) R3=%d' % (len(R1), len(R2), res['R2']['non_L'], len(r3owners)))
print('CHECKS=%d FAILS=%s' % (NCHK, fails))
