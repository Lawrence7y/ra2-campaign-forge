# -*- coding: utf-8 -*-
"""w1: ② 全部持有表枚举（全镜像 4 对齐原始命中 → 反推 vtable → COL→TD+8 RTTI，fail-closed）。
不依赖 function_atlas entry+size（纪律 1）。双通道之一：原始字节命中先验指令边界。"""
import os,sys,json,struct
sys.path.insert(0,os.path.dirname(__file__))
import ax_lib

ROWS = ["005F9720","00709A40","006F3F40","006F6CA0","006F4A70","00711F00","0070E2B0","0040BA50"]

def is_code(pe,v): return v is not None and pe.is_code(v)
def table_like(pe,v): return v==0 or is_code(pe,v)
def valid_col(pe,v):
    if v is None or not pe.is_data(v): return False
    if pe.u32(v)!=0: return False
    td=pe.u32(v+0xC)
    if td is None or not pe.is_mapped(td): return False
    nm=pe.cstr(td+8,16)
    return bool(nm) and (nm.startswith('.?AV') or nm.startswith('.?AU'))
def vt_start(pe,x):
    s=x; steps=0
    while steps<4096:
        prev=s-4; pv=pe.u32(prev)
        if pv is None: return None
        if valid_col(pe,pv): return s
        if not table_like(pe,pv): return None
        s=prev; steps+=1
    return None
def raw_hits(pe,entry):
    needle=struct.pack('<I',entry); hits=[]
    for s in pe.secs:
        lo=s['va']; hi=s['va']+min(s['vsize'],s['rawsize']); off=pe.off(lo)
        if off is None: continue
        blob=pe.buf[off:off+(hi-lo)]; start=0
        while True:
            i=blob.find(needle,start)
            if i<0: break
            if i%4==0: hits.append(lo+i)
            start=i+1
    return sorted(hits)

def main():
    pe=ax_lib.load()
    # 全表枚举自校验
    tabs={}; lo,hi=pe.rdata; va=lo
    while va<hi:
        if va-4>=pe.image_base:
            pv=pe.u32(va-4)
            if valid_col(pe,pv) and is_code(pe,pe.u32(va)):
                n=0
                while n<2000:
                    v=pe.u32(va+4*n)
                    if not table_like(pe,v): break
                    n+=1
                tabs[va]=dict(col=pv,n=n)
        va+=4
    out={'sha':pe.sha,'n_tables':len(tabs),'n_slots':sum(t['n'] for t in tabs.values()),'rows':[]}
    for ent in ROWS:
        e=int(ent,16); hits=raw_hits(pe,e); holders=[]; nonvt=[]
        for h in hits:
            s=vt_start(pe,h)
            if s is None: nonvt.append('%08X'%h); continue
            r=ax_lib.rtti_of_table(pe,s)
            if r is None: nonvt.append('%08X!rtti'%h); continue
            slot=(h-s)//4
            holders.append(dict(vt='%08X'%s,slot=slot,name=r['name'],col='%08X'%r['col'],td='%08X'%r['td'],
                                slot_ok=(pe.u32(s+4*slot)==e),tabsz=tabs.get(s,{}).get('n')))
        slots=sorted({x['slot'] for x in holders})
        out['rows'].append(dict(entry=ent,n_raw=len(hits),holders=holders,nonvt=nonvt,slots=slots))
        print("\n== %s raw=%d holders=%d slots=%s nonvt=%s"%(ent,len(hits),len(holders),slots,nonvt))
        for x in holders:
            print("   vt=%s slot=%-4d %-34s col=%s slot_ok=%s"%(x['vt'],x['slot'],x['name'],x['col'],x['slot_ok']))
    json.dump(out,open(os.path.join(os.path.dirname(__file__),'holders.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print("\n[selfcheck] tables=%d slots=%d"%(len(tabs),sum(t['n'] for t in tabs.values())))

if __name__=='__main__': main()
