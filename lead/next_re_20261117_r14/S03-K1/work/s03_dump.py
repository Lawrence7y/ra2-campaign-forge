"""S03-K1 step3: dump CCFileClass & MixFileClass methods and ctors (non-truncated).
Also collect all [reg+disp] writes inside ctors for the field table.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b = Bin()
E = os.path.join(os.path.dirname(__file__), '..', 'EVIDENCE')

def dump_file(fname, ranges):
    lines=[]
    for start,end,name in ranges:
        lines.append(f"\n===== {name} [{start:08X},{end:08X}) =====")
        lines.append(dump(b,start,end,skipdata=True))
    txt="\n".join(lines)
    open(os.path.join(E,fname),'w',encoding='utf-8').write(txt)
    return txt

# CCFileClass ctor + methods (full file-class cluster)
cc = dump_file('E03_ccfile_methods.txt', [
    (0x4739F0,0x473A20,'ctor_4739F0_head'),
    (0x473AE0,0x473B10,'v12_473AE0'),
    (0x473B10,0x473B50,'v9_473B10'),
    (0x473BA0,0x473BE0,'Seek_473BA0'),
    (0x473C00,0x473C50,'Size_473C00'),
    (0x473C50,0x473CD0,'Open_473C50'),
    (0x473CD0,0x473D10,'IsAvail_473CD0'),
    (0x473D10,0x473E50,'GetFile_473D10'),
    (0x473E50,0x473F00,'ReadWhole_473E50'),
    (0x473F00,0x473F40,'v15_473F00'),
    (0x473FC0,0x474000,'v2_473FC0'),
    (0x473AB0,0x473AE0,'CDCheck_473AB0'),
    (0x431F10,0x431F40,'disk_open_431F10'),
    (0x431F30,0x431F70,'disk_avail_431F30'),
])

# MixFileClass ctor + Find
mx = dump_file('E04_mixfile_methods.txt', [
    (0x5B3C20,0x5B3EB0,'ctor_5B3C20_full'),
    (0x5B4430,0x5B4620,'Find_5B4430'),
    (0x5B3AC0,0x5B3B20,'list_init_5B3AC0'),
    (0x5B4590,0x5B45C0,'node_remove_5B4590'),
    (0x5B4630,0x5B46E0,'dtor_5B4630'),
])

print("E03 lines:",len(cc.splitlines()),"E04 lines:",len(mx.splitlines()))
print("written to",E)
