# -*- coding: utf-8 -*-
"""R216 q2：GOAL_THREE_TARGETS 追加 §1274（CR 保持 337）。"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'; F=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
b0=open(F,'rb').read(); h0=hashlib.sha256(b0).hexdigest()
print('GOAL 旧 sha=%s bytes=%d CR=%d'%(h0[:16],len(b0),b0.count(b'\r')))
assert b0.count(b'\r')==337
assert b'## \xc2\xa71274 ' not in b0
dst=BASE+'/GOAL_THREE_TARGETS_20261018.md.before_r216_1274_20261128.bak'
assert not os.path.exists(dst); open(dst,'wb').write(b0)
SEC = '''
## §1274 · R216（2026-11-28）· ?AVAbstractClass@@ 四子对象 MI 布局字节实证（slot8 写 4 张 vftable）+ QI 四 IID 全解 + 律 U 101/101 + 律 W 360 违例全为正偏移；FACT_INDEX V599

**一 · MI 布局.** `0x7e1f50`(mdisp=0,24 槽) 的 slot8=`0x4105a0` 在前 11 条指令里直接写四个 vfptr：
`[esi]=0x7e1f50` / `[esi+4]=0x7e1f34` / `[esi+8]=0x7e1f2c` / `[esi+0xc]=0x7e1f24`，随后 `test al,1` 决定
`call 0x7c8b3d`，`ret 4`。四张视图在视图表内 mdisp 逐一对上（0/4/8/12），pTD 同 `0x8177c8`、pCHD 同 `0x7fb108`。
主视图基址作为槽值出现 **0** 次。⇒ R91 的 vt==[esi] 对象模型在基类上抬为「vt 分区段写入」的字节实证。

**二 · QueryInterface 四 IID.** slot0=`0x410260`，`repe cmpsd`(ecx=4) 比对四个 16 字节常量：
`0x7f7c90`=00000000-0000-0000-C000-000000000046、`0x7f7c80`=00000109-…（IPersistStream）、
`0x7f7c70`=0000010C-…（IPersist）、`0x7e9ae0`=170DAC82-12E4-11D2-8175-006008055BB5。
失败 `0x80004002`，出参空 `0x80004003`，匹配第 4 个接口时交出 **this+4**。引用计数：`0x7f7c90` push 56 处、
`0x7f7c80` 60 处、`0x7f7c70`/`0x7e9ae0` 各 0 处（仅本函数 `mov edi,imm32` 装入）。

**三 · 24 槽全解.** 无一条未解；字节组去重 15 种，`0x4c9150`(`33c0c3`) 被 7 个槽共用。
字段：`+0x10`=dword（slot13 送进 0x4a1d50）、`+0x20`=byte 标志（slot4 读判、slot13 序列化）。
slot1/slot2 均为 `b801000000c20400`（mov eax,1 / ret 4）。

**四 · 律 U 101/101 反例 0.** mdisp≠0 视图 260 张，slot0 为 adjustor thunk 者 101 张，
全部满足 `N == self.mdisp − target.mdisp`；组合 (4,0)×91 / (24,0)×6 / (1728,0)/(44,0)/(40,0)/(36,0) 各 1。
其余 159 张 slot0 首指令 = ret(78)/xor(75)/mov(3)/sub(3)。

**五 · 律 T → 律 W.** 律 T（disp==mdisp）4202 命中，符 3876 / 违例 326（B 内嵌 201 / C 近邻 79 / A off=0 46）。
律 W（disp+delta==mdisp）扫 1,394,300 条指令后 C7 命中 4195，可反解 2911，符 2551 / 违例 **360**，
且 **360 条违例的差值全部 > 0、0 条 ≤ 0** ⇒ 新判据是**不等式** `写入偏移 ≥ 该视图 mdisp`。
差值按 (类,值) 强聚合（`?AVGenericNode@@` +16×11、`?AV?$rc_ptr@VWDTState@@@@` +8×11、`?AVTactical@@` +3496×4）
⇒ 违例族 = 宿主成员内嵌偏移，不是 thunk 反例。

**六 · 口径订正 3 条（0 条进结论）.** ①m9 用 `isdigit()` 解析十六进制 disp 丢掉 `0xc` ⇒ 正控 3/4 假 FAIL，改 `int(p,0)` 后 4/4；
②m8 try-align 反控失败（命中点前移 50 B 仍有 227/300 能"对齐"）⇒ 该法弃用；③主会话把 EX1 的 `call 0x4a1ca0`
站点 331 误记为 1（E8 复算 331 一致），属主会话读错，非子代理错。

**七 · 落盘.** R14_COMMON **§2.224**（CR 1081）、本段 CR 337、LEAD_LOCK QR→QS、STATUS_BOARD 第 216 轮（CR 0）。
FACT_INDEX **V598→V599**（仅 F29 一行，275368→277566 B，+2198），sha `45d366ae`→`616a86e2`；
`facts_floors` CUR/TOTAL/FLOORS['F29']=12751/MASTER `87f42300`→`b058464c`、`gate_runner.LEDGER`→V599；
`C16_FLOORS` 纳入 **224:8692**（216 节，sha `d1d2aa6e`→`89193ad4`）。三门实测 exit 0。
'''
s1=(b0.decode('utf-8')+SEC).encode('utf-8')
assert s1.count(b'\r')==337, s1.count(b'\r')
open(F,'wb').write(s1)
r=open(F,'rb').read(); assert r.count(b'\r')==337 and b'## \xc2\xa71274' in r
print('新 sha=%s bytes=%d CR=%d LF=%d'%(hashlib.sha256(r).hexdigest()[:16],len(r),r.count(b'\r'),r.count(b'\n')))
json.dump({'old':h0,'new':hashlib.sha256(r).hexdigest(),'old_bytes':len(b0),'new_bytes':len(r)},
 open(ROOT+'/_r216/q2.json','w'),indent=1)
