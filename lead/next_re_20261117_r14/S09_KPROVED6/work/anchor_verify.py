"""Verify each claimed +0xNN anchor's INSTRUCTION matches the semantics description."""
import re
from pathlib import Path
OUT=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED6')
lines=(OUT/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines()
out=['entry\tclaimed_anchor\tclaimed_desc\tactual_instruction']
for l in lines[1:]:
    f=l.split('\t'); e=f[0]; sem=f[3]
    rings=(OUT/'EVIDENCE'/('RINGS_%s.txt'%e)).read_text(encoding='utf-8')
    dmap={}
    for m in re.finditer(r'\+([0-9A-F]{4})\s+([0-9A-F]{8})\s+(\S+)\s+(.*)',rings):
        dmap[m.group(1).upper()]=(m.group(3)+' '+m.group(4).strip())
    # find anchor+desc patterns like "+0x0A mov eax,80004003" (allow short hex)
    for m in re.finditer(r'\+0x([0-9A-Fa-f]{2,4})\s+([^、；，,；）]+?)(?=[、；，）]|$)',sem):
        a=m.group(1).upper().zfill(4); desc=m.group(2).strip()
        actual=dmap.get(a,'<<NO DISASM>>')
        out.append('%s\t+0x%s\t%s\t%s'%(e,a,desc,actual))
(OUT/'work'/'anchor_verify.txt').write_text('\n'.join(out)+'\n',encoding='utf-8')
print('wrote',len(out)-1,'anchor checks')
