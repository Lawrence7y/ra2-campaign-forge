# -*- coding: utf-8 -*-
"""R16-D1-WIDE-B2 authoritative raw derive (read-only gamemd.exe / writes only this dir).

Method follows R16_D1_WIDE_B1/derive_raw.py + R16_D1_FINAL/generate.py (the D1 precedent),
with card §3.4 applied: where final.tsv's decisive table class != row-name class,
re-select the row-name class's OWN live table (class-consistency-first) and flag CLASS_FIX.

Table enumeration is NOT re-implemented: it imports R16_PROBE_4FINAL.final (read-only at
import; has an if-__name__ guard), the same authoritative enumerator that produced final.tsv.
"""
import io, os, sys, re, json, bisect, collections, hashlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, "R16_PROBE_4FINAL")
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
sys.path.insert(0, PROBE)
import final as F   # authoritative table enumerator; no writes at import

import capstone

IB = F.IMAGE_BASE

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

TARGETS = ['0046C890','00473B10','004A2990','004A8960','004A9840','004AAD30',
           '004AAE90','004AB9B0','004D7330','004D94B0','004DFB70','004F4320',
           '004F4480','0051D6F0','00523340','0054E890','0054EA70','005B3970']
# row-name class (text before ::) from coverage.tsv name column
NAMECLS = {
 '0046C890':'BulletTypeClass','00473B10':'CCFileClass','004A2990':'CStreamClass',
 '004A8960':'TabClass','004A9840':'TabClass','004AAD30':'TabClass',
 '004AAE90':'TabClass','004AB9B0':'DisplayClass','004D7330':'FootClass',
 '004D94B0':'FootClass','004DFB70':'AircraftClass','004F4320':'MouseClass',
 '004F4480':'MouseClass','0051D6F0':'InfantryClass','00523340':'InfantryClass',
 '0054E890':'T_DynamicVectorClass_PAUKamikazeControl__',
 '0054EA70':'T_DynamicVectorClass_PAUKamikazeControl__','005B3970':'MissionClass'}

# ---- image / atlas / tables (read-only)
img = F.Image(EXE)
text = F.Text(img)
atlas = F.load_atlas()
starts = sorted(atlas)
sizes = [atlas[s] for s in starts]
tabs = F.enumerate_tables(img)
stop = set(tabs)
for vt in tabs:
    tabs[vt]['n_slots'] = F.table_len(img, vt, stop)
installs = {vt: list(text.stores[vt]) for vt in tabs if text.stores.get(vt)}
holdings = collections.defaultdict(list)
for vt, t in tabs.items():
    for k in range(t['n_slots']):
        v = img.u32(vt + k * 4)
        if v is not None and F.TEXT_LO <= v < F.TEXT_HI:
            holdings[v].append((vt, k))

def host_of(site):
    i = bisect.bisect_right(starts, site) - 1
    if i >= 0 and starts[i] <= site < starts[i] + sizes[i]:
        return starts[i], True
    return None, False

def ext_sites(ei, vt):
    sz = atlas.get(ei)
    body = (ei, ei + sz) if sz else None
    out = []
    for s, _d in installs.get(vt, []):
        if body and body[0] <= s < body[1]:
            continue
        out.append(s)
    return out

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def host_capstone(site):
    """B1 precedent: when site not in atlas, find function start by scanning back for
    the last ret before site, then the first real insn after it."""
    lo, hi = site - 0x100, site + 0x40
    insns = list(md.disasm(bytes(img.buf[lo - IB:hi - IB]), lo))
    prev = None
    for ins in insns:
        if ins.address < site and ins.mnemonic in ("ret", "retf"):
            prev = ins
    if prev:
        for ins in insns:
            if ins.address > prev.address and ins.mnemonic not in ("nop", "int3"):
                return ins.address
    return None

def disasm_at(va, n=24):
    o = va - IB
    out = []
    for ins in md.disasm(bytes(img.buf[o:o + n]), va):
        out.append("%s %s" % (ins.mnemonic, ins.op_str))
    return out

# final.tsv (authoritative D1 decisive table)
with io.open(os.path.join(PROBE, 'final.tsv'), encoding='utf-8-sig') as f:
    fmap = {}
    hdr = f.readline().rstrip('\r\n').split('\t')
    for ln in f:
        c = ln.rstrip('\r\n').split('\t')
        if len(c) >= len(hdr):
            fmap[c[0]] = dict(zip(hdr, c))

recs = []
for e in TARGETS:
    ei = int(e, 16)
    fr = fmap.get(e)
    if not fr:
        recs.append(dict(entry=e, error="not_in_final")); continue
    dec_vt = int(fr['vt'], 16)
    dec_slot = int(fr['slot'])
    dec_cls = tabs[dec_vt]['cls'] if dec_vt in tabs else None
    nc = NAMECLS[e]
    # class-consistency test: exact .?AV<NC>@@ or template/pseudo-name token match (B1 0040F870口径)
    dec_ok = (dec_cls == '.?AV%s@@' % nc) or bool(F.col_match_of(nc, dec_cls))
    class_fix = (not dec_ok)
    chosen_vt, chosen_slot = dec_vt, dec_slot
    sel_reason = None
    if class_fix:
        cands = []
        for vt, k in holdings.get(ei, []):
            t = tabs[vt]
            if t['cls'] != '.?AV%s@@' % nc:   # strict exact row-name-class table
                continue
            if img.u32(t['col'] + 4) != 0:     # primary table (offset 0)
                continue
            es = ext_sites(ei, vt)
            if not es:                          # must be a LIVE table w/ external install site
                continue
            cands.append((vt, k, es[0]))
        cands.sort()
        if not cands:
            recs.append(dict(entry=e, error="no_class_consistent_live_table",
                             dec_vt='%08X' % dec_vt, dec_cls=dec_cls, name_cls=nc))
            continue
        chosen_vt, chosen_slot, _site0 = cands[0]
        sel_reason = ("final.tsv 决定性表 vt=%08X 的 RTTI 类 %s 与行名类 %s 不符（违反纪律7）；"
                      "按卡面 §3.4 类一致优先，另取行名类自己的活表 vt=%08X 同槽 slot%d"
                      % (dec_vt, dec_cls, nc, chosen_vt, chosen_slot))
    # derive all fields from chosen table
    t = tabs[chosen_vt]
    col = t['col']
    coff = img.u32(col + 4)
    td = img.u32(col + 12)
    mg = img.cstr(td + 8) if td else None
    slot_val = img.u32(chosen_vt + chosen_slot * 4)
    # install site: first external site of chosen table
    es = ext_sites(ei, chosen_vt)
    if not es:
        recs.append(dict(entry=e, error="no_external_install_site", vt='%08X' % chosen_vt))
        continue
    site = es[0]
    insns = disasm_at(site, 24)
    ins = insns[0] if insns else "?"
    om = re.search(r"\[([^\]]+)\]", ins)
    op = om.group(1).strip() if om else ""
    host, in_atlas = host_of(site)
    if not in_atlas:
        cap_host = host_capstone(site)
        if cap_host:
            host = cap_host
    chk = [
        slot_val == ei,
        img.u32(col) == 0,
        coff == 0,
        td is not None and (mg or "").startswith(".?A"),
        not (ei <= site < ei + atlas.get(ei, 0)),
        chosen_vt is not None,
    ]
    recs.append(dict(
        entry=e, name=fr['name'], sub=fr['subsystem'], grade=fr['grade'],
        vt="%08X" % chosen_vt, slot=chosen_slot, site="%08X" % site,
        col=("%08X" % col) if col is not None else "未取得",
        coff=coff, td=("%08X" % td) if td is not None else "未取得",
        mg=mg or "未取得",
        host=("%08X" % host) if host else "未取得",
        in_atlas=in_atlas, ins=ins, insns=insns[:4], op=op,
        slot_val=("%08X" % slot_val) if slot_val is not None else "未取得",
        chk6=all(chk), chk=chk, note=fr.get('note', ''),
        class_fix=class_fix, name_cls=nc,
        dec_vt=("%08X" % dec_vt), dec_slot=dec_slot, dec_cls=dec_cls or "未取得",
        sel_reason=sel_reason, n_hold=len(holdings.get(ei, [])),
        n_exact_hold=sum(1 for v, _k in holdings.get(ei, []) if tabs[v]['cls'] == '.?AV%s@@' % nc),
    ))

dump = dict(exe_sha=sha256(EXE),
            cov_sha=sha256(COV), cov_bytes=os.path.getsize(COV),
            tables=len(tabs), slots=sum(t['n_slots'] for t in tabs.values()),
            recs=recs)
io.open(os.path.join(HERE, "raw_dump.json"), "w", encoding="utf-8").write(
    json.dumps(dump, ensure_ascii=False, indent=1))
print("wrote raw_dump.json tables=%d slots=%d" % (len(tabs), sum(t['n_slots'] for t in tabs.values())))
for x in recs:
    if "error" in x:
        print(x["entry"], "ERROR", x["error"]); continue
    print("%s CF=%s vt=%s slot=%d site=%s col=%s coff=%s td=%s mg=%s host=%s op=[%s] ins='%s' slotval=%s chk=%s" % (
        x["entry"], x["class_fix"], x["vt"], x["slot"], x["site"], x["col"], x["coff"], x["td"], x["mg"],
        x["host"], x["op"], x["ins"], x["slot_val"], x["chk"]))
