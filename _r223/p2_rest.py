# -*- coding: utf-8 -*-
"""R223 续写：GOAL §1281 / LEAD_LOCK QZ / STATUS_BOARD 第 223 轮。"""
import os, hashlib, re
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/R17_LEAD_BASELINE'; TIER=ROOT+'/lead/next_re_20261117_r14'
GOAL=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'; LOCK=ROOT+'/lead/LEAD_LOCK'
BOARD=TIER+'/STATUS_BOARD.md'
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r223_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b,dst
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b,dst
    raise SystemExit('bak exhausted')
GOAL_APP = """
## §1281 · R223（2026-11-28）· 0x7c6620 网格冲突检查器全解（3x3 邻域 + 阈值 0xc + 双向修补 + 自递归）；0x7c7371 状态块 12 B 四偏移；四张 4 项对齐表与 8 项 nibble 表成对同构；音频簇活跃/死区分界

- **目标一（gamemd.exe 静态本体，R222 待办①②③ 全关）**：
  1. `0x7c6620` 定性为**网格记录 3x3 邻域冲突检查器**，非 ACM 帧更新器。记录寻址 `rec = dword[0xb0b6ec] + (arg1 + arg2*dword[0x8759a4])*8`（步长取内存全局），8 B 记录只碰 `[rec+0]`(dword 值) 与 `[rec+4]`(dword 标志 bit0/bit1)，与分配器清零 6 B 自洽；9 组邻域由 `edi/ecx` 初值 `-1` + `cmp 2/jl` 给出，(0,0) 由 `or eax,ecx`/`test` 跳过；阈值 `0xc`（`cdq+xor+sub` 取绝对值 2 处）；bit0 置位且 arg3≠0 ⇒ 直接返 0 不修，bit0 清零 ⇒ 按 arg2==1 选方向把邻居改成 `本值∓0xc` 并 `or [rec+4],2`，随后**自递归**处理被拖动的邻居（`0x7c66ee`，4 实参 stdcall）；3 个 ret、返回值只有 0/1。
  2. `0x7c6620` **无任何外部引用**（`.text` rel32 唯一 1 条自递归；dword 字面量 / push imm32 / 0f8x / eb·7x rel8 / ff15·ff25 全 0；`.rdata`/`.data`/`.detour` rel32 各 0；RVA 与段相对形式各 0）⇒ 死代码。与 `0x7c62ac`、`0x7c6270`、`0x7c6730`、`0x7c6752` 整族同属死区；文件里活跃的音频路径只有块2 族 + 状态清零器 `0x7c7350`。
  3. `0x7c7371` 的状态块 `&[ebx+0x7d0]` 只有 **4 个偏移共 12 B**：`+0`(dword 值)、`+4`(word step)、`+6`(dword 值 ch2)、`+0xa`(word step ch2)，映射回对象 `obj+0x7d0/0x7d4/0x7d6/0x7da`，与清零器 `0x7c7350` 写的四槽一一对应；`0x7c7350` 唯一调用点 `0x7c2a74`，`0x7c7371` 恰 2 个调用点 `0x7c24a2`/`0x7c2557`。
  4. 四张 4 项对齐表同构：每族 `4t − 8t` 恒 `0x20`；跨表同索引 4/4 全等（k=0 13 B、k=1/2/3 各 15 B），把 imm8 也屏蔽后全库仅剩 2 个图案（4 + 12 成员）；唯一结构差异是 stub0 后的对齐填充 `90`/`8bff`/`8d4900`/`8d4900`；4 项表三个非零项跳进本族 8 项表的 idx 6/4/2（12/12），stub3 结束 +1 恰为本族解码器入口（4/4）。
  5. `.data` 的 320 dword 单调串 `[0x874700,0x874c00)`（步长 0x204..0x20a、全落 .text）**不是指针表**：无任何 disp32 引用（逐值 0 命中）、非 4 对齐（91/320）、前驱非 int3/ret（0/320）⇒ 数据巧合，不能当作函数指针证据。
  6. 网格描述符四全局 `0x8759a0/a4/a8/ac`（行数/列数/两项来自 `d[0x87f90c]`/`d[0x87f910]`）与网格基址 `0xb0b6ec`（BSS）；分配 = `(d[0x87f918]+1)*(d[0x87f914]+1)*8`；**活跃块2 族对它们引用数全 0**，`0x7c6620` 是唯一同时读 base 与 stride 的消费者。
- **判据**：`_r223/` 共 13 个脚本 / **124 断言 / 0 FAIL**（m7 32、m9 16、m19 13、m13 12、m20 10、m17 8、m12 7、m10 6、m11 6、m14 4、m2 3、m16 2、m18 2）；反控 eax 基址对照、imm8 屏蔽后图案数 4→2、320 串三否证。
- **跨家族**：exec `#584`（hy4，39 回合 / 20.37′，`[OVERTIME: 20.37' vs 2.0']`）26 断言 26/0 全 PASS，其「状态块 0x7fc 属另一对象」的判断由主会话复算采纳；审计 `#585`（hy4 audit，18 回合 / 18.43′，`[OVERTIME]`）A1–A8、B1/B2/B3/B5、C1–C3 全 PASS，B4 口径订正（表址 disp32 起点 = 指令起始 +3，ModRM 0x9d）已采纳；跨家族审计 `#587`（deepseek audit，24 回合 / 8.05′）独立复现同构结论并**订正主会话措辞**（不是「16 个 stub 全部相同」，而是「跨表同索引相同，4 组×4 个」）——该订正由主会话用 m20 复算成立并采纳；`#586`（deepseek 首发）被取消（`cancelled`，0 回合）如实记录。
- **自错**：E1 `p1_four.py` 的 W2 断言「R14 原文无 CRLF」与 CR=1081 口径矛盾（同 R222 E2，不影响写入）；E2 首版 `m9_tables_final.py` 把 stub0 末尾的间接 jmp 误计入 stub 体，导致 padding 判据错位（已改为「stub0 体后紧跟 `ff 24 9d` 指令，其后再量 pad」）。
- **未取得**：记录值量纲与 arg3/arg4 语义、`[rec+4]` bit2..31 的其他使用方、`d[0x87f90c]`/`d[0x87f910]` 语义；F23/F35 grade；C7 三死分支、C11 十二 ID。
"""
GOAL_APP=GOAL_APP.replace('\r\n','\n')
b,dst=bak(GOAL,'GOAL')
ck('G1 GOAL 备份已独占创建',os.path.exists(dst),dst)
s=b.decode('utf-8')
ck('G2 GOAL 追加段无 CR','\r' not in GOAL_APP)
new=s+GOAL_APP; nb=new.encode('utf-8')
ck('G3 GOAL 新 CR == 337',nb.count(b'\r')==337,nb.count(b'\r'))
ck('G4 GOAL 新末节 = §1281',[l for l in new.split('\n') if l.startswith('## §')][-1].startswith('## §1281'))
ck('G5 GOAL 字节净增 == 追加段长度',len(nb)-len(b)==len(GOAL_APP.encode()),(len(b),len(nb)))
open(GOAL,'wb').write(nb)
ck('G6 GOAL 回读一致',open(GOAL,'rb').read()==nb)
print('[GOAL] %d -> %d B CR=%d'%(len(b),len(nb),nb.count(b'\r')))

LOCK_APP = """
**QZ1. 🟢 0x7c6620 定性：网格记录 3x3 邻域冲突检查器（R222 待办① 关闭）.** 函数体 `[0x7c6620,0x7c672a)` 0x10a B。
`rec = dword[0xb0b6ec] + (arg1 + arg2*dword[0x8759a4])*8`（`0x7c662a/0x7c6633/0x7c663a/0x7c663d`）。
8 B 记录只碰 `[rec+0]`（值）与 `[rec+4]`（标志，`test 1`@`0x7c667d`、`or 2`@`0x7c66c7`/`0x7c66dc`），无 `[rec+5..7]`。
`edi/ecx` 初 `-1`、`cmp 2`+`jl` ⇒ 9 组；(0,0) 由 `0x7c6651 or eax,ecx`/`test`/`je` 跳过。阈值 `0xc`（`cdq+xor+sub` 取绝对值 2 处）。
bit0 置位且 `arg3!=0` ⇒ 直接返 0；bit0 清零 ⇒ 按 `arg2==1` 把邻居改成 `本值∓0xc` 并 `or [rec+4],2`，再**自递归**（`0x7c66ee`，4 实参 + `lea esp,[esp+0x10]`）。
3 个 ret、返回 0/1。判据 `_r223/m7_final.py` **32/0**。

**QZ2. 🔴 0x7c6620 死代码（三线一致）.** `.text` rel32 指向它**仅 1 条自递归**；dword 字面量 0、`push imm32` 0；
审计补测 0f8x / eb·7x rel8 / `ff15`·`ff25` 各 0，`.rdata`/`.data`/`.detour` rel32 各 0，RVA `0x3c6620` 与段相对 `0x3c5620` 各 0；relocs stripped 无导出。
⇒ 与 `0x7c62ac`/`0x7c6270`/`0x7c6730`/`0x7c6752` 整族同属死区；活跃音频路径 = 块2 族 + `0x7c7350`。

**QZ3. 🟢 状态块 12 B 四偏移（R222 待办② 关闭）.** `obj+0x7d0`(dword 值)/`obj+0x7d4`(word step)/`obj+0x7d6`(dword ch2 值)/`obj+0x7da`(word ch2 step)。
内部位点：`+0` 4 处（`0x7c73c7`/`0x7c778c` 读、`0x7c798b`/`0x7c75c3` 写）、`+4` 4 处、`+6` 2 处（`0x7c7b61`/`0x7c7d5b`）、`+0xa` 2 处（`0x7c7b64`/`0x7c7d5e`）。
清零器 `0x7c7350` 写 `[eax]`/`[eax+4]`/`[eax+6]`/`[eax+0xa]` 与之一一对应；其唯一调用点 `0x7c2a74`。`0x7c7371` 恰 2 个调用点 `0x7c24a2`/`0x7c2557`。
窗口内另有 `[ebx+0x7fc]` 两条（`0x73c51c`/`0x73c5b2`）**属另一对象**，不并入本块（执行员 #584 判断，主会话复算采纳）。

**QZ4. 🟢 四张 4 项对齐表同构 + 与 8 项 nibble 表成对（R222 待办③ 关闭）.** 每族 `4t − 8t` 恒 `0x20`：
块1 `0x7c6b58/0x7c6b38`、块2A `0x7c7778/0x7c7758`、块2B `0x7c7b3c/0x7c7b1c`、块2C `0x7c7f10/0x7c7ef0`；
8 项表与 4 项表相对块1 的位移相同（`0xc20/0xfe4/0x13b8`）。屏蔽 imm32+disp32 后**跨表同索引 4/4 全等**
（k=0 13 B `55c1ed0433db0bede9…`；k=1/2/3 15 B `83ed0c/08/04 55c1ed04 33db 45 e9…`）；再屏蔽 imm8 后全库仅 2 图案（4+12 成员）。
唯一结构差异 = stub0 后的对齐填充 `90`(1 B)/`8bff`(2 B)/`8d4900`(3 B)/`8d4900`(3 B)。
4 项表各有 1 条 `jmp dword [ebx*4+表址]`（指令起始 `0x7c67d0`/`0x7c73ef`/`0x7c77b6`/`0x7c7b86`，disp32 起点 = 起始 +3，审计 #585 B4 口径）；
三个非零项跳进本族 8 项表 idx **6/4/2**（12/12，`8-2k` 律），stub3 结束 +1 恰为本族解码器入口（4/4）⇒ 4 项表 = 声道/位宽对齐跳板，8 项表 = nibble 分派。
判据 `_r223/m9_tables_final.py` 16/0、`m5_mapping.py` 5/0。

**QZ5. 🟡 `.data` 320 dword 单调串不是指针表（反控）.** `[0x874700,0x874c00)` 320 个值全落 `.text`、单调、步长 `0x204..0x20a`、首 `0x7b15ec` 末 `0x7d9d27`；
但逐值搜 disp32 命中 **0**、`%4==0` 仅 **91/320**、前驱 int3/ret **0/320** ⇒ 数据巧合。审计中出现的 `0x7c6789/0x7c6990/0x7c637a/0x7c6581`
「指向音频簇的 dword」全落在这一串里，只有 1 个是真实指令起点，**不可当函数指针**（`_r223/m14_tbl874.py` 4/0、`m15_coincide.py`、`m17_proof.py` 8/0）。

**QZ6. 🟡 网格描述符与消费者隔离.** `0x8759a0 ← d[0x87f918]+1`（行，`0x6b2784`）、`0x8759a4 ← d[0x87f914]+1`（列/步长，`0x6b27ec`/`0x6b2b3b`）、
`0x8759a8 ← d[0x87f90c]`（`0x6b27fe`）、`0x8759ac ← d[0x87f910]`（`0x6b2790`）；分配 `(rows)*(cols)*8`（`0x6b2731/0x6b2734/0x6b2737`），清零 `esi−1` 次（`0x6b274b`），基址 `0xb0b6ec`（BSS）。
引用：`0x8759a0` 4 / `0x8759a4` 18（16 读 2 写）/ `0x8759a8` 10 / `0x8759ac` 10 / `0xb0b6ec` 32。
**活跃块2 族对它们与 base 引用均 0** ⇒ 网格记录与 ADPCM 解码两条独立数据流；`0x7c6620` 是唯一同时读 base 与 stride 的消费者（`_r223/m19_facts.py` 13/0）。

**QZ7. 🟡 跨家族与自错.** exec `#584`（hy4，**39 回合 / 20.37′**，`[OVERTIME: 20.37' vs 2.0']`）26/26 PASS；
审计 `#585`（hy4 audit，**18 回合 / 18.43′**，`[OVERTIME]`）A 组 8/8、B 组 4/5（B4 口径订正：表址 disp32 起点 = 指令起始 +3，ModRM `9d`）、C 组 3/3；
跨家族审计 `#587`（deepseek audit，**24 回合 / 8.05′**）三争议点全部复现，**订正主会话措辞**：不是「16 个 stub 全部字节相同」，而是「跨表同索引相同（4 组×4）」；
其独立发现「表址位移与 handler 位移不等差（+0xc1f vs +0xc20）」由主会话用 m20 复算成立。`#586`（deepseek 首发）状态 `cancelled`（0 回合 / 15.9′），如实记录不计入结论。
自错 2 条 **0 条进结论**：E1 `p1_four.py` W2「原文无 CRLF」与 CR=1081 口径矛盾（同 R222 E2）；E2 `m9_tables_final.py` 首版把 stub0 后间接 jmp 计入 stub 体致 pad 判据错位。

**QZ8. ⚪ 收口.** R14_COMMON **§2.231** CR 保持 **1081**（1965287→1974405 B）；GOAL **§1281** CR 保持 **337**；本段 **QZ** CR 保持 **137**；
STATUS_BOARD 第 223 轮 CR 保持 **0**（开局 272 行 ≥ 260，**已归档最早 2 段**（206/207 轮）到 BOARD_ARCHIVE：1535894→1551003 B、ARCH CR 保持 2952；BOARD 272→225 行）。
`gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`。

**QZ9. ⚪ 未取得.** ①记录值量纲与 `arg3`/`arg4` 真实语义（静态只证到标志位与开关）；②`[rec+4]` bit2..bit31 的其它使用方；③`d[0x87f90c]`/`d[0x87f910]` 语义；
④F23/F35 grade 裁定；⑤C7 三死分支自然真实行、C11 十二 ID 真判据接入方案。
"""
LOCK_APP=LOCK_APP.replace('\r\n','\n')
b,dst=bak(LOCK,'LOCK')
ck('L1 LEAD_LOCK 备份已独占创建',os.path.exists(dst),dst)
s=b.decode('utf-8')
ck('L2 LOCK 追加段无 CR','\r' not in LOCK_APP)
new=s+LOCK_APP; nb=new.encode('utf-8')
ck('L3 LOCK 新 CR == 137',nb.count(b'\r')==137,nb.count(b'\r'))
codes=re.findall(r'^\*\*([A-Z]{2})\d*\.',new,re.M)
ck('L4 LOCK 新段 = QZ 且未被占用',codes[-1]=='QZ' and codes.count('QZ')>=9,codes[-3:])
open(LOCK,'wb').write(nb)
ck('L5 LOCK 回读一致',open(LOCK,'rb').read()==nb)
print('[LOCK] %d -> %d B CR=%d'%(len(b),len(nb),nb.count(b'\r')))

BOARD_APP = """
## 🟢 R17 第 223 轮（2026-11-28）· 0x7c6620 定性为网格 3x3 邻域冲突检查器（死代码）+ 状态块 12 B 四偏移 + 四张 4 项对齐表与 8 项 nibble 表成对同构 + 音频簇活跃/死区分界

- **0x7c6620 = 网格记录 3x3 邻域冲突检查器（R222 待办① 关闭）**：`rec = dword[0xb0b6ec] + (arg1 + arg2*dword[0x8759a4])*8`（步长取内存全局，`0x7c6633 imul eax,[0x8759a4]`）；8 B 记录只碰 `[rec+0]`(dword 值) 与 `[rec+4]`(dword 标志)，与分配器清零 6 B（`[rec+0]` dword + `[rec+4]`/`[rec+5]` byte）自洽。9 组邻域由 `edi/ecx` 初值 `-1` + `cmp reg,2`/`jl` 给出，(0,0) 由 `0x7c6651 or eax,ecx` + `test` 跳过；阈值 `0xc`（`cdq`+`xor`+`sub` 取绝对值 2 处）。bit0 置位且 `arg3!=0` ⇒ 直接返 0（`0x7c6686/0x7c668a`）；bit0 清零 ⇒ 按 `arg2==1` 把邻居改成 `本值∓0xc`（`0x7c66bf..0x7c66c5` / `0x7c66d4..0x7c66da`）并 `or [rec+4],2`，再**自递归**（`0x7c66ee`，4 实参 + `lea esp,[esp+0x10]`）。3 个 ret、返回 0/1。
- **0x7c6620 无任何外部引用 ⇒ 死代码**：`.text` rel32 唯一 1 条 = 自递归；dword 字面量 0、`push imm32` 0；审计补测 0f8x / eb·7x rel8 / `ff15`·`ff25` 各 0，`.rdata`/`.data`/`.detour` rel32 各 0，RVA `0x3c6620` 与段相对 `0x3c5620` 各 0。⇒ 与 `0x7c62ac`、`0x7c6270`、`0x7c6730`、`0x7c6752` 整族同属死区；活跃音频路径只有块2 族 + 状态清零器 `0x7c7350`。
- **状态块只有 12 B / 4 个偏移（R222 待办② 关闭）**：`obj+0x7d0`(dword 值)、`obj+0x7d4`(word step)、`obj+0x7d6`(dword ch2 值)、`obj+0x7da`(word ch2 step)；内部位点 `+0` 4 处、`+4` 4 处、`+6` 2 处、`+0xa` 2 处；与 `0x7c7350` 写的四槽 `[eax]`/`[eax+4]`/`[eax+6]`/`[eax+0xa]` **一一对应**。`0x7c7350` 唯一调用点 `0x7c2a74`；`0x7c7371` 恰 2 个调用点 `0x7c24a2`/`0x7c2557`。窗口内 `[ebx+0x7fc]` 两条（`0x73c51c`/`0x73c5b2`）属**另一对象**，不并入本块。
- **四张 4 项对齐表同构 + 与 8 项 nibble 表成对（R222 待办③ 关闭）**：每族 `4t − 8t` 恒 **0x20**（块1 `0x7c6b58/0x7c6b38`、2A `0x7c7778/0x7c7758`、2B `0x7c7b3c/0x7c7b1c`、2C `0x7c7f10/0x7c7ef0`），8 项表与 4 项表相对块1 位移相同（`0xc20/0xfe4/0x13b8`）。屏蔽 imm32+disp32 后**跨表同索引 4/4 全等**（k=0 13 B、k=1/2/3 各 15 B）；再屏蔽 imm8 后全库仅 **2 图案**（4+12 成员）。唯一结构差异是 stub0 后的对齐填充 `90`/`8bff`/`8d4900`/`8d4900`。4 项表三个非零项跳进本族 8 项表 idx **6/4/2**（12/12，`8-2k` 律），stub3 结束 +1 恰为本族解码器入口（4/4）。
- **`.data` 320 dword 单调串不是指针表（反控）**：`[0x874700,0x874c00)` 320 值全落 `.text`、步长 `0x204..0x20a`、首 `0x7b15ec` 末 `0x7d9d27`；但逐值搜 disp32 **0 命中**、`%4==0` 仅 **91/320**、前驱 int3/ret **0/320** ⇒ 数据巧合。审计中的「指向音频簇的 dword」全落在这一串里，只有 1 个是真实指令起点，不可当函数指针。
- **网格描述符与消费者隔离**：`0x8759a0←d[0x87f918]+1`（行）、`0x8759a4←d[0x87f914]+1`（列/步长）、`0x8759a8←d[0x87f90c]`、`0x8759ac←d[0x87f910]`；分配 `(rows)*(cols)*8`、清零 `esi−1` 次、基址 `0xb0b6ec`（BSS）。引用 4/18(16R2W)/10/10/32；**活跃块2 族引用全 0** ⇒ 网格与 ADPCM 两条独立数据流，`0x7c6620` 是唯一同时读 base 与 stride 的消费者。
- **跨家族**：exec `#584`（hy4，**39 回合 / 20.37′**，`[OVERTIME: 20.37' vs 2.0']`）26/26 PASS；审计 `#585`（hy4 audit，**18 回合 / 18.43′**，`[OVERTIME]`）A8/B4-of-5/C3 通过（B4 口径订正：表址 disp32 起点 = 指令起始 +3，ModRM `9d`）；跨家族审计 `#587`（deepseek audit，**24 回合 / 8.05′**）三争议点全部复现并**订正措辞**（「跨表同索引相同（4 组×4）」而非「16 个全部相同」）、独立发现「表址位移与 handler 位移不等差（+0xc1f vs +0xc20）」已复算成立；`#586`（deepseek 首发）`cancelled` 0 回合 / 15.9′ 如实记录。
- **自错 2 条（0 条进结论）**：E1 `p1_four.py` W2「原文无 CRLF」与 CR=1081 口径矛盾（同 R222 E2）；E2 `m9_tables_final.py` 首版把 stub0 后的间接 jmp 计入 stub 体致 pad 判据错位。
- **收口**：R14 §2.231 CR **1081**（1965287→1974405 B）、GOAL §1281 CR **337**、本段 QZ CR **137**、本段 CR **0**（开局 272 行 ≥ 260，**已归档 206/207 轮到 BOARD_ARCHIVE**：1535894→1551003 B、ARCH CR 保持 2952；BOARD 272→225 行）。判据 `_r223/` 13 脚本 **124 断言 / 0 FAIL**（m7 32、m9 16、m19 13、m13 12、m20 10、m17 8、m12 7、m10 6、m11 6、m14 4、m2 3、m16 2、m18 2）。
"""
BOARD_APP=BOARD_APP.replace('\r\n','\n')
b,dst=bak(BOARD,'BOARD')
ck('B1 BOARD 备份已独占创建',os.path.exists(dst),dst)
s=b.decode('utf-8')
ck('B2 BOARD 追加段无 CR','\r' not in BOARD_APP)
ck('B3 BOARD 追加段无 tab','\t' not in BOARD_APP)
new=s+BOARD_APP
if not new.endswith('\n'): new+='\n'
nb=new.encode('utf-8')
ck('B4 BOARD 新 CR == 0',nb.count(b'\r')==0,nb.count(b'\r'))
ck('B5 BOARD 新行数 <= 300',nb.count(b'\n')<=300,nb.count(b'\n'))
open(BOARD,'wb').write(nb)
ck('B6 BOARD 回读一致',open(BOARD,'rb').read()==nb)
print('[BOARD] %d -> %d 行 CR=%d'%(b.count(b'\n'),nb.count(b'\n'),nb.count(b'\r')))
if fails:
    print('[FAILS]',fails)
