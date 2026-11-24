"""Dump LocomotionClass-family vtables as raw dwords, annotate which dwords look like code (within .text).
Channel 1: byte-level, no atlas dependency."""
from pehelp import *

VTS = {
 'DriveLocomotionClass':  {'off24':0x7E7E8C,'off4':0x7E7EB0,'main':0x7E7F7C},
 'DropPodLocomotionClass':{'off24':0x7E8254,'off4':0x7E8278,'main':0x7E8344},
 'FlyLocomotionClass':    {'off4':0x7E89F4,'main':0x7E8AC0},
 'HoverLocomotionClass':  {'off4':0x7EACFC,'main':0x7EADC8},
 'LocomotionClass':       {'off4':0x7EADF4,'main':0x7EAEC0},
 'JumpjetLocomotionClass':{'off24':0x7ECD44,'off4':0x7ECD68,'main':0x7ECE34},
 'MechLocomotionClass':   {'off4':0x7EDB6C,'main':0x7EDC38},
 'RocketLocomotionClass': {'off4':0x7F0B1C,'main':0x7F0BE8},
 'ShipLocomotionClass':   {'off24':0x7F2D68,'off4':0x7F2D8C,'main':0x7F2E58},
 'TeleportLocomotionClass':{'off24':0x7F4FDC,'off4':0x7F5000,'main':0x7F50CC},
 'TunnelLocomotionClass': {'off4':0x7F5A24,'main':0x7F5AF0},
 'WalkLocomotionClass':   {'off24':0x7F69D4,'off4':0x7F69F8,'main':0x7F6AC4},
}

def is_code(va):
    try: return section_of(va) == '.text'
    except Exception: return False

for name, tbls in VTS.items():
    for kind, va in tbls.items():
        # dump up to 56 dwords or until non-code gap after >=3 code dwords
        vals=[]
        for i in range(56):
            v=u32(va+4*i)
            vals.append(v)
        # print compact: slot: value (code?) - stop heuristically at first run of >=3 non-code after code
        print('=== %-26s %-5s vt=%08X ===' % (name, kind, va))
        for i,v in enumerate(vals):
            tag = 'CODE' if is_code(v) else ('---' if v==0 else section_of(v) if v>=IMAGE_BASE else 'imm')
            print('  slot %2d [+%03X] @%08X = %08X %s' % (i, 4*i, va+4*i, v, tag))
            # stop at first non-code after slot>=8 (main ~10 slots) - but for off4 up to 49
        print()
