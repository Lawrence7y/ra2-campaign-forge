
import sys
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
print("SHA256="+K.SHA)
print("ImageBase=0x%08X"%K.IB)
print("sections:")
for a,b,p,r in K.SECS: print("  0x%08X-0x%08X raw=0x%X/%d"%(a,b,p,r))
