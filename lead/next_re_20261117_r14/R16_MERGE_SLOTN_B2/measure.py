# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B2 · 开卡实测（只读，不落盘任何目标文件）。
打印：基线 mtime/字节/sha256/行数、行尾、不变量、3.1 五个数、指针替换留痕。
供合并脚本取数，所有数字均从盘上现算，不引用任何预测值。
"""
import hashlib, json, os, sys, collections, datetime
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B2", "delta.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
C4   = "\u2463"                     # ④
SB   = "④ 活表槽位见证"             # 口径 B 子串
OLD  = "R14_COMMON §12.4"
NEW  = "R14_COMMON §12.6"

def sha(b): return hashlib.sha256(b).hexdigest()
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e

def statinfo(p):
    st=os.stat(p); b=open(p,"rb").read()
    iso=datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    return dict(path=p, mtime=st.st_mtime, mtime_local=iso, bytes=len(b), sha256=sha(b),
                nlines_lf=b.count(b"\n"), crlf=b.count(b"\r\n"),
                bom=(b[:3]==b"\xef\xbb\xbf"), ends_nl=b.endswith(b"\n"))

def eol(b):
    return dict(CRLF=b.count(b"\r\n"), LF=b.count(b"\n")-b.count(b"\r\n"),
                CR=b.count(b"\r")-b.count(b"\r\n"), BOM=(b[:3]==b"\xef\xbb\xbf"),
                ends_nl=b.endswith(b"\n"))

def load_atlas():
    s=set()
    for i,line in enumerate(open(ATLAS,encoding="utf-8-sig")):
        if i==0: continue
        p=line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): s.add(ne(p[0]))
    return s

def counts(text, atlas):
    data=text.splitlines()[1:]
    coldist=collections.Counter(len(ln.split("\t")) for ln in data)
    yz=ina=outa=na=nb=0
    for ln in data:
        c=ln.split("\t")
        if len(c)<8: continue
        if c[4].strip()=="[已证]":
            yz+=1
            if ne(c[0]) in atlas: ina+=1
            else: outa+=1
            if C4 in c[3]: na+=1                 # 口径 A
            if SB in c[3]: nb+=1                 # 口径 B
    return dict(data_rows=len(data), coldist=dict((str(k),v) for k,v in coldist.items()),
                yizheng=yz, atlas_in=ina, atlas_out=outa, N_A=na, N_B=nb)

def main():
    cov_b=open(COV,"rb").read(); pan_b=open(PANEL,"rb").read(); delta_b=open(DELTA,"rb").read()
    cov_text=cov_b.decode("utf-8"); pan_text=pan_b.decode("utf-8")
    atlas=load_atlas()

    print("=== 基线 stat ===")
    for nm,p,b in [("coverage.tsv",COV,cov_b),("PANEL.md",PANEL,pan_b),("delta.tsv",DELTA,delta_b)]:
        s=statinfo(p)
        print(f"{nm}: bytes={s['bytes']} sha256={s['sha256']} mtime_local={s['mtime_local']} "
              f"LF={s['nlines_lf']} CRLF={s['crlf']} bom={s['bom']} ends_nl={s['ends_nl']}")
    print("行尾 coverage:", eol(cov_b))
    print("行尾 PANEL   :", eol(pan_b))

    print("\n=== 改前全表计数 ===")
    cb=counts(cov_text, atlas)
    print(json.dumps(cb, ensure_ascii=False))

    drows=[ln.split("\t") for ln in delta_b.decode("utf-8-sig").splitlines()[1:]]
    assert len(drows)==15
    repl=sum(d[3].count(OLD) for d in drows)
    print(f"\n=== delta 指针 {OLD}->{NEW} 出现次数(逐行 col4 累计) = {repl} ===")

    # 定位 15 行 + 构造改后文本（内存）
    cov_lines=cov_text.splitlines(keepends=True)
    by_entry={}
    for idx,ln in enumerate(cov_lines):
        core=ln[:-1] if ln.endswith("\n") else ln
        c=core.split("\t")
        if len(c)>=8: by_entry.setdefault(ne(c[0]),[]).append(idx)
    newcol={}
    for d in drows:
        e=ne(d[0]); c4=d[3].replace(OLD,NEW); newcol[e]=c4
        idxs=by_entry.get(e,[])
        assert len(idxs)==1, (e,idxs)
        i=idxs[0]; core=cov_lines[i][:-1] if cov_lines[i].endswith("\n") else cov_lines[i]
        c=core.split("\t")
        assert c4.startswith(c[3]), ("prefix FAIL",e)
    N_pre=0
    before_has=[]
    for d in drows:
        e=ne(d[0]); i=by_entry[e][0]
        core=cov_lines[i][:-1] if cov_lines[i].endswith("\n") else cov_lines[i]
        c=core.split("\t")
        has=(C4 in c[3]); N_pre+=has
        before_has.append((e,has, SB in c[3]))
    print("\n=== 15 行改前是否已含 ④ / ④ 活表槽位见证 ===")
    for e,h,hb in before_has: print(f"  {e} has④={h} hasB={hb}")
    print(f"N_pre(15 行改前已含字符④的行数) = {N_pre}")

    after_lines=list(cov_lines)
    for d in drows:
        e=ne(d[0]); i=by_entry[e][0]; ln=after_lines[i]
        nl="\n" if ln.endswith("\n") else ""
        core=ln[:-1] if nl else ln; c=core.split("\t"); c[3]=newcol[e]
        after_lines[i]="\t".join(c)+nl
    cov_after_text="".join(after_lines)
    ca=counts(cov_after_text, atlas)

    print("\n=== 改后(内存模拟)全表计数 ===")
    print(json.dumps(ca, ensure_ascii=False))

    print("\n=== 3.1 五个数（实测）===")
    print(f"N_pre   = {N_pre}")
    print(f"N_A_pre = {cb['N_A']}")
    print(f"N_A_post= {ca['N_A']}   (net +{ca['N_A']-cb['N_A']})")
    print(f"N_B_pre = {cb['N_B']}")
    print(f"N_B_post= {ca['N_B']}   (net +{ca['N_B']-cb['N_B']})")

    print("\n=== 指针 §12.6 / §12.4 全表命中 ===")
    print(f"改后 §12.6 行数 = {sum(1 for ln in cov_after_text.splitlines() if NEW in ln)}")
    print(f"改前 §12.6 行数 = {sum(1 for ln in cov_text.splitlines() if NEW in ln)}")
    print(f"改后 §12.4 命中次数 = {cov_after_text.count(OLD)}")
    print(f"改前 §12.4 命中次数 = {cov_text.count(OLD)}")
    # B1 已入库的 15 个 entry
    b1=os.path.join(ROOT,"R16_SLOTN_B1","delta.tsv")
    b1e=set(ne(l.split("\t")[0]) for l in open(b1,encoding="utf-8-sig").read().splitlines()[1:] if l.strip())
    s126=set(ne(l.split("\t")[0]) for l in cov_after_text.splitlines() if NEW in l and len(l.split("\t"))>=8)
    print(f"改后含 §12.6 的 entry 数={len(s126)} 与 B1 15 entry 相同={s126==b1e}")

if __name__=="__main__":
    main()
