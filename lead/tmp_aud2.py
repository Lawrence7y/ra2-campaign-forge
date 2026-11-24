import sys,os,re
sys.stdout.reconfigure(encoding="utf-8")
L=r"D:\Project\ra2-campaign-forge\lead"
E=[]
with open(os.path.join(L,"next_re_20261117_r14","R17_R78_T1_RECLASS","files_excluded_prime.tsv"),encoding="utf-8") as fh:
    fh.readline()
    for line in fh:
        g=line.rstrip("\n").split("\t"); E.append(dict(rel=g[0],bytes=int(g[2]),label=g[5],why=g[6]))
import random; random.seed(11)
for key in ["E2_包壳脚本流出物(首行横幅)","E1_工具流出物","E3_元记录目录","E4_旧版别名"]:
    v=[r for r in E if r["why"].startswith(key)]
    print("="*25,key,len(v),sum(r["bytes"] for r in v))
    for r in random.sample(v,min(6,len(v))):
        h=open(os.path.join(L,r["rel"].replace("/",os.sep)),"rb").read(140).decode("utf-8","replace").replace("\n"," | ")
        print(f'  {r["bytes"]:8d} {r["rel"][:84]}')
        print("     »",h[:110])
