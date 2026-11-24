# -*- coding: utf-8 -*-
"""
R16-PROBE-F1-PIVOT · pivot.py
测量脚本（可复跑）。只读 gamemd.exe；只写本目录。

做四件事：
  A. 对 32 行 `audit_ring4_alloc_reg_pivot` 逐行做**独立字节复核**
     （不依赖 verdict.tsv 的散文，先从字节解出 vt / slot / 槽值 / COL链 / 分配点 /
     寄存器枢轴 / 装表指令 / 发布点 / CLSID），再把散文与**已并表的 ④ 正文**对账。
  B. 站点唯一性（§8.6 条 1「site 不共用」）在 32 行内 + 对 76 行 ctor_install 交叉。
  C. 用写死的规则给 derivable 判定。
  D. 复算 4GAP 的「F1 缺口 122」口径，量清它是措辞分类产物还是真缺口。
  E. 14 行 sem_* 的归类。

用法： python pivot.py
"""
import sys, os, csv, io, re, json, struct, hashlib, collections

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
SCAN = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
PIN = os.path.join(R14, 'R16_PROBE_4GAP', '_pin_coverage.tsv')
LIVE = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
# 盘在动（㉙）：先把 live coverage 钉成本目录快照，全文只读快照。
COV = os.path.join(HERE, '_pin_coverage_live.tsv')
if not os.path.isfile(COV):
    import shutil
    shutil.copyfile(LIVE, COV)


def sha_of(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()
AUD = {'NAMED_PUSH_AUDIT4': os.path.join(R14, 'NAMED_PUSH_AUDIT4', 'verdict.tsv'),
       'NAMED_PUSH_AUDIT6': os.path.join(R14, 'NAMED_PUSH_AUDIT6', 'verdict.tsv')}
TARGET_REASON = 'audit_ring4_alloc_reg_pivot'

csv.field_size_limit(10 ** 7)


# ─────────────────────────── PE / 只读字节层 ───────────────────────────
class Img(object):
    def __init__(self, path):
        import pefile
        self.pe = pefile.PE(path, fast_load=True)
        self.pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.sec = []
        for s in self.pe.sections:
            self.sec.append((s.Name.rstrip(b'\0').decode('latin1'),
                             self.ib + s.VirtualAddress,
                             self.ib + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData),
                             s.PointerToRawData))
        self.raw = open(path, 'rb').read()
        self.sha = hashlib.sha256(self.raw).hexdigest().upper()
        # IAT: va -> symbol
        self.iat = {}
        for ent in getattr(self.pe, 'DIRECTORY_ENTRY_IMPORT', []) or []:
            for imp in ent.imports:
                if imp.address:
                    nm = imp.name
                    if nm is None:
                        nm = 'ord#%d' % (imp.ordinal or 0)
                    dll = ent.dll.decode('latin1') if isinstance(ent.dll, bytes) else str(ent.dll)
                    nm = nm.decode('latin1') if isinstance(nm, bytes) else str(nm)
                    self.iat[imp.address] = '%s!%s' % (dll, nm)

    def sec_of(self, va):
        for n, lo, hi, pr in self.sec:
            if lo <= va < hi:
                return n, lo, pr
        return None, None, None

    def off(self, va):
        n, lo, pr = self.sec_of(va)
        if n is None:
            raise ValueError('VA %08X 不在任何节' % va)
        return pr + (va - lo)

    def rd(self, va, n):
        o = self.off(va)
        return self.raw[o:o + n]

    def u32(self, va):
        return struct.unpack('<I', self.rd(va, 4))[0]

    def cstr(self, va, maxn=256):
        o = self.off(va)
        e = self.raw.index(b'\0', o)
        return self.raw[o:min(e, o + maxn)].decode('latin1')


IMG = Img(EXE)


def hx(va, n=16):
    return ' '.join('%02X' % b for b in IMG.rd(va, n))


# ─────────────────────────── 读入输入 ───────────────────────────
def load_tsv(path):
    with io.open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def load_coverage():
    """coverage.tsv 表头是逗号、数据是 TAB（历史遗留）⇒ 按 TAB 手工切。"""
    cov = {}
    with io.open(COV, encoding='utf-8-sig', newline='') as f:
        body = f.read().split('\n')
    for line in body[1:]:
        f = line.split('\t')
        if len(f) > 7:
            cov[f[0].strip().upper()] = dict(subsystem=f[1], name=f[2], sem=f[3],
                                             grade=f[4], path=f[5])
    return cov


SCANROWS = load_tsv(SCAN)
COVROWS = load_coverage()
PINROWS = {}
for line in io.open(PIN, encoding='utf-8-sig', newline='').read().split('\n')[1:]:
    f = line.split('\t')
    if len(f) > 7:
        PINROWS[f[0].strip().upper()] = dict(sem=f[3], grade=f[4])

VERD = {}
for tag in sorted(os.listdir(R14)):
    if not tag.startswith('NAMED_PUSH_AUDIT'):
        continue
    p = os.path.join(R14, tag, 'verdict.tsv')
    if not os.path.isfile(p):
        continue
    for r in load_tsv(p):
        r['_audit_dir'] = tag
        VERD[r['entry'].upper()] = r
AUD = dict((r['_audit_dir'], None) for r in VERD.values() if '_audit_dir' in r)

T32 = [r for r in SCANROWS if r['f_reason'] == TARGET_REASON]
T76 = [r for r in SCANROWS if r['f_reason'] == 'audit_ring4_ctor_install']
T14 = [r for r in SCANROWS if r['f_reason'] in ('sem_virtual_witness_only', 'sem_live_table_install')]
HEX8 = re.compile(r'\b([0-9A-F]{8})\b')


def addrs(text):
    return [int(x, 16) for x in HEX8.findall(text or '')]


def hexin(text):
    return set(x.upper() for x in HEX8.findall(text or ''))


# ─────────────────────────── 字节解码：分配块 ───────────────────────────
def decode_alloc_block(a0):
    """解 `push size / call new / add esp,4 / test eax / je / mov ecx,eax / call ctor`
    或（sub-form B）从 `call new` 起。返回 dict 或 None。"""
    try:
        b = IMG.rd(a0, 32)
    except ValueError:
        return None
    i = 0
    size = None
    if b[0] == 0x6A:                      # push imm8  → 分配尺寸
        size = b[1]
        i = 2
    elif a0 >= 2:
        # sub-form B：锚点是 `call new`，`push imm8` 在其前 2 字节
        pb = IMG.rd(a0 - 2, 2)
        if pb[0] == 0x6A:
            size = pb[1]
    if i >= len(b) or b[i] != 0xE8:
        return None
    rel = struct.unpack('<i', b[i + 1:i + 5])[0]
    new_site = a0 + i
    new_fn = new_site + 5 + rel
    i += 5
    if b[i:i + 3] != b'\x83\xC4\x04':     # add esp,4
        return None
    i += 3
    if b[i:i + 2] != b'\x85\xC0':         # test eax,eax
        return None
    i += 2
    if b[i] != 0x74:                      # je rel8
        return None
    i += 2
    if b[i:i + 2] != b'\x8B\xC8':         # mov ecx,eax  ← 寄存器枢轴
        return None
    pivot_site = a0 + i
    i += 2
    if b[i] != 0xE8:
        return None
    rel = struct.unpack('<i', b[i + 1:i + 5])[0]
    ctor_call = a0 + i
    ctor = ctor_call + 5 + rel
    return dict(size=size, new_site=new_site, new_fn=new_fn, pivot_site=pivot_site,
                ctor_call=ctor_call, ctor=ctor)


def clsid_text_check(sem, clsid):
    """已并表 ④ 正文里写的 CLSID 与字节解出的 CLSID 对账。
    正文可能写 8 位（007E98A0）也可能写 6 位（7E98F0）；两种都认。"""
    if not clsid:
        return '-', 'NONE'
    toks = re.findall(r'(?:CLSID|GUID)[^0-9A-Fa-f]{0,12}([0-9A-Fa-f]{6,8})', sem or '')
    if re.search(r'(?:CLSID|GUID)\s*None', sem or ''):
        return 'MISSING_NONE', 'None'
    if not toks:
        return 'MISSING', ''
    for t in toks:
        try:
            if int(t, 16) == clsid:
                return 'MATCH', t
        except ValueError:
            pass
    return 'MISMATCH', '/'.join(toks)


def decode_publish(start, vt):
    """从 start 起 64B 内找 `68 <imm32> FF D6/FF D0`（push CLSID；call esi/eax）。
    即「把 CLSID 压栈、经寄存器调 ole32!CoRegisterClassObject」的发布点。"""
    try:
        b = IMG.rd(start, 64)
    except ValueError:
        return None
    for i in range(0, len(b) - 7):
        if b[i] == 0x68 and b[i + 5] == 0xFF and b[i + 6] in (0xD6, 0xD0):
            return dict(clsid=struct.unpack('<I', b[i + 1:i + 5])[0],
                        push_site=start + i, call_site=start + i + 5,
                        reg='esi' if b[i + 6] == 0xD6 else 'eax')
    return None


def ctor_install(ctor):
    """ctor 形如 `8B C1 C7 40 04 00 00 00 00 C7 00 <vt32> C3`；
    返回 (装表指令地址, vt32) 或 None。"""
    try:
        b = IMG.rd(ctor, 20)
    except ValueError:
        return None
    sig = b'\x8B\xC1\xC7\x40\x04\x00\x00\x00\x00\xC7\x00'
    if b[:len(sig)] == sig:
        return ctor + len(sig) - 2, struct.unpack('<I', b[len(sig):len(sig) + 4])[0]
    # 兜底：任意 `C7 00 <vt32>` / `C7 01 <vt32>`
    for i in range(0, 16):
        if b[i] == 0xC7 and b[i + 1] in (0x00, 0x01, 0x02, 0x03, 0x06, 0x07):
            return ctor + i, struct.unpack('<I', b[i + 2:i + 6])[0]
    return None


def rtti_of(vt):
    """vt-4 = COL（.rdata）；COL+0xC = TD（实测在 .data）；TD+8 = 内联类名。"""
    try:
        col = IMG.u32(vt - 4)
        if IMG.sec_of(col)[0] != '.rdata':
            return None
        td = IMG.u32(col + 0xC)
        if IMG.sec_of(td)[0] is None:
            return None
        name = IMG.cstr(td + 8, 160)
        if not name.startswith('.?AV'):
            return None
        return dict(col=col, td=td, name=name)
    except (ValueError, struct.error):
        return None


def body_end(entry, limit=0x200):
    """entry 体内最后一个 `C2 xx 00` / `C3` 之前。取首个 `C2 10 00` 之后继续找，
    简化：取 [entry, entry+limit) 内最后一个 ret 的位置。"""
    b = IMG.rd(entry, limit)
    last = None
    i = 0
    while i < len(b) - 2:
        if b[i] == 0xC2 and b[i + 2] == 0x00:
            last = entry + i + 3
            i += 3
            continue
        if b[i] == 0xC3:
            last = entry + i + 1
            i += 1
            continue
        i += 1
    return last


# ─────────────────────────── A. 32 行逐行复核 ───────────────────────────
def vt_from_ring2(ring2):
    """ring2_at 首 token 即槽地址；vt = 槽地址 − 0xC（slot#3）。"""
    a = addrs(ring2)
    return (a[0] - 0xC) if a else None


def analyse_target(row):
    e = int(row['entry'], 16)
    v = VERD.get(row['entry'].upper(), {})
    ring2 = v.get('ring2_at', '')
    ring4 = v.get('ring4_at', '')
    vt = vt_from_ring2(ring2)
    rec = dict(entry=row['entry'].upper(), subsystem=row['subsystem'], name=row['name'],
               vt=None, slot=3, slot_value=None, slot_value_matches=False,
               ring4_at_text=ring4, form='', derivable='NEED_AUDIT',
               key_addrs_present='', note='', errs=[])
    if vt is None:
        rec['errs'].append('ring2_at 空')
        return rec
    rec['vt'] = '%08X' % vt
    slot_va = vt + 0xC
    try:
        sv = IMG.u32(slot_va)
    except ValueError:
        rec['errs'].append('槽地址不可读')
        return rec
    rec['slot_value'] = '%08X' % sv
    rec['slot_value_matches'] = (sv == e)
    rt = rtti_of(vt)
    rec['col'] = '%08X' % rt['col'] if rt else None
    rec['rtti'] = rt['name'] if rt else None
    if not rt:
        rec['errs'].append('RTTI 链解不出')
    a = addrs(ring4)
    rec['n_ring4'] = len(a)
    if not a:
        rec['errs'].append('ring4_at 空')
        return rec
    blk = decode_alloc_block(a[0])
    if not blk:
        rec['errs'].append('分配块解不出 @%08X' % a[0])
        rec['derivable'] = 'NO'
        return rec
    rec.update(new_site='%08X' % blk['new_site'], new_fn='%08X' % blk['new_fn'],
               pivot_site='%08X' % blk['pivot_site'], ctor_call='%08X' % blk['ctor_call'],
               ctor='%08X' % blk['ctor'], size=blk['size'],
               alloc_site='%08X' % a[0])
    ci = ctor_install(blk['ctor'])
    if not ci:
        rec['errs'].append('ctor 内未找到 C7 装表')
        rec['derivable'] = 'NO'
        return rec
    rec['install_site'] = '%08X' % ci[0]
    rec['install_vt'] = '%08X' % ci[1]
    rec['install_matches_row_vt'] = (rt is not None and ci[1] == vt)
    pub = decode_publish(blk['ctor_call'], vt)
    if pub:
        rec['clsid'] = '%08X' % pub['clsid']
        rec['publish_call'] = '%08X' % pub['call_site']
        rec['publish_reg'] = pub['reg']
    # 装表点是否在 entry 体内
    be = body_end(e)
    rec['entry_body_end'] = '%08X' % be if be else '?'
    rec['install_outside_body'] = (be is not None and not (e <= ci[0] < be))
    # 形态
    rec['form'] = 'ALLOC_REG_PIVOT'
    # 关键地址四要素自核
    kp = []
    if rt is not None and rec['slot_value_matches']:
        kp.append('vt')
        kp.append('slot')
    if blk:
        kp.append('pivot')
    if ci:
        kp.append('install')
    rec['key_addrs_present'] = '+'.join(kp)
    return rec


def scan_slot_for(tgt, slots=130):
    """在 .rdata 里找 dd tgt 的命中，再按 −4k 反推 vt 并解 RTTI。
    （.data 的 vtable 扫不到——那正是 2 个 locomotion ctor 的情形，它们的 ④ 走 direct call。）"""
    pat = struct.pack('<I', tgt)
    hits = []
    for n, lo, hi, pr in IMG.sec:
        if n != '.rdata':
            continue
        blob = IMG.raw[pr:pr + (hi - lo)]
        i = blob.find(pat)
        while i >= 0:
            if i % 4 == 0:
                hits.append(lo + i)
            i = blob.find(pat, i + 1)
    out = []
    for h in hits[:4]:
        for k in range(0, slots):
            vt = h - 4 * k
            try:
                col = IMG.u32(vt - 4)
            except ValueError:
                continue
            if IMG.sec_of(col)[0] != '.rdata':
                continue
            try:
                td = IMG.u32(col + 0xC)
                nm = IMG.cstr(td + 8, 90)
            except (ValueError, struct.error):
                continue
            if nm.startswith('.?AV'):
                out.append(dict(slot_va=h, slot=k, vt=vt, col=col, rtti=nm))
                break
    return dict(hits=hits, resolved=out)


def find_direct_call(fstart, flen, target):
    """在 [fstart, fstart+flen) 里找 `E8` 且 site+5+rel32 == target。"""
    try:
        b = IMG.rd(fstart, flen)
    except ValueError:
        return []
    r = []
    for i in range(len(b) - 5):
        if b[i] == 0xE8:
            rel = struct.unpack('<i', b[i + 1:i + 5])[0]
            if fstart + i + 5 + rel == target:
                r.append(fstart + i)
    return r


# ─────────────────────────── 写死规则：derivable ───────────────────────────
RULE = """
R1  vt 必须由 ring2_at 首 token − 0xC 得到，且 dword[vt+0xC] == entry
       （槽值不吻合 ⇒ NEED_AUDIT，理由：② 的槽位自述与字节不符）
R2  vt−4 必须是 .rdata 的 COL，且 COL+0xC→TD、TD+8 的内联名以 `.?AV` 开头
       （解不出 ⇒ NEED_AUDIT，理由：② 的 RTTI 链不可复现）
R3  以 ring4_at 首地址为锚，必须解出完整分配块
       push imm8? / call new / add esp,4 / test eax,eax / je / mov ecx,eax / call ctor
       （解不出 ⇒ NO，理由：枢轴站点形态不成立）
R4  ctor 体内必须存在 `C7 00 <imm32>` 装表指令，且 imm32 == R1 的 vt
       （不存在或不等 ⇒ NO，理由：装表点不可复现 / 装表值与本行 vt 不符）
R5  装表点必须在 entry 体内之外（e <= install < body_end 则视为 self-ctor ⇒ NO）
R6  四要素 {vt, slot, pivot(分配/枢轴), install(装表点)} 至少 3 项独立自核通过 ⇒ YES
       （<3 ⇒ NEED_AUDIT）
note: 本规则只判「能否据字节写出合 §12.6 的 ④」；不判 grade、不判 ③、不判命名。
"""


def apply_rule(rec):
    """按 RULE 给 derivable（四要素已在 analyse_target 里自核）。"""
    if rec.get('vt') is None or not rec.get('slot_value_matches'):
        return 'NEED_AUDIT', 'R1 槽值不吻合或 vt 不可得'
    if rec.get('rtti') is None:
        return 'NEED_AUDIT', 'R2 RTTI 链不可复现'
    if 'install_site' not in rec:
        return 'NO', 'R4 装表指令不可复现'
    if not rec.get('install_matches_row_vt'):
        return 'NO', 'R4 装表值与本行 vt 不符'
    if not rec.get('install_outside_body'):
        return 'NO', 'R5 装表点在 entry 体内（self-ctor 属 ②）'
    n = len([x for x in rec.get('key_addrs_present', '').split('+') if x])
    if n < 3:
        return 'NEED_AUDIT', 'R6 四要素自核 <3'
    return 'YES', 'R1–R6 全通（%d/4 要素自核）' % n


# ─────────────────────────── B. 站点唯一性 ───────────────────────────
def site_stats(recs, key):
    c = collections.Counter(r[key] for r in recs if key in r)
    dup = {k: n for k, n in c.items() if n > 1}
    return c, dup


# ─────────────────────────── D. 缺口口径复算 ───────────────────────────
# gap.py:72–105 的四个正则**逐字照抄**（只读引用，不 import，避免在他人目录落 .pyc）
RE_SLOT_WIT = re.compile(r'④\s*活表槽位见证')
RE_DIRECT_CN = re.compile(r'^④[^；;。]{0,80}?直调')
RE_DIRECT_EN = re.compile(r'^④\s*direct\s*E8', re.I)
RE_INSTALL = re.compile(r'^④[^；;。]{0,80}?(?:活\s*vt|安装点|构造安装)')
RE_LABEL = re.compile(r'③b④')
WINDOW = 100


def clause(text, start):
    w = text[start:start + WINDOW]
    m = re.search(r'[；;。]', w)
    return w[:m.start()] if m else w


def flags_of(sem):
    f = dict(slot_witness=False, direct_sites=False, install_only=False, n_ring4=0)
    for m in re.finditer('④', sem or ''):
        f['n_ring4'] += 1
        cl = clause(sem, m.start())
        if RE_SLOT_WIT.match(cl):
            f['slot_witness'] = True
        elif RE_DIRECT_CN.match(cl):
            f['direct_sites'] = True
        elif RE_DIRECT_EN.match(cl):
            pass
        elif RE_INSTALL.match(cl):
            f['install_only'] = True
    return f


def bucket_of(f, sem):
    if f['slot_witness']:
        return 'B1_slot_witness'
    if f['direct_sites']:
        return 'B2_direct_sites'
    if f['install_only']:
        return 'B3_install_only'
    if RE_LABEL.search(sem or ''):
        return 'B4_only_label_3b'
    if f['n_ring4']:
        return 'B5_other_ring4_text'
    return 'B6_nothing'


# ─────────────────────────── 主流程 ───────────────────────────
def main():
    out = io.open(os.path.join(HERE, '_pivot_run.json'), 'w', encoding='utf-8', newline='\n')
    log = []

    def P(s):
        log.append(s)

    P('gamemd.exe sha256 = %s' % IMG.sha)
    P('coverage pin(本目录) sha=%s bytes=%d' % (sha_of(COV), os.path.getsize(COV)))
    try:
        P('coverage live      sha=%s bytes=%d（仅作时点对照，全文不用它）'
          % (sha_of(LIVE), os.path.getsize(LIVE)))
    except OSError:
        P('coverage live 不可读')
    P('coverage 4GAP pin  sha=%s bytes=%d' % (sha_of(PIN), os.path.getsize(PIN)))
    P('target rows (f_reason=%s) = %d' % (TARGET_REASON, len(T32)))

    recs = []
    for r in T32:
        rec = analyse_target(r)
        d, why = apply_rule(rec)
        rec['derivable'] = d
        rec['rule_reason'] = why
        recs.append(rec)
    recs.sort(key=lambda x: x['entry'])

    # 三桶
    tb = collections.Counter(r['derivable'] for r in recs)
    P('三桶 = %s' % dict(tb))

    # 已并表状态 + 措辞
    for r in recs:
        c = COVROWS.get(r['entry'])
        p = PINROWS.get(r['entry'])
        r['merged'] = bool(c)
        r['merged_grade'] = c['grade'] if c else None
        r['merged_has4'] = ('④' in c['sem']) if c else False
        r['merged_sem'] = c['sem'] if c else ''
        r['pin_has4'] = ('④' in p['sem']) if p else False
        r['pin_grade'] = p['grade'] if p else None
        r['s126_cited'] = ('§12.6' in r['merged_sem']) or ('D-47' in r['merged_sem'])
        r['clsid_status'], r['clsid_text_tok'] = clsid_text_check(
            r['merged_sem'], int(r['clsid'], 16) if r.get('clsid') else None)
        hs = hexin(r['merged_sem'])
        r['clsid_in_text'] = (r['clsid_status'] == 'MATCH')
        r['vt_in_text'] = r.get('vt') in hs
        r['ctor_in_text'] = r.get('ctor') in hs
        r['alloc_in_text'] = r.get('alloc_site') in hs
        r['clsid_in_text_any'] = r.get('clsid') in hs

    # 站点唯一性
    _, dup_pivot = site_stats(recs, 'pivot_site')
    _, dup_install = site_stats(recs, 'install_site')
    _, dup_ctor = site_stats(recs, 'ctor')
    P('32 行内重复：pivot_site=%s install_site=%s ctor=%s' % (dup_pivot, dup_install, dup_ctor))
    rec_install_all = set(r['install_site'] for r in recs if 'install_site' in r)
    rec_ctor_all = set(r['ctor'] for r in recs if 'ctor' in r)
    # 与 76 行交叉（76 行的 ring4_at 是 `C7 /0` 装表指令）
    c76 = set()
    for r in T76:
        v = VERD.get(r['entry'].upper(), {})
        for a in addrs(v.get('ring4_at', '')):
            c76.add('%08X' % a)
    P('32 install ∩ 76 ring4_at = %s' % sorted(rec_install_all & c76))
    P('32 ctor    ∩ 76 ring4_at = %s' % sorted(rec_ctor_all & c76))

    # 全量 site 计数（32+76 = 108）
    all_site = collections.Counter()
    for r in recs:
        if 'install_site' in r:
            all_site[r['install_site']] += 1
    for s in c76:
        all_site[s] += 1
    P('108 行装表站点总数=%d，重复站点=%s' % (len(all_site),
                                       {k: v for k, v in all_site.items() if v > 1}))
    # 共用被调（不是共用站点）：所有 32 行是否共用同一个 operator new
    newf = collections.Counter(r['new_fn'] for r in recs if 'new_fn' in r)
    P('32 行共用分配器 = %s' % dict(newf))
    size_c = collections.Counter(r.get('size') for r in recs)
    P('32 行分配尺寸 = %s' % dict(size_c))
    # esi 的来历：宿主内 `mov esi,[007E15D8]`
    prov = None
    try:
        pat = b'\x8B\x35\xD8\x15\x7E\x00'
        lo, hi = 0x006BB9A0, 0x006BD000
        blob = IMG.raw[IMG.off(lo):IMG.off(hi)]
        k = blob.find(pat)
        if k >= 0:
            site = lo + k
            prov = dict(site='%08X' % site, iat='007E15D8',
                        sym=IMG.iat.get(0x007E15D8, '?'))
    except ValueError:
        pass
    P('esi 来历 = %s' % prov)

    # D. 缺口口径复算
    gap_rows = []
    for r in SCANROWS:
        if r['f_reason'] not in ('audit_ring4_ctor_install', TARGET_REASON,
                                 'sem_virtual_witness_only', 'sem_live_table_install'):
            continue
        e = r['entry'].upper()
        c = COVROWS.get(e)
        sem = c['sem'] if c else ''
        f = flags_of(sem)
        bk = bucket_of(f, sem)
        gap_rows.append(dict(entry=e, f_reason=r['f_reason'], bucket=bk,
                             grade=c['grade'] if c else '-',
                             has4=('④' in sem),
                             sem_len=len(sem)))
    P('F1 122 行的现盘分桶 = %s' % dict(collections.Counter(
        g['bucket'] for g in gap_rows)))
    P('F1 122 行现盘 grade = %s' % dict(collections.Counter(g['grade'] for g in gap_rows)))
    P('F1 122 行含 ④ 字符 = %d' % sum(1 for g in gap_rows if g['has4']))
    by_reason = {}
    for rs in ('audit_ring4_ctor_install', TARGET_REASON,
               'sem_virtual_witness_only', 'sem_live_table_install'):
        sub = [g for g in gap_rows if g['f_reason'] == rs]
        by_reason[rs] = dict(
            n=len(sub),
            buckets=dict(collections.Counter(g['bucket'] for g in sub)),
            grades=dict(collections.Counter(g['grade'] for g in sub)),
            has4=sum(1 for g in sub if g['has4']),
        )
    P('按 f_reason 拆：%s' % json.dumps(by_reason, ensure_ascii=False))

    summary = dict(
        exe_sha256=IMG.sha,
        cov_pin_sha=sha_of(COV), cov_pin_bytes=os.path.getsize(COV),
        cov_4gap_pin_sha=sha_of(PIN), cov_4gap_pin_bytes=os.path.getsize(PIN),
        cov_live_sha=(sha_of(LIVE) if os.path.isfile(LIVE) else None),
        cov_live_bytes=(os.path.getsize(LIVE) if os.path.isfile(LIVE) else None),
        target_n=len(T32),
        three_buckets=dict(tb),
        clsid_defects=dict(collections.Counter(r.get('clsid_status', '-') for r in recs)),
        provenance=dict(
            vt_in_text=sum(1 for r in recs if r.get('vt_in_text')),
            ctor_in_text=sum(1 for r in recs if r.get('ctor_in_text')),
            alloc_in_text=sum(1 for r in recs if r.get('alloc_in_text')),
            clsid_in_text=sum(1 for r in recs if r.get('clsid_in_text_any')),
        ),
        s126_whole_table=sum(1 for v in COVROWS.values()
                             if ('§12.6' in v['sem']) or ('D-47' in v['sem'])),
        s126_proved=sum(1 for v in COVROWS.values()
                        if v['grade'] == '[已证]' and (('§12.6' in v['sem']) or ('D-47' in v['sem']))),
        pivot_site_dup=dup_pivot, install_site_dup=dup_install, ctor_dup=dup_ctor,
        shared_allocator=dict(newf), sizes=dict((str(k), v) for k, v in size_c.items()),
        esi_provenance=prov,
        cross_76=dict(install=sorted(rec_install_all & c76), ctor=sorted(rec_ctor_all & c76)),
        gap122=dict(
            buckets=dict(collections.Counter(g['bucket'] for g in gap_rows)),
            grades=dict(collections.Counter(g['grade'] for g in gap_rows)),
            has4=sum(1 for g in gap_rows if g['has4']),
            by_reason=by_reason),
        merged32=dict(
            n=sum(1 for r in recs if r['merged']),
            proved=sum(1 for r in recs if r['merged_grade'] == '[已证]'),
            has4=sum(1 for r in recs if r['merged_has4']),
            pin_has4=sum(1 for r in recs if r['pin_has4']),
            s126_cited=sum(1 for r in recs if r['s126_cited']),
        ),
        rule=RULE.strip().split('\n'),
        log=log,
    )

    # ── pivot32.tsv ──
    cols = ['entry', 'subsystem', 'name', 'vt', 'slot', 'slot_value_matches',
            'ring4_at_text', 'form', 'derivable', 'key_addrs_present', 'note',
            # —— 本卡追加列（卡面 11 列之后，逐列自解释） ——
            'merged_grade', 'merged_has4', 'pin_has4', 's126_cited',
            'install_site', 'ctor', 'pivot_site', 'clsid', 'clsid_in_text',
            'clsid_status', 'clsid_text_tok', 'rule_reason', 'alloc_site']
    with io.open(os.path.join(HERE, 'pivot32.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(cols) + '\n')
        for r in recs:
            note = []
            if r['merged'] and r['merged_grade'] == '[已证]':
                note.append('现盘已[已证]且已含④')
            if r['pin_has4']:
                note.append('4GAP pin 截面即已含④')
            if r.get('clsid_status') == 'MISMATCH':
                note.append('④正文CLSID错写%s(字节%s)' % (r.get('clsid_text_tok'), r['clsid']))
            elif r.get('clsid_status') == 'MISSING_NONE':
                note.append('④正文留占位符CLSID None(字节%s)' % r['clsid'])
            elif r.get('clsid_status') == 'MISSING':
                note.append('④正文未写CLSID(字节%s)' % r['clsid'])
            if r.get('s126_cited') is False:
                note.append('未引§12.6')
            if r['errs']:
                note.append('ERR:' + ';'.join(r['errs']))
            row = [r.get(c) if not isinstance(r.get(c), bool) else ('TRUE' if r.get(c) else 'FALSE')
                   for c in cols[:11]]
            row[10] = '; '.join(note) if note else ''
            extra = [r.get('merged_grade') or '-',
                     'TRUE' if r['merged_has4'] else 'FALSE',
                     'TRUE' if r['pin_has4'] else 'FALSE',
                     'TRUE' if r['s126_cited'] else 'FALSE',
                     r.get('install_site') or '-', r.get('ctor') or '-',
                     r.get('pivot_site') or '-', r.get('clsid') or '-',
                     ('TRUE' if r.get('clsid_in_text') else 'FALSE'),
                     r.get('clsid_status') or '-', r.get('clsid_text_tok') or '-',
                     r.get('rule_reason') or '-', r.get('alloc_site') or '-']
            f.write('\t'.join(str(x) for x in row + extra) + '\n')

    # ── other14.tsv ──
    with io.open(os.path.join(HERE, 'other14.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('entry\tsubsystem\tname\tf_reason\tn_anch\thas_dispatch\thas_direct\t'
                'in_atlas\tgrade\thas4_char\tevidence_path\tsem_head\thas_audit_record\t'
                'deriv_class\tslot_rtti\tslot_va\tslot_idx\tdirect_sites\twhy_no_audit\n')
        for r in T14:
            e = r['entry'].upper()
            c = COVROWS.get(e, {})
            sem = c.get('sem', '')
            has_aud = 'TRUE' if e in VERD else 'FALSE'
            sv = scan_slot_for(int(e, 16))
            ds = []
            # 语义栏里的宿主地址可能写成 6 位（6C4010）或 8 位；按 VA 补零再试
            for tok in re.findall(r'\b([0-9A-F]{6,8})\b', sem):
                if len(tok) < 6:
                    continue
                try:
                    fs = int(tok, 16)
                except ValueError:
                    continue
                if IMG.sec_of(fs)[0] != '.text':
                    continue
                ds += ['%08X' % x for x in find_direct_call(fs, 0x160, int(e, 16))]
            ds = sorted(set(ds))
            dc = ('already_proved_direct_call' if ds else
                  ('already_proved_vtable_dispatch' if 'vtable dispatched' in sem
                   else 'already_proved_virtual_dispatch'))
            if r['f_reason'] == 'sem_live_table_install' and not ds:
                dc = 'already_proved_ctor_install'
            kind = ('非 F1：审计序列里无 ring4_at 记录（n_anch=0），'
                    '④ 的等价物写在语义栏散文里，未用 `④ …` 子句措辞')
            f.write('\t'.join([e, r['subsystem'], r['name'], r['f_reason'], r['n_anch'],
                               r['has_dispatch'], r['has_direct'], r['in_atlas'],
                               c.get('grade', '-'),
                               'TRUE' if '④' in sem else 'FALSE',
                               c.get('path', '-'),
                               (sem[:120].replace('\t', ' ').replace('\n', ' ')),
                               has_aud, dc,
                               sv['resolved'][0]['rtti'] if sv['resolved'] else '-',
                               ('%08X' % sv['resolved'][0]['slot_va']) if sv['resolved'] else '-',
                               str(sv['resolved'][0]['slot']) if sv['resolved'] else '-',
                               ';'.join(ds) if ds else '-', kind]) + '\n')

    # ── 复算明细（给 REPORT 用）──
    with io.open(os.path.join(HERE, '_gap122_recompute.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('entry\tf_reason\tbucket\tgrade\thas4\tsem_len\n')
        for g in gap_rows:
            f.write('%s\t%s\t%s\t%s\t%s\t%d\n' % (g['entry'], g['f_reason'], g['bucket'],
                                                 g['grade'], g['has4'], g['sem_len']))

    json.dump(summary, out, ensure_ascii=False, indent=1, default=str)
    out.close()

    print('\n'.join(log))
    print()
    print('三桶 =', dict(tb))
    print('merged32 =', summary['merged32'])
    print('gap122 buckets =', summary['gap122']['buckets'])
    return summary


if __name__ == '__main__':
    main()
