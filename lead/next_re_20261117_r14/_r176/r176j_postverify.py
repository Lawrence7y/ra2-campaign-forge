# -*- coding: utf-8 -*-
"""R176 写后复验：V559 内容、残留错标签普查（逐文件）、门禁常量自洽。"""
import csv,io,os,re,sys,hashlib,ast
T='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
R='/home/t628/projects/ra2-campaign-forge'
P=F=0
def ck(n,c,d=''):
    global P,F
    if c: P+=1; print('PASS',n,d)
    else: F+=1; print('FAIL',n,d)
v559=os.path.join(T,'R17_R128_FACTINDEX_V559/FACT_INDEX.tsv')
v558=os.path.join(T,'R17_R128_FACTINDEX_V558/FACT_INDEX.tsv')
raw=open(v559,'rb').read()
ck('A1 V559 bytes',len(raw)==129405,'%d'%len(raw))
ck('A2 V559 sha',hashlib.sha256(raw).hexdigest()=='e4642d554d8ba9f1dab25b6a2b456e365252051035f9104003b58ff622d489e9')
ck('A3 CR=0',raw.count(b'\r')==0)
ck('A4 LF=55',raw.count(b'\n')==55,'%d'%raw.count(b'\n'))
ck('A5 V558 untouched',hashlib.sha256(open(v558,'rb').read()).hexdigest()=='157996aa5da193d3ac254c9d6026343050b23f969793f83433469d5520bd8aa5')
rows=list(csv.DictReader(io.StringIO(raw.decode()),delimiter='\t'))
ck('B1 54 rows',len(rows)==54,'%d'%len(rows))
f24=[r for r in rows if r['fact_id']=='F24'][0]
st,lm=f24['statement'],f24['limitations']
old_lab='键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4'
old_lab2='键名加冒号加空白加末尾方括号'
ck('B2 old statement label only inside correction',st.count(old_lab)==1,'%d'%st.count(old_lab))
ck('B3 old limitations label only inside 引文 (1 total)',lm.count(old_lab2)==1,'%d'%lm.count(old_lab2))
ck('B4 byte-exact form in statement',st.count('1({) + 12(, "bounds": ) + 1(})')>=1,'%d'%st.count('1({) + 12(, "bounds": ) + 1(})'))
ck('B5 byte-exact form in limitations',lm.count('1({) + 12(, "bounds": ) + 1(})')>=1,'%d'%lm.count('1({) + 12(, "bounds": ) + 1(})'))
ck('B6 stmt bytes 11349',len(st.encode())==11349,'%d'%len(st.encode()))
ck('B7 lim bytes 36142',len(lm.encode())==36142,'%d'%len(lm.encode()))
# 残留普查：只数落在「非订正段」里的旧标签
# S-636 族（第二次同族）：旧标签必须以「引文」形态恰好出现 1 次、不得有非引文出现。
# 引文判定用「」括号配对扫描，而不是「剥掉订正段」——订正段可能嵌在更外层的括号里。
def unquoted_count(txt,lab):
    quoted=set()
    for m in re.finditer(r'「[^「」]*」',txt):
        for k in range(m.start(),m.end()):
            quoted.add(k)
    n=0
    for m in re.finditer(re.escape(lab),txt):
        if not all(k in quoted for k in range(m.start(),m.end())):
            n+=1
    return n
ck('C1 stmt: old label appears once, all inside 引文',st.count(old_lab)==1 and unquoted_count(st,old_lab)==0,
   'total=%d unquoted=%d'%(st.count(old_lab),unquoted_count(st,old_lab)))
ck('C2 lim: old label appears once, all inside 引文',lm.count(old_lab2)==1 and unquoted_count(lm,old_lab2)==0,
   'total=%d unquoted=%d'%(lm.count(old_lab2),unquoted_count(lm,old_lab2)))
# 全表：还有哪行提到「括号与收尾 / 末尾方括号」
others=[]
for r in rows:
    if r['fact_id']=='F24': continue
    for col in ('statement','limitations'):
        if '括号与收尾' in r[col] or '末尾方括号' in r[col]:
            others.append((r['fact_id'],col))
ck('C3 no other row carries the labels',others==[],repr(others))
# 三份文本
def rd(p):
    return open(p,'rb').read().decode('utf-8',errors='replace')
LL=rd(os.path.join(R,'lead/LEAD_LOCK')); RC=rd(os.path.join(T,'R14_COMMON.md'))
BR=rd(os.path.join(T,'STATUS_BOARD.md')); AR=rd(os.path.join(T,'BOARD_ARCHIVE.md'))
GO=rd(os.path.join(R,'lead/GOAL_THREE_TARGETS_20261018.md'))
lab_ll='键名 8 + 冒号 1 + 空白 1 + 结构字符'
print('RESIDUAL: LEAD_LOCK lab_ll=%d labA=%d ; RC 末尾方括号=%d ; FI old=%d'%(
    LL.count(lab_ll),LL.count(old_lab),RC.count('末尾方括号'),raw.decode().count(old_lab)))
ck('D1 LEAD_LOCK still carries 空白 1 + 结构字符 (to be noted, not edited this round)',LL.count(lab_ll)==1,'%d'%LL.count(lab_ll))
ck('D2 R14_COMMON still carries 末尾方括号 (to be noted)',RC.count('末尾方括号')==1,'%d'%RC.count('末尾方括号'))
# 门禁常量
src=open(os.path.join(R,'_r160/facts_floors.py'),encoding='utf-8').read()
ck('E1 facts CUR_SHA256 is V559',"CUR_SHA256 = 'e4642d554d8ba9f1dab25b6a2b456e365252051035f9104003b58ff622d489e9'" in src)
ck('E2 facts TOTAL_BYTES 129405','TOTAL_BYTES = 129405' in src)
ck('E3 facts F24 floor','\'F24\': (11349, 36142),' in src)
ck('E4 facts EXPECT_CUR V559',"'R17_R128_FACTINDEX_V559'" in src)
g=open(os.path.join(R,'_r161/gate_runner.py'),encoding='utf-8').read()
ck('E5 gate_runner LEDGER V559',"'R17_R128_FACTINDEX_V559'" in g and 'V558' not in g)
ck('E6 gate_runner no old sha', '157996aa5da193d3ac254c9d6026343050b23f969793f83433469d5520bd8aa5' not in g)
# 指针
PT=rd(os.path.join(T,'FACT_INDEX_CURRENT.md'))
ck('F1 pointer V559 twice',PT.count('R17_R128_FACTINDEX_V559')==2,'%d'%PT.count('R17_R128_FACTINDEX_V559'))
ck('F2 pointer sha',  'e4642d554d8ba9f1dab25b6a2b456e365252051035f9104003b58ff622d489e9' in PT)
ck('F3 pointer bytes 129405','| 字节数 | 129405 |' in PT)
ck('F4 pointer R176','| 声明轮次 | R176 |' in PT)
print('---- %d PASS / %d FAIL ----'%(P,F))
sys.exit(1 if F else 0)
