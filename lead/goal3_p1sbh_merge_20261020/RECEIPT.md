# ③ 门 P1+SBH 合批 · 离线编译与门禁重算回执

**时间**：2026-10-20 21:5x–22:0x
**性质**：离线静态工作，未起跑任何真机趟，未启动 gamemd / ra2loader，母本零改动。
**对应目标**：③ 建立安全改动能力，完成判据第 1 条（合入同一基线后编译通过）与第 2 条（期望值重算）的准备。

---

## 一、结论摘要

| 项 | 结果 |
|:--|:--|
| P1 + SBH 合并 diff 应用 | **5/5 段干净命中**，零冲突 |
| 离线编译 | **CL_EXIT=0 / CL2_EXIT=0 / LINK_EXIT=0**，仅母本既有的 3 条 `fopen` C4996 警告 |
| §3.4 标记计数 | `[VER-GATE]`=12、`[SBH-GUARD]`=4、`[G3-SPLIT]`=30 |
| §3.4 全局符号重复定义 | **NONE**（35 个文件级定义，零重复） |
| §3.4 关键常量唯一性 | `g_targetScanInterval` 定义 1 处、钳位上限 `64` 单值；`EnableSbhGuard` 默认 `0` 单值 |
| `verify_hooks` 对合并件 | **FAIL** —— 见第四节，两个真实缺口 |

---

## 二、合批过程

### 2.1 输入件与哈希

| 件 | 大小 | sha256 前 16 |
|:--|--:|:--|
| `_work/p1base.cpp`（P1 基线，= `goal3_versioncheck_p2rebase_20261020/blitter_hooks_p2rebase.cpp`） | 261,746 B | `4431f4a422411966` |
| `_work/sbh.diff`（SBH 守卫原始 diff） | 18,782 B | — |
| `_work/sbh_on_p1_input.diff`（rebased 到 P1 的合并 diff） | 18,832 B | — |
| `_work/out_fuzz0.cpp`（应用后 + 补声明） | 278,462 B | `6de310d4f3af4b7b` |
| `build/ra2render_merged.dll` | 178,688 B | `4d3aacf7ddf5139f` |
| 母本 `ra2render/blitter_hooks.cpp` | 241,267 B | `656e6b4e48cdd251`（**未改动**） |

### 2.2 5 段合并命中明细

```
hunk1 OK  base 1,6     -> 1,11     （去重 bcrypt，补 g_enableSbhGuard 声明）
hunk2 OK  base 635,6   -> 640,10   （LoadConfig 读 EnableSbhGuard）
hunk3 OK  base 3754,6  -> 3763,395 （SBH 守卫主体 ~390 行）
hunk4 OK  base 4207,6  -> 4605,7   （InstallSbhGuardPatch 调用）
hunk5 OK  base 4218,6  -> 4617,7   （RemoveSbhGuardPatch 调用，逆序卸载位）
ALL APPLIED
```

**hunk1 的特殊处理**：原始 `sbh.diff` 的 hunk1 要 `#include <bcrypt.h>` 与
`#pragma comment(lib, "bcrypt.lib")`，但 P1 基线已由 `[VER-GATE V1]` 引入同两行。
`mkdiff.py` 的规则是「去重 + 补一行说明注释」，我按该规则重建 hunk1：

```cpp
// [SBH-GUARD] bcrypt.h / bcrypt.lib 已由 [VER-GATE V1] 引入（合批去重，不重复 include）
// [SBH-GUARD] 开关（默认 0 = 不碰 .text）
bool g_enableSbhGuard = false;
```

**为什么必须补这一行**：`patch` 应用原始 `sbh.diff` 时 hunk1 被拒（`.rej` 落盘），
导致 `g_enableSbhGuard` 的**全局定义缺失**，而 hunk2/3/4/5 仍在引用它 ——
这会直接编译失败。21:07 落盘的 `out_fuzz0.cpp` 正是这个状态（`g_enableSbhGuard`
出现 2 次、全是使用、零定义）。我用 Edit 补齐后编译才通过。

### 2.3 编译命令（可复跑）

`build_merged.cmd`：

```cmd
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x86
cl.exe /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /c /I"...\ra2render" /Fo:merged.obj "..\_work\out_fuzz0.cpp"
cl.exe /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /c /I"...\ra2render" /Fo:dllmain.obj "...\ra2render\dllmain.cpp"
cl.exe /nologo /LD /Fe:ra2render_merged.dll merged.obj dllmain.obj /link /MACHINE:X86 /SUBSYSTEM:WINDOWS kernel32.lib user32.lib winmm.lib bcrypt.lib
```

实测输出：

```
=== compiling merged P1+SBH ===
out_fuzz0.cpp
..\_work\out_fuzz0.cpp(3835): warning C4996: 'fopen' ...
..\_work\out_fuzz0.cpp(3875): warning C4996: 'fopen' ...
..\_work\out_fuzz0.cpp(4328): warning C4996: 'fopen' ...
CL_EXIT=0
dllmain.cpp
CL2_EXIT=0
LINK_EXIT=0
```

三条 C4996 是母本既有的 `fopen` 弃用警告，与合批无关。

---

## 三、§3.4 三项语法检查

### 3.1 标记计数

| 标记 | 次数 |
|:--|--:|
| `[VER-GATE` | 12 |
| `[SBH-GUARD` | 4 |
| `[G3-SPLIT` | 30 |

### 3.2 全局符号重复定义

文件级定义 35 个，**重复定义：NONE**。

重点核验 §310 记录过的两类事故：

| 符号 | 定义数 | 出现数 | 判定 |
|:--|--:|--:|:--|
| `g_telemetry` | 1（`ForgeTelemetry g_telemetry = {0,...}` @L27） | 60 | ✅ 单定义 |
| `g_enableSbhGuard` | 1（@L7） | 3 | ✅ 补声明后单定义 |
| `g_targetScanInterval` | 1（@L32） | 13 | ✅ 单定义 |
| `g_enableLFH` | 1 | 5 | ✅ |

### 3.3 关键常量唯一性

| 常量 | 实测 | 判定 |
|:--|:--|:--|
| `g_targetScanInterval` 初始化 | `= 1`（@L32，原版默认） | ✅ 非 §310 的旧值 8 |
| 同键钳位上限 | `> 64 → 64`（@L633，单值） | ✅ |
| `EnableSbhGuard` 默认值 | `0`（`GetIniIntEx("System","EnableSbhGuard",0,...)` 单处） | ✅ 默认不碰 .text |

---

## 四、`verify_hooks` 对合并件 FAIL —— 两个真实缺口

用 `tools/verify_hooks.py` 的**原始 `main()`**（不是重写的近似版）跑两档：

| 档 | `虚表安装/还原` | `Inline 备份` | `Install*/Remove*` | `ini 键/LoadConfig` | 结论 |
|:--|:--|:--|:--|:--|:--|
| 母本 `blitter_hooks.cpp` | 13 / 13 | 9 | 0 / 0 | 23 / 23 | **PASS** |
| P1+SBH `out_fuzz0.cpp` | **0 / 0** | 9 | **8 / 8** | 23 / **24** | **FAIL** |

### 缺口 1：`verify_hooks.py` 不认 P1 的五参数签名（假绿风险）

P1 把 `PatchVTablePointer` 从 4 参数改成 5 参数：

```cpp
// 母本
static bool PatchVTablePointer(uintptr_t targetAddr, uintptr_t newFunc,
                               uintptr_t *outOrigFunc, const char *name)
// P1（新增 expectOrig 版本门校验）
static bool PatchVTablePointer(uintptr_t targetAddr, uintptr_t newFunc,
                               uintptr_t *outOrigFunc, const char *name,
                               uintptr_t expectOrig)
```

而 `tools/verify_hooks.py:89-128` 的抽取正则写死 4 参数形态，实测：

| 档 | `PatchVTablePointer` 调用数 | 4 参正则命中 | 5 参正则命中 |
|:--|--:|--:|--:|
| 母本 | 13 | **13** | 0 |
| P1 | 13 | **0** | 13 |
| P1+SBH | 13 | **0** | 13 |

后果：门禁报「0 个虚表槽均有对应还原」并因 `0 == 0` 判 **PASS**。
这是**假绿**——13 个虚表槽位的覆盖在这条门禁下完全失明。

**影响范围**：③ 门第 2 条「13 个虚表槽位期望值重算」与第 3 条「verify_hooks 23/23」
都依赖这条门禁。P1 一旦合入，门禁必须先修，否则后续所有核验都在失明状态下进行。

### 缺口 2：`EnableSbhGuard` 未列入 `ra2render.ini`

合并件的 LoadConfig 读 `[System] EnableSbhGuard`（默认 0），但 `ra2render.ini` 的
`[System]` 节只有 `EnableLFH` 与 `HighPrecisionTimer`，没有这个键。门禁 [4] 项因此报：

```
[4] ini 键 vs LoadConfig
    !! LoadConfig 读取但 ini 未列出: ['EnableSbhGuard']
```

这是真实配置缺口：用户无法从 ini 发现这个开关，也无法开启守卫做 A/B。

---

## 五、未闭合项与下一步

| # | 项 | 状态 |
|:--|:--|:--|
| 1 | `verify_hooks` 五参数兼容补丁副本 | **在飞**（子代理产出 `verify_hooks.v2.py`） |
| 2 | `ra2render.ini` 补 `EnableSbhGuard=0` 补丁副本 | **在飞**（同子代理） |
| 3 | 白名单期望值对着当前母本重算 | 待 1 修好后做 |
| 4 | 13 槽位 / 9 位点的期望值重算 | 待 1 修好后做；9 位点清单已确认三档一致（见下） |
| 5 | 异族核验 | 待 1、2 交付后派 GLM/千问 |
| 6 | 真机「部署→冒烟→回滚→哈希复核」 | 需用户在场 |

**9 个 inline 代码位点三档一致性**（已实测，母本 / P1 / P1+SBH 完全相同）：

```
s_origCellClassDrawBytes, s_origDrawShroudFogBytes, s_origFogBlendB1Bytes,
s_origFogBlendB2Bytes, s_origGreatestThreatBytes, s_origNativeDecideBytes,
s_origPlotCellBytes, s_origRadarPendingCallBytes, s_origTacticalRedrawBytes
```

**13 个虚表槽位**（P1 的 5 参数形态，含期望原入口）：

| # | 目标槽 | 期望原入口 |
|--:|:--|:--|
| 1 | `ADDR_VTABLE_BLIT_TRANS_XLAT_ALPHA_ZREAD + 4` | `ADDR_VFUNC_BLIT_TRANS_XLAT_ALPHA_ZREAD` |
| 2 | `ADDR_VTABLE_BLIT_TRANS_XLAT_G + 4` | `ADDR_VFUNC_BLIT_TRANS_XLAT_G` |
| 3 | `ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G + 4` | `ADDR_VFUNC_RLE_BLIT_TRANS_XLAT_G` |
| 4 | `ADDR_VTABLE_BLIT_TRANS_G + 4` | `ADDR_VFUNC_BLIT_TRANS_G` |
| 5 | `ADDR_VTABLE_BLIT_TRANS_DARKEN_G + 4` | `ADDR_VFUNC_BLIT_TRANS_DARKEN_G` |
| 6 | `ADDR_VTABLE_BLIT_PLAIN_G + 4` | `ADDR_VFUNC_BLIT_PLAIN_G` |
| 7 | `ADDR_VTABLE_ENTRY_TECHNO_AUTO_TARGET` | `ADDR_ORIG_TECHNO_AUTO_TARGET` |
| 8 | `ADDR_VTABLE_ENTRY_UNIT_AUTO_TARGET` | `ADDR_ORIG_UNIT_AUTO_TARGET` |
| 9 | `ADDR_VTABLE_ENTRY_UNIT_DRAW` | `ADDR_ORIG_UNIT_DRAW` |
| 10 | `ADDR_VTABLE_ENTRY_INFANTRY_DRAW` | `ADDR_ORIG_INFANTRY_DRAW` |
| 11 | `ADDR_VTABLE_ENTRY_AIRCRAFT_DRAW` | `ADDR_ORIG_AIRCRAFT_DRAW` |
| 12 | `ADDR_VTABLE_ENTRY_BUILDING_DRAW` | `ADDR_ORIG_BUILDING_DRAW` |
| 13 | `ADDR_VTABLE_ENTRY_BULLET_DRAW` | `ADDR_ORIG_BULLET_DRAW` |

---

## 六、复跑命令

```bash
cd D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal3_p1sbh_merge_20261020

# 1. 合批 diff 应用校验（内存重放，不改盘）
PYTHONDONTWRITEBYTECODE=1 python analyze_p1_signature.py

# 2. 用原始 verify_hooks main() 跑母本与合并件两档
PYTHONDONTWRITEBYTECODE=1 python run_gate_on_merged.py

# 3. 离线编译
cmd //c build_merged.cmd
```

---

## 七、诚实边界

1. **未做真机验证**：编译通过只证明语法与链接正确，不证明守卫在游戏里行为正确。
2. **未做异族核验**：本件是主会话自测，③ 门第 2 条要求异族核验，尚未派。
3. **白名单未重算**：本件只统计了 13 槽与 9 位点的清单与一致性，未逐个对着母本二进制
   重算 `ADDR_*` 的实测值 —— 这是 ③ 门第 2 条的实质内容，待 `verify_hooks.v2` 到位后做。
4. **`ra2render.ini` 缺口未修**：只登记，修复件在飞。
5. **`0x0084F2BA` 崩溃与本件无关**：那是 ② 的线，本件不涉及。
