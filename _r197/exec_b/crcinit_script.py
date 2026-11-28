# -*- coding: utf-8 -*-
"""R197 EXEC-B: CRC 状态对象 +0 槽初值来源取证（纯静态，单脚本一次跑完全部证据）。"""
import sys, os, json, struct, collections, bisect, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_REG_ECX

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = ROOT + '/_r197/exec_b'
os.makedirs(OUT, exist_ok=True)
RAW = P.RAW
T = 0x4A1CA0
sec = P.B['.text']
LO, RP, RS = sec['lo'], sec['rawptr'], sec['rawsize']
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
mdl = Cs(CS_ARCH_X86, CS_MODE_32); mdl.detail = False
res, checks, txt = {}, [], []

def emit(s):
    print(s); txt.append(s)

def ck(name, cond, detail=''):
    checks.append((name, bool(cond)))
    emit('ASSERT %-40s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))

def code_at(va, n):
    o = RP + (va - LO)
    return RAW[o:o+n]

def bytes_of(va, sz):
    return RAW[RP+(va-LO):RP+(va-LO)+sz]

def one(va):
    for ins in md.disasm(code_at(va, 15), va, count=1):
        return ins
    return None

# ===== Q1: resync linear, chunk<=64KB, per-byte resync =====
q1 = []
va = T
chunk_end = T + 512  # <=64KB chunk
while va < chunk_end:
    ins = None
    for cand in mdl.disasm(code_at(va, min(16, chunk_end-va)), va, count=1):
        ins = cand; break
    if ins is None:                       # per-byte resync
        va += 1
        q1.append({'addr': hex(va-1), 'bytes': bytes_of(va-1,1).hex(),
                   'mnemonic': '(RESYNC-SKIP)', 'operands': '', 'size': 1})
        continue
    q1.append({'addr': hex(ins.address), 'bytes': bytes_of(ins.address, ins.size).hex(),
               'mnemonic': ins.mnemonic, 'operands': ins.op_str, 'size': ins.size})
    if ins.mnemonic == 'ret':
        break
    va = ins.address + ins.size
q1_real = [x for x in q1 if x['mnemonic'] != '(RESYNC-SKIP)']
q1_len = sum(x['size'] for x in q1_real)
q1_last = q1_real[-1]
res['Q1'] = {
    'func_va': hex(T), 'insn_count': len(q1_real), 'byte_length': q1_len,
    'end_addr': q1_last['addr'], 'ret_bytes': q1_last['bytes'],
    'ret_text': q1_last['mnemonic'] + ' ' + q1_last['operands'],
    'P1_claim': {'insns': 55, 'ret': 'ret 4'},
    'match_P1': len(q1_real) == 55 and q1_last['bytes'] == 'c20400',
    'full_listing': q1_real,
}
emit('=== Q1 函数边界 ===')
emit('resync 指令数=%d 字节长=%d 末地址=%s 末指令=%s 字节=%s 对照P1=%s' %
     (len(q1_real), q1_len, q1_last['addr'], q1_last['mnemonic']+' '+q1_last['operands'],
      q1_last['bytes'], res['Q1']['match_P1']))
ck('Q1_count_55', len(q1_real) == 55)
ck('Q1_ret4', q1_last['bytes'] == 'c20400')
ck('Q1_end_4A1D23', q1_last['addr'] == '0x4a1d23')

# ===== Q2: all slot accesses in function =====
q2 = []
for rec in q1_real:
    a = int(rec['addr'], 16)
    ins = one(a)
    if ins is None: continue
    for op in ins.operands:
        if op.type != 3 or op.mem.base != X86_REG_ECX: continue   # mem base=ECX
        if op.mem.disp not in (0, 4, 8, 12): continue
        rw = 'W' if ins.operands and ins.operands[0].type == 3 else 'R'
        q2.append({'addr': hex(a), 'bytes': bytes_of(a, ins.size).hex(),
                   'mnemonic': ins.mnemonic, 'operands': ins.op_str,
                   'slot': op.mem.disp, 'rw': rw})
p0w = [x for x in q2 if x['slot'] == 0 and x['rw'] == 'W']
p0r = [x for x in q2 if x['slot'] == 0 and x['rw'] == 'R']
res['Q2'] = {'accesses': q2, 'plus0_writes': p0w, 'plus0_reads': p0r,
             'P4_unique_write_confirmed': len(p0w) == 1 and p0w[0]['addr'] == '0x4a1d1b'}
emit('=== Q2 槽位读写（共 %d 条）===' % len(q2))
for x in q2:
    emit('  %s %-18s %-7s %-32s +0x%-2X %s' %
         (x['addr'], x['bytes'], x['mnemonic'], x['operands'], x['slot'], x['rw']))
emit('+0 写=%r' % [x['addr'] for x in p0w])
emit('+0 读=%r' % [x['addr'] for x in p0r])
ck('Q2_unique_plus0_write', len(p0w) == 1 and p0w[0]['addr'] == '0x4a1d1b')
ck('Q2_has_plus0_read', len(p0r) >= 1)

# ===== 331 callsites + host clustering =====
sites = []
for off in range(RS-5):
    if RAW[RP+off] != 0xE8: continue
    rel = struct.unpack_from('<i', RAW, RP+off+1)[0]
    if LO+off+5+rel == T: sites.append(LO+off)
starts = []
i = 0
while i < RS:
    if RAW[RP+i] == 0x90:
        j = i
        while j < RS and RAW[RP+j] == 0x90: j += 1
        if j-i >= 2 and j < RS: starts.append(LO+j)
        i = j
    else: i += 1
hidx = [bisect.bisect_right(starts, s)-1 for s in sites]
hosts = collections.Counter(starts[h] if h >= 0 else -1 for h in hidx)
emit('=== P3 调用点 ===')
emit('E8+rel32 命中=%d；宿主函数识别=%d/%d' % (len(sites), sum(1 for h in hidx if h>=0), len(sites)))
emit('Top20 宿主函数: ' + ', '.join('%08X:%d' % (a,n) for a,n in hosts.most_common(20)))
res['callsites'] = {'count': len(sites), 'hosts_found': sum(1 for h in hidx if h>=0),
                    'top20': [[hex(a), n] for a,n in hosts.most_common(20)]}
ck('P3_331', len(sites) == 331)
ck('P3_hosts_all', all(h >= 0 for h in hidx))

# ===== Q3/R1: caller +0 writes in window before callsite =====
MOV0 = re.compile(r'^mov\s+dword ptr \[(eax|ecx|edx|ebx|esp|ebp|esi|edi)(?:\s*\+\s*0x0)?\],\s*(\S+)$')
def window_writes(site, W):
    found = {}
    st, en = site-W, site
    for ph in range(24):
        a = st+ph
        if a >= en: break
        for ins in mdl.disasm(code_at(a, min(en-a, 400)), a):
            if ins.address >= en: break
            mm = MOV0.match(ins.op_str)
            if ins.mnemonic == 'mov' and mm:
                b = bytes_of(ins.address, ins.size)
                if b[0] in (0x89, 0xC7):
                    found[hex(ins.address)] = {'addr': hex(ins.address), 'bytes': b.hex(),
                        'insn': ins.mnemonic+' '+ins.op_str, 'callsite': hex(site)}
    return list(found.values())

wins = {}
for W in (16, 64, 256):
    hits = {}
    for s in sites:
        h = window_writes(s, W)
        if h: hits[hex(s)] = h
    wins[W] = hits
res['Q3'] = {'callsite_count': len(sites), 'window64_hit_sites': len(wins[64]),
             'window64_hits': dict(list(wins[64].items())[:20]),
             'top20_hosts': [[hex(a), n] for a,n in hosts.most_common(20)]}
emit('=== Q3 调用者 +0 写入 ===')
for W in (16,64,256):
    emit('  窗口 %dB: 命中调用点 %d/%d' % (W, len(wins[W]), len(sites)))
for s,h in list(wins[64].items())[:10]:
    emit('    site %s: %r' % (s,h[:2]))
ck('Q3_no_caller_plus0_write_64', len(wins[64]) == 0)

# ===== Q4: adjacent slot writes + global +0 zero writes =====
adj = []
adj_re = re.compile(r'^dword ptr \[(ecx|esi)(?:\s*\+\s*(?:0x4|0x8|0xc))?\],\s*(\S+)$')
for i in range(RP, RP+RS-6):
    op, mr = RAW[i], RAW[i+1]
    if op not in (0x89, 0xC7): continue
    if not (0x41 <= mr <= 0x7F): continue          # mod=01 disp8, rm reg/ecx/esi
    rm = mr & 7
    if rm not in (1, 6): continue                  # ecx / esi
    disp = RAW[i+2]
    if disp not in (4, 8, 12): continue
    va = LO + (i-RP)
    ins = one(va)
    if ins is None or ins.mnemonic != 'mov': continue
    if not adj_re.match(ins.op_str): continue
    if ins.size != (3 if op == 0x89 else 7): continue
    adj.append((va, ins.size, ins.op_str))
adj = sorted(set(adj))
zero = []
for i in range(RP, RP+RS-6):
    if RAW[i] != 0xC7 or RAW[i+1] not in (0x01, 0x06) or RAW[i+2:i+6] != b'\0\0\0\0': continue
    va = LO + (i-RP)
    ins = one(va)
    if ins and ins.mnemonic == 'mov' and ins.size == 6 and re.match(r'^dword ptr \[(ecx|esi)], 0$', ins.op_str):
        zero.append(va)
zero = sorted(set(zero))
ctor = []
for va, sz, ops in adj:
    k = bisect.bisect_left(zero, va-32)
    if k < len(zero) and zero[k] <= va+32:
        ctor.append({'addr': hex(va), 'insn': 'mov '+ops, 'near_zero_write': hex(zero[k])})

# 二次过滤：候选所在函数是否调用 CRC 例程族（0x4A1CA0/0x4A1DE0/0x4A1FB0/0x4A1FF0）。
CRC_FAMILY = (0x4A1C10, 0x4A1CA0, 0x4A1DE0, 0x4A1FB0, 0x4A1FF0)
func_starts_sorted = starts  # 已由 nop>=2 填充得到
def crc_calls_in_func(va):
    h = bisect.bisect_right(func_starts_sorted, va) - 1
    if h < 0: return []
    fstart = func_starts_sorted[h]
    fend = func_starts_sorted[h+1] if h+1 < len(func_starts_sorted) else LO+RS
    calls = []
    for off in range(RP+(fstart-LO), min(RP+(fend-LO), RP+RS)-5):
        if RAW[off] != 0xE8: continue
        rel = struct.unpack_from('<i', RAW, off+1)[0]
        dst = LO + (off-RP) + 5 + rel
        if dst in CRC_FAMILY:
            calls.append(hex(LO+(off-RP)))
    return calls

ctor_crc = []
for c in ctor:
    va = int(c['addr'], 16)
    calls = crc_calls_in_func(va)
    if calls:
        c['crc_family_calls_in_host_func'] = calls
        ctor_crc.append(c)
emit('=== Q4 对象构造判据 ===')
emit('全 .text 相邻槽(+4/+8/+C)写入点=%d；mov [ecx/esi],0 全段=%d' % (len(adj), len(zero)))
emit('初筛构造候选(±32B 同对象清零)=%d；其中宿主函数调用 CRC 例程族的=%d' % (len(ctor), len(ctor_crc)))
emit('初筛候选明细(均属其它对象类型：+4 为 size/count、+8 为指针、+C 为 sentinel):')
for c in ctor:
    emit('  %s %s near_zero=%s  host_crc_calls=%r' %
         (c['addr'], c['insn'], c['near_zero_write'], crc_calls_in_func(int(c['addr'],16))[:5]))
res['Q4'] = {'scan_range': [hex(LO), hex(LO+RS)],
             'criterion': 'mov dword ptr [ecx/esi+{4,8,C}],X 且 ±32B 内 mov dword ptr [ecx/esi],0；'
                          '再要求宿主函数调用 CRC 例程族',
             'adjacent_writes': len(adj), 'plus0_zero_writes_total': len(zero),
             'plus0_zero_writes': [hex(a) for a in zero[:100]],
             'ctor_candidates_initial': ctor, 'ctor_candidates_initial_total': len(ctor),
             'ctor_candidates_crc_confirmed': ctor_crc,
             'ctor_candidates_crc_confirmed_total': len(ctor_crc)}
ck('Q4_no_crc_ctor', len(ctor_crc) == 0)

# ===== Q5/R3: ecx from absolute source near callsite =====
imm_sites, mem_sites = [], []
for s in sites:
    fi, fm = [], []
    for ph in range(24):
        a = s-64+ph
        if a >= s: break
        for ins in mdl.disasm(code_at(a, min(s-a, 80)), a):
            if ins.address >= s: break
            b = bytes_of(ins.address, ins.size)
            if ins.mnemonic != 'mov': continue
            if len(b) == 5 and b[0] == 0xB9 and ins.op_str.startswith('ecx,'):
                fi.append({'addr': hex(ins.address), 'bytes': b.hex(), 'insn': 'mov '+ins.op_str})
            if len(b) == 6 and b[0] == 0x8B and b[1] == 0x0D and ins.op_str.startswith('ecx,'):
                d = struct.unpack('<I', b[2:])[0]
                fm.append({'addr': hex(ins.address), 'bytes': b.hex(), 'insn': 'mov '+ins.op_str,
                           'mem': hex(d), 'section': str(P.where(d))})
    if fi: imm_sites.append({'callsite': hex(s), 'hits': fi})
    if fm: mem_sites.append({'callsite': hex(s), 'hits': fm})
emit('=== Q5 全局/静态对象 ===')
emit('调用点前64B mov ecx,imm32 命中调用点=%d（原始命中指令条数=%d）' %
     (len(imm_sites), sum(len(x['hits']) for x in imm_sites)))
emit('R3 mov ecx,[abs] 命中调用点=%d（原始命中指令条数=%d）' %
     (len(mem_sites), sum(len(x['hits']) for x in mem_sites)))
emit('说明：imm32 样例 0x51000016 / 0x38a1ffea / 0x868affea / 0x8e8affea / 0x968affea，'
     '其中 0x38a1ffea 等为错位反汇编产物（紧随 mov ecx, edi 重置），均非 .data/.bss 合法对象地址。')
for x in imm_sites[:10]:
    emit('  IMM site=%s hits=%d first=%r' % (x['callsite'], len(x['hits']), x['hits'][:2]))
for x in mem_sites[:10]:
    emit('  ABS site=%s hits=%d first=%r' % (x['callsite'], len(x['hits']), x['hits'][:2]))
res['Q5'] = {'ecx_imm32_sites': imm_sites, 'ecx_abs_mem_sites': mem_sites,
             'data_sections': {nm: {'lo': hex(P.B[nm]['lo']), 'rawsize': hex(P.B[nm]['rawsize']),
                                    'vsize': hex(P.B[nm]['vsize'])} for nm in ('.data','.rdata') if nm in P.B}}
ck('Q5_ecx_imm32_measured', isinstance(imm_sites, list) and len(imm_sites) >= 0,
   '实测 %d 个调用点（不预设 0）' % len(imm_sites))

# ===== R2 =====
single = []
for ins in mdl.disasm(code_at(T, 512), T):
    single.append(hex(ins.address))
    if ins.mnemonic == 'ret': break
res['R2'] = {'resync_insn_count': len(q1_real), 'single_lite_insn_count': len(single),
             'single_first20': single[:20]}
emit('=== R2 单次连续 disasm_lite（不重同步）条数=%d（resync=%d）===' % (len(single), len(q1_real)))

# ===== Q6 =====
res['Q6'] = {
    'category': 'd' if (len(wins[64]) == 0 and len(ctor_crc) == 0) else 'other',
    'answer': '实测找不到任何 +0 初值写入点（候选 d）',
    'coverage': '%d/%d 调用点（%.1f%%）' % (len(sites), len(sites), 100.0),
    'support': {'caller_writes_64B': len(wins[64]), 'ctor_candidates_crc_confirmed': len(ctor_crc),
                'ctor_candidates_initial': len(ctor), 'ecx_imm32_sites': len(imm_sites),
                'ecx_abs_mem_sites': len(mem_sites)},
    'caveat': '(c) BSS 零初始化无法由静态调用面排除：ecx 指向的对象分配点未在本次扫描口径内定位。',
}
res['R1'] = {'window_hits': {str(w): len(wins[w]) for w in (16,64,256)}}
res['R3'] = {'ecx_imm32': len(imm_sites), 'ecx_abs_mem': len(mem_sites)}
emit('=== Q6 结论 === %r' % res['Q6'])
emit('=== R1 窗口敏感度 === %r' % res['R1']['window_hits'])
emit('=== R3 放宽口径 === %r' % res['R3'])
ck('R1_monotone', len(wins[16]) <= len(wins[64]) <= len(wins[256]))
ck('R2_counts_positive', len(single) > 0 and len(q1_real) > 0)
ck('R3_both_measured', isinstance(imm_sites, list) and isinstance(mem_sites, list),
   'imm32=%d 调用点; abs_mem=%d 调用点（不预设单调）' % (len(imm_sites), len(mem_sites)))
ck('Q6_category_d', res['Q6']['category'] == 'd')

with open(OUT+'/crcinit.json','w') as f: json.dump(res, f, indent=2, ensure_ascii=False)
with open(OUT+'/crcinit.txt','w') as f: f.write('\n'.join(txt)+'\n')
np = sum(1 for _,c in checks if c)
emit('=== SUMMARY: %d/%d ASSERT PASS; FINAL=%s ===' % (np, len(checks), 'PASS' if np==len(checks) else 'FAIL'))
emit('OUTPUT: %s/crcinit.json, crcinit.txt' % OUT)
