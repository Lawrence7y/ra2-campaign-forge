# -*- coding: utf-8 -*-
"""R176 草稿：构造 V559 的两处文本改动，只打印 diff 形状，不写盘。"""
import csv,io,csv as C,sys,difflib
SRC='R17_R128_FACTINDEX_V558/FACT_INDEX.tsv'
raw=open(SRC,'rb').read()
txt=raw.decode('utf-8')
rd=list(csv.DictReader(io.StringIO(txt),delimiter='\t'))
row=[r for r in rd if r['fact_id']=='F24'][0]
st,lm=row['statement'],row['limitations']

OLD_ST='键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4'
NEW_ST='1({) + 12(, "bounds": ) + 1(})'
SUB_ST='（**R176 订正**：原写「键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4」，其中「空白 1」实测 **2**（逗号后与冒号后各 1）、「括号与收尾 4」实为花括号 **2** + 逗号 **1** = **3**，两处误差恰好抵消才凑成 14）'
OLD_LM='（键名加冒号加空白加末尾方括号）'
NEW_LM='（1({) + 12(, "bounds": ) + 1(})；**R176 订正**：原写「键名加冒号加空白加末尾方括号」—— 该 14 B 里方括号 **0** 个（文件的 ] 在偏移 17,624,353、末字节 } 在 17,624,354），且空格实为 2 个）'

assert st.count(OLD_ST)==1, st.count(OLD_ST)
assert lm.count(OLD_LM)==1, lm.count(OLD_LM)
st2=st.replace(OLD_ST,NEW_ST+SUB_ST)
lm2=lm.replace(OLD_LM,NEW_LM)
print('ST bytes %d -> %d (%+d)'%(len(st.encode()),len(st2.encode()),len(st2.encode())-len(st.encode())))
print('LM bytes %d -> %d (%+d)'%(len(lm.encode()),len(lm2.encode()),len(lm2.encode())-len(lm.encode())))
print()
print('--- NEW STMT CTX ---')
i=st2.find('1({)')
print(repr(st2[i-120:i+260]))
print()
print('--- NEW LIM CTX ---')
j=lm2.find('1({)')
print(repr(lm2[j-120:j+320]))
# 逐字节 diff 形状（autojunk=False，S-617）
sm=difflib.SequenceMatcher(None,st,st2,autojunk=False)
ops=[o for o in sm.get_opcodes() if o[0]!='equal']
print('stmt opcodes',[(o[0],o[2]-o[1],o[4]-o[3]) for o in ops])
sm2=difflib.SequenceMatcher(None,lm,lm2,autojunk=False)
ops2=[o for o in sm2.get_opcodes() if o[0]!='equal']
print('lim opcodes',[(o[0],o[2]-o[1],o[4]-o[3]) for o in ops2])

print()
print('--- verification ---')
print('OLD_ST gone from new stmt:', st2.count(OLD_ST)==0)
print('NEW_ST present exactly once:', st2.count(NEW_ST)==1, st2.count(NEW_ST))
print('OLD_LM gone:', lm2.count(OLD_LM)==0)
print('st2 char delta',len(st2)-len(st),'byte delta',len(st2.encode())-len(st.encode()))
sm=difflib.SequenceMatcher(None,st,st2,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal': print(' stmt',tag,'del',i2-i1,'ins',j2-j1)
sm2=difflib.SequenceMatcher(None,lm,lm2,autojunk=False)
for tag,i1,i2,j1,j2 in sm2.get_opcodes():
    if tag!='equal': print(' lim',tag,'del',i2-i1,'ins',j2-j1)
