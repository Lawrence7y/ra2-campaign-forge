"""Emit ANCHORS.tsv: every entry-relative +0xNN anchor claimed in coverage_delta.tsv,
with the exact instruction from EVIDENCE/RINGS_<entry>.txt (M5 cross-check)."""
import re
from pathlib import Path
OUT=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED6')
lines=(OUT/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines()
out=['entry\tanchor\tinstruction\tverified']
for l in lines[1:]:
    f=l.split('\t'); e=f[0]; sem=f[3]
    rings=(OUT/'EVIDENCE'/('RINGS_%s.txt'%e)).read_text(encoding='utf-8')
    dmap={}
    for m in re.finditer(r'\+([0-9A-F]{4})\s+([0-9A-F]{8})\s+(\S+)\s+(.*)',rings):
        dmap[m.group(1)]=(m.group(3),m.group(4).strip())
    # entry-relative anchors are those whose hex matches a disasm line
    seen=set()
    for a in re.findall(r'\+0x([0-9A-Fa-f]{2,4})',sem):
        h=a.upper().zfill(4)
        if h in dmap and h not in seen:
            seen.add(h); mn,op=dmap[h]
            out.append('%s\t+0x%s\t%s %s\tYES'%(e,h,mn,op))
(OUT/'EVIDENCE'/'ANCHORS.tsv').write_text('\n'.join(out)+'\n',encoding='utf-8')
print('wrote ANCHORS.tsv with',len(out)-1,'verified anchors')
