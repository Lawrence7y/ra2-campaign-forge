"""Per-row audit for R4_FILL_91_R2 fill_delta.tsv — independent bytes only.

Audits the 12 sampled rows and (for the dedicated question) the 4 rows whose
install host is an initterm callback.
"""
import json
import re
import struct

import capstone

import reib

TSV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R4_FILL_91_R2\fill_delta.tsv"
SAMPLE = ["00464AC0", "0055A050", "0055A950", "00597D50", "005C0FE0", "005CA6D0",
          "005CB440", "005D6540", "005D74A0", "0073C5F0", "007B9C30", "007BA380"]
INITTERM_ROWS = ["005519B0", "0055B880", "0055BAA0", "006CF240"]
ATEXIT_STUB = 0x7C978A
INITTERM_FN = 0x7CBED3
INITTERM_LO = 0x812000
INITTERM_HI = 0x815DA4

CLAIM = re.compile(
    r'(?P<cls>[A-Za-z_][A-Za-z0-9_]*)::slot(?P<slot>\d+)'
    r'[（(]\s*vt=(?P<vt>[0-9A-Fa-f]{8})\s*[，,]\s*槽\s*(?P<slot2>\d+)\s*值=(?P<val>[0-9A-Fa-f]{8})\s*[，,]'
    r'\s*COL=(?P<col>[0-9A-Fa-f]{8})\s+offset=(?P<off>\d+)\s*[，,]'
    r'\s*RTTI=(?P<td>[0-9A-Fa-f]{8})\s*[→>]\s*(?P<dec>\.\?[AU][^\s，,；;）)]*)'
    r'\s*[，,；;]\s*装表点\s*(?P<site>[0-9A-Fa-f]{8})\s*位于\s*(?P<host>[0-9A-Fa-f]{8})\s*体内')


def load_rows():
    out = {}
    with open(TSV, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split('\t')
    for ln in lines[1:]:
        f = ln.split('\t')
        out[f[0]] = dict(zip(hdr, f))
    return out


def hexbytes(img, va, n):
    b = img.raw(va, n)
    return ' '.join('%02X' % x for x in b) if b else ''


def all_witnesses(img, entry, limit=200):
    hits = []
    for s in img.sections:
        if s['name'] not in ('.rdata', '.data'):
            continue
        blob = img.buf[s['raw_off']:s['raw_off'] + s['raw_size']]
        pat = struct.pack('<I', entry)
        pos = blob.find(pat)
        while pos >= 0:
            if pos % 4 == 0:
                vt = reib.vtable_start(img, s['va'] + pos)
                if vt:
                    col = reib.col_at(img, vt)
                    if col and reib.plausible_col(img, col['col']):
                        hits.append(dict(vt=vt, slot=(s['va'] + pos - vt) // 4, col=col))
            pos = blob.find(pat, pos + 1)
    hits.sort(key=lambda h: (h['vt'], h['slot']))
    return hits[:limit]


def tables_by_class(img):
    """Map demangled class name -> [vtable starts] by scanning .rdata/.data for
    COLs whose TD name matches."""
    out = {}
    for s in img.sections:
        if s['name'] not in ('.rdata', '.data'):
            continue
        va, size = s['va'], s['raw_size']
        for p in range(va, va + size - 4, 4):
            col = img.u32(p)
            if col is None or not img.in_image(col):
                continue
            if not reib.plausible_col(img, col):
                continue
            name = reib.demangle_class(img.cstr(img.u32(col + 0xC) + 8, 96))
            if name:
                out.setdefault(name, set()).add(p + 4)
    return out


def free_closure(dis, host, iat_heapfree, depth=3):
    """Function names reaching a HeapFree/delete import within `depth` calls."""
    frontier = {host}
    seen = set(frontier)
    hits = []
    for _ in range(depth):
        nxt = set()
        for f in frontier:
            for a, ins in dis.body(f, limit=200000).items():
                for op in ins.operands:
                    if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                        if (op.mem.disp & 0xFFFFFFFF) in iat_heapfree:
                            hits.append((f, iat_heapfree[op.mem.disp & 0xFFFFFFFF]))
                t = dis.calltarget(ins)
                if t is not None and t not in seen and t > 0x401000:
                    nxt.add(t)
        seen |= nxt
        frontier = nxt
    return sorted(set(hits))


def main():
    img = reib.Image()
    dis = reib.Dis(img)
    iat = reib.iat_map(img)
    iat_heapfree = {k: v for k, v in iat.items() if 'HeapFree' in v}
    strict = reib.atexit_set(img, dis, ATEXIT_STUB)
    sup = reib.atexit_superset(img, ATEXIT_STUB, window=48)
    atexit_regs = set(fn for _, fn in strict)
    sup_regs = set(fn for _, fn, _ in sup)
    # deallocator set: operator delete (0x7C8B3D) and its HeapFree helper
    free_callees = {0x7C8B3D, 0x7C93E8}
    _vw_cache = {}

    def writes_vtable(fn):
        """Does this function store a COL-guarded vtable address into memory?"""
        if fn in _vw_cache:
            return _vw_cache[fn]
        ok = False
        for a, ins in dis.body(fn, limit=200000).items():
            if ins.mnemonic.startswith('mov') and dis.dst_is_mem(ins):
                v = dis.imm(ins)
                if v is not None and img.in_image(v) and img.u32(v - 4) is not None \
                        and reib.plausible_col(img, img.u32(v - 4)):
                    ok = True
                    break
        _vw_cache[fn] = ok
        return ok

    vt_writers = writes_vtable
    all_calls_to_stub = 0
    tv = img.text
    blob = img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]
    pos = blob.find(b'\xe8')
    while pos >= 0:
        if pos + 5 <= len(blob):
            rel = struct.unpack('<i', blob[pos + 1:pos + 5])[0]
            if tv['va'] + pos + 5 + rel == ATEXIT_STUB:
                all_calls_to_stub += 1
        pos = blob.find(b'\xe8', pos + 1)

    init_vals = {}
    for p in range(INITTERM_LO, INITTERM_HI, 4):
        init_vals.setdefault(img.u32(p), []).append(p)
    cands = reib.start_candidates(img)
    by_class = tables_by_class(img)
    rows = load_rows()
    result = {}

    for entry_s in SAMPLE + INITTERM_ROWS:
        r = rows[entry_s]
        col4 = r['one_line_semantics']
        m = CLAIM.search(col4)
        entry = int(entry_s, 16)
        d = dict(entry=entry_s, name=r['name'], in_sample=entry_s in SAMPLE,
                 col4=col4, claim=m.group(0) if m else None)
        if not m:
            d['error'] = 'claim regex did not match'
            result[entry_s] = d
            continue
        vt = int(m.group('vt'), 16)
        slot = int(m.group('slot'))
        col_a = int(m.group('col'), 16)
        td = int(m.group('td'), 16)
        site = int(m.group('site'), 16)
        host = int(m.group('host'), 16)

        # ---------- 1. vt & slot ----------
        slotval = img.u32(vt + slot * 4)
        colv = reib.col_at(img, vt)
        ws = all_witnesses(img, entry)
        row_cls = r['name'].split('::')[0]
        d['check1'] = dict(
            vt_bytes=hexbytes(img, vt - 4, 12),
            slot_dword_bytes=hexbytes(img, vt + slot * 4, 4),
            slot_value=('%08X' % slotval) if slotval else None,
            equals_entry=(slotval == entry),
            slot_numbers_agree=(slot == int(m.group('slot2'))),
            vt_is_table_start=bool(colv and reib.plausible_col(img, colv['col'])),
            col_matches_claim=bool(colv and colv['col'] == col_a),
            n_witnesses=len(ws),
            claim_is_a_witness=any(w['vt'] == vt and w['slot'] == slot for w in ws),
            witnesses=[dict(vt='%08X' % w['vt'], slot=w['slot'], col='%08X' % w['col']['col'],
                            cls=w['col']['td_name'], off=w['col']['offset']) for w in ws],
            row_class_tables=['%08X' % x for x in sorted(by_class.get(row_cls, []))],
            row_class_table_holds_entry=any(w['col']['td_name'] == row_cls for w in ws),
        )

        # ---------- 2. COL ----------
        d['check2'] = dict(
            u32_vt_minus_4='%08X' % (img.u32(vt - 4) or 0),
            bytes_at_vt_minus_4=hexbytes(img, vt - 4, 4),
            matches_claim=bool(colv and colv['col'] == col_a),
            col_header_bytes=hexbytes(img, col_a, 24),
            sig=colv['sig'],
            sig_zero=(colv['sig'] == 0),
            offset=colv['offset'],
            offset_matches_claim=(colv['offset'] == int(m.group('off'))),
            cd='%08X' % colv['cd'],
            ptd='%08X' % colv['td'],
            pchd='%08X' % colv['pchd'],
            ptd_matches_claim=(colv['td'] == td),
        )

        # ---------- 3. TD & class name ----------
        td_from_col = img.u32(col_a + 0xC)
        raw = img.cstr(td + 8, 96)
        name = reib.demangle_class(raw)
        d['check3'] = dict(
            td_from_bytes='%08X' % (td_from_col or 0),
            td_matches_claim=(td_from_col == td),
            td_bytes=hexbytes(img, td, 8) + ' | ' + hexbytes(img, td + 8, 24),
            td8_inline_raw=(raw or b'').decode('latin-1'),
            td8_is_inline_string=bool(raw and raw.startswith(b'.?A')),
            demangled=name,
            claim_label=m.group('cls'),
            claim_dec=m.group('dec'),
            label_equals_td_name=(name == m.group('cls')),
            row_class=row_cls,
            class_mismatch=(name != row_cls),
        )

        # ---------- 4. site & host ----------
        ins = dis.one(site)
        hbody = dis.body(host, limit=200000)
        ebody = dis.body(entry, limit=200000)
        d['check4'] = dict(
            site='%08X' % site,
            site_bytes=hexbytes(img, site, ins.size if ins else 8),
            site_insn=('%s %s' % (ins.mnemonic, ins.op_str)) if ins else None,
            writes_vt=bool(ins and ins.mnemonic.startswith('mov') and dis.dst_is_mem(ins)
                           and dis.imm(ins) == vt),
            host='%08X' % host,
            host_head_bytes=hexbytes(img, host, 16),
            host_body_insns=len(hbody),
            site_in_host_body=(site in hbody),
            entry_body_insns=len(ebody),
            entry_in_host_body=(entry in hbody),
            host_is_padded_start=any(img.raw(host - k, k) for k in (2, 3, 4)) and all(
                x in (0xCC, 0x90) for x in (img.raw(host - 2, 2) or b'')),
            host_initterm_slot=('%08X' % init_vals[host][0]) if host in init_vals else None,
            entry_install_sites_in_own_body=[('%08X' % a) for a, i in ebody.items()
                                             if i.mnemonic.startswith('mov')
                                             and dis.dst_is_mem(i) and dis.imm(i) == vt],
        )

        # ---------- 5. ring-23 ----------
        stores, loads = reib.store_sites(img, dis, vt)
        indirect = reib.indirect_sites(img, dis, vt)
        all_sites = dict(stores)
        for a, (load_at, i2) in indirect.items():
            all_sites.setdefault(a, i2)
        sites = []
        for a in sorted(all_sites):
            i = all_sites[a]
            hb = host if a == site else reib.host_for_site(dis, a, cands)
            fc = free_closure(dis, hb, iat_heapfree) if hb else None
            dsh = reib.dtor_shape(dis, hb, free_callees, vt_writers) if hb else None
            sites.append(dict(
                site='%08X' % a,
                insn=('%s %s' % (i.mnemonic, i.op_str)) if a in stores else
                ('%s %s  [imm load @ %08X]' % (i.mnemonic, i.op_str, indirect[a][0])),
                form='direct-imm-store' if a in stores else 'reg-mediated-store',
                host=('%08X' % hb) if hb else None,
                atexit_strict=bool(hb in atexit_regs),
                atexit_superset=bool(hb in sup_regs),
                dtor=dsh['flags'] if dsh else [],
                free_path=[('%08X' % f, n) for f, n in fc] if fc else [],
                in_initterm=bool(hb in init_vals),
                is_claim=(a == site)))
        used = next(s for s in sites if s['is_claim'])
        target = reib.store_target(dis, host, site, ins) if ins else None
        d['check5'] = dict(
            n_write_points=len(sites),
            write_points=sites,
            n_reg_mentions=len(loads),
            reg_mentions=[('%08X' % a, '%s %s' % (i.mnemonic, i.op_str))
                          for a, i in sorted(loads.items())][:12],
            used=used,
            store_target=('%s %08X' % (target[0], target[1])) if target and target[1] else
                         (target[0] if target else None),
            store_target_section=img.secname(target[1]) if target and target[1] else None,
            atexit_strict_count=len(atexit_regs),
            atexit_superset_count=len(sup_regs),
            stub_call_count=all_calls_to_stub,
            entry_dtor=reib.dtor_shape(dis, entry, free_callees),
        )
        result[entry_s] = d
        print('audited', entry_s, flush=True)

    with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R4_FILL_AUDIT\scripts\audit.json",
              'w', encoding='utf-8') as f:
        json.dump(dict(rows=result,
                       atexit=dict(stub='%08X' % ATEXIT_STUB,
                                   n_push_call=len(atexit_regs),
                                   n_calls_any=all_calls_to_stub,
                                   regs=['%08X' % x for x in sorted(atexit_regs)]),
                       initterm=dict(fn='%08X' % INITTERM_FN, lo='%08X' % INITTERM_LO,
                                     hi='%08X' % INITTERM_HI,
                                     entries=(INITTERM_HI - INITTERM_LO) // 4),
                       sample=SAMPLE, initterm_rows=INITTERM_ROWS),
                  f, indent=1, ensure_ascii=False)
    print('wrote audit.json')


if __name__ == '__main__':
    main()
