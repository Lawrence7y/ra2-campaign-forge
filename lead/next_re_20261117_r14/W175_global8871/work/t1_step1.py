"""Task 1 step 1: disassemble the 3 write sites and the constructor 0x665650."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from wbase import dump, disasm, fmt, u32

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"

# 1) call site 0x52BA60 (Init) around the call to 0x665650
dump(0x52BA60, 0x260, EVID + r"\t1_callsite_52BA60.txt",
     header="; Init.CPP function 0x52BA60, from 0x52BA60 len 0x260 (skipdata=True)")

# 2) constructor 0x665650: first 0x400 bytes should contain vptr store
dump(0x665650, 0x500, EVID + r"\t1_ctor_665650_head.txt",
     header="; candidate ctor 0x665650 head 0x500 bytes (skipdata=True)")

# 3) cleanup 0x6BE1C0 around the delete/NULL store
dump(0x6BE1C0, 0x1000, EVID + r"\t1_cleanup_6BE1C0.txt",
     header="; cleanup 0x6BE1C0 from 0x6BE1C0 len 0x1000 (skipdata=True)",
     stop_at=0x6BEB00)

print("done")
