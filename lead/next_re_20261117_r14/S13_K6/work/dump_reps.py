# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
for va,n in [(0x40BC10,80),(0x40B700,70),(0x40B880,190),(0x40B640,50),(0x40B670,35),(0x40F630,20)]:
 print(f'\n=== {va:#x} ===');p.dump(va,n)
