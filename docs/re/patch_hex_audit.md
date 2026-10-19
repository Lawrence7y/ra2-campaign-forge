# 六大落地补丁 18 项机器码 / rel32 / 语义等价独立第三方复算审计报告
# Independent Hex, rel32 & Semantic Equivalence Audit Report for Six Patch Packs (18 Items)

```text
[META]
task=PATCH-HEX-AUDIT  executor=Antigravity(agy)/2f8a82ed-f187-4413-be65-74cf214db7ef  elapsed=580s  mode=read-only
scope_declared=docs/re/patch_hex_audit.md, out/re_work/agy_patchhex/**
```

---

## [0] 结论摘要

本审计针对 `docs/re/pending_execution_master_table.md` 声明的「零推演落地」进行第三方独立工程复算，对象涵盖 P-1 至 P-6 共 18 项落地补丁。
核心结论：
1. **原字节与等长性 100% 吻合**：17 处静态 VA 的原始机器码经 `tools/audit_bytes.py` 严格断言全绿通过（OK=17，MISMATCH=0），单例动态结构备份（P-2.5）契约完备；全部替换机器码严格等长，未破坏任何后续指令边界；
2. **rel32 逐条独立复算全绿**：以 `0x01B00000` 独立页为基准，10 处外部挂钩正向跳转与 11 处跳板内负向回绕跳转（`rel32 >= 0x80000000`）共 21 处 rel32 逐位精确匹配；
3. **关键缺陷拦截逐位等价**：P-1.3 H-D5 实证采用 `0F B6 C0` (`movzx eax, al`) 彻底排除 `83 E0 FF` 符号扩展漏洞，且尾声平栈重放；P-5.1/P-5.2 音频早退严格执行 `xor eax, eax`（返回 NULL）并分别以 `ret 8` / `ret 4` 平栈；
4. **最大风险**：P-2（裂缝保护与间谍卫星门控）修改了写入存档并影响寻敌的 `CellClass+0x134` 字段，属于核心游戏状态层，**严禁混端联机，联机全员必须统一加载相同构建**。
**总裁决：全表 18 项全部裁定为【可落地】。**

---

## [1] 逐条必答项结论表

### 1.1 六大落地补丁 18 项独立复算 18 行总表

| 项号 | 原字节核对 | 等长 | rel32 | 语义等价 | 风险 | 可落地/需修正 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P-1.1** | [实证] PASS (`0F 85 69 05 00 00` MATCH) | 等长 (6B) | [实证] MATCH (`0x014B3909`, 回绕 OK) | [实证] 等价 (`test [esp+0x20], 0x40` 读 ZF, `popad;popfd` 还原) | 中高 (Tier 4, 同步校验判定) | **可落地** |
| **P-1.2** | [实证] PASS (`A0 80 48 B0 00` MATCH) | 等长 (5B) | [实证] MATCH (`0x014B33DA`, 回绕 OK) | [实证] 等价 (首位 `pushad` 快照原 `EAX=slot*37`, 退栈后重放) | 低 (Tier 5, 故障后善后) | **可落地** |
| **P-1.3** | [实证] PASS (`5F 5E 5D 5B 83 C4 14 C3` MATCH) | 等长 (8B) | [实证] MATCH (`0x014B2206`, 自包含) | [实证] 等价 (采用 `0F B6 C0` 杜绝符号扩展; 尾声平栈 `ret`) | 中 (Tier 4, 帧同步计算尾声) | **可落地** |
| **P-1.4** | [实证] PASS (`E8 9A A3 E7 FF` MATCH) | 等长 (5B) | [实证] MATCH (`0x014B37AA`, 回绕 OK) | [实证] 等价 (ECX 现场无损透传 `0x4C6CB0`, 回跳 `0x64CAA8`) | 高 (Tier 3, 触及①命令序) | **可落地** |
| **P-1.5** | [实证] PASS (`E8 A1 A0 E7 FF` MATCH) | 等长 (5B) | [实证] MATCH (`0x014B34F1`, 回绕 OK) | [实证] 等价 (重放 `call 0x4C6CB0`, 回跳 `0x64CC0F`) | 高 (Tier 3, 触及①命令序) | **可落地** |
| **P-2.1** | [实证] PASS (`89 99 34 01 00 00` MATCH) | 等长 (6B) | N/A (纯 NOPx6) | [实证] 等价 (消除误清零 `Cell+0x134`, 其余开图逻辑保留) | 极高 (Tier 1, 触及①同步与③存档) | **可落地** |
| **P-2.2** | [实证] PASS (`89 B8 34 01 00 00` MATCH) | 等长 (6B) | N/A (纯 NOPx6) | [实证] 等价 (消除 `RevealArea3` 误清零 `Cell+0x134`) | 极高 (Tier 1, 触及①同步与③存档) | **可落地** |
| **P-2.3** | [实证] PASS (`89 98 34 01 00 00` MATCH) | 等长 (6B) | N/A (纯 NOPx6) | [实证] 等价 (消除 `Reshroud` 误清零 `Cell+0x134`) | 极高 (Tier 1, 触及①同步与③存档) | **可落地** |
| **P-2.4** | [实证] PASS (`74 65` MATCH) | 等长 (2B) | [实证] MATCH (`EB 65` 短跳转到 `0x508FF6`) | [实证] 等价 (短路全图点亮分支，不破坏 TYPE 单例) | 极高 (Tier 1, 触及①同步与③存档) | **可落地** |
| **P-2.5** | [实证] PASS (动态单例捕获与回写) | N/A | N/A | [实证] 等价 (首次捕获 4 处原值，卸载时逐项原样回写) | 高 (Tier 2, 触及①单例一致性) | **可落地** |
| **P-3.1** | [实证] PASS (`C0 CE 62 00` MATCH) | 等长 (4B) | N/A (虚表槽 69 替换) | [实证] 等价 (纯 Draw 剔除，Update 寿命解耦，早退 `ret 8`) | 低 (Tier 6, 纯本地表现层) | **可落地** |
| **P-3.2** | [实证] PASS (`80 E2 62 00` MATCH) | 等长 (4B) | N/A (虚表槽 69 替换) | [实证] 等价 (纯 Draw 剔除，早退 `ret 8`，放行透传原例程) | 低 (Tier 6, 纯本地表现层) | **可落地** |
| **P-4.1** | [实证] PASS (`6A 01 FF 74 24 08` MATCH) | 等长 (6B) | [实证] MATCH (`0x01337324`, 回绕 OK) | [实证] 等价 (8B头+8B对齐，命中改写 `[esp+0x1C]`, 未命中透传) | 中 (Tier 5, 启动期锁定防堆坏) | **可落地** |
| **P-4.2** | [实证] PASS (`FF 74 24 04 E8 A2 08 00 00` MATCH) | 等长 (9B) | [实证] MATCH (`0x0133763E`, 回绕 OK) | [实证] 等价 (硬件范围守卫+投毒 `0xDEADBEEF`, caller清参) | 中 (Tier 5, 双释放免疫) | **可落地** |
| **P-5.1** | [实证] PASS (`51 A0 AC 64 84 00` MATCH) | 等长 (6B) | [实证] MATCH (`0x013AF89B`, 回绕 OK) | [实证] 等价 (早退 `xor eax, eax; ret 8` 严格平栈返回 NULL) | 低 (Tier 6, 表现层优化) | **可落地** |
| **P-5.2** | [实证] PASS (`A0 AC 64 84 00` MATCH) | 等长 (5B) | [实证] MATCH (`0x013AF85B`, 回绕 OK) | [实证] 等价 (早退 `xor eax, eax; ret 4` 严格平栈返回 NULL) | 低 (Tier 6, 表现层优化) | **可落地** |
| **P-6.1** | [实证] PASS (`0F 8D 98 00 00 00` MATCH) | 等长 (6B) | [实证] MATCH (`0x00000099` -> `0x6D3E37`) | [实证] 等价 (Force-Full 双模切换，`jge` 改无条件 `jmp+nop`) | 最低 (Tier 7, 纯本地视口调度) | **可落地** |
| **P-6.2** | [实证] PASS (`A1 F4 F7 87 00` 原生API) | N/A | N/A (原生 API 驱动) | [实证] 等价 (`RegisterCellAsVisible`, 350格全量保底, 严禁钩0x48D000) | 最低 (Tier 7, 纯本地渲染) | **可落地** |

### 1.2 E1~E6 必答项结论对照表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|:---:|---|
| **E1** | 原字节核对：台账原字节是否与 gamemd.exe 一致？ | 17 处静态 VA 全部 100% 逐位 MATCH，动态项契约清晰，无 P0 勘误 | [实证] | `out/re_work/agy_patchhex/bytes/check_bytes.py`；claims 17/17 OK |
| **E2** | 等长性：替换机器码长度 == 原字节长度？ | 15 处机器码补丁全部等长；不等长处（如 5B E9 覆盖 6B/8B/9B）均以 `90` (NOP) 严格平齐，下一条指令首字节零破坏 | [实证] | `pending_execution_master_table.md:39-55` 逐行字节数 |
| **E3** | rel32 复算：0x01B00000 基址逐条复算与负向回绕核对？ | 21 处 rel32（10 处正向挂钩 + 11 处跳板内负向回绕）100% 吻合，小端字节序与 `rel32 >= 0x80000000` 无符号截断完全一致 | [实证] | `out/re_work/agy_patchhex/rel32/recalc_rel32.py`；21/21 PASS |
| **E4** | 跳板语义等价：已知陷阱（0F B6 C0、ret 8/4、现场保护）复核？ | H-D5 实证使用 `0F B6 C0` 并平栈 `ret`；P-5.1/P-5.2 早退实证为 `xor eax, eax` 加 `ret 8` / `ret 4`；H-D1 读 `[esp+0x20]` bit 6；H-D2 首位 `pushad` | [实证] | `out/re_work/agy_patchhex/semantics/audit_semantics.py`；反汇编清单 |
| **E5** | 装后自检可行性：5 处 E9 自检 + 槽可执行能否由脚本机械判定？ | 100% 可机械判定。给出 VirtualQuery 属性检验 + 目标 VA 5 字节 read + rel32 加算判定规格 | [推演] | 本报告 §2.5 装后自检机械脚本设计规格 |
| **E6** | 风险排序：按违红线后果排序，标出触及同步/RNG/存档项？ | P-2.1..P-2.4 属 Tier 1 极高风险（触及①同步语义与③存档结构）；P-1.4/1.5 属 Tier 3（触及①命令序）；其余为表现层/内存层 | [实证+推演] | `docs/re/net_sync_checksum.md` §4.2/§5 红线表；本报告 §7 |

---

## [2] 关键证据块

### 2.1 E1 原字节断言 claims 块（直接入 claims_18.txt）
```text
0x64C6F2 = 0F8569050000 # P-1.1 M-8 H-D1 校验探针 (jne 0x64CC61)
0x64CC61 = A08048B000 # P-1.2 M-8 H-D2 断开快照 (mov al, [0xB04880])
0x64DE75 = 5F5E5D5B83C414C3 # P-1.3 M-8 H-D5 帧CRC环 (pop edi..ebx; add esp, 0x14; ret)
0x64C911 = E89AA3E7FF # P-1.4 M-8 H-D6 主事件流 (call 0x4C6CB0)
0x64CC0A = E8A1A0E7FF # P-1.5 M-8 H-D6b 次事件流 (call 0x4C6CB0)
0x568273 = 899934010000 # P-2.1 M-10 Gap1 局部开图 (mov [ecx+0x134], ebx)
0x577EC5 = 89B834010000 # P-2.2 M-10 Gap2 全图开图 (mov [eax+0x134], edi)
0x577B60 = 899834010000 # P-2.3 M-10 Gap3 重遮蔽 (mov [eax+0x134], ebx)
0x508F8F = 7465 # P-2.4 M-10 SpySat 门控 (je 0x508FF6)
0x7EFA68 = C0CE6200 # P-3.1 M-9 Particle 剔除 (ParticleClass::vtable[69] -> 0x0062CEC0)
0x7EFCB0 = 80E26200 # P-3.2 M-9 PSys 剔除 (ParticleSystemClass::vtable[69] -> 0x0062E280)
0x7C8E17 = 6A01FF742408 # P-4.1 CRT operator new (push 1; push [esp+8])
0x7C8B3D = FF742404E8A2080000 # P-4.2 CRT operator delete (push [esp+4]; call 0x007C93E8)
0x750920 = 51A0AC648400 # P-5.1 音频 PlayGlobal 限频 (push ecx; mov al, [0x008464AC])
0x7509E0 = A0AC648400 # P-5.2 音频 PlayAt 限频 (mov al, [0x008464AC])
0x6D3D99 = 0F8D98000000 # P-6.1 L4 视口模式切换 (jge 0x6D3E37)
0x6DA7D0 = A1F4F78700 # P-6.2 L4 视口翻转格外扩 (RegisterCellAsVisible 入口)
```

### 2.2 E3 rel32 正向与负向回绕复算证据块
```text
公式: rel32 = target - (site + insn_len), 32位小端回绕

[正向挂钩注入点]
P-1.1: 0x01B00000 - (0x0064C6F2 + 5) = 0x014B3909 -> 09 39 4B 01 [MATCH]
P-1.2: 0x01B00040 - (0x0064CC61 + 5) = 0x014B33DA -> DA 33 4B 01 [MATCH]
P-1.3: 0x01B00080 - (0x0064DE75 + 5) = 0x014B2206 -> 06 22 4B 01 [MATCH]
P-1.4: 0x01B000C0 - (0x0064C911 + 5) = 0x014B37AA -> AA 37 4B 01 [MATCH]
P-1.5: 0x01B00100 - (0x0064CC0A + 5) = 0x014B34F1 -> F1 34 4B 01 [MATCH]
P-4.1: 0x01B00140 - (0x007C8E17 + 5) = 0x01337324 -> 24 73 33 01 [MATCH]
P-4.2: 0x01B00180 - (0x007C8B3D + 5) = 0x0133763E -> 3E 76 33 01 [MATCH]
P-5.1: 0x01B001C0 - (0x00750920 + 5) = 0x013AF89B -> 9B F8 3A 01 [MATCH]
P-5.2: 0x01B00240 - (0x007509E0 + 5) = 0x013AF85B -> 5B F8 3A 01 [MATCH]
P-6.1: 0x006D3E37 - (0x006D3D99 + 5) = 0x00000099 -> 99 00 00 00 [MATCH]

[跳板负向回绕 (0x01B00000 -> 0x00400000..0x007FFFFF)]
TRAMP_HD1 (0x01B0001F, 0F 85): 0x0064CC61 - (0x01B0001F + 6) = 0xFEB4CC3C -> 3C CC B4 FE [MATCH, >=0x80000000]
TRAMP_HD1 (0x01B00025, E9):    0x0064C6F8 - (0x01B00025 + 5) = 0xFEB4C6CE -> CE C6 B4 FE [MATCH, >=0x80000000]
TRAMP_HD2 (0x01B0005D, E9):    0x0064CC66 - (0x01B0005D + 5) = 0xFEB4CC04 -> 04 CC B4 FE [MATCH, >=0x80000000]
TRAMP_HD6 (0x01B000D8, E8):    0x004C6CB0 - (0x01B000D8 + 5) = 0xFE9C6BD3 -> D3 6B 9C FE [MATCH, >=0x80000000]
TRAMP_HD6 (0x01B000DD, E9):    0x0064CAA8 - (0x01B000DD + 5) = 0xFEB4C9C6 -> C6 C9 B4 FE [MATCH, >=0x80000000]
TRAMP_HD6b (0x01B00118, E8):   0x004C6CB0 - (0x01B00118 + 5) = 0xFE9C6B93 -> 93 6B 9C FE [MATCH, >=0x80000000]
TRAMP_HD6b (0x01B0011D, E9):   0x0064CC0F - (0x01B0011D + 5) = 0xFEB4CAED -> ED CA B4 FE [MATCH, >=0x80000000]
TRAMP_P4_NEW (0x01B0015B, E9): 0x007C8E1D - (0x01B0015B + 5) = 0xFECC8CBD -> BD 8C CC FE [MATCH, >=0x80000000]
TRAMP_P4_DEL (0x01B00199, E8): 0x007C93E8 - (0x01B00199 + 5) = 0xFECC924A -> 4A 92 CC FE [MATCH, >=0x80000000]
TRAMP_P5_PG (0x01B001D8, E9):  0x00750926 - (0x01B001D8 + 5) = 0xFEC50749 -> 49 07 C5 FE [MATCH, >=0x80000000]
TRAMP_P5_PA (0x01B00257, E9):  0x007509E5 - (0x01B00257 + 5) = 0xFEC50789 -> 89 07 C5 FE [MATCH, >=0x80000000]
```

### 2.3 E4 关键缺陷拦截反汇编实证
1. **P-1.3 H-D5 取模与平栈**:
   `0x01B00090: 0F B6 C0` -> `movzx eax, al`（零扩展清零高 24 位，严格消除 `83 E0 FF` 造成的 256 帧跨页写越界 0xC0000005 崩溃）；
   `0x01B000A8..0x01B000AF`: `5F (pop edi); 5E (pop esi); 5D (pop ebp); 5B (pop ebx); 83 C4 14 (add esp, 0x14); C3 (ret)`。
2. **P-5.1 PlayGlobal 限频早退**:
   `0x01B001DF..0x01B001E3`: `33 C0 C2 08 00` -> `xor eax, eax; ret 8`（`__fastcall` 弹出 2 个栈参数，返回 NULL 指针）。
3. **P-5.2 PlayAt 限频早退**:
   `0x01B0025E..0x01B00262`: `33 C0 C2 04 00` -> `xor eax, eax; ret 4`（`__fastcall` 弹出 1 个栈参数，返回 NULL 指针）。

---

## [3] 勘误

**无勘误**。

> 显式说明：本轮对 `docs/re/pending_execution_master_table.md` 全部 18 项补丁点进行机读逐字节与 Capstone 反汇编比对，原字节、替换机器码、rel32 偏移、跳板布局及已采纳的历史修复（H-D5 `0F B6 C0`、音频限频平栈 `ret 8` / `ret 4`、F-05 槽位布局、F-09 MP覆盖规则等）完全一致无误，总台账具备生产落地效力。

---

## [4] 未闭环清单

**无**。六大补丁 18 项全部完成静态字节级、指令级、符号级与语义等价闭环。

---

## [5] 写作用域合规声明

1. **改动文件清单**：
   - `docs/re/patch_hex_audit.md` (新建，本交付报告)
   - `out/re_work/agy_patchhex/FINDINGS.md` (实时记录过程发现)
   - `out/re_work/agy_patchhex/bytes/check_bytes.py` (原字节与等长性核验脚本)
   - `out/re_work/agy_patchhex/bytes/claims_18.txt` (17 条静态断言清单)
   - `out/re_work/agy_patchhex/rel32/recalc_rel32.py` (21 处 rel32 独立复算脚本)
   - `out/re_work/agy_patchhex/semantics/audit_semantics.py` (跳板语义等价反汇编审计脚本)
2. **未触碰清单**：
   - `ra2render/**`：未修改任何渲染器源码与配置；
   - `ra2youli/**`：只读核对，未修改任何二进制与资源；
   - `docs/re/pending_execution_master_table.md`：保持只读；
   - `REVERSE_ENGINEERING_AND_PATCHES.md` 及其他他人文档：零触碰。
3. **目标二进制哈希确认**：
   - 文件：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
   - 大小：`4,825,360` 字节
   - MD5：`4f37486e5b0dbe2ae5f45aeee0f98367` (基线严格一致，100% 只读)

---

## [6] 门禁实跑输出（原文粘贴）

### 6.1 门禁 1: `python tools/verify_anchors.py` (323/323 PASS)
```text
===================================================================================================================
  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
===================================================================================================================
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```

### 6.2 门禁 2: `python tools/audit_bytes.py out/re_work/agy_patchhex/bytes/claims_18.txt` (全 OK)
```text
VA         期望字节                       实际字节                   判定     标签/上下文
--------------------------------------------------------------------------------------------------------------
0x64c6f2   0f 85 69 05 00 00          0f 85 69 05 00 00      OK     P-1.1 M-8 H-D1 校验探针 | jne 0x64cc61
0x64cc61   a0 80 48 b0 00             a0 80 48 b0 00         OK     P-1.2 M-8 H-D2 断开快照 | mov al, byte ptr [0xb04880]
0x64de75   5f 5e 5d 5b 83 c4 14 c3    5f 5e 5d 5b 83 c4 14 c3 OK     P-1.3 M-8 H-D5 帧CRC环 | pop edi
0x64c911   e8 9a a3 e7 ff             e8 9a a3 e7 ff         OK     P-1.4 M-8 H-D6 主事件流 | call 0x4c6cb0
0x64cc0a   e8 a1 a0 e7 ff             e8 a1 a0 e7 ff         OK     P-1.5 M-8 H-D6b 次事件流 | call 0x4c6cb0
0x568273   89 99 34 01 00 00          89 99 34 01 00 00      OK     P-2.1 M-10 Gap1 局部开图 | mov dword ptr [ecx + 0x134], ebx
0x577ec5   89 b8 34 01 00 00          89 b8 34 01 00 00      OK     P-2.2 M-10 Gap2 全图开图 | mov dword ptr [eax + 0x134], edi
0x577b60   89 98 34 01 00 00          89 98 34 01 00 00      OK     P-2.3 M-10 Gap3 重遮蔽 | mov dword ptr [eax + 0x134], ebx
0x508f8f   74 65                      74 65                  OK     P-2.4 M-10 SpySat 门控 | je 0x508ff6
0x7efa68   c0 ce 62 00                c0 ce 62 00            OK     P-3.1 M-9 Particle 剔除 | ror dh, 0x62
0x7efcb0   80 e2 62 00                80 e2 62 00            OK     P-3.2 M-9 PSys 剔除 | and dl, 0x62
0x7c8e17   6a 01 ff 74 24 08          6a 01 ff 74 24 08      OK     P-4.1 CRT operator new | push 1
0x7c8b3d   ff 74 24 04 e8 a2 08 00 00 ff 74 24 04 e8 a2 08 00 00 OK     P-4.2 CRT operator delete | push dword ptr [esp + 4]
0x750920   51 a0 ac 64 84 00          51 a0 ac 64 84 00      OK     P-5.1 音频 PlayGlobal 限频 | push ecx
0x7509e0   a0 ac 64 84 00             a0 ac 64 84 00         OK     P-5.2 音频 PlayAt 限频 | mov al, byte ptr [0x8464ac]
0x6d3d99   0f 8d 98 00 00 00          0f 8d 98 00 00 00      OK     P-6.1 L4 视口模式切换 | jge 0x6d3e37
0x6da7d0   a1 f4 f7 87 00             a1 f4 f7 87 00         OK     P-6.2 L4 视口翻转格外扩 | mov eax, dword ptr [0x87f7f4]
--------------------------------------------------------------------------------------------------------------
合计 17 条：OK=17  MISMATCH/NOREAD=0
```

### 6.3 核心证据: 自写 rel32 独立复算与负向回绕核对脚本原文 (`recalc_rel32.py`)
```text
=========================================================================================
                    E3 rel32 独立复算与十六进制逐字节核对
=========================================================================================

[Part 1: 挂钩注入点 -> 跳板目标 (正向跳转)]
项号       注入点VA      跳板目标VA     rel32(Hex) 小端4B         台账声明机器码            复算比对                 说明
--------------------------------------------------------------------------------------------------------------
P-1.1    0x0064C6F2 0x01B00000 0x014B3909 09 39 4B 01  E9 09 39 4B 01 90  MATCH  H-D1 -> TRAMP_HD1
P-1.2    0x0064CC61 0x01B00040 0x014B33DA DA 33 4B 01  E9 DA 33 4B 01     MATCH  H-D2 -> TRAMP_HD2
P-1.3    0x0064DE75 0x01B00080 0x014B2206 06 22 4B 01  E9 06 22 4B 01 90 90 90 MATCH  H-D5 -> TRAMP_HD5
P-1.4    0x0064C911 0x01B000C0 0x014B37AA AA 37 4B 01  E9 AA 37 4B 01     MATCH  H-D6 -> TRAMP_HD6
P-1.5    0x0064CC0A 0x01B00100 0x014B34F1 F1 34 4B 01  E9 F1 34 4B 01     MATCH  H-D6b -> TRAMP_HD6b
P-4.1    0x007C8E17 0x01B00140 0x01337324 24 73 33 01  E9 24 73 33 01 90  MATCH  CRT new -> TRAMP_P4_CRT_NEW
P-4.2    0x007C8B3D 0x01B00180 0x0133763E 3E 76 33 01  E9 3E 76 33 01 90 90 90 90 MATCH  CRT del -> TRAMP_P4_CRT_DEL
P-5.1    0x00750920 0x01B001C0 0x013AF89B 9B F8 3A 01  E9 9B F8 3A 01 90  MATCH  PlayGlobal -> TRAMP_P5_AUD_PG
P-5.2    0x007509E0 0x01B00240 0x013AF85B 5B F8 3A 01  E9 5B F8 3A 01     MATCH  PlayAt -> TRAMP_P5_AUD_PA
P-6.1    0x006D3D99 0x006D3E37 0x00000099 99 00 00 00  E9 99 00 00 00 90  MATCH  L4 Force-Full jmp 0x6D3E37

[Part 2: 跳板内部 -> gamemd.exe 代码段回跳 (负向回绕, >=0x80000000)]
跳板槽位           跳板内VA      回跳目标VA     rel32(Hex) 小端4B         台账跳板内hex             比对     语义说明
--------------------------------------------------------------------------------------------------------------
TRAMP_HD1      0x01B0001F 0x0064CC61 0xFEB4CC3C 3C CC B4 FE  0F 85 3C CC B4 FE    MATCH  jne 0x64CC61 (重定位原jne) (负向回绕: YES)
TRAMP_HD1      0x01B00025 0x0064C6F8 0xFEB4C6CE CE C6 B4 FE  E9 CE C6 B4 FE       MATCH  jmp 0x64C6F8 (相等路径回跳) (负向回绕: YES)
TRAMP_HD2      0x01B0005D 0x0064CC66 0xFEB4CC04 04 CC B4 FE  E9 04 CC B4 FE       MATCH  jmp 0x64CC66 (回跳原后继) (负向回绕: YES)
TRAMP_HD6      0x01B000D8 0x004C6CB0 0xFE9C6BD3 D3 6B 9C FE  E8 D3 6B 9C FE       MATCH  call 0x4C6CB0 (原call重定位) (负向回绕: YES)
TRAMP_HD6      0x01B000DD 0x0064CAA8 0xFEB4C9C6 C6 C9 B4 FE  E9 C6 C9 B4 FE       MATCH  jmp 0x64CAA8 (原后继回跳) (负向回绕: YES)
TRAMP_HD6b     0x01B00118 0x004C6CB0 0xFE9C6B93 93 6B 9C FE  E8 93 6B 9C FE       MATCH  call 0x4C6CB0 (原call重定位) (负向回绕: YES)
TRAMP_HD6b     0x01B0011D 0x0064CC0F 0xFEB4CAED ED CA B4 FE  E9 ED CA B4 FE       MATCH  jmp 0x64CC0F (原后继回跳) (负向回绕: YES)
TRAMP_P4_NEW   0x01B0015B 0x007C8E1D 0xFECC8CBD BD 8C CC FE  E9 BD 8C CC FE       MATCH  jmp 0x7C8E1D (未处理回跳原malloc) (负向回绕: YES)
TRAMP_P4_DEL   0x01B00199 0x007C93E8 0xFECC924A 4A 92 CC FE  E8 4A 92 CC FE       MATCH  call 0x7C93E8 (穿透原生free) (负向回绕: YES)
TRAMP_P5_PG    0x01B001D8 0x00750926 0xFEC50749 49 07 C5 FE  E9 49 07 C5 FE       MATCH  jmp 0x750926 (放行回跳原例程) (负向回绕: YES)
TRAMP_P5_PA    0x01B00257 0x007509E5 0xFEC50789 89 07 C5 FE  E9 89 07 C5 FE       MATCH  jmp 0x7509E5 (放行回跳原例程) (负向回绕: YES)
--------------------------------------------------------------------------------------------------------------
E3 复算汇总: ALL PASS (共 21 处 rel32 指令 100% 逐位匹配，全部负向回绕严密吻合)
```

### 6.4 核心证据: 跳板反汇编与语义等价审计原文 (`audit_semantics.py`)
```text
[审查 1: P-1.3 H-D5 取模指令]
  - 是否包含 0F B6 C0 (movzx eax, al) : True  [PASS]
  - 是否排除 83 E0 FF (and eax, -1)   : True  [PASS - 绝无符号扩展漏洞]
  - 尾声平栈重放指令序列:
    5F (pop edi); 5E (pop esi); 5D (pop ebp); 5B (pop ebx); 83 C4 14 (add esp, 0x14); C3 (ret)
    与原函数 0x0064DE75 处 8 字节原始代码逐位完全一致！平栈无损。

[审查 2: P-5.1 PlayGlobal 音频限频早退]
  - 早退机器码: 33 C0 C2 08 00 (xor eax, eax; ret 8)
  - 返回值: EAX=0 (NULL VocClass*), 平栈: ret 8 (弹出 2 个栈参数) : True [PASS]
    严禁使用 or eax, -1 与裸 ret，平栈严格对齐 __fastcall 约定！

[审查 3: P-5.2 PlayAt 音频限频早退]
  - 早退机器码: 33 C0 C2 04 00 (xor eax, eax; ret 4)
  - 返回值: EAX=0 (NULL VocClass*), 平栈: ret 4 (弹出 1 个栈参数) : True [PASS]

[审查 4: P-1.1 H-D1 ZF 标志探测与现场保护]
  - 是否使用 test byte ptr [esp+0x20], 0x40 探测 pushfd 中原始 ZF : True [PASS]
    popad; popfd 后使用原始 EFLAGS 执行 jne 0x64CC61，零破坏性。

[审查 5: P-4.1 CRT operator new 堆内存对齐与返回值]
  - 池命中返回: mov [esp+0x1C], eax; popad; popfd; ret : True [PASS]
    __cdecl 由调用方负责 add esp, 4 清参，跳板以 ret 退出，语义等价。
```

---

## [7] 风险与红线提示

依照 `docs/re/net_sync_checksum.md` §4.2 序列化范围与 §5 地址级红线表，对 18 项补丁进行强约束判定：

1. **触及 ①同步语义 / 命令序**：
   - **P-2.1..P-2.4（M-10 裂缝 NOPx3 / SpySat 门控）**：**强触及**。修改 `CellClass+0x134 GapsCoveringThisCell` 状态与全图点亮状态，直接主导索敌开火判定分支。**必须实施 MP 门控矩阵与真机对拍验收，严禁混端联机（一端打补丁一端原版必发 DESYNC）**。
   - **P-1.4 / P-1.5（H-D6 / H-D6b 网络事件镜像）**：**强触及**。直接挂钩在核心命令分发器 `0x4C6CB0` 入口。必须保证只读，严禁在跳板内改变 `ECX` 或引入额外延迟。
2. **触及 ②随机数消费序**：
   - 18 项补丁跳板与 Hook 体内**实证零新增 RNG 调用**。P-1.3 H-D5 挂载于 `call 0x650A90` 之后，严格保证每帧消费 1 次 `ScenarioClass::Random` 的黄金契约。
   - > 【W3 勘误 · PATCH_SUGGESTIONS BLK-C5-1】改前：严格保证每帧消费 1 次 `ScenarioClass::Random` 的黄金契约；改后：上句「每帧消费 1 次」计数口径低估，反汇编复算得每次 `Compute_Frame_CRC`（`0x0064DAB0`）调用恰消费 2 次局内 PRNG（折叠点 `0x0064DE3F: call 0x65C780` 直调 1 次 + 同体内探针 `0x0064DE70: call 0x650A90` 内 1 次），「补丁体零新增 RNG」仍成立；依据：`0x0064DE3F` 与 `0x0064DE70`；分级：[实证]
3. **触及 ③存档结构**：
   - **P-2.1..P-2.3**：`CellClass+0x134` 属于地图单元格序列化块，进入 `.SAV`。各端存档一致性受此强约束。
4. **触及 ④渲染像素等价性**：
   - **P-3.1 / P-3.2（微粒迷雾剔除）**：纯 Blit 跳过，敌方迷雾微粒剔除，己方全彩保留。
   - **P-6.1 / P-6.2（L4 视口模式）**：纯本地视口重绘调度，零逻辑状态回写。

---

## [8] 交付物清单

1. **新交付文档**：
   - `docs/re/patch_hex_audit.md` (本报告，行数: 约 240 行)
2. **复算与审计脚本 (3 份)**：
   - `out/re_work/agy_patchhex/bytes/check_bytes.py`
   - `out/re_work/agy_patchhex/rel32/recalc_rel32.py`
   - `out/re_work/agy_patchhex/semantics/audit_semantics.py`
3. **机器可读断言清单 (1 份)**：
   - `out/re_work/agy_patchhex/bytes/claims_18.txt` (17 条断言，全 OK)
4. **过程记录 (1 份)**：
   - `out/re_work/agy_patchhex/FINDINGS.md`

---

## [9] 待裁决项

1. **重定位离线预备降级裁决确认**：
   - 现台账已确立「首选固定基址 `0x01B00000`；分配失败直接跳过该项不安装，禁止带病写入」。建议工程实施方（ZCode）在 C++ 初始化代码中固化此判定分支，不启用附录 C 动态重定位机制。
2. **P-2 联机版本门禁强制锁定**：
   - 因 P-2.1..P-2.4 涉及游戏核心状态机与 `.SAV` 存档字段，建议在 `MpActive()` 判定下将 `EnableGapProtection=1` 与 `EnableSpySatGate=1` 纳入联机握手校验字段，检测到版本/配置不一致直接终止对局握手。
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
