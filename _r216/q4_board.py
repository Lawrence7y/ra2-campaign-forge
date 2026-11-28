# -*- coding: utf-8 -*-
"""R216 q4：STATUS_BOARD 追加第 216 轮（CR 保持 0，总行数 <= 300）。"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'; F=ROOT+'/lead/next_re_20261117_r14/STATUS_BOARD.md'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
b0=open(F,'rb').read(); h0=hashlib.sha256(b0).hexdigest()
n0=b0.count(b'\n'); print('BOARD 旧 sha=%s bytes=%d CR=%d 行=%d'%(h0[:16],len(b0),b0.count(b'\r'),n0))
assert b0.count(b'\r')==0
assert n0<260, '需先归档'
assert b'## R216 (' not in b0
dst=BASE+'/STATUS_BOARD.md.before_r216_20261128.bak'
assert not os.path.exists(dst); open(dst,'wb').write(b0)
SEC = '''## R216 (2026-11-28) · ?AVAbstractClass@@ 四子对象 MI 布局字节实证 + QI 四 IID 全解 + 律 U 101/101 + 律 W 违例 360 全为正偏移

**一、MI 布局.** 主视图 `0x7e1f50`(mdisp=0,24 槽) 的 slot8=`0x4105a0` 前 11 条指令即写 4 个 vfptr：
`[esi]=0x7e1f50` / `[esi+4]=0x7e1f34` / `[esi+8]=0x7e1f2c` / `[esi+0xc]=0x7e1f24`，随后 `test al,1` → `call 0x7c8b3d`，`ret 4`。
四张视图 mdisp = **0/4/8/12** 逐一对上，pTD 同 **0x8177c8**、pCHD 同 **0x7fb108**；主视图基址作为槽值 **0** 次。

**二、QI 四 IID.** slot0=`0x410260`（150 B）用 `repe cmpsd`(ecx=4) 比对：
`0x7f7c90`=00000000-0000-0000-C000-000000000046、`0x7f7c80`=00000109(IPersistStream)、
`0x7f7c70`=0000010C(IPersist)、`0x7e9ae0`=170DAC82-12E4-11D2-8175-006008055BB5。
失败 `0x80004002`、出参空 `0x80004003`、匹配第 4 个接口交出 **this+4**。push imm32 引用 56/60/0/0 ⇒ 后两个"扫不到"有解释。

**三、24 槽全解.** 0 条未解，字节组去重 15 种，`0x4c9150`(`33c0c3`) 被 7 槽共用。字段 **+0x10=dword**、**+0x20=byte 标志**。
`0x4a1d50`(23 B, E8 站点 460) 与 `0x4a1ca0`(134 B, 环缓冲 `cmp eax,4`, E8 站点 331) 为 slot13 的两条调用目标。

**四、律 U 101/101.** mdisp≠0 视图 260 张，slot0 为 adjustor thunk 者 101 张全部 `N == mdisp_self − mdisp_target`，反例 0；
组合 (4,0)×91 / (24,0)×6 / (1728,0)/(44,0)/(40,0)/(36,0) 各 1。

**五、律 T → 律 W.** 律 T 命中 4202（符 3876 / 违例 326）；律 W 扫 1,394,300 条指令后命中 4195、可反解 2911、
符 2551 / 违例 **360**，且 360 条差值**全部 > 0、0 条 ≤ 0** ⇒ 新判据是不等式「写入偏移 ≥ 视图 mdisp」；
差值按 (类,值) 强聚合 = 宿主成员内嵌偏移（`?AVGenericNode@@` +16×11 等）。

**六、订正 3 条.** ①`isdigit()` 丢十六进制 `0xc` ⇒ 正控 3/4 假 FAIL，改 `int(p,0)` 后 4/4；②try-align 反控失败（前移 50 B 仍 227/300 能"对齐"）⇒ 弃用，改线性扫描建表；③主会话把 EX1 的 `call 0x4a1ca0` 站点 331 误记为 1（复算 331 一致），属主会话读错。

**七、落盘.** §2.224(CR 1081) / §1274(CR 337) / QS(CR 137) / 本段(CR 0，214→本段后行数见收口)。
FACT_INDEX **V598→V599** 仅 F29 一行，275368→**277566** B，sha `45d366ae`→**`616a86e2`**；
facts_floors CUR/TOTAL/F29=12751/MASTER→`b058464c`、gate_runner LEDGER→V599、C16_FLOORS 纳入 **224:8692**（sha→`89193ad4`）。三门 exit 0。
'''
s1=(b0.decode('utf-8')+('\n'+SEC if not b0.decode('utf-8').endswith('\n') else SEC)).encode('utf-8')
assert s1.count(b'\r')==0
open(F,'wb').write(s1)
r=open(F,'rb').read()
print('新 sha=%s bytes=%d 行=%d CR=%d'%(hashlib.sha256(r).hexdigest()[:16],len(r),r.count(b'\n'),r.count(b'\r')))
assert r.count(b'\n')<=300
json.dump({'old':h0,'new':hashlib.sha256(r).hexdigest(),'old_lines':n0,'new_lines':r.count(b'\n')},
 open(ROOT+'/_r216/q4.json','w'),indent=1)
