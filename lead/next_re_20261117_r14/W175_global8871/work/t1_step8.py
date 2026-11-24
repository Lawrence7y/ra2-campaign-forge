"""Task 1 step 8: final raw string search for RulesClass / rules.cpp; build definitive id evidence."""
import sys, os, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

# raw search all sections for 'RulesClass','rules.cpp','Rules.CPP'
P("=== raw 'RulesClass' / 'rules.cpp' strings in all sections ===")
for s in BIN.sections:
    buf=BIN.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    for needle in [b"RulesClass", b"rules.CPP", b"Rules.CPP", b"rules.cpp", b"RULES.INI", b"Rule"]:
        i=0
        while True:
            j=buf.find(needle,i)
            if j<0: break
            ctx=buf[max(0,j-30):j+60].split(b"\x00")[0]
            P("  [%s] %08X needle=%r ctx=%r"%(s["name"],s["va"]+j,needle,ctx))
            i=j+1

# source file strings in ctor 0x665650 and dtor 0x667a30 region
P("\n=== printable strings referenced within ctor/dtor range (source paths) ===")
for va_range in [(0x665650,0x667a27),(0x667a30,0x667d00)]:
    d=BIN.read(va_range[0],va_range[1]-va_range[0])
    for mt in re.finditer(rb"[ -~]{8,}",d):
        st=mt.group()
        if b"\\" in st or b".CPP" in st.upper() or b".H" in st:
            P("  %08X  %r"%(va_range[0]+mt.start(),st[:90]))

with open(EVID+r"\t1_rulesclass_strings.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("\n".join(out[:60]))
