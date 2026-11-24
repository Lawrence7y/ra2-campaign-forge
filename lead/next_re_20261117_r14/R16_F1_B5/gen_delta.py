# -*- coding: utf-8 -*-
"""
R16_F1_B5 — 生成 fields.tsv / delta.tsv / verify_summary.json（F1 缺口 B5 收官批，第 73-76 行）。

输入：scan_raw.json（只读取数）+ diag.json（site/func + 6 项字节复核）+ coverage.tsv（只读）
产物：只写本目录。只补第 4 列 ④ 成文：原文 + '；' + ④ 文本（原文严格前缀、一字不删）。
不改 grade / 不改判定 / 不并表。披露节号 §12.6（不是 §12.4）。

note 列逐行记下「改前第 4 列是否已含 ④」，供并表算净增。

复核（全部回 gamemd.exe 只读字节）：
  u32(vt + slot*4) == entry ; u32(vt-4) == col ; u32(col+4) == offset
  u32(col+12) == td ; cstr(td+8) == mangled ; 装表点 imm32 == vt
  rtti_class == row_class ; 装表点在 entry 体外
"""
import os
import sys
import json
import re
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
SCAN = os.path.join(HERE, 'scan_raw.json')
DIAG = os.path.join(HERE, 'diag.json')
FIELDS = os.path.join(HERE, 'fields.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
VERIFY = os.path.join(HERE, 'verify_summary.json')

DISC = ('（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，'
        '见 R14_COMMON §12.6 与 PANEL 对应披露）')
WITNESS = '④ 活表槽位见证'

# 每行区分依据（反抄袭 §4.2）：格式串，运行时用 diag 的真实数值 fill，避免手写任何十六进制。
NOTES = {
    '00763200': ('WaveClass 第8槽（标量删除析构体）；vt={vt}，COL={col}，TD={td}；'
                 'site {site} imm={vt}，宿主 {func}（atlas，ctor 内 0075E956 call 0x5F3900 '
                 '基类构造后装表，追加进全局 DynamicVector 容器，非 atexit、行外）；'
                 'RTTI {mg} 与行名类一致；ring4_at 明「本行 00763206 析构器内自装表按㉓排除」，'
                 'diag 选体外站点 {site}（不在 entry 体内）；本组唯一 WaveClass 行。'),
    '00763D90': ('WaypointPathClass 第6槽（流写出槽）；vt={vt}，COL={col}，TD={td}；'
                 'site {site} imm={vt}，宿主 {func}（atlas）；RTTI {mg} 与行名类一致；'
                 'ring4_at 给 0076375F/00763730 两 token，0076375F 命中装表且 imm==vt，'
                 '00763730 为宿主函数体起点，按 ring4_at 取 {site}；该表另有 007637E4/'
                 '00763845/007638C6/00763CA7/00763E26 装表点，本组唯一 WaypointPathClass 行。'),
    '00772CD0': ('WeaponTypeClass 第5槽（流读入 Load）；vt={vt}，COL={col}，TD={td}；'
                 'site {site} imm={vt}，宿主 {func}（atlas，ctor 00771C70 内装表）；'
                 'RTTI {mg} 与行名类一致；与 slot6 行(00772EB0)同表同 vt、同写点 {site}、'
                 '同宿主 {func}，仅以槽号 5/6 区分；该表另有 00771F28/00771F57/007730F7 '
                 '装表点，按 ring4_at 取 {site}。'),
    '00772EB0': ('WeaponTypeClass 第6槽（流写出 Save）；同表同 vt={vt}、site {site}、'
                 'func {func}、COL={col}；RTTI {mg} 与行名类一致；'
                 'ring4_at 明「与 slot5 同一写点」，与 slot5 行(00772CD0)仅以槽号 6/5 '
                 '区分（这两个 ④ 正文在归一 entry 后仍不同：槽号 6 vs 5）。'),
}


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_cov_bytes():
    with open(COV, 'rb') as f:
        raw = f.read()
    cov = {}
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) != 8:
            continue
        e = c[0].decode('ascii', 'ignore').strip().upper()
        if e:
            cov.setdefault(e, c)
    return cov


def fourth_text(ident, cls, slot, vt, col, off, td, mg, site, func, entry):
    """骨架同 B1/B2/B3/B4；ident = 行名 slotN。"""
    return ('④ 活表槽位见证：%s（vt=%s，槽 %s 值=%s，COL=%s offset=%s，'
            'RTTI=%s→%s；装表点 %s 位于 %s 体内，entry 体外） '
            '④升级句：%s（④ 表属类与行名类一致，均为 %s；'
            '该槽即其 vt=%s 表 slot%s，无归属歧义）%s' % (
                ident, vt, slot, entry, col, off, td, mg, site, func,
                ident, cls, vt, slot, DISC))


def main():
    cov_before = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
    exe_sha = sha256p(EXE)

    with open(SCAN, encoding='utf-8') as f:
        scan = json.load(f)
    with open(DIAG, encoding='utf-8') as f:
        diag = json.load(f)

    cov = load_cov_bytes()
    img = probe.Image(EXE)
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    field_header = ('entry\tclass\tslot_no\tvtaddr\tsource_of_vtaddr\tcoladdr\t'
                    'col_offset\trtti_addr\trtti_mangled\tinstall_site\t'
                    'install_func\tstatus(OK|SKIP)\tsame_source\tnote')
    delta_header = ('entry\tsubsystem\tname\tone_line_semantics\tgrade\t'
                    'evidence_path\tn_sources\tconflict')

    field_lines = []
    delta_lines = []
    texts = []
    verify = []
    bad = []

    for sr, dr in zip(scan['rows'], diag):
        entry = sr['entry']
        assert dr['entry'] == entry
        name = sr['name']
        cls = sr['name_cls']
        slot = str(dr['slot'])
        vt = dr['vt']
        col = dr['col']
        off = str(dr['off'])
        td = dr['td']
        mg = dr['mg']
        site = dr['site']
        func = dr['func'] or '未取得'
        same_source = sr['same_source']

        e_int = int(entry, 16)
        vt_int = int(vt, 16)
        col_int = int(col, 16)
        td_int = int(td, 16)
        site_int = int(site, 16)
        checks = {}
        checks['u32(vt+slot*4)==entry'] = img.u32(vt_int + int(slot) * 4) == e_int
        checks['u32(vt-4)==COL'] = img.u32(vt_int - 4) == col_int
        checks['u32(COL+4)==offset'] = img.u32(col_int + 4) == int(off)
        checks['u32(COL+12)==TD'] = img.u32(col_int + 12) == td_int
        checks['cstr(TD+8)==mangled'] = img.cstr(td_int + 8, 256) == mg
        code = bytes(img.buf[site_int - img.base:site_int - img.base + 12])
        ins = next(md.disasm(code, site_int))
        imm = (ins.operands[1].imm & 0xFFFFFFFF
               if ins.mnemonic == 'mov' and len(ins.operands) == 2
               and ins.operands[1].type == capstone.x86.X86_OP_IMM else None)
        checks['imm32@site==vt'] = imm == vt_int
        checks['rtti_class==row_class'] = probe.col_name_match(cls, mg) == 'match'
        checks['install_outside_entry_body'] = dr['outside'] and func != entry

        ok = all(checks.values())
        status = 'OK' if ok else 'SKIP'
        if not ok:
            bad.append((entry, [k for k, v in checks.items() if not v]))

        hit = ''
        for c in sr['candidates']:
            if c['vt'] == vt and c['slot'] == int(slot):
                hit = c['hit']
                break
        src_vt = ('R16_F1_B5/scan_fields.py: scan_dd(.rdata/.data) hit=%s -> '
                  'vtable_start -> vt=%s ; slot(name或从表解)=%s ; '
                  'site==ring4_at token %s (capstone imm32==vt) ; '
                  'atlas which_body=%s ; f_reason=%s ; '
                  'n_install_decoded=%s/out=%s/in=%s' % (
                      hit, vt, slot, site, func, sr['f_reason'],
                      sr['n_install_decoded'], sr['n_install_outside'],
                      sr['n_install_inside']))

        orig = cov.get(entry)
        if orig is None:
            raise RuntimeError('entry %s not found in coverage.tsv' % entry)
        orig_sem = orig[3].decode('utf-8', 'ignore')
        n_before = orig_sem.count('④')
        has4_before = '是' if n_before > 0 else '否'
        frags = []
        pos = 0
        while True:
            j = orig_sem.find('④', pos)
            if j < 0:
                break
            frags.append(orig_sem[j:j + 30])
            pos = j + 1
        pre4_marker = ('【改前第4列已含④=%s（④ 计数=%d%s）】' % (
            has4_before, n_before,
            ('；改前片段: ' + ' | '.join(frags[:2])) if frags else ''))

        note = NOTES[entry].format(
            vt=vt, col=col, td=td, site=site, func=func, mg=mg, cls=cls, slot=slot)
        note = note + '；' + pre4_marker

        field_lines.append('\t'.join([
            entry, cls, slot, vt, src_vt, col, off, td, mg, site, func,
            status, same_source, note]))
        verify.append(dict(entry=entry, status=status, checks=checks,
                           site=site, func=func, vt=vt, slot=int(slot),
                           pre4_n=n_before, pre4_has=(n_before > 0)))

        if not ok:
            continue

        ident = name
        t = fourth_text(ident, cls, slot, vt, col, off, td, mg, site, func, entry)
        texts.append((entry, t))
        assert WITNESS not in orig_sem, 'already has witness'
        new_sem = orig[3] + '；'.encode('utf-8') + t.encode('utf-8')
        outcols = [orig[0], orig[1], orig[2], new_sem,
                   orig[4], orig[5], orig[6], orig[7]]
        for i in (0, 1, 2, 4, 5, 6, 7):
            assert outcols[i] == orig[i], 'col %d changed for %s' % (i + 1, entry)
        assert outcols[3].startswith(orig[3]), 'col4 prefix not preserved'
        delta_lines.append(b'\t'.join(outcols).decode('utf-8'))

    with open(FIELDS, 'w', encoding='utf-8', newline='\n') as f:
        f.write(field_header + '\n')
        f.write('\n'.join(field_lines) + '\n')
    with open(DELTA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(delta_header + '\n')
        f.write('\n'.join(delta_lines) + '\n')

    cov_after = sha256p(COV)
    print('coverage.tsv bytes:', cov_bytes)
    print('coverage.tsv sha256 BEFORE:', cov_before)
    print('coverage.tsv sha256 AFTER :', cov_after)
    print('coverage unchanged:', cov_before == cov_after)
    print('gamemd.exe sha256:', exe_sha, '(card: 73201CC0...CF67476)')
    print('fields.tsv rows:', len(field_lines), 'delta.tsv rows:', len(delta_lines))
    print('SKIP rows:', bad)

    keys = ['u32(vt+slot*4)==entry', 'u32(vt-4)==COL', 'u32(COL+4)==offset',
            'u32(COL+12)==TD', 'cstr(TD+8)==mangled', 'imm32@site==vt',
            'rtti_class==row_class', 'install_outside_entry_body']
    print('byte-level verification:')
    for k in keys:
        print('  %-32s %d/%d True' % (k, sum(1 for v in verify if v['checks'][k]), len(verify)))

    full = [t for _e, t in texts]
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for _e, t in texts]
    print('uniqueness: distinct full %d/%d ; entry-normalized %d/%d' % (
        len(set(full)), len(full), len(set(norm)), len(norm)))

    vt_set = set(); cls_set = set(); site_set = set(); slot_set = set()
    for v in verify:
        vt_set.add(v['vt']); slot_set.add(str(v['slot'])); site_set.add(v['site'])
    for sr in scan['rows']:
        cls_set.add(sr['name_cls'])
    print('diversity: vt=%d slot=%d cls=%d site=%d' % (
        len(vt_set), len(slot_set), len(cls_set), len(site_set)))
    print('pre-existing ④ rows:', [(v['entry'], v['pre4_n']) for v in verify if v['pre4_has']])

    with open(VERIFY, 'w', encoding='utf-8') as f:
        json.dump(dict(cov_before=cov_before, cov_after=cov_after,
                       cov_bytes=cov_bytes, exe_sha=exe_sha,
                       n_fields=len(field_lines), n_delta=len(delta_lines),
                       verify=verify, bad=bad, keys=keys,
                       key_pass={k: sum(1 for v in verify if v['checks'][k]) for k in keys},
                       n_distinct_full=len(set(full)),
                       n_distinct_norm=len(set(norm)),
                       n_distinct_vt=len(vt_set), n_distinct_slot=len(slot_set),
                       n_distinct_cls=len(cls_set), n_distinct_site=len(site_set),
                       sample=(texts[0][1] if texts else '')),
                   f, ensure_ascii=False, indent=1)
    print('wrote', FIELDS, DELTA, VERIFY)
    return 0


if __name__ == '__main__':
    sys.exit(main())
