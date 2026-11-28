#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 四件套余下三件 + C16 钉入 + 门禁回归。
GOAL_THREE_TARGETS §1250 / LEAD_LOCK PX 段 / STATUS_BOARD 第 195 轮；check_disc C16_FLOORS 190 -> 192（钉 199、200）。
"""
import os,sys,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
T=os.path.join(ROOT,'lead/next_re_20261117_r14'); LR=os.path.join(ROOT,'lead')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def rd(p): return open(p,'rb').read()
def wr(p,b): open(p,'wb').write(b)
def sha(b): return hashlib.sha256(b).hexdigest()
S200=6684; F200=S200//2

# ---------- GOAL_THREE_TARGETS §1250 ----------
P=os.path.join(LR,'GOAL_THREE_TARGETS_20261018.md'); raw=rd(P)
ck('G0a 旧 GOAL CR=337 / LF=48570 / sha cfe2da1b',raw.count(b'\r')==337 and raw.count(b'\n')==48570 and sha(raw).startswith('cfe2da1b'),
   (raw.count(b'\r'),raw.count(b'\n'),sha(raw)[:16]))
S1250=('\n\n## §1250 R195：L 的 78 张表安装面（341 条装点 / 零命中 0）；AbstractClass 构造族 5 入口与 +0x10/+0x20 二进制内自证；'
'槽 18..23 默认实现与 0x48 复用；0x4105A0 = 1 主表 + 3 子表；二次构造函数内覆写主表；CRC 状态 +0 无初值写入（331==331 口径订正）\n\n'
'**① 安装面（100% 覆盖的 resync 线性扫描）**：1,394,132 条指令 / 4,063,139 B（段 4,063,232 B）/ 重同步 93 次 ⇒ 「imm32 == L 表头」**341 条**，'
'78/78 张表头全有、零命中 **0**、形态 100% `mov [reg],imm32`；每张 3..8 次（恰 3 次 14 张、8 次 1 张 0x7E8B38）。'
'反控：这 341 个地址在全文件其余四段里**一次都不出现**，byte=inst=341（不虚高）。旧读数「4 条 / 2 张」与「285 条 / 10 张零命中」分别由字节扫描错位、块内失步造成。\n\n'
'**② 构造族 5 入口**：0x410170 / 0x4101C0 / 0x4101E0 / 0x4105A0 / 0x6E8000，全部装 0x7E1F50（24 槽）。0x410170 给出 +0x10 = 0xFFFFFFFF、'
'+0x14 低 3 位清零、+0x18 = 0、+0x1C = 0、+0x20 = 0 ⇒ **+0x10 / +0x20 首次拿到二进制内自证**（此前只有 kb/22 外部源）。\n\n'
'**③ 0x4105A0（标量删除析构）一次装 4 张表**：+0 = 0x7E1F50（主表 24 槽）、+4 = 0x7E1F34（mdisp 4，6 槽）、+8 = 0x7E1F2C（mdisp 8，1 槽）、'
'+0xC = 0x7E1F24（mdisp 12，1 槽）；表头前 4 字节 **4/4 都是 COL**，后三条 pCHD 同为 0x7FB108。\n\n'
'**④ 二次构造**：0x6E8000 先装 0x7E1F50 四次，随后 0x6E807E 把 +0 覆写成 0x7F4680、（+4/+8/+0xC）覆写成 0x7F4664/0x7F465C/0x7F4654。\n\n'
'**⑤ 槽 18..23**：0x4104C0 / 0x4104F0 / 0x410520 / 0x410530 / 0x410540 / 0x410570；槽 19 与槽 22 体内 `call [eax+0x48]`（= 槽 18，全段 929 处）；'
'槽 18 读三个 .data **BSS** 全局 0x887680/4/8，唯一写入者 0x410110（连写三处清零）、唯一读取者 0x4104C0。\n\n'
'**⑥ CRC 状态归属**：0x4A1CA0 调用面 **331 == 331**（resync 线性 / 字节 E8+rel32），R194「上界 331 / 下界 94 / 假命中 237」应读作「331 即真值，'
'94 是不重同步的产物（丢 213 条 = 64.4%）」；体 55 条 / 134 B / 四槽 {+0,+4,+8,+0xC} / `not` 2 次；+0 唯一写 **0x4A1D1B `89 01 mov [ecx],eax`**，'
'是 read-modify-write，**无独立初值写入**。\n\n'
'**⑦ 未取得**：实现语义名、CRC 初值来源、0x6E8000 覆写的语义动机、三个 BSS 全局含义、`ncb` 最大 = 最外层 的编译器依据。\n\n'
'**⑧ 跨家族**：执行员 #477（hy4，18 回合 / 4.25 分）15/15 PASS 且「+0 无初值写入」成立，但「线性 118」被主会话复算推翻（真值 331）；'
'执行员 #478（61 回合 error_max_turns）用 d0 判主/子表（得 1214/0），L=0 全链作废；审计员 #479（21 回合 error_max_turns，[OVERTIME 8.73\' vs 8.0\']）'
'被砍前已写出 16,200 B 产物，六问三反控全部完成且与主会话逐值一致，并额外指出「21 张 >64 槽表头全在 L 内、贡献 L 槽数的 69.7%」。\n')
nb=(raw.decode('utf-8')+S1250).encode('utf-8')
ck('G1 新 GOAL CR 保持 337',nb.count(b'\r')==337,nb.count(b'\r'))
ck('G2 §1250 唯一',nb.count('## §1250 R195'.encode())==1,nb.count('## §1250 R195'.encode()))

# ---------- LEAD_LOCK PX ----------
P2=os.path.join(LR,'LEAD_LOCK'); raw2=rd(P2)
ck('K0a 旧 LEAD_LOCK CR=137 / LF=8035 / sha 3fd3481e',raw2.count(b'\r')==137 and raw2.count(b'\n')==8035 and sha(raw2).startswith('3fd3481e'),
   (raw2.count(b'\r'),raw2.count(b'\n'),sha(raw2)[:16]))
PX=('\n\n## PX · R17 第 195 轮（2026-11-28 11x–12x）· L 的 78 张表的**安装面**全图（341 条装点、零命中 0 张、100% 覆盖）；'
'AbstractClass 构造族 5 入口与 +0x10/+0x20 的**二进制内自证**；0x4105A0 = 1 主表 + 3 子表；槽 18..23 与 0x48 复用；CRC 状态 +0 无初值写入、调用面 331==331 口径订正\n\n'
'**PX1. 🔴 交付一：安装面 —— 78/78 张表全有指令级装点、零命中 0 张.** 见 R14_COMMON §2.200 一。**341 条**，形态 100% `mov [reg],imm32`，'
'每张 3..8 次。反控：341 个地址在 .data/.rdata/.rsrc/.detour 里**一次都不出现**（byte=inst=341，不虚高）。'
'旧读数「4 条 / 2 张」（字节扫描 `i+=2` 错位 + 漏 ModRM 内 C7）与「285 条 / 10 张零命中」（64KB 分块但块内不重同步）**均作废**。\n\n'
'**PX2. 🔴 交付二：AbstractClass 构造族 = 5 个入口 + 字段初值自证.** 0x410170 / 0x4101C0 / 0x4101E0 / 0x4105A0 / 0x6E8000 全装 0x7E1F50（24 槽）。'
'0x410170：+0x10 = **0xFFFFFFFF**、+0x14 低 3 位清零、+0x18 = 0、+0x1C = 0、+0x20 = **0**。'
'⇒ +0x10/+0x20 两字段**首次拿二进制内自证**，不再只依赖 kb/22。\n\n'
'**PX3. 🟠 交付三：0x4105A0 = 1 主表 + 3 接口子表.** +0 = 0x7E1F50（24 槽，mdisp 0）、+4 = 0x7E1F34（mdisp 4，6 槽）、+8 = 0x7E1F2C（mdisp 8，1 槽）、'
'+0xC = 0x7E1F24（mdisp 12，1 槽）；表头前 4 字节 **4/4 都是 COL**，后三条 pCHD 同为 0x7FB108；尾部 `call 0x7C8B3D` = operator delete 薄壳 ⇒ 标量删除析构形态。\n\n'
'**PX4. 🟠 交付四：二次构造的字节实证.** 0x6E8000 先装 0x7E1F50 四次，**0x6E807E 把 +0 覆写成 0x7F4680**、+4/+8/+0xC 覆写成 0x7F4664/0x7F465C/0x7F4654'
'⇒ 同一构造函数内主表被替换。\n\n'
'**PX5. 🟠 交付五：槽 18..23 默认实现（§2.199 只到 17）.** 0x4104C0 / 0x4104F0 / 0x410520 / 0x410530 / 0x410540 / 0x410570。'
'槽 19 与槽 22 都 `call [eax+0x48]`（= 槽 18，全段 **929 处**）；槽 18 读三个 .data **BSS** 全局 0x887680/4/8，唯一写 0x410110（连写三处清零）、唯一读 0x4104C0。\n\n'
'**PX6. 🟠 交付六：CRC 状态对象归属与调用面口径订正.** 0x4A1CA0 调用面 **331 == 331**（resync 线性 / 字节 E8+rel32），'
'⇒ R194「上界 U=331 / 下界 94 / 假命中 237」应读作「**331 即真值**，94 是不重同步的产物（丢 213 条 = 64.4%）」。'
'体 55 条 / 134 B / 四槽 {+0,+4,+8,+0xC} / `not` 恰 2 次；**+0 唯一写 = 0x4A1D1B `89 01 mov dword ptr [ecx], eax`**，'
'是「读入 → not → 折叠 → not → 写回」，**无独立初值写入** ⇒ 初值来源（R194 遗留）**仍未取得**。\n\n'
'**PX7. 🟡 落盘与门禁.** 台账 **V579 → V580**（只改 F55：stmt 22,159→**25,923 B**、lim 17,231→**17,582 B**、第 4 列 733→**892 B**、**197,698 B**、'
'sha `57a6e343…`、**9 断言 0 FAIL**）；R14_COMMON 追加 **§2.200（6,684 B ⇒ floor 3,342）**，CR 保持 1081；GOAL 追加 **§1250**，CR 保持 337；'
'LEAD_LOCK 追加 **PX**，CR 保持 137；STATUS_BOARD 追加第 195 轮，CR 保持 0。看板开局 **277 行 ≥ 260** ⇒ 先归档最早两段（R184、R185，53 行）'
'到 BOARD_ARCHIVE（**17 断言 0 FAIL**；归档 1,419,491 → **1,428,551 B** / CR 2952；看板 59,375 → **50,315 B** / 224 行）。'
'C16_FLOORS 190 → **192**（钉 §2.199 / §2.200）并重算 C16_FLOORS_SHA256。\n\n'
'**PX8. 📌 自错（当场抓出，无一条进入结论）.** ① 字节模式扫 C7（`i+=2` 错位）得 4 条 / 2 张表；② 64KB 分块不重同步得 285 条 / 10 张零命中；'
'③ 单次连续 `disasm_lite` 在 `0x46F5A0` 停住，只覆盖 11.12%，会把 331 错报成 118；④ `chain()` 传错对象类型（int vs COL dict）触发 TypeError 两次；'
'⑤ 把 `mov eax,[0x887680]` 的指令地址 0x410113 误读成装点地址；⑥ 正则把 capstone 小偏移写成 `0x +`（实际十进制）致 D4/D5 假 FAIL 两次。\n\n'
'**PX9. ⚪ 未取得（不粉饰）.** ① 18+6 个实现的**游戏语义名**仍未取得；② CRC 状态 +0 的**初值来源**未取得；③ 0x6E8000 覆写主表的**语义动机**未取得；'
'④ 三个 BSS 全局的游戏含义未取得；⑤ 「`numContainedBases` 最大 = 最外层」仍无编译器侧依据；⑥ **跨家族**：执行员 **#477**（hy4，18 回合、4.25 分 / 预算 8 分）15/15 PASS 且「+0 无初值写入」成立，'
'但其「线性诊断 118」与「c=118/d=0」**被主会话复算推翻**（真值 331，且 331 里 271 个 ecx 来路无法用 64 B 前向窗口判定）；'
'执行员 **#478**（hy4，61 回合 `error_max_turns`）用 `d0` 判主/子表（得 1214/0），L=0 全链作废，未采用；'
'审计员 **#479**（deepseek，21 回合 `error_max_turns`，`[OVERTIME: 实测 8.73\' vs 预算 8.0\']`）在被砍前已写出 `_r195/audit_r195_core.txt`（16,200 B），'
'六问三反控全部完成，与主会话**逐值一致**，并额外指出「21 张 >64 槽表头全在 L 内、贡献 L 槽数 5,607 中的 3,910（69.7%）」；'
'⑦ F23/F35 grade 未改；⑧ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑨ 86.19% 原值仍不可重算；⑩ C7 三死分支仍各 0 行、C11 十二个永不 FAIL id 未动。\n')
nb2=(raw2.decode('utf-8')+PX).encode('utf-8')
ck('K1 新 LEAD_LOCK CR 保持 137',nb2.count(b'\r')==137,nb2.count(b'\r'))
ck('K2 PX 段唯一',nb2.count('## PX · R17 第 195 轮'.encode())==1,nb2.count('## PX · R17 第 195 轮'.encode()))

# ---------- STATUS_BOARD 第 195 轮 ----------
P3=os.path.join(T,'STATUS_BOARD.md'); raw3=rd(P3)
ck('B0a 旧看板 CR=0 / 224 换行 / sha（归档后）',raw3.count(b'\r')==0 and raw3.count(b'\n')==224,
   (raw3.count(b'\r'),raw3.count(b'\n')))
SB=('\n\n## 🟢 R17 第 195 轮（2026-11-28 11x–12x）· L 的 78 张表的**安装面**全图（341 条装点 / 78 张零命中 0 / 100% 覆盖）；AbstractClass 构造族 5 入口把 +0x10、+0x20 变成**二进制内自证**；0x4105A0 = 1 主表 + 3 子表；二次构造函数内覆写主表；CRC 状态 +0 **无初值写入**、调用面 331==331 口径订正\n\n'
'**交付一 · 安装面.** resync 线性反汇编 1,394,132 条 / 覆盖 4,063,139 B（段 4,063,232 B = 100.00%）/ 重同步 93 次 ⇒ 「imm32 == L 表头」**341 条**：'
'**78/78 张表头全有、零命中 0 张**、形态 **100% `mov dword ptr [reg], imm32`**、每张 **3..8 次**（恰 3 次 14 张、8 次 1 张 `0x7E8B38`）。'
'反控：这 341 个地址在 .data/.rdata/.rsrc/.detour 里**一次都不出现**，byte=inst=341（不虚高）。'
'旧读数「4 条 / 2 张」（字节扫 C7 时 `i+=2` 错位）与「285 条 / 10 张零命中」（64KB 分块块内不重同步）**均作废**。\n\n'
'**交付二 · 构造族 5 入口 + 字段内自证.** 0x410170 / 0x4101C0 / 0x4101E0 / 0x4105A0 / 0x6E8000 全装 `0x7E1F50`（24 槽）。'
'0x410170：`+0x10 = 0xFFFFFFFF`（`c7 40 10 ff ff ff ff`）、`+0x14` 低 3 位清零、`+0x18 = 0`、`+0x1C = 0`、`+0x20 = 0`'
'（`mov byte ptr [eax+0x20], cl`，cl 源自 `xor ecx,ecx`）⇒ **+0x10 / +0x20 首次拿二进制内自证**，此前只有 kb/22 外部源。\n\n'
'**交付三 · 0x4105A0 = 1 主表 + 3 接口子表.** `+0 ← 0x7E1F50`（主表 24 槽）、`+4 ← 0x7E1F34`（mdisp 4 / 6 槽）、`+8 ← 0x7E1F2C`（mdisp 8 / 1 槽）、'
'`+0xC ← 0x7E1F24`（mdisp 12 / 1 槽）；表头前 4 字节 **4/4 都是 COL**，后三条 pCHD 同为 `0x7FB108`；尾部 `call 0x7C8B3D`（operator delete 薄壳）⇒ 标量删除析构。\n\n'
'**交付四 · 二次构造.** 0x6E8000 先装 `0x7E1F50` 四次，**0x6E807E 把 +0 覆写成 `0x7F4680`**、+4/+8/+0xC 覆写成 `0x7F4664 / 0x7F465C / 0x7F4654`'
'⇒ 同一构造函数里主表被替换。\n\n'
'**交付五 · 槽 18..23.** `0x4104C0 / 0x4104F0 / 0x410520 / 0x410530 / 0x410540 / 0x410570`；槽 19 与槽 22 体内都 `call [eax+0x48]`（= 槽 18，全段 **929 处**）；'
'槽 18 读三个 .data **BSS** 全局 `0x887680/4/8`（vsize 内、rawsize 外），唯一写 `0x410110`（连写三处清零）、唯一读 `0x4104C0`。\n\n'
'**交付六 · CRC 状态归属（R194 遗留）.** `0x4A1CA0` 调用面 **331 == 331**（resync 线性 / 字节 `E8+rel32`）⇒ R194「上界 331 / 下界 94 / 假命中 237」'
'应读作「**331 即真值**，94 是不重同步产物（丢 213 条 = 64.4%）」。体 **55 条 / 134 B**、四槽 `{+0,+4,+8,+0xC}` 全中、`not` **恰 2 次**；'
'**+0 唯一写 = 0x4A1D1B `89 01 mov [ecx],eax`**，是 read-modify-write，**无独立初值写入** ⇒ 初值来源**仍未取得**。\n\n'
'**落盘 · 三门 · 归档.** 看板开局 **277 ≥ 260** ⇒ 先归档最早两段（R184、R185，53 行，**17 断言 0 FAIL**；归档 1,419,491 → **1,428,551 B** / CR 2952，'
'看板 59,375 → **50,315 B** / 224 行）。台账 **V579 → V580**（只改 F55：stmt **25,923 B** / lim **17,582 B** / 第 4 列 **892 B** / **197,698 B** / sha `57a6e343…` / 9 断言 0 FAIL）；'
'R14 **§2.200 = 6,684 B ⇒ floor 3,342**，CR 1081；GOAL **§1250**，CR 337；LEAD_LOCK **PX**，CR 137；看板 CR 0。C16_FLOORS 190 → **192**。\n\n'
'**自错（当场抓出，无一条进入结论）.** ① 字节扫 C7（`i+=2` 错位）得 4 条 / 2 张表；② 64KB 分块不重同步得 285 条 / 10 张零命中；'
'③ 单次连续 `disasm_lite` 在 `0x46F5A0` 停住，只覆盖 **11.12%**，会把 331 错报成 118；④ `chain()` 传错对象类型触发 TypeError 两次；'
'⑤ 把 `mov eax,[0x887680]` 的指令地址 0x410113 误读成装点地址；⑥ 正则把 capstone 小偏移写成 `0x +`（实际十进制）致假 FAIL 两次。\n\n'
'**跨家族 · 未取得.** 执行员 **#477**（hy4，18 回合、4.25 分 / 预算 8 分）15/15 PASS，「+0 无初值写入」成立，但其「线性 118」被主会话复算推翻（真值 331，'
'且 331 里 271 个 ecx 来路无法用 64 B 前向窗口判定）；执行员 **#478**（hy4，61 回合 `error_max_turns`）用 `d0` 判主/子表（得 1214/0），L=0 全链作废；'
'审计员 **#479**（deepseek，21 回合 `error_max_turns`，`[OVERTIME: 8.73\' vs 8.0\']`）被砍前已写出 16,200 B 产物，六问三反控全部完成且与主会话**逐值一致**，'
'并额外指出「21 张 >64 槽表头全在 L 内、贡献 L 槽数 5,607 中的 3,910（69.7%）」。未取得：① 实现语义名；② CRC 初值来源；③ 0x6E8000 覆写的语义动机；'
'④ 三个 BSS 全局含义；⑤ `ncb` 最大 = 最外层 的编译器依据；⑥ F23/F35 grade；⑦ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑧ 86.19% 原值不可重算；'
'⑨ C7 三死分支各 0 行；⑩ C11 十二个永不 FAIL id 未动。\n')
nb3=(raw3.decode('utf-8')+SB).encode('utf-8')
ck('B1 新看板 CR 保持 0',nb3.count(b'\r')==0,nb3.count(b'\r'))
ck('B2 新看板行数 <= 300',nb3.count(b'\n')+1<=300,nb3.count(b'\n')+1)
ck('B3 第 195 轮标题唯一',nb3.count('## 🟢 R17 第 195 轮'.encode())==1,nb3.count('## 🟢 R17 第 195 轮'.encode()))

# ---------- C16 钉入 ----------
P4=os.path.join(T,'check_disc.py'); cd=rd(P4).decode('utf-8')
ck('C0 旧 C16_FLOORS_SHA256 存在',bool(re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'",cd,re.M)))
m=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',cd,re.S)
body=m.group(1)
ents=re.findall(r'(\d+):\s*(\d+)',body)
ck('C1 旧表 190 条 / 无 199 / 无 200',len(ents)==190 and 199 not in dict((int(a),int(b)) for a,b in ents) and 200 not in dict((int(a),int(b)) for a,b in ents),(len(ents),))
# 用旧表重算 sha 命中旧常量（硬闸）
norm='\n'.join('%d:%d'%(int(a),int(b)) for a,b in ents)
oldsha=re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'",cd,re.M).group(1)
ck('C2 旧表规范化串 sha 命中旧常量（硬闸）',sha(norm.encode())==oldsha,(sha(norm.encode())[:16],oldsha[:16]))
# §2.199 字节数实测
r14=rd(os.path.join(T,'R14_COMMON.md')).decode('utf-8')
i199=r14.index('## 2.199 R194')
i200=r14.index('## 2.200 R195')
L199=len(r14[i199:i200].encode('utf-8'))-2   # 去掉分隔的两个换行
ck('C3 §2.199 实测字节',L199>0,L199)
F199=L199//2
newbody=body+'\n    199: %d,\n    200: %d,'%(F199,F200)
cd2=cd.replace('C16_FLOORS = {\n'+body+'\n}','C16_FLOORS = {\n'+newbody+'\n}',1)
ents2=re.findall(r'(\d+):\s*(\d+)',newbody)
D2=dict((int(a),int(b)) for a,b in ents2)
ck('C4 新表 192 条 / 199 与 200 都已钉入 / 200==3342',len(ents2)==192 and 199 in D2 and D2.get(200)==3342,(len(ents2),D2.get(199),D2.get(200)))
norm2='\n'.join('%d:%d'%(int(a),int(b)) for a,b in ents2)
cd2=re.sub(r"^C16_FLOORS_SHA256 = '[0-9a-f]{64}'","C16_FLOORS_SHA256 = '%s'"%sha(norm2.encode()),cd2,flags=re.M)
ck('C5 新 sha 已换',sha(norm2.encode())!=oldsha,(sha(norm2.encode())[:16],))
if fails:
    print('ABORT before writes: %d FAIL'%len(fails)); sys.exit(1)
for p,b in ((P,nb),(P2,nb2),(P3,nb3)):
    wr(p,b)
wr(P4,cd2.encode('utf-8'))
ck('G3 回读 GOAL 一致',rd(P)==nb and rd(P).count(b'\r')==337)
ck('K3 回读 LOCK 一致',rd(P2)==nb2 and rd(P2).count(b'\r')==137)
ck('B4 回读看板一致',rd(P3)==nb3 and rd(P3).count(b'\r')==0 and rd(P3).count(b'\n')+1<=300)
ck('C6 回读 check_disc 一致',rd(P4)==cd2.encode('utf-8'))
print('GOAL %d -> %d B (CR %d)'%(len(raw),len(nb),nb.count(b'\r')))
print('LOCK %d -> %d B (CR %d)'%(len(raw2),len(nb2),nb2.count(b'\r')))
print('BOARD %d -> %d B (CR %d, %d 行)'%(len(raw3),len(nb3),nb3.count(b'\r'),nb3.count(b'\n')+1))
print('C16 190 -> 192 ; §2.199 floor=%d ; §2.200 floor=%d ; sha %s'%(F199,F200,sha(norm2.encode())[:16]))
print('FAILS=%d'%len(fails))
