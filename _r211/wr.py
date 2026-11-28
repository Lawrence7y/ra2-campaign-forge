# -*- coding: utf-8 -*-
"""R211 写入工具：wx 独占备份 -> 断言旧 sha/CR -> 一次性写 -> 回读校验。"""
import os,hashlib,time,sys
ROOT='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BAK=os.path.join(ROOT,'R17_LEAD_BASELINE')
def sha(b): return hashlib.sha256(b).hexdigest()
def backup(path,tag):
    p=os.path.join(ROOT,path)
    b=open(p,'rb').read()
    s=sha(b); cr=b.count(b'\r'); lf=b.count(b'\n')
    name=os.path.basename(path)
    dst=os.path.join(BAK,'%s.before_r211_%s_%s.bak'%(name,tag,time.strftime('%Y%m%d_%H%M%S')))
    fd=os.open(dst,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(b)
    assert sha(open(dst,'rb').read())==s
    print('BACKUP %s -> %s  sha=%s CR=%d LF=%d'%(path,os.path.basename(dst),s[:16],cr,lf))
    return (p,s,cr,lf,b)
def write(path,tag,newexp,exp_sha,exp_cr):
    p,s,cr,lf,old=backup(path,tag)
    assert s==exp_sha, 'SHA MISMATCH %s vs %s'%(s,exp_sha)
    assert cr==exp_cr, 'CR MISMATCH %d vs %d'%(cr,exp_cr)
    b=newexp(old)
    if isinstance(b,str): b=b.encode('utf-8')
    with open(p,'wb') as f: f.write(b)
    chk=open(p,'rb').read()
    assert chk==b
    print('WROTE %s bytes %d -> %d CR %d -> %d sha %s -> %s'%(path,len(old),len(chk),cr,chk.count(b'\r'),s[:16],sha(chk)[:16]))
    return chk
