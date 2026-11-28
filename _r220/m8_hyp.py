import sys,json,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
# IMA ADPCM step table
ima=[7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31]
best=None
for pat_bytes in ('<H','<I'):
    import struct as S
    pat=S.pack('<16H',*ima)
    k=R.find(pat)
    print("IMA step table (16H) found at file off",hex(k) if k>=0 else None)
    k2=R.find(S.pack('<89H',*([7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767])))
    print("IMA full 89 step table found:",hex(k2) if k2>=0 else None)
# dispatch table 0x7c7778
o=P.r2o(0x7c7778)
dws=struct.unpack_from('<8I',R,o)
print("disp table 0x7c7778:",[hex(x) for x in dws])
# extent of 0x879b30: find where values stop looking small; scan 4000 dwords
o2=P.r2o(0x879b30)
vals=struct.unpack_from('<4000i',R,o2)
big=[i for i,v in enumerate(vals) if abs(v)>0x4000]
print("first |v|>0x4000 index:",big[:3], "value:", [vals[i] for i in big[:3]])
print("twin extent estimate bytes:", (big[0]*4) if big else None, "records of 64 dwords?", (big[0]//64 if big else None))
print("last 8 values before break:",vals[big[0]-8:big[0]] if big else None)
# 0x87bd90 extent
o3=P.r2o(0x87bd90)
b=R[o3:o3+300]
print("bd90 300B hex:",b.hex())
# check for 16 repeats
seq=[b[i] for i in range(0,256,16)]
print("bd90 every-16th byte:",seq)
json.dump({'disp7c7778':[hex(x) for x in dws],'twin_break_idx':big[0] if big else None},open('_r220/m8.json','w'),indent=1)
