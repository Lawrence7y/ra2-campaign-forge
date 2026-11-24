# Q1 溯源定谳报告：`counters[].shape.b_valid` 字段取值与引擎语义

> **报告版本**：2026-11-05  
> **分析员**：b_valid 溯源员（RA2/YR 数据链路分析员）  
> **分析纪律**：纯离线数据分析 + gamemd.exe 静态反汇编；零真机、不启动游戏、不写采样代码、找不到写找不到。

---

## 1. 一句话结论

`counters[].shape.b_valid` 是 harness 对引擎全局建筑实例动态向量 `BuildingClass::Array`（基址 `0x00A8EB40`）的内存形状有效性探针；`b_valid=false` 的**唯一真实引擎语义**是「战局当前建筑实体数为 0、动态向量处于尚未插入任何元素时的惰性未分配空指针初始态（`Count=0 ∧ Items=NULL`）」，与 BOOT/载入方式无关，且由反例 `t55k_20261020`（全 false 仍 31.24 fps 满帧）与 `l3_1101v4c`（全程 false 但 w2 恢复至 30.68 fps）**确证与 5.7 倍帧时恶化无任何因果关系**，属样本偏倚导致的伴随伪相关。

---

## 2. (a) Harness 取值代码溯源

在 `lead/goal1_harness8_20261031` 目录下，对关键词 `b_items`、`b_valid`、`counters` 进行源码静态 grep，命中文件包括：
- `qc151_trip.harness8_v4.py`
- `qc151_trip.harness8_v3.py`
- `qc151_trip.harness8.py`

三份 harness 脚本在计数器取值段逻辑完全同构。以下以当前基线版本 `qc151_trip.harness8_v4.py` 为例，给出准确行号与完整取值实现：

### 2.1 常量定义（`qc151_trip.harness8_v4.py:3839-3840`）
```python
3839: MEASURE_B_VA = 0x00A8EB50            # B（Items=0x00A8EB44）
3840: MEASURE_B_ITEMS_VA = 0x00A8EB44
```

### 2.2 计数器副读函数（`qc151_trip.harness8_v4.py:3979-4001`）
```python
3979: def _rpm_counters(handle) -> dict:
3980:     """★ 1 Hz 计数器副读（§3.2）：units/infantry/aircraft + G/B/Techno
3981:     （Items 形状自检 D-3：`Items != 0 ∧ Count ≤ 100000`——Items 是**指针**，
3982:     ★ 禁用 `Count−Items==0xC`（把指针当计数，恒假；§3.6-D3））+ 工作集/提交内存。
3983: 
3984:     ★ 任一项读失败 ⇒ 该项 `null`（不写 0）；**零写入**目标进程。
3985:     """
3986:     units = _rpm_u32(handle, MEASURE_UNITS_VA)
3987:     infantry = _rpm_u32(handle, MEASURE_INFANTRY_VA)
3988:     aircraft = _rpm_u32(handle, MEASURE_AIRCRAFT_VA)
3989:     g = _rpm_u32(handle, MEASURE_G_VA)
3990:     g_items = _rpm_u32(handle, MEASURE_G_ITEMS_VA)
3991:     b = _rpm_u32(handle, MEASURE_B_VA)
3992:     b_items = _rpm_u32(handle, MEASURE_B_ITEMS_VA)
3993:     techno = _rpm_u32(handle, MEASURE_TECHNO_VA)
3994:     ws_kb, pf_kb = _rpm_mem_kb(handle)
3995:     return {"units": units, "infantry": infantry, "aircraft": aircraft,
3996:             "g": g, "b": b, "techno": techno, "g_items": g_items,
3997:             "b_items": b_items, "ws_kb": ws_kb, "pf_kb": pf_kb,
3998:             "shape": {"g_valid": (None if (g is None or g_items is None)
3999:                                   else (g_items != 0 and g <= 100000)),
4000:                       "b_valid": (None if (b is None or b_items is None)
4001:                                   else (b_items != 0 and b <= 100000))}}
```

### 2.3 采样主轮询调度（`qc151_trip.harness8_v4.py:4015-4035`）
```python
4015:     counters: list = []
...
4019:     next_ctr = t0 - 1.0        # ★ 首轮即做一次计数器副读（t_rel≈0，§3.2 schema）
...
4031:         if t_now >= next_ctr:
4032:             row = _rpm_counters(handle)
4033:             row["t_rel"] = round(t_now - t0, 6)
4034:             counters.append(row)
4035:             next_ctr = t_now + 1.0
```

### 2.4 完整取值布尔逻辑
- harness 每 1 秒（1 Hz）调用一次 `_rpm_counters`；
- 调用 Windows 原生 API `ReadProcessMemory`（4 字节无符号小端序读取）：
  - `b = _rpm_u32(handle, 0x00A8EB50)`
  - `b_items = _rpm_u32(handle, 0x00A8EB44)`
- 判定条件：
  - 若 `b is None or b_items is None`（RPM 读失败），则 `b_valid = None`；
  - 否则，`b_valid = (b_items != 0 and b <= 100000)`。
  - 即：**当且仅当 `b_items == 0` 或 `b > 100000` 时，`b_valid` 产生 `False`**。

---

## 3. (b) 全局 VA 常量与引擎数据结构溯源

通过对 `ra2youli/gamemd.exe` 的 PE 结构、MSVC RTTI 链及静态反汇编分析，对这组 VA 的身份确证如下：

### 3.1 核心数据结构：`DynamicVectorClass<BuildingClass*>`
`MEASURE_B_VA` 与 `MEASURE_B_ITEMS_VA` 属于 RA2/YR 引擎标准动态向量模板类 `DynamicVectorClass<T>`：
- **基址**：`0x00A8EB40`（符号名 `BuildingClass::Array`，见 `docs/re/LESSONS_20261003_RE_INSTRUMENTS.md:397` 与 `docs/re/savegame_block_manifest.md:391`）
- **所属段**：`.data` 段中的 BSS 未初始化区（内存 VA `0x00A8EB40`，镜像加载时由 OS PE Loader 零填充）
- **RTTI 证据**：
  - 虚表地址：`0x007E9E24`
  - CompleteObjectLocator 位于 `0x007E9E24 - 4 = 0x007E9E20`，指向 VA `0x00801280`
  - TypeDescriptor 位于 `0x00823270`
  - 符号名字符串解析：`.?AV?$DynamicVectorClass@PAVBuildingClass@@@@`（完全匹配 `DynamicVectorClass<BuildingClass*>`）

### 3.2 字段内存布局（Offset Map）
| 偏移 | 全局 VA | 字段名 | 类型 | Harness 常量名 | 初始状态（CRT Init） | 运行时语义 |
|---|---|---|---|---|---|---|
| `+0x00` | `0x00A8EB40` | `vftable` | `void**` | — | `0x007E9E24` | 指向 `DynamicVectorClass<BuildingClass*>` 虚函数表 |
| `+0x04` | `0x00A8EB44` | `Items` / `Vector` | `BuildingClass**` | `MEASURE_B_ITEMS_VA` | `0x00000000` (NULL) | 指向堆内存中分配的指针数组首地址 |
| `+0x08` | `0x00A8EB48` | `VectorMax` | `uint32_t` | — | `0` | 当前向量分配的总容量（Capacity） |
| `+0x0C` | `0x00A8EB4C` | `IsAllocated` | `uint8_t` | — | `1` | 内存管理标志位 |
| `+0x0D` | `0x00A8EB4D` | `IsInitialized` | `uint8_t` | — | `0` | 状态标志位 |
| `+0x10` | `0x00A8EB50` | `Count` / `ActiveCount` | `uint32_t` | `MEASURE_B_VA` | `0` | 当前活跃建筑实体总数 |
| `+0x14` | `0x00A8EB54` | `CapacityIncrement` | `uint32_t` | — | `10` (`0x0A`) | 自动扩容步长 |

### 3.3 汇编生命周期证据
1. **静态全局构造（`0x004E6B60`）**：
   ```x86asm
   004E6B60: 33 C0                 xor eax, eax
   004E6B62: 68 A0 6B 4E 00        push 0x4E6BA0           ; 析构函数注册
   004E6B67: A3 44 EB A8 00        mov [0x00A8EB44], eax   ; Items = NULL (0)
   004E6B6C: A3 48 EB A8 00        mov [0x00A8EB48], eax   ; VectorMax = 0
   004E6B71: C6 05 4C EB A8 00 01  mov byte [0x00A8EB4C], 1
   004E6B78: A2 4D EB A8 00        mov byte [0x00A8EB4D], al
   004E6B7D: C7 05 40 EB A8 00 24 9E 7E 00 mov [0x00A8EB40], 0x007E9E24 ; vftable
   004E6B87: C7 05 54 EB A8 00 0A 00 00 00 mov [0x00A8EB54], 10         ; GrowthStep = 10
   004E6B91: A3 50 EB A8 00        mov [0x00A8EB50], eax   ; Count = 0
   004E6B96: E8 EF 2B 2E 00        call 0x007C978A         ; atexit(0x4E6BA0)
   ```
2. **实体插入与惰性扩容（`0x0043BAD6 - 0x0043BB24`，`BuildingClass::BuildingClass` 构造函数末尾）**：
   ```x86asm
   0043BAD6: A1 48 EB A8 00        mov eax, [0x00A8EB48]   ; eax = VectorMax
   0043BADB: 39 05 50 EB A8 00     cmp [0x00A8EB50], eax   ; Count == VectorMax ?
   0043BAE1: 7C 2C                 jl 0x0043BB0F           ; 容量充足则直接插入
   ...
   0043BAF9: 8B 15 40 EB A8 00     mov edx, [0x00A8EB40]   ; edx = vftable
   0043BAFF: 03 C1                 add eax, ecx            ; eax = VectorMax + 10
   0043BB01: 53                    push ebx
   0043BB02: 50                    push eax
   0043BB03: B9 40 EB A8 00        mov ecx, 0x00A8EB40     ; this = &BuildingClass::Array
   0043BB08: FF 52 08              call dword ptr [edx+8]  ; VectorClass::Resize -> operator new[] 分配堆
   ...
   0043BB0F: 8B 0D 50 EB A8 00     mov ecx, [0x00A8EB50]   ; ecx = Count
   0043BB15: 8B C1                 mov eax, ecx            ; index = Count
   0043BB17: 41                    inc ecx                 ; Count++
   0043BB18: 89 0D 50 EB A8 00     mov [0x00A8EB50], ecx   ; 写回 Count
   0043BB1E: 8B 0D 44 EB A8 00     mov ecx, [0x00A8EB44]   ; ecx = Items (堆指针)
   0043BB24: 89 34 81              mov [ecx + eax*4], esi  ; Items[index] = this (建筑指针)
   ```

---

## 4. (c) `b_valid=false` 在引擎语义上的候选解释与判定依据

根据公式 `b_valid = (b_items != 0 and b <= 100000)`，`b_valid=false` 仅有两种代数可能：`b_items == 0` 或 `b > 100000`。在实跑所有 87 扇窗口中，`b` 的实测取值仅为 `0` 或个位数（`1–6`），**无任何一例 `b > 100000`**。因此所有 `b_valid=false` 均由 `b_items == 0`（且同拍 `b == 0`）引发。

对引擎语义的 4 个候选解释逐一判定如下：

### 候选 C1：`BuildingClass::Array` 容器处于惰性分配未扩容状态（当前地图建筑总数为 0）
- **解释内容**：战局内目前不存在任何 `BuildingClass` 实体。由于 RA2 引擎采用按需惰性扩容设计，`Items` 保持静态初始化的 `NULL`（`0`），`Count` 为 `0`。
- **判定依据**：
  1. **代码逻辑确证**：汇编 `0x004E6B67` 确证静态初始化时 `Items = 0`；`0x0043BAD6` 确证唯有当首栋建筑创建时，才会调用 `Resize` 分配堆空间；
  2. **地图文件确证**：测试所用地图 `XMP29U2.MAP` 解析确认：`[Structures]` 节完全为空（0 行），地图上预置了 3840 辆坦克（`[Units]`）与 2560 名步兵（`[Infantry]`），但**没有预置任何中立或平民建筑物**；
  3. **实体总数守恒确证**：在 `l3_1101v4c` 中，`units=1211, infantry=365, b=0`，加和 `1211 + 365 + 0 = 1576`，精确等于同拍采到的 `techno=1576`（`TechnoClass` 为单位/步兵/飞机的公共基类），说明建筑确实为 0；
  4. **动态翻转实证**：在 `archive_T49_u0800` 的 `w0` 窗内，观测到前序时刻 `b=0, b_items=0, b_valid=False`；中途某一秒随着首栋建筑落成，`b` 变为 1，`b_items` 瞬间被分配堆地址 `272040160`（`0x103A0020`），`b_valid` 同拍翻转为 `True`。
- **裁决**：**成立（唯一真实引擎语义）**。

### 候选 C2：`ReadProcessMemory` 失败 / 进程消亡 / 内存保护阻断
- **解释内容**：目标进程未运行或已崩溃，导致读取失败返回 0。
- **判定依据**：
  1. **Harness 源码逻辑证伪**：`qc151_trip.harness8_v4.py:3998-4001` 明确写明：若 RPM 失败，`b` 或 `b_items` 为 `None`，此时表达式返回 `None`（json 中表现为 `null`），而非布尔值 `False`；
  2. **副读产物证伪**：在所有 `b_valid=false` 的窗口中，`ws_kb`（136MB）和 `pf_kb`（123MB）均平稳产出，`CurrentFrame` 均正常高频推进，表明进程活跃且内存读权限完全正常。
- **裁决**：**排除（反证否定）**。

### 候选 C3：单例未初始化 / 采样窗落在对局外部（生命周期错位）
- **解释内容**：测量窗过早开始，截获在主菜单态或过场加载态。
- **判定依据**：
  1. **帧推进证伪**：`l3_1101v4c` 各窗推进了 463、710、767 个逻辑帧；慢组 `l3_1101v3a` 推进了 290、351、147 帧；
  2. **单位数证伪**：各窗的 `units` 都在 1000–1300 档，且逐秒有交火战损下降（如 v4c w0 从 1211 降至 1092）；
  3. **截图证伪**：落盘的 `frame_early_01.png` 与 `frame_target_01.png` 亲眼可查，战术地图全面铺开，已进入真实对局。
- **裁决**：**排除（反证否定）**。

### 候选 C4：数值越界溢出（`b > 100000`）
- **解释内容**：读到了野指针或引擎发生内部越界。
- **判定依据**：实测 87 窗中，所有 `b_valid=false` 样本的 `b` 全为 `0`，没有大于 100,000 的记录。
- **裁决**：**排除（事实否定）**。

---

## 5. (d) 跨趟确证：`l3_1101v4c` vs `l3_1101v4d` 进程生命周期与因果性判定

### 5.1 启动文件与时间戳核对
查阅两趟产物目录下的 `_launch_result.json`、`qc151_fields.json` 与 `measure_w0.json`：

| 字段 / 维度 | `l3_1101v4c` | `l3_1101v4d` | 判定意义 |
|---|---|---|---|
| **Trip ID** | `QC161-U0800-L3-V4-20261101C` | `QC161-U0800-L3-V4-20261101D` | 独立趟标识 |
| **载具目录 (carrier)** | `ct/c_094343442247_15396` | `ct/c_164711816568_32328` | 全新独立生成的文件载具 |
| **启动时间戳 (ts)** | `2026-11-01T09:43:43+08:00` | `2026-11-01T16:47:11+08:00` | **两者相隔 7 小时 3 分 28 秒** |
| **目标进程 PID** | **`18880`** | **`2820`** | **操作系统分配的不同 PID** |
| **进程创建时间戳** | **`134379710375351078`** | **`134379964434682870`** | **Windows 内核进程对象完全不同** |
| **`measure_w0` t_abs0** | **`1793497532.395`** | **`1793522919.265`** | 墙钟差 25,386.87 秒 |
| **载具清理 (carrier_delete)** | `deleted: true`（09:47:03） | `deleted: true`（16:50:09） | 每趟结束时彻底清理载具与孤儿进程 |
| **残留进程 (leftover_procs)** | `[]` | `[]` | 零进程复用 |

### 5.2 确证结论
1. **两个完全独立的冷启动进程**：`l3_1101v4c` 与 `l3_1101v4d` 绝不是同一次进程内的运行期状态变化，而是相隔 7 个多小时、具有各自全新 carrier 部署、全新 gamemd.exe 进程树的两个独立运行实例。
2. **`b_valid` 从 false 变 true 的真正机制**：
   - 遭遇战（Skirmish）模式下，地图本身无建筑，各 House 只有基地车（MCV）及其护卫；
   - 在 `v4c` 中，因地图预置了 3840 辆重坦与 2560 名步兵产生极端空间拥堵，AI 的基地车在全趟 3 窗（75 秒）内**未能找到空地展开，或在展开前即被消灭**，导致全局建筑数始终为 0，`BuildingClass::Array.Items` 维持 `NULL`，`b_valid` 恒为 `False`；
   - 在 `v4d` 中，AI 基地车成功展开（w0 出现 3 栋建筑，随后递增至 4、5、6 栋），触发了 `BuildingClass::BuildingClass` 构造函数对 `BuildingClass::Array` 的首次 `Resize` 堆内存分配，`b_items` 被填入堆指针 `356815120`，使 `b_valid` 翻转为 `True`。

### 5.3 否定「`b_valid` 是 5.7 倍帧时恶化根因」的铁证
领队在 TASK.md §2 观察到「慢组全 false，快组全 true」的现象，但本分析通过两记反例彻底否定了其因果性：

1. **反例一：`t55k_20261020`（同图 `93c2974b`、842 单位）**
   - 产物路径：`out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/t55k_20261020/measure_w{0,1,2}.json`
   - 实测读数：
     - `w0`: `b=0, b_items=0, b_valid=False`, `frame_ms_p50 = 32.24 ms`, `fps_avg = 31.24`（满帧！）
     - `w1`: `b=0, b_items=0, b_valid=False`, `frame_ms_p50 = 32.37 ms`, `fps_avg = 31.28`（满帧！）
     - `w2`: `b=0, b_items=0, b_valid=False`, `frame_ms_p50 = 32.30 ms`, `fps_avg = 31.24`（满帧！）
   - **结论**：`b_valid=false`（全图 0 建筑）完全可以跑出满帧（31.25 fps）。0 建筑绝对不是引擎慢爬的原因。

2. **反例二：`l3_1101v4c` 趟内的自身加速**
   - 产物路径：`out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w{0,1,2}.json`
   - 实测读数：
     - `w0`: `b_valid=False`, `frame_ms_p50 = 50.48 ms`, `fps_avg = 18.52`
     - `w1`: `b_valid=False`, `frame_ms_p50 = 33.11 ms`, `fps_avg = 28.40`
     - `w2`: `b_valid=False`, `frame_ms_p50 = 32.42 ms`, `fps_avg = 30.68`（推进 767 帧，已接近满帧 31.25！）
   - **结论**：同一对局中，在 `b_valid` 恒为 `False` 的情况下，引擎自发从 18.5 fps 恢复到了 30.7 fps。

**定谳**：`b_valid` 在慢组（v3a/hb/v4c-w0）全 false、快组（v4d/v4e）全 true 的表面分离，纯粹是因为两组在遭遇战中 MCV 展开博弈状态的偶然差异（且建筑本身体量极小，仅 0 栋 vs 3–6 栋，不可能产生 5.7 倍的算力负载差异），**属于典型的伴随伪相关（Spurious Correlation）**。真正的归因中心必须转向 Q2 所述的队伍 AI / 寻路遍历 / 音频视口节流等领域。

---

## 6. 证据索引清单

| 证据项 | 来源路径与位置 | 关键字段 / 关键指令 | 实证结论 |
|---|---|---|---|
| E1 | `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:3839-3840` | `MEASURE_B_VA = 0x00A8EB50`, `MEASURE_B_ITEMS_VA = 0x00A8EB44` | 取值 VA 常量定义 |
| E2 | `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:3979-4001` | `def _rpm_counters`, `"b_valid": ... (b_items != 0 and b <= 100000)` | 取值与有效性判定逻辑 |
| E3 | `ra2youli/gamemd.exe:0x007E9E20` | RTTI COL: `0x801280` -> TypeDescriptor: `0x823270` | 定谳为 `DynamicVectorClass<BuildingClass*>` |
| E4 | `ra2youli/gamemd.exe:0x004E6B60` | `mov [0xa8eb44], 0`, `mov [0xa8eb50], 0`, `mov [0xa8eb40], 0x7e9e24` | 静态构造将 Items 与 Count 初始化为 0 |
| E5 | `ra2youli/gamemd.exe:0x0043BAD6-BB24` | `cmp [0xa8eb50], eax`, `call [edx+8] (Resize)`, `mov [ecx+eax*4], esi` | 首次插入实体时按需分配堆内存 |
| E6 | `out/.../qc161_u0400_trip/_src_L3_sf10c_20261021/XMP29U2.MAP` | `[Structures]` 节（0 条目） vs `[Units]` (3840) + `[Infantry]` (2560) | 地图初始 0 建筑 |
| E7 | `out/.../qc161_u0400_trip/l3_1101v4c/measure_w0.json:counters[0]` | `units: 1211, infantry: 365, b: 0, techno: 1576, b_items: 0` | 实体总数守恒：1211+365=1576 |
| E8 | `out/.../qc161_u0400_trip/l3_1101v4c/_launch_result.json` & `qc151_fields.json` | PID: 18880, 创建时间: 134379710375351078, carrier: `c_094343442247_15396` | v4c 独立冷启动进程 |
| E9 | `out/.../qc161_u0400_trip/l3_1101v4d/_launch_result.json` & `qc151_fields.json` | PID: 2820, 创建时间: 134379964434682870, carrier: `c_164711816568_32328` | v4d 独立冷启动进程（相隔 7.05h） |
| E10 | `out/.../qc161_u0400_trip/t55k_20261020/measure_w0.json` | `b_valid: False, b_items: 0`, `p50: 32.24 ms, fps: 31.24` | 反例否定因果性：0 建筑仍跑满帧 |
| E11 | `out/.../qc161_u0400_trip/l3_1101v4c/measure_w2.json` | `b_valid: False, b_items: 0`, `p50: 32.42 ms, fps: 30.68` | 反例否定因果性：单趟内 0 建筑提速至满帧 |
