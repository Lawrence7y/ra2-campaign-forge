"""Count instructions / calls / loop-back-edges for key per-object movement functions.
Channel: byte-level capstone linear disasm skipdata=True from known function entries; size from Ghidra func body.
"""
from pehelp import *
# (name, entry, size from Ghidra)
FNS=[
 ('FootClass::AI',0x4DA530,2520),
 ('UnitClass::AI',0x7360C0,2182),
 ('InfantryClass::AI',0x51BAB0,1239),
 ('AircraftClass::AI',0x414BB0,1544),
 ('Drive big Process',0x4B2630,8503),
 ('Walk big Process',0x75AEC0,4988),
 ('Ship big Process',0x6A1C80,8470),
 ('Mech big Process',0x5B01C0,5602),
 ('Hover big Process',0x5164D0,1809),
 ('UpdatePathfinding 0x4D3920',0x4D3920,2259),
 ('CallFindPath 0x4CBBA0',0x4CBBA0,158),
 ('FindPath 0x42C900',0x42C900,None),  # unknown size
 ('SearchCore 0x429D6D',0x429D6D,1649),
 ('loco slot23 common 0x55A910',0x55A910,15),
]
print('%-32s %10s %8s %7s %7s'%('fn','entry','bytes','instrs','calls'))
for name,va,size in FNS:
    nbytes=size if size else 4096
    ins=disasm(va,nbytes)
    ninstr=len(ins)
    ncalls=sum(1 for i in ins if i.mnemonic in ('call','callq'))
    # only count instructions within size
    if size:
        ins2=[i for i in ins if i.address < va+size]
        ninstr=len(ins2); ncalls=sum(1 for i in ins2 if i.mnemonic=='call')
    print('%-32s 0x%08X %8d %7d %7d'%(name,va,size or 0,ninstr,ncalls))
