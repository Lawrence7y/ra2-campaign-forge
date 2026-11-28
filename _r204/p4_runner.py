#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 p4：gate_runner.LEDGER 同步 V586 -> V587（C20 三方一致）。
纪律：wx 独占备份 -> 断言旧 sha256 -> 一次性写入 -> 回读校验。
"""
import hashlib, os, time
ROOT='/home/t628/projects/ra2-campaign-forge'
P=ROOT+'/_r161/gate_runner.py'
BASE=ROOT+'/R17_LEAD_BASELINE'
os.makedirs(BASE,exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
STAMP=time.strftime('%Y%m%d_%H%M%S')
src=open(P,'rb').read(); old=sha(src)
assert src.count(b'R17_R131_FACTINDEX_V586')==1, src.count(b'R17_R131_FACTINDEX_V586')
bak='%s/gate_runner.py.%s.bak'%(BASE,STAMP)
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,src); os.close(fd)
assert sha(open(bak,'rb').read())==old
new=src.replace(b'R17_R131_FACTINDEX_V586',b'R17_R131_FACTINDEX_V587')
open(P,'wb').write(new)
rb=open(P,'rb').read()
assert sha(rb)!=old and b'R17_R131_FACTINDEX_V586' not in rb and rb.count(b'R17_R131_FACTINDEX_V587')==1
assert rb.count(b'\r')==src.count(b'\r'), (rb.count(b'\r'), src.count(b'\r'))
print('OLD sha=%s -> NEW sha=%s  CR=%d' % (old[:16], sha(rb)[:16], rb.count(b'\r')))
print('OK')
