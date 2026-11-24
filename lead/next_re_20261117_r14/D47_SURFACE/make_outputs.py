# -*- coding: utf-8 -*-
"""D47-SURFACE producer: runs classification, writes surface.tsv / distribution.tsv / REPORT.md."""

import io, os, re, sys, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import surface as S  # noqa: E402

WORK = os.path.join(HERE, 'work')
SUBS = ['S%02d' % i for i in range(1, 23)]


def main():
    rows = S.load_coverage()
    atlas = S.load_atlas()
    audit = S.load_audit_records()
    trace = S.load_census_trace()

    proved = [r for r in rows if r['grade'] == S.GRADE_PROVED]
    recs = [(r, S.classify(r, audit, trace)) for r in proved]

    # ---------- distributions ----------
    form_of = {r['entry']: d['form'] for r, d in recs}
    band_of = {r['entry']: d['band'] for r, d in recs}
    reason_of = {r['entry']: d['reason'] for r, d in recs}
    anchor_of = {r['entry']: d['anchor'] for r, d in recs}
    in_atlas = {r['entry']: (r['entry'] in atlas) for r in rows}
    strict_of = {r['entry']: ('[未证]' not in r['sem']) for r in rows}

    cnt = collections.Counter(form_of.values())
    band = collections.Counter(band_of.values())
    rcnt = collections.Counter(reason_of.values())

    # ---------- disclosure mentions ----------
    f1_entries = [r['entry'] for r, d in recs if d['form'] == 'F1']
    disc = S.disclosure_mentions(f1_entries)

    # ---------- surface.tsv (F1 only) ----------
    def enrich(entry, d):
        """Append the decoded byte form of every anchor, so each row is checkable at a
        glance instead of carrying a bare address.  When no install instruction decodes,
        say what the address actually is (never let a bare VA pass as an install)."""
        txt = d['anchor'] or ''
        if entry in audit:
            txt = audit[entry][1].get('ring4_at', '') or txt
        anch = S.anchors_in(txt, entry)
        dec = []
        for a in anch:
            if a['kind'] == 'MOV_IMM' and a['info'].get('vt'):
                dec.append('%08X %s=0x%08X' % (a['va'], a['info']['form'], a['info']['imm']))
        if dec:
            return txt, '解码: ' + '; '.join(dec)
        # no install decoded -> describe the anchors honestly
        kinds = []
        for a in anch:
            if a['kind'] == 'CALL_REL':
                kinds.append('%08X call 0x%08X' % (a['va'], a['info']['target']))
            elif a['kind'] == 'CALL_VT':
                kinds.append('%08X call [reg+0x%X]' % (a['va'], a['info'].get('disp', 0)))
            elif a['kind'] == 'MOV_IMM':
                kinds.append('%08X mov imm=0x%08X' % (a['va'], a['info']['imm']))
        if kinds:
            return txt, '解码: ' + '; '.join(kinds) + ' （非装表指令；装表地址见 reason/语义栏）'
        return txt, '无地址锚（语义见证：见 ring4_anchor 原文）'

    with io.open(os.path.join(HERE, 'surface.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('entry\tsubsystem\tgrade\tf_form\tring4_anchor\tnamed_in_disclosure\tevidence_path\n')
        for r, d in sorted(recs, key=lambda x: (x[0]['subsystem'], x[0]['entry'])):
            if d['form'] != 'F1':
                continue
            raw, note = enrich(r['entry'], d)
            anchor = (raw or '').replace('\t', ' ').replace('\n', ' ')
            anchor = '%s ‖ %s' % (anchor, note)
            f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                r['entry'], r['subsystem'], r['grade'], d['form'], anchor,
                ';'.join(disc.get(r['entry'], [])) or '-', r['ev']))

    # ---------- distribution.tsv ----------
    dist = collections.defaultdict(lambda: collections.Counter())
    proved_by_sub = collections.Counter()
    for r in proved:
        dist[r['subsystem']][form_of[r['entry']]] += 1
        proved_by_sub[r['subsystem']] += 1
    with io.open(os.path.join(HERE, 'distribution.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('subsystem\tF1\tF2\tF3\tF4\ttotal_proved\n')
        for s in SUBS:
            c = dist[s]
            f.write('%s\t%d\t%d\t%d\t%d\t%d\n' % (s, c['F1'], c['F2'], c['F3'], c['F4'],
                                                  proved_by_sub[s]))
        c = collections.Counter()
        for s in SUBS:
            for k, v in dist[s].items():
                c[k] += v
        f.write('TOTAL\t%d\t%d\t%d\t%d\t%d\n' % (c['F1'], c['F2'], c['F3'], c['F4'],
                                                  sum(proved_by_sub.values())))

    # ---------- step 3 / 4 arithmetic ----------
    # per-subsystem panel values
    base = S.panel(rows, atlas)

    def panel_after(form_filter=None):
        agg = collections.defaultdict(lambda: dict(n=0, named=0, proved=0, strict=0))
        for r in rows:
            if r['entry'] not in atlas:
                continue
            a = agg[r['subsystem']]
            a['n'] += 1
            if S.is_named(r['name']):
                a['named'] += 1
            if r['grade'] == S.GRADE_PROVED:
                if form_filter and form_filter(r['entry']):
                    continue
                a['proved'] += 1
                if '[未证]' not in r['sem']:
                    a['strict'] += 1
        return agg

    def summarize(agg, label):
        nm = st = 0
        lines = []
        for s in SUBS:
            a = agg[s]
            tn, tp, no, so = S.verdict(a)
            nm += no
            st += so
            lines.append((s, a, tn, tp, no, so))
        return nm, st, lines

    before = summarize(base, 'before')
    # §12.3 wins: every F1 row flips (loses ④)
    after123 = summarize(panel_after(lambda e: form_of.get(e) == 'F1'), '123')
    # D-43(A) wins: 0 rows flip
    afterA = before

    # ---------- work reports ----------
    with io.open(os.path.join(WORK, 'arithmetic.txt'), 'w', encoding='utf-8') as f:
        f.write('=== BEFORE (§12.3 not applied / D-43(A) standing)\n')
        f.write('nominal %d/22  strict %d/22\n' % (before[0], before[1]))
        for s, a, tn, tp, no, so in before[2]:
            f.write('%s n=%d named=%d(/thr %d) proved=%d strict=%d thr_p=%d nom=%s strict=%s\n'
                    % (s, a['n'], a['named'], tn, a['proved'], a['strict'], tp, no, so))
        f.write('\n=== AFTER (§12.3 wins: all F1 rows lose ring-4)\n')
        f.write('nominal %d/22  strict %d/22\n' % (after123[0], after123[1]))
        for s, a, tn, tp, no, so in after123[2]:
            f.write('%s n=%d named=%d(/thr %d) proved=%d strict=%d thr_p=%d nom=%s strict=%s\n'
                    % (s, a['n'], a['named'], tn, a['proved'], a['strict'], tp, no, so))

    # F1 per subsystem + sensitivity
    f1_by_sub = collections.Counter()
    f1_atlas = 0
    f1_strict = 0
    for r, d in recs:
        if d['form'] == 'F1':
            f1_by_sub[r['subsystem']] += 1
            if r['entry'] in atlas:
                f1_atlas += 1
            if '[未证]' not in r['sem']:
                f1_strict += 1

    with io.open(os.path.join(WORK, 'summary.json'), 'w', encoding='utf-8') as f:
        import json
        json.dump(dict(proved=len(proved), forms=dict(cnt), bands=dict(band),
                       reasons=dict(rcnt), f1_by_sub=dict(f1_by_sub),
                       f1_atlas=f1_atlas, f1_strict=f1_strict,
                       nominal_before=before[0], strict_before=before[1],
                       nominal_after=after123[0], strict_after=after123[1]),
                  f, ensure_ascii=False, indent=1)

    # hand over the numbers to the report writer
    ctx = dict(proved=len(proved), cnt=cnt, band=band, rcnt=rcnt,
               f1_by_sub=f1_by_sub, f1_atlas=f1_atlas, f1_strict=f1_strict,
               before=before, after123=after123,
               dist=dist, proved_by_sub=proved_by_sub,
               recs=recs, form_of=form_of, band_of=band_of, reason_of=reason_of,
               anchor_of=anchor_of, in_atlas=in_atlas, strict_of=strict_of,
               disc=disc, audit=audit)
    return ctx


if __name__ == '__main__':
    ctx = main()
    print('proved', ctx['proved'], 'forms', dict(ctx['cnt']), 'bands', dict(ctx['band']))
    print('nominal before/after', ctx['before'][0], ctx['after123'][0])
    print('strict  before/after', ctx['before'][1], ctx['after123'][1])
    print('F1 by sub', dict(ctx['f1_by_sub']))
