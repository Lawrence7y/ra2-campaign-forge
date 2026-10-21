# verify_hooks 五参数兼容修复 · 回执

**时间**：2026-10-20 22:5x–23:0x
**性质**：离线静态工作。母本零改动，未起跑任何真机趟。
**对应目标**：③ 建立安全改动能力，判据第 2 条（13 槽 / 9 位点期望值重算）与第 3 条（verify_hooks 通过）。

---

## 一、结论

| 档 | 虚表安装/还原 | Inline 备份 | Install*/Remove* | ini/LoadConfig | 结论 |
|:--|:--|--:|:--|:--|:--|
| MOTHER（母本 + 母本 ini） | **13 / 13** | 9 | 7 / 7 | 23 / 23 | **PASS** |
| P1（+ 母本 ini） | **13 / 13** | 9 | 7 / 7 | 23 / 23 | **PASS** |
| P1+SBH（+ 母本 ini） | **13 / 13** | 9 | 8 / 8 | 23 / **24** | **FAIL**（缺口真实） |
| P1+SBH（+ **v2 ini**） | **13 / 13** | 9 | 8 / 8 | **24 / 24** | **PASS** |

**母本档仍是 13/13 且 PASS ⇒ 补丁没有破坏旧口径。**
**P1+SBH 档在母本 ini 下 FAIL、在 v2 ini 下 PASS ⇒ 缺口真实存在且修复有效。**

---

## 二、两个缺口

### 缺口 1：`PatchVTablePointer` 五参数签名不被识别（假绿）

P1 版本门把签名从 4 参改成 5 参：

```cpp
// 母本
static bool PatchVTablePointer(uintptr_t targetAddr, uintptr_t newFunc,
                               uintptr_t *outOrigFunc, const char *name)
// P1（新增 expectOrig 版本门校验）
static bool PatchVTablePointer(uintptr_t targetAddr, uintptr_t newFunc,
                               uintptr_t *outOrigFunc, const char *name,
                               uintptr_t expectOrig)
```

原 `extract_vtable_installs` / `extract_vtable_removes` 用固定 4 参正则，对 P1 与 P1+SBH
抽取结果为 **0**，门禁却因 `0 == 0` 判 **PASS**：

```
[1] 虚表 Install/Remove 对称
    OK  0 个虚表槽均有对应还原
```

13 个虚表槽位完全失明。**这是假绿，不是真通过。**

#### 修复方式

不再用固定参数个数的正则，改为**括号配平扫描 + 按实参位置取值**：

- `_split_args()`：按顶层逗号切分实参串，跳过嵌套 `() [] {}` 与字符串字面量内的逗号（含转义引号）。
- `_iter_calls()`：从 `PatchVTablePointer(` 起做括号配平扫描，产出实参列表。
- install：`name` 取第 4 个实参（字符串字面量）；`expect_orig` 取第 5 个实参（4 参时为 `None`）。
- remove：判据由「第 2 参是 nullptr」改为「**第 3 参是 nullptr**」。

最后一条是关键：母本与 P1 的还原调用形态不同，但**共同点是第 3 参为 `nullptr`**：

```cpp
// 母本（4 参）
PatchVTablePointer(ADDR_VTABLE_... + 4,
                   reinterpret_cast<uintptr_t>(g_pOrig...), nullptr, "还原 X");
// P1（5 参）—— 注意第 2 参不是 nullptr，第 3 参才是
PatchVTablePointer(ADDR_VTABLE_... + 4,
                   reinterpret_cast<uintptr_t>(g_pOrig...), nullptr, "还原 X",
                   union_cast<uintptr_t>(&BlitterHooks::Hook_X));
```

旧正则的「第 2 参 nullptr」只对母本偶然成立。

#### 修复效果

| 档 | 修复前 install/remove | 修复后 install/remove | `expect_orig` 填充 |
|:--|:--|:--|:--|
| MOTHER | 0 / 0 | **13 / 13** | 0 / 13（4 参，正确） |
| P1 | 0 / 0 | **13 / 13** | 13 / 13（5 参，正确） |
| P1+SBH | 0 / 0 | **13 / 13** | 13 / 13（5 参，正确） |

install / remove 目标集三档均 **13 对 13 完全配对**（`install_only=0`、`remove_only=0`）。

### 缺口 2：`EnableSbhGuard` 未列入 `ra2render.ini`

合并件 LoadConfig 读 `GetIniIntEx("System", "EnableSbhGuard", 0, ...)`，但母本 ini 的
`[System]` 节只有 `EnableLFH` 与 `HighPrecisionTimer`。门禁 [4] 项因此报：

```
[4] ini 键 vs LoadConfig
    !! LoadConfig 读取但 ini 未列出: ['EnableSbhGuard']
```

#### 修复方式

`ra2render.ini.v2` 在 `[System]` 节 `EnableLFH` 之后插入两行：

```ini
; [SBH-GUARD] RC-1 堆 freelist 毒值守卫。0 = 不碰 .text（与原版逐位等价）；1 = 启用守卫（A/B 实验臂用）
EnableSbhGuard=0
```

与母本的 diff **只有这两行**：

```
@@ -57,4 +57,6 @@
 ; 启用 Low Fragmentation Heap (LFH) ...
 EnableLFH=1
+; [SBH-GUARD] RC-1 堆 freelist 毒值守卫。0 = 不碰 .text（与原版逐位等价）；1 = 启用守卫（A/B 实验臂用）
+EnableSbhGuard=0
 ; 锁定 Windows 系统时钟中断周期为 1ms ...
 HighPrecisionTimer=1
```

---

## 三、哈希

| 件 | 大小 | sha256 前 16 | 状态 |
|:--|--:|:--|:--|
| `tools/verify_hooks.py`（母本） | — | `8520fd0b231c9df9` | **未改动** |
| `ra2render/ra2render.ini`（母本） | 16,496 B | `27c9a60c55a8a1b4` | **未改动** |
| `ra2render/blitter_hooks.cpp`（母本） | 241,267 B | `656e6b4e48cdd251` | **未改动** |
| `verify_hooks.v2.py`（副本） | 20,541 B | `caa324cc2c701167` | 新建 |
| `ra2render.ini.v2`（副本） | 16,645 B | `577baa489cb3d8a5` | 新建 |

---

## 四、并发写入事故（如实登记）

派发 GLM 工作流修复此件后，我（主会话）**同时在同目录做同一件事**，造成两个写者交替覆写
`verify_hooks.v2.py`。GLM 子代理检测到异常并升级提问（`dwfq-eba184ee-1`），我确认责任在己
并令其停手让出目录，改由它只提供「正则原文 + 漏洞评估 + 假绿风险」三项文本意见供择优合并。

**纪律教训**：同一目录同一组交付件只允许一个写者。派发子代理后主会话不得在同目录动手。

**当前盘上版本**：以本回执为准（`caa324cc2c701167` / `577baa489cb3d8a5`）。
GLM 的原始方案未落盘，其意见若收到将另附。

---

## 五、复跑

```bash
cd D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal3_verifyhooks_fix_20261020

# 四档门禁实跑（母本档 / P1 / P1+SBH 母本 ini / P1+SBH v2 ini）
PYTHONDONTWRITEBYTECODE=1 python run_all_gates.py

# 三档抽取对照（含 expect_orig 与 ini 缺口）
PYTHONDONTWRITEBYTECODE=1 python three_way_check.py
```

---

## 六、未闭合项

| # | 项 | 状态 |
|:--|:--|:--|
| 1 | 白名单期望值对着当前母本重算 | **未做**（③ 门判据 2 的实质内容） |
| 2 | 13 槽 / 9 位点清单 | 已确认三档一致，但**未对着二进制重算 `ADDR_*` 实测值** |
| 3 | 异族核验 | **未做**（GLM 被令停手，千问核验阶段未到） |
| 4 | 真机「部署→冒烟→回滚→哈希复核」 | 需用户在场 |
| 5 | `tools/verify_hooks.py` 母本是否要吸收 v2 | **待 Lead 裁决**（母本零改动是铁律） |

---

## 七、诚实边界

1. 本件只证明**门禁工具**能正确识别 5 参签名，**不证明** 13 个槽位的 `ADDR_*` 常量值与
   母本二进制一致 —— 那是判据 2 的另一半，未做。
2. `Install*/Remove*` 从 7/7 变 8/8 是 SBH 守卫新增的 `InstallSbhGuardPatch` /
   `RemoveSbhGuardPatch` 一对，属预期增量，不是回归。
3. 未做异族核验。本回执的「PASS」是主会话自测，按 §3.3 不能单独作为 ③ 门第 3 条的
   最终证据。
4. 并发写入事故已登记，GLM 的独立意见未收到。
