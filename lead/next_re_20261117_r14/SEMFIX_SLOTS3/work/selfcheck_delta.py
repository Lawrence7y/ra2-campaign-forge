# contract self-check for coverage_delta.tsv
import io
F = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_SLOTS3\coverage_delta.tsv"
rows = [l.rstrip("\n").split("\t") for l in io.open(F,encoding="utf-8").read().splitlines()]
hdr, data = rows[0], rows[1:]
errs = []
if hdr != ["entry","subsystem","name","one_line_semantics","grade","evidence_path"]:
    errs.append("bad header: %r"%hdr)
if len(data)!=15: errs.append("row count %d != 15"%len(data))
for r in data:
    if len(r)!=6: errs.append("%s cols=%d"%(r[0],len(r))); continue
    e,s,n,sem,g,ev = r
    for tok in ["未证","未定","弱信号","线索","（槽语义未证）","槽语义未证"]:
        if tok in sem: errs.append("%s has forbidden token %s"%(e,tok))
    if g!="[已证]": errs.append("%s grade %s"%(e,g))
    if "③b" not in sem: errs.append("%s no ③b"%e)
    if "+0x" not in sem: errs.append("%s no +0x anchor"%e)
    if "EVIDENCE/ROW_%s.txt"%e not in ev: errs.append("%s bad evidence path"%e)
entries = [r[0] for r in data]
if len(set(entries))!=len(entries): errs.append("duplicate entries")
s05 = [r[0] for r in data if r[1]=="S05"]
s09 = [r[0] for r in data if r[1]=="S09"]
if len(s05)!=7: errs.append("S05 count %d != 7"%len(s05))
if len(s09)!=8: errs.append("S09 count %d != 8"%len(s09))
if "00704350" in entries: errs.append("00704350 must be excluded")
slots2 = set("0047AE10 0065CDD0 0065D0D0 0065D190 004D82B0 004D5690 004DB260 00702D40 00706640 00708C30 004D94B0".split())
if slots2 & set(entries): errs.append("overlap with SLOTS2: %s"%(slots2&set(entries)))
exp = set("006F3330 006F8DF0 006FC0B0 006FFEC0 0070BF50 00712170 00716150 006D0270 006D04F0 00653850 004F4480 004A8960 006C6680 004F4320 006AC210".split())
if set(entries)!=exp: errs.append("entry set mismatch: missing %s extra %s"%(exp-set(entries),set(entries)-exp))
# name base-class corrections
namemap = {r[0]:r[2] for r in data}
for e,want in {"006F3330":"TechnoClass::slot185","006FC0B0":"TechnoClass::slot240","00716150":"TechnoTypeClass::slot42"}.items():
    if namemap.get(e)!=want: errs.append("name %s=%s != %s"%(e,namemap.get(e),want))
print("rows=%d s05=%d s09=%d"%(len(data),len(s05),len(s09)))
print("forbidden-token check: PASS" if not any("forbidden" in e for e in errs) else "FAIL")
if errs:
    print("ERRORS:"); [print(" -",e) for e in errs]
else:
    print("ALL CHECKS PASS")
