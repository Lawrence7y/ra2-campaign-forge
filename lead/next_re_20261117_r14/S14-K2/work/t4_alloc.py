#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T4 双点闭合第二点: 构造器分配点 push<size> -> operator new。"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W

SIZES = {0x160B8:"HouseClass", 0xA0:"TeamClass", 0x30:"ScriptClass",
         0xD4:"TaskForceClass", 0x110:"AITriggerTypeClass", 0xF8:"TeamTypeClass"}
TARGET = set(SIZES.keys())

def scan_operator_new_calls():
    sites=[]; code=W.DATA[W.TEXT_RAW:W.TEXT_RAW+W.TEXT_RSZ]; base=W.TEXT_VA
    for i in range(len(code)-5):
        if code[i]==0xE8:
            rel=struct.unpack_from("<i",code,i+1)[0]; dst=base+i+5+rel
            if dst==0x7C8E17: sites.append(base+i)
    return sites

def find_push_before(ns, window=0x50):
    res=[]; start=ns-window; o1=W.va2off(start); o2=W.va2off(ns)+5
    if o1 is None or o2 is None: return res
    code=W.DATA[o1:o2]
    for i in range(len(code)-5):
        va=start+i
        if code[i]==0x68:
            imm=struct.unpack_from("<I",code,i+1)[0]
            if imm in TARGET: res.append((va,"68 imm32",imm))
        elif code[i]==0x6A:
            imm=code[i+1]
            if imm in TARGET: res.append((va,"6A imm8",imm))
    return res

def main():
    ns=scan_operator_new_calls()
    print("direct call 0x7C8E17 (operator new) sites:",len(ns))
    print("\n=== 分配点 push<size> -> operator new 双点闭合 ===")
    found={k:[] for k in SIZES}
    for n in ns:
        for va,kind,imm in find_push_before(n):
            found[imm].append((va,kind,n))
    for imm,cname in sorted(SIZES.items()):
        lst=found[imm]
        print(f"\n{cname} size=0x{imm:X} ({imm}):")
        if not lst: print("   NO direct push->new in window")
        for va,kind,n in lst[:12]:
            print(f"   push @0x{va:X} [{kind} 0x{imm:X}] -> new @0x{n:X}")

if __name__=="__main__":
    main()
