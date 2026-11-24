#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find cells with InfantryClass nodes on +0xE4 chain; report cell coords, owner, layer, count.
Read-only. Usage: find_inf_cells.py [maxn]
"""
import sys, ctypes
import w177_core as W
import wb_probe as P
import dsnap as D

def main():
    maxn = int(sys.argv[1]) if len(sys.argv)>1 else 40
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    base=m.u32(P.CELL_ARRAY); mapc=P.MAP_SINGLETON
    w=m.u32(mapc+0x14C); h=m.u32(mapc+0x150)
    out=[]
    for cy in range(h):
        rb=base+((cy<<9))*4; buf=ctypes.create_string_buffer(w*4); got=ctypes.c_size_t(0)
        if not W.k32.ReadProcessMemory(m.h,ctypes.c_void_p(rb),buf,w*4,ctypes.byref(got)):continue
        for cx in range(w):
            cell=int.from_bytes(buf.raw[cx*4:cx*4+4],'little')
            if not cell or cell==P.INVALID_CELL:continue
            head=m.u32(cell+0xE4); nodes=[]; seen=set(); p=head
            while p and p not in seen and len(nodes)<12:
                seen.add(p)
                nm,_=D.rtti_name(m,p)
                owner=m.u32(p+0x21C)
                layer=m.u32(p+0x94)
                if nm and 'InfantryClass' in nm:
                    nodes.append({'this':hex(p),'owner':hex(owner),'layer':layer})
                p=m.u32(p+0x30)
            if nodes:
                out.append({'cell':[cx,cy],'n_inf':len(nodes),'nodes':nodes,'is_player':any(n['owner']==hex(ph) for n in nodes)})
    player=[o for o in out if o['is_player']]
    print('total cells with inf',len(out),'player-owned',len(player))
    for o in player[:maxn]:
        print(o['cell'],'n_inf',o['n_inf'],[(n['this'],n['layer']) for n in o['nodes']])
    m.close()

if __name__=='__main__':main()
