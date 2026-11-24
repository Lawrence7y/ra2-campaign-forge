# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
for va,n in [(0x6E6310,0x180),(0x6F1920,0x280),(0x7F120 if False else 0x721270,0x120),(0x727AA0,0x400),(0x751590,0x180),(0x752460,0x600),(0x763610,0x400),(0x763690,0x200)]:
 print(f'---- region {va:08X} ----')
 p.dump(va,n)
