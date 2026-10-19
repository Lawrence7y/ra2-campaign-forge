# ZCode 落地卡 · VXL 缓存预热扩容（SomeVoxelCache 初始容量 10→64）

> **卡号**：`ZC-VXL-PRE` · **优先级**：P1（低风险首批；渲染层缓存粒度）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-VXL-CACHE 静态定谳）  
> **上游**：`docs/re/vxl_cache_shadow_landing.md`（R-VXL-CACHE）§3.1/§4/§5 · 复算脚本 `out/re_work/re_sprint/R_vxl_cache/`  
> **本卡范围**：**仅 L-VXL-1 一点**（缓存 Miss 插入的**首次**分配粒度）。L-VXL-2 / L-VXL-3 **本卡不做**，仅附录预告。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **静态证据**：`out/re_work/re_sprint/R_vxl_cache/vxl_cache_bytes_report.txt`（L1-CACHE-GROW **MATCH**）· `vxl_cache_chain_report.txt`

---

## 0. 一句话

把 `Draw_A_VXL` 缓存 Miss 插入路径里 `mov ebx, 0xa`（`0x706D78`）的 **5 字节**等长改成 `mov ebx, 0x40`，使 `SomeVoxelCache` **首次**容量从 10 条升到 64 条（≈ 32 朝向 × 2 帧），覆盖常见朝向/帧组合、少扩容、少 qsort；扩容步长（翻倍）与插入/命中语义**原样不动**。

---

## 1. 执行表（字节级，等长替换）

| 项 | 值 |
|---|---|
| **步骤 ID** | `L-VXL-1` |
| **VA** | `0x00706D78` |
| **文件偏移** | `0x00306D78` |
| **节** | `.text` |
| **函数** | 缓存 Miss 插入扩容（`TechnoClass::Draw_A_VXL` 核 `0x00706640` 内） |
| **原字节（5B）** | `BB 0A 00 00 00` |
| **原指令** | `mov ebx, 0xa` （初始容量 = 10 条目） |
| **新字节（5B）** | `BB 40 00 00 00` |
| **新指令** | `mov ebx, 0x40` （初始容量 = 64 条目） |
| **改动长度** | **必须 5==5 等长**（禁 trampoline / 禁动 `.detour`） |
| **语义** | 只改**首次**分配粒度；扩容步长（`0x706D7F` `mov ebx,eax`，翻倍）、拷贝、插入、`IsSorted=0` 置脏、`LastFoundEntry` 清空 **全部不动** |
| **核验** | **[实证] MATCH**（`vxl_cache_bytes_report.txt` L1-CACHE-GROW） |

### 1.1 上下文窗（安装前后自检用）

| 偏移相对 VA | 原字节 | 说明 |
|---|---|---|
| `0x706D74` | `85 C0` | `test eax, eax` —— 判当前 Capacity 是否为 0 |
| `0x706D76` | `75 07` | `jne 0x706D7F` —— 非 0（已有容量）走 growstep；**0 才落到本点** |
| `0x706D78` | `BB 0A 00 00 00` | **★ 本卡替换点** → `BB 40 00 00 00` |
| `0x706D7D` | `EB 0A` | `jmp 0x706D89` —— 跳过 growstep，**禁改** |
| `0x706D7F` | `8B D8` | `mov ebx, eax` —— growstep（增量=当前容量，翻倍），**禁改** |
| `0x706D89` | `8D 3C 18` | `lea edi, [eax+ebx]` —— 新容量 = 旧容量 + 增量 |
| `0x706D8C` | `8D 14 FD 00 00 00 00` | `lea edx, [edi*8]` —— 新字节数 = 新容量 × 8 |
| `0x706D94` | `E8 7E 20 0C 00` | `call 0x7C8E17`（`operator new[]`）—— 扩容分配点 |

### 1.2 语义边界（只许动这一件事）

| 点 | 动作 | 本卡 |
|---|---|---|
| `0x706D78` `mov ebx, 0xa` | 首次分配粒度 10 | **改为 64** |
| `0x706D7F` `mov ebx, eax` | 后续扩容步长 = 当前容量（翻倍） | **保留** |
| `0x706E13` `C6 45 0C 00` | 插入置 `IsSorted=0`（排序脏） | **保留** |
| `0x706E17` | `Count++` | **保留** |
| `0x70680E` `75 65` | `DisableVoxelCache` 门 | **尊重，勿 NOP** |

**邻接约束（硬）**：`0x706D7D` 为 `EB 0A`、`0x706D7F` 为 `8B D8` —— **只许动 `0x0A→0x40` 一字节**（imm8 在 5B 指令内），禁改 `EB`/`8B`，禁改 `BB` 操作码。

---

## 2. 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | **拒绝安装** |
| G0.2 | `VA 0x706D78` 文件偏移 `0x306D78` 首 5B | `BB 0A 00 00 00` | 若已是 `BB 40 00 00 00`：报告「已打」并跳过；其它：**拒绝** |
| G0.3 | 窗前 `0x706D76` = `75 07` | MATCH | 拒绝 |
| G0.4 | 窗后 `0x706D7D` = `EB 0A` 且 `0x706D7F` = `8B D8` | MATCH | 拒绝 |
| G0.5 | `.text` 节可写性/映像基址 | PE32 / base `0x400000` | 拒绝 |
| G0.6 | 开关键 `EnableVxlCachePrewarm` | 显式 `1` 才安装 | 默认 **0=不装**（零行为变化） |

**Q1 真机首字节（安装前）**：断点/读 `0x706D78` 首字节 → `BB`+`0A` = 未打；`BB`+`40` = 本键已装；其它 = **停手并上报**（禁止覆盖未知安装者）。

---

## 3. 开关 · 遥测 · 回滚

### 3.1 开关（ini，`[Render]`）

| 键 | 默认 | 语义 |
|---|---|---|
| `EnableVxlCachePrewarm` | **`0`** | `1` 时安装 L-VXL-1；`0` 时不碰 `.text` |
| （另卡）`EnableVxlShadowSkip` / `EnableVxlShadowCacheForce` | `0` | **本卡不实现**；键名勿提前占用写入逻辑 |

**启动日志**：`VxlCachePrewarm=on|off|forced-off-mp`（与既有门控风格一致）。

### 3.2 遥测（只读计数，禁止热路径膨胀；无百分比承诺）

| 计数器 | 插桩 VA | 含义 |
|---|---|---|
| `vxlCacheInstalled` | init | 0/1 |
| `vxlCacheFindCalls` | `0x7107E0` 入口 | L2 Find 查询次数（分母） |
| `vxlCacheFindHits` | `0x7107E0` 命中返回 `0x710851` | 二分命中次数 |
| `vxlCacheL1Hits` | `0x746EA0` 返回 `AL=1` 前 | MRU 快路径命中 |
| `vxlCacheQsortCalls` | `0x710800` 前 | 排序脏触发次数（L-VXL-1 后应**下降**） |
| `vxlCacheGrowths` | `0x706D94`（`call new[]`）前 | 扩容次数（L-VXL-1 直接作用点，应**下降**） |
| `vxlCacheInserts` | `0x706E17` 前 | 新条目写入次数 |

**采样协议**：同地图、同镜头、同单位编成（建议 ≥24 辆同型号静止 + 8 辆旋转）；窗口 ≥300 帧、丢弃首 60 帧；键开/关各一遍，**只报告计数差值方向与调用次数**，禁止写百分比承诺。

### 3.3 回滚

1. **软**：`EnableVxlCachePrewarm=0` + 重启游戏/重载 DLL（安装态 init 读一次，参考 `LoadConfig` 仅 init 读一次的教训）。  
2. **硬**：备份 5B 原字节 `s_origLVxl1[5] = BB 0A 00 00 00` → `memcpy` 还原。  
3. **卸载工具**：若走补丁器，提供 `--uninstall-lvxl1` 仅还原该 5B。

---

## 4. 真机验收用例（Z- 系列，最小 3 条）

| ID | 步骤 | 期望 |
|---|---|---|
| **A1** | 默认配置启动 | `0x706D78` 仍为 `BB 0A 00 00 00`；无崩溃；`VxlCachePrewarm=off` |
| **A2** | `EnableVxlCachePrewarm=1` 启动 | `0x706D78` = `BB 40 00 00 00`；`0x706D76/0x706D7D/0x706D7F` 未变；日志 `VxlCachePrewarm=on` |
| **A3** | 打完字节后连打**两局**（含单位旋转/换帧） | 两局 `except.txt` 均空；无花屏/无影错位/无崩溃 |
| **A4** | A3 同场景采样遥测 | `vxlCacheFindCalls` / `vxlCacheFindHits` / `vxlCacheQsortCalls` / `vxlCacheGrowths` **计数可见**；对照键关局：`vxlCacheGrowths` 与 `vxlCacheQsortCalls` 有下降方向 |

**禁止把「没崩」当成功**：A4 必须有计数文件/日志证据；本卡**无任何百分比收益承诺**，只验收「字节装上 + 两局无 except + 计数可见」。

---

## 5. MP（联机）裁决

| 项 | 结论 |
|---|---|
| 是否可装 | **可装**。纯表现层缓存粒度，不进 `.SAV`、不进同步契约、无 DESYNC（`net_sync_desync_map.md` **D-VXL13** = SAFE） |
| 联机默认建议 | **建议装**（全端同键 `EnableVxlCachePrewarm=1`）。理由：零观感差、零逻辑写；收益在帧时间/扩容次数侧，两端一致便于对拍遥测 |
| 例外 | 若对拍基线要求「绝对零补丁差」，可全端置 `0`；**禁止混端**（一端 1 一端 0）以便遥测同口径 |
| 与观感分叉 | 本点**不**产生观感分叉（不同于 L-VXL-2 的影跳过） |

---

## 6. 风险（执行方必读）

| ID | 风险 | 要求 |
|---|---|---|
| R-1 | 每 Type 每缓存多占 `(64−10)×8 = 432B`；4 缓存 ≈ **1.7KB/Type** | 仅初始 64，**不改**翻倍步长；已计入「低」风险 |
| R-2 | 外部安装者已改同址 | G0.2/Q1 首字节门禁；非 `0A`/`40` 停手 |
| R-3 | 邻接 flags / 指令边界 | 只许 imm8 `0x0A→0x40`；**禁改** `EB 0A` / `8B D8` / 操作码 `BB` |
| R-4 | 误改 growstep 导致容量爆炸 | G0.4 强制 `0x706D7F = 8B D8` |
| R-5 | 尊重 `DisableVoxelCache` | `0x70680E` 门**不得 NOP**；禁缓存单位仍走软光栅 |
| R-6 | 与 L-VXL-2/3 混装归因混乱 | 本卡只装 L-VXL-1；异常先关本键再考虑另卡 |

---

## 7. 交付回执（填完交回）

```
ZC-VXL-PRE RESULT
- build/md5(gamemd):
- install path: (ra2render hook | external patcher | ...)
- EnableVxlCachePrewarm:
- G0.1–G0.6: PASS/FAIL
- Q1 first byte before:
- bytes after @0x706D78:
- neighbor check @0x706D76/7D/7F:
- A1..A4: (each PASS/FAIL + evidence path)
- telemetry sample: (path; FindCalls/FindHits/QsortCalls/Growths)
- except.txt (game1|game2): empty|path
- rollback tested: y/n
```

---

## 8. 不在本卡（附录预告）

| ID | 概要 | 风险 | 键名（预留） | 状态 |
|---|---|---|---|---|
| **L-VXL-2** | SHP 单位影强制跳过：`0x73D0E3` `0F 84 AF 01 00 00` → `E9 AF 01 00 00 90` | **中**（脚下影消失，观感） | `EnableVxlShadowSkip` | **另卡**；`MpActive` 时强制不装 |
| **L-VXL-3** | VXL 影缓存强制启用：`0x706C3B` `0F 85 A0 00 00 00` → `90×6` | **中低**（忽略 `DisableShadowCache`） | `EnableVxlShadowCacheForce` | **另卡**；异常先关再关本键归因 |

> 预告仅供排期，**不得**在本卡安装路径中顺手落 L-VXL-2/3。降采样（动 `0x707480` 光核）**不落地**（高风险，R-VXL-CACHE R-4）。

其它不在本卡：`ra2render` 源码重构、台账/看板登记（Lead 收口）、MP 握手字段扩展。

---

*依据：R-VXL-CACHE §3.1/§4/§5/§6；原字节 1/1 MATCH；imm8 `0x0A→0x40` 为唯一 5B 等长替换；收益只给插桩口径，无百分比承诺。*
