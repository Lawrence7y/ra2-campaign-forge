# -*- coding: utf-8 -*-
"""
R16_F1_B2 — 生成 fields.tsv / delta.tsv / verify_summary.json（F1 缺口 B2，第 19-36 行）。

输入：scan_raw.json（只读取数）+ diag.json（ site/func + 6 项字节复核）+ coverage.tsv（只读）
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

# 每行 note：用 vt/slot/site/func 与同表相邻行作区分依据（反抄袭）
NOTES = {
    '005FEAF0': 'OverlayTypeClass 第5槽；vt=007EF600，COL=008076F0；site 005FE2F1 imm=007EF600，宿主 005FE250（atlas，与 ring4_at in_func 一致）；该 vt 另有 005FE3CD/005FE3F6/005FEB21/005FEF36 四处装表点，本行取 ring4_at 指定的 005FE2F1',
    '00629FD0': 'ParasiteClass 第23槽；vt=007EF890，COL=00807B30；site 00629231 imm=007EF890，宿主 00629210（atlas，与 ring4_at ctor 地址一致）；与同表其余装表点区分',
    '0062D7A0': 'ParticleClass 第5槽；vt=007EF954，COL=00807BE8；site 0062B767 imm=007EF954，宿主 0062B5E0（atlas）；与同表 slot8 行仅以槽号 5/8 区分',
    '0062D9A0': 'ParticleClass 第8槽；同 vt=007EF954、site 0062B767；ring4_at 第二 token 0062B5E0 即宿主函数（atlas 命中）；与 slot5 行仅以槽号区分',
    '0062FE90': 'ParticleSystemClass 第10槽；vt=007EFB9C，COL=00807CA0；site 0062DD16 imm=007EFB9C，宿主 0062DC50（atlas，与 ring4_at 第二 token 一致）；与 slot6 行同表同站点、靠槽号 10/6 区分',
    '00630090': 'ParticleSystemClass 第6槽；同 vt=007EFB9C、site 0062DD16、func 0062DC50；与 slot10 行同表同站点、仅以槽号区分',
    '00644960': 'ParticleSystemTypeClass 第8槽；vt=007F00A8，COL=00808238；site 0064419C imm=007F00A8，宿主 006440A0（atlas，与 ring4_at 第二 token 一致）',
    '006457A0': 'ParticleTypeClass 第6槽；vt=007F0188，COL=008082F0；site 00644CF4 imm=007F0188，宿主 00644BE0（atlas，与 ring4_at 第二 token 一致）；与 slot8 行同表同站点、靠槽号 6/8 区分',
    '00645950': 'ParticleTypeClass 第8槽；同 vt=007F0188、site 00644CF4、func 00644BE0；与 slot6 行同表同站点、仅以槽号区分',
    '006B5850': 'SmudgeTypeClass 第5槽；vt=007F3528，COL=008099A0；site 006B529B imm=007F3528，宿主 006B5260（atlas，与 ring4_at in_func 一致）',
    '006C2B10': 'T_TClassFactory_VAircraftTypeClass__ 第3槽；vt=007F3B28，COL=0080A8E8；site 006C2A49 imm=007F3B28，宿主 006C2A40（atlas，ctor 入口+9）；RTTI .?AV?$TClassFactory@VAircraftTypeClass@@@@ 与行名类一致；各工厂类 vt/site 互不相同',
    '006C2C90': 'T_TClassFactory_VInfantryTypeClass__ 第3槽；vt=007F3B40，COL=0080A938；site 006C2BC9 imm=007F3B40，宿主 006C2BC0（atlas）；与 AircraftType 工厂行以 vt/class/site 区分',
    '006C2E10': 'T_TClassFactory_VBulletTypeClass__ 第3槽；vt=007F3B58，COL=0080A988；site 006C2D49 imm=007F3B58，宿主 006C2D40（atlas）；vt/class/site 与同族其余行互异',
    '006C2F90': 'T_TClassFactory_VIsometricTileTypeClass__ 第3槽；vt=007F3B70，COL=0080A9D8；site 006C2EC9 imm=007F3B70，宿主 006C2EC0（atlas）；vt/class/site 与同族其余行互异',
    '006C3110': 'T_TClassFactory_VOverlayTypeClass__ 第3槽；vt=007F3B88，COL=0080AA28；site 006C3049 imm=007F3B88，宿主 006C3040（atlas）；vt/class/site 与同族其余行互异',
    '006C3290': 'T_TClassFactory_VSmudgeTypeClass__ 第3槽；vt=007F3BA0，COL=0080AA78；site 006C31C9 imm=007F3BA0，宿主 006C31C0（atlas）；vt/class/site 与同族其余行互异',
    '006C3410': 'T_TClassFactory_VUnitClass__ 第3槽；vt=007F3BB8，COL=0080AAC8；site 006C3349 imm=007F3BB8，宿主 006C3340（atlas）；vt/class/site 与同族其余行互异',
    '006C3590': 'T_TClassFactory_VBuildingClass__ 第3槽；vt=007F3BD0，COL=0080AB18；site 006C34C9 imm=007F3BD0，宿主 006C34C0（atlas）；vt/class/site 与同族其余行互异',
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
        src_vt = ('R16_F1_B2/scan_fields.py: scan_dd(.rdata/.data) hit=%s -> '
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

    # 6 项字节复核汇总
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
