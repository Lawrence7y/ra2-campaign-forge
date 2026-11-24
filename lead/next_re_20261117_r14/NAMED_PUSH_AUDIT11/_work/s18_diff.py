import sys, json, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

DELTA = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B3\delta.tsv"
rows_v = {d["entry"]: d for d in json.load(open("verify3.json", encoding="utf-8"))}

lines = [l.rstrip("\n") for l in open(DELTA, encoding="utf-8")]
hdr = lines[0].split("\t")
print("header:", hdr)
bad = 0
for ln in lines[1:]:
    f = ln.split("\t")
    entry, sub, name, sem = f[0], f[1], f[2], f[3]
    d = rows_v[entry]
    t = sem
    print("=" * 110)
    print(f"{entry} {d['expected_class']}  vt={d['vt']} slot#{d['slot_no']}")

    def grab(pat, label, expect):
        m = re.search(pat, t)
        got = None
        if m:
            got = m.group(1)
        ok = None
        if got is not None:
            ok = int(got, 16) == expect if expect is not None else None
        print(f"   {label}: claimed={got} measured={expect:08X if expect else None} ok={ok}")
        return ok

    # guards
    for k, (addr, ops, by) in enumerate(d["guards"]):
        pass
    g1 = int(d["guards"][0][0], 16); g2 = int(d["guards"][1][0], 16); g3 = int(d["guards"][2][0], 16)
    print(f"   guards measured: {g1:08X}(0x80070057) {g2:08X}(0x80040110) {g3:08X}(0x8007000e)")
    print(f"     claimed in text? {hex(g1) in t.lower() or f'{g1:08X}' in t} "
          f"{hex(g2) in t.lower()} {hex(g3) in t.lower()}")

    # vt / slot
    vt = int(d["vt"], 16)
    m = re.search(r"槽 ([0-9A-F]{8})\(vt ([0-9A-F]{8}) \+12", t)
    print(f"   slot claim: {m.groups() if m else None} measured: slot={vt+12:08X} vt={vt:08X}")

    # factory ctor
    inst = int(d["factory_vt_installers"][0], 16)
    fn = inst - 9
    m = re.search(r"ctor ([0-9A-F]{8}) 装 vt", t)
    print(f"   factory ctor claim: {m.group(1) if m else None} measured installer@{inst:08X} fn={fn:08X}")

    # object main vt
    mv = d["obj_main_vt"]["vt"] if d["obj_main_vt"] else None
    m = re.search(r"对象主 vt ([0-9A-F]{8})", t)
    print(f"   object main vt claim: {m.group(1) if m else None} measured={mv} "
          f"slot0={d['obj_main_vt']['slot0'] if d['obj_main_vt'] else None}")

    # QI site / destroy site
    qa = int(d["qi"][0][0], 16)
    da = int(d["destroy"][0][0], 16)
    print(f"   QI@{qa:08X} destroy@{da:08X}  claimed_qi={'%08X' % qa in t} claimed_destroy={'%08X' % da in t}")

    # host
    print(f"   host 006BB9A0 claimed: {'006BB9A0' in t}")

    # RTTI col/td
    col = d["factory_rtti"]["col"]; td = d["factory_rtti"]["td"]
    print(f"   COL={col} TD={td}  claimed_col={col in t} claimed_td={td in t}")

    # jge target
    jge = [x for x in d["test_jge"] if x[1] == "jge"]
    print(f"   jge target={jge[0][2] if jge else None} claimed={'jge '+jge[0][2] if jge else None} "
          f"in_text={bool(jge) and (jge[0][2] in t)}")
