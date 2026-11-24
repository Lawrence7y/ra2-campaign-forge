# -*- coding: utf-8 -*-
"""
D47-SURFACE — D-47 影响面逐行测量 (measurement only, no ruling).

Classifies every `[已证]` row of COVERAGE/coverage.tsv by the FORM of its ring-4
(④ 使用见证) evidence:

  F1 · slot-install form  : ④ rests on "entry occupies vtable slot N" + "that table is
                            installed by a ctor inside .text"  (the shared pivot)
  F2 · visible dispatch   : ④ has a dispatch point independent of the slot
                            (call dword ptr [reg+disp] pinned to this class / real caller
                             that is not direct-only)
  F3 · direct-only        : only static (E8) callers
  F4 · other / undecidable: everything else  (reported separately, never folded into F1/F2)

Evidence order (per card): audit-table `same_source`/`ring4_at` first; otherwise the ④
description carried by the row's evidence / semantics.  Ambiguity -> F4.

Run:  python surface.py
Writes: surface.tsv, distribution.tsv, REPORT.md, work/*.txt
"""
import io, os, re, sys, json, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)                     # ...\next_re_20261117_r14
ROOT = os.path.dirname(os.path.dirname(R14))    # ...\ra2-campaign-forge
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PANEL = os.path.join(R14, 'COVERAGE', 'PANEL.md')
COMMON = os.path.join(R14, 'R14_COMMON.md')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
WORK = os.path.join(HERE, 'work')

sys.path.insert(0, os.path.join(HERE, 'work'))
import probe  # noqa: E402

GRADE_PROVED = '[已证]'
HEX8 = re.compile(r'(?<![0-9A-Za-z])(?:0x)?([0-9A-Fa-f]{8})(?![0-9A-Za-z])')


# ----------------------------------------------------------------------------- inputs
def load_coverage():
    lines = open(COV, encoding='utf-8-sig').read().splitlines()
    rows = []
    for ln in lines[1:]:
        c = ln.split('\t')
        if len(c) != 8:
            continue
        rows.append(dict(entry=c[0].upper(), subsystem=c[1], name=c[2], sem=c[3],
                         grade=c[4], ev=c[5], n_sources=c[6], conflict=c[7]))
    return rows


def load_atlas():
    out = set()
    for i, ln in enumerate(open(ATLAS, encoding='utf-8-sig')):
        if i == 0:
            continue
        out.add(ln.split('\t')[0].strip().upper())
    return out


def load_audit_records():
    """entry -> (path, dict) from NAMED_PUSH_AUDIT*/verdict.tsv (the tables with ring4_at)."""
    recs = {}
    for d in sorted(os.listdir(R14)):
        f = os.path.join(R14, d, 'verdict.tsv')
        if not (d.startswith('NAMED_PUSH_AUDIT') and os.path.isfile(f)):
            continue
        L = open(f, encoding='utf-8-sig').read().splitlines()
        hdr = L[0].split('\t')
        if 'ring4_at' not in hdr:
            continue
        for ln in L[1:]:
            c = ln.split('\t')
            if len(c) < len(hdr):
                continue
            d2 = dict(zip(hdr, c))
            recs.setdefault(d2['entry'].upper(), (os.path.relpath(f, R14), d2))
    return recs


def load_census_trace():
    import glob
    tr = {}
    for f in glob.glob(os.path.join(R14, 'C*_census', 'EVIDENCE', 'classification_trace.tsv')):
        L = open(f, encoding='utf-8-sig').read().splitlines()
        hdr = L[0].split('\t')
        for ln in L[1:]:
            c = ln.split('\t')
            if len(c) < len(hdr):
                continue
            d = dict(zip(hdr, c))
            try:
                a = '%08X' % int(d['entry'])
            except (ValueError, KeyError):
                continue
            tr.setdefault(a, d)
    return tr


# ----------------------------------------------------------------------------- anchors
def anchors_in(text, entry=None):
    """Decode every 8-hex token in text. Returns list of dicts."""
    out = []
    if not text:
        return out
    for m in HEX8.finditer(text):
        try:
            va = int(m.group(1), 16)
        except ValueError:
            continue
        if not (0x00401000 <= va < 0x00B96000):
            continue
        kind, info = probe.decode_at(va)
        out.append(dict(va=va, kind=kind, info=info,
                        is_entry=(entry is not None and va == int(entry, 16))))
    return out


def forms(anch, entry=None):
    """Collapse anchor list into the set of evidence forms present."""
    tgt = int(entry, 16) if entry else None
    s = set()
    for a in anch:
        if a['kind'] == 'MOV_IMM' and a['info'].get('vt'):
            s.add('install')                      # mov [reg], <vtable in .rdata>
        elif a['kind'] == 'CALL_VT':
            s.add('dispatch')                     # call dword ptr [reg+disp]
        elif a['kind'] == 'CALL_REL' and tgt is not None and a['info'].get('target') == tgt:
            s.add('direct')                       # e8 -> this entry
    return s


# ④ language markers
LIVE_TABLE = re.compile(r'活表|活虚表|活\s*vptr|活vptr|构造器装|ctor\s*装|构造器装入|由构造器'
                        r'|ctor install|LIVE\(ctor\)|构造期活\s*vptr|虚表槽\s*\d+|slot\s*\d+\s*=')
VIRT_WITNESS = re.compile(r'仅虚派发见证|无直接调用者|虚派发见证')
DISPATCH_TXT = re.compile(r'派发点|虚派发|call\s*\[|call\s+dword\s+ptr\s*\[|活虚表派发|槽位派发')
NEG_DISPATCH = re.compile(r'无[^，。;]{0,12}派发|无直调|无可证派发|无槽位|无\s*call\s*\[')
DIRECT_ONLY = re.compile(r'唯一\s*call\s*直指|call\s*直指|直调|direct\s*call|唯一\s*调用者|直指'
                         r'|called\s+(by|from)|0\s*direct\s+callers')
VIRT_WITNESS_EN = re.compile(r'vtable[\s-]*dispatch(ed)?', re.I)
NO_RING4 = re.compile(r'YRpp[/\\]kb\s*地址名|YRpp\s*named|names?[- ]only', re.I)
# ② slot identity markers (used only to flag the F1-leaning band, never to assert F1)
SLOT_ID = re.compile(r'vtable\s*槽|虚表槽|\bslot\s*\d+|slot\d+|vslot|vt\[\s*\d+\s*\]|vt\+\s*0x[0-9A-Fa-f]+')
INSTALL_WORD = re.compile(r'装表|装入|装\s*00|ctor|构造器|factory.*(push|size)|entry 写本类vtable|C7\s*\[this\]')


def classify(row, audit, trace):
    """
    Returns dict(form, reason, anchor, evidence_kind, band)
    form in F1..F4 ; band in B1..B5 (see REPORT)
    """
    entry = row['entry']
    sem = row['sem']
    evk = evidence_kind(row)[0]

    # ---- 1) audit table route (ring4_at) -----------------------------------
    if entry in audit:
        apath, rec = audit[entry]
        if rec.get('verdict', '').strip() == 'PASS':
            r4 = rec.get('ring4_at', '')
            ss = rec.get('same_source', '')
            anch = anchors_in(r4, entry)
            fm = forms(anch, entry)
            neg = bool(NEG_DISPATCH.search(r4))
            txt_disp = bool(DISPATCH_TXT.search(r4)) and not neg
            real_caller = (('真实调用者' in r4) or
                           ('调用者' in r4 and '无直调' not in r4)) and not neg
            base = dict(anchor=r4, evidence_kind=evk, audit=apath, same_source=ss)
            # a direct call to this entry is a ④ witness independent of the slot ->
            # the row does NOT depend on the slot pivot (real caller, not direct-only)
            if 'dispatch' not in fm and 'install' in fm and 'direct' in fm:
                return dict(form='F2', reason='audit_ring4_install_plus_caller', band='B3', **base)
            if 'dispatch' in fm or txt_disp or real_caller:
                return dict(form='F2', reason='audit_ring4_dispatch', band='B3', **base)
            if 'install' in fm:
                return dict(form='F1', reason='audit_ring4_ctor_install', band='B1', **base)
            if 'direct' in fm:
                return dict(form='F3', reason='audit_ring4_direct', band='B4', **base)
            # ring4_at names an alloc/register site; the ctor install is only in `reason`
            if re.search(r'ctor|构造', rec.get('reason', '')) and \
               re.search(r'装|C7\s*0?0?\w*\s*装|mov\s*\[\w+\],0?7[EF]', rec.get('reason', '')):
                return dict(form='F1', reason='audit_ring4_alloc_reg_pivot', band='B1', **base)
            return dict(form='F4', reason='audit_ring4_unresolved', band='B5', **base)

    # ---- 2) ring-4 wording in the row's own text ---------------------------
    anch = anchors_in(sem, entry)
    fm = forms(anch, entry)
    if 'dispatch' in fm and not NEG_DISPATCH.search(sem):
        return dict(form='F2', reason='sem_call_mem_anchor', anchor=_first(anch, 'CALL_VT'),
                    evidence_kind=evk, band='B3')
    # a ctor/dtor whose own body installs the vptr: that install is ②/③, so the ④ must be
    # a caller.  "called by ..." / a decoded E8 to this entry => not slot-dependent.
    if 'install' in fm and 'direct' in fm:
        return dict(form='F2', reason='sem_install_plus_caller',
                    anchor=_first(anch, 'CALL_REL'), evidence_kind=evk, band='B3')
    if 'install' in fm and DIRECT_ONLY.search(sem) and not LIVE_TABLE.search(sem):
        return dict(form='F3', reason='sem_own_install_plus_caller',
                    anchor=_first(anch, 'MOV_IMM'), evidence_kind=evk, band='B4')
    live = bool(LIVE_TABLE.search(sem) or VIRT_WITNESS.search(sem))
    if live and 'install' in fm:
        return dict(form='F1', reason='sem_live_table_install', anchor=_first(anch, 'MOV_IMM'),
                    evidence_kind=evk, band='B1')
    if VIRT_WITNESS.search(sem) or (VIRT_WITNESS_EN.search(sem) and
                                    re.search(r'0\s*direct\s+callers|无直', sem)):
        return dict(form='F1', reason='sem_virtual_witness_only', anchor=sem[:120],
                    evidence_kind=evk, band='B1')
    if 'direct' in fm or DIRECT_ONLY.search(sem):
        return dict(form='F3', reason='sem_direct_only', anchor=_first(anch, 'CALL_REL') or sem[:120],
                    evidence_kind=evk, band='B4')

    # ---- 3) F4, with the F1-leaning band flagged (never asserted as F1) ----
    if NO_RING4.search(sem) or '名字已证，语义据名' in sem:
        return dict(form='F4', reason='name_only_no_ring4', anchor='', evidence_kind=evk, band='B5')
    if SLOT_ID.search(sem) and INSTALL_WORD.search(sem):
        return dict(form='F4', reason='slot_pivot_not_stated_as_ring4', anchor=sem[:120],
                    evidence_kind=evk, band='B2')
    if entry in trace:
        return dict(form='F4', reason='census_no_ring4', anchor='', evidence_kind=evk, band='B5')
    return dict(form='F4', reason='no_ring4_described', anchor='', evidence_kind=evk, band='B5')


def _first(anch, kind):
    for a in anch:
        if a['kind'] == kind:
            info = a['info']
            if kind == 'MOV_IMM':
                return '%08X mov [%s],0x%08X (vt=%s)' % (
                    a['va'], info['form'], info['imm'], info.get('vt'))
            if kind == 'CALL_VT':
                return '%08X %s disp=0x%X' % (a['va'], info['form'], info.get('disp', 0))
            if kind == 'CALL_REL':
                return '%08X call 0x%08X' % (a['va'], info['target'])
            return '%08X %s' % (a['va'], kind)
    return ''


def evidence_kind(row):
    hs = []
    for h in row['ev'].split(';'):
        h = h.split('#')[0]
        if 'classification_trace' in h:
            k = 'census_trace'
        elif re.search(r'NAMED_PUSH_AUDIT\d*/VERDICT\.md$', h):
            k = 'named_audit'
        elif re.search(r'_audit/VERDICT\.md$', h):
            k = 'audit_verdict'
        elif '/VERDICT.md' in h or '\\VERDICT' in h:
            k = 'verdict_md'
        elif 'delta.tsv' in h:
            k = 'delta'
        elif h.startswith('EVIDENCE/'):
            k = 'card_evidence'
        else:
            k = 'other'
        hs.append(k)
    hs = sorted(set(hs))
    return (hs[0] if len(hs) == 1 else '+'.join(hs)), hs, row['ev']


# ----------------------------------------------------------------------------- disclosure
def disclosure_mentions(entries):
    """entry -> list of disclosure locations naming it."""
    panel = open(PANEL, encoding='utf-8').read()
    common = open(COMMON, encoding='utf-8').read()
    # cut R14_COMMON §13.4 block (D-47) and §12.3 block for targeted search
    def block(text, start_pat, end_pat):
        m = re.search(start_pat, text)
        if not m:
            return ''
        rest = text[m.start():]
        m2 = re.search(end_pat, rest[10:])
        return rest[:10 + m2.start()] if m2 else rest
    b_c = block(common, r'### 13\.4 待裁项', r'\n### 13\.5')
    b_123 = block(common, r'### 12\.3 【§8\.6', r'\n### 12\.4')
    b_88 = block(common, r'#### 条 1 · D-39', r'\n#### 条 2')
    out = collections.defaultdict(list)
    for e in entries:
        if e in dict.fromkeys(HEX8.findall(panel) or []):
            pass
        if re.search(r'(?<![0-9A-Za-z])' + e + r'(?![0-9A-Za-z])', panel):
            out[e].append('PANEL.md')
        if re.search(r'(?<![0-9A-Za-z])' + e + r'(?![0-9A-Za-z])', b_c):
            out[e].append('R14_COMMON§13.4')
        if re.search(r'(?<![0-9A-Za-z])' + e + r'(?![0-9A-Za-z])', b_123):
            out[e].append('R14_COMMON§12.3')
        if re.search(r'(?<![0-9A-Za-z])' + e + r'(?![0-9A-Za-z])', b_88):
            out[e].append('R14_COMMON§8.8条1')
    return out


# --------------------------------------------------------------------- panel columns
SUB_RE = re.compile(r'::sub_[0-9A-Fa-f]+$')
BARE_SUB = re.compile(r'^sub_[0-9A-Fa-f]+$')


def is_named(name):
    n = name.strip()
    if not n:
        return False
    if SUB_RE.search(n) or BARE_SUB.match(n):
        return False
    return True


def panel(rows, atlas):
    agg = collections.defaultdict(lambda: dict(n=0, named=0, proved=0, strict=0))
    for r in rows:
        if r['entry'] not in atlas:
            continue
        k = r['subsystem']
        a = agg[k]
        a['n'] += 1
        if r['grade'] == '[已证]':
            a['proved'] += 1
            if is_named(r['name']):
                a['named'] += 1
            if '[未证]' not in r['sem']:
                a['strict'] += 1
        elif is_named(r['name']):
            # named column counts named rows regardless of grade
            pass
    # named counts all named rows (any grade) in atlas
    agg2 = collections.defaultdict(lambda: dict(n=0, named=0, proved=0, strict=0))
    for r in rows:
        if r['entry'] not in atlas:
            continue
        k = r['subsystem']
        a = agg2[k]
        a['n'] += 1
        if is_named(r['name']):
            a['named'] += 1
        if r['grade'] == '[已证]':
            a['proved'] += 1
            if '[未证]' not in r['sem']:
                a['strict'] += 1
    return agg2


def verdict(a):
    n = a['n']
    thr_named = math.ceil(0.9 * n)
    thr_p = math.ceil(0.5 * n)
    nominal = a['named'] >= thr_named and a['proved'] >= thr_p
    strict = a['named'] >= thr_named and a['strict'] >= thr_p
    return thr_named, thr_p, nominal, strict

if __name__ == '__main__':
    # 可复跑入口：分类 + 出表 + 达标算术（产物与 make_outputs.py 相同）
    import make_outputs
    ctx = make_outputs.main()
    print('proved rows            :', ctx['proved'])
    print('F1 / F2 / F3 / F4      :', ctx['cnt']['F1'], '/', ctx['cnt']['F2'],
          '/', ctx['cnt']['F3'], '/', ctx['cnt']['F4'])
    print('bands (B1..B5)         :', dict(ctx['band']))
    print('F1 by subsystem        :', dict(ctx['f1_by_sub']))
    print('nominal (D-43A/12.3)   : %d/22 -> %d/22' % (ctx['before'][0], ctx['after123'][0]))
    print('strict  (D-43A/12.3)   : %d/22 -> %d/22' % (ctx['before'][1], ctx['after123'][1]))
    print('wrote surface.tsv / distribution.tsv / REPORT.md / work/*')
