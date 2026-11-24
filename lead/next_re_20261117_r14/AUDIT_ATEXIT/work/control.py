
# -*- coding: utf-8 -*-
"""Positive control: classifier must return B for entries already adjudicated
as atexit-dtor-only by a-S20-KPROVED and a-S13-K12, and A for their white lists."""
import sys, os, importlib.util, json
OUT=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('az',os.path.join(OUT,'analyze_lib.py'))
az=importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
S13_BLACK=[0x0040B740,0x0040B820,0x0040F680,0x0040F760,0x0040FC50,0x0040FD30,0x0046B6A0,
           0x0046B780,0x0054E930,0x0054E9E0,0x0062B110,0x0062B1F0,0x0065BF90,0x0065C070]
S13_WHITE=[0x0040F870,0x0054E890,0x0054EA70]
S20_DEMOTE=[0x0040EF60,0x0040F040,0x0053C560,0x00551370,0x00551450,0x00556F50,0x00557030,
            0x00422BE0,0x00423930,0x004253B0,0x00425530,0x004A7C10]
S20_PASS=[0x0040F0A0,0x0040F150,0x0053C6A0,0x005514B0,0x00551560,0x00557090,0x00557140]
def show(tag, lst, want):
    print('== %s (expect %s) =='%(tag,want))
    hit=0
    for e in lst:
        c,d=az.classify(e)
        tabs=d.get('tables',[])
        desc=[]
        for t in tabs:
            desc.append('tbl=%08X slot=%d col=%s live=%d dtor=%d static=%d'%(
                t['table'],t['slot'],t['col'],len(t['live']),len(t['dtor']),len(t['static_init'])))
        print('  %08X -> %s  immref=%s  %s'%(e,c,('yes' if d.get('immref_sites') else 'no'),' | '.join(desc)))
        if c==want: hit+=1
    print('  hit %d/%d'%(hit,len(lst)))
show('S13 blacklist',S13_BLACK,'B')
show('S13 whitelist',S13_WHITE,'A')
show('S20 demote',S20_DEMOTE,'B')
show('S20 exact PASS',S20_PASS,'A')
