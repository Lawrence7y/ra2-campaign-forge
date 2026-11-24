#!/usr/bin/env python3
"""T3 step 1: RTTI TypeDescriptor enumeration + vtable discovery for target classes."""
import sys, os, re, struct
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())

# --- enumerate TypeDescriptors by scanning .data for '.?AV' mangled names ---
p("=== TypeDescriptor name scan (.data/.rdata) ===")
td_by_name={}
for (sec,va,vs,pr,rs,ch) in sections():
    if sec not in ('.data','.rdata'): continue
    blob=read(va,vs)
    for m in re.finditer(rb'\.\?AV([A-Za-z0-9_]+)@@', blob):
        name=m.group(1).decode('latin1')
        name_va=va+m.start()
        td_va=name_va-8  # TD+8 = name
        td_by_name.setdefault(name,[]).append(td_va)
for target in ['CDFileClass','BufferIOFileClass','RawFileClass','CCFileClass','MixFileClass','FileClass','VirtualFileClass']:
    tds=td_by_name.get(target,[])
    p(f"  {target}: TDs={[hex(x) for x in tds]}")

# --- scan .rdata for COLs that point to those TDs (COL+0xC = TD) ---
def find_cols_for(td):
    cols=[]
    for (sec,va,vs,pr,rs,ch) in sections():
        if sec not in ('.data','.rdata'): continue
        blob=read(va,vs)
        pat=struct.pack('<I',td)
        idx=0
        while True:
            i=blob.find(pat,idx)
            if i<0: break
            colva=va+i-0xC
            cols.append(colva)
            idx=i+1
    return cols

# --- find vtables: scan entire image for dword == COL, vtable = addr+4 ---
def find_vfts_for(col):
    vfts=[]
    pat=struct.pack('<I',col)
    for (sec,va,vs,pr,rs,ch) in sections():
        blob=read(va,vs)
        idx=0
        while True:
            i=blob.find(pat,idx)
            if i<0: break
            vft=va+i+4
            vfts.append(vft)
            idx=i+1
    return vfts

for cls in ['BufferIOFileClass','RawFileClass','CDFileClass','CCFileClass','MixFileClass']:
    tds=td_by_name.get(cls,[])
    p(f"\n### {cls}")
    for td in tds:
        cols=find_cols_for(td)
        p(f"  TD={td:08X} COLs={[hex(x) for x in cols]}")
        for col in cols:
            vfts=find_vfts_for(col)
            p(f"    COL={col:08X} vft[-1] hits (vtable starts)={[hex(x) for x in vfts]}")

# --- known anchors: which vtable contains 0x401950 / 0x401940 / 0x431B80 / 0x65CA00 ? ---
p("\n=== anchors: scan .rdata dwords == target funcs ===")
for fn in [0x401940,0x401950,0x431B20,0x431B80,0x65CA00,0x4739F0,0x5B3C20]:
    pat=struct.pack('<I',fn)
    hits=[]
    for (sec,va,vs,pr,rs,ch) in sections():
        if sec not in ('.rdata','.data'): continue
        blob=read(va,vs)
        idx=0
        while True:
            i=blob.find(pat,idx)
            if i<0: break
            hits.append((va+i,sec))
            idx=i+1
    p(f"  func {fn:08X}: hits={[(hex(a),s) for a,s in hits]}")

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T3_rtti_discovery.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T3_rtti_discovery.txt]")
