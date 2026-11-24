# -*- coding: utf-8 -*-
r"""
R16-AUDIT-PIVOT32 · 可复跑审计脚本（只读）

审计对象（只读）：
  R16_FIX_PIVOT32\delta.tsv       32 行改后文本
  R16_FIX_PIVOT32\defects.tsv     执行器自建缺陷表（10 行）
  R16_FIX_PIVOT32\REPORT.md       执行器自述
依据（只读）：
  COVERAGE\coverage.tsv           盘上真值基准（sha256 用作“未被写”的对照）
  R16_PROBE_F1_PIVOT\pivot32.tsv  探针（clsid / clsid_status / s126_cited）
  NAMED_PUSH_AUDIT4\verdict.tsv   审计原文（逐行 reason 含正确 GUID + 缺陷标注）
  NAMED_PUSH_AUDIT4\VERDICT.md    审计原文（逐行段 GUID 行 + §5 汇总表 + 必改字结论）
  _cards\R16-AUDIT-PIVOT32.md     任务卡（追加句原文）

范围：§A 10 行全文 + §B 8 行抽样 = 18 行。
  其余 14 行只做 §C/§D 的机器核（计数用），不计入 18 行的逐项结论。

用法：python verify.py
产物：check18.tsv（本目录）
"""
import sys, os, io, hashlib, re, struct

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
COV = os.path.join(ROOT, r'COVERAGE\coverage.tsv')
DEL = os.path.join(ROOT, r'R16_FIX_PIVOT32\delta.tsv')
DEF = os.path.join(ROOT, r'R16_FIX_PIVOT32\defects.tsv')
REP = os.path.join(ROOT, r'R16_FIX_PIVOT32\REPORT.md')
PIV = os.path.join(ROOT, r'R16_PROBE_F1_PIVOT\pivot32.tsv')
AVT = os.path.join(ROOT, r'NAMED_PUSH_AUDIT4\verdict.tsv')
AVM = os.path.join(ROOT, r'NAMED_PUSH_AUDIT4\VERDICT.md')
CARD = os.path.join(ROOT, r'_cards\R16-AUDIT-PIVOT32.md')
OUT = os.path.join(ROOT, r'R16_AUDIT_PIVOT32\check18.tsv')

# 定向字节复核用的原始映像（只读；仅用于印证 audit 断言的 GUID 指针，不做重扫）
EXE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\pristine_gamemd.exe'

fails = []       # (section, entry, item, detail)
obs = []         # 观察项（不判 FAIL）


def fail(sec, entry, item, detail=''):
    fails.append((sec, entry, item, detail))


def observe(item, detail=''):
    obs.append((item, detail))


def rd(p):
    return open(p, 'rb').read()


def dec(b):
    return b.decode('utf-8', 'strict')


def rows_of(p):
    raw = rd(p)
    lines = raw.split(b'\n')
    if lines and lines[-1] == b'':
        lines = lines[:-1]
    return [(i, ln, ln.split(b'\t')) for i, ln in enumerate(lines)]


# ------------------------------------------------------------------ 载入
cov_rows = rows_of(COV)
cov_hdr = cov_rows[0][1]
cov = {}
cov_dupe = {}
for idx, raw, cols in cov_rows:
    if idx == 0 or len(cols) != 8:
        continue
    e = dec(cols[0])
    if e in cov:
        cov_dupe.setdefault(e, 1)
        cov_dupe[e] += 1
    else:
        cov[e] = (idx, raw, cols)

delta = [(i, r, c) for i, r, c in rows_of(DEL) if i > 0]
dby = {dec(c[0]): (i, r, c) for i, r, c in delta}
del_hdr = rows_of(DEL)[0][1]

piv_rows = rows_of(PIV)
piv_hdr = [dec(x) for x in piv_rows[0][2]]
pivot = {}
for i, r, c in piv_rows:
    if i == 0:
        continue
    d = dict(zip(piv_hdr, [dec(x) for x in c]))
    pivot[d['entry']] = d

def_rows = rows_of(DEF)
def_hdr = [dec(x) for x in def_rows[0][2]]
defects = {}
for i, r, c in def_rows:
    if i == 0:
        continue
    d = dict(zip(def_hdr, [dec(x) for x in c]))
    d['_line'] = i + 1
    defects[d['entry']] = d

avt_rows = rows_of(AVT)
avt_hdr = [dec(x) for x in avt_rows[0][2]]
audit_tsv = {}
for i, r, c in avt_rows:
    if i == 0:
        continue
    d = dict(zip(avt_hdr, [dec(x) for x in c]))
    d['_line'] = i + 1
    audit_tsv[d['entry']] = d

audit_md = dec(rd(AVM)).split('\n')
card = dec(rd(CARD)).split('\n')

# 追加句：从卡面原文取（避免抄错）
APPEND = None
for ln in card:
    if '追加句统一为' in ln:
        a, b = ln.find('`'), ln.rfind('`')
        if 0 <= a < b:
            APPEND = ln[a + 1:b]
            break
assert APPEND, '无法从卡面解析追加句'

# ---------------------------------------------------------------- 前置
pre = []


def chk(item, ok, detail=''):
    pre.append((item, ok, detail))
    if not ok:
        fail('PRE', '-', item, detail)


chk('delta 行数 == 32', len(delta) == 32, 'actual=%d' % len(delta))
chk('pivot32 行数 == 32', len(pivot) == 32, 'actual=%d' % len(pivot))
chk('defects 行数 == 10', len(defects) == 10, 'actual=%d' % len(defects))
chk('delta entry 集合 == pivot32', set(dby) == set(pivot),
    'delta-only=%s piv-only=%s' % (sorted(set(dby) - set(pivot)), sorted(set(pivot) - set(dby))))
chk('delta 内 entry 无重复', len(dby) == len(delta))
chk('32 行在 coverage.tsv 均命中', all(e in pivot and e in cov for e in pivot),
    'missing=%s' % [e for e in pivot if e not in cov])
chk('32 行在 coverage.tsv 无重复行', not ({e: n for e, n in cov_dupe.items() if e in pivot}),
    str({e: n for e, n in cov_dupe.items() if e in pivot}))
chk('delta 行顺序 == pivot32 顺序', [dec(c[0]) for _, _, c in delta] == list(pivot))
chk('32 行尾部均以卡面追加句结尾',
    all(c[3].endswith(APPEND.encode('utf-8')) for _, _, c in delta),
    '%d/32' % sum(1 for _, _, c in delta if c[3].endswith(APPEND.encode('utf-8'))))
chk('delta 未越界包含 FAIL 行(006BFF90/006C0A10)',
    not ({'006BFF90', '006C0A10'} & set(dby)))
if dec(del_hdr) != dec(cov_hdr):
    observe('表头分隔符不同', 'coverage 表头用逗号(%r) / delta 表头用制表符；数据行两者均为 8 列制表符' % dec(cov_hdr)[:40])

# coverage 未被写
cov_sha = hashlib.sha256(rd(COV)).hexdigest().upper()
rep_txt = dec(rd(REP))
rep_sha = re.findall(r'\b([0-9A-F]{64})\b', rep_txt)
chk('coverage.tsv 文件 sha256 与 REPORT 自述一致', bool(rep_sha) and all(s == cov_sha for s in rep_sha),
    'disk=%s report=%s' % (cov_sha[:20], [s[:20] for s in rep_sha]))
still_old = [e for e, d in defects.items() if d['old_value'] not in dec(cov[e][2][3])]
chk('10 行缺陷旧值仍留在 coverage.tsv（未并表）', not still_old, '异常=%s' % still_old)
import datetime
mt_cov = os.path.getmtime(COV)
mt_del = os.path.getmtime(DEL)
note_mtime = 'coverage mtime=%s / delta mtime=%s' % (
    datetime.datetime.fromtimestamp(mt_cov).strftime('%Y-%m-%d %H:%M:%S'),
    datetime.datetime.fromtimestamp(mt_del).strftime('%Y-%m-%d %H:%M:%S'))
chk('coverage.tsv mtime 早于 delta.tsv（未被本批改写）', mt_cov < mt_del, note_mtime)

# ---------------------------------------------------------------- 定向字节印证（辅助证据源）
def pe_map():
    data = rd(EXE)
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    nsec = struct.unpack_from('<H', data, pe + 6)[0]
    optsz = struct.unpack_from('<H', data, pe + 20)[0]
    opt = pe + 24
    base = struct.unpack_from('<I', data, opt + 28)[0]
    sec = opt + optsz
    secs = []
    for i in range(nsec):
        o = sec + i * 40
        vsz, va, rsz, raw = struct.unpack_from('<IIII', data, o + 8)
        secs.append((va, vsz, raw, rsz))

    def va2off(va):
        rva = va - base
        for sva, vsz, raw, rsz in secs:
            if sva <= rva < sva + max(vsz, rsz):
                return raw + (rva - sva)
        return None

    def guid_at(va):
        o = va2off(va)
        if o is None:
            return None
        b = data[o:o + 16]
        if len(b) < 16:
            return None
        d1 = struct.unpack_from('<I', b, 0)[0]
        d2, d3 = struct.unpack_from('<HH', b, 4)
        return '{%08X-%04X-%04X-%02X%02X-%s}' % (
            d1, d2, d3, b[8], b[9], b[10:16].hex().upper())
    def text_blob():
        """返回 (.text 原始字节, .text 线性 VA)。"""
        o = sec
        for i in range(nsec):
            oo = o + i * 40
            if data[oo:oo + 8].rstrip(b'\0') == b'.text':
                vsz, va, rsz, raw = struct.unpack_from('<IIII', data, oo + 8)
                return data[raw:raw + rsz], va + base
        return None, None

    return data, base, va2off, guid_at, text_blob


byte_ok = {}
byte_ctx = {}
guid_struct = {}
if os.path.exists(EXE):
    data, base, va2off, guid_at, text_blob = pe_map()
    # 注册点 call esi 地址取自审计 verdict.tsv 的 reason（“FFD6@XXXXXX 注册”）
    CALL = {}
    for e, d in audit_tsv.items():
        m = re.search(r'FFD6@([0-9A-F]{8}) 注册', d['reason'])
        if m:
            CALL[e] = int(m.group(1), 16)
    for e in list(defects):
        callva = CALL.get(e)
        if callva is None:
            byte_ok[e] = None
            continue
        off = va2off(callva - 5)
        if off is None:
            byte_ok[e] = None
            continue
        bs = data[off:off + 5]
        want = defects[e]['new_value'].replace('CLSID ', '')
        got = '%08X' % struct.unpack_from('<I', data, off + 1)[0] if bs[0] == 0x68 else None
        byte_ok[e] = (bs[0] == 0x68 and got == want)
        byte_ctx[e] = 'push %s @ %08X (call esi @ %08X)' % (got, callva - 5, callva)
        if got:
            guid_struct[e] = guid_at(int(got, 16))
    # 前一块（VSuperClass）实测：审计 VERDICT.md:1159 称其注册点(即 push 处)为 006BC5AE
    off = va2off(0x006BC5AE)
    prev_g = '%08X' % struct.unpack_from('<I', data, off + 1)[0]
    byte_ctx['_prev_block'] = prev_g
    guid_struct['_prev_block'] = guid_at(int(prev_g, 16))
    byte_ctx['_prev_block_site'] = '006BC5AE'

    # 全 .text 注册点唯一性扫描：每个 rclsid 指针被 push+call esi 注册的次数
    reg_scan = {}
    body, tva = text_blob()
    if body is not None:
        targets = ['%s' % d['new_value'].replace('CLSID ', '') for d in defects.values()]
        targets += ['007E9930', '007E9940', '007E98F0', '007E9910',
                    '007E9920', '007E9860', '007E9580']   # 同批 16 行里其余 6 个 + 上一块
        for g in sorted(set(targets)):
            pat = b'\x68' + struct.pack('<I', int(g, 16))
            hits, j = [], body.find(pat)
            while j >= 0:
                if body[j + 5:j + 7] == b'\xff\xd6':
                    hits.append(tva + j)
                j = body.find(pat, j + 1)
            reg_scan[g] = hits

# ---------------------------------------------------------------- 逐行核
def check_row(entry):
    ci, craw, ccols = cov[entry]
    di, draw, dcols = dby[entry]
    old4, new4 = dec(ccols[3]), dec(dcols[3])
    r = {'entry': entry, 'cov_line': ci + 1, 'old_len': len(old4), 'new_len': len(new4)}
    r['append_at_end'] = new4.endswith(APPEND)
    r['append_count'] = new4.count(APPEND)
    r['s126_before'] = old4.count('§12.6')
    r['s126_after'] = new4.count('§12.6')
    r['pre_126'] = old4.count('12.6')
    r['pre_d47'] = old4.count('D-47')
    r['pre_m84'] = old4.count('M84')
    r['piv_s126'] = pivot[entry]['s126_cited']
    body = new4[:-len(APPEND)] if r['append_at_end'] else None
    r['strict_prefix'] = (body == old4)
    if entry in defects:
        d = defects[entry]
        ot, nt = d['old_value'], d['new_value']
        pos = old4.find(ot)
        r.update(old_tok=ot, new_tok=nt, tok_pos=pos, tok_count_old=old4.count(ot),
                 tok_ctx=old4[max(0, pos - 34):pos + len(ot) + 34],
                 replace_exact=(new4 == old4.replace(ot, nt, 1) + APPEND),
                 piv_clsid=pivot[entry]['clsid'], piv_status=pivot[entry]['clsid_status'])
        av = audit_tsv.get(entry, {})
        r['avt_line'] = av.get('_line', '')
        r['avt_has_new'] = nt.replace('CLSID ', '') in av.get('reason', '')
        r['avt_mark'] = ('须改字' if '须改字' in av.get('reason', '') else
                         '须补' if '须补' in av.get('reason', '') else
                         '执行器 None' if '执行器 None' in av.get('reason', '') else '无')
        r['avt_verdict'] = av.get('verdict', '')
        r['md_sec_line'] = [i + 1 for i, ln in enumerate(audit_md)
                            if ln.startswith('GUID  实为 %s' % nt.replace('CLSID ', ''))]
        r['md_tab_line'] = [i + 1 for i, ln in enumerate(audit_md)
                            if ln.startswith('| %s |' % entry) and nt.replace('CLSID ', '') in ln]
        r['byte_ok'] = byte_ok.get(entry)
        r['byte_ctx'] = byte_ctx.get(entry, '')
        r['guid_struct'] = guid_struct.get(entry, '')
    return r


def vote_C(r):
    e = r['entry']
    if not r['append_at_end']:
        fail('C', e, '追加句不在行末/非逐字')
    if r['append_count'] != 1:
        fail('C', e, '追加句出现 %d 次' % r['append_count'])
    if r['s126_before'] != 0:
        fail('C', e, '原文已含 §12.6 仍追加', 'before=%d' % r['s126_before'])
    if r['s126_after'] - r['s126_before'] != 2:
        fail('C', e, '§12.6 增量 != 2（追加句内含 2 处）')


def vote_A(r):
    e = r['entry']
    if r['tok_count_old'] != 1:
        fail('A', e, 'old_value 在第4列出现 %d 次（应唯一）' % r['tok_count_old'])
    if not r['replace_exact']:
        fail('A', e, '非“仅换该 token + 尾部追加”的最小形式')
    if not r['avt_has_new']:
        fail('A', e, '审计 verdict.tsv 未见该新值')
    if r['avt_mark'] == '无':
        fail('A', e, '审计原文无缺陷标注')
    if not r['md_sec_line'] or not r['md_tab_line']:
        fail('A', e, '审计 VERDICT.md 段内 GUID 行或 §5 表缺该值',
             'sec=%s tab=%s' % (r['md_sec_line'], r['md_tab_line']))
    if r['piv_clsid'].upper() != r['new_tok'].replace('CLSID ', '').upper():
        fail('A', e, '新值与 pivot32.tsv clsid 不一致')
    if r['piv_status'] not in ('MISMATCH', 'MISSING_NONE'):
        fail('A', e, '探针未把该行标为缺陷', r['piv_status'])
    if r['byte_ok'] is False:
        fail('A', e, '定向字节复核与审计断言不符', r['byte_ctx'])


rows10 = sorted(defects, key=lambda x: int(x, 16))
only_append = sorted([e for e in pivot if e not in defects], key=lambda x: int(x, 16))
assert len(rows10) == 10 and len(only_append) == 22

SAMPLE_IDX = sorted({0, 21} | {round(21 * i / 7) for i in range(1, 7)})
rows8 = [only_append[i] for i in SAMPLE_IDX]
assert len(rows8) == 8 and len(set(rows8)) == 8

R = {}
for e in rows10:
    R[e] = check_row(e)
    vote_C(R[e])
    vote_A(R[e])
for e in rows8:
    R[e] = check_row(e)
    vote_C(R[e])
    if not R[e]['strict_prefix']:
        fail('C', e, '22 行“只追加”不满足严格前缀')

# 全 32 行机核（仅计数，不计入 18 行结论）
ALL = {}
for e in pivot:
    ALL[e] = check_row(e)
    vote_C(ALL[e])
    if e in defects and not ALL[e]['replace_exact']:
        fail('A', e, '最小性失败(全量核)')
    if e not in defects and not ALL[e]['strict_prefix']:
        fail('C', e, '严格前缀失败(全量核)')

# §D：第 1/2/3/5/6/7/8 列
d_bad = []
for _, _, c in delta:
    e = dec(c[0])
    ccols = cov[e][2]
    for k in (0, 1, 2, 4, 5, 6, 7):
        if c[k] != ccols[k]:
            d_bad.append((e, k + 1))
            break
if d_bad:
    for e, col in d_bad:
        fail('D', e, '第%d列与 coverage.tsv 不一致' % col)
g_bad = [dec(c[0]) for _, _, c in delta if c[4] != cov[dec(c[0])][2][4]]
if g_bad:
    fail('D', ','.join(g_bad), 'grade 被改')

# §B：CLSID 依据 + 冲突
clsid_new = {}
for e in rows10:
    nt = R[e]['new_tok']
    if nt.startswith('CLSID '):
        clsid_new[e] = nt.split(' ', 1)[1].upper()
conflicts = []
inv = {}
for e, v in clsid_new.items():
    inv.setdefault(v, []).append(e)
for v, es in inv.items():
    if len(es) > 1:
        conflicts.append('%s 被多 entry 共用: %s' % (v, es))
for e, v in clsid_new.items():
    for e2, d2 in pivot.items():
        if e2 != e and d2['clsid'].upper() == v:
            conflicts.append('%s(%s) 与 %s 的 clsid 相同' % (e, v, e2))
# 全库交叉：该 GUID 字面是否出现在 coverage.tsv 其它行
cross = {v: [] for v in clsid_new.values()}
for idx, raw, cols in cov_rows:
    if idx == 0 or len(cols) != 8:
        continue
    e = dec(cols[0])
    s = raw.upper()
    for v in cross:
        if v.encode() in s:
            cross[v].append(e)
for e, v in clsid_new.items():
    others = [x for x in cross[v] if x != e]
    if others:
        conflicts.append('%s 的 %s 另见于行 %s' % (e, v, others))
if conflicts:
    fail('B', ','.join(sorted(clsid_new)), 'CLSID 冲突', '; '.join(conflicts))
for e in rows10:
    nt = R[e]['new_tok']
    if nt.startswith('CLSID ') and R[e]['byte_ok'] is False:
        fail('B', e, '定向字节复核与 CLSID 断言不符', R[e]['byte_ctx'])

# 去重失败项
_seen, _u = set(), []
for f in fails:
    k = (f[0], f[1], f[2])
    if k not in _seen:
        _seen.add(k)
        _u.append(f)
fails[:] = _u

# ---------------------------------------------------------------- 输出
def line(*a):
    print(*a)


line('=' * 100)
line('R16-AUDIT-PIVOT32 · verify.py  (只读复跑)')
line('=' * 100)
line('追加句（卡面原文，%d chars）: %s' % (len(APPEND), APPEND))
line('§A 10 行: %s' % ', '.join(rows10))
line('§B 8 行（entry 升序首/末 + 等距 6，步长 21/7=3）: %s' % ', '.join(rows8))
line('')
line('-- 前置断言 --')
for item, ok, det in pre:
    line('  [%s] %s%s' % ('OK' if ok else 'NG', item, ('  | ' + det) if det and not ok else ''))
if obs:
    line('  [OBS] ' + obs[0][0] + ': ' + obs[0][1])

line('')
line('-- §A 10 行：有据 / 精确 / 最小 / 不误伤 --')
line('%-9s %-4s %-19s %-19s %-5s %-6s %-4s %-4s %-14s %s' % (
    'entry', 'cnt', 'old_tok', 'new_tok', 'pos', '字节复核', '最小', '标注', '审计依据', '探针'))
line('-' * 118)
for e in rows10:
    r = R[e]
    ev = 'verdict.tsv:%s' % r['avt_line']
    if r['md_tab_line']:
        ev += ' +VERDICT.md:%s' % ','.join(map(str, r['md_tab_line']))
    line('%-9s %-4d %-19s %-19s %-5d %-6s %-4s %-4s %-14s %s' % (
        e, r['tok_count_old'], r['old_tok'], r['new_tok'], r['tok_pos'],
        'OK' if r['byte_ok'] else ('n/a' if r['byte_ok'] is None else 'MISMATCH'),
        'OK' if r['replace_exact'] else 'NG', r['avt_mark'], ev, r['piv_status']))
line('')
line('  token 上下文（确认替换落在 CLSID 主张处，非他处同名串）:')
for e in rows10:
    line('    %-9s …%s…' % (e, R[e]['tok_ctx']))

line('')
line('-- 006BF810 方向专核 --')
r = R['006BF810']
line('  旧值 %s → 新值 %s（旧值在第4列出现 %d 次 @%d）' % (
    r['old_tok'], r['new_tok'], r['tok_count_old'], r['tok_pos']))
line('  上下文: …%s…' % r['tok_ctx'])
line('  审计原文三处一致要求改成 %s：' % r['new_tok'])
line('    VERDICT.md:1199  「%s」→「%s」' % ('7E9580', '007E9950'))
line('    VERDICT.md:1159  本行真实 GUID 为 007E9950（006BC5EB push）')
line('    VERDICT.md:%s  §5 汇总表 | 006BF810 | 006BF740 | 007E9950 |' % r['md_tab_line'][0])
line('    verdict.tsv:2    「本行实为 007E9950，须改字」')
line('  定向字节：%s' % r['byte_ctx'])
line('  指向的 CLSID 结构：%s' % r['guid_struct'])
line('  前一块实测: push %s @ 006BC5AE → %s' % (
    byte_ctx.get('_prev_block', 'n/a'), guid_struct.get('_prev_block', 'n/a')))
line('  （故审计“7E9580 属前一块、本行应为 007E9950”在字节层成立，改字方向 = 正确）')

line('')
line('-- §B 9 行 CLSID 依据/冲突 --')
line('%-9s %-11s %-11s %-11s %-6s %-4s %s' % ('entry', 'new_clsid', 'piv_clsid', '字节复核', 'avt行', '表行', '标注'))
line('-' * 96)
for e in rows10:
    v = clsid_new.get(e)
    if not v:
        continue
    r = R[e]
    line('%-9s %-11s %-11s %-11s %-6s %-4s %s' % (
        e, v, r['piv_clsid'], 'OK' if r['byte_ok'] else 'NG',
        r['avt_line'], ','.join(map(str, r['md_tab_line'])), r['avt_mark']))
line('  冲突/重号: %s' % ('无' if not conflicts else '; '.join(conflicts)))
if reg_scan:
    dup_reg = {g: h for g, h in reg_scan.items() if len(h) != 1}
    line('  全 .text 注册点唯一性（push imm32 + call esi）: %d 个 rclsid，各注册 %s' % (
        len(reg_scan), '恰好 1 处' if not dup_reg else '异常: %s' % dup_reg))
    for g in sorted(clsid_new.values()):
        if g in reg_scan:
            line('    %s ← 注册于 %s' % (g, ','.join('%08X' % s for s in reg_scan[g])))
    if dup_reg:
        fail('B', ','.join(sorted(clsid_new)), 'rclsid 注册点非唯一', str(dup_reg))
line('  审计全局依据: VERDICT.md:1160「11 行 GUID 写成 None … 并入前须补齐」；'
     '本批范围内 9 行（另 2 行 006BFF90/006C0A10 属 FAIL 行，不在 32 行内）')

line('')
line('-- §C §12.6（全 32 行机核，仅计数）--')
line('  尾部逐字追加且仅 1 次      : %d/32' % sum(1 for e in pivot if ALL[e]['append_at_end'] and ALL[e]['append_count'] == 1))
line('  原文已含 §12.6 的行         : %d/32（应为 0）' % sum(1 for e in pivot if ALL[e]['s126_before'] > 0))
line('  原文已含 “12.6/D-47/M84” 片段: %d/32（应为 0）' % sum(
    1 for e in pivot if ALL[e]['pre_126'] or ALL[e]['pre_d47'] or ALL[e]['pre_m84']))
line('  只追加行严格前缀            : %d/22' % sum(1 for e in pivot if e not in defects and ALL[e]['strict_prefix']))
line('  替换行 = 旧.replace+追加    : %d/10' % sum(1 for e in pivot if e in defects and ALL[e]['replace_exact']))
line('  追加句字面变体              : %d 种（应为 1）' % len({APPEND}))
n_form = sum(1 for e in pivot
             if pivot[e]['slot'] == '3'
             and pivot[e]['slot_value_matches'].upper() == 'TRUE'
             and pivot[e]['form'] == 'ALLOC_REG_PIVOT')
line('  追加句形态前提(pivot32: slot=3 且 slot 值==entry 且 form=ALLOC_REG_PIVOT): %d/32'
     % n_form)

line('')
line('-- §D 越权 --')
line('  第1/2/3/5/6/7/8 列逐字节不同: %d 行（应为 0）' % len({e for e, _ in d_bad}))
line('  grade 被改                  : %d 行（应为 0）' % len(g_bad))
line('  delta 行数 / 集合==pivot32  : %d / %s' % (len(delta), set(dby) == set(pivot)))
line('  coverage.tsv 是否被写        : sha 一致=%s；mtime %s' % (
    '是' if (bool(rep_sha) and all(s == cov_sha for s in rep_sha)) else '否', note_mtime))

line('')
line('-- 不合格清单 --')
if not fails:
    line('  (无)')
for sec, e, item, det in fails:
    line('  [%s] %-9s %s%s' % (sec, e, item, ('  | ' + det) if det else ''))

# ---------------------------------------------------------------- check18.tsv
hdr = ['entry', 'audit_class', 'cov_line', 'old_len', 'new_len', 'delta_len',
       'append_verbatim', 'append_count', 'append_at_end', 'strict_prefix',
       's126_before', 's126_after', 'pre_126_any', 'old_tok', 'new_tok',
       'tok_count_in_old', 'tok_pos', 'replace_exact', 'byte_push_imm_ok',
       'push_site', 'clsid_struct_guid',
       'ev_verdict_tsv_line', 'ev_verdict_md_sec_line', 'ev_verdict_md_tab_line',
       'piv_clsid', 'piv_clsid_status', 'cols_1_2_3_5_6_7_8_equal', 'verdict', 'note']
out = ['\t'.join(hdr)]
for e in rows10 + rows8:
    r = R[e]
    cls = 'A10-错值替换' if e in defects else 'B8-只追加'
    f_e = [f for f in fails if f[1] == e]
    verdict = 'FAIL' if f_e else 'PASS'
    note = '; '.join('%s(%s)' % (f[2], f[3]) for f in f_e)[:280]
    out.append('\t'.join([
        e, cls, str(r['cov_line']), str(r['old_len']), str(r['new_len']),
        str(r['new_len'] - r['old_len']),
        'Y' if r['append_at_end'] else 'N', str(r['append_count']),
        'Y' if r['append_at_end'] else 'N', 'Y' if r['strict_prefix'] else 'N',
        str(r['s126_before']), str(r['s126_after']),
        'Y' if (r['pre_126'] or r['pre_d47'] or r['pre_m84']) else 'N',
        r.get('old_tok', ''), r.get('new_tok', ''),
        str(r.get('tok_count_old', '')), str(r.get('tok_pos', '')),
        ('Y' if r['replace_exact'] else 'N') if e in defects else 'n/a',
        ('Y' if r['byte_ok'] else ('N' if r['byte_ok'] is False else 'n/a')) if e in defects else 'n/a',
        r.get('byte_ctx', ''), r.get('guid_struct', ''),
        str(r.get('avt_line', '')), ','.join(map(str, r.get('md_sec_line', []))),
        ','.join(map(str, r.get('md_tab_line', []))),
        r.get('piv_clsid', ''), r.get('piv_status', ''),
        'Y' if not [1 for ee, _ in d_bad if ee == e] else 'N',
        verdict, note,
    ]))
open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
line('')
line('写出: %s（18 行数据）' % OUT)
line('FAIL 条数: %d' % len(fails))
