# -*- coding: utf-8 -*-
"""R176：V558 -> V559（只改 F24 的 statement 与 limitations 两处错标签）。
纪律：全部断言在写盘之前；母本只读；新目录用独占创建。"""
import csv,io,os,sys,hashlib,time
T='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
SRC=os.path.join(T,'R17_R128_FACTINDEX_V558/FACT_INDEX.tsv')
DSTDIR=os.path.join(T,'R17_R128_FACTINDEX_V559')
DST=os.path.join(DSTDIR,'FACT_INDEX.tsv')
BASELINE=os.path.join(T,'R17_LEAD_BASELINE')
P=F=0
def ck(n,c,d=''):
    global P,F
    if c: P+=1; print('PASS',n,d)
    else: F+=1; print('FAIL',n,d)
raw=open(SRC,'rb').read()
txt=raw.decode('utf-8')
ck('A1 src sha',hashlib.sha256(raw).hexdigest()=='157996aa5da193d3ac254c9d6026343050b23f969793f83433469d5520bd8aa5')
ck('A2 src bytes',len(raw)==128835,'%d'%len(raw))
ck('A3 src CR=0',raw.count(b'\r')==0)
ck('A4 src LF=55',raw.count(b'\n')==55,'%d'%raw.count(b'\n'))
OLD_ST='键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4'
NEW_ST='1({) + 12(, "bounds": ) + 1(})（**R176 订正**：原写「键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4」；该 14 B 逐字节为 { , 空格 "bounds" 冒号 空格 }，其中空白实测 **2**（逗号后与冒号后各 1）、花括号 **2** + 逗号 **1** = **3** 不是 4 —— 两处误差方向相反（−1 与 +1）恰好抵消才凑成 14，故数值和仍对、分解标签是错的）'
OLD_LM='（键名加冒号加空白加末尾方括号）'
NEW_LM='（1({) + 12(, "bounds": ) + 1(})；**R176 订正**：原写「键名加冒号加空白加末尾方括号」—— 该 14 B 里方括号 **0** 个（文件的 ] 在偏移 17,624,353、末字节 } 在 17,624,354，都不在这 14 B 内），空格实为 **2** 个）'
ck('B1 OLD_ST unique in file',txt.count(OLD_ST)==1,'%d'%txt.count(OLD_ST))
ck('B2 OLD_LM unique in file',txt.count(OLD_LM)==1,'%d'%txt.count(OLD_LM))
ck('B3 NEW_ST absent before',txt.count(NEW_ST)==0,'%d'%txt.count(NEW_ST))
ck('B4 NEW_LM absent before',txt.count(NEW_LM)==0,'%d'%txt.count(NEW_LM))
new=txt.replace(OLD_ST,NEW_ST).replace(OLD_LM,NEW_LM)
# S-624 族：NEW_ST 自身引用旧标签 ⇒ 作用域必须剥掉 NEW_ST 再数
_wo=new.replace(NEW_ST,'')
ck('C1 OLD_ST gone OUTSIDE the correction segment',_wo.count(OLD_ST)==0,'%d'%_wo.count(OLD_ST))
ck('C1b neg-ctrl: raw count is 1 (it lives inside NEW_ST)',new.count(OLD_ST)==1,'%d'%new.count(OLD_ST))
ck('C2 NEW_ST once',new.count(NEW_ST)==1,'%d'%new.count(NEW_ST))
ck('C3 OLD_LM gone',new.count(OLD_LM)==0)
ck('C4 NEW_LM once',new.count(NEW_LM)==1,'%d'%new.count(NEW_LM))
ck('C5 char delta positive',len(new)>len(txt),'%d'%(len(new)-len(txt)))
# 结构不变：逐行 CSV 解析，只有 F24 的 2 列不同
a=list(csv.DictReader(io.StringIO(txt),delimiter='\t'))
b=list(csv.DictReader(io.StringIO(new),delimiter='\t'))
ck('D1 row count same',len(a)==len(b)==54,'%d/%d'%(len(a),len(b)))
diff=[(x['fact_id'],[k for k in x if x[k]!=y[k]]) for x,y in zip(a,b) if x!=y]
ck('D2 only F24 differs',diff==[('F24',['statement','limitations'])],repr(diff))
same=sum(1 for x,y in zip(a,b) if x==y)
ck('D3 other 53 rows byte-identical',same==53,'%d'%same)
# 母本没有被改
ck('E1 src still original sha',hashlib.sha256(open(SRC,'rb').read()).hexdigest()=='157996aa5da193d3ac254c9d6026343050b23f969793f83433469d5520bd8aa5')
if F:
    print('ABORT: %d FAIL before write'%F); sys.exit(1)
# 备份（wx 独占）
ts=time.strftime('%Y%m%d_%H%M%S')
bpath=os.path.join(BASELINE,'FACT_INDEX_V558.before_r176_%s.tsv'%ts)
with open(bpath,'xb') as f:
    f.write(raw)
ck('F1 backup written exclusive',os.path.getsize(bpath)==128835)
ck('F2 backup identical',open(bpath,'rb').read()==raw)
ck('F3 dst not exist yet',not os.path.exists(DST))
data=new.encode('utf-8')
with open(DST,'xb') as f:
    f.write(data)
back=open(DST,'rb').read()
ck('G1 readback bytes',len(back)==len(data),'%d'%len(back))
ck('G2 readback equals',back==data)
ck('G3 readback CR=0',back.count(b'\r')==0)
ck('G4 readback LF=55',back.count(b'\n')==55,'%d'%back.count(b'\n'))
sha=hashlib.sha256(back).hexdigest()
print('V559 = %d B / %s'%(len(back),sha))
print('delta = %+d B'%(len(back)-len(raw)))
print('---- %d PASS / %d FAIL ----'%(P,F))
sys.exit(1 if F else 0)
