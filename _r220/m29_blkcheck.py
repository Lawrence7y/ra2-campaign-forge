import sys,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
IMA=list(struct.unpack_from('<89H',R,P.r2o(0x8758e4)))
vals=list(struct.unpack_from('<'+str(16*89)+'i',R,P.r2o(0x879b30)))
blk=[vals[i*16:(i+1)*16] for i in range(89)]
for k in (0,1,4,6,44,45,60,88):
    a=blk[k][:8]; d=[a[i+1]-a[i] for i in range(7)]
    print("blk%-3d IMA=%-6d asc=%s diff=%s"%(k,IMA[k],a,d))
# AP test
ap=sum(1 for b in blk if len(set(b[i+1]-b[i] for i in range(7)))==1)
print("严格 AP 块数:",ap)
# try value[i] = floor(s*(i*2+1)/8) with s from IMA but per-block best s by least squares
import statistics
for k in (0,4,44,88):
    a=blk[k][:8]
    # s estimate from a[7]: s ≈ a[7]*8/15
    print("blk",k,"s_est=",a[7]*8/15, "IMA=",IMA[k], "pred floor:",[ (a[7]*8//15*(2*i+1))//8 for i in range(8)], "actual",a)
