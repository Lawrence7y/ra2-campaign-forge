#!/usr/bin/env python3
"""Patch final_audit.py to the post-Swizzle-fix numbers and add the entry-table check."""
import io

p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W131_subsystems\final_audit.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('check("coverage.assigned == 5497", smap["coverage"]["assigned"] == 5497,',
              'check("coverage.assigned == 5493", smap["coverage"]["assigned"] == 5493,')
s = s.replace('smap["coverage"]["assigned_bytes"] == 2091344,',
              'smap["coverage"]["assigned_bytes"] == 2089876,')
s = s.replace('check("coverage.assigned_bytes == 2091344",',
              'check("coverage.assigned_bytes == 2089876",')

anchor = ('check("subsystem count == 26", len(smap["subsystems"]) == 26,\n'
          '      "got %d" % len(smap["subsystems"]))')
add = (anchor + '\n'
       'n_ent = tsv_rows(os.path.join(HERE, "subsystem_entries.tsv"))\n'
       'check("subsystem_entries rows >= 20", n_ent >= 20, "got %d" % n_ent)')
if anchor in s and "subsystem_entries rows" not in s:
    s = s.replace(anchor, add)

# also grade the new sections
s = s.replace('"§855", "§856"):', '"§855", "§856", "§857", "§858"):')

io.open(p, "w", encoding="utf-8").write(s)
print("patched final_audit.py")
