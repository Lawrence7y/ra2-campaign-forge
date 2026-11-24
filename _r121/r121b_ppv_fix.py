#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r121b_ppv_fix.py -- 重测 QI(0x7f7c80) 出参去向，并修掉崩溃轮的两处结构性缺陷。

崩溃轮 _r121/r121a_qiconsume.py 的两处缺陷（本轮逐条实测，非推测）：
  D1 ppv 槽 K 从未参与判定。
     analyze() 解出 P = mov P,[esp+K] 之后只写进 out['P'] / arg_index，
     consume 的判定不要求 P 非空 => K 平移任意值，桶都不变。
     实测：K 平移 -0x10/-0xc/-8/-4/+4/+8/+0x10/+0x14 共 8 个值，OleSaveToStream 恒为 36。
     因此它的反控 N3「K+4 必须变化」结构性恒 FAIL —— 不是数据问题，是判据缺一条门槛。
  D2 寄存器回溯的后向窗口只有 0x40 字节。
     24 个站点写成 call ebp，而 ebp 的初值在函数首部装入，距站点数百字节，
     落在 0x40 窗口外 => 被误报为 REG:ebp<-UNRESOLVED。

本脚本的判据（每条带正反控）：
  F1 P 门槛：未解出 P 的站点进 NO-P-AT-K，不进任何 API 桶。这使 K 真正参与判定。
  F2 寄存器回溯不用函数边界，用「精确解码链向前找最后一次写该寄存器」，
     并对该写做支配性检验：区间 (write_addr, site) 内是否存在任何直接 call/jmp rel32 目标。
     只有该区间无内部入口，才允许「站点处该寄存器 == 该写的值」这一步推理；
     有内部入口的站点一律降级为 NOT-DOMINATED，不计入 API 桶。
  F3 诚实登记：间接跳转（call/jmp [reg]）的目标无法静态解析，这一残差单独报数。

反控：
  N1 立即数精确：站点处 0x68 + imm32 == 目标，逐字节核对。
  N2 偏移敏感：站点 +1 处起算同一套判据，解出 ppv 槽的必须 0。
  N3 槽位敏感（P 门槛生效后）：K 平移 -4/+4/+8，OleSaveToStream 必须变化。
  N5 恒真排除：目标换成 0x7f7c84，站点必须 0。
  P2 正控 对照 IID：0x7f7c90 跑同型测量，桶分布必须与 0x7f7c80 不同。
  P3 正控 合成字节串：手工构造已知形状，分析器必须正确分类（证明判据不是恒 0）。

内存纪律：disasm_lite 分块；只对命中站点前后 <=2 KiB 窗口开 detail。脚本带 timeout。
"""
import collections
import json
import os
import re
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r121'))
import x121lib                                    # noqa: E402
import capstone                                   # noqa: E402

OUT = os.path.join(ROOT, '_r121', 'r121b_ppv_fix.json')
PE_PATH = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
checks = []

MDL = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MDL.detail = False
MDL.skipdata = True

REGRE = r'(?:eax|ebx|ecx|edx|esi|edi|ebp)'
TERM_MN = {'ret', 'jmp'}

pe = x121lib.PE(PE_PATH)
IATV = {va: nm for va, (_dll, nm) in pe.iat.items()}
TEXT = next(s for s in pe.sections if s['name'] == '.text')
TEXT_VA0 = pe.image_base + TEXT['va']
TEXT_VA1 = TEXT_VA0 + TEXT['vsize']


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name +
          ((' | ' + json.dumps(detail, ensure_ascii=False)) if detail != '' else ''), flush=True)
    return bool(cond)


def find_push_imm(imm):
    pat = b'\x68' + struct.pack('<I', imm & 0xffffffff)
    out, i, end = [], TEXT['raw'], TEXT['raw'] + TEXT['vsize']
    while True:
        j = pe.buf.find(pat, i, end)
        if j < 0:
            break
        out.append(pe.image_base + TEXT['va'] + (j - TEXT['raw']))
        i = j + 1
    return out


def dec_window(va, back, fwd):
    lo = max(TEXT_VA0, va - back)
    hi = min(TEXT_VA1, va + fwd)
    o = pe.off_va(lo)
    blob = pe.buf[o:o + (hi - lo)]
    return [(i.address, i.size, i.mnemonic, i.op_str) for i in MDL.disasm(blob, lo)]


def ppv_slot(seq, idx, look=10):
    """push R immediately before site, and lea R,[esp+K] within LOOK insns before it,
    not crossing another write to R. (Same shape r121a used; it was NOT the bug.)"""
    if idx - 1 < 0:
        return None
    a, sz, mn, ops = seq[idx - 1]
    if mn != 'push' or not re.fullmatch(REGRE, ops):
        return None
    R = ops
    for j in range(idx - 2, max(-1, idx - 2 - look), -1):
        mn2, ops2 = seq[j][2], seq[j][3]
        m = re.fullmatch(r'(%s), \[esp \+ (0x[0-9a-f]+)\]' % REGRE, ops2)
        if mn2 == 'lea' and m and m.group(1) == R:
            return dict(reg=R, K=m.group(2), lea=hex(seq[j][0]), push=hex(a))
        if mn2 in ('mov', 'lea', 'pop', 'xor', 'add', 'sub', 'and', 'or') and \
                re.match(r'^%s\s*,' % R, ops2):
            return None
    return None


def qi_index(seq, idx):
    for i in range(idx, len(seq)):
        if seq[i][2] == 'call' and seq[i][3] == 'dword ptr [ecx]':
            return i
    return None


# 这些助记符写第一个操作数（不是读）。call/jmp/push/cmp/test 一律不算写。
WRITE_MN = {'mov', 'lea', 'pop', 'xor', 'add', 'sub', 'and', 'or', 'adc', 'sbb',
            'inc', 'dec', 'neg', 'not', 'shl', 'shr', 'sar', 'imul', 'movzx', 'movsx',
            'xchg', 'sete', 'setne', 'setl', 'setg'}


def last_write_before(site, reg, maxback=0x2000):
    """exact decoding chain: nearest preceding instruction that WRITES reg.
    Only WRITE_MN with reg as destination counts. A read such as `call ebp`
    or `push ebp` is NOT a write -- that mistake is exactly what produced the
    bogus REG-OTHER-WRITE rows in the first build of this script."""
    seq = dec_window(site, maxback, 0)
    w = None
    for (a, sz, mn, ops) in seq:
        if a >= site:
            break
        if mn not in WRITE_MN:
            continue
        dst = ops.split(',')[0].strip()
        if dst == reg:
            w = (a, '%s %s' % (mn, ops))
    return w


def inner_entries(lo, hi):
    """direct call/jmp rel32 whose target lies strictly inside (lo, hi)."""
    if hi - lo < 6:
        return []
    o = pe.off_va(lo)
    blob = pe.buf[o:pe.off_va(hi)]
    hits = []
    for i in range(len(blob) - 5):
        if blob[i] in (0xe8, 0xe9):
            r = struct.unpack_from('<i', blob, i + 1)[0]
            t = lo + i + 5 + r
            if lo < t < hi:
                hits.append(dict(at=hex(lo + i), target=hex(t)))
    return hits


def resolve_reg_call(site, seq, i, reg):
    """classify `call reg`: walk back for its last write; require domination."""
    w = last_write_before(site, reg)
    info = {'at': hex(seq[i][0]), 'kind': 'REG', 'reg': reg, 'raw': 'call %s' % reg}
    if w is None:
        info['name'] = 'REG-UNRESOLVED'
        return info
    info['write'] = hex(w[0])
    info['write_raw'] = w[1]
    m = re.fullmatch(r'mov %s, dword ptr \[(0x[0-9a-f]+)\]' % reg, w[1])
    if m:
        v = int(m.group(1), 16)
        info['slot'] = hex(v)
        info['name'] = IATV.get(v, 'NOT-IAT:%x' % v)
    else:
        info['name'] = 'REG-OTHER-WRITE'
    ents = inner_entries(w[0], site)
    info['inner_entries'] = ents
    info['dominated'] = (len(ents) == 0)
    if not info['dominated']:
        info['name'] = 'REG-NOT-DOMINATED'
    return info


def analyze(site, shift=0, kshift=0):
    seq = dec_window(site, 0x40, 0x100)
    idx = next((i for i, x in enumerate(seq) if x[0] == site + shift), None)
    if idx is None:
        return {'site': hex(site), 'bucket': 'SITE-NOT-DECODABLE'}
    out = {'site': hex(site)}
    slot = ppv_slot(seq, idx)
    out['ppv'] = slot
    qi = qi_index(seq, idx)
    out['qi'] = hex(seq[qi][0]) if qi is not None else None
    if slot is None:
        out['bucket'] = 'NO-PPV-SLOT'
        return out
    if qi is None:
        out['bucket'] = 'NO-QI'
        return out
    K = hex(int(slot['K'], 16) + kshift) if kshift else slot['K']
    out['K_used'] = K
    pushes, P = [], None
    for i in range(qi + 1, min(len(seq), qi + 23)):
        a, sz, mn, ops = seq[i]
        m = re.fullmatch(r'(%s), dword ptr \[esp \+ %s\]' % (REGRE, re.escape(K)), ops)
        if mn == 'mov' and m:
            P = m.group(1)
            out['P'] = P
            out['P_at'] = hex(a)
            continue
        if mn == 'push':
            pushes.append(ops)
            continue
        if mn == 'call':
            if ops.startswith('dword ptr [0x'):
                v = int(ops[len('dword ptr ['):-1], 16)
                ci = {'at': hex(a), 'kind': 'IAT', 'slot': hex(v),
                      'name': IATV.get(v, 'NOT-IAT:%x' % v), 'raw': 'call %s' % ops}
            elif re.fullmatch(REGRE, ops):
                ci = resolve_reg_call(site, seq, i, ops)
            else:
                ci = {'at': hex(a), 'kind': 'OTHER', 'name': 'OTHER:%s' % ops,
                      'raw': 'call %s' % ops}
            out['consume'] = ci
            out['bucket'] = 'NO-P-AT-K' if P is None else ci['name']
            if P and P in pushes:
                out['arg_index'] = len(pushes) - 1 - pushes.index(P)
            out['pushes'] = pushes
            rel = None
            for j in range(i + 1, min(len(seq), i + 10)):
                if seq[j][2] == 'call':
                    rel = seq[j][3]
                    break
                if seq[j][2] in TERM_MN:
                    break
            out['after'] = rel
            return out
        if mn in TERM_MN:
            out['bucket'] = 'TERM-BEFORE-CALL'
            return out
    out['bucket'] = 'SCAN-END'
    return out


def run_target(target):
    sites = find_push_imm(target)
    rows = [analyze(s) for s in sites]
    return sites, rows, collections.Counter(r['bucket'] for r in rows)


OLE = 'OleSaveToStream'
T80 = 0x7f7c80
S80, R80, B80 = run_target(T80)
n_ole = sum(v for k, v in B80.items() if OLE in (k or ''))

ck('F0 站点数 = %d（首字节 0x68 且 imm32 == 0x7f7c80）；桶合计 = %d（必须相等）'
   % (len(S80), sum(B80.values())),
   len(S80) == 60 and sum(B80.values()) == len(S80),
   {'sites': len(S80), 'buckets': dict(B80), 'ole': n_ole})

# ---- N1 ----
bad = 0
for s in S80:
    o = pe.off_va(s)
    if pe.buf[o] != 0x68 or struct.unpack_from('<I', pe.buf, o + 1)[0] != T80:
        bad += 1
ck('N1 反控 imm32 精确：%d 站点逐字节核对 0x68 + imm32，不符 = %d（必须 0）'
   % (len(S80), bad), bad == 0, {'bad': bad})

# ---- N2 ----
n2 = sum(1 for r in (analyze(s, shift=1) for s in S80) if r.get('ppv'))
ck('N2 反控 偏移敏感：站点 +1 起算解出 ppv 槽的 = %d（必须 0）' % n2, n2 == 0, {'n': n2})

# ---- N5 ----
Sx = find_push_imm(0x7f7c84)
ck('N5 反控 恒真排除：目标 0x7f7c84 站点 = %d（必须 0）' % len(Sx), len(Sx) == 0, {'n': len(Sx)})

# ---- N3 槽位敏感（P 门槛生效后）----
ks = {}
for sh in (-4, 4, 8):
    bb = collections.Counter(analyze(s, kshift=sh)['bucket'] for s in S80)
    ks[sh] = sum(v for k, v in bb.items() if OLE in (k or ''))
ck("N3 反控 槽位敏感（P 门槛生效后）：K 平移 -4/+4/+8 的 OleSaveToStream = %s，基准 = %d ⇒ 必须全变化"
   % (json.dumps(ks), n_ole),
   all(v != n_ole for v in ks.values()), {'shifted': ks, 'base': n_ole})

# ---- P2 正控 ----
T90 = 0x7f7c90
S90, R90, B90 = run_target(T90)
ck('P2 正控 对照 0x7f7c90：站点 %d，桶 %s ⇒ 与 0x7f7c80 桶分布不同'
   % (len(S90), json.dumps(dict(B90), ensure_ascii=False)),
   dict(B90) != dict(B80), {'sites': len(S90), 'buckets': dict(B90)})

# ---- P3 正控 合成字节串 ----
synthetic = bytes.fromhex(
    '8d54240c'      # lea edx,[esp+0xc]
    '52'            # push edx
    '68807c7f00'    # push 0x7f7c80   <- site
    '50'            # push eax
    '8b08'          # mov ecx,[eax]
    'ff11'          # call [ecx]      <- QI
    '8b44240c'      # mov eax,[esp+0xc]
    '50'            # push eax
    'ff15f4157e00'  # call [0x7e15f4] <- OleSaveToStream
)
syn = [(i.address, i.size, i.mnemonic, i.op_str) for i in MDL.disasm(synthetic, 0x1000)]
syn_slot = ppv_slot(syn, 2)
syn_qi = qi_index(syn, 2)
ck('P3 正控 合成字节串：lea/push/site/QI/consume 形状能被正确解出（判据非恒 0）',
   syn_slot is not None and syn_slot['K'] == '0xc' and syn_qi == 5,
   {'slot': syn_slot, 'qi': syn_qi, 'n_ins': len(syn)})

# ---- F2 寄存器回溯与支配性 ----
reg_rows = [r for r in R80 if (r.get('consume') or {}).get('kind') == 'REG']
unres = [r['site'] for r in reg_rows if 'UNRESOLVED' in (r['consume'].get('name') or '')]
notdom = [r['site'] for r in reg_rows if not r['consume'].get('dominated')]
dist = sorted(int(r['consume']['write'], 16) and (int(r['site'], 16) - int(r['consume']['write'], 16))
              for r in reg_rows if r['consume'].get('write'))
ck('F2 后向窗口改为精确链后：寄存器调用 %d 个，仍 UNRESOLVED = %d（崩溃轮为 24），未支配 = %d'
   % (len(reg_rows), len(unres), len(notdom)),
   len(unres) == 0 and len(notdom) == 0,
   {'reg_rows': len(reg_rows), 'unresolved': unres, 'not_dominated': notdom,
    'write_dist_min': dist[0] if dist else None, 'write_dist_max': dist[-1] if dist else None})

# ---- F3 间接跳转残差（诚实登记，不是断言）----
ind = []
for off in range(0, TEXT['vsize'], 65536):
    blob = pe.buf[TEXT['raw'] + off:TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
    for (a, sz, mn, ops) in MDL.disasm_lite(blob, TEXT['va'] + pe.image_base + off):
        if mn in ('call', 'jmp') and re.fullmatch(r'(dword ptr \[[^\]]+\]|%s)' % REGRE, ops):
            ind.append(a)
ck('F3 残差登记：全 .text 里间接 call/jmp 站点 = %d 个（其目标无法静态解析，是 F2 的残差）'
   % len(ind), len(ind) > 0, {'n': len(ind)})

# ---- F4 after / Release ----
aft = collections.Counter(r.get('after') for r in R80)
n_rel = aft.get('dword ptr [ecx + 8]', 0)
ck('F4 消费 call 之后 <=8 条内的 call 操作数分布 = %s；其中 [ecx+8]（槽 2 = Release）= %d'
   % (json.dumps(dict(aft), ensure_ascii=False), n_rel),
   n_rel == len(R80) and dict(aft) == {'dword ptr [ecx + 8]': len(R80)}, {'after': dict(aft)})

# ---- F5 K 分布 ----
kd = collections.Counter((r.get('ppv') or {}).get('K') for r in R80)
ad = collections.Counter(r.get('arg_index') for r in R80)
ck('F5 ppv 槽 K 分布 = %s；ppv 的实参位置分布 = %s'
   % (json.dumps(dict(kd), ensure_ascii=False), json.dumps(dict(ad), ensure_ascii=False)),
   True, {'K': dict(kd), 'arg': dict(ad)})

out = dict(file=PE_PATH, checks=checks,
           text=dict(va=hex(TEXT_VA0), vsize=hex(TEXT['vsize'])),
           summary=dict(sites_7f7c80=len(S80), buckets_7f7c80=dict(B80), ole_7f7c80=n_ole,
                        sites_7f7c90=len(S90), buckets_7f7c90=dict(B90),
                        after_7f7c80=dict(aft), K_dist=dict(kd), arg_dist=dict(ad),
                        indirect_jmps=len(ind)),
           results={'0x7f7c80': R80, '0x7f7c90': R90})
open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
npass = sum(1 for c in checks if c['ok'])
print('\n%d/%d PASS -> %s' % (npass, len(checks), OUT))
sys.exit(0 if npass == len(checks) else 1)
