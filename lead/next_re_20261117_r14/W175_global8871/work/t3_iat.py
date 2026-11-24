"""Final small checks: IAT 0x7E14D4 name; A2/A3 moffs byte-channel writes."""
import sys, os, struct, pefile
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

# IAT resolution
pe=BIN.pe
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
P("=== IAT / import resolution for 0x7E14D4 and nearby ===")
target={0x7e14d4:'7E14D4',0x7e14d8:'7E14D8'}
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll=entry.dll.decode(errors='replace')
    for imp in entry.imports:
        if imp.address in target:
            P("  %08X -> %s!%s"%(imp.address,dll,imp.name.decode(errors='replace') if imp.name else hex(imp.ordinal)))

# what string is at 0x849f48
def readable(va,n=80):
    try: b=BIN.read(va,n)
    except Exception: return None
    s=b.split(b'\x00')[0]
    return s if s and all(32<=c<127 for c in s) else None
P("\nstring@0x849F48: %r"%readable(0x849f48))
P("string@0x83AC5C: %r"%readable(0x83ac5c))
P("string@0x83B31C: %r"%readable(0x83b31c))

# A2/A3 moffs byte-channel
P("\n=== BYTE-CHANNEL moffs writes (A2/A3) ===")
for s in BIN.sections:
    buf=BIN.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    for nm,pat in [('A2_A8ED6B',b'\xa2\x6b\xed\xa8\x00'),('A3_B73550',b'\xa3\x50\x35\xb7\x00')]:
        i=0
        while True:
            j=buf.find(pat,i)
            if j<0: break
            P("  %-12s %08X"%(nm,s["va"]+j))
            i=j+1

with open(EVID+r"\t3_iat_moffs.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("\n".join(out))
