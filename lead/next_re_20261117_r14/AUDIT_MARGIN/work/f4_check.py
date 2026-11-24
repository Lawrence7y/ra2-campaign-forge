# -*- coding: utf-8 -*-
"""AUDIT-MARGIN F4: byte-level ③b recheck on a sample of [已证] rows,
with positive and negative controls. Read-only against gamemd.exe.

Emits EVIDENCE/<entry>__<safe_name>.txt = full disassembly + feature block,
and work/f4_facts.tsv = the machine-measured facts one line per sampled row.
Adjudication (whether the semantic's ③b claim holds) is recorded separately by hand
in FRAGILE_ROWS.tsv -- the script only reports what the bytes say.
"""
import sys, os, re, csv

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import disasm_lib as D
import frag_scan as F

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
EV = os.path.join(R14, "AUDIT_MARGIN", "EVIDENCE")
WORK = os.path.join(R14, "AUDIT_MARGIN", "work")
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

# (entry, why sampled)
SAMPLE = [
    # --- group A: S15 rows whose semantics claims "跳表薄壳唯一call直指"
    ('006E01C0', 'A shell-claim: TActionClass::WakeupSelf'),
    ('006E1980', 'A shell-claim: TActionClass::StopSounds'),
    ('006E2050', 'A shell-claim: TActionClass::DestroyAttachedObject'),
    ('006E2EB0', 'A shell-claim: TActionClass::RetintGreen'),
    ('00720B20', 'A shell-claim: TActionClass::PlayMusicTheme'),
    ('00726900', 'A shell-claim: TActionClass::DisableTrigger'),
    # --- group B: S15 rows whose semantics claims a real traversal (③b4 loop)
    ('006E2A10', 'B loop-claim: TActionClass::DeleteTrigger 遍历全局触发器表'),
    ('006E2AA0', 'B loop-claim: TActionClass::ForceTrigger 遍历全局触发器表'),
    # --- group C: the two rows the card names as known-fragile CONTROLS
    ('004E2690', 'C control: S09 [已证] slot27, ③b anchors cited in semantics'),
    ('0045A640', 'C control: S08 [静态推断] slot1 (card calls it ③b-invalid)'),
    # --- group D: S16 / S17 [已证] rows of the name-derived kind (F3a)
    ('006CB560', 'D S16 [已证] SuperClass::Grant'),
    ('0071AF20', 'D S16 [已证] TemporalClass::Fire'),
    ('006CF240', 'D S17 [已证] Here_I_Am (the single S17 F3a row)'),
    # --- group E: negative controls that must NOT show a ③b contract
    ('006CDEB0', 'E neg-control: S16 [静态推断] SuperClass::slot3'),
    ('006CDFD0', 'E F2 row: S16 [已证] SuperClass::Save (docs/re 2nd channel)'),
    ('006CE220', 'E F2 row: S16 [已证] ~SuperClass (docs/re 2nd channel)'),
]


def load_atlas():
    a = {}
    with open(ATLAS, 'r', encoding='utf-8', newline='') as f:
        rd = csv.reader(f, delimiter='\t')
        next(rd)
        for r in rd:
            if len(r) >= 2 and r[0]:
                try:
                    a[r[0].strip().upper()] = int(r[1])
                except ValueError:
                    pass
    return a


def safe(s):
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', s)[:60]


def main():
    atlas = load_atlas()
    pe = D.PE()
    rows = F.load()
    byentry = {r['entry']: r for r in rows}
    facts = []
    for entry, why in SAMPLE:
        r = byentry.get(entry)
        size = atlas.get(entry)
        if r is None or size is None:
            print('SKIP %s (%s)' % (entry, why))
            continue
        ins = D.disasm(pe, int(entry, 16), size)
        f = D.features(ins, int(entry, 16), size)
        name = r['name']
        path = os.path.join(EV, '%s__%s.txt' % (entry, safe(name)))
        with open(path, 'w', encoding='utf-8') as g:
            g.write('entry      : %s\n' % entry)
            g.write('subsystem  : %s\n' % r['subsystem'])
            g.write('name       : %s\n' % name)
            g.write('grade      : %s\n' % r['grade'])
            g.write('atlas_size : 0x%X (%d bytes)\n' % (size, size))
            g.write('semantics  : %s\n' % r['sem'])
            g.write('evidence   : %s\n' % r['ev'])
            g.write('sample_note: %s\n' % why)
            g.write('exe        : gamemd.exe SHA-256 73201CC0..F67476 (verified)\n')
            g.write('\n--- measured features ---\n%s\n' % D.fmt_feat(f))
            g.write('direct_calls      : %s\n' % ', '.join('0x%08X' % c for c in f['calls']))
            g.write('indirect_calls    : %s\n' % ', '.join('0x%08X' % c for c in f['indirect_calls']))
            g.write('back_jumps(loop?) : %s\n' % ', '.join('0x%08X %s->0x%08X' % t for t in f['back_jumps']))
            g.write('non_stack_writes  : %s\n' % ', '.join('0x%08X %s [%s+%s+0x%X]'
                    % (a, m, b, i, (d if d >= 0 else -d)) for (a, m, b, i, d) in f['nonspace_writes']))
            g.write('\n--- disassembly ---\n')
            g.write(D.text(ins))
            g.write('\n')
        facts.append(dict(entry=entry, subsystem=r['subsystem'], name=name, grade=r['grade'],
                          size=size, n_instr=f['n'], rets=f['rets'], calls=len(f['calls']),
                          indirect=len(f['indirect_calls']), cond=f['cond_branches'],
                          back=len(f['back_jumps']), jt=f['jump_table'],
                          memw=len(f['mem_writes']), stackw=f['stack_writes'],
                          nonspacew=len(f['nonspace_writes']), neg1=len(f['neg1_returns']),
                          why=why, file=os.path.relpath(path, os.path.join(R14, 'AUDIT_MARGIN'))))
        print('%-9s %-4s %-46s size=%-5d n=%-4d calls=%d ind=%d cond=%-3d back=%d jt=%-5s '
              'memw=%d stackw=%d nonspacew=%d neg1=%d'
              % (entry, r['subsystem'], name[:46], size, f['n'], len(f['calls']),
                 len(f['indirect_calls']), f['cond_branches'], len(f['back_jumps']),
                 f['jump_table'], len(f['mem_writes']), f['stack_writes'],
                 len(f['nonspace_writes']), len(f['neg1_returns'])))

    with open(os.path.join(WORK, 'f4_facts.tsv'), 'w', encoding='utf-8', newline='') as g:
        cols = list(facts[0].keys())
        g.write('\t'.join(cols) + '\n')
        for x in facts:
            g.write('\t'.join(str(x[k]) for k in cols) + '\n')
    print('\nsampled=%d  EVIDENCE files written to %s' % (len(facts), EV))


if __name__ == '__main__':
    main()
