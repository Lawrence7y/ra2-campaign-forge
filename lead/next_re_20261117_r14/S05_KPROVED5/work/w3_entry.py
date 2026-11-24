# -*- coding: utf-8 -*-
"""w3: ① 入口形态 —— 16B 对齐 + 前驱 ret/nop/int3 或 thunk 序言。"""
import os,sys,json
sys.path.insert(0,os.path.dirname(__file__))
import ax_lib
from capstone import *
ROWS=["005F9720","00709A40","006F3F40","006F6CA0","006F4A70","00711F00","0070E2B0","0040BA50"]
pe=ax_lib.load(); MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
out={}
for e in ROWS:
    ent=int(e,16)
    aligned = (ent%16==0)
    # 反解前 16 字节
    st=ent-16; raw=pe.bytes_at(st,16)
    pred=list(MD.disasm(raw,st))
    predtxt='; '.join('%X:%s %s'%(i.address,i.mnemonic,i.op_str) for i in pred)
    head=pe.bytes_at(ent,12)
    headins=list(MD.disasm(head,ent))
    headtxt='; '.join('%s %s'%(i.mnemonic,i.op_str) for i in headins[:3])
    lastpred=pred[-1].mnemonic if pred else '?'
    ok = aligned and lastpred in ('ret','retf','nop','int3','jmp')
    out[e]=dict(aligned=aligned,pred=predtxt,pred_last=lastpred,head=headtxt,ok=ok,
                head_bytes=head[:8].hex())
    print("%s align=%s pred_last=%s ok=%s head=[%s]"%(e,aligned,lastpred,ok,headtxt))
json.dump(out,open(os.path.join(os.path.dirname(__file__),'entry.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
