"""R121 Q1 (v2, sweep-aligned): push-imm sites + first-call classification + 2b resolution."""
import sys, json, struct
sys.path.insert(0, '_r121')
import x121core2 as C
import x121sweep as S

pe = C.load()
sw = S.get(pe)


def analyze(imm):
    sites = C.find_push_imm_sites(pe, imm)
    rows = []
    for site in sites:
        ins5 = C.one(pe, site)
        sc = dict(mnem=ins5.mnemonic, size=ins5.size, raw=C.raw(ins5)) if ins5 else None
        fc = None
        for i in C.fwd(sw, pe, site, n=40):
            if i.address > site and i.address <= site + 64 and i.mnemonic == 'call':
                fc = i
                break
        row = dict(site=site, site_hex=hex(site), selfcheck=sc)
        if fc is None:
            row['call'] = dict(kind='NO-CALL-IN-64B')
            row['bucket'] = 'NO-CALL-IN-64B'
        else:
            c = C.call_class(pe, fc)
            c['addr'] = fc.address
            c['addr_hex'] = hex(fc.address)
            c['delta'] = fc.address - site
            row['call'] = c
            if c['kind'] == 'A':
                key = 'A:IAT %s' % c['api']
                row['bucket'] = 'a-call[abs]-IAT:' + c['api']
            elif c['kind'] == 'A_NOT_IAT':
                key = 'A:NOT-IAT %s' % hex(c['abs'])
                row['bucket'] = 'a-call[abs]-NOT-IAT:' + hex(c['abs'])
            elif c['kind'] == 'B':
                key = 'B:call [%s]%s' % (c['base'], ('%+d' % c['disp']) if c['disp'] else '')
                # 2b: nearest prior write of base
                rid = C.reg_id(fc, c['base'])
                w, walked = C.nearest_write(pe, sw, fc.address, rid, maxn=64)
                rinfo = None
                if w is not None:
                    rinfo = dict(ins=C.raw(w), addr=hex(w.address), walked=walked,
                                 mnem=w.mnemonic, ops=w.op_str)
                    ava = C.iat_if_abs_mov(pe, w)
                    if ava is not None:
                        rinfo['abs'] = hex(ava)
                        nm = pe.iat_name(ava)
                        if nm:
                            rinfo['api'] = nm
                            rinfo['dll'] = pe.iat[ava][0]
                else:
                    rinfo = dict(found=False, walked=walked,
                                 why='no write to %s within %d instrs backwards' % (c['base'], walked))
                row['reg_resolve'] = rinfo
                if rinfo and rinfo.get('api'):
                    row['bucket'] = 'b-reg-cached-IAT:' + rinfo['api']
                    row['reg_cached_api'] = rinfo['api']
                else:
                    row['bucket'] = 'b-unresolved:call[%s]' % c['base']
                    row['unresolved_ins'] = rinfo.get('ins') if rinfo else None
            elif c['kind'] == 'C':
                if c.get('reg'):
                    row['bucket'] = 'c-call-reg:%s' % c['reg']
                else:
                    row['bucket'] = 'c-call-rel:%s' % hex(c['target'])
            else:
                row['bucket'] = 'other:%s' % c['raw']
        fs = C.cc_func_start(pe, site)
        row['func_start'] = fs
        row['func_start_hex'] = hex(fs) if fs else None
        ppv = C.find_ppv_pair(pe, sw, site)
        row['ppv_pair'] = {k: (hex(v) if isinstance(v, int) and k in ('lea_addr', 'push_addr', 'K') else v)
                           for k, v in ppv.items()} if ppv else None
        if ppv:
            row['ppv_pair']['K_int'] = ppv['K']
        rows.append(row)

    buckets = {}
    for r in rows:
        buckets[r['bucket']] = buckets.get(r['bucket'], 0) + 1

    # raw 2a/b/c buckets independent of resolution
    rawb = {}
    for r in rows:
        c = r['call']
        if c['kind'] == 'A':
            k = 'a call [abs] IAT=%s' % c['api']
        elif c['kind'] == 'A_NOT_IAT':
            k = 'a call [abs] NOT-IAT=%s' % hex(c['abs'])
        elif c['kind'] == 'B':
            k = 'b call [%s%s%s]' % (c['base'], '+' if (c['disp'] or 0) > 0 else '',
                                     ('%d' % c['disp']) if c['disp'] else '')
        elif c['kind'] == 'C':
            k = 'c call %s' % (('reg %s' % c['reg']) if c.get('reg') else hex(c['target'] or 0))
        else:
            k = c['kind']
        rawb[k] = rawb.get(k, 0) + 1

    return dict(imm=imm, imm_hex=hex(imm), count=len(sites),
                sites=[hex(s) for s in sites],
                buckets=buckets, sum_buckets=sum(buckets.values()),
                raw_kind_buckets=rawb, sum_raw=sum(rawb.values()),
                rows=rows)


def controls():
    sa = C.find_push_imm_sites(pe, 0x7f7c81)
    base = C.find_push_imm_sites(pe, 0x7f7c80)
    b = []
    for s in base:
        o = pe.off_va(s + 1)
        if pe.buf[o] == 0x68:
            b.append(hex(s + 1))
    # extra control: 0x7f7c80 as a *non-push* imm (e.g. any 4-byte occurrence)
    occ = []
    pat = struct.pack('<I', 0x7f7c80)
    i = 0
    while True:
        j = pe.buf.find(pat, i)
        if j < 0:
            break
        occ.append(j)
        i = j + 1
    return dict(ctrl_5a=dict(rule='0x68 + u32 == 0x7f7c81', count=len(sa), addrs=[hex(x) for x in sa]),
                ctrl_5b=dict(rule='byte at site+1 == 0x68', count=len(b), addrs=b),
                extra_u32_occurrences_all_file=len(occ))


def by_func(rows):
    g = {}
    for r in rows:
        g.setdefault(r['func_start_hex'], []).append(r['site_hex'])
    return {k: dict(n=len(v), sites=v) for k, v in g.items()}


q = analyze(0x7f7c80)
pos = analyze(0x7f7c90)
out = dict(
    target=hex(0x7f7c80),
    pe=dict(e_lfanew=hex(pe.e_lfanew), machine=hex(pe.machine), nsec=pe.nsec,
            image_base=hex(pe.image_base), size_of_image=hex(pe.size_of_image), ndirs=pe.ndirs,
            sections=[dict(name=s['name'], va=hex(s['va']), vsize=hex(s['vsize']),
                           raw=hex(s['raw']), rawsize=hex(s['rawsize'])) for s in pe.sections],
            iat_slots=len(pe.iat), iat_dlls=sorted(set(d for d, n, v in pe.imports)),
            ole32_imports=sorted((n, hex(s)) for d, n, s in pe.imports if d == 'ole32.dll'),
            bytes_at_7f7c80=pe.read_va(0x7f7c80, 16).hex(),
            bytes_at_7f7c90=pe.read_va(0x7f7c90, 16).hex()),
    q1_main=q, q1_posctrl=pos, controls=controls(),
    funcs_of_main=by_func(q['rows']),
    identical_distribution=(q['buckets'] == pos['buckets']),
    identical_count=(q['count'] == pos['count']),
)
json.dump(out, open('_r121/x121exec_q1.json', 'w'), indent=1)

print('== Q1 main 0x7f7c80: sites=%d' % q['count'])
for k, v in sorted(q['buckets'].items(), key=lambda x: -x[1]):
    print('   %-52s %d' % (k, v))
print('   sum=%d (== sites: %s)' % (q['sum_buckets'], q['sum_buckets'] == q['count']))
print('   raw kinds:')
for k, v in sorted(q['raw_kind_buckets'].items(), key=lambda x: -x[1]):
    print('   %-52s %d' % (k, v))
print('== posctrl 0x7f7c90: sites=%d' % pos['count'])
for k, v in sorted(pos['buckets'].items(), key=lambda x: -x[1]):
    print('   %-52s %d' % (k, v))
print('== controls:', json.dumps(out['controls']))
print('== funcs:', len(out['funcs_of_main']))
for k, v in out['funcs_of_main'].items():
    print('   %s n=%d' % (k, v['n']))
print('== identical dist:', out['identical_distribution'], 'count:', out['identical_count'])
