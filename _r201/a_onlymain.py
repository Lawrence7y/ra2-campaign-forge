#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 卡 A：11 个 only_main 宿主的真实装填序列与 only_main 口径订正。
一条命令完成：复现校验、逐宿主取证、机械理由判定、宽松复扫、交集差集、两组反控。"""
import sys, struct, json, bisect, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}

REGNAME = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
recs = []
pos = T['rawptr']; end = T['rawptr'] + T['rawsize']
while pos < end - 6:
    if RAW[pos] != 0xC7: pos += 1; continue
    modrm = RAW[pos + 1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4 or (rm == 5 and mod == 0): pos += 1; continue
    va = LO + (pos - T['rawptr'])
    if mod == 1:
        disp = struct.unpack_from('<b', RAW, pos + 2)[0]; imm = struct.unpack_from('<I', RAW, pos + 3)[0]
        recs.append((va, REGNAME[rm], disp, imm)); pos += 7
    elif mod == 2:
        disp = struct.unpack_from('<i', RAW, pos + 2)[0]; imm = struct.unpack_from('<I', RAW, pos + 6)[0]
        recs.append((va, REGNAME[rm], disp, imm)); pos += 10
    else: pos += 1
sub = [r for r in recs if 1 <= r[2] <= 9 and r[3] in VT]
main11 = [r for r in sub if MD[r[3]] == 0]
eq_md = [r for r in sub if r[2] == MD[r[3]]]
ne_md = [r for r in sub if r[2] != MD[r[3]]]

BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
CALLAT = []
p2 = 0
while p2 < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[p2:p2 + 65536], LO + p2):
        got = True
        if mn == 'call' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): CALLAT.append((off, t))
        p2 += sz
    if not got: p2 += 1
SORT = sorted(set(t for _, t in CALLAT))
def host_of(c, S=None):
    S = S if S is not None else SORT
    i = bisect.bisect_left(S, c) - 1
    return S[i] if i >= 0 else None
def next_entry(c, S=None):
    S = S if S is not None else SORT
    i = bisect.bisect_right(S, c)
    return S[i] if i < len(S) else HI
byhost = collections.defaultdict(list)
for r in sub: byhost[host_of(r[0])].append(r)

def insns_of(h, hi):
    o = P.r2o(h)
    if o is None: return []
    return [(i.address, i.size, i.bytes.hex(), i.mnemonic, i.op_str)
            for i in md.disasm(RAW[o:o + (hi - h)], h)]

def table_stores(ins):
    out = []; has_main = has_sub = False
    for ad, sz, bs, mn, op in ins:
        if mn == 'mov' and op.startswith('dword ptr [') and ', 0x' in op:
            try: iv = int(op.rsplit(', ', 1)[1], 16)
            except Exception: continue
            if iv not in VT: continue
            out.append((ad, op, iv, MD[iv]))
            if MD[iv] == 0: has_main = True
            else: has_sub = True
    return has_main, has_sub, out

def classify(limit=4096, S=None, BH=None):
    S = S if S is not None else SORT
    BH = BH if BH is not None else byhost
    both = only_sub = only_main = 0; om = []
    for h, rs in BH.items():
        if h is None: continue
        hi = min(next_entry(h, S), h + limit)
        hm, hs, _ = table_stores(insns_of(h, hi))
        if hm and hs: both += 1
        elif hs: only_sub += 1
        else: only_main += 1; om.append(h)
    return both, only_sub, only_main, sorted(om)

def loose_scan(h, span=4096):
    stop = h + span; hits = []
    o = P.r2o(h)
    if o is not None:
        for i in md.disasm(RAW[o:o + (stop - h)], h):
            if i.mnemonic == 'mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
                try: iv = int(i.op_str.rsplit(', ', 1)[1], 16)
                except Exception: continue
                if iv in VT:
                    fh = host_of(i.address)
                    hits.append(dict(at=hex(i.address), bytes=i.bytes.hex(),
                                     ins=i.mnemonic + ' ' + i.op_str, imm=hex(iv), cls=CLS[iv],
                                     shape='disasm_mov_mem_imm', func=hex(fh) if fh else None))
    p = T['rawptr'] + (h - LO); e = T['rawptr'] + (min(stop, HI) - LO)
    while p < e - 6:
        if RAW[p] != 0xC7: p += 1; continue
        modrm = RAW[p + 1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
        if reg != 0: p += 1; continue
        va = LO + (p - T['rawptr'])
        if mod == 0 and rm == 5:
            imm = struct.unpack_from('<I', RAW, p + 6)[0]; sz = 10; disp = s32(struct.unpack_from('<I', RAW, p + 2)[0]); shape = 'C7_0_mod0_rm5'
        elif mod == 0:
            imm = struct.unpack_from('<I', RAW, p + 2)[0]; sz = 6; disp = 0; shape = 'C7_0_mod0'
        elif mod == 1:
            disp = struct.unpack_from('<b', RAW, p + 2)[0]; imm = struct.unpack_from('<I', RAW, p + 3)[0]; sz = 7; shape = 'C7_0_mod1'
        elif mod == 2:
            disp = struct.unpack_from('<i', RAW, p + 2)[0]; imm = struct.unpack_from('<I', RAW, p + 6)[0]; sz = 10; shape = 'C7_0_mod2'
        else: p += 1; continue
        if imm in VT:
            fh = host_of(va)
            hits.append(dict(at=hex(va), bytes=RAW[p:p + sz].hex(), ins='C7 /0 mov dword ptr [reg+disp], imm32',
                             imm=hex(imm), cls=CLS[imm], disp=disp, shape=shape,
                             func=hex(fh) if fh else None))
        p += sz
    seen = set(); out = []
    for x in hits:
        if x['at'] in seen: continue
        seen.add(x['at']); out.append(x)
    return sorted(out, key=lambda z: int(z['at'], 16))

# ============ 1. 复现校验 ============
print('===== 1. 复现校验 =====')
ck('C0a sub=697', len(sub) == 697, len(sub))
ck('C0b main11=11', len(main11) == 11, len(main11))
ck('C0c hosts=262', len(byhost) == 262, len(byhost))
b0, o0, m0, om0 = classify(4096)
ck('C0d (both,only_sub,only_main)=(251,0,11)', (b0, o0, m0) == (251, 0, 11), (b0, o0, m0))
ck('C0e disp8==mdisp 686 / 不等 11', (len(eq_md), len(ne_md)) == (686, 11), (len(eq_md), len(ne_md)))
if fails:
    print('\nFAIL: 复现校验未通过，停止后续。', fails)
    print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
    sys.exit(1)

# ============ 2+3+4. 逐宿主取证 / 机械理由 / 宽松复扫 ============
print('\n===== 2/3/4. 11 个 only_main 宿主取证 =====')
print('口径订正: R200 的 else 分支实际判据为 not has_sub (非 has_main 与 has_sub 皆 False)。')
print('  有主表装填(has_main=True)的 only_main 宿主: %d 个; 完全零装填: %d 个' %
      (sum(1 for h in om0 if table_stores(insns_of(h, min(next_entry(h), h + 4096)))[0]),
       sum(1 for h in om0 if not any(table_stores(insns_of(h, min(next_entry(h), h + 4096)))[:2]))))
detail = []; reasons_map = {}; loose_all = {}
for h in om0:
    hi = min(next_entry(h), h + 4096)
    o = P.r2o(h)
    prev = RAW[o - 1] if o and o > 0 else None
    head = RAW[o:o + 16].hex() if o else None
    ins = insns_of(h, hi)
    hm, hs, tst = table_stores(ins)
    has_call = any(x[3] == 'call' for x in ins)
    has_ret = any(x[3].startswith('ret') for x in ins)
    raw_vt = [r for r in recs if h <= r[0] < hi and r[3] in VT]
    owner = list(byhost[h])
    owner_va = [r[0] for r in owner]
    loose = loose_scan(h, 4096)
    in_win = [x for x in loose if h <= int(x['at'], 16) < hi]
    after_win = [x for x in loose if hi <= int(x['at'], 16) < h + 4096]
    # (ii) 严格按字节形状判定：shape 必须是 C7 /0 mod1 或 mod2 且 disp 在 1..9 才算合法子表 store。
    #      其余（C7_0_mod0 即 disp=0、mod0 直接 disp32、reg!=0、或线性反汇编得到的其他形状）才归入 (ii)。
    legal_sub_shapes = ('C7_0_mod1', 'C7_0_mod2')
    odd = [x for x in loose if x['shape'] not in legal_sub_shapes]
    shape_evidence = []
    for x in odd:
        a = int(x['at'], 16); o = P.r2o(a)
        raw2 = RAW[o:o + 2].hex() if o else None
        shape_evidence.append(dict(at=x['at'], bytes2=raw2, shape=x['shape'], imm=x['imm'],
                                   ins=x.get('ins', 'C7 /0 mov dword ptr [reg+disp], imm32')))
    # 线性反汇编失步判据：owner_sub 的字节是合法 C7 /0 disp8 (c746/c747)，
    #   但窗口内从 h 线性反汇编得到的 text_stores 地址集合不含该 owner 地址。
    ts_addr = set(x[0] for x in tst)
    desync = [(hex(r[0]), RAW[P.r2o(r[0]):P.r2o(r[0]) + 2].hex(), r[2])
              for r in owner if h <= r[0] < hi and hex(r[0]) not in ts_addr]
    owner_outside = [hex(v) for v in owner_va if not (h <= v < hi)]
    owner_shapes = [(hex(r[0]), RAW[P.r2o(r[0]):P.r2o(r[0]) + 2].hex(), r[2], hex(r[3]), CLS[r[3]])
                    for r in owner]
    reasons = []
    evidence = {}
    if owner_outside or after_win or next_entry(h) < h + 4096:
        reasons.append('(i)')
        evidence['(i)'] = dict(owner_store_outside_window=owner_outside,
                               next_entry=hex(next_entry(h)), h_plus_4096=hex(h + 4096),
                               win_hi=hex(hi), win_len=hi - h,
                               loose_after_win=[(x['at'], x['shape'], x['imm']) for x in after_win])
    if odd or desync:
        reasons.append('(ii)')
        evidence['(ii)'] = dict(nonlegal_shape_stores=shape_evidence,
                                linear_disasm_desync_owner_sub=desync,
                                note='owner_sub 字节为合法 c746/c747 (C7 /0 disp8)，但线性反汇编从宿主起点失步未将其列入 text_stores')
    if not hm and not hs:
        reasons.append('(iii)')
        evidence['(iii)'] = dict(note='no imm-in-VT memory-write store classified by R200 disasm in [h,h+4096)',
                                 owner_sub_stores=owner_shapes,
                                 loose_hits=[(x['at'], x['shape'], x['imm']) for x in loose])
    reasons = sorted(set(reasons))
    reasons_map[hex(h)] = dict(reasons=reasons, evidence=evidence, has_main=hm, has_sub=hs)
    loose_all[hex(h)] = loose
    rec = dict(host=hex(h), prev_byte=hex(prev) if prev is not None else None, head16=head,
               hi=hex(hi), win_len=hi - h, next_entry=hex(next_entry(h)),
               has_main=hm, has_sub=hs, has_call=has_call, has_ret=has_ret,
               insns=[[hex(a), bs, mn, op] for a, sz, bs, mn, op in ins],
               text_stores=[[hex(a), op, hex(iv), CLS[iv], mdsp] for a, op, iv, mdsp in tst],
               raw_vt_stores=[[hex(va), rn, disp, hex(imm), CLS[imm]] for va, rn, disp, imm in raw_vt],
               owner_sub=[[hex(va), rn, disp, hex(imm), CLS[imm], MD[imm]] for va, rn, disp, imm in owner],
               owner_shapes=owner_shapes)
    detail.append(rec)
    print('\n--- host %s prev=%s head16=%s ---' % (rec['host'], rec['prev_byte'], rec['head16']))
    print('    window [%s,%s) len=%d next_entry=%s has_main=%s has_sub=%s has_call=%s has_ret=%s' %
          (rec['host'], rec['hi'], rec['win_len'], rec['next_entry'], hm, hs, has_call, has_ret))
    print('    owner_sub (disp 1..9 imm in VT): %s' % rec['owner_sub'])
    print('    raw_vt_stores in window: %s' % rec['raw_vt_stores'])
    print('    disasm text stores in window: %s' % rec['text_stores'])
    print('    insns (%d):' % len(ins))
    for a, sz, bs, mn, op in ins:
        print('        %s  %-20s %-8s %s' % (hex(a), bs, mn, op))
    print('    REASON %s evidence=%s' % (reasons, json.dumps(evidence, ensure_ascii=False)))
    print('    LOOSE 4096 hits (%d): %s' % (len(loose), [(x['at'], x['shape'], x['imm'], x['func']) for x in loose]))
    ck('C2 win %s has insns' % rec['host'], len(ins) > 0, len(ins))
    ck('C3 win %s reason assigned' % rec['host'], len(reasons) > 0, reasons)

ck('C1 only_main hosts == 11', len(om0) == 11, len(om0))

# ============ 5. 交集/差集 ============
print('\n===== 5. only_main 与 main11 宿主交集/差集 =====')
m11h = sorted(set(host_of(r[0]) for r in main11))
omh = sorted(om0)
inter = sorted(set(m11h) & set(omh))
m11only = sorted(set(m11h) - set(omh))
omonly = sorted(set(omh) - set(m11h))
print('   main11 宿主 (%d): %s' % (len(m11h), [hex(x) for x in m11h]))
print('   only_main 宿主 (%d): %s' % (len(omh), [hex(x) for x in omh]))
print('   交集 (%d): %s' % (len(inter), [hex(x) for x in inter]))
print('   仅 main11 (%d): %s' % (len(m11only), [hex(x) for x in m11only]))
print('   仅 only_main (%d): %s' % (len(omonly), [hex(x) for x in omonly]))
ck('C5a 交集=6', len(inter) == 6, len(inter))
ck('C5b 仅 main11=4', len(m11only) == 4, len(m11only))
ck('C5c 仅 only_main=5', len(omonly) == 5, len(omonly))

# ============ 6. 反控 ============
print('\n===== 6. 反控 =====')
print('   (a) 窗口上限变化:')
ctrl_a = {}
for lim in (4096, 8192, 16384):
    b, os_, m, om = classify(lim)
    ctrl_a[str(lim)] = dict(both=b, only_sub=os_, only_main=m, hosts=len(byhost), om=[hex(x) for x in om])
    print('       limit=%-6d both=%-4d only_sub=%-3d only_main=%-3d hosts=%d om=%s' %
          (lim, b, os_, m, len(byhost), [hex(x) for x in om]))
SORT2 = sorted(set(t for _, t in CALLAT if P.r2o(t) and RAW[P.r2o(t) - 1] in (0xC3, 0xCC, 0x90)))
byhost2 = collections.defaultdict(list)
for r in sub: byhost2[host_of(r[0], SORT2)].append(r)
print('   (b) 宿主定义改为 CALLAT 目标且前一字节 in {C3,CC,90}: 目标数 %d -> %d' % (len(SORT), len(SORT2)))
b, os_, m, om = classify(4096, SORT2, byhost2)
ctrl_b = dict(both=b, only_sub=os_, only_main=m, hosts=len(byhost2), om=[hex(x) for x in om])
print('       both=%-4d only_sub=%-3d only_main=%-3d hosts=%d om=%s' %
      (b, os_, m, len(byhost2), [hex(x) for x in om]))
ck('C6a 反控(a) 三分类已计算', len(ctrl_a) == 3, list(ctrl_a.keys()))
ck('C6b 反控(b) 三分类已计算', ctrl_b['hosts'] >= 0, ctrl_b['hosts'])

out = dict(
    reproduce=dict(sub=len(sub), main11=len(main11), hosts=len(byhost), both=b0, only_sub=o0,
                   only_main=m0, eq_md=len(eq_md), ne_md=len(ne_md)),
    detail=detail, reasons=reasons_map,
    loose={k: [{kk: vv for kk, vv in x.items()} for x in v] for k, v in loose_all.items()},
    sets=dict(m11_hosts=[hex(x) for x in m11h], om_hosts=[hex(x) for x in omh],
              intersection=[hex(x) for x in inter], m11_only=[hex(x) for x in m11only],
              om_only=[hex(x) for x in omonly]),
    controls=dict(a=ctrl_a, b=ctrl_b),
    asserts=N, fails=fails)
json.dump(out, open('/home/t628/projects/ra2-campaign-forge/_r201/a_onlymain.json', 'w'),
          ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
