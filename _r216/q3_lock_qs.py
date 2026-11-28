# -*- coding: utf-8 -*-
"""R216 q3：LEAD_LOCK 追加 QS 段（CR 保持 137）。"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'; F=ROOT+'/lead/LEAD_LOCK'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
b0=open(F,'rb').read(); h0=hashlib.sha256(b0).hexdigest()
print('LEAD_LOCK 旧 sha=%s bytes=%d CR=%d'%(h0[:16],len(b0),b0.count(b'\r')))
assert b0.count(b'\r')==137
assert b'## QS \xc2\xb7 R216' not in b0
dst=BASE+'/LEAD_LOCK.before_r216_QS_20261128.bak'
assert not os.path.exists(dst); open(dst,'wb').write(b0)
SEC = '''
## QS · R216（2026-11-28）· ?AVAbstractClass@@ 四子对象 MI 布局（slot8 写 4 张 vftable 字节实证）；QI 四 IID 全解；律 U 101/101；律 W 违例 360 条全为正偏移；V599

**QS1. 🔴 四子对象 MI 布局（字节实证）.** `0x7e1f50`(mdisp=0,24 槽) 的 slot8=`0x4105a0` 前 11 条即写四个 vfptr：
`[esi]=0x7e1f50` / `[esi+4]=0x7e1f34` / `[esi+8]=0x7e1f2c` / `[esi+0xc]=0x7e1f24`（四条 `c7 46 xx` 全字节在 §2.224），
随后 `test al,1` / `je` / `call 0x7c8b3d` / `ret 4`。四张视图 mdisp 逐一对上 **0/4/8/12**，pTD 同 **0x8177c8**、pCHD 同 **0x7fb108**。
主视图基址作为任何视图槽值出现 **0** 次 ⇒ 只在构造/析构被写，不被继承槽复用。

**QS2. 🔴 QueryInterface 四 IID 全解.** slot0=`0x410260`（150 B），`repe cmpsd`(ecx=4) 依次比对：
`0x7f7c90` **00000000-0000-0000-C000-000000000046**、`0x7f7c80` **00000109-…**（IPersistStream）、
`0x7f7c70` **0000010C-…**（IPersist）、`0x7e9ae0` **170DAC82-12E4-11D2-8175-006008055BB5**。
失败 **0x80004002**，出参空 **0x80004003**；匹配第 4 个接口时 `lea ecx,[ebx+4]` 交出 **this+4**。
push imm32 引用数：`0x7f7c90` **56** / `0x7f7c80` **60** / `0x7f7c70` **0** / `0x7e9ae0` **0**
（后两个只在本函数以 `mov edi,imm32` 装入）⇒ 「扫不到引用」有解释，不是漏扫。

**QS3. 🔴 24 槽全解，0 条未解.** 字节组去重 **15** 种；`0x4c9150`(`33c0c3`) 被 **7** 槽共用（3/5/6/11/12/15/16）。
字段：**+0x10 = dword**（slot13 `mov eax,[esi+0x10]` → call `0x4a1d50`）、**+0x20 = byte 标志**（slot4 `mov dl,[ecx+0x20]` + sete，
slot13 `mov cl,[esi+0x20]` → call `0x4a1ca0`）。`0x4a1d50` 体 23 B（`push 4` + `lea edx,[esp+4]` + `call 0x4a1de0` + `ret 4`，E8 站点 **460**）；
`0x4a1ca0` 体 134 B（环缓冲插入，容量 `cmp eax,4`，E8 站点 **331**）。

**QS4. 🔴 律 U 101/101 反例 0.** mdisp≠0 视图 **260** 张；slot0 为 adjustor thunk 者 **101** 张，全部 `N == self.mdisp − target.mdisp`。
组合 (4,0,4)×**91** / (24,0,24)×**6** / (1728,0)/(44,0)/(40,0)/(36,0) 各 **1**。其余 **159** 张首指令 = `ret`78 / `xor`75 / `mov`3 / `sub`3。
AbstractClass 三条次级视图 slot0 = `0x4105e0`/`0x4105f0`/`0x410600`，字节均 `836c240404e9xxxxxxxx`。

**QS5. 🔴 律 T → 律 W，360 违例全为正偏移.** 律 T（disp==mdisp）：**4202** 命中，符 **3876**(92.24%)、违例 **326**
（B 内嵌成员 201 / C 近邻 79 / A off=0 写次级视图 46）。律 W（disp+delta==mdisp）：线性扫 **1,394,300** 条指令
（`disasm_lite`+`skipdata`，64 KB 分块）后 C7 命中 **4195**，可反解 delta **2911**，符 **2551**、违例 **360**；
**360 条违例的 (disp+delta)−mdisp 全部 > 0，0 条 ≤ 0** ⇒ 可用判据是**不等式**「写入偏移 ≥ 视图 mdisp」。
差值按 (类,值) 强聚合 = 宿主成员内嵌偏移：`?AVGenericNode@@` +16×11 / +4×7 / +28×4、`?AV?$rc_ptr@VWDTState@@@@` +8×11、
`?AVTactical@@` +3496×4、`?AV?$DynamicVectorClass@UDrawRecord@FoggedObjectClass@@@@` +92×6。

**QS6. 🟡 口径订正 3 条（0 条进结论）.** ①m9 用 `isdigit()` 解析十六进制 disp 丢掉 `0xc` ⇒ 正控只 3/4 假 FAIL，
改 `int(p,0)` 后 **4/4**；②m8 的 try-align 反控失败（命中点前移 50 B 仍有 **227/300** 能"对齐"）⇒ 该法**弃用**，
改一次性线性扫描建表，前驱唯一；③主会话把 EX1 的 `call 0x4a1ca0` 站点 **331** 误记为 1，E8 字节口径复算 **331** 一致
⇒ 属主会话读错，非子代理错。

**QS7. 🟡 跨家族（§2.12 规则 D 复算）.** #559（hy4 exec）`_r216/ex1_field.py` / `ex1.json`（92,748 B）/ `ex1_out.txt`，
5 条正反控全 PASS（`0x20` 113 vs `0x24` 92、`0x10` 8099 vs `0x14` 5649、目标 +1 命中 0）。
主会话独立复算 `_r216/m11_recheck_ex1.py`：E8 站点 **460/331**、两函数末指令 `ret 4`、`call 0x4a1de0` 存在、
`[reg+0x20]` byte 读 16 / 写 34、`[reg+0x10]` dword 读 2439 / 写 3263（均排除 esp/ebp）全部一致。
#560（deepseek audit 只读）产物 `_r216/audit_ds1..4.py` 与 `audit_ds_views.json`（255,176 B）。

**QS8. 🟡 落盘与门禁.** R14_COMMON **§2.224** CR 保持 **1081**（1913694→1922387 B）；GOAL **§1274** CR 保持 **337**
（5462250→5465474 B）；本段 **QS** CR 保持 **137**；STATUS_BOARD 第 216 轮 CR 保持 **0**。
**FACT_INDEX V598→V599**（仅 F29 一行，其余 **56 行逐字节不变**），sha `45d366ae`→**`616a86e2`**、275368→**277566** B（+2198）；
`facts_floors` 的 CUR_SHA256/TOTAL_BYTES/`FLOORS['F29'].stmt`→**12751**/MASTER `87f42300`→**`b058464c`**；`gate_runner.LEDGER`→V599；
`C16_FLOORS` 纳入 **224:8692**（**216** 节，sha `d1d2aa6e`→**`89193ad4`**）。三门实测 **exit 0**（check_disc live 31 / facts_floors D0–D10 / gate_runner G1 G2 G3a–G3f）。

**QS9. ⚪ 未取得.** ①MI 四子对象的**接口语义**归属（哪个 IID 对应哪个子对象）仍未证，QI 只给 4 个常量与「第 4 个交出 this+4」；
②`0x4a1ca0` 环缓冲容量 4 的上层含义；③三全局 `0x887680/84/88` 运行期初值（virt-only，须 win-main）；
④**360** 条律 W 违例的逐类内嵌偏移表（本轮只给 top）；⑤主视图 9958 个 slot≥3 槽语义（本轮只解 AbstractClass 24 槽）；
⑥F23/F35 grade；⑦C7 三死分支、C11 十二 ID。
'''
s1=(b0.decode('utf-8')+SEC).encode('utf-8')
assert s1.count(b'\r')==137, s1.count(b'\r')
open(F,'wb').write(s1)
r=open(F,'rb').read(); assert r.count(b'\r')==137 and b'## QS ' in r
print('新 sha=%s bytes=%d CR=%d LF=%d'%(hashlib.sha256(r).hexdigest()[:16],len(r),r.count(b'\r'),r.count(b'\n')))
json.dump({'old':h0,'new':hashlib.sha256(r).hexdigest(),'old_bytes':len(b0),'new_bytes':len(r)},
 open(ROOT+'/_r216/q3.json','w'),indent=1)
