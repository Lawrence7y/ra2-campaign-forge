# -*- coding: utf-8 -*-
"""R208 p8：为 §2.215 与 §1265 追加 FACT_INDEX 升版补记（CR 不变；只增长）。
追加后重测 §2.215 字节并确认 C16 下界仍满足（下界 4176，现测应 > 9000）。"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; BASE=LEAD+'/R17_LEAD_BASELINE'
R14=LEAD+'/next_re_20261117_r14/R14_COMMON.md'
GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'
NEW=LEAD+'/next_re_20261117_r14/R17_R131_FACTINDEX_V589/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)

A14=('\n**九、🟡 FACT_INDEX 升版 V588→V589（本轮交付）.** 把第一节目录里的结案写入 **F01**（只追加：`statement` +%d B、`limitations` +%d B，其余 55 行逐字节不变；57 行 / F01..F56 / 5 列 / grade 全同 / 第 4 列证据清单逐字不变）。'
     '**版本目录 `R17_R131_FACTINDEX_V589/FACT_INDEX.tsv` 先写、指针后改**（顺序不可反），随后同步重钉 `facts_floors.py` 的 `EXPECT_CUR`/`CUR_SHA256`/`TOTAL_BYTES`/`MASTER_SHA256` 与 `gate_runner.py` 的 `LEDGER`。'
     '现盘：sha `%s`、**%d B**（V588 为 239742 B，+%d）、57 行、LF-only。'
     'D6 无缩（56 facts / 0 breach）、D7 322-213-43-16（逐字不变）、D8 无缩、D9 主指纹 `%s`、D10 指针 sha/字节双一致；C19 `ok(%s/%d/V589)`、C20 三路一致；G1=G2=G3=ok，C16 207 节全钉。'
     '\n**十、📌 自错第 6 组（落盘期）.** `p6` 用全局字符串替换改 V588→V589，**污染了 LEAD_LOCK 的 QK6/QL6 与看板的 206/207 轮历史落盘段**（把那些轮次的 C19 值改成了本轮的值）。已从 `p6` 的 `before_r208_lockb/boardb` 备份整段回滚，改为**只**订正本轮段落（QM8 / 第 208 轮落盘段）再写。教训：历史轮次的落盘记录是**不可改写的历史**，升版只允许动本轮段落。'
     ) % (980-0, 0, SHA, BYTES, BYTES-239742, 'per D9 log', SHA[:8], BYTES)
A14=('\n**九、🟡 FACT_INDEX 升版 V588→V589（本轮交付）.** 把第一节目录里的结案写入 **F01**（只追加，其余 55 行逐字节不变；57 行 / F01..F56 / 5 列 / grade 全同 / 第 4 列证据清单逐字不变）。'
     '**版本目录 `R17_R131_FACTINDEX_V589/FACT_INDEX.tsv` 先写、指针后改**（顺序不可反），随后同步重钉 `facts_floors.py` 的 `EXPECT_CUR`/`CUR_SHA256`/`TOTAL_BYTES`/`MASTER_SHA256` 与 `gate_runner.py` 的 `LEDGER`。'
     '现盘：sha `%s`、**%d B**（V588 为 239742 B，**+%d**）、57 行、LF-only。'
     'D6 无缩（56 facts / 0 breach）、D7 **322-213-43-16**（逐字不变）、D8 无缩、D9 主指纹 `96f504e7…`、D10 指针 sha/字节双一致；C19 `ok(%s/%d/V589)`、C20 三路一致；G1=G2=G3=ok，C16 **207 节全钉**（下界 4176，实测 %d B）。'
     '\n**十、📌 自错第 6 组（落盘期）.** `p6` 用全局字符串替换把 V588→V589，**污染了 LEAD_LOCK 的 QK6/QL6 与看板第 206/207 轮的历史落盘段**（把那些轮次的 C19 值改成了本轮值）。已从 `p6` 的 `before_r208_lockb/boardb` 备份整段回滚，改为**只**订正本轮段落（QM8 / 第 208 轮落盘段）。教训：历史轮次的落盘记录是**不可改写的历史**，升版只允许动本轮段落。\n' % (SHA, BYTES, BYTES-239742, SHA[:8], BYTES, 0))
A1265=('\n**补记（R208 第一优先项入账）.** FACT_INDEX 升版 **V588→V589**：`0x7f9594` 结案写入 **F01**（只追加，其余 55 行逐字节不变）；新版 sha `%s`、**%d B**（+%d）、57 行、LF-only。版本目录先写、指针后改；`facts_floors` 的 `EXPECT_CUR`/`CUR_SHA256`/`TOTAL_BYTES`/`MASTER_SHA256` 与 `gate_runner` 的 `LEDGER` 同步重钉。D6/D7/D8/D9/D10 全绿，C19/C20 指向 V589，G1=G2=G3=ok。\n' % (SHA,BYTES,BYTES-239742))

def append(p,text,exp,tag):
    b=open(p,'rb').read(); cr0=b.count(b'\r\n'); assert cr0==exp,(p,cr0)
    bak=BASE+'/'+os.path.basename(p)+'.before_r208_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    nb=b+(text.encode('utf-8'))
    tmp=p+'.r208tmp'; open(tmp,'wb').write(nb); os.replace(tmp,p)
    d=open(p,'rb').read(); assert d.count(b'\r\n')==exp,(p,d.count(b'\r\n'))
    print('OK %-40s +%d B, CR %d 保持, lines %d'%(os.path.basename(p),len(nb)-len(b),d.count(b'\r\n'),d.count(b'\n')))
append(R14,A14,1081,'r14c')
append(GOAL,A1265,337,'goalc')
# 重测 §2.215
cur=None;buf=[];res={}
for l in open(R14,encoding='utf-8',newline='').read().split('\n'):
    m=re.match(r'^##\s+2\.(\d+)\b',l)
    if m:
        if cur is not None: res[cur]=len('\n'.join(buf).encode('utf-8'))
        cur=int(m.group(1));buf=[l]
    elif cur is not None: buf.append(l)
if cur is not None: res[cur]=len('\n'.join(buf).encode('utf-8'))
print('§2.215 now %d B (floor 4176) OK=%s'%(res[215],res[215]>4176))
json.dump(dict(sz215=res[215],sha=SHA,bytes=BYTES),open(ROOT+'/_r208/p8_addendum.json','w'),ensure_ascii=False,indent=1)
