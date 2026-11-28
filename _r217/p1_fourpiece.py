# -*- coding: utf-8 -*-
"""R217 p1：四件套追加（写入纪律：wx 独占备份 -> 断言旧 sha/CR/命中次数 == 1 -> 一次性写 -> 回读校验）。
段落：R14_COMMON §2.225 / GOAL §1275 / LEAD_LOCK 下一字母段 QJ+1 -> QK / STATUS_BOARD 第 217 轮。
CR 契约：R14_COMMON 1081 / GOAL 337 / LEAD_LOCK 137 / STATUS_BOARD 0（新增段内一律不得引入 \r）。
"""
import os,hashlib,json,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/R17_LEAD_BASELINE'
os.makedirs(BASE,exist_ok=True)
SPEC={
 'R14_COMMON':dict(path=T+'/R14_COMMON.md',cr=1081,sha='caa0ea247a14c019'),
 'GOAL':dict(path=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md',cr=337,sha='5ca5e1899bbbddaf'),
 'LOCK':dict(path=ROOT+'/lead/LEAD_LOCK',cr=137,sha='49f92644189e68d2'),
 'BOARD':dict(path=T+'/STATUS_BOARD.md',cr=0,sha='3046ea0252df7555'),
 'ARCH':dict(path=T+'/BOARD_ARCHIVE.md',cr=2952,sha='be6becf01651bfa5'),
}
STAMP='20261128_1830'
def backup(tag,path):
    b=open(path,'rb').read()
    h=hashlib.sha256(b).hexdigest()
    dst='%s/%s.before_r217_%s_%s.bak'%(BASE,os.path.basename(path),tag,STAMP)
    if os.path.exists(dst):                      # 幂等：同内容才复用，否则换戳重开
        old=open(dst,'rb').read()
        assert old==b, 'BACKUP DIFFERS '+dst     # 前置断言已验 sha，此处再兜一层
        return b,h
    fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)   # wx 独占
    with os.fdopen(fd,'wb') as f: f.write(b)
    return b,h
def verify(name,expect_cr):
    p=SPEC[name]['path']; b=open(p,'rb').read()
    yield dict(name=name,cr=b.count(b'\r'),lf=b.count(b'\n'),bytes=len(b),sha=hashlib.sha256(b).hexdigest()[:16])
# --- 0) 前置断言 ---
pre={}
for k,v in SPEC.items():
    b=open(v['path'],'rb').read()
    h=hashlib.sha256(b).hexdigest()
    assert b.count(b'\r')==v['cr'], '%s CR %d != %d'%(k,b.count(b'\r'),v['cr'])
    assert h.startswith(v['sha']), '%s sha %s != %s'%(k,h[:16],v['sha'])
    pre[k]=dict(cr=v['cr'],bytes=len(b),sha=h)
    print('[前置OK] %-10s cr=%-5d bytes=%-8d sha=%s'%(k,v['cr'],len(b),h[:16]))
# --- 1) R14_COMMON §2.225 ---
R14="""## 2.225 R217（2026-11-28）· 槽数上限截断实证 + 9958 口径锁定 + QI 三读模型 + 转发桩槽位律；律 U 独立复现 101/101

### 一 · 🔴 槽数上限 256 截断：6 张表真实槽数 309..344（非 256）
槽数判据 = 从 V 起每 4 字节取 DWORD，直到该值不落在 `.text`；上限取消后实测：

| 表 | 类名 | 真槽数 |
|---|---|---|
| `0x7f5c70` | `?AVUnitClass@@` | **344** |
| `0x7eb058` | `?AVInfantryClass@@` | **343** |
| `0x7e22a4` | `?AVAircraftClass@@` | **341** |
| `0x7e8c94` | `?AVFootClass@@` | **341** |
| `0x7e3ebc` | `?AVBuildingClass@@` | **322** |
| `0x7f4960` | `?AVTechnoClass@@` | **309** |

全 1218 张表：**无上限总槽数 14044**；**cap=256 后 13580**；**差额 464**。
零槽表 4 张 `0x877000`/`0x877010`/`0x87b17c`/`0x87b18c`，全部与 `0x7e8278` 共用同一 COL `0x800040`（`?AVDropPodLocomotionClass@@`, mdisp=4）。
**视图级 mdisp≠0 = 264，COL 记录级 = 260，差额 4 = 上述 4 张零槽视图**（同一 COL 被 5 张视图共用，本二进制仅此 1 例）。
正控：`0x7e1f50`=24、`0x7e1f34`=6、`0x7e1f2c`=1、`0x7e1f24`=1，与 R216 逐数一致。
反控：把判据放宽为 `.text` ∪ `.rdata`，总槽数暴涨至 **142625**（+128581）⇒ `.text` 判据是必要的，不是可选。

### 二 · 🔴 9958 口径锁定：R210 的 9958 是**无上限**口径，cap256 会得 9494
主视图定义 = 每个 pCHD 视图族中 mdisp==0 的那张 ⇒ **族数 954 / 主视图 954 张**（复现 R210）。
- 主视图 slot≥3：**无上限 = 9958**（与 R210 记载 9958 逐数一致，差 **0**）
- 主视图 slot≥3：**cap256 = 9494**（差 **−464**，正好等于 6 张溢出表的溢出量）

⇒ **R210「主视图 954 表 slot≥3 = 9958」是无截断口径，结论正确、无需订正**；但凡后续脚本若带 cap 256 会稳定少 464，本段把它钉死为口径判据。
全 1218 表口径：slot≥3 无上限 **10814** / cap256 **10350**。
反控：若把主视图口径放松成「族内任意一张」，分母变 1218（≠954）⇒ 主视图口径必须限定 mdisp==0。

### 三 · 🔴 QI 0x410260 实参模型：三处栈读 orig = 0xc / 0xc / 0x8（无 orig+4 读）
按 push/pop 累计 delta，**原栈偏移 = 指令内 disp − delta**（R217 自错 E5：曾误用 `+delta`）：

| 指令 | 字节 | 指令内 disp | 累计 push delta | 原 esp 偏移 |
|---|---|---|---|---|
| `0x410260` | `8b44240c` | `0xc` | 0 | **`esp+0xc`** |
| `0x410272` | `8b54240c` | `0xc` | 0 | **`esp+0xc`** |
| `0x41028c` | `8b5c2410` | `0x10` | 8 | **`esp+0x8`** |

`ret 0xc` 清 3 个栈参（thiscall ⇒ this 走 ecx，栈参 = orig+4/+8/+0xc）。**orig+4 全程未被读**；
唯一被写穿的输出指针在 orig+0xc（`mov [eax],ebx` 三条 + `mov [eax],ecx` 一条），非空校验在 `0x410265`（失败 `0x80004002` 之上一路 `0x80004003`）。
⇒ 与子代理 card A（#562）结论 **orig+8 = IID、orig+0xc = ppv 一致**；主会话中途用 `+delta` 得出的「IID=0xc」是自错，**已撤回**。

### 四 · 🔴 转发桩（主对象转发）槽位律：76 处全部落在 mdisp=4 视图的 **slot 3**，K 恒 `0x2c`
五条指令字节（`0x410210`，16 B）= `8b442404` `8b50fc` `8d48fc` `ff522c` `c20400`：
`mov eax,[esp+4]` / `mov edx,[eax-4]` / `lea ecx,[eax-4]` / `call [edx+0x2c]` / `ret 4`。
**寄存器分工**：`edx` 装完整对象 vftable、`ecx` 装对象指针（∴ `call` 的操作数寄存器 == `mov` 的目标寄存器，不是 `lea` 的目标 —— R217 自错 E4）。
命中 **76 处 / 76 张表**，槽序号 **100% 为 3**，所在表 mdisp **100% 为 4**，K **100% 为 `0x2c`**（= 主视图 slot 11）。
主视图 slot11 落点分布：`0x4c9150`(33c0c3)×9 + 67 个各 1 次的不同函数。
反控：把 `-4` 改 `-8` ⇒ 命中 **0**；改用 slot10 落点则 34 张落在 `0x410480` ⇒ slot 号与 K 的对应不是巧合。

### 五 · 律 U 独立复现（跨家族 §2.12 规则 D）
子代理 card A（hy4 exec #562）独立实现，**律 U 成立 101 / 违例 0**；反控 N==mdisp−1 成立 **0**。
主会话 `_r217/m13_final_ctl.py` 自算同值 **101/101/0**，两家族一致。
本轮 **不新增**律 U/律 V（R210 §2.218 已立），仅作独立复现与口径确认。

### 六 · 🟡 自错登记 5 条（0 条进结论）
E1 `m3`/`m4` 在首个 `ret` 截断（`0x41026f` 是 E_POINTER 提前返回）⇒ 律 V 抽出 0 命中；改按 `0x90`/`0xcc` 填充切函数后恢复。
E2 `m5` 律 V 对 180/184 视图只拿到 `{0}`，而 0 恒属于 mdset ⇒ **空判据**（假通过）；`m6` 加 ppv 寄存器解析后仅 **84/184** 视图可判，据此把覆盖率如实降级。
E3 `m7` 把 COL 地址当 pCHD 查族表 ⇒ 空结果；正确为 `FAM[COL[VT[v]]['pCHD']]`。
E4 `m10` 要求 `call` 寄存器 == `lea` 目标 ⇒ 0 命中；实为 == `mov` 目标。
E5 `m11` 用 `orig = X + delta` ⇒ 误判 card A；正确为 `X − delta`，card A 正确。

### 七 · 🟡 与子代理的分歧裁定
- **card A（#562）A3 自报「命中 0」**：其卡面要求命中函数数/表数，它先报 0，但其最终 result 已修正为「命中 1 个函数 `0x00410210`、涉及 76 张表、K=0x2C、全在槽 3」——与主会话 m7/m10 一致。**分歧已闭合，采信 76/76/slot3**。
- **card A 报「COL 的 +0x14 self 字段指向自身」不成立**：主会话复算 **`+0x14 == 自身` 命中 0 个**、取值 `0` 者 **1009** 个 ⇒ **card A 正确，卡面背景描述错误，本轮已在卡面口径中改正**（以 sig=0 ∧ pCD=0 ∧ pTD 指向 `.?AV`/`.?AU` TD ∧ pCHD 落在 `.rdata` 为筛据）。
- **COL 计数 1203(cardA) vs 1214(cardB/主会话)**：差额为 `pCHD` 段校验是否强制；主会话加段校验后仍 **1214**（card A 的 1203 来自额外的 sig/pCD 严格阶段）。二者不矛盾，取 **1214** 为计数基准。

### 八 · 🟡 落盘与门禁
见本轮 p2/p3 段；`_r217/m13_final_ctl.py` **32 断言全 PASS、0 FAIL**；二进制基准 `gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`。
"""
p=SPEC['R14_COMMON']['path']; b0,h0=backup('R14COMMON',p)
assert b0.endswith(b'\n')
assert b0.count(b'\r')==1081
new=b0+('\n'+R14).encode('utf-8')          # 全 LF：CR 契约 1081 不变
assert new.count(b'\r')==SPEC['R14_COMMON']['cr'], 'R14 CR %d'%new.count(b'\r')
open(p,'wb').write(new)
chk=open(p,'rb').read()
print('[写入] R14_COMMON bytes %d -> %d  cr %d -> %d  sha %s -> %s'%(len(b0),len(chk),b0.count(b'\r'),chk.count(b'\r'),h0[:16],hashlib.sha256(chk).hexdigest()[:16]))
assert chk.count(b'\r')==SPEC['R14_COMMON']['cr'] and chk.startswith(b0)
json.dump(dict(pre={k:v for k,v in pre.items()},r14_new_sha=hashlib.sha256(chk).hexdigest(),r14_new_bytes=len(chk)),open(ROOT+'/_r217/p1a.json','w'),indent=1)
print('[OK] §2.225 已落盘')
