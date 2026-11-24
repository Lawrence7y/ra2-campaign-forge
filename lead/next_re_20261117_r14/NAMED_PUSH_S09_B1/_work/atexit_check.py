# -*- coding: utf-8 -*-
"""核对 atexit 注册（㉓）：给定函数名 VA，检查是否 push <VA>; call 0x7C978A。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

ATEXIT=0x7C978A
def check(func_va, window=0x80):
    needle=b"\x68"+struct.pack("<I",func_va)  # push imm32
    hits=[]
    data=R.TEXT_DATA
    v0=R.TEXT_VA
    st=0
    while True:
        i=data.find(needle,st)
        if i<0: break
        pushva=v0+i
        for j in range(i+5,min(i+5+window,len(data)-5)):
            if data[j]==0xE8:
                rel=struct.unpack_from("<i",data,j+1)[0]
                if (v0+j+5+rel)&0xFFFFFFFF==ATEXIT:
                    hits.append((pushva, v0+j))
                    break
        st=i+1
    return hits

for va in [0x40D290,0x5BDA40,0x4882D0,0x4886E0,0x4B55F0,0x4E2830,0x4F38,0x6A9DD30]:
    h=check(va)
    print("atexit-registered %08X : %s" % (va, [("push@%08X"%a, "call@%08X"%b) for a,b in h]))
