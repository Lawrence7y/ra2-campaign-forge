# -*- coding: utf-8 -*-
"""
R16_SLOTN_B3 — 字段独立复核 + 生成 fields.tsv / delta.tsv（批次 3，数据行 31..43）。

与 R16_SLOTN_B1/B2 同规格；只改本批行、NOTE、FUNC_OVERRIDE 与两处
「表属类与行名类一致」选表覆写（数据行 32/33 / entry 005B3570/005B35E0）。
披露指针节号改为 §12.6（D-47(A) 重号后）。

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

# §12.6（重号后；不是 §12.4）
DISC = ('（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，'
        '见 R14_COMMON §12.6 与 PANEL 对应披露）')

# atlas 缺装表点宿主函数的行 —— 用 capstone 反汇编定界（只读）。
# 006AF120=xor eax,eax / push 0x6AF160 → 006AF13D=install imm=007F315C → 006AF15C=ret
# 006B6C10=xor eax,eax / push 0x6B6C50 → 006B6C2D=install imm=007F35E4 → 006B6C4C=ret
FUNC_OVERRIDE = {
    '006B1850': '006AF120', '006B1900': '006AF120',
    '006B8660': '006B6C10', '006B8710': '006B6C10',
}

# 「表属类与行名类一致」覆写（§3.1）：
# 005B3570/005B35E0（InfantryClass::slot123/122）的 work_scan.site_of=0043B71F
# 只命中 BuildingClass 表（007E3EBC，TD+8=.?AVBuildingClass@@），与行名类 InfantryClass
# 冲突。该 entry 实际被 7 张表同槽持有，其中 InfantryClass 表 vt=007EB058
# （COL=008033B8, TD=00825508, TD+8=.?AVInfantryClass@@）才是类一致表。
# 取该表自己的装表点：00517D9D（imm=007EB058, func 00517D90）/ 00521A11（imm=007EB058,
# func 00521960），均位于 entry 体外。两行取不同装表点以增强行行不同性。
CLASS_FIX = {
    '005B3570': dict(mangled='.?AVInfantryClass@@', site='00517D9D',
                     func='00517D90', ws='0043B71F'),
    '005B35E0': dict(mangled='.?AVInfantryClass@@', site='00521A11',
                     func='00521960', ws='0043B71F'),
}

NOTES = {
    '005B3060': 'MissionClass 第 23 槽；vt=007EDCC0，COL=00805D28；site 005B2DE9 反汇编 imm=007EDCC0，宿主 005B2DA0（atlas 命中）；2 表同槽（另 RadioClass 007F0508），按 site+行名类一致取 MissionClass',
    '005B3570': ('InfantryClass 第 123 槽；该 entry 被 7 张表同槽持有，work_scan.site_of=0043B71F '
                 '落在 BuildingClass 表（RTTI 与行名类冲突），按「表属类与行名类一致」改取 InfantryClass 表 '
                 'vt=007EB058（TD+8=.?AVInfantryClass@@），装表点改取该表自己的 00517D9D（imm=007EB058，func 00517D90）'),
    '005B35E0': ('InfantryClass 第 122 槽；同为 7 表同槽，site_of=0043B71F(BuildingClass) 弃用，'
                 '按类一致改取 InfantryClass 表 vt=007EB058，装表点取该表自己的 00521A11'
                 '（imm=007EB058，func 00521960，atlas 命中）——与 123 槽行取不同装表点'),
    '005B3650': 'MissionClass 第 125 槽；vt=007EDCC0；site 005B2DE9 宿主 005B2DA0（atlas）；与 slot23 同表但槽号相异；2 表同槽按行名类取 MissionClass',
    '005B36B0': 'MissionClass 第 126 槽；vt=007EDCC0；site 005B2DE9 宿主 005B2DA0（atlas）；与第 125 槽相邻而不同；2 表同槽按行名类取 MissionClass',
    '005B4630': 'MixFileClass 第 0 槽；vt=007EDF50（表起点即 dd 命中点，slot0）；site 005B3C52 宿主 005B3C20（atlas）；该 vt 另有 005B3F59/005B4639 两装表点',
    '00653100': 'RadarClass 第 16 槽；vt=007F0344，COL=008083C0；site 00652B45 宿主 00652960（atlas）；reason 记 1 处 direct（本卡纪律不计）',
    '0065CBF0': 'RawFileClass 第 5 槽；vt=007F0904，COL=00808790；site 0065CA03 宿主 0065CA00（atlas）；该 vt 另有 0065CAA8/0065D3A3/006C77C7 三装表点；reason 记 12 处 direct（不计）',
    '006B1850': 'SlaveManagerClass 动态向量模板例化 slot2；vt=007F315C，COL=00809620；site 006AF13D 装静态 vptr [0xB0B5F0]，宿主 006AF120 由 capstone 定界（atlas 缺，xor eax,eax prologue→ret 006AF15C）',
    '006B1900': 'SlaveManagerClass 动态向量模板例化 slot4；同 vt=007F315C 的第 4 槽；site 006AF13D 宿主 006AF120（capstone 定界）；与同表 slot2 相异',
    '006B8660': 'SpawnManagerClass 动态向量模板例化 slot2；vt=007F35E4，COL=00809A08；site 006B6C2D 装静态 vptr [0xB0B880]，宿主 006B6C10 由 capstone 定界（atlas 缺，xor eax,eax prologue→ret 006B6C4C）',
    '006B8710': 'SpawnManagerClass 动态向量模板例化 slot4；同 vt=007F35E4 的第 4 槽；site 006B6C2D 宿主 006B6C10（capstone 定界）；与同表 slot2 相异',
    '006F9E50': 'TechnoClass 第 23 槽；vt=007F4960，COL=0080C058；site 006F3130 宿主 006F2B40（atlas）；该 vt 另有 006F4413/006F450D 两装表点；reason 记 2 处 direct（不计）',
}


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    cov_before = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
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

        # 类一致覆写（行 32/33）：chosen 落在类不符的 BuildingClass 表，改选类一致的 InfantryClass 表
        if entry in CLASS_FIX:
            fx = CLASS_FIX[entry]
            fixed = None
            for c in r['candidates']:
                if c.get('mangled') == fx['mangled'] and c.get('slot') == int(slot):
                    fixed = c
                    break
            if fixed is not None:
                ch = fixed
                site = fx['site']
                func = FUNC_OVERRIDE.get(entry) or fx['func']
                override_note = (' ; CLASS_FIX: site_of=%s(BuildingClass) 弃用, '
                                 '改取类一致表 vt=%s / site=%s / func=%s' % (
                                     fx['ws'], ch['vt'], site, func))
            else:
                ch = None  # 类一致表没找到则整行 SKIP，绝不编造

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

        ws_site_show = (CLASS_FIX[entry]['ws'] if entry in CLASS_FIX else (site if entry not in FUNC_OVERRIDE else r['site']))
        src_vt = ('R16_SLOTN_B3/scan_fields.py: scan_dd(.rdata/.data) hit=%s -> '
                  'probe.vtable_start() -> vt=%s ; slot==slotN43.tsv#%d=%s ; '
                  'site==work_scan.json:A_agg.site_of[%s]=%s%s' % (
                      ch['hit'] if ch else 'NA', vt, r['row'], slot, entry,
                      ws_site_show, override_note))
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
    print('coverage.tsv bytes:', cov_bytes)
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
        if entry in CLASS_FIX:
            site_set.add(CLASS_FIX[entry]['site']); cls_set.add(r['name'].split('::')[0])
            slot_set.add(r['slot_no']); vt_set.add('007EB058'); continue
        if ch:
            vt_set.add(ch['vt']); slot_set.add(r['slot_no'])
            cls_set.add(r['name'].split('::')[0]); site_set.add(r['site'])
    print('  distinct vt:', len(vt_set), ' slot:', len(slot_set),
          ' class:', len(cls_set), ' site:', len(site_set))

    with open(os.path.join(HERE, 'verify_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(cov_before=cov_before, cov_after=cov_after, cov_bytes=cov_bytes,
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
