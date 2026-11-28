# -*- coding: utf-8 -*-
"""R223 四件套写入：R14_COMMON §2.231 / GOAL §1281 / LEAD_LOCK QZ / STATUS_BOARD 第 223 轮。"""
import os, hashlib, re
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/R17_LEAD_BASELINE'
TIER=ROOT+'/lead/next_re_20261117_r14'
RC=TIER+'/R14_COMMON.md'; GOAL=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK=ROOT+'/lead/LEAD_LOCK'; BOARD=TIER+'/STATUS_BOARD.md'; ARCH=TIER+'/BOARD_ARCHIVE.md'
EXPECT={RC:(1081,1965287),GOAL:(337,5492231),LOCK:(137,1534826),BOARD:(0,80643),ARCH:(2952,1551003)}
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
    raise SystemExit('bak exhausted: '+path)
print('=== 0 写前不变量 ===')
pre={}
for p,(cr,nb) in EXPECT.items():
    b=open(p,'rb').read()
    pre[p]=(hashlib.sha256(b).hexdigest(),len(b),b.count(b'\r'))
    ck('I0 %s CR=%d bytes=%d'%(os.path.basename(p),cr,nb), b.count(b'\r')==cr and len(b)==nb, pre[p])
rcs=[l for l in open(RC,encoding='utf-8').read().split('\n') if l.startswith('## 2.')]
gs=[l for l in open(GOAL,encoding='utf-8').read().split('\n') if l.startswith('## §')]
lc=re.findall(r'^\*\*([A-Z]{2})\d*\.',open(LOCK,encoding='utf-8').read(),re.M)
bl=open(BOARD,'rb').read().count(b'\n')
ck('I1 R14 末节 = 2.230', rcs[-1].startswith('## 2.230'), rcs[-1][:40])
ck('I2 GOAL 末节 = §1280', gs[-1].startswith('## §1280'), gs[-1][:40])
ck('I3 LEAD_LOCK 末段 = QY（下一段 QZ 未被占用）', lc[-1]=='QY', lc[-3:])
ck('I4 STATUS_BOARD 已归档到 225 行（< 260）', bl==225, bl)
if fails:
    print('[ABORT 写前]',fails); raise SystemExit(1)

# ---------------------------------------------------------------- R14_COMMON
R14_APP = """
## 2.231 R223（2026-11-28）· 0x7c6620 网格冲突检查器全解 + 0x7c7371 状态块 4 偏移布局 + 四张 4 项对齐表同构 + 音频簇活跃/死代码分界

**1. 0x7c6620 是「网格记录 3x3 邻域冲突检查器」，不是 ACM 帧更新器（R222 待办① 关闭）.** 函数体
`[0x7c6620, 0x7c672a)` = 0x10a B，`0x7c672a` 起 5 B `cc`（前邻 `0x7c6613..0x7c661f` 13 B 全 `cc`）。
寻址：`0x7c662a mov eax,[ebp+0xc]` → `0x7c6633 imul eax,dword[0x8759a4]`（步长取**内存全局**不是立即数）→
`0x7c663a add eax,[ebp+8]` → `0x7c663d lea esi,[esi+eax*8]`，`esi` 来自 `0x7c662d mov esi,[0xb0b6ec]`
⇒ **rec = dword[0xb0b6ec] + (arg1 + arg2*dword[0x8759a4]) * 8**。记录只有两个字段被触碰：`[rec+0]`（dword 值，
12 处读写）与 `[rec+4]`（dword 标志，`test ...,1` 于 `0x7c667d`，`or ...,2` 于 `0x7c66c7`/`0x7c66dc`）；
全函数 **无** `[esi+5..7]` 访问 ⇒ 8 B 记录只用 6 B（与分配器 `0x6b2756..0x6b2764` 清零 `[rec+0]`(dword)+`[rec+4]`(byte)+`[rec+5]`(byte) 完全一致）。

**2. 算法：3x3 邻域 + 阈值 0xc + 双向修补.** 双重循环 `edi`/`ecx` 初值均 `0xffffffff`、回边 `cmp reg,2` + `jl`
（`0x7c670b/0x7c670c/0x7c670f` 内层、`0x7c6715/0x7c6716/0x7c6719` 外层）⇒ 9 组；`(0,0)` 那组由
`0x7c664f mov eax,edi` / `0x7c6651 or eax,ecx` / `0x7c6653 test eax,eax` / `0x7c6655 je 0x7c670b` 跳过（`or` 结果 0 仅当两者全 0）。
对每个邻居：`abs(邻居值 − 本记录值) = 0xc` 以内继续（`cdq` + `xor eax,edx` + `sub eax,edx` 各 2 次，`cmp eax,0xc`
在 `0x7c6696`/`0x7c66ad`），超过则进入修补。修补按 `[rec+4] bit0` 分两支：bit0 置位且 `arg3 != 0`
（`0x7c6686 cmp dword[ebp+0x14],0` / `0x7c668a jne 0x7c670b`）⇒ **直接返回 0**（不修）；bit0 清零 ⇒ 按
`arg2 == 1`（`0x7c66b2 cmp dword[ebp+0x10],1`）决定方向：邻居值 < 本值则把邻居改成 `本值 − 0xc`
（`0x7c66bf..0x7c66c5`），否则改成 `本值 + 0xc`（`0x7c66d4..0x7c66da`），并 `or dword[rec+4],2` 标记已修。
修补后**递归**同一函数处理被拖动后的邻居（`0x7c66ee call 0x7c6620`，4 实参 + `0x7c66f3 lea esp,[esp+0x10]`），
递归返回 0 且 `arg3 == 0` 时本层也返回 0（`0x7c66fd cmp dword[ebp+0x14],0` / `0x7c6701 jne` / `0x7c6703 xor eax,eax`）。
全函数 3 个 `ret`（`0x7c66a2`/`0x7c670a` 前 `xor eax,eax`；`0x7c6729` 前 `mov eax,1`）⇒ 返回值只有 0/1。

**3. 0x7c6620 在文件里无任何外部引用（死代码，二审一致）.** 全 `.text` 扫 `e8/e9` rel32 指向 `0x7c6620`
**唯一 1 条 = 0x7c66ee 自递归**；全文件 dword 字面量 `0x7c6620` **0 次**、`68 20 66 7c 00`（push imm32）**0 次**；
跨家族审计员另测 0f8x rel32 / eb·7x rel8 / `ff 15`·`ff 25` 三种间接形式各 **0**，`.rdata`/`.data`/`.detour` 内 rel32 各 **0**，
RVA 形式 `0x3c6620` 与段相对 `0x3c5620` 各 **0**；无导出、relocs stripped。⇒ 与 `0x7c62ac`（解包器）、`0x7c6270`（reset8）、
`0x7c6730`（reset4）、`0x7c6752` 及其整族（块1）同属**未被引用的死区**，`gamemd.exe` 里活跃的音频路径只有块2 族 + 状态清零器。

**4. 0x7c7371 的状态块 `&[ebx+0x7d0]` 只 4 个偏移、共 12 B（R222 待办② 关闭）.** 窗口扫描口径两条独立互校：
① 全 `.text` 扫 `[ebx + 0x7d0..0x7ff]` 字面 disp（`disasm_lite` 一遍，1394186 条）得 **5 个位点**：
`0x7c2490` / `0x7c2545` / `0x7c2a6d` 三条 `lea`（取址传参）+ `0x73c51c` / `0x73c5b2` 两条 `[ebx+0x7fc]`（**属另一对象**，与 0x7d0 块无关）；
② 在 `0x7c7371..0x7c8000` 内部按「`ebx` 已被 `0x7c7379 mov ebx,[ebp+0x1c]` 重载为结构基址」的派生口径扫描，得 4 个字段：
`+0`（dword，4 位点：`0x7c73c7`/`0x7c778c` 读、`0x7c798b`/`0x7c75c3` 写）、`+4`（word，4 位点：`0x7c73c9`/`0x7c778e` 读、`0x7c798d`/`0x7c75c5` 写）、
`+6`（dword，2 位点：`0x7c7b61` 读 / `0x7c7d5b` 写）、`+0xa`（word，2 位点：`0x7c7b64` 读 / `0x7c7d5e` 写）。
映射回对象 = `obj+0x7d0` / `obj+0x7d4` / `obj+0x7d6` / `obj+0x7da`，**12 B 连续**（`+0..+0xb`），
与清零器 `0x7c7350` 写的四个槽 `[eax]`(dword)/`[eax+4]`(word)/`[eax+6]`(dword)/`[eax+0xa]`(word) **一一对应**
⇒ 状态块 = 两个声道各 6 B（int32 预测器 + uint16 step），与 R222 记录 6 B/声道自洽。
`0x7c7350` **唯一调用点 0x7c2a74**（全 `.text` rel32 扫）；`0x7c7371` 恰 **2 个调用点 0x7c24a2 / 0x7c2557**。

**5. 四张 4 项对齐表同构（R222 待办③ 关闭），且与各自的 8 项 nibble 表成对.** 四族实测：
块1 `4t=0x7c6b58 / 8t=0x7c6b38 / dec=0x7c6808`；块2A `0x7c7778 / 0x7c7758 / 0x7c7428`；
块2B `0x7c7b3c / 0x7c7b1c / 0x7c77f0`；块2C `0x7c7f10 / 0x7c7ef0 / 0x7c7bc0`；
**每族 `4t − 8t` 恒 `0x20`（8 项表后紧跟 4 项表）**，四族的 8 项表相对块1 的位移与 4 项表位移**完全相同**
（`0xc20 / 0xfe4 / 0x13b8`）。4 项表内容：`7c67c3/7c67d8/7c67e8/7c67f8`、`7c73e2/7c73f8/7c7408/7c7418`、
`7c77a9/7c77c0/7c77d0/7c77e0`、`7c7b79/7c7b90/7c7ba0/7c7bb0`。
逐 stub 屏蔽（imm32 与 disp32 置 0）比对：**跨表同索引 4/4 全等**（k=0 组 13 B `55c1ed0433db0bede9…`；
k=1/2/3 组各 15 B `83ed0c/08/04 55c1ed04 33db 45 e9…`）⇒ **四张表是同一模板的四份独立展开**；
把 imm8 也屏蔽后全库只剩 **2 个图案**（13 B 组 4 个成员 + 15 B 组 12 个成员）。stub0 之后的**对齐填充**是唯一结构差异：
块1 `90`（1 B）、块2A `8bff`（2 B）、块2B/2C `8d4900`（3 B）—— 三档 pad 恰把下一个 stub 对到 4 字节边界。
4 项表各有 **1 条** `jmp dword ptr [ebx*4 + 表址]` 引用（指令起始 `0x7c67d0`/`0x7c73ef`/`0x7c77b6`/`0x7c7b86`；
表址 disp32 起点 = 指令起始 +3），表址字面量全文件各 **1** 次。
4 项表三个非零项的跳转目标全部落在**本族 8 项表内**：`stub1 → idx6`、`stub2 → idx4`、`stub3 → idx2`（四族 12/12 一致，`8-2k` 律）；
`stub3` 结束地址 +1 恰为**本族解码器入口**（4/4）。⇒ 4 项表 = 声道/位宽组合的「对齐修正」跳板，8 项表 = nibble 值分派。

**6. `.data` 的 320 dword 单调串 [0x874700,0x874c00) 不是指针表（反控成立）.** 该区间 320 个 dword 值全落 `.text`、
单调递增、步长 `0x204..0x20a`（`0x206`×7 / `0x207`×55·… 、均值 519.4）、首 `0x7b15ec` 末 `0x7d9d27`；
但：①全 `.text` 对 `[0x874700,0x874c00)` **逐值**搜 disp32 命中 **0**；②这些值 **不是 4 对齐**（320 中仅 91 个 `%4==0`）；
③前驱字节是 `int3`/`ret` 的 **0/88**（第一段）与 **0/320**（全段）⇒ **不是函数入口**、**不是跳转表**，是编译器生成的数据巧合。
（审计中出现的 `0x7c6789`/`0x7c6990`/`0x7c637a`/`0x7c6581` 等「指向音频簇的 dword」全部落在这串里，且 4 个只有 1 个是真实指令起点，
不能当作函数指针证据。）

**7. 网格描述符 4 个全局与网格消费者.** `0x8759a0 ← dword[0x87f918]+1`（`0x6b2784`，行数）、
`0x8759a4 ← dword[0x87f914]+1`（`0x6b27ec` 与 `0x6b2b3b`，列数/步长）、`0x8759a8 ← dword[0x87f90c]`（`0x6b27fe`）、
`0x8759ac ← dword[0x87f910]`（`0x6b2790`）；分配字节 = `(d[0x87f918]+1) * (d[0x87f914]+1) * 8`
（`0x6b2731 lea esi,[eax+1]` / `0x6b2730 inc ecx` / `0x6b2734 imul esi,ecx` / `0x6b2737 lea edx,[esi*8]`），
清零循环跑 `esi−1` 次（`0x6b274b lea edx,[esi-1]`），基址存 `0xb0b6ec`（BSS，文件内无字节）。
引用计数：`0x8759a0` 4 / `0x8759a4` 18（16 读 2 写）/ `0x8759a8` 10 / `0x8759ac` 10 / `0xb0b6ec` 32。
**活跃的块2 族（`0x7c7371..0x7c7f20`）对这四个全局与网格基址引用数均为 0** ⇒ 网格记录与 ADPCM 解码是两条独立的数据流；
`0x7c6620` 是唯一同时读 `0xb0b6ec` 与 `0x8759a4` 的消费者 ⇒ 它是网格子系统的成员。

**8. 判据与反控.** `_r223/m2_window.py` 3/0、`m7_final.py` **32/0**、`m9_tables_final.py` **16/0**、`m10_grid.py` 6/0、
`m11_live.py` 6/0、`m12_indirect.py` 7/0、`m13_reach2.py` 12/0（2 条 FAIL 已定性为「320 dword 串撞值」假阳性，见第 6 条）、
`m14_tbl874.py` 4/0、`m16_grid2.py` 2/0、`m17_proof.py` 8/0、`m18_grid3.py` 2/0、`m19_facts.py` 13/0、`m20_audit_recheck.py` 10/0。
反控：eax 基址同窗口扫描 vs ebx 5 个位点；把 imm8 一并屏蔽后图案数 4→2；去掉 `+2 B` 偏置见 R222；
320 dword 串的「不是 4 对齐/不是入口/无 disp32」三条独立否证指针表假设。`gamemd.exe` sha256 `73201cc0…f3fcf67476`。

### 十一 · 仍未取得

①`0x7c6620` 的记录值语义（网格里是什么量纲）与 `arg3`/`arg4` 的真实含义（静态只能证明是标志位与开关）；
②`[rec+4]` bit2..bit31 是否有其它使用方（本轮只观测 bit0/bit1）；③`dword[0x87f90c]`/`dword[0x87f910]` 的语义（只知被写入 `0x8759a8`/`0x8759ac`）；
④F23/F35 grade 裁定；⑤C7 三死分支自然真实行、C11 十二 ID 真判据接入方案。
"""
R14_APP=R14_APP.replace('\r\n','\n')
b,dst=bak(RC,'R14')
ck('W1 R14 备份已独占创建',os.path.exists(dst),dst)
s=b.decode('utf-8')
ck('W2 R14 原文无 CRLF','\r\n' not in s)
ck('W3 R14 追加段无 CR','\r' not in R14_APP)
ck('W4 R14 追加段无 tab','\t' not in R14_APP)
new=s+R14_APP; nb=new.encode('utf-8')
ck('W5 R14 新 CR == 1081',nb.count(b'\r')==1081,nb.count(b'\r'))
ck('W6 R14 字节净增 == 追加段长度',len(nb)-len(b)==len(R14_APP.encode()),(len(b),len(nb)))
ck('W7 R14 新末节 = 2.231',[l for l in new.split('\n') if l.startswith('## 2.')][-1].startswith('## 2.231'))
open(RC,'wb').write(nb)
back=open(RC,'rb').read()
ck('W8 R14 回读一致',back==nb,hashlib.sha256(back).hexdigest()[:16])
print('[R14] %d -> %d B, CR=%d'%(len(b),len(nb),back.count(b'\r')))
