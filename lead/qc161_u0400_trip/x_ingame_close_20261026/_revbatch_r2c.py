# _revbatch_r2c.py — shot integrity: raw-pixel md5 (duplicate detection), inter-shot sampled diffs
import os, zlib, struct, hashlib

ROOT = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x"
ARMS = [("P0","20261028T084855_0001_P0_ORIG"),("P0N","20261028T085311_0001_P0N_INJ_OFF"),
("P1","20261028T085640_0001_P1_G1B0exp"),("P2","20261028T090813_0001_P2_G1B0def"),
("P3","20261028T091330_0001_P3_G1B1"),("P3m","20261028T092052_0001_P3m_MENU")]
MAGIC=b"\x89PNG\r\n\x1a\n"

def rgb(path):
    b=open(path,"rb").read(); assert b[:8]==MAGIC
    pos=8; idat=b""; w=h=None
    while pos<len(b):
        ln=struct.unpack(">I",b[pos:pos+4])[0]; typ=b[pos+4:pos+8]; data=b[pos+8:pos+8+ln]
        if typ==b"IHDR": w,h=struct.unpack(">II",data[:8])
        elif typ==b"IDAT": idat+=data
        elif typ==b"IEND": break
        pos+=12+ln
    raw=zlib.decompress(idat)
    return raw, w, h

store={}
print("--- raw pixel md5 (identical => duplicate capture)")
for tag,d in ARMS:
    for fn in sorted(os.listdir(os.path.join(ROOT,d,"shots"))):
        if not fn.endswith(".png"): continue
        raw,w,h=rgb(os.path.join(ROOT,d,"shots",fn))
        m=hashlib.md5(raw).hexdigest()
        store["%s/%s"%(tag,fn)]=raw
        print("%-4s %-18s md5=%s"%(tag,fn,m))

def difffrac(a,b,w,h):
    stride=1+w*3; tot=hits=0
    for y in range(0,h,7):
        ya=y*stride+1; xa=None
        ra=a[ya:ya+w*3]; rb=b[ya:ya+w*3]
        for x in range(0,w*3,21):
            tot+=1
            if ra[x:x+3]!=rb[x:x+3]: hits+=1
    return hits/tot

keys=list(store.keys())
p3p="P3/post_close_end.png"; p0p="P0/post_close_end.png"
print("--- sampled diffs")
print("P3.post vs P0.post:",round(difffrac(store[p3p],store[p0p],5376,1451),4))
print("P3.post vs P1.post:",round(difffrac(store[p3p],store["P1/post_close_end.png"],5376,1451),4))
print("P3.post vs P3.pre :",round(difffrac(store[p3p],store["P3/pre_close.png"],5376,1451),4))
print("P0.batt vs P0.pre :",round(difffrac(store["P0/battle_end.png"],store["P0/pre_close.png"],5376,1451),4))
print("P0N.batt vs P0N.pre:",round(difffrac(store["P0N/battle_end.png"],store["P0N/pre_close.png"],5376,1451),4))
print("P3m.menu vs P3m.pre:",round(difffrac(store["P3m/menu_ready.png"],store["P3m/pre_close.png"],5376,1451),4))
print("P3m.post vs P0.post:",round(difffrac(store["P3m/post_close_end.png"],store[p0p],5376,1451),4))
print("P2.post vs P0.post:",round(difffrac(store["P2/post_close_end.png"],store[p0p],5376,1451),4))
