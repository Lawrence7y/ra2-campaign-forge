# -*- coding: utf-8 -*-
"""
R16_F1_B3 — 生成 fields.tsv / delta.tsv / verify_summary.json（F1 缺口 B3，第 37-54 行）。

输入：scan_raw.json（只读取数）+ diag.json（site/func + 6 项字节复核）+ coverage.tsv（只读）
产物：只写本目录。只补第 4 列 ④ 成文：原文 + '；' + ④ 文本（原文严格前缀、一字不删）。
不改 grade / 不改判定 / 不并表。披露节号 §12.6（不是 §12.4）。

复核（全部回 gamemd.exe 只读字节）：
  u32(vt + slot*4) == entry
  u32(vt-4) == col ; u32(col+4) == offset ; u32(col+12) == td ; cstr(td+8) == mangled
  装表点 imm32 == vt（capstone 解码）
  rtti_class == row_class（probe.col_name_match）
  装表点在 entry 体外（atlas body 判定 + func != entry）
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

# 每行 note：用 vt/slot/site/func/RTTI 与同表/同族相邻行作区分依据（反抄袭）
NOTES = {
    '006C3890': ('T_TClassFactory_VInfantryClass__ 第3槽；vt=007F3C00，COL=0080ABB8，'
                 'TD=00841928；site 006C37C9 imm=007F3C00，宿主 006C37C0（atlas，ctor 入口+9）；'
                 'RTTI .?AV?$TClassFactory@VInfantryClass@@@@ 内 InfantryClass 与行名一致；'
                 '同族工厂行 vt/COL/site 各不相同，本行以 Infantry 类 + vt=007F3C00 区分'),
    '006C3A10': ('T_TClassFactory_VAnimClass__ 第3槽；vt=007F3C18，COL=0080AC08，TD=00841958；'
                 'site 006C3949 imm=007F3C18，宿主 006C3940（atlas，ctor 入口+9）；'
                 'RTTI .?AV?$TClassFactory@VAnimClass@@@@ 内 AnimClass 与行名一致；'
                 '与 Infantry 工厂行相邻但 vt=007F3C18/COL=0080AC08/site=006C3949 全异'),
    '006C3B90': ('T_TClassFactory_VAnimTypeClass__ 第3槽；vt=007F3C30，COL=0080AC58，TD=00841988；'
                 'site 006C3AC9 imm=007F3C30，宿主 006C3AC0（atlas，ctor 入口+9）；'
                 'RTTI .?AV?$TClassFactory@VAnimTypeClass@@@@ 内 AnimTypeClass 与行名一致；'
                 '与 Anim 工厂行同属 V 系列但 Anim/AnimType 类不同、vt 与 site 均异'),
    '006C5210': ('T_TClassFactory_VFactoryClass__ 第3槽；vt=007F3D98，COL=0080B108，TD=00841CB8；'
                 'site 006C5149 imm=007F3D98，宿主 006C5140（atlas）；'
                 'RTTI .?AV?$TClassFactory@VFactoryClass@@@@ 内 FactoryClass 与行名一致；'
                 'ring4_at=006C5149 纯装表点 token，无 ctor 散文；与 AUDIT11 三行以 vt/类/site 区分'),
    '006C5390': ('T_TClassFactory_VWarheadTypeClass__ 第3槽；vt=007F3DB0，COL=0080B158，TD=00841CE8；'
                 'site 006C52C9 imm=007F3DB0，宿主 006C52C0（atlas）；'
                 'RTTI .?AV?$TClassFactory@VWarheadTypeClass@@@@ 内 WarheadTypeClass 与行名一致；'
                 '与 Factory 工厂行同批 AUDIT12 但 vt=007F3DB0/site=006C52C9 不同'),
    '006C5510': ('T_TClassFactory_VWeaponTypeClass__ 第3槽；vt=007F3DC8，COL=0080B1A8，TD=00841D20；'
                 'site 006C5449 imm=007F3DC8，宿主 006C5440（atlas）；'
                 'RTTI .?AV?$TClassFactory@VWeaponTypeClass@@@@ 内 WeaponTypeClass 与行名一致；'
                 'vt/site/COL/RTTI 与同批 WarheadType 行逐一不同'),
    '006C5690': ('T_TClassFactory_VParticleClass__ 第3槽；vt=007F3DE0，COL=0080B1F8，TD=00841D58；'
                 'site 006C55C9 imm=007F3DE0，宿主 006C55C0（atlas）；'
                 'RTTI .?AV?$TClassFactory@VParticleClass@@@@ 内 ParticleClass 与行名一致；'
                 '与 ParticleType/ParticleSystem 工厂行靠 Particle 单类与 vt=007F3DE0 区分'),
    '006C5810': ('T_TClassFactory_VParticleTypeClass__ 第3槽；vt=007F3DF8，COL=0080B248，TD=00841D88；'
                 'site 006C5749 imm=007F3DF8，宿主 006C5740（atlas）；'
                 'RTTI .?AV?$TClassFactory@VParticleTypeClass@@@@ 内 ParticleTypeClass 与行名一致；'
                 '与 ParticleClass 工厂行仅差 Type 后缀但 vt/site/COL 全异'),
    '006C5990': ('T_TClassFactory_VParticleSystemClass__ 第3槽；vt=007F3E10，COL=0080B298，TD=00841DC0；'
                 'site 006C58C9 imm=007F3E10，宿主 006C58C0（atlas）；'
                 'RTTI .?AV?$TClassFactory@VParticleSystemClass@@@@ 内 ParticleSystemClass 与行名一致；'
                 '与 ParticleSystemType 行靠 System/SystemType 类与独立 vt 区分'),
    '006C5B10': ('T_TClassFactory_VParticleSystemTypeClass__ 第3槽；vt=007F3E28，COL=0080B2E8，TD=00841DF8；'
                 'site 006C5A49 imm=007F3E28，宿主 006C5A40（atlas）；'
                 'RTTI .?AV?$TClassFactory@VParticleSystemTypeClass@@@@ 内 ParticleSystemTypeClass 与行名一致；'
                 '同族最长类名，vt=007F3E28/site=006C5A49 唯一'),
    '006C5C90': ('T_TClassFactory_VAITriggerTypeClass__ 第3槽；vt=007F3E40，COL=0080B338，TD=00841E38；'
                 'site 006C5BC9 imm=007F3E40，宿主 006C5BC0（atlas）；'
                 'RTTI .?AV?$TClassFactory@VAITriggerTypeClass@@@@ 内 AITriggerTypeClass 与行名一致；'
                 '以 AI 触发器类 + vt=007F3E40 与其余工厂行区分'),
    '006C5E10': ('T_TClassFactory_VNeuronClass__ 第3槽；vt=007F3E58，COL=0080B388，TD=00841E70；'
                 'site 006C5D49 imm=007F3E58，宿主 006C5D40（atlas）；'
                 'RTTI .?AV?$TClassFactory@VNeuronClass@@@@ 内 NeuronClass 与行名一致；'
                 'Neural 类唯一，vt/site 与相邻 AI 触发器行不同'),
    '006C5F90': ('T_TClassFactory_VFoggedObjectClass__ 第3槽；vt=007F3E70，COL=0080B3D8，TD=00841EA0；'
                 'site 006C5EC9 imm=007F3E70，宿主 006C5EC0（atlas）；'
                 'RTTI .?AV?$TClassFactory@VFoggedObjectClass@@@@ 内 FoggedObjectClass 与行名一致；'
                 '以 FoggedObject 类 + vt=007F3E70 与 Neuron 行区分'),
    '006C6110': ('T_TClassFactory_VAlphaShapeClass__ 第3槽；vt=007F3E88，COL=0080B428，TD=00841ED8；'
                 'site 006C6049 imm=007F3E88，宿主 006C6040（atlas）；'
                 'RTTI .?AV?$TClassFactory@VAlphaShapeClass@@@@ 内 AlphaShapeClass 与行名一致；'
                 'AUDIT12 工厂行末行，vt=007F3E88/site=006C6049 唯一'),
    '006DBD20': ('Tactical::slot5；vt=007F4348，COL=0080B9A8，TD=00842A38；'
                 'site 006D1D54 imm=007F4348，宿主 006D1C20（atlas 真构造器）；'
                 'RTTI .?AVTactical@@ 与行名类一致；该表另有 006D1E58/006D1E80/006DC473 三处装表点，'
                 '本行按 ring4_at 取 006D1D54；与 slot6 行同表同站点、仅以槽号 5/6 区分'),
    '006DBE00': ('Tactical::slot6；同表同 vt=007F4348、site 006D1D54、func 006D1C20；'
                 'ring4_at 散文载 c7 06 48 43 7f 00 即该装表指令字节、5 调用方均 push 0xe18+new、'
                 '实例落全局 0x887324 被 .text 读 447 次=活表；与 slot5 行仅以槽号 6/5 区分'),
    '006E3E30': ('TActionClass::slot6；vt=007F443C，COL=0080BAF0，TD=00842B78；'
                 'site 006DD036 imm=007F443C，宿主 006DD000（atlas，ctor 前 call 00410170）；'
                 'RTTI .?AVTActionClass@@ 与行名类一致；该表另有 006DD18D/006DD1B6/006E3DD4/006E4666 '
                 '四处装表点，本行取 ring4_at 指定的 006DD036；与 Tactical 行以类+vt 区分'),
    '006E57A0': ('TagClass::slot6；vt=007F44E0，COL=0080BBA0，TD=008249E8；'
                 'site 006E4E07 imm=007F44E0，宿主 006E4DE0（atlas，ctor 前 call 00410170）；'
                 'RTTI .?AVTagClass@@ 与行名类一致；该表另有 006E4F69/006E5754 两处装表点，'
                 '本行取 ring4_at 指定的 006E4E07；与 TAction 行以类+vt+site 区分'),
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


def fourth_text(cls, slot, vt, col, off, td, mg, site, func, entry):
    return ('④ 活表槽位见证：%s::slot%s（vt=%s，槽 %s 值=%s，COL=%s offset=%s，'
            'RTTI=%s→%s；装表点 %s 位于 %s 体内，entry 体外） '
            '④升级句：%s::slot%s（④ 表属类与行名类一致，均为 %s；'
            '该槽即其 vt=%s 表 slot%s，无归属歧义）%s' % (
                cls, slot, vt, slot, entry, col, off, td, mg, site, func,
                cls, slot, cls, vt, slot, DISC))


def main():
    cov_before = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
    exe_sha = sha256p(EXE)

    with open(SCAN, encoding='utf-8') as f:
        scan = json.load(f)
    with open(DIAG, encoding='utf-8') as f:
        diag = json.load(f)
    diag_by = {d['entry']: d for d in diag}

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

        # ---- 6 项字节复核（本脚本独立再算一次，不复用 diag 结果）----
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

        # 找到该行候选的 dd hit（source_of_vtaddr 用）
        hit = ''
        for c in sr['candidates']:
            if c['vt'] == vt and c['slot'] == int(slot):
                hit = c['hit']
                break
        src_vt = ('R16_F1_B3/scan_fields.py: scan_dd(.rdata/.data) hit=%s -> '
                  'vtable_start -> vt=%s ; slot==name slot%s ; '
                  'site==ring4_at token %s (capstone imm32==vt) ; '
                  'atlas which_body=%s ; f_reason=%s ; '
                  'n_install_decoded=%s/out=%s/in=%s' % (
                      hit, vt, slot, site, func, sr['f_reason'],
                      sr['n_install_decoded'], sr['n_install_outside'],
                      sr['n_install_inside']))

        field_lines.append('\t'.join([
            entry, cls, slot, vt, src_vt, col, off, td, mg, site, func,
            status, same_source, NOTES[entry]]))
        verify.append(dict(entry=entry, status=status, checks=checks,
                           site=site, func=func, vt=vt, slot=int(slot)))

        if not ok:
            continue

        t = fourth_text(cls, slot, vt, col, off, td, mg, site, func, entry)
        texts.append((entry, t))
        orig = cov.get(entry)
        if orig is None:
            raise RuntimeError('entry %s not found in coverage.tsv' % entry)
        new_sem = orig[3] + '；'.encode('utf-8') + t.encode('utf-8')
        outcols = [orig[0], orig[1], orig[2], new_sem,
                   orig[4], orig[5], orig[6], orig[7]]
        for i in (0, 1, 2, 4, 5, 6, 7):
            assert outcols[i] == orig[i], 'col %d changed for %s' % (i + 1, entry)
        assert outcols[3].startswith(orig[3]), 'col4 prefix not preserved'
        assert WITNESS not in orig[3].decode('utf-8', 'ignore'), 'already has witness'
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

    # 6 项字节复核汇总（外加 rtti_class / outside 共 8 项）
    keys = ['u32(vt+slot*4)==entry', 'u32(vt-4)==COL', 'u32(COL+4)==offset',
            'u32(COL+12)==TD', 'cstr(TD+8)==mangled', 'imm32@site==vt',
            'rtti_class==row_class', 'install_outside_entry_body']
    print('byte-level verification:')
    for k in keys:
        print('  %-32s %d/%d True' % (k, sum(1 for v in verify if v['checks'][k]), len(verify)))

    # 行行不同自检
    full = [t for _e, t in texts]
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for _e, t in texts]
    print('uniqueness: distinct full %d/%d ; entry-normalized %d/%d' % (
        len(set(full)), len(full), len(set(norm)), len(norm)))

    vt_set = set(); slot_set = set(); cls_set = set(); site_set = set()
    for v in verify:
        vt_set.add(v['vt']); slot_set.add(str(v['slot'])); site_set.add(v['site'])
    for sr in scan['rows']:
        cls_set.add(sr['name_cls'])
    print('diversity: vt=%d slot=%d cls=%d site=%d' % (
        len(vt_set), len(slot_set), len(cls_set), len(site_set)))

    with open(VERIFY, 'w', encoding='utf-8') as f:
        json.dump(dict(cov_before=cov_before, cov_after=cov_after,
                       cov_bytes=cov_bytes, exe_sha=exe_sha,
                       n_fields=len(field_lines), n_delta=len(delta_lines),
                       verify=verify, bad=bad,
                       keys=keys,
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
