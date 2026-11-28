# -*- coding: utf-8 -*-
"""R216 p1：生成 FACT_INDEX V599（在 V598 上只改 F29 一行：追加 MI 布局 + 四个 IID + 律 T/U/W 证据）。
先写目录，后改指针（R215 纪律）。所有数字来自本轮实测 json。"""
import os,hashlib,json,shutil
ROOT='/home/t628/projects/ra2-campaign-forge'; T=ROOT+'/lead/next_re_20261117_r14'
OLD=T+'/R17_R131_FACTINDEX_V598/FACT_INDEX.tsv'
NEW=T+'/R17_R131_FACTINDEX_V599'
NEWF=NEW+'/FACT_INDEX.tsv'
b0=open(OLD,'rb').read()
sha0=hashlib.sha256(b0).hexdigest(); n0=len(b0)
print('旧 V598 sha=%s bytes=%d'%(sha0,n0))
FLOORS_F29=(3435,20898); EVIDB_F29=459

m10=json.load(open(ROOT+'/_r216/m10.json'))
m11=json.load(open(ROOT+'/_r216/m11.json'))
ADD=(
 ' 【R216 追加·?AVAbstractClass@@ 四子对象 MI 布局与四条律】'
 '(1) AbstractClass 并非单视图：0x7e1f50(mdisp=0,24 槽)/0x7e1f34(mdisp=4,6 槽)/0x7e1f2c(mdisp=8,1 槽)/0x7e1f24(mdisp=12,1 槽)；'
 '主视图 slot8=0x4105a0 体内依次 mov [esi+0]=0x7e1f50、[esi+4]=0x7e1f34、[esi+8]=0x7e1f2c、[esi+0xc]=0x7e1f24 后按 al&1 决定 call 0x7c8b3d，ret 4 ⇒ 4 个 vfptr 的写入是静态字节实证。'
 '(2) 主视图 slot0=0x410260 为 QueryInterface：repe cmpsd ecx=4 依次比对 0x7f7c90/0x7f7c80/0x7f7c70/0x7e9ae0 四个 16 字节常量，'
 'GUID 文本= 00000000-0000-0000-C000-000000000046 / 00000109-0000-0000-C000-000000000046 / 0000010C-0000-0000-C000-000000000046 / 170DAC82-12E4-11D2-8175-006008055BB5；'
 '无匹配返回 0x80004002，出参空返回 0x80004003，匹配第 4 个常量时写 this+4（即 4 字节 adjustor 偏移）。'
 '(3) 律 U（this-adjustor thunk）：mdisp!=0 的 260 张视图里，slot0 形如 sub/add dword ptr [esp+4],N 后 jmp 到另一视图 slot0 者 101 张，'
 '101/101 满足 N == self.mdisp - target.mdisp，反例 0；组合分布 (4,0,4)x91 / (24,0,24)x6 / (1728,0,1728)x1 / (44,0,44)x1 / (40,0,40)x1 / (36,0,36)x1。'
 '(4) 律 T（原口径 disp==mdisp）：全 .text mov dword ptr [reg+disp],<视图基址> 命中 4202 条，符 3876(92.24%)、违例 326(7.76%)；'
 '违例分族 B 内嵌成员 201 / C 近邻偏移 79 / A off=0 写次级视图 46。'
 '(5) 律 W（升级口径：disp + reg 基址增量 delta == mdisp）：线性扫描 1,394,300 条指令后重算，C7 命中 4195 条，'
 '可反解 delta 者 2911 条中符 2551、违例 360；360 条违例的 (disp+delta)-mdisp 全部 > 0，0 条 <= 0，'
 '即『写入点偏移恒 >= 该视图 mdisp』，负偏移 0 条 ⇒ 该不等式方向可作为新判据。'
 '(6) 口径订正 3 条：m9 用 isdigit() 解析 disp 丢掉十六进制 0xc 致正控 3/4 假 FAIL（改 int(p,0) 后 4/4）；'
 'm8 的 try-align 反控失败（命中点前移 50B 仍有 227/300 能"对齐"）⇒ try-align 法判为不可信并弃用，改一次性线性扫描建表；'
 'EX1 报 call 0x4a1de0 的 0x4a1ca0 站点 331 与主会话 E8 字节口径 331 一致，此前摘要误记为 1（主会话读错，非子代理错）。'
)
raw=b0.decode('utf-8')
lines=raw.split('\n')
hit=None
for i,ln in enumerate(lines):
    if ln.startswith('F29\t'):
        hit=i; break
assert hit is not None
cols=lines[hit].split('\t')
print('F29 列数=%d ; statement 长度=%d'%(len(cols),len(cols[1])))
oldstmt=cols[1]
cols[1]=oldstmt+ADD
lines[hit]='\t'.join(cols)
new=('\n'.join(lines)).encode('utf-8')
# 逐行差异断言：只有 F29 一行变
o=b0.decode('utf-8').split('\n'); n=new.decode('utf-8').split('\n')
diff=[i for i in range(len(o)) if o[i]!=n[i]]
print('变更行号（0 基）=%s ; 总行数 %d -> %d'%(diff,len(o),len(n)))
assert diff==[hit], 'UNEXPECTED DIFF'
os.makedirs(NEW,exist_ok=True)
assert not os.path.exists(NEWF), 'V599 已存在'
open(NEWF,'wb').write(new)
sha1=hashlib.sha256(new).hexdigest(); n1=len(new)
print('新 V599 sha=%s bytes=%d (+%d)'%(sha1,n1,n1-n0))
# 新 FLOORS（字符长度与 sha）与 EVID
import importlib.util
st=cols[1]
import hashlib as H
print('新 F29 正文 字节=%d 字符=%d sha16=%s'%(len(st.encode('utf-8')),len(st),H.sha256(st.encode('utf-8')).hexdigest()[:16]))
json.dump({'old_sha':sha0,'old_bytes':n0,'new_sha':sha1,'new_bytes':n1,'diff_line':hit,
 'stmt_bytes':len(st.encode('utf-8')),'stmt_chars':len(st),
 'stmt_sha':H.sha256(st.encode('utf-8')).hexdigest()},
 open(ROOT+'/_r216/p1.json','w'),indent=1)
