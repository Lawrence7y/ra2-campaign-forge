# -*- coding: utf-8 -*-
"""
R16-F1-OTHER14 — 只读字节复核（14 行：2 direct_call + 12 slot_witness）。

输入（全部只读）：
  R16_PROBE_F1_PIVOT/other14.tsv       探针清单（14 行 + slot/direct 线索）
  COVERAGE/coverage.tsv               整行原值（本脚本绝不写）
  ra2youli/gamemd.exe                 只读 PE（pefile fast_load + capstone）

方法：复用 PROBE_802/probe.py 的 Image / TextScan / vtable_start / col_of /
      scan_dd / which_body / load_atlas_sizes（与 R16_F1_B1..B5 同法）。

输出（只写本目录）：scan_raw.json —— 供下一阶段生成 delta/fields/report。
"""
import os, sys, json, re, hashlib, collections
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
OTHER14 = os.path.join(R14, 'R16_PROBE_F1_PIVOT', 'other14.tsv')
OUT = os.path.join(HERE, 'scan_raw.json')

DIRECT_SITES = {'004AF540': '006C404C', '004B5AB0': '006C494C'}
EXPECT_EXE_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_other14():
    rows = []
    with open(OTHER14, encoding='utf-8') as f:
        hdr = f.readline().rstrip('\r\n').split('\t')
        ix = {k: i for i, k in enumerate(hdr)}
        for ln in f:
            c = ln.rstrip('\r\n').split('\t')
            if len(c) != len(hdr):
                continue
            rows.append({k: c[ix[k]] for k in hdr})
    return rows


def load_coverage_raw():
    """读 coverage.tsv 原始字节行（8 列），entry -> list[bytes]。不写。"""
    cov = {}
    with open(COV, 'rb') as f:
        raw = f.read()
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) == 8:
            try:
                e = c[0].decode('ascii').upper()
            except Exception:
                continue
            cov.setdefault(e, c)
    return cov, len(raw)


def u32hex(v):
    return '%08X' % v if v is not None else None


def main():
    cov_sha_before = sha256p(COV)
    exe_sha = sha256p(EXE)
    cov_bytes = os.path.getsize(COV)
    exe_bytes = os.path.getsize(EXE)
    if exe_sha != EXPECT_EXE_SHA:
        raise RuntimeError('gamemd.exe sha mismatch: %s' % exe_sha)

    rows = load_other14()
    cov, cov_raw_len = load_coverage_raw()
    img = probe.Image(EXE)
    ts = probe.TextScan(img)
    atlas_sizes = probe.load_atlas_sizes()
    ranges = probe.body_ranges(atlas_sizes)

    print('exe  :', exe_bytes, 'B sha', exe_sha)
    print('cov  :', cov_bytes, 'B sha', cov_sha_before, '(raw split len %d)' % cov_raw_len)
    print('.text: insns %d skip %d [%08X,%08X)' % (ts.n_insn, ts.n_skip, ts.lo, ts.hi))
    bad = [(k, ts.direct.get(int(k, 16), 0), v)
           for k, v in probe.ANCHORS.items() if ts.direct.get(int(k, 16), 0) != v]
    print('anchors:', 'OK' if not bad else bad)

    out = dict(exe_sha=exe_sha, exe_bytes=exe_bytes, cov_sha_before=cov_sha_before,
               cov_bytes=cov_bytes, anchors_ok=(not bad),
               text_insns=ts.n_insn, text_skip=ts.n_skip,
               rows=[])

    for r in rows:
        entry = r['entry'].upper()
        cat = r['f_reason']
        form = 'direct_call' if cat == 'sem_live_table_install' else 'slot_witness'
        e_int = int(entry, 16)
        cov_row = cov.get(entry)
        if cov_row is None:
            raise RuntimeError('entry %s not in coverage.tsv' % entry)
        sem_before = cov_row[3].decode('utf-8', 'replace')
        pre_has4 = '④' in sem_before

        rec = dict(entry=entry, subsystem=r['subsystem'], name=r['name'],
                   category=cat, form=form,
                   cov_cols=[c.decode('utf-8', 'replace') for c in cov_row],
                   pre_has4=pre_has4,
                   pre_sem=sem_before,
                   deriv_class=r['deriv_class'],
                   why_no_audit=r['why_no_audit'],
                   probe_sem_head=r['sem_head'])

        if form == 'slot_witness':
            slot_va = int(r['slot_va'], 16)
            slot_idx = int(r['slot_idx'])
            vt = slot_va - slot_idx * 4
            vt_hex = u32hex(vt)
            col = img.u32(vt - 4)
            td = img.u32(col + 12) if col is not None and img.in_image(col) else None
            off = img.u32(col + 4) if col is not None and img.in_image(col) else None
            mangled = img.cstr(td + 8, 256) if td is not None and img.in_image(td) else None
            # 6 项字节复核
            c1 = img.u32(vt + slot_idx * 4) == e_int
            c2 = img.u32(vt - 4) == col
            c3 = off == 0
            c4 = img.u32(col + 12) == td
            c5 = mangled == r['slot_rtti']
            # install sites: 所有 mov [mem], imm32==vt 的站点
            sites = ts.installs_of(vt)  # [(site_va, disp)]
            # 选主站点：优先 imm_ok 且不在 entry 体内（体外装表）；host 用 atlas 命中，
            # atlas 未命中（CRT 静态初始化函数未收录）时用 nop/int3 填充后的函数起点反汇编定界。
            def derive_host(sva):
                if body_of(sva):
                    return '%08X' % body_of(sva), 'atlas'
                # 向前找最近一段 >=3 字节 0xCC/0x90 填充，取其后第一字节为函数起点；
                # 再验证从该起点线性反汇编能精确落到 sva（指令边界）。
                so = sva - img.base
                lo = max(0, so - 512)
                seg = bytes(img.buf[lo:so + 16])
                import capstone as _cs
                mdx = _cs.Cs(_cs.CS_ARCH_X86, _cs.CS_MODE_32)
                mdx.detail = True
                mdx.skipdata = True
                cand = None
                for i in range(2, len(seg) - 3):
                    if (seg[i-2] in (0xCC, 0x90) and seg[i-1] in (0xCC, 0x90)
                            and seg[i] not in (0xCC, 0x90)):
                        st = img.base + lo + i
                        code = bytes(img.buf[st - img.base:sva - img.base + 16])
                        if sva in [x.address for x in mdx.disasm(code, st)]:
                            cand = st
                return (('%08X' % cand) if cand else None), 'disasm-padding'

            body_of = lambda sva: probe.which_body(ranges, sva)
            site_recs = []
            for sva, disp in sites:
                body = body_of(sva)
                inside = (body == e_int)  # 装表点落在 entry 自身体内 = 析构自装(㉓)
                # 指令字节
                so = sva - img.base
                ib = bytes(img.buf[so:so + 8]).hex().upper()
                # capstone 解码 imm
                import capstone
                md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
                md.detail = True
                ins = next(md.disasm(bytes(img.buf[so:so + 12]), sva), None)
                imm = None
                if ins and ins.mnemonic == 'mov' and len(ins.operands) == 2 \
                        and ins.operands[1].type == capstone.x86.X86_OP_IMM:
                    imm = ins.operands[1].imm & 0xFFFFFFFF
                h, hsrc = derive_host(sva)
                site_recs.append(dict(site='%08X' % sva, disp=disp,
                                      bytes=ib, ins=(ins.mnemonic + ' ' + ins.op_str) if ins else None,
                                      imm=(u32hex(imm) if imm is not None else None),
                                      imm_ok=(imm == vt),
                                      host=h, host_src=hsrc,
                                      inside_entry=inside))
            outside = [s for s in site_recs if s['imm_ok'] and not s['inside_entry']]
            inside_ok = [s for s in site_recs if s['imm_ok'] and s['inside_entry']]
            chosen = outside[0] if outside else (inside_ok[0] if inside_ok else None)
            c6 = bool(outside)  # 活表独立链成立：体外 imm32==vt 装表点存在（host 名为命名用途）
            rtti_match = probe.col_name_match(r['name'].split('::')[0], mangled)
            # name 类含 '<...>' 模板时 col_name_match 可能 nomatch，另用 token 含判
            toks = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', r['name'].split('::')[0]))
            toks_ok = bool(mangled) and all(t in mangled for t in toks if t not in ('Class',))
            rec.update(dict(
                slot_idx=slot_idx, slot_va='%08X' % slot_va, vt=vt_hex,
                col=u32hex(col), off=off, td=u32hex(td), mangled=mangled,
                checks=dict(c1_slot_eq_entry=c1, c2_vtm4_eq_col=c2,
                            c3_colp4_eq_offset0=c3, c4_colp12_eq_td=c4,
                            c5_cstr_tdp8_eq_slot_rtti=c5, c6_outside_install_exists=c6),
                sites=site_recs, chosen=chosen,
                n_sites=len(site_recs), n_outside=len(outside), n_inside=len(inside_ok),
                rtti_col_name_match=rtti_match, rtti_tokens_ok=toks_ok,
                key_addrs=('vt=%s,slot=%d,slot_va=%s,COL=%s,off=%s,TD=%s,RTTI=%s,'
                           'install=%s,host=%s(%s)' % (
                               vt_hex, slot_idx, '%08X' % slot_va, u32hex(col), off,
                               u32hex(td), mangled,
                               chosen['site'] if chosen else '未取得',
                               chosen['host'] if chosen else '未取得',
                               chosen['host_src'] if chosen else '-'))))
            if not (c1 and c2 and c3 and c4 and c5 and c6 and toks_ok):
                rec['status'] = 'SKIP'
                miss = [k for k, v in rec['checks'].items() if not v]
                if not toks_ok:
                    miss.append('rtti_tokens_ok')
                rec['skip_reason'] = 'byte check fail: ' + ','.join(miss)
            else:
                rec['status'] = 'OK'
            rec['same_source_judged'] = 'no'
            rec['same_source_basis'] = (
                '②=COL→TD→RTTI 装饰名(%s→%s，.rdata/.data 静态类名链)；'
                '④=体外装表点 %s(host %s[%s，%s]，.text 中 mov [dest],imm32==vt，非本 entry 体内)，'
                '两者字节链不同（.rdata/.data 名称链 vs .text 装表指令），④ 独立于 ②；'
                '槽位占用 vt[%d]==entry 仅按 D-47(A)/§12.6 让位口径引用，不作独立证据链。'
                % (u32hex(col), mangled,
                   chosen['site'] if chosen else '未取得',
                   chosen['host'] if chosen else '未取得',
                   chosen['host_src'] if chosen else '-',
                   ('静态初始化函数' if chosen and chosen['host_src'] == 'disasm-padding' else 'ctor/常规函数'),
                   slot_idx))

        else:
            # direct_call: site E8 rel32 -> entry
            site = int(DIRECT_SITES[entry], 16)
            so = site - img.base
            raw5 = bytes(img.buf[so:so + 5])
            import capstone
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            md.detail = True
            ins = next(md.disasm(bytes(img.buf[so:so + 8]), site), None)
            tgt = None
            imm_ok = False
            if ins and ins.mnemonic == 'call' and len(ins.operands) >= 1 \
                    and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                tgt = ins.operands[0].imm & 0xFFFFFFFF
                imm_ok = (tgt == e_int)
            # site+5+rel32 == entry 手算
            rel32 = int.from_bytes(raw5[1:5], 'little', signed=True)
            arith_ok = (site + 5 + rel32 == e_int)
            body = probe.which_body(ranges, site)
            inside = (body == e_int)
            # 宿主函数体的头几条指令，证明是工厂 CreateInstance
            host = '%08X' % body if body else None
            hb = None
            if body:
                hbo = body - img.base
                hb = bytes(img.buf[hbo:hbo + 16]).hex().upper()
            d1 = raw5[0] == 0xE8
            d2 = arith_ok
            d3 = imm_ok
            d4 = (not inside) and bool(body)
            rec.update(dict(
                site='%08X' % site, call_bytes=raw5.hex().upper(),
                rel32=('%+d' % rel32), ins=(ins.mnemonic + ' ' + ins.op_str) if ins else None,
                target=(u32hex(tgt) if tgt is not None else None),
                host=host, host_head=hb, inside_entry=inside,
                checks=dict(d1_opcode_E8=d1, d2_site5rel32_eq_entry=d2,
                            d3_capstone_target_eq_entry=d3, d4_outside_nonself=d4),
                key_addrs=('site=%08X,E8=%s,rel32=%s,target=%s,host=%s' % (
                    site, raw5.hex().upper(), '%+d' % rel32,
                    u32hex(tgt) if tgt is not None else '未取得', host or '未取得'))))
            if not (d1 and d2 and d3 and d4):
                rec['status'] = 'SKIP'
                miss = [k for k, v in rec['checks'].items() if not v]
                rec['skip_reason'] = 'direct check fail: ' + ','.join(miss)
            else:
                rec['status'] = 'OK'
            rec['same_source_judged'] = 'no'
            rec['same_source_basis'] = (
                '②=类属/身份证据(构造器装 canonical vt off0/off4 + 工厂上下文，见本行语义栏；'
                '与 vt 派生不同源)；④=工厂 CreateInstance 体内 direct call E8 @%s → %s，'
                'site+5+rel32==entry 且非自环，位于 .text 调用站点，独立于 ② 的类身份链；'
                'D-47(A)/§12.6 仅作披露指针（本形态不依赖槽位让位）。' % (
                    '%08X' % site, entry))
        out['rows'].append(rec)
        print('%s %-4s %-9s status=%s pre4=%s | %s' % (
            entry, rec['subsystem'], form, rec['status'], rec['pre_has4'],
            rec.get('skip_reason', '')))

    cov_sha_after = sha256p(COV)
    out['cov_sha_after'] = cov_sha_after
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\ncov sha before/after:', cov_sha_before, cov_sha_after,
          'unchanged=', cov_sha_before == cov_sha_after)
    print('wrote', OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
