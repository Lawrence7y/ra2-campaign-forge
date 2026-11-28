# -*- coding: utf-8 -*-
"""R217 p2：GOAL §1275 / LEAD_LOCK QK / STATUS_BOARD 第 217 轮。
写入纪律同上；CR 契约 GOAL 337 / LOCK 137 / BOARD 0；新增内容一律全 LF。
看板纪律：写前若行数 >= 260 必须先归档最早 2 段（保持 ARCH CR=2952）。当前 240 行 < 260 => 不归档。
"""
import os,hashlib,json,re
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/R17_LEAD_BASELINE'
STAMP='20261128_1830'
def backup(tag,path):
    b=open(path,'rb').read(); h=hashlib.sha256(b).hexdigest()
    dst='%s/%s.before_r217_%s_%s.bak'%(BASE,os.path.basename(path),tag,STAMP)
    if os.path.exists(dst):
        assert open(dst,'rb').read()==b,'BACKUP DIFFERS '+dst
        return b,h
    fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb') as f: f.write(b)
    return b,h
# ---------- GOAL §1275 ----------
GP=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
b0,h0=backup('GOAL',GP)
assert b0.count(b'\r')==337 and h0.startswith('5ca5e1899bbbddaf')
assert b0.endswith(b'\n')
G="""## §1275 R217（2026-11-28）· 槽数上限截断 + 9958 口径 + QI 三读模型 + 转发桩 slot3 律

**① 🔴 槽数上限 256 是错的：6 张表真槽数 309..344.** UnitClass `0x7f5c70`=344、InfantryClass `0x7eb058`=343、
AircraftClass `0x7e22a4`=341、FootClass `0x7e8c94`=341、BuildingClass `0x7e3ebc`=322、TechnoClass `0x7f4960`=309。
全 1218 表：无上限 14044 / cap256 13580 / 差 464。零槽表 4 张与 `0x7e8278` 共用 COL `0x800040`
（`?AVDropPodLocomotionClass@@`, mdisp=4）⇒ 视图级 mdisp≠0=264、COL 记录级=260、差 4 由此而来。
反控：判据放宽到 `.text`∪`.rdata` 总槽暴涨 142625（+128581）⇒ `.text` 判据必要。

**② 🔴 9958 口径锁定 = 无上限.** 主视图（每 pCHD 族 mdisp==0 那张）954 张；slot≥3 **无上限 9958（与 R210 差 0）**、
**cap256 9494（差 −464）**. ⇒ R210 的 9958 结论正确、不需订正，但后续脚本若带 cap 256 必少 464，本段钉死口径。
全表口径 slot≥3：无上限 10814 / cap256 10350。反控：主视图放松成「族内任意一张」⇒ 分母 1218≠954。

**③ 🔴 QI `0x410260` 实参模型：orig = 0xc / 0xc / 0x8.** 原栈偏移 = 指令内 disp − 累计 push delta
（自错 E5：曾误用 `+delta`）。`8b44240c`@0x410260→orig+0xc、`8b54240c`@0x410272→orig+0xc、`8b5c2410`@0x41028c→orig+0x8。
`ret 0xc` 三栈参（thiscall ⇒ this 走 ecx）⇒ **orig+4 全程未被读**；输出指针唯一在 orig+0xc。
与子代理 card A 的「orig+8=IID、orig+0xc=ppv」一致；主会话中途结论已撤回。

**④ 🔴 转发桩槽位律：76 处全在 mdisp=4 视图的 slot 3，K 恒 `0x2c`.** 字节 `8b442404 8b50fc 8d48fc ff522c c20400`
（`0x410210`，16 B）。`edx` 装 vftable、`ecx` 装对象指针 ⇒ `call` 寄存器 == `mov` 目标（自错 E4）。
主视图 slot11 落点：`0x4c9150`×9 + 67 个各 1 次。反控：`-4`→`-8` 命中 0。

**⑤ 律 U 独立复现 101/101/0**（card A #562 hy4 与主会话 `m13` 双家族同值）。**本轮不新增律 U/律 V**（R210 §2.218 已立）。

**⑥ 自错 5 条 0 进结论**：m3/m4 首个 ret 截断；m5 律 V 空判据（184 视图仅 84 可判，已降级）；m7 族表查错键；
m10 call/lea 寄存器错绑；m11 `orig=X+delta` 符号错。**card A 正确处已采信**（含「COL +0x14 == 自身」实测 0 命中、值 0 者 1009）。

**⑦ 未取得**：①`0x4a1ca0` 环缓冲容量 4 的上层语义；②三全局 `0x887680/84/88` 运行期初值（virt-only，须 win-main）；
③360 条律 W 违例逐类内嵌偏移全表（只给 top）；④6 张超 256 表的 slot≥256 段语义（共 464 槽未查）；
⑤零槽视图 `0x877000/10`、`0x87b17c/8c` 为何在 `.data` 而非 `.rdata`；⑥F23/F35 grade；⑦C7 三死分支、C11 十二 ID。
"""
new=b0+('\n'+G).encode('utf-8')
assert new.count(b'\r')==337
open(GP,'wb').write(new)
c=open(GP,'rb').read(); assert c.startswith(b0) and c.count(b'\r')==337
print('[GOAL] §1275 bytes %d -> %d cr=%d sha %s -> %s'%(len(b0),len(c),c.count(b'\r'),h0[:16],hashlib.sha256(c).hexdigest()[:16]))
# ---------- LEAD_LOCK QK ----------
LP=ROOT+'/lead/LEAD_LOCK'
b1,h1=backup('LOCK',LP)
assert b1.count(b'\r')==137 and h1.startswith('49f92644189e68d2')
assert b1.endswith(b'\n')
L="""**QK. 🔴 槽数上限 256 截断实证.** 取消上限后 6 张表真槽数 **309/322/341/341/343/344**
（Unit `0x7f5c70` / Infantry `0x7eb058` / Aircraft `0x7e22a4` / Foot `0x7e8c94` / Building `0x7e3ebc` / Techno `0x7f4960`）。
全 **1218** 表：无上限 **14044** 槽，cap256 **13580**，**差 464**。零槽 4 张（`0x877000`/`0x877010`/`0x87b17c`/`0x87b18c`）
与 `0x7e8278` 共用 COL **`0x800040`**（`?AVDropPodLocomotionClass@@`, mdisp=4）⇒ 视图级 mdisp≠0 **264** vs COL 记录级 **260**，差 4 即此。
反控：判据含 `.rdata` ⇒ 总槽 **142625**（+128581）。正控：AbstractClass 四视图 24/6/1/1 与 R216 一致。

**QK2. 🔴 9958 口径 = 无上限.** 主视图 954 张（每 pCHD 族 mdisp==0）：slot≥3 **无上限 9958（R210 差 0）**、**cap256 9494（−464）**。
⇒ R210 结论正确不需订正；口径钉死：**统计主视图 slot≥3 时严禁带 cap 256**。全表 slot≥3 无上限 **10814** / cap256 **10350**。
反控：主视图口径放松成「族内任意一张」⇒ **1218 ≠ 954**。

**QK3. 🔴 QI `0x410260` 三处栈读 orig = 0xc/0xc/0x8.** 公式 **orig = 指令内 disp − 累计 push delta**
（自错 E5：曾用 `+delta` 得 0x18 并误判）。读点：`8b44240c`@`0x410260`→orig+0xc；`8b54240c`@`0x410272`→orig+0xc；
`8b5c2410`@`0x41028c`（delta=8）→orig+0x8。`ret 0xc` = 三栈参、this 走 ecx ⇒ **orig+4 从未被读**。
输出指针唯一在 orig+0xc（`mov [eax],*` 共 4 处）；非空校验 `0x410265`，失败 `0x80004003`，其后 `0x80004002`。
**裁定：card A（#562）的 orig+8=IID / orig+0xc=ppv 成立，主会话中途结论撤回。**

**QK4. 🔴 转发桩槽位律（新）.** `0x410210` 五条 16 B = `8b442404 8b50fc 8d48fc ff522c c20400`
= `mov eax,[esp+4]` / `mov edx,[eax-4]` / `lea ecx,[eax-4]` / `call [edx+0x2c]` / `ret 4`。
**76 处 / 76 张表，槽序号 100% = 3，所在表 mdisp 100% = 4，K 100% = `0x2c`（= 主视图 slot11）。**
寄存器分工：`edx` 装 vftable（自 `[eax-4]`）、`ecx` 装对象指针 ⇒ `call` 操作数寄存器 == **`mov` 目标**（自错 E4）。
主视图 slot11 落点：`0x4c9150`(33c0c3)×9 + 67 个各 1 次。反控：`-4`→`-8` 命中 **0**；改查 slot10 则 34 张落在 `0x410480`。

**QK5. 🟡 律 U 独立复现 101/101/0.** card A（hy4 #562，45 回合 / 6.27′，无超时）与主会话 `m13` 双家族同值；
反控 N==mdisp−1 成立 0。**本轮不新增律 U/律 V**（R210 §2.218 已立），仅独立复现。

**QK6. 🟡 自错 5 条 / 子代理分歧 3 条，全部有裁定.** 自错：m3/m4 首个 `ret` 截断（`0x41026f` 是 E_POINTER 提前返回）；
m5 律 V **空判据**（0 恒属 mdset ⇒ 184 视图里只有 **84** 可判，已如实降级覆盖率）；m7 `FAM[VT[v]]` 键错（应 `FAM[COL[VT[v]]['pCHD']]`）；
m10 `call`↔`lea` 错绑；m11 符号错。分歧：①card A 的 A3 自报 0 命中，其最终 result 已修正为 76/76/slot3，**与主会话一致**；
②card A 报「COL `+0x14` != 自身」—— 主会话复算 `+0x14==自身` **0 个**、值为 0 者 **1009** 个 ⇒ **card A 正确、卡面背景错**；
③COL 计数 card A 1203 vs card B/主会话 **1214**：差值来自额外 sig/pCD 严格阶段，取 1214 为基准。

**QK7. 🟡 收口.** `_r217/m13_final_ctl.py` **32 断言全 PASS / 0 FAIL**；`gamemd.exe` sha256 `73201cc0...f3fcf67476`。
四件套：本段 **QK** CR 保持 **137**；R14_COMMON **§2.225** CR 保持 **1081**；GOAL **§1275** CR 保持 **337**；
STATUS_BOARD 第 217 轮 CR 保持 **0**。

**QK8. ⚪ 未取得.** ①`0x4a1ca0` 环缓冲容量 4 语义；②三全局 `0x887680/84/88` 运行期初值（virt-only，须 win-main）；
③律 W 违例 360 条逐类内嵌偏移全表；④6 张超 256 表 slot≥256 共 **464** 槽未查；⑤零槽视图在 `.data` 的成因；
⑥F23/F35 grade；⑦C7 三死分支、C11 十二 ID。
"""
new2=b1+('\n'+L).encode('utf-8')
assert new2.count(b'\r')==137
open(LP,'wb').write(new2)
c2=open(LP,'rb').read(); assert c2.startswith(b1) and c2.count(b'\r')==137
print('[LOCK] QK bytes %d -> %d cr=%d sha %s -> %s'%(len(b1),len(c2),c2.count(b'\r'),h1[:16],hashlib.sha256(c2).hexdigest()[:16]))
# ---------- STATUS_BOARD ----------
SP=T+'/STATUS_BOARD.md'
b3,h3=backup('BOARD',SP)
assert b3.count(b'\r')==0 and h3.startswith('3046ea0252df7555')
lines=b3.count(b'\n'); print('[BOARD] 写前行数=%d (上限 300, 归档阈值 260) => %s'%(lines,'需归档' if lines>=260 else '不归档'))
assert lines<260, '需先归档'
B="""## 第 217 轮（2026-11-28）槽数上限截断实证 + 9958 口径锁定 + QI 三读模型 + 转发桩 slot3 律

- **槽数上限 256 被证伪**：6 张表真槽数 309/322/341/341/343/344（Unit/Infantry/Aircraft/Foot/Building/Techno）。全 1218 表无上限 14044 槽、cap256 13580、差 464。反控判据含 .rdata 则 142625（+128581）。
- **零槽 4 张共用 COL 0x800040**（DropPodLocomotionClass, mdisp=4）⇒ 视图级 mdisp≠0=264 vs COL 记录级=260，差 4 由此解释。
- **9958 口径锁定为无上限**：主视图 954 张 slot≥3 无上限 9958（与 R210 差 0）、cap256 9494（差 −464）⇒ R210 正确不需订正，但严禁带 cap。
- **QI 0x410260 三处栈读 orig=0xc/0xc/0x8**，公式 orig=指令内 disp−push delta；ret 0xc 三栈参、orig+4 从未被读；裁定 card A 的 orig+8=IID / orig+0xc=ppv 成立，主会话中途结论撤回。
- **转发桩新律**：0x410210 字节 8b4424048b50fc8d48fcff522cc20400，76 处全部 mdisp=4 视图 slot 3、K 恒 0x2c（=主视图 slot11）；edx 装 vftable、ecx 装对象指针。
- **律 U 独立复现 101/101/0**（card A #562 45 回合 6.27′ 无超时；card B #563 19 回合 2.12′ 无超时），双家族同值；本轮不新增律 U/律 V。
- **自错 5 条 0 进结论**：首个 ret 截断 / 律 V 空判据（184→84 可判已降级）/ 族表键错 / call-lea 错绑 / orig=X+delta 符号错。分歧 3 条均有裁定。
- **收口**：m13 32 断言全 PASS；R14 §2.225 CR 1081、GOAL §1275 CR 337、本段 QK CR 137、看板 CR 0（240→241 行）。
"""
new3=b3+('\n'+B).encode('utf-8')
assert new3.count(b'\r')==0, 'BOARD CR %d'%new3.count(b'\r')
open(SP,'wb').write(new3)
c3=open(SP,'rb').read()
print('[BOARD] 行数 %d -> %d cr=%d sha %s -> %s'%(lines,c3.count(b'\n'),c3.count(b'\r'),h3[:16],hashlib.sha256(c3).hexdigest()[:16]))
assert c3.count(b'\r')==0 and c3.startswith(b3) and c3.count(b'\n')<=300
json.dump(dict(goal_sha=hashlib.sha256(c).hexdigest(),goal_bytes=len(c),goal_cr=c.count(b'\r'),
 lock_sha=hashlib.sha256(c2).hexdigest(),lock_bytes=len(c2),lock_cr=c2.count(b'\r'),
 board_sha=hashlib.sha256(c3).hexdigest(),board_bytes=len(c3),board_lines=c3.count(b'\n')),open(ROOT+'/_r217/p2.json','w'),indent=1)
print('[OK] 四件套 3/3 落盘')
