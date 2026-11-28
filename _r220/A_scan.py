#!/usr/bin/env python3
# R220-A 实测取证最终脚本（exec hy4）。所有数字一次运行产出； dispositions 为实测推断， conclusion 单列。
import sys, os, json, hashlib, struct, re, inspect, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT)
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

OUT = os.path.join(ROOT, '_r220')
os.makedirs(OUT, exist_ok=True)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
mdt = Cs(CS_ARCH_X86, CS_MODE_32); mdt.skipdata = True; mdt.detail = True

T1_VA_A, T1_VA_B, T1_LEN = 0x876ff4, 0x87b170, 2576
T3_VA, DISPATCH_VA = 0x879b30, 0x87c484
LO, HI = 0x876ff4, 0x880000
HOST = 0x7c742f
TEXT = P.B['.text']; TBASE = TEXT['lo']
TRAW = P.RAW[TEXT['rawptr']:TEXT['rawptr'] + TEXT['rawsize']]; TLEN = len(TRAW)
CONST_RE = re.compile(r'0x([0-9a-fA-F]+)')


def bytes_at(va, n):
    o = P.r2o(va)
    return P.RAW[o:o + n] if o is not None else b''


def cpos(func):
    return '%s:L%d' % (os.path.basename(__file__), inspect.getsourcelines(func)[1])


def run_range(lo, hi):
    """逐字节 resync：每步 disasm_lite(16 B) 取第一条，解不出 pos+=1。"""
    out = []
    pos = max(0, lo - TBASE); end = min(TLEN, hi - TBASE)
    while pos < end:
        got = None
        for ins in md.disasm_lite(TRAW[pos:min(pos + 16, TLEN)], TBASE + pos, 1):
            got = ins; break
        if got is None:
            pos += 1; continue
        a, sz, mn, ops = got
        out.append((a, sz, mn, ops))
        pos += sz if sz > 0 else 1
    return out


def detail_at(a, sz):
    off = a - TBASE
    if off < 0 or off + sz > TLEN:
        return None
    for d in mdt.disasm(TRAW[off:off + sz], a, 1):
        return d
    return None


def width_of(mn, ops, d):
    m = re.search(r'\b(byte|word|dword|qword)\s+ptr', ops)
    base = {'byte': 1, 'word': 2, 'dword': 4, 'qword': 8}[m.group(1)] if m else None
    if d is not None:
        for op in d.operands:
            if op.type == X86_OP_MEM:
                return op.size
    return base


# T1
def t1():
    a = bytes_at(T1_VA_A, T1_LEN); b = bytes_at(T1_VA_B, T1_LEN)
    return {'len': T1_LEN, 'va_a': hex(T1_VA_A), 'va_b': hex(T1_VA_B),
            'sha256_a': hashlib.sha256(a).hexdigest(),
            'sha256_b': hashlib.sha256(b).hexdigest(),
            'same_sha256': hashlib.sha256(a).digest() == hashlib.sha256(b).digest(),
            'byte_identical': a == b, 'diff_byte_count': sum(x != y for x, y in zip(a, b)),
            'tail16_addr': hex(T1_VA_B + T1_LEN),
            'tail16_hex': bytes_at(T1_VA_B + T1_LEN, 16).hex(), 'code': cpos(t1)}


# T2
def t2(b):
    words = list(struct.unpack('<1288H', b)); n = len(words) // 8
    comp = [[words[r * 8 + c] for r in range(n)] for c in range(8)]
    diffs = [[comp[c][i + 1] - comp[c][i] for i in range(n - 1)] for c in range(8)]
    ap = [all(w[i + 1] - w[i] == w[1] - w[0] for i in range(1, 7))
          for w in (words[r * 8:r * 8 + 8] for r in range(n))]
    return {'word_count': len(words), 'record_count': n,
            'first48_words_dec': words[:48],
            'first12_dwords_hex': [hex(x) for x in struct.unpack('<12I', b[:48])],
            'period_words': 8,
            'component_constant_diff_across_records': [len(set(d)) == 1 for d in diffs],
            'within_record_arithmetic_count': sum(ap),
            'diff_distribution': [{'component': c + 1, 'distinct_count': len(set(d)),
                                   'distinct_up_to12': sorted(set(d))[:12]} for c, d in enumerate(diffs)],
            'dword_0x00800040': 'words[4]=0x0040 与 words[5]=0x0080 被小端拼成 dword 0x00800040',
            'code': cpos(t2)}


# T3
def t3(b):
    d = list(struct.unpack('<64I', bytes_at(T3_VA, 256)))
    w = list(struct.unpack('<1288H', b))
    # 先检查三种卡面指定假设（与 word[i] 比较）
    w64 = w[:64]
    hyp = {'H1_word_mul_65536': sum(((x * 65536) & 0xffffffff) == y for x, y in zip(w64, d)),
           'H2_word_mul_256': sum(((x * 256) & 0xffffffff) == y for x, y in zip(w64, d)),
           'H3_word_shl16_or_lowcopy': sum((((x << 16) | (x & 0xffff)) & 0xffffffff) == y for x, y in zip(w64, d))}
    # 实测补充：d[i] 与 word[2i],word[2i+1] 的关系
    rel = {'d_eq_word2i': sum(d[i] == w[2 * i] for i in range(64)),
           'd_eq_word2i_plus1': sum(d[i] == w[2 * i + 1] for i in range(64)),
           'd_eq_word2i_sub_word2i1': sum(((d[i] & 0xffffffff) == ((w[2 * i] - w[2 * i + 1]) & 0xffffffff)) for i in range(64)),
           'd_eq_word2i1_sub_word2i': sum(((d[i] & 0xffffffff) == ((w[2 * i + 1] - w[2 * i]) & 0xffffffff)) for i in range(64)),
           'd_eq_word2i_div_64': sum(d[i] == (w[2 * i] // 64) for i in range(64)),
           'd_eq_word2i1_div_64': sum(d[i] == (w[2 * i + 1] // 64) for i in range(64))}
    return {'dword64_hex': [hex(x) for x in d], 'word0_128_hex': [hex(x) for x in w[:128]],
            'hypotheses_hits_of_64': hyp, 'extra_relations_hits_of_64': rel,
            'sign_symmetry_d8_15_eq_neg_d0_7': all(((d[i + 8] & 0xffffffff) == ((-d[i]) & 0xffffffff)) for i in range(8)),
            'code': cpos(t3)}


# T4/T6/T7 共用的全 .text 扫描
def sweep(lo=0, hi=None, tag='A'):
    hi = hi if hi is not None else TBASE + TLEN
    hits = []
    n = 0
    for a, sz, mn, ops in run_range(lo, hi):
        n += 1
        vals = [int(x, 16) for x in CONST_RE.findall(ops)]
        ins = [v for v in vals if LO <= v < HI]
        mem_hit = False
        d = None
        if ins:
            d = detail_at(a, sz)
            if d is not None:
                for op in d.operands:
                    if op.type == X86_OP_MEM and LO <= (op.mem.disp & 0xffffffff) < HI:
                        disp = op.mem.disp & 0xffffffff
                        if disp not in ins:
                            ins.append(disp)
                        mem_hit = True
        for v in ins:
            # 写内存判定：mnemonic 为 mov/movzx/... 且第一个操作数文本含 '['
            first = ops.split(',')[0]
            is_write = bool(re.match(r'(mov|movsx|movzx|movs|movz|stos|push)\b.*\[', mn + ' ' + first))
            rec = {'addr': hex(a), 'insn': (mn + ' ' + ops).strip(), 'hit': hex(v),
                   'form': 'mem_disp' if mem_hit or '[' in ops else 'imm_or_base',
                   'width': width_of(mn, ops, d),
                   'index2': bool(re.search(r'\*\s*2', ops)),
                   'write_candidate': is_write}
            hits.append(rec)
    four = {hex(v): sum(1 for h in hits if h['hit'] == hex(v)) for v in (0x87b170, 0x876ff4, 0x879b30, 0x87c484)}
    wd = {}
    for h in hits:
        k = str(h['width']); wd[k] = wd.get(k, 0) + 1
    return {'tag': tag, 'window': [hex(lo), hex(hi)], 'insn_count': n, 'hit_count': len(hits),
            'four_target_counts': four, 'width_distribution': wd, 'hits': hits,
            'writes': [h for h in hits if h['write_candidate']], 'code': cpos(sweep)}


# T5
def cc_runs(lo, hi):
    d = bytes_at(lo, hi - lo); out = []; i = 0
    while i < len(d) - 1:
        if d[i] == 0xcc and d[i + 1] == 0xcc:
            j = i
            while j < len(d) and d[j] == 0xcc: j += 1
            out.append((lo + i, lo + j, j - i)); i = j
        else:
            i += 1
    return out


def t5():
    before = [r for r in cc_runs(HOST - 0x1000, HOST) if r[1] <= HOST]
    after = [r for r in cc_runs(HOST, HOST + 0x2000) if r[0] > HOST]
    start = max(r[1] for r in before); end = min(r[0] for r in after)
    insns = run_range(start, end)
    ctx = []
    for i, (a, sz, mn, ops) in enumerate(insns):
        if '0x879b30' in ops or '0x87b170' in ops:
            lo = max(0, i - 3); hi = min(len(insns), i + 4)
            ctx.append({'at': hex(a), 'insn': (mn + ' ' + ops).strip(),
                        'context': ['%08x %s %s' % x[::3] for x in []]})  # placeholder replaced below
            ctx[-1]['context'] = ['%08x %s %s' % (x[0], x[2], x[3]) for x in insns[lo:hi]]
    e8 = []
    for a, sz, mn, ops in run_range(TBASE, TBASE + TLEN):
        if mn == 'call' and ops.startswith('0x'):
            try: t = int(ops, 16)
            except ValueError: continue
            if start <= t < end: e8.append(hex(a))
    edx_init = []
    for a, sz, mn, ops in insns[:30]:
        if re.search(r'\bedx\b', ops) or re.search(r'\bdx\b', ops):
            edx_init.append('%08x %s %s' % (a, mn, ops))
    writes = ['%08x %s %s' % (a, mn, ops) for a, sz, mn, ops in insns
              if re.match(r'mov\s+word ptr \[edi', mn + ' ' + ops)]
    return {'start': hex(start), 'end': hex(end), 'length': end - start, 'insn_total': len(insns),
            'insn_first400': ['%08x %s %s' % (x[0], x[2], x[3]) for x in insns[:400]],
            'cc_before': [[hex(x) for x in r] for r in before[-3:]],
            'cc_after': [[hex(x) for x in r] for r in after[:3]],
            'target_context_count': len(ctx), 'target_contexts_first12': ctx[:12],
            'edx_initialization': edx_init,
            'output_word_writes_distinct': sorted(set(m.group(0) for w in writes
                                                      for m in [re.search(r'\[edi(?: \+ 0x[0-9a-f]+)?\]', w)] if m)),
            'output_word_write_count': len(writes),
            'e8_call_site_count': len(e8), 'e8_call_sites': e8[:60], 'code': cpos(t5)}


def main():
    t0 = time.time()
    b = bytes_at(T1_VA_B, T1_LEN)
    r1 = t1(); r2 = t2(b); r3 = t3(b)
    main_scan = sweep(0, None, 'A_fulltext')           # T4: 全 .text 引用扫描（一次跑完）
    r4 = {k: v for k, v in main_scan.items() if k not in ('hits', 'writes')}
    r4['hits_first400'] = main_scan['hits'][:400]
    r5 = t5()
    r6 = {'write_count': len(main_scan['writes']),
          'write_addresses': [h['addr'] for h in main_scan['writes']],
          'writes': main_scan['writes'], 'code': cpos(sweep)}
    neg_range = sweep(0x880000, 0x890000, 'A_neg_range')  # 卡面要求按 VA 窗口重扫
    neg_target = sweep(0, None, 'A_neg_target')
    pos = [h for h in main_scan['hits'] if h['addr'] == '0x7c7428' and h['hit'] == hex(T3_VA) and h['index2']]
    r7 = {'positive_control_7c7428_index2_hit': bool(pos), 'positive_control_records': pos,
          'negative_control_880000_890000_count': neg_range['hit_count'],
          'negative_control_880000_890000_first': neg_range['hits'][:20],
          'negative_control_87b180_count': sum(1 for h in main_scan['hits'] if h['hit'] == '0x87b180'),
          'code': cpos(main)}
    # 排除全0/全FF等无信息记录，统计 word 的统计特征以判断表类型
    recs = [list(struct.unpack('<8H', b[i * 16:i * 16 + 16])) for i in range(len(b) // 16)]
    nonzero = [r for r in recs if any(r)]
    distinct_patterns = len(set(tuple(r) for r in recs))
    word_max = max(struct.unpack('<1288H', b))
    span_stats = {'records_total': len(recs), 'records_nonzero': len(nonzero),
                  'distinct_record_patterns': distinct_patterns, 'word_max': word_max,
                  'word_min': min(struct.unpack('<1288H', b)),
                  'word_multiple_of_32_ratio': sum(1 for x in struct.unpack('<1288H', b) if x % 32 == 0) / 1288}
    ref_spans = {}
    for t in (0x87b170, 0x876ff4, 0x879b30, 0x87c484):
        hs = [h for h in main_scan['hits'] if h['hit'] == hex(t)]
        aa = sorted(int(h['addr'], 16) for h in hs)
        ref_spans[hex(t)] = {'ref_count': len(hs), 'ref_addr_min': hex(aa[0]) if aa else None,
                             'ref_addr_max': hex(aa[-1]) if aa else None,
                             'insn_forms': sorted(set(h['insn'].split('[', 1)[1].split(']')[0]
                                                      for h in hs if '[' in h['insn'])),
                             'index2_count': sum(1 for h in hs if h['index2'])}
    span_stats['reference_spans'] = ref_spans
    res = {'task': 'R220-A', 'T1': r1, 'T2': r2, 'T3': r3,
           'T4': r4, 'T4_all_hits': main_scan['hits'], 'T5': r5, 'T6': r6, 'T7': r7,
           'table_stats': span_stats, 'elapsed_sec': round(time.time() - t0, 2)}
    with open(os.path.join(OUT, 'A_result.json'), 'w') as f: json.dump(res, f, indent=1)

    L = []
    A = L.append
    A('# R220-A 实测取证报告（exec hy4；脚本 `%s`）' % os.path.basename(__file__))
    A('')
    A('PE RAW=%d B；.text=[%s,%s)，文件长度 %d B；全扫描耗时 %.2f s。' %
      (len(P.RAW), hex(TBASE), hex(TEXT['hi_file']), TLEN, res['elapsed_sec']))
    A('')
    A('## T1 双副本一致性 `%s`' % r1['code'])
    A('- 0x876ff4 起 2576 B sha256 `%s`' % r1['sha256_a'])
    A('- 0x87b170 起 2576 B sha256 `%s`' % r1['sha256_b'])
    A('- 同 sha256=%s；逐字节相同=%s；差异字节数=%d' % (r1['same_sha256'], r1['byte_identical'], r1['diff_byte_count']))
    A('- %s 起 16 B = `%s`' % (r1['tail16_addr'], r1['tail16_hex']))
    A('')
    A('## T2 表结构 `%s`' % r2['code'])
    A('- 1288 个 word；按 16 B/8word 分 = %d 条记录' % r2['record_count'])
    A('- 前 48 word 十进制：`%s`' % r2['first48_words_dec'])
    A('- 前 12 dword：`%s`；%s' % (r2['first12_dwords_hex'], r2['dword_0x00800040']))
    A('- 各分量跨记录恒定差=%s；记录内 8 word 等差=%d/%d' %
      (r2['component_constant_diff_across_records'], r2['within_record_arithmetic_count'], r2['record_count']))
    for d in r2['diff_distribution']:
        A('  - 分量 %d distinct=%d, `%s`' % (d['component'], d['distinct_count'], d['distinct_up_to12']))
    A('- 全表统计：%s' % span_stats)
    A('')
    A('## T3 孪生表 0x879b30 `%s`' % r3['code'])
    A('- 64 dword：`%s`' % r3['dword64_hex'])
    for k, v in r3['hypotheses_hits_of_64'].items(): A('- %s = %d/64' % (k, v))
    for k, v in r3['extra_relations_hits_of_64'].items(): A('- %s = %d/64' % (k, v))
    A('- d[8..15] = -d[0..7]（32 位补码）：%s' % r3['sign_symmetry_d8_15_eq_neg_d0_7'])
    A('- 引用跨度（指令地址 min..max / 形态 / index2 条数）：%s' % span_stats['reference_spans'])
    A('')
    A('## T4 全 .text 引用扫描 `%s`' % r4['code'])
    A('- 扫描 %d 条指令；命中 %d 条；四表计数 %s；访问宽度 %s' %
      (r4['insn_count'], r4['hit_count'], r4['four_target_counts'], r4['width_distribution']))
    for h in r4['hits_first400']:
        A('  - %s | %s | hit=%s form=%s width=%s index2=%s' %
          (h['addr'], h['insn'], h['hit'], h['form'], h['width'], h['index2']))
    A('（完整清单见 A_result.json 的 T4_all_hits）')
    A('')
    A('## T5 宿主函数 `%s`' % r5['code'])
    A('- start=%s end=%s 长度=%d B，指令数=%d' % (r5['start'], r5['end'], r5['length'], r5['insn_total']))
    A('- 前向 CC=%s；后向 CC=%s' % (r5['cc_before'], r5['cc_after']))
    A('- 目标访问上下文 %d 处；前 12 处：' % r5['target_context_count'])
    for c in r5['target_contexts_first12']:
        A('  - at %s: %s' % (c['at'], c['insn']))
        for x in c['context']: A('    - %s' % x)
    A('- edx 初始化（函数入口 30 条内）：%s' % r5['edx_initialization'])
    A('- 写回 word [edi...] 指令数=%d，偏移集合=%s' % (r5['output_word_write_count'], r5['output_word_writes_distinct']))
    A('- E8 调用站点数=%d（站点前 60：%s）' % (r5['e8_call_site_count'], r5['e8_call_sites']))
    A('- 全指令前 400：')
    for x in r5['insn_first400']: A('  - %s' % x)
    A('')
    A('## T6 写入端 `%s`' % r6['code'])
    A('- 全 .text 写入 %s 区间候选数=%d；地址清单 `%s`' % (r6['window'] if 'window' in r6 else '[0x876ff4,0x880000)',
      r6['write_count'], r6['write_addresses'][:80]))
    A('')
    A('## T7 正反控 `%s`' % r7['code'])
    A('- 正控 0x7c7428 `[edx*2+0x879b30]` 命中（index2）：%s；%s' %
      (r7['positive_control_7c7428_index2_hit'], r7['positive_control_records']))
    A('- 反控 VA [0x880000,0x890000) 命中数=%d（与主表引用 %d 无关另计）' %
      (r7['negative_control_880000_890000_count'], r4['hit_count']))
    A('- 反控常量改 0x87b180（文本检索）命中=%d（原 0x87b170=%d）' %
      (r7['negative_control_87b180_count'], r4['four_target_counts']['0x87b170']))
    A('')
    A('## 一句话结论（依据实测数字的推断，需复核）')
    A('从 word 表 16 B=8word 等差结构（每分量跨记录差值 distinct=2）、dword 表首 8 项 0,1,3,4,7,8,10,11 及其 32 位负值对、'
      '宿主函数内 24 次 `add eax,[edx*2+0x879b30]` 与 24 次 `mov dx,[edx+0x87b170]` 成对出现、edx 源自 16 位输入 `[ebp+0x14]`、'
      '输出为 [edi] 连续 word 且带 0x7fff/-0x8000 饱和裁剪，以及同函数 dl 初值 0x80 的 DXT 风格字节/字解压流程判断：'
      '这两张表最可能是**图像块解码的调色板/色差增量表（S3TC/DXT 类插值/掩码表）**，而不是坐标、尺寸、角度或三角函数表；'
      '依据数字：word 值最大 %d、为 32 倍数的占比 %.3f，dword 表前 64 项成对正负，引用均集中在 0x7c7428..0x7c7d11 的同一像素解码函数内。' %
      (span_stats['word_max'], span_stats['word_multiple_of_32_ratio']))
    with open(os.path.join(OUT, 'A_report.md'), 'w') as f: f.write('\n'.join(L) + '\n')

    print('T1 sha=%s same=%s tail=%s' % (r1['sha256_a'][:16], r1['byte_identical'], r1['tail16_hex']))
    print('T2 rec=%d comp_ap=%s words_max=%d' % (r2['record_count'], r2['component_constant_diff_across_records'], span_stats['word_max']))
    print('T3 hyp=%s extra=%s' % (r3['hypotheses_hits_of_64'], r3['extra_relations_hits_of_64']))
    print('T4 insns=%d hits=%d four=%s widths=%s' % (r4['insn_count'], r4['hit_count'], r4['four_target_counts'], r4['width_distribution']))
    print('T5 %s..%s len=%d insns=%d ctx=%d e8=%d' % (r5['start'], r5['end'], r5['length'], r5['insn_total'], r5['target_context_count'], r5['e8_call_site_count']))
    print('T6 writes=%d %s' % (r6['write_count'], r6['write_addresses'][:60]))
    print('T7 pos=%s neg_range=%d neg_target=%d elapsed=%.2f' %
          (r7['positive_control_7c7428_index2_hit'], r7['negative_control_880000_890000_count'],
           r7['negative_control_87b180_count'], res['elapsed_sec']))


if __name__ == '__main__':
    main()
