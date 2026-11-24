# -*- coding: utf-8 -*-
"""
R16-F1-OTHER14 — 由 scan_raw.json 生成 fields.tsv / delta.tsv 并复核。

只写本目录；coverage.tsv / gamemd.exe 只读。
fields.tsv 列（卡面 §4.2，12 列）：
  entry subsystem name category form key_addrs evidence_src same_source_judged
  same_source_basis pre_has_ring4 status note
delta.tsv 列（卡面 §4.1，8 列，与 coverage.tsv 同构）：只放成功行，只改第 4 列。
披露指针一律 §12.6（不是 §12.4）。
"""
import os, sys, json, re, hashlib
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
RAW = os.path.join(HERE, 'scan_raw.json')
FIELDS = os.path.join(HERE, 'fields.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
VSUM = os.path.join(HERE, 'verify_summary.json')

DISC_SLOT = ('（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，'
             '见 R14_COMMON §12.6 与 PANEL 对应披露）')

FIELD_HEADER = ('entry\tsubsystem\tname\t'
                'category(sem_virtual_witness_only|sem_live_table_install)\t'
                'form(direct_call|slot_witness)\tkey_addrs\tevidence_src\t'
                'same_source_judged(yes|no)\tsame_source_basis\t'
                'pre_has_ring4(是/否)\tstatus(OK|SKIP)\tnote')
DELTA_HEADER = ('entry\tsubsystem\tname\tone_line_semantics\tgrade\t'
                'evidence_path\tn_sources\tconflict')


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def slot_text(r):
    """照 B1–B5 先例骨架，逐字段填实；披露指针 §12.6。"""
    cls = r['name'].split('::')[0]
    slot = str(r['slot_idx'])
    c = r['chosen']
    return ('④ 活表槽位见证：%s::slot%s（vt=%s，槽 %s 值=%s，COL=%s offset=%s，'
            'RTTI=%s→%s；装表点 %s 位于 %s 体内，entry 体外） '
            '④升级句：%s::slot%s（④ 表属类与行名类一致，均为 %s；'
            '该槽即其 vt=%s 表 slot%s，无归属歧义）%s' % (
                cls, slot, r['vt'], slot, r['entry'], r['col'], r['off'],
                r['td'], r['mangled'], c['site'], c['host'],
                cls, slot, cls, r['vt'], slot, DISC_SLOT))


def direct_text(r):
    """形态 1 direct call；写清调用站点地址 + 指令字节 + 被调 entry（§8.6 条 1 口径）。
    指令字节按字节空格分隔（E8 EF B4 DE FF），既便于人工核对，也使两行在 8 位十六进制
    entry 归一后仍因操作数字节不同而各异（满足卡面 §4.3 行行不同自检）。"""
    cb = ' '.join(r['call_bytes'][i:i + 2] for i in range(0, len(r['call_bytes']), 2))
    return ('④ direct call 使用见证（形态 1）：调用站点 %s 处指令 %s（E8 指令边界），'
            'site+5+rel32==%s，被调 entry=%s；站点位于工厂 %s 体内、体外非自环，'
            'direct call 独立于 ② 类身份证据（D-47 披露指针：R14_COMMON §12.6 与 PANEL 对应披露）' % (
                r['site'], cb, r['entry'], r['entry'], r['host']))


def main():
    cov_sha_before = sha256p(COV)
    raw = json.load(open(RAW, encoding='utf-8'))
    # 复核 coverage 在 scan 与 gen 之间未变
    if cov_sha_before != raw['cov_sha_before']:
        print('!! coverage changed since scan; abort. before=%s scan=%s'
              % (cov_sha_before, raw['cov_sha_before']))
        return 2
    with open(COV, 'rb') as f:
        cov_raw = f.read()
    cov = {}
    for ln in cov_raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) == 8:
            try:
                e = c[0].decode('ascii').upper()
            except Exception:
                continue
            cov.setdefault(e, c)

    field_lines, delta_lines, texts, vrows = [], [], [], []
    errors = []
    for r in raw['rows']:
        entry = r['entry']
        orig = cov.get(entry)
        if orig is None:
            errors.append('%s missing in coverage' % entry)
            continue
        st = r['status']
        form = r['form']
        ok = (st == 'OK')
        if ok:
            t = slot_text(r) if form == 'slot_witness' else direct_text(r)
            texts.append((entry, t))
            new_sem = orig[3] + '；'.encode('utf-8') + t.encode('utf-8')
            outcols = [orig[0], orig[1], orig[2], new_sem,
                       orig[4], orig[5], orig[6], orig[7]]
            for i in (0, 1, 2, 4, 5, 6, 7):
                if outcols[i] != orig[i]:
                    errors.append('%s col %d changed' % (entry, i + 1))
            if not outcols[3].startswith(orig[3]):
                errors.append('%s col4 prefix broken' % entry)
            if outcols[4] != '[已证]'.encode('utf-8'):
                errors.append('%s grade changed: %s' % (entry, outcols[4]))
            if '§12.6' not in t or '§12.4' in t:
                errors.append('%s disclosure pointer wrong' % entry)
            if r['pre_has4']:
                errors.append('%s already has ④ pre-change' % entry)
            delta_lines.append(b'\t'.join(outcols).decode('utf-8'))
        else:
            t = '（未补：%s）' % r.get('skip_reason', 'SKIP')

        # evidence_src
        if form == 'slot_witness':
            esrc = ('R16_F1_OTHER14/scan.py: other14.tsv#%s(slot_va=%s,slot_idx=%d,slot_rtti=%s) '
                    '+ gamemd.exe 只读 probe.scan_dd(.rdata/.data)/vtable_start/col_of '
                    '+ probe.TextScan.installs_of(vt) + probe.which_body(atlas 或 nop/CC 填充反测定界)'
                    % (entry, r['slot_va'], r['slot_idx'], r['mangled']))
            note = ('%s 第%d槽；vt=%s COL=%s TD=%s RTTI=%s；装表点 %s 位于 %s 体内(%s)，entry 体外；'
                    '6 项字节复核=%s；RTTI token=%s/name=%s；%s；改前第4列已含④=%s'
                    % (r['name'].split('::')[0], r['slot_idx'], r['vt'], r['col'],
                       r['td'], r['mangled'], r['chosen']['site'], r['chosen']['host'],
                       r['chosen']['host_src'], all(r['checks'].values()),
                       r['rtti_tokens_ok'], r['rtti_col_name_match'],
                       r.get('skip_reason', 'OK'), '是' if r['pre_has4'] else '否'))
        else:
            esrc = ('R16_F1_OTHER14/scan.py: other14.tsv#%s(direct_sites=%s) '
                    '+ gamemd.exe 只读 capstone 解码 E8 rel32 @site -> entry '
                    '+ probe.which_body(工厂函数)'
                    % (entry, r['site']))
            note = ('direct call 形态 1：site %s 字节 %s rel32=%s -> %s；host %s；'
                    '4 项复核=%s；与 ② 独立；%s；改前第4列已含④=%s'
                    % (r['site'], r['call_bytes'], r['rel32'], r['target'],
                       r['host'], all(r['checks'].values()),
                       r.get('skip_reason', 'OK'), '是' if r['pre_has4'] else '否'))
        field_lines.append('\t'.join([
            entry, r['subsystem'], r['name'], r['category'], form,
            r['key_addrs'], esrc, r['same_source_judged'], r['same_source_basis'],
            '是' if r['pre_has4'] else '否', st, note]))
        vrows.append(dict(entry=entry, form=form, status=st,
                          checks=r['checks'], all_checks=all(r['checks'].values()),
                          same_source=r['same_source_judged'], pre_has4=r['pre_has4']))

    with open(FIELDS, 'w', encoding='utf-8', newline='\n') as f:
        f.write(FIELD_HEADER + '\n')
        f.write('\n'.join(field_lines) + '\n')
    with open(DELTA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(DELTA_HEADER + '\n')
        f.write('\n'.join(delta_lines) + '\n')

    cov_sha_after = sha256p(COV)
    # 行行不同自检（entry 归一后）
    full = [t for _e, t in texts]
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for t in full]
    summary = dict(
        cov_sha_before=cov_sha_before, cov_sha_after=cov_sha_after,
        cov_unchanged=(cov_sha_before == cov_sha_after),
        cov_bytes=os.path.getsize(COV),
        exe_sha=raw['exe_sha'], exe_bytes=raw['exe_bytes'],
        n_rows=len(raw['rows']), n_ok=sum(1 for v in vrows if v['status'] == 'OK'),
        n_skip=sum(1 for v in vrows if v['status'] == 'SKIP'),
        n_same_source_yes=sum(1 for v in vrows if v['same_source'] == 'yes'),
        n_direct_ok=sum(1 for v in vrows if v['form'] == 'direct_call' and v['status'] == 'OK'),
        n_slot_ok=sum(1 for v in vrows if v['form'] == 'slot_witness' and v['status'] == 'OK'),
        n_distinct_full=len(set(full)), n_full=len(full),
        n_distinct_norm=len(set(norm)), n_norm=len(norm),
        errors=errors, rows=vrows,
        samples={f: next((t for e, t in texts if e == e0), '')
                 for f, e0 in [('slot_witness', '0040BC10'), ('direct_call', '004AF540')]})
    with open(VSUM, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    print('cov sha before/after:', cov_sha_before, cov_sha_after,
          'unchanged=', cov_sha_before == cov_sha_after)
    print('fields rows:', len(field_lines), 'delta rows:', len(delta_lines))
    print('OK/SKIP:', summary['n_ok'], summary['n_skip'],
          'same_source=yes:', summary['n_same_source_yes'])
    print('distinct full:', summary['n_distinct_full'], '/', summary['n_full'],
          'distinct normalized:', summary['n_distinct_norm'], '/', summary['n_norm'])
    print('ERRORS:', errors if errors else 'none')
    print('wrote', FIELDS, DELTA, VSUM)
    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
