
import sys,os
sys.path.insert(0,os.path.dirname(__file__)); import common,k16
for st,en in [(0x519F40,0x51A020),(0x6FA1E0,0x6FA260),(0x6FA950,0x6FAA10)]:
 print('\n###',hex(st),hex(en))
 for i in common.disasm(st,en-st): print(common.fmt(i))
