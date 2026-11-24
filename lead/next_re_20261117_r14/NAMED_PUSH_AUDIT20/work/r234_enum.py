import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
tables = {0x007F2E58: "Ship", 0x007F50CC: "Teleport", 0x007F6AC4: "Walk"}

for vt, nm in tables.items():
    print("#" * 76)
    print(f"### {nm}  vt {vt:08X}")
    for w in b.writers_of_imm(vt):
        va = w["ins_va"]
        st = b.func_back(va)
        print(f"\n--- write @{va:08X} {w['text']}   in fn {st and hex(st)}")
        body = b.dis(st, 70)
        # classify
        has_del = any(x.mnemonic == "call" and x.op_str.lower() in ("0x7c8b3d", "0x7c8b3c") for x in body)
        has_test1 = any(x.mnemonic == "test" and "byte ptr [esp" in x.op_str and x.op_str.rstrip().endswith(", 1") for x in body)
        ret4 = any(x.mnemonic == "ret" and x.op_str.strip() == "4" for x in body)
        print(f"    classify: call_operator_delete={has_del} test_byte[esp],1={has_test1} ret4={ret4}")
        print(show(body[:34], "    "))
        print(f"    callers: {[hex(x) for x in b.callers_of(st)]}  push-imm: {[hex(x) for x in b.push_sites(st)]}")
