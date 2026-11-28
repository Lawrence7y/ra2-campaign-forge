# -*- coding: utf-8 -*-
"""R209 p5：GOAL §1267 / LEAD_LOCK QR / STATUS_BOARD 第 209 轮 + C16_FLOORS 重钉。
"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; TIER=LEAD+'/next_re_20261117_r14'; BASE=LEAD+'/R17_LEAD_BASELINE'
GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'; LOCK=LEAD+'/LEAD_LOCK'
BOARD=TIER+'/STATUS_BOARD.md'; CD=TIER+'/check_disc.py'
def backup(path,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r209_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    return b,bak
def commit(path,nb,ob,exp_cr,tag):
    assert nb.count(b'\r\n')==exp_cr,(tag,nb.count(b'\r\n'),exp_cr)
    tmp=path+'.r209tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert open(path,'rb').read()==nb
    print('OK %-24s %d -> %d B  CR %d'%(os.path.basename(path),len(ob),len(nb),nb.count(b'\r\n')))

# ---------- GOAL §1267 ----------
S = '''## §1267 · R209（2026-11-28）· 律 T 订正：额外视图前三槽 = QI/AddRef/Release 三连 thunk（101 表 / 303 槽 + 2 越界）；70 thunk 零孤儿；T/S/I 260 零残留

**订正（数字全不动，口径从「slot0 一条」扩到「前三槽三连」）.**
1. 🔴 `.text` this 调整 thunk 实测 **70** 个（`83 6C 24 04` 67 + `81 6C 24 04` 3），**全部被 vftable 引用，孤儿 0**。承载表仍 **101** 张，但其 **slot0/slot1/slot2 三槽连排全为 thunk**（303 槽）+ **2** 处越界槽（HouseClass mdisp=40 的 slot3/slot4）= **305 槽**。R208 的「slot0 是 thunk」是过窄口径。
2. 🔴 **三槽语义 = IUnknown 三方法**：slot0 落点首 ret **0xc**（101/101）、slot1 **0x4**（101/101）、slot2 **0x4**（101/101）。反控：主视图 954 表同三槽 ret 分布 slot0 `{4:709,12:187,8:1,0:3}`、slot1 9 种、slot2 7 种，**异构** ⇒ 恒定性为额外视图独有。`0x410260`（75 表共用 QI）体首 `mov eax,[esp+0xc] / test / mov eax,0x80004003 / ret 0xc`，有效路径 `repe cmpsd` 比 4 个 GUID（0x7f7c90/0x7f7c80/0x7f7c70/0x7e9ae0），失败 `0x80004002`。
3. 🔴 **落点 == 本类主视图同槽号**，k=0/1/2 各 **101/101** ⇒ 额外视图是「按 this 偏移转发给主视图」的机械产物，不是另一套实现。
4. 🟡 `(slot0,slot1,slot2)` 去重 **23** 组、组内 mdisp 唯一；只落 **13** 个 jmp 三元组 ⇒ 多 mdisp 复用同一套实现。slot0 口径 thunk **22**（R208 报 21 漏了 B81 的 0x41c670）。
5. 🟡 **越界 2 槽**：HouseClass 9 槽表 slot3=`0x510ab0`（imm=4 → 0x4f6e60 = `mov eax,[esp+4]; mov eax,[eax+0xc]; ret 4` getter）、slot4=`0x510ac0`（imm=4 → 0x4f6950 取缓冲）；imm 恒 4 ≠ 表 mdisp 40 ⇒ **越界槽 imm 是接口偏移不是类偏移**。
6. 🟡 **T/S/I 互斥**：S 156 表（0x410590 78 / 0x410580 75 / 0x6d1770 3，全单槽、三集合两两不交、无一含 thunk）、I 3 表（0x41bc30/0x522a60/0x746100，各 1 表、无一含 thunk），与 T 101 表**两两不交**，101+156+3=**260** 零残留。`0x6d1770` 三表 = MouseClass/TabClass/ScrollClass（mdisp 全 21784）；其比较的 `0x11c7`/`0x11c8` **不是** pTD（pTD 全落 .data），该函数直接 call/jmp 各 0 次，查的 `0xb0c1c0` 落 .data 虚拟尾部（运行期 BSS）⇒ 语义未取得。
7. 🟡 **四列分母**（禁互代）：①锚点 67/3（70）；②slot0 口径 thunk 22；③前三槽口径 thunk 70；④槽口径 305；表/COL 口径 101；额外视图总表 260。
8. 🟡 **跨家族**：#534（hy4，11 回合 / 2.53'，无 OVERTIME）8/8 PASS；#536（deepseek，19 回合 / 3.45'）5/5 PASS 并给 3 个新数（213 张表 <3 槽 / imm 分布 / 未进前三槽的 2 个 thunk）经 `v6` 复算成立；其漏斗 23707/10932/1229 与我方 23711/10936/1225 的差是**口径**（hi_virt+窗口6 vs hi_file+窗口4），`v7` 精确复现其四数。**否决其一条措辞**：「ret 0xc = 前 12 字节 this 调整」错，是 stdcall 清 3 个 dword 参数。**#535 一次性失败如实记**：36 回合 `error_max_turns`、返回空，0 条采信。
9. 🟡 **FACT_INDEX V591**：F29 stmt 5343→7377 B、lim 20898→21688 B（其余 55 行逐字节不变），sha `e49a3edd`→`c529a08c`、242630→**245454** B；指针 + facts_floors（MASTER `940c94c0`→`ba31ddc1`）+ gate_runner LEDGER 同步重钉。三门 exit 0。
10. 📌 **自错 5 组**（B81 E9 位置 +9 应 +8 / 断言 thunk 只在 slot0 得 48 假孤儿 / 用 COL+8 取 pCHD 应 +16 / 预设 21 个落点与全含 E_POINTER 两个数错 / `rich if False` 语法手误），0 条进结论。
11. ⚪ **未取得**：`attributes` 位义（动态）、`attributes 5 vs 1`、13 个 onlysec pTD 成因、34 个无类 TD 派生链、5 个 pTD 多记录成因、`0x11c7` 语义（运行期 BSS）、HouseClass slot4 完整语义、主视图 slot>=3 槽语义、R206 遗留 6 项、F23/F35 grade（两 tsv 不可读，禁预估）、C7 三死分支、C11 十二 ID。

'''
b,_=backup(GOAL,'goal_1267')
assert b.count(b'\r\n')==337 and b.count('## §1267'.encode())==0
nb=b+b'\n'+S.encode('utf-8')
assert nb.count(b'\r\n')==337
commit(GOAL,nb,b,337,'goal_1267')

# ---------- LEAD_LOCK QR ----------
S = '''## QR · R209（2026-11-28）· 律 T 从「slot0」扩为「前三槽」：101 表 × 3 槽 = IUnknown 三连 thunk（303 槽）+ 2 越界；70 thunk 零孤儿；T/S/I = 260 零残留；V591

**QR1. 🔴 律 T 口径订正（数字不动）.** R208 述「101 条额外视图 slot0 是 this 调整 thunk」。全槽扫描后：`.text` thunk 共 **70**（83 锚点 67 + 81 锚点 3），**全部被引用、孤儿 0**；101 张表的 **slot0/slot1/slot2 三槽全是 thunk**（303），加 **2** 越界槽（HouseClass mdisp=40 的 slot3/4）共 **305** 槽。⇒ 是「前三槽一组 thunk」，不是「slot0 一条」。

**QR2. 🔴 三槽 = QI/AddRef/Release.** slot0 落点首 ret **0xc** 101/101、slot1 **0x4** 101/101、slot2 **0x4** 101/101；反控主视图 954 表同三槽为 `{4:709,12:187,8:1,0:3}` / 9 种 / 7 种，异构 ⇒ 恒定性为额外视图独有。`0x410260`（75 表共用 QI）体首 `mov eax,[esp+0xc]` / `test` / `mov eax,0x80004003` / `ret 0xc`；有效路径 4 次 `repe cmpsd` 比 GUID `0x7f7c90`/`0x7f7c80`/`0x7f7c70`/`0x7e9ae0`，失败 `0x80004002`。

**QR3. 🔴 落点 == 本类主视图同槽.** k=0/1/2 各 **101/101**。⇒ 额外视图不另实现，按 this 偏移 m 调整后**转发**给本类主视图。

**QR4. 🟡 复用结构.** `(s0,s1,s2)` 去重 **23** 组（组内 mdisp 唯一，分布 `{4:91,24:6,1728:1,44:1,40:1,36:1}`），只落 **13** 个 jmp 三元组。slot0 口径 thunk **22**（R208「21」漏 B81 `0x41c670`）；全槽口径 70。四个合法分母（锚点 67/3、slot0 22、三槽 70、槽 305）**禁互代**。

**QR5. 🟡 越界 2 槽.** HouseClass mdisp=40 表 9 槽，slot3 `0x510ab0`（imm=4 → `0x4f6e60`：`mov eax,[esp+4] ; mov eax,[eax+0xc] ; ret 4`）、slot4 `0x510ac0`（imm=4 → `0x4f6950`：`mov ecx,[esp+4] ; sub esp,0x40 ; ... ; push 0x20`）。imm 恒 4 ≠ mdisp 40 ⇒ 越界槽 imm 是**接口偏移**。

**QR6. 🟡 T/S/I = 260 零残留.** S 156（0x410590 78 / 0x410580 75 / 0x6d1770 3，全单槽、三集合不交、无一含 thunk）+ I 3（0x41bc30/0x522a60/0x746100 各 1 表、无一含 thunk）+ T 101，三集合两两不交，合计 260。`0x6d1770` 三表 = MouseClass/TabClass/ScrollClass（mdisp 21784）；其 `0x11c7`/`0x11c8` 非 pTD（pTD 全 .data），直接被 call/jmp 各 0 次，查的 `0xb0c1c0` 落 .data 虚拟尾部（运行期 BSS）⇒ 语义**未取得**。

**QR7. 🟡 跨家族（§2.12 规则 D 全复算）.** #534（hy4，11 回合 / 2.53' / 无 OVERTIME）8/8 PASS，落 `_r209/x1_triple.json`。#536（deepseek，19 回合 / 3.45' / 无 OVERTIME）5/5 PASS，另给 3 数（213 张表 <3 槽、imm 分布 `4×40/24×18/36×3/40×3/44×3/1728×3`、未进前三槽的 thunk 恰 0x510ab0+0x510ac0）经 `v6` 成立；其漏斗 23707/10932/1229 与我方 23711/10936/1225 之差是**口径**（hi_virt+窗口 6 vs hi_file+窗口 4），`v7` 精确复现其四数。**否决**其「ret 0xc = 前 12 字节 this 调整双参」措辞（实为 stdcall 清 3 dword 参数）。**#535 一次性失败如实记**：36 回合 `error_max_turns` 返回空，0 条采信。

**QR8. 🟡 落盘与门禁.** R14_COMMON **§2.217** CR 保持 **1081**；GOAL **§1267** CR 保持 **337**；本段 **QR** CR 保持 **137**；STATUS_BOARD 第 209 轮 CR 保持 **0**（开局 241 行 < 260，不归档）。C16_FLOORS 纳入 §2.217（unpinned 0 / hollow 0 / missing 0）。**FACT_INDEX V590→V591**：F29 stmt 5343→7377 B、lim 20898→21688 B（其余 55 行逐字节不变），sha `e49a3edd`→**`c529a08c`**、242630→**245454** B；指针 + facts_floors（D0/D8/D9/D10，MASTER `940c94c0`→`ba31ddc1`）+ gate_runner LEDGER 同步重钉。三门 exit 0：C19 ok(c529a08c/245454/V591)、C20 ok、G1=G2=G3=ok。

**QR9. 📌 自错 5 组（0 条进结论）.** ①`q2` B81 判据 E9 位置写 +9（应 +8）⇒ 漏全部 81 thunk；②`q2` 断言「thunk 只在 slot0」⇒ 得 48 个假孤儿（实 0）；③`q7` 用 `COL+8` 取 pCHD（`+8` 是恒零 cdOffset，pCHD 在 `+16`）⇒ 101 条全报 no primary；④`q4`/`q5` 预设「落点 21 个」与「全部含 E_POINTER」两个数错（实测 40 / 8）；⑤`p3_master` 手误 `rich if False else None` 一次 SyntaxError。

**QR10. ⚪ 未取得.** ①`attributes` 位义（须 win-main 动态；attrs&1 的 4 条 pdisp=-1 与标准矛盾）；②`attributes 5 vs 1`；③13 个 onlysec pTD 成因；④34 个无类 TD 派生链；⑤5 个 pTD 多记录成因；⑥`0x11c7`/`0x11c8` 语义（运行期 BSS）；⑦HouseClass slot4 全语义；⑧主视图 954 表 slot>=3 槽语义；⑨R206 遗留 6 项；⑩F23/F35 grade（两 tsv 不可读，禁预估回填）；⑪C7 三死分支、C11 十二 ID。

'''
b,_=backup(LOCK,'lock_qr')
assert b.count(b'\r\n')==137 and b.count('## QR ·'.encode())==0
nb=b+b'\n'+S.encode('utf-8')
assert nb.count(b'\r\n')==137
commit(LOCK,nb,b,137,'lock_qr')

# ---------- STATUS_BOARD 第 209 轮 ----------
SB = '''## 🟢 R17 第 209 轮（2026-11-28）· 律 T 口径订正：额外视图**前三槽** = QI/AddRef/Release 三连 thunk（101 表 / 303 槽 + 2 越界）；70 thunk 零孤儿；T/S/I = 260 零残留

**取得（1 订正 + 4 新事实）.** ①🔴 **律 T 口径订正**：R208 述「额外视图 slot0 是 this 调整 thunk，101 条」——数字全对但**口径过窄**。改用全槽扫描后实测 `.text` 段 this 调整 thunk 共 **70** 个（`83 6C 24 04` 锚点 67 + `81 6C 24 04` 锚点 3），**全部被 vftable 槽引用，孤儿 0 个**；承载表仍 **101** 张，但其 **slot0/slot1/slot2 三槽连排全为 thunk**（303 槽），另有 **2** 处越界槽（`HouseClass` mdisp=40 的 slot3/slot4），合计 **305** 槽。②🔴 **三槽语义 = IUnknown 三方法**：slot0 落点首 `ret` 恒 **0xc**（101/101）、slot1 恒 **0x4**（101/101）、slot2 恒 **0x4**（101/101）；反控主视图 954 表同三槽 ret 分布 `{4:709,12:187,8:1,0:3}` / 9 种 / 7 种，**异构** ⇒ 恒定性为额外视图独有。`0x410260`（75 表共用 QI）体首 `mov eax,[esp+0xc] / test eax,eax / jne / mov eax,0x80004003 / pop ebx / ret 0xc`，有效路径 `repe cmpsd` 比 4 个 GUID（`0x7f7c90`/`0x7f7c80`/`0x7f7c70`/`0x7e9ae0`），失败 `0x80004002`。③🔴 **落点 == 本类主视图同槽号**，k=0/1/2 **各 101/101** ⇒ 额外视图按 this 偏移转发，不另实现。④🟡 **复用结构**：`(s0,s1,s2)` 去重 **23** 组（组内 mdisp 唯一），只落 **13** 个 jmp 三元组；slot0 口径 thunk **22**（R208「21」漏 B81 `0x41c670`）。⑤🟡 **越界 2 槽**：HouseClass slot3 `0x510ab0`（imm=4 → `0x4f6e60`：`mov eax,[esp+4]; mov eax,[eax+0xc]; ret 4`）、slot4 `0x510ac0`（imm=4 → `0x4f6950` 取缓冲），imm 恒 4 ≠ 表 mdisp 40 ⇒ **越界槽 imm 是接口偏移**。⑥🟡 **T/S/I 互斥 = 260 零残留**：S 156（`0x410590` 78 / `0x410580` 75 / `0x6d1770` 3，全单槽、三集合不交、无一含 thunk）+ I 3（`0x41bc30`/`0x522a60`/`0x746100` 各 1 表）+ T 101，两两不交。`0x6d1770` 三表 = MouseClass/TabClass/ScrollClass（mdisp 21784），其 `0x11c7`/`0x11c8` **非 pTD**（pTD 全 .data），直接被 call/jmp 各 0 次，查的 `0xb0c1c0` 落 .data 虚拟尾部（运行期 BSS）⇒ **语义未取得**。

**跨家族（§2.12 规则 D 全复算）.** #534（hy4，11 回合 / **2.53'** vs 预算 8.0，无 OVERTIME）8/8 PASS，落 `_r209/x1_triple.json`，逐数一致。#536（deepseek，19 回合 / 3.45'，无 OVERTIME）5/5 PASS，另给 3 个数（**213** 张表不足 3 槽、imm 分布 `4×40/24×18/36×3/40×3/44×3/1728×3`、未进前三槽的 thunk 恰 `0x510ab0`+`0x510ac0`）经 `v6` 逐条复算成立；其判据漏斗 `23707/10932/1229/1214/1214` 与我方 `23711/10936/1225/1214/1214` 之差**是口径不是错**（`hi_virt` 判段 + 窗口 6 vs `hi_file` + 窗口 4），`v7` 枚举变体后**精确复现**其四数。**否决其一条措辞**：「`0xc` = 前 12 字节 this 调整的成员指针双参」错——`ret 0xc` 是 stdcall 清 3 个 dword 参数。**#535 一次性失败如实记**：36 回合 / 6.2' 报 `error_max_turns`、返回空结果，0 条结论采信，改 5 项精简卡 #536 后才成功。

**自错 5 组（0 条进结论）.** ①`q2` B81 判据 E9 位置写 +9（应 +8）⇒ 漏全部 3 条 81 thunk；②`q2` 断言「thunk 只在 slot0」⇒ 得 48 个假孤儿（实 0）；③`q7` 用 `COL+8` 取 pCHD（`+8` 是恒零 `cdOffset`，`pCHD` 在 `+16`）⇒ 101 条全报 no primary；④`q4`/`q5` 预设「落点 21 个」与「QI 目标全含 E_POINTER」两个数错（实测 40 / 8）；⑤`p3_master` 手误 `rich if False else None` 一次 SyntaxError。

**落盘与门禁.** R14_COMMON **§2.217** CR 保持 **1081**；GOAL **§1267** CR 保持 **337**；LEAD_LOCK **QR** CR 保持 **137**；本段第 209 轮 CR 保持 **0**（开局 241 行 < 260，**不归档**）。**FACT_INDEX V590→V591**：F29 stmt 5343→7377 B、lim 20898→21688 B（其余 55 行逐字节不变；57 行 / 5 列 / grade 与第 4 列全同），sha `e49a3edd`→`c529a08c`、242630→**245454** B；指针 + facts_floors（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER `940c94c0`→`ba31ddc1`）+ gate_runner LEDGER 同步重钉。C16_FLOORS 纳入 §2.217（unpinned 0 / hollow 0 / missing 0）。三门 exit 0：`check_disc`（C15 末节 217、C16 209 节全钉、C19 ok(c529a08c/245454/V591)、C20 ok）、`facts_floors`（D8 245454、D9/D10 一致）、`gate_runner`（G1=G2=G3=ok）。五项 CR 不变量全绿，无孤儿进程。

**⚪ 未取得.** ①`attributes` 位义（须 win-main 动态）；②`attributes 5 vs 1`；③13 个 onlysec pTD 成因；④34 个无类 TD 派生链；⑤5 个 pTD 多记录成因；⑥`0x11c7`/`0x11c8` 语义（运行期 BSS）；⑦HouseClass slot4 全语义；⑧主视图 954 表 slot>=3 槽语义；⑨R206 遗留 6 项；⑩F23/F35 grade（两 tsv 不可读，禁预估回填）；⑪C7 三死分支、C11 十二 ID。

'''
b,_=backup(BOARD,'board_209')
assert b.count(b'\r\n')==0
n=b.count(b'\n')
print('BOARD 开局行数 =',n)
assert n<260, n
nb=b+(b'\n' if not b.endswith(b'\n') else b'')+SB.encode('utf-8')
assert nb.count(b'\r\n')==0
commit(BOARD,nb,b,0,'board_209')
print('BOARD 收口行数 =',nb.count(b'\n'))
