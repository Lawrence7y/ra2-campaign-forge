# -*- coding: utf-8 -*-
import json, sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_SLOTN_B3")
from verify import Image, EXE, body_range, decode_at, find_install_sites, func_ok

img = Image(EXE)

# 行 36 entry 005B4630 自身函数体是否含装表点 005B4639
br = body_range(img, 0x005B4630)
print("body(005B4630) =", ["0x%08X" % x for x in br] if br else None)
print("005B4639 in own body:", bool(br and br[0] <= 0x005B4639 < br[1]))
i = decode_at(img, 0x005B4639)
print("005B4639:", i.mnemonic, i.op_str if i else None)

# 逐行关键事实
res = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_SLOTN_B3\verify_out.json",
                     encoding="utf-8"))
print("\n# n entry name slot vt site func covline cov4len applen covtail appendhead cov4_has4 grade_ok")
for r in res["rows"]:
    a = r["A"]
    print("#", r["n"], r["entry"], r["name"], r["slot_no"], r.get("vt"), r.get("site"),
          r.get("func_text"), a["cov_line"], a["cov4_len"], a["appended_len"],
          repr(a["cov4_tail_char"]), repr(a["append_head"]),
          a["cov4_already_has_ring4"], a["col5_grade_ok"],
          "funcbody=%s" % (r["aux_func"]["body"],))
