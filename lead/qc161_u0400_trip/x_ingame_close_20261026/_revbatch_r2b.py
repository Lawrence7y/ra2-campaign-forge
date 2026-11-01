# _revbatch_r2b.py — second metric: global black-pixel ratio, center-region stats
import os, zlib, struct

ROOT = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x"
ARMS = [("P0","20261028T084855_0001_P0_ORIG"),("P0N","20261028T085311_0001_P0N_INJ_OFF"),
("P1","20261028T085640_0001_P1_G1B0exp"),("P2","20261028T090813_0001_P2_G1B0def"),
("P3","20261028T091330_0001_P3_G1B1"),("P3m","20261028T092052_0001_P3m_MENU")]
MAGIC=b"\x89PNG\r\n\x1a\n"

def rgb_of(path):
    b=open(path,"rb").read(); assert b[:8]==MAGIC
    pos=8; idat=b""; w=h=None
    while pos<len(b):
        ln=struct.unpack(">I",b[pos:pos+4])[0]; typ=b[pos+4:pos+8]
        data=b[pos+8:pos+8+ln]
        if typ==b"IHDR": w,h,bd,ct=struct.unpack(">IIBB",data[:10])
        elif typ==b"IDAT": idat+=data
        elif typ==b"IEND": break
        pos+=12+ln
    raw=zlib.decompress(idat); stride=1+w*3
    return raw, stride, w, h

def stats(path):
    raw,stride,w,h=rgb_of(path)
    # black ratio: all channels <=10, sampled every 5th pixel
    tot=blk=0; lum_sum=0; lum_n=0
    for y in range(0,h,4):
        base=y*stride+1
        row=raw[base:base+w*3]
        for x in range(0,w*3,15):
            r,g,bl=row[x],row[x+1],row[x+2]
            tot+=1
            if r<=10 and g<=10 and bl<=10: blk+=1
            lum_sum+=0.299*r+0.587*g+0.114*bl; lum_n+=1
    # center region (middle 1280x720 box)
    cx0,cy0=(w-1280)//2,(h-720)//2
    ct=0; cb=0; clum=0.0; cn=0
    for y in range(cy0,cy0+720,4):
        base=y*stride+1
        row=raw[base:base+w*3]
        for x in range(cx0*3,cx0*3+1280*3,15):
            r,g,bl=row[x],row[x+1],row[x+2]
            ct+=1
            if r<=10 and g<=10 and bl<=10: cb+=1
            clum+=0.299*r+0.587*g+0.114*bl; cn+=1
    return dict(blk_ratio=round(blk/tot,4), mean_lum=round(lum_sum/lum_n,2),
                center_blk=round(cb/ct,4), center_lum=round(clum/cn,2))

for tag,d in ARMS:
    sdir=os.path.join(ROOT,d,"shots")
    for fn in sorted(os.listdir(sdir)):
        if fn.endswith(".png"):
            s=stats(os.path.join(sdir,fn))
            print("%-4s %-18s black_ratio=%.4f mean_lum=%7.2f | center(1280x720): black=%.4f lum=%7.2f"%(tag,fn,s["blk_ratio"],s["mean_lum"],s["center_blk"],s["center_lum"]))
