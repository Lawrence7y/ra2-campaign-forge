#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 p5：把台账升版与三门结果补记进 R14_COMMON §2.209（追加到文件末尾 = 该节末尾）。
纪律：wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
追加只增长，故 C16 floor（下界）仍成立。
"""
import hashlib, os, re, time
ROOT='/home/t628/projects/ra2-campaign-forge'
P=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
BASE=ROOT+'/R17_LEAD_BASELINE'
def sha(b): return hashlib.sha256(b).hexdigest()
STAMP=time.strftime('%Y%m%d_%H%M%S')
b=open(P,'rb').read(); old=sha(b)
assert b.count(b'\r')==1081, b.count(b'\r')
# 硬闸：§2.209 必须是最后一节
i=b.rfind(b'## 2.209')
assert i>0 and b.find(b'\n## ', i)==-1, '2.209 must be the last section'
SEC_OLD=len(b[i:].rstrip(b'\n\n'))
NOTE = """
**十二、🟡 台账与三门（写盘顺序：新版本目录先写，指针后改，最后同步 runner）.** 台账 **V586 → V587**：只改 **F01** 一行（本条正是 RTTI 类名恢复链的宿主事实行），追加本轮 CHD/BCD/BCA 的布局实证与两条充要律；其余 **55 行逐字节未变**（`G2b`）。F01 现盘 `stmt 458 → 6847 B`、`lim 14490 → 15247 B`、`evid 183 → 529 B`、`EVID 3 → 20 条`；台账总字节 **225848 → 233340 B**、sha **07a55ac3… → 062111ba…**、`ITEMS 295 → 312`、`UNIQ 187 → 203`、`LOST 43 / LOST_UNIQ 16` 逐键未变、MASTER **a8a54e49… → 65b70fc6…**。升版脚本 `_r204/p3_repin_v587.py` 的 **fail-closed 硬闸**：先用旧常量复算旧 MASTER 必须命中旧 pin，再校验 17 条新证据路径全部可解析、LOST 多重集逐键不变、三条反控（F01 lim floor +1 / EVIDB +1 / TOTAL_BYTES +1）都让 MASTER 变。**自错两处当场抓出**：① `G3o` 首版把 `UNIQ` 增量写成「新条目数 17」，实测 **16**（`lead/next_re_20261117_r14/R14_COMMON.md` 已被既有行引用过，去重后不新增唯一路径）；② 订正时又把差集写成 `set(newitems) - uniq`（`uniq` 取自已追加后的现盘，差集恒空），改为从旧常量 `EVID` 还原 `uniq_before` 并先用它复算旧 `UNIQ` 作硬闸。两处均**未写盘**（`★ fail-closed` 拦下），第三跑才落盘。**三门**：`check_disc.py` **exit 0**（C16 节数 **200 → 201**、新增 209 钉 **5313** = 实测 10626//2，C16_FLOORS_SHA256 `1683ee24… → 2a4374a3…`；C19 ok(062111ba/233340/V587)；C20 ok(V587)）；`facts_floors.py` **exit 0**（D7 `items=312 uniq=203 lost=43/16`、D8 233340、D9+D10 双一致）；`gate_runner.py` **G1=G2=G3=ok**（G3c/G3d 的回显文案仍写「V553」，是 runner 里的**静态标签字符串**、不参与判据，本轮按最小改动未动，如实登记）。**C20 首次变红的定位**：`_r161/gate_runner.py:51` 的 `LEDGER` 硬编码旧目录，指针升版后三方不一致 —— 说明 C20 这条门禁**确实会咬人**（不是恒绿），本轮按「先写目录、再改指针、最后同步 runner」的顺序通过。
"""
core=NOTE.replace('\r\n','\n').strip('\n')
head='\n' if b.endswith(b'\n') else '\n\n'
new=b+(head+core+'\n\n').encode('utf-8')
bak='%s/R14_COMMON.md.%s.bak'%(BASE,STAMP)
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
assert sha(open(bak,'rb').read())==old
open(P,'wb').write(new)
rb=open(P,'rb').read()
assert rb.count(b'\r')==1081, rb.count(b'\r')
assert sha(rb)!=old and rb.startswith(b)
j=rb.rfind(b'## 2.209'); assert j>0 and rb.find(b'\n## ', j)==-1
SEC_NEW=len(rb[j:].rstrip(b'\n\n'))
print('2.209 bytes %d -> %d ; sections=%d ; CR=%d' % (SEC_OLD, SEC_NEW, len(re.findall(rb'^##\s+2\.(\d+)\b', rb, re.M)), rb.count(b'\r')))
print('OK')
