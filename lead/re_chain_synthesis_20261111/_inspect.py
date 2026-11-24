import os
import re

scripts = [
    r"D:\Project\ra2-campaign-forge\lead\re_crashwriter_static_20261110\_cw_disasm.py",
    r"D:\Project\ra2-campaign-forge\lead\slot2_fullscan_20261111\_sf_scan.py",
    r"D:\Project\ra2-campaign-forge\lead\playerctrl_semantics_20261111\_ps_disasm.py",
    r"D:\Project\ra2-campaign-forge\lead\re_orphan_owners_20261110\_oo_disasm.py",
    r"D:\Project\ra2-campaign-forge\lead\re_orphan_owners_20261110\_oo_map.py",
    r"D:\Project\ra2-campaign-forge\lead\re_map_preset_decode_20261110\_md_parse.py",
    r"D:\Project\ra2-campaign-forge\lead\re_loadbench_diff_20261110\_ld_diff.py",
]

for s in scripts:
    print("===", os.path.basename(s), "in", os.path.dirname(s))
    with open(s, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    for m in re.finditer(r'(open\(.*?[,\)].*?[\'"]w[\'"].*?\)|write_text\([^)]+\))', content):
        print("  Write:", m.group(0))
