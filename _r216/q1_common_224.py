# -*- coding: utf-8 -*-
"""R216 q1：追加 R14_COMMON §2.224（CR 必须保持 1081，全 LF）。"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'; F=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
b0=open(F,'rb').read(); h0=hashlib.sha256(b0).hexdigest(); cr0=b0.count(b'\r')
print('R14_COMMON 旧 sha=%s bytes=%d CR=%d LF=%d'%(h0[:16],len(b0),cr0,b0.count(b'\n')))
assert cr0==1081, cr0
assert b'## 2.224 ' not in b0
dst=BASE+'/R14_COMMON.md.before_r216_224_20261128.bak'
assert not os.path.exists(dst); open(dst,'wb').write(b0)
SEC = '''
## 2.224 R216（2026-11-28）· ?AVAbstractClass@@ 四子对象 MI 布局实证（4 张 vftable 字节写入 + QI 四 IID）；律 U 101/101；律 W 违例 360 条全为正偏移

### 一 · AbstractClass 不是单视图，是 4 子对象多重继承

主视图 `0x7e1f50`（mdisp=0，24 槽）的 **slot8 = 0x4105a0** 是析构/标量删除，其前 11 条指令直接给出 4 个 vfptr 的**字节级写入**：

    004105a0  8a442404            mov al, byte ptr [esp + 4]
    004105a4  56                  push esi
    004105a5  8bf1                mov esi, ecx
    004105a7  a801                test al, 1
    004105a9  c706501f7e00        mov dword ptr [esi], 0x7e1f50
    004105af  c74604341f7e00      mov dword ptr [esi + 4], 0x7e1f34
    004105b6  c746082c1f7e00      mov dword ptr [esi + 8], 0x7e1f2c
    004105bd  c7460c241f7e00      mov dword ptr [esi + 0xc], 0x7e1f24
    004105c4  7409                je 0x4105cf
    004105c6  56                  push esi
    004105c7  e871853b00          call 0x7c8b3d
    004105cc  83c404              add esp, 4
    004105cf  8bc6                mov eax, esi
    004105d1  5e                  pop esi
    004105d2  c20400              ret 4

四张视图在视图表里都可独立查到（COLA 记录 mdisp 逐一对上）：`0x7e1f50`(0,24 槽) / `0x7e1f34`(4,6 槽) /
`0x7e1f2c`(8,1 槽) / `0x7e1f24`(12,1 槽)，四条 COLA 的 pTD 同为 `0x8177c8`、pCHD 同为 `0x7fb108`。
⇒ R91 的「vt==[esi] 对象模型」在此类上被**字节实证**为「vt 分区段：[esi+0x0]/[+0x4]/[+0x8]/[+0xc] 各挂一张」。
`0x7e1f50` 作为任何视图的**槽值**出现 **0 次** ⇒ 主视图地址只在构造/析构里被写，不被继承槽复用。

### 二 · 主视图 slot0 = QueryInterface，比对 4 个 16 字节常量

`0x410260` 全长 150 字节（0x410260..0x4102f9，尾部 5 字节 0x90）。结构：`[esp+0xc]` 为空 → 返回 `0x80004003`；
否则 `repe cmpsd`（ecx=4）依次比对 `0x7f7c90` / `0x7f7c80` / `0x7f7c70` / `0x7e9ae0`，命中即把第 3 个参数写进出参；
四轮皆空 → 返回 `0x80004002`。第 4 个常量的特殊处理：

    004102d4  85db                test ebx, ebx
    004102d6  7405                je 0x4102dd
    004102d8  8d4b04              lea ecx, [ebx + 4]
    004102db  eb02                jmp 0x4102df
    004102dd  33c9                xor ecx, ecx
    004102df  8908                mov dword ptr [eax], ecx

即匹配第 4 个接口时交出 **this+4**（4 字节 adjustor 偏移），前三个接口交出 `this`。
四个常量的 16 字节与 GUID 文本（实测）：

    0x7f7c90  0000000000000000c000000000000046  00000000-0000-0000-C000-000000000046  (IUnknown)
    0x7f7c80  0901000000000000c000000000000046  00000109-0000-0000-C000-000000000046  (IPersistStream)
    0x7f7c70  0c01000000000000c000000000000046  0000010C-0000-0000-C000-000000000046  (IPersist)
    0x7e9ae0  82ac0d17e412d2118175006008055bb5  170DAC82-12E4-11D2-8175-006008055BB5  (游戏自有 IID)

`0x7f7c90` 在 .text 被 `push imm32` 引用 **56** 处、`0x7f7c80` **60** 处；`0x7f7c70` 与 `0x7e9ae0` 各 **0** 处
（只在本函数里被 `repe cmpsd` 以 `mov edi,imm32` 形式装入）。这解释了「为什么 0x7f7c70/0x7e9ae0 扫不到引用」。

### 三 · 24 槽逐槽函数体（全部解出，无一条未解）

| slot | 地址 | 字节 | 语义（实测体） |
|---|---|---|---|
| 0 | 0x410260 | 150 B | QueryInterface：4 IID 比对，失败 0x80004002/0x80004003 |
| 1 | 0x410300 | 8 B | `b801000000c20400` mov eax,1 / ret 4（AddRef 桩） |
| 2 | 0x410310 | 8 B | 同 slot1 逐字节相同（Release 桩） |
| 3 | 0x4c9150 | 3 B | `33c0c3` xor eax,eax / ret（空返回） |
| 4 | 0x410450 | 17 B | mov dl,[ecx+0x20] / test / sete al / ret 4 ⇒ **+0x20 = byte 标志** |
| 5,6 | 0x4c9150 | 3 B | 同 slot3（同址复用） |
| 7 | 0x4103e0 | 45 B | 参数空→0x80004003；否则 `call [eax+0x30]` 后 `add eax,4` 写 [esi]、[esi+4]=0 |
| 8 | 0x4105a0 | 53 B | 析构/标量删除：写 4 张 vfptr；al&1 时 call 0x7c8b3d |
| 9 | 0x410470 | 1 B | `c3` ret |
| 10 | 0x410480 | 3 B | `c20800` ret 8 |
| 11,12 | 0x4c9150 | 3 B | 同 slot3 |
| 13 | 0x410410 | 35 B | `mov eax,[esi+0x10]` → call 0x4a1d50；`mov cl,[esi+0x20]` → call 0x4a1ca0 ⇒ 序列化两个字段 |
| 14 | 0x410490 | 4 B | `83c8ffc3` or eax,-1 / ret |
| 15,16 | 0x4104a0 / 0x4104b0 | 3 B | xor eax,eax / ret |
| 17 | 0x410440 | 3 B | `b001c3` mov al,1 / ret |
| 18 | 0x4104c0 | 35 B | R215 已解：从 3 个 BSS 全局各取 1 dword 写 [eax+0]/[+4]/[+8] |
| 19 | 0x4104f0 | 45 B | `call [eax+0x48]` 取 3 dword 描述符再拷给出参，ret 8 |
| 20,21 | 0x410520 / 0x410530 | 3 B | `32c0c3` xor al,al / ret |
| 22 | 0x410540 | 45 B | 同 slot19 体（仅 ret imm 8→4 不同） |
| 23 | 0x410570 | 1 B | `c3` ret |

字节组去重后 **15** 种；完全同址的槽组：{1,2} 各自独立但字节相同、{3,5,6,11,12,15,16} 共用 `0x4c9150`
（7 处）、{9,23} 两条 `c3` 但地址不同、{20,21} 两条 `32c0c3` 地址不同。

### 四 · 律 U（this-adjustor thunk）：101/101 无反例

mdisp≠0 的视图共 **260** 张。其中 slot0 形如 `sub/add dword ptr [esp+4], N` 后接 `jmp` 到另一视图 slot0 的 **101** 张，
**101/101** 满足 `N == self.mdisp − target.mdisp`，反例 **0**。其余 159 张 slot0 首指令为 `ret`(78) / `xor`(75) / `mov`(3) / `sub`(3)。
组合分布：(4,0,4)×91 / (24,0,24)×6 / (1728,0,1728)×1 / (44,0,44)×1 / (40,0,40)×1 / (36,0,36)×1。
AbstractClass 三条次级视图 slot0 即 `0x4105e0`（sub 4 / jmp 0x410260）、`0x4105f0`（sub 4 / jmp 0x410300）、
`0x410600`（sub 4 / jmp 0x410310），字节均为 `836c240404e9xxxxxxxx`。

### 五 · 律 T → 律 W：C7 写 vfptr 的偏移判据升级与 360 条违例

**律 T（旧口径 disp == mdisp）**：全 .text `mov dword ptr [reg+disp], <视图基址>` 命中 **4202** 条，符 **3876**（92.24%），
违例 **326**（7.76%），分族：B 内嵌成员 201 / C 近邻偏移 79 / A off=0 写次级视图 46。

**律 W（新口径 disp + delta == mdisp，delta = 寄存器基址相对 this 的增量）**：一次性线性扫描 **1,394,300** 条指令
（`disasm_lite` + `skipdata`，64 KB 分块流式，峰值内存受控）后重算，C7 命中 **4195** 条，可反解 delta **2911** 条，
其中符 **2551**、违例 **360**。关键：**360 条违例的 (disp+delta) − mdisp 全部 > 0，0 条 ≤ 0**。

⇒ 可用的新判据是**不等式**：`写入偏移 ≥ 该视图 mdisp`，负偏移 0 条。差值按 (类, 差值) 强聚合，例如
`?AVGenericNode@@` +16×11 / +4×7 / +28×4、`?AV?$rc_ptr@VWDTState@@@@` +8×11、`?AVTactical@@` +3496×4、
`?AV?$DynamicVectorClass@UDrawRecord@FoggedObjectClass@@@@` +92×6 ⇒ 这些是**宿主对象的成员内嵌偏移**，不是 thunk 违例。

### 六 · 口径订正与自错（0 条进结论）

1. **m9 自错**：用 `p.lstrip('-').isdigit()` 解析 capstone 的十六进制 disp（`0xc`/`0x88`）返回 False，
   导致 `0x4105bd`（`[esi+0xc]`）被丢弃、正控只命中 3/4 假 FAIL。改 `int(p,0)` 后 4/4 通过。
2. **m8 try-align 法判为不可信并弃用**：用「命中点前 24 B 内试起点、能顺序解码到命中点即接受」反解前驱，
   正控能过，但**反控失败** —— 把命中点整体前移 50 B 再对齐，300 条里仍有 **227** 条能"对齐"。该法不能区分真前驱。
   改用一次性线性扫描建全局指令表后，前驱是唯一的。
3. **主会话读错非子代理错**：EX1 报 `call 0x4a1ca0` 站点 **331**，主会话 E8 字节口径复算 **331** 一致；
   先前摘要误记为「1」，属主会话读错，已在记录中订正。
4. **m7 前驱分析口径作废**：m7 用「从命中点 −40 B 起盲目解码」取前驱，对齐不可靠；其「A 族 lea 命中 12/46」
   数字不进结论，仅保留律 U 的 101/101（该部分不依赖前驱对齐）。

### 七 · 跨家族（§2.12 规则 D）

#559（hy4 exec，卡 r216_ex1_fieldoffs）产出 `_r216/ex1_field.py` / `ex1.json` / `ex1_out.txt`：
`0x4a1d50` 体 23 B（`mov eax,[esp+4]` / `lea edx,[esp+4]` / `push 4` / `push edx` / `mov [esp+0xc],eax` /
`call 0x4a1de0` / `ret 4`），`0x4a1ca0` 体 134 B（环缓冲插入，`cmp eax,4` 容量 4），E8 站点 **460** / **331**，
5 条正反控全 PASS。主会话独立复算（不复用其代码）：`_r216/m11_recheck_ex1.py`，站点数 460/331 与
`ret 4` 末指令、`call 0x4a1de0` 存在性、`[reg+0x20]` byte 读 16 写 34、`[reg+0x10]` dword 读 2439 写 3263 全部一致。
#560（deepseek audit）见 `_r216/audit_ds*.py` 产物与本轮 LEAD_LOCK 记录。
'''
s1=(b0.decode('utf-8')+SEC).encode('utf-8')
assert s1.count(b'\r')==1081, s1.count(b'\r')
open(F,'wb').write(s1)
r=open(F,'rb').read()
assert r.count(b'\r')==1081 and b'## 2.224 ' in r
print('新 sha=%s bytes=%d CR=%d LF=%d'%(hashlib.sha256(r).hexdigest()[:16],len(r),r.count(b'\r'),r.count(b'\n')))
json.dump({'old':h0,'new':hashlib.sha256(r).hexdigest(),'old_bytes':len(b0),'new_bytes':len(r),
 'cr':r.count(b'\r'),'lf':r.count(b'\n')},open(ROOT+'/_r216/q1.json','w'),indent=1)
