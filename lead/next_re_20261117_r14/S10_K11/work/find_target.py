
import os, hashlib
root=r'D:/Project/ra2-campaign-forge'
hits=[]
for dp, dns, fns in os.walk(root):
    for fn in fns:
        if fn.lower()=='gamemd.exe':
            p=os.path.join(dp,fn)
            h=hashlib.sha256()
            with open(p,'rb') as f:
                for b in iter(lambda:f.read(1<<20), b''): h.update(b)
            hits.append((p, os.path.getsize(p), h.hexdigest()))
for p,s,h in hits: print(s, h, p)
try:
 import capstone, pefile
 print('capstone', capstone.__version__, 'pefile', pefile.__version__)
except Exception as e: print('IMPORT ERR', repr(e))
