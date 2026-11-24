
import sys
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
for va,sz,name in [(0x722F00,854,'00722F00 caller of grow1'),(0x722440,807,'00722440 caller of grow3'),(0x47C060,873,'0047C060 candidate')]:
    print("="*80); print(name,"@0x%08X"%va)
    for i in K.dis(va,sz): print(K.fmt(i))
