# -*- coding: utf-8 -*-
"""S05-KPROVED4 · ④ 直接调用站点验证（全 .text skipdata 重扫，指令边界 E8）。
四条件：E8 边界 / site+5+rel32==entry / 站点在函数体外 / 非自环。
不依赖 atlas entry+size：函数体外判定用本卡 CFG extent（自写）。"""
import json,struct,capstone,ax_lib

ROWS=["00704350","006FFBE0","00703860","005F9950","006F3F40","006F6CA0","005F9720","007171A0"]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
md.skipdata=True; md.detail=False

def extent(pe,e,n=0x6000):
    """自写 CFG 近似 extent：从入口线性反汇编到 ret 后填充。"""
    code=pe.bytes_at(e,n); end=e
    for i in md.disasm(code,e):
        end=i.address+i.size
        if i.mnemonic in ('ret','retf') and i.address>e:
            tail=pe.bytes_at(end,16) or b''
            if sum(1 for b in tail[:8] if b in (0xCC,0x90))>=5: break
    return end

def scan_text(pe):
    """全 .text 指令边界 E8 站点 -> [(site, target)]。"""
    lo,hi=pe.text
    code=pe.bytes_at(lo,hi-lo)
    sites=[]
    for i in md.disasm(code,lo):
        if i.mnemonic=='call' and i.size==5:
            raw=bytes(i.bytes)
            if raw[0]==0xE8:
                rel=struct.unpack('<i',raw[1:5])[0]
                sites.append((i.address,i.address+5+rel))
    return sites

if __name__=='__main__':
    pe=ax_lib.load()
    print('[scan] .text span',hex(pe.text[0]),hex(pe.text[1]),'bytes',pe.text[1]-pe.text[0])
    sites=scan_text(pe)
    print('[scan] instruction-boundary E8 call sites =',len(sites))
    extents={r:extent(pe,int(r,16)) for r in ROWS}
    out={'n_e8_boundary':len(sites),'rows':{}}
    for r in ROWS:
        e=int(r,16); ex=extents[r]
        hits=[(s,t) for (s,t) in sites if t==e]
        valid=[]; invalid=[]
        for s,t in hits:
            inside = e<=s<ex
            selfloop = s==e
            if (not inside) and (not selfloop):
                valid.append(s)
            else:
                invalid.append((s,'inside' if inside else 'self'))
        out['rows'][r]=dict(extent=hex(ex),n_hits=len(hits),
                            valid_sites=['%08X'%s for s in valid],
                            invalid=[[('%08X'%s),why] for s,why in invalid])
        print('%s extent=%s E8-hits=%d valid=%d sites=%s' % (r,hex(ex),len(hits),len(valid),['%08X'%s for s in valid]))
    with open('sites.json','w',encoding='utf-8') as f: json.dump(out,f,indent=1)
