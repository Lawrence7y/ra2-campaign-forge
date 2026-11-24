# -*- coding: utf-8 -*-
"""
R16_SLOTN_B2 — 字段独立复核 + 生成 fields.tsv / delta.tsv（批次 2，数据行 16..30）。

与 R16_SLOTN_B1/gen_delta.py 同规格；只改本批行、NOTE、FUNC_OVERRIDE 与一个
多表行的类一致选表覆写（数据行 30 / entry 005B2FD0）。

复核（全部回 gamemd.exe 读字节，只读）：
  u32(vt + slot*4) == entry
  u32(vt-4) == col ; u32(col+4) == offset ; u32(col+12) == td ; cstr(td+8) == mangled
  装表点指令 imm32 == vt
  函数体包含装表点（atlas 缺则以 capstone 反汇编定界）

产物只写本目录。coverage.tsv 只读。
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
FIELDS = os.path.join(HERE, 'fields.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')

DISC = ('（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，'
        '见 R14_COMMON §12.4 与 PANEL 对应披露）')

# atlas 缺装表点宿主函数的行 —— 用 capstone 反汇编定界（只读）。
# 00539580=prologue / ... / 0053959D=install / 005395BC=ret（行 25）
# 0054FDC0=prologue / ... / 0054FDDD=install / 0054FDFC=ret（行 26/27）
# 005569A0=prologue / ... / 005569BD=install / 005569DC=ret（行 28/29）
FUNC_OVERRIDE = {
    '0053C6A0': '00539580',
    '005514B0': '0054FDC0', '00551560': '0054FDC0',
    '00557090': '005569A0', '00557140': '005569A0',
}

# 多表行的「表属类与行名类一致」覆写：
# 005B2FD0（InfantryClass::slot124）的 work_scan.site_of=0043B71F 只命中
# BuildingClass 表（007E3EBC，TD=.?AVBuildingClass@@），与行名类 InfantryClass
# 冲突（审计 C「表属类与行名类一致」要求 TD+8 名类==行名类）。
# 该 entry 实际被 7 张表同槽持有，其中 InfantryClass 表 vt=007EB058
# （COL=008033B8, TD=00825508, TD+8=.?AVInfantryClass@@）才是类一致表；
# 取该表自己的装表点 00517D9D（位于函数 00517D90 体内，imm32=007EB058）。
CLASS_FIX_ENTRY = '005B2FD0'
CLASS_FIX_MANGLED = '.?AVInfantryClass@@'
CLASS_FIX_SITE = '00517D9D'
CLASS_FIX_FUNC = '00517D90'

NOTES = {
    '004D4CB0': 'AircraftClass 第 134 槽；dd hit=007E24BC->vt=007E22A4，site 00413D87 命中；vt_count=4，按 site+类名一致取 AircraftClass 表',
    '004D4DC0': 'FootClass 第 132 槽；dd hit=007E8EA4->vt=007E8C94；site 004D345D 位于 004D31E0 体内（与 004DE630 先例同宿主）',
    '004D5070': 'FootClass 第 135 槽；同 vt=007E8C94；site 004D345D 反汇编对齐在 004D31E0 体内；与 slot132/138 邻槽相异',
    '004D5350': 'FootClass 第 138 槽；同 vt=007E8C94；site 004D345D 位于 004D31E0 体内；reason 记 2 处 direct（本卡纪律不计）',
    '004D6AA0': 'FootClass 第 136 槽；同 vt=007E8C94；site 004D345D 位于 004D31E0 体内；与第 138 槽相隔两格',
    '004D9290': 'FootClass 第 144 槽；vt_count=3，dd 命中 3 张表，按 site 004D345D + 行名类一致取 007E8C94；非独立链已披露',
    '004DA2C0': 'FootClass 第 140 槽；vt_count=3 同类同 vt 族，按 slot140 与 site 004D345D 定该槽；非独立链已披露',
    '004DDF90': 'AircraftClass 第 150 槽；vt_count=4，4 表共享该槽，按 site 00413D87 + 行名 AircraftClass 取 vt=007E22A4',
    '0051F3E0': 'InfantryClass 第 132 槽；vt=007EB058，COL=008033B8；site 00517ACC 位于构造体 00517A50 内；该表另有 00517D9D/00521A11 两装表点',
    '0053C6A0': 'PBVAnimClass 动态向量模板例化 slot2；dd hit=007EBFD4->vt=007EBFCC；site 0053959D 宿主 00539580 由 capstone 定界（atlas 缺）',
    '005514B0': 'PAVLaserDrawClass 模板例化 slot2；site 0054FDDD 宿主 0054FDC0 由反汇编定界（ret 0054FDFC）；该 vt 仅此一装表点',
    '00551560': 'PAVLaserDrawClass 模板例化 slot4；同 vt=007ECEDC 的第 4 槽；site 0054FDDD 宿主 0054FDC0；与同表 slot2 相异',
    '00557090': 'PAVLineTrail 模板例化 slot2；site 005569BD 宿主 005569A0 由反汇编定界（ret 005569DC）；atlas 未收该宿主',
    '00557140': 'PAVLineTrail 模板例化 slot4；同 vt=007ED0CC 的第 4 槽；site 005569BD 宿主 005569A0；与同表 slot2 相异',
    '005B2FD0': ('InfantryClass 第 124 槽；该 entry 被 7 张表同槽持有，work_scan.site_of=0043B71F 落在 '
                 'BuildingClass 表（RTTI 与行名类冲突），故按「表属类与行名类一致」改取 InfantryClass 表 '
                 'vt=007EB058（TD+8=.?AVInfantryClass@@），装表点改取该表自己的 00517D9D（imm32=007EB058）'),
}


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    cov_before = sha256p(COV)
    with open(SCAN, encoding='utf-8') as f:
        scan = json.load(f)
    img = probe.Image(EXE)

    # 读 coverage.tsv 原始字节，按行建 entry -> 原始 8 列（byte）
    with open(COV, 'rb') as f:
        raw = f.read()
    raw_lines = raw.split(b'\n')
    cov = {}
    for ln in raw_lines:
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) == 8:
            try:
                e = c[0].decode('ascii').upper()
            except Exception:
                continue
            cov.setdefault(e, c)

    def fourth_text(cls, slot, vt, col, off, td, mg, site, func, entry):
        return ('④ 活表槽位见证：%s::slot%s（vt=%s，槽 %s 值=%s，COL=%s offset=%s，'
                'RTTI=%s→%s；装表点 %s 位于 %s 体内，entry 体外） '
                '④升级句：%s::slot%s（④ 表属类与行名类一致，均为 %s；'
                '该槽即其 vt=%s 表 slot%s，无归属歧义）%s' % (
                    cls, slot, vt, slot, entry, col, off, td, mg, site, func,
                    cls, slot, cls, vt, slot, DISC))

    field_lines = []
    delta_lines = []
    verify = []
    texts = []
    field_header = ('entry\tclass\tslot_no\tvtaddr\tsource_of_vtaddr\tcoladdr\t'
                    'col_offset\trtti_addr\trtti_mangled\tinstall_site\t'
                    'install_func\tstatus(OK|SKIP)\tnote')
    delta_header = ('entry\tsubsystem\tname\tone_line_semantics\tgrade\t'
                    'evidence_path\tn_sources\tconflict')

    for r in scan['rows']:
        entry = r['entry']
        ch = r['chosen']
        cls = r['name'].split('::')[0]
        slot = r['slot_no']
        site = r['site']
        func = FUNC_OVERRIDE.get(entry) or r['func'] or '未取得'
        override_note = ''

        # 类一致覆写（行 30）：chosen 落在类不符的 BuildingClass 表，改选类一致的 InfantryClass 表
        if entry == CLASS_FIX_ENTRY:
            fixed = None
            for c in r['candidates']:
                if c.get('mangled') == CLASS_FIX_MANGLED and c.get('slot') == int(slot):
                    fixed = c
                    break
            if fixed is not None:
                ch = fixed
                site = CLASS_FIX_SITE
                func = FUNC_OVERRIDE.get(entry) or CLASS_FIX_FUNC
                override_note = (' ; CLASS_FIX: site_of=0043B71F(BuildingClass) 弃用, '
                                 '改取类一致表 vt=%s / site=%s / func=%s' % (ch['vt'], site, func))
            else:
                # 兜底：类一致表没找到则整行 SKIP，绝不编造
                ch = None

        ok = True
        checks = []
        if ch is None:
            ok = False
            checks.append('no-vt-candidate')
            vt = col = off = td = mg = '未取得'
        else:
            vt = ch['vt']; col = ch['col']; off = str(ch['col_offset'])
            td = ch['td']; mg = ch['mangled']
            # byte-level independent verification
            e_int = int(entry, 16); vt_int = int(vt, 16)
            slot_int = int(slot)
            v_slot = img.u32(vt_int + slot_int * 4)
            v_col = img.u32(vt_int - 4)
            v_off = img.u32(int(col, 16) + 4)
            v_td = img.u32(int(col, 16) + 12)
            v_mg = img.cstr(int(td, 16) + 8, 256)
            c1 = (v_slot == e_int); checks.append('u32(vt+slot*4)==entry:%s' % c1)
            c2 = (v_col == int(col, 16)); checks.append('u32(vt-4)==COL:%s' % c2)
            c3 = (v_off == int(off)); checks.append('u32(COL+4)==offset:%s' % c3)
            c4 = (v_td == int(td, 16)); checks.append('u32(COL+12)==TD:%s' % c4)
            c5 = (v_mg == mg); checks.append('cstr(TD+8)==mangled:%s' % c5)
            # install site imm32 == vt：capstone 解码
            import capstone
            site_int = int(site, 16)
            code = bytes(img.buf[site_int - img.base:site_int - img.base + 12])
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            md.detail = True
            ins = next(md.disasm(code, site_int))
            imm = (ins.operands[1].imm & 0xFFFFFFFF
                   if ins.mnemonic == 'mov' and len(ins.operands) == 2
                   and ins.operands[1].type == capstone.x86.X86_OP_IMM else None)
            c6 = (imm == vt_int); checks.append('imm32@site(decoded)==vt:%s' % c6)
            ok = all([c1, c2, c3, c4, c5, c6])

        # 额外一致性自检：RTTI 名类 == 行名类（审计 C）
        if ch is not None:
            cls_chk = probe.col_name_match(cls, mg)
            checks.append('rtti_class==row_class:%s' % (cls_chk == 'match'))
            if cls_chk != 'match':
                ok = False

        verify.append(dict(entry=entry, ok=ok, checks=checks))

        src_vt = ('R16_SLOTN_B2/scan_fields.py: scan_dd(.rdata/.data) hit=%s -> '
                  'probe.vtable_start() -> vt=%s ; slot==slotN43.tsv#%d=%s ; '
                  'site==work_scan.json:A_agg.site_of[%s]=%s%s' % (
                      ch['hit'] if ch else 'NA', vt, r['row'], slot, entry,
                      (site if entry != CLASS_FIX_ENTRY else '0043B71F'),
                      override_note))
        status = 'OK' if ok else 'SKIP'
        field_lines.append('\t'.join([
            entry, cls, slot, vt, src_vt, col, off, td, mg, site, func,
            status, NOTES[entry]]))

        if ok:
            t = fourth_text(cls, slot, vt, col, off, td, mg, site, func, entry)
            texts.append((entry, t))
            orig = cov.get(entry)
            if orig is None:
                raise RuntimeError('entry %s not found in coverage.tsv' % entry)
            # 原第 4 列一字不删，用 ；衔接
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
    print('coverage.tsv sha256 BEFORE:', cov_before)
    print('coverage.tsv sha256 AFTER :', cov_after)
    print('coverage unchanged:', cov_before == cov_after)
    print('fields.tsv rows:', len(field_lines), ' delta.tsv rows:', len(delta_lines))
    print('byte-level verification:')
    for v in verify:
        print(' ', v['entry'], 'OK' if v['ok'] else 'FAIL', '; '.join(v['checks']))

    # 行行不同自检
    print('uniqueness self-check:')
    print('  distinct full ④ texts:', len(set(t for _e, t in texts)), '/', len(texts))
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for _e, t in texts]
    print('  distinct texts with entry normalized to placeholder:', len(set(norm)), '/', len(norm))
    vt_set = set(); slot_set = set(); cls_set = set(); site_set = set()
    for r in scan['rows']:
        ch = r['chosen']
        entry = r['entry']
        if entry == CLASS_FIX_ENTRY:
            site_set.add(CLASS_FIX_SITE); cls_set.add(r['name'].split('::')[0])
            slot_set.add(r['slot_no']); vt_set.add('007EB058'); continue
        if ch:
            vt_set.add(ch['vt']); slot_set.add(r['slot_no'])
            cls_set.add(r['name'].split('::')[0]); site_set.add(r['site'])
    print('  distinct vt:', len(vt_set), ' slot:', len(slot_set),
          ' class:', len(cls_set), ' site:', len(site_set))

    with open(os.path.join(HERE, 'verify_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(cov_before=cov_before, cov_after=cov_after,
                       n_fields=len(field_lines), n_delta=len(delta_lines),
                       verify=verify,
                       n_distinct_full=len(set(t for _e, t in texts)),
                       n_distinct_norm=len(set(norm)),
                       n_distinct_vt=len(vt_set), n_distinct_slot=len(slot_set),
                       n_distinct_cls=len(cls_set), n_distinct_site=len(site_set),
                       sample=(texts[0][1] if texts else '')),
                   f, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
