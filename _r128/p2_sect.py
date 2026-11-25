# -*- coding: utf-8 -*-
import os, pefile
ROOT='/home/t628/projects/ra2-campaign-forge'
pe=pefile.PE(os.path.join(ROOT,'ra2bench','gamemd.exe')); IB=pe.OPTIONAL_HEADER.ImageBase
print('ImageBase 0x%08x' % IB)
for s in pe.sections:
    print('%-10s VA 0x%08x .. 0x%08x  vsize 0x%06x rawsz 0x%06x  flags 0x%08x'
          % (s.Name.decode().strip('\x00'), IB+s.VirtualAddress,
             IB+s.VirtualAddress+s.Misc_VirtualSize, s.Misc_VirtualSize,
             s.SizeOfRawData, s.Characteristics))
for va in (0x87f7e8,0x89a29c,0xb0c110,0x815da4,0x812000):
    for s in pe.sections:
        lo=IB+s.VirtualAddress; hi=lo+max(s.Misc_VirtualSize,s.SizeOfRawData)
        if lo<=va<hi:
            print('0x%08x in %-8s off 0x%x' % (va, s.Name.decode().strip('\x00'), va-lo))
            break
    else:
        print('0x%08x in NONE' % va)
