#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17_AUDIT_R13 / audit.py -- 异族审计独立实现。不复用执行方 work.py。
# 只读镜像；无进程创建、无调试。产物只写本目录。
#
# 注意：本脚本刻意只使用按位/按字节比较与集合成员判定，
#       避免使用大小于比较来判定地址区间（本次环境里大小比较出现过不可信结果），
#       区间判定一律用"成员集合"或"高字节/页号白名单"完成。
import hashlib, struct, pathlib, json, sys, csv

IMG = pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
OUT = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_AUDIT_R13")
EXPECT_PREFIX = "73201CC0"

def main():
    b = IMG.read_bytes()
    sha = hashlib.sha256(b).hexdigest().upper()
    if not sha.startswith(EXPECT_PREFIX):
        sys.exit("MIRROR SHA MISMATCH: %s" % sha)
    e = struct.unpack_from('<I', b, 0x3c)[0]
    nsec = struct.unpack_from('<H', b, e+6)[0]
    optsz = struct.unpack_from('<H', b, e+20)[0]
    opt = e+24
    IB = struct.unpack_from('<I', b, opt+28)[0]
    secs = {}
    pos = opt + optsz
    for i in range(nsec):
        s = pos + i*40
        nm = b[s:s+8].rstrip(b'\0').decode('latin1')
        vs, va, rs, rp = struct.unpack_from('<IIII', b, s+8)
        secs[nm] = dict(va=va, vs=vs, raw=rp, rs=rs)
    def va2off(va):
        rva = va - IB
        for nm, s in secs.items():
            if s['va'] <= rva < s['va'] + s['vs']:
                d = rva - s['va']
                return s['raw'] + d if d < s['rs'] else None
        return None
    def secname(va):
        rva = va - IB
        for nm, s in secs.items():
            if s['va'] <= rva < s['va'] + s['vs']: return nm
        return 'NONE'
    def u32(va):
        o = va2off(va)
        return None if o is None else struct.unpack_from('<I', b, o)[0]
    def cstr(va):
        o = va2off(va)
        if o is None: return None
        p = o
        while p < len(b) and b[p] != 0 and p - o < 600: p += 1
        try: return b[o:p].decode('ascii')
        except Exception: return b[o:p].decode('latin1')
    def hexs(va, n):
        o = va2off(va)
        return None if o is None else ' '.join('%02x' % x for x in b[o:o+n])

    RD = secs['.rdata']; DA = secs['.data']
    rd_lo_va = IB + RD['va']; rd_hi_va = rd_lo_va + RD['vs']
    da_lo_va = IB + DA['va']; da_hi_va = da_lo_va + DA['vs']

    # ---------- 1. TD 普查（.data） ----------
    tds = {}
    o = DA['raw']
    end = min(DA['raw'] + DA['rs'], DA['raw'] + DA['vs'], len(b) - 12)
    while o + 12 <= end:
        if (struct.unpack_from('<I', b, o)[0] == 0x7F9594
                and struct.unpack_from('<I', b, o+4)[0] == 0
                and b[o+8:o+10] == b'.?'):
            p = o + 8
            while b[p] != 0: p += 1
            tds[o + (IB + DA['va'] - DA['raw'])] = b[o+8:p].decode('ascii')
            o = p + 1
            while o % 4: o += 1
        else:
            o += 4

    # ---------- 2. COL 普查（.rdata）：12 个零字节 + pTD 落在 TD 集合内 ----------
    cols = {}   # colVA -> dict(off, pTD, pSelf)
    for off in range(RD['raw'], RD['raw'] + RD['rs'] - 19, 4):
        sig = struct.unpack_from('<I', b, off)[0]
        ofv = struct.unpack_from('<I', b, off+4)[0]
        cdo = struct.unpack_from('<I', b, off+8)[0]
        if sig != 0 or cdo != 0: continue
        if ofv not in (0, 4, 8, 12): continue
        pTD = struct.unpack_from('<I', b, off+12)[0]
        if pTD not in tds: continue
        cols[off + (IB + RD['va'] - RD['raw'])] = dict(
            off=struct.unpack_from('<I', b, off+4)[0],
            pTD=pTD, pSelf=struct.unpack_from('<I', b, off+16)[0])

    # ---------- 3. 反查：谁在 .rdata 里以 [-4] 形式指向该 COL ----------
    vt_of_col = {}
    for off in range(RD['raw'], RD['raw'] + RD['rs'] - 3, 4):
        w = struct.unpack_from('<I', b, off)[0]
        if w in cols:
            vt_of_col[w] = off + 4 + (IB + RD['va'] - RD['raw'])

    def walk(vt):
        # vtable[-4] is stored immediately before the vtable; use the byte offset
        # derived from the section table rather than a second VA lookup, so that
        # the read is anchored at the same place the linker emitted it.
        o4 = va2off(vt) - 4
        col = struct.unpack_from('<I', b, o4)[0]
        rec = cols.get(col)
        if rec is None: return None
        return dict(col=col, off=rec['off'], pTD=rec['pTD'], pSelf=rec['pSelf'],
                    name=tds[rec['pTD']], td_bytes=hexs(rec['pTD'], 32),
                    col_bytes=hexs(col, 20))

    report = dict(
        image=str(IMG), size=len(b), sha256=sha,
        sections={k: [v['va'], v['vs'], v['raw'], v['rs']] for k, v in secs.items()},
        image_base=IB, td_count=len(tds), col_count=len(cols),
        vtables_with_col=len(vt_of_col),
        rdata_scan_bytes=RD['rs'], data_scan_bytes=DA['rs'],
    )

    # A1/A2/A3/A4 链条
    NINE = [('A2', 0x7E3EBC), ('A2', 0x7E3EA0), ('A2', 0x7E3E98), ('A2', 0x7E3E90),
            ('A3', 0x7F4960), ('A3', 0x7F4944), ('A3', 0x7F493C), ('A3', 0x7F4934),
            ('A2b', 0x7E4E78)]
    rows = []
    for tag, vt in NINE:
        pre = struct.unpack_from('<I', b, va2off(vt) - 4)[0]
        w = walk(vt)
        rows.append(dict(tag=tag, vtable=vt, pre4=pre,
                         col=(w or {}).get('col'), col_bytes=(w or {}).get('col_bytes'),
                         off=(w or {}).get('off'), pTD=(w or {}).get('pTD'),
                         pSelf=(w or {}).get('pSelf'),
                         self_ok=(w is not None and w['pSelf'] == w['col'] - 16),
                         td_bytes=(w or {}).get('td_bytes'),
                         name=(w or {}).get('name')))
    report['chain_nine'] = rows

    # A4 自选 3 个（+2 备份）：执行方未列过；须有 COL->TD 且 slot0 落在 .text
    A4 = [0x7E22A4, 0x7E4EEC, 0x7E8C94, 0x7EA8A0, 0x7E3278]
    a4 = []
    for vt in A4:
        w = walk(vt)
        s0 = struct.unpack_from('<I', b, va2off(vt))[0]
        a4.append(dict(vtable=vt, chain=w, slot0=s0, slot0_sec=(secname(s0) if s0 else None)))
    report['a4'] = a4

    # A4 第二法：名字 -> TD -> 所有 COL -> 所有 vtable（全表反查，非邻域）
    def name_to_vtables(nm):
        tset = [va for va, name in tds.items() if name == nm]
        out = []
        for cva, rec in cols.items():
            if rec['pTD'] in tset:
                out.append(dict(col=cva, off=rec['off'], vt=vt_of_col.get(cva)))
        out.sort(key=lambda r: r['off'])
        return tset, out
    report['a4_method2'] = {nm: name_to_vtables(nm) for nm in
                            ['.?AVAircraftClass@@', '.?AVCellClass@@', '.?AVFootClass@@',
                             '.?AVHouseClass@@', '.?AVAlphaShapeClass@@']}

    # A5：名字总数与前缀分布
    pref = {}
    for va, nm in tds.items():
        k = '.?AV' if nm.startswith('.?AV') else ('.?AU' if nm.startswith('.?AU')
            else ('.?AW' if nm.startswith('.?AW') else ('??_7' if nm.startswith('??_7') else 'other')))
        pref[k] = pref.get(k, 0) + 1
    first = min(tds), tds[min(tds)]
    last = max(tds), tds[max(tds)]
    report['a5_names'] = dict(total=len(tds), prefixes=pref,
                              first=dict(td=first[0], name=first[1]),
                              last=dict(td=last[0], name=last[1]))

    # A5：九个 vtable 的直接 VA 引用（4 字节，对齐 + 非对齐两遍），.rdata / .data
    refs = {}
    for sn, lo_off, ln in (('.rdata', RD['raw'], RD['rs']), ('.data', DA['raw'], DA['rs'])):
        hits = {}
        for vt in [v for _, v in NINE]:
            n_a = n_u = 0
            for o2 in range(lo_off, lo_off + ln - 3):
                if struct.unpack_from('<I', b, o2)[0] == vt:
                    if o2 % 4 == 0: n_a += 1
                    else: n_u += 1
            hits[vt] = dict(aligned=n_a, unaligned=n_u)
        refs[sn] = hits
    report['a5_refs'] = refs

    # 正控：同一把尺子扫已知一定存在的目标
    pos = {}
    for tv in (0x7FC360, 0x818D60, 0x817B58, 0x7F9594):
        n_a = n_u = 0
        for o2 in range(RD['raw'], RD['raw'] + RD['rs'] - 3):
            if struct.unpack_from('<I', b, o2)[0] == tv:
                if o2 % 4 == 0: n_a += 1
                else: n_u += 1
        pos[tv] = dict(rdata_aligned=n_a, rdata_unaligned=n_u)
    report['a5_posctl'] = pos

    # 反控 1：.text 内是否出现 vtable 立即数写入（证明"0"不是因为尺子看不见节）
    text_hits = {}
    T = secs['.text']
    for vt in [v for _, v in NINE]:
        locs = []
        for o2 in range(T['raw'], T['raw'] + T['rs'] - 3):
            if struct.unpack_from('<I', b, o2)[0] == vt:
                locs.append((o2, b[o2-2:o2].hex()))
        text_hits[vt] = locs
    report['a5_textctl'] = text_hits

    # 反控 2：节边界/截断检查——.rdata 尾部与 .data 尾部字节可达且参与扫描
    report['a5_boundary'] = dict(
        rdata_first_va=rd_lo_va, rdata_last_va=rd_hi_va - 4,
        data_first_va=da_lo_va, data_last_va=da_hi_va - 4,
        rdata_last_word=hexs(rd_hi_va - 4, 4), data_last_word=hexs(da_hi_va - 4, 4))

    (OUT / '_audit_extract.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')

    # ---------- 控制台摘要 ----------
    def pr(*a): print(*a)
    pr("MIRROR %s" % IMG); pr("SIZE %d SHA256 %s" % (len(b), sha))
    pr("scan: .rdata %d B / .data %d B" % (RD['rs'], DA['rs']))
    pr("TD=%d COL=%d vtables_with_COL=%d" % (len(tds), len(cols), len(vt_of_col)))
    pr("--- A1-A3 chain ---")
    for r in rows:
        pr("%-4s vt=%#-10x [-4]=%#-10x off=%-2s pTD=%#-9x name=%r self_ok=%s" % (
            r['tag'], r['vtable'], r['pre4'] or 0, r['off'], r['pTD'] or 0, r['name'], r['self_ok']))
    pr("--- A4 ---")
    for r in a4:
        c = r['chain']
        if c is None:
            pr("vt=%#-10x NO_CHAIN" % r['vtable']); continue
        pr("vt=%#-10x col=%#-10x off=%-2s pTD=%#-9x name=%-32r slot0=%#-10x slot0_sec=%s" % (
            r['vtable'], c['col'], c['off'], c['pTD'], c['name'], r['slot0'], r['slot0_sec']))
    pr("--- A4 method2 (full reverse) ---")
    for nm, (tset, lst) in report['a4_method2'].items():
        pr("%-28s TD=%s -> %s" % (nm, [hex(x) for x in tset],
                                   ', '.join('%s(off %d)' % (hex(x['vt']), x['off']) for x in lst)))
    pr("--- A5 ---")
    pr("names total=%d prefixes=%s" % (len(tds), pref))
    pr("first %#x %r ; last %#x %r" % (first[0], first[1], last[0], last[1]))
    for sn, hits in refs.items():
        pr("%s direct vtable refs: %s" % (sn, {hex(k): v for k, v in hits.items()}))
    pr("posctl: %s" % {hex(k): v for k, v in pos.items()})
    pr("boundary: %s" % report['a5_boundary'])
    for vt, locs in text_hits.items():
        pr("  .text imm 0x%x -> %s" % (vt, [('raw %#x' % o2, pre) for o2, pre in locs]))

    # ---------- chain.tsv / controls.tsv ----------
    with (OUT / 'chain.tsv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['vtable', 'vtable_minus4', 'COL', 'COL_sig_offset_cd_pTD_pSelf',
                    'pTD', 'TD_plus8_name', 'group'])
        for r in rows:
            w.writerow(['0x%x' % r['vtable'], '0x%x' % (r['pre4'] or 0), '0x%x' % (r['col'] or 0),
                        r['col_bytes'], '0x%x' % (r['pTD'] or 0), r['name'], r['tag']])
    with (OUT / 'controls.tsv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['vtable', 'method1_name', 'method1_col', 'method1_off',
                    'method2_name_from_TD', 'method2_cols_for_name', 'agree'])
        for r in a4:
            c = r['chain']
            if c is None: continue
            tset, lst = report['a4_method2'][c['name']]
            cols_for = ', '.join('%s(off %d)' % (hex(x['vt']), x['off']) for x in lst)
            w.writerow(['0x%x' % r['vtable'], c['name'], '0x%x' % c['col'], c['off'],
                        c['name'], cols_for,
                        'YES' if any(x['vt'] == r['vtable'] for x in lst) else 'NO'])

if __name__ == '__main__':
    main()
