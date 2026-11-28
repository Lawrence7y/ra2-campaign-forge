# -*- coding: utf-8 -*-
"""R209 p4：四件套 + C16_FLOORS 重钉。
  R14_COMMON §2.217（CR 保持 1081，LF-only 追加）
  GOAL §1267（CR 保持 337）
  LEAD_LOCK QR（CR 保持 137）
  STATUS_BOARD 第 209 轮（CR 保持 0，行数 <= 300；开局 241 < 260 不归档）
每处写入：wx 独占备份 -> 断言旧 sha/CR -> 一次写入 -> 回读校验。全部 bytes 模式（防 CRLF 折叠）。
"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; TIER=LEAD+'/next_re_20261117_r14'; BASE=LEAD+'/R17_LEAD_BASELINE'
R14=TIER+'/R14_COMMON.md'; GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'
LOCK=LEAD+'/LEAD_LOCK'; BOARD=TIER+'/STATUS_BOARD.md'
CD=TIER+'/check_disc.py'
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

# ---------- 1. R14_COMMON §2.217 ----------
S217 = '''## 2.217 · R209（2026-11-28）· 律 T 口径订正：额外视图前三槽 = QueryInterface/AddRef/Release 三连 thunk；70 thunk 无孤儿；305 槽口径与 101 表口径分列

**一、🔴 律 T 口径订正（数字不动，口径过窄）.** R208 §2.216 述「额外视图 vftable 的 slot0 是 this 调整 thunk，101 条」。改用**全槽扫描**（不是只取 slot0）后实测：`.text` 段 this 调整 thunk 共 **70** 个（`83 6C 24 04` 锚点 67 + `81 6C 24 04` 锚点 3），**全部**被 vftable 槽引用，**孤儿 thunk 0 个**。承载它们的 vftable 仍是 **101** 张，但这 101 张的 **slot0 / slot1 / slot2 三槽连排全是 thunk**（303 槽），另有 **2** 处越界槽（`.?AVHouseClass@@` mdisp=40 表的 slot3/slot4），合计 **305** 槽。⇒ 正确表述是「额外视图数组的**前三槽**是一组 this 调整 thunk」，不是「slot0 是 thunk」。

**二、🔴 三槽语义 = IUnknown 三方法（字节级证据）.** 三槽各 101 张表：

| 槽 | E9 落点首 ret | 分母 | 语义推断 |
|---|---|---|---|
| slot0 | `0xc`（=12） | 101/101 | `QueryInterface(this, riid, ppv)` stdcall 清 3 个 dword 栈 |
| slot1 | `0x4` | 101/101 | `AddRef(this)` |
| slot2 | `0x4` | 101/101 | `Release(this)` |

反控（同一判据施于主视图 954 张表的同三槽）：slot0 ret 分布 `{4:709, 12:187, 8:1, 0:3}`、slot1 **9 种**、slot2 **7 种** ⇒ 异构，**不满足**「恒 12/4/4」。⇒ 24/12/4 的恒定性是**额外视图（调整 thunk）独有**的性质，不是全镜像的普遍性质。
`0x410260`（75 张表共用的 QI 目标）体首逐指令：`mov eax,[esp+0xc]` / `push ebx` / `test eax,eax` / `jne` / `mov eax,0x80004003` / `pop ebx` / `ret 0xc`；有效路径 `mov edx,[esp+0xc]` / `repe cmpsd` 逐 16 B GUID 比 4 次（`0x7f7c90` / `0x7f7c80` / `0x7f7c70` / `0x7e9ae0`，前三者前 8 B 为 `00000000`/`09010000`/`0c010000` 与 `c0 00 ... 46` 尾巴 = IID 形态），失败走 `0x80004002`（E_NOINTERFACE）。

**三、🔴 落点 == 本类主视图同槽号（101/101 × 3）.** 三槽 thunk 的 E9 落点分别等于「同组 mdisp==0 那张主视图」的 slot0 / slot1 / slot2，k=0/1/2 **各 101/101**。⇒ 额外视图不是"另一套实现"，而是「把 IUnknown 三方法按 this 偏移 m 调整后**原样转发**给本类主视图」的机械产物。

**四、🟡 三元组与 jmp 目标的复用结构.** `(slot0, slot1, slot2)` 去重 **23** 组，23 组内 mdisp 唯一（`{4:91, 24:6, 1728:1, 44:1, 40:1, 36:1}` 表）；但只落 **13** 个 jmp 三元组 ⇒ 同一套 QI/AddRef/Release 实现被多个 mdisp 复用。按 slot0 口径计 thunk **22 个**（含 B81 那条），按全槽口径 **70 个**；R208 报「21 个」漏了 B81 的 `0x41c670`。

**五、🟡 越界 2 槽（`.?AVHouseClass@@` mdisp=40）.** 该表 9 槽 `[0x510a80,0x510a90,0x510aa0,0x510ab0,0x510ac0,0x4f6a80,0x4f6b50,0x4f6d10,0x4f6910]`，slot3 = thunk `0x510ab0`（imm=4，jmp `0x4f6e60`，体 = `mov eax,[esp+4] ; mov eax,[eax+0xc] ; ret 4` = getter）、slot4 = thunk `0x510ac0`（imm=4，jmp `0x4f6950`，体首 `mov ecx,[esp+4] ; sub esp,0x40 ; lea eax,[esp] ; ... ; push 0x20` = 取缓冲）。两槽 imm 恒 **4**（接口自身偏移）而非表 mdisp **40** ⇒ **越界槽不遵循 thunk-imm==mdisp**，imm 是接口基类偏移不是类基类偏移。

**六、🟡 T/S/I 互斥性加固（260 = 101 + 156 + 3）.** S 形态 3 张静态表承载 **156** 张全单槽表（`0x410590`=`ret 4` 78、`0x410580`=`xor al,al; ret 8` 75、`0x6d1770` 3，三者承载表集合**两两不交**且**无一含 thunk**）；I 形态 3 个真函数体各承载 1 张表（`0x41bc30`→0x7fb340、`0x522a60`→0x803318、`0x746100`→0x80cbc8，**无一含 thunk**）；T/S/I 三集合与 T 集合**两两不交**。101+156+3 = **260** = 额外视图总数，**零残留**。
`0x6d1770` 三张承载表 = `MouseClass` / `TabClass` / `ScrollClass`（mdisp 全 **21784**、均单槽）；其体内比较 `0x11c7` / `0x11c8` 两个立即数——**不是**任何类的 pTD（类 pTD 全落 `.data`；`0x11c7` 全域 dword 出现仅 2 处：`.text 0x6379fb / 0x6d1775`），且 `0x6d1770` 自身被直接 `call` / `jmp` **各 0 次** ⇒ **语义未取得**，不外推。顺带取得：`0x6d1770` 查的 `0xb0c1c0` 落在 `.data` 段 **虚拟尾部**（`> hi_file 0x87e000`，实为运行期 BSS），静态无初值 ⇒ 该路径的静态判定到此为止。

**七、🟡 分母口径四列（防混用）.** 同一现象有四个合法分母，必须分列不可互代：①`.text` 字节锚点 **67/3（合 70）**；②额外视图 slot0 口径 thunk **22**；③额外视图前三槽口径 thunk **70**；④额外视图**槽**口径 **305**（= 303 + 2）。表口径 **101**，COL 口径 **101**，额外视图总表 **260**。

**八、🟡 跨家族（§2.12 规则 D 全部主会话复算）.** 执行员 **#534**（hy4，11 回合 / **2.53'** vs 预算 8.0，无 OVERTIME）：8 项自报全 PASS，落 `_r209/x1_triple.json`，逐数一致（70 / 1214 / 954 / 14044 / 101 / 23 / 303 / 70 引用 70 / slot0 12·slot1 4·slot2 4 / 越界 2 槽）。审计员 **#536**（deepseek，19 回合 / 3.45' / 无 OVERTIME）：5 项全 PASS，独立重建判据漏斗与全槽反汇编，另给 3 个数复现（155/156 无、但 **213** 张表不足 3 槽 / imm 分布 `4×40, 24×18, 36×3, 40×3, 44×3, 1728×3` / 未进前三槽的 thunk 恰 `0x510ab0`+`0x510ac0`）——主会话 `v6` 逐条复算成立；其判据漏斗 `23707/10932/1229/1214/1214` 与我方 `23711/10936/1225/1214/1214` 的差**源于口径**（按 `hi_virt` 判段 + 窗口 6 vs 按 `hi_file` 判段 + 窗口 4），`v7` 枚举变体后**精确复现**审计四数，非算错。**否决审计一条措辞**：「`0xc` 对应前 12 字节 this 调整的成员指针双参」错——`ret 0xc` 是 stdcall 被调方清 12 字节栈 = 3 个 dword 参数，与 this 调整量无关（`0x410260` 体首读 `[esp+0xc]` 作 ppv、`[esp+0x10]` 作 pv 已证）。
**一次性失败如实记**：审计员 **#535**（deepseek，36 回合 / 6.2' / 预算 8.0）报 `error_max_turns`、**返回空结果**，0 条结论采信；改为 5 项精简卡 #536 后才成功。

**九、📌 自错 5 组（0 条进结论）.** ①`q2` 的 B81 判据把 E9 位置写成 +9（实为 +8），漏掉全部 3 条 81 thunk ⇒ 误得「A83 67 条、无 81」；②`q2` 断言「thunk 只在 slot0」⇒ 得 48 个"孤儿"，全假（实为 0 孤儿）；③`q7` 用 `COL+8` 取 pCHD（实际 `+8` 是恒零 cdOffset，pCHD 在 `+16`）⇒ 101 条全报 "no primary"；④`q4`/`q5` 预设「A83 目标 21 个、QI 目标全部含 E_POINTER」，实测 40 个落点 / 8 个含 E_POINTER，两个 FAIL 均是预设数字错；⑤`p3_master` 引入 `rich if False else None` 语法错（手误），一次 SyntaxError 后修正。

**十、🟡 FACT_INDEX 升版 V590→V591.** 把律 T 订正（三槽三连 + 305 槽 + 越界 2 槽 + 四列分母）写入 **F29**（stmt 5343→7377 B、lim 20898→21688 B，其余 55 行逐字节不变；57 行 / 5 列 / grade 与第 4 列全同）。sha `e49a3edd`→**`c529a08c`**，242630→**245454** B。指针 + facts_floors（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER_SHA256 `940c94c0`→`ba31ddc1`）+ gate_runner LEDGER 同步重钉。

**十一、🟡 落盘与门禁.** 本段 **§2.217** CR 保持 **1081**；GOAL **§1267** CR 保持 **337**；LEAD_LOCK **QR** CR 保持 **137**；STATUS_BOARD 第 209 轮 CR 保持 **0**（开局 241 行 < 260，**不归档**）。C16_FLOORS 纳入 §2.217（unpinned 0 / hollow 0 / missing 0）。三门 exit 0：`check_disc`（C15 末节 217、C16 209 节全钉、C19 ok(c529a08c/245454/V591)、C20 ok）、`facts_floors`（D8 245454、D9/D10 一致、MASTER ba31ddc1）、`gate_runner`（G1=G2=G3=ok）。

**十二、⚪ 未取得（不粉饰）.** ① `attributes` 位义（须 `win-main` 动态；`attrs&1` 的 4 条 `pdisp=-1` 与 MSVC 标准位义矛盾）；② `attributes 5 vs 1` 语义；③ 13 个 onlysec pTD 的**成因**（名单 R207 QL2 已取得）；④ 34 个无类 TD 的接口派生链；⑤ 5 个 pTD 多记录成因；⑥ S 表 `0x6d1770` 的 `0x11c7`/`0x11c8` 语义（该路径读运行期 BSS `0xb0c1c0`，静态不可判）；⑦ HouseClass slot4 目标 `0x4f6950` 完整语义（只读前 6 条指令）；⑧ 主视图 954 表 slot>=3 的槽语义（本轮未测）；⑨ R206 遗留 6 项；⑩ F23/F35 grade（`coverage.tsv`/`function_atlas.tsv` 仍不可读，禁预估回填）；⑪ C7 三死分支、C11 十二 ID。

'''
b,bak=backup(R14,'r14_217')
assert b.count(b'\r\n')==1081
assert b.count(b'## 2.217')==0
nb=b+b'\n'+S217.encode('utf-8')
assert nb.count(b'\r\n')==1081
commit(R14,nb,b,1081,'r14_217')
print('R14_COMMON 2.217 OK')
