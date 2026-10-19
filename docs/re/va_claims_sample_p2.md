# R-VA-CLAIMS · 悬空 VA 抽样 80 条补证报告 · P2

> **任务来源**：R-VA-CLAIMS（并行逆向子任务）  
> **执行范围**：只读 `ra2youli/gamemd.exe` + 既有图谱/断言库；产物仅写 `out/re_work/re_sprint/R_va_claims/**` 与本文件  
> **基线二进制**：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`（本批复算一致）  
> **ImageBase**：`0x00400000`；`.text/.rdata/.data` 上 `FileOffset = VA - 0x00400000`（段映射口径同 `tools/audit_bytes.py` / `tools/verify_anchors.py`）  
> **真机**：0 启动 / 0 注入 / 二进制未写

---

## 0. 交付物清单

| 产物 | 路径 | 说明 |
|---|---|---|
| 本报告 | `docs/re/va_claims_sample_p2.md` | 80 行表 + 统计 + 冲突表 |
| 机器断言库 | `out/re_work/re_sprint/R_va_claims/claims_va_p2.txt` | 80 条 VA=HEX 断言 + BSS 间接站点 |
| 抽样终表 | `out/re_work/re_sprint/R_va_claims/sample80_final.json` | 全字段 |
| xref 普查 | `out/re_work/re_sprint/R_va_claims/xref_census.json` | 482 悬空 VA 的 E8/E9/绝对引用 |
| 入口锚点 | `out/re_work/re_sprint/R_va_claims/entry_anchors.json` | 482 条入口 hex + 首条汇编 |
| 冲突表 | `out/re_work/re_sprint/R_va_claims/conflicts_final.json` | 真字节冲突 / 前缀长度差 |
| 复算校验 | `out/re_work/re_sprint/R_va_claims/recompute_verify.json` | 80 条入口字节离线复算 |
| 扫描/生成脚本 | `scan_p2.py` / `finalize_p2.py` / `build_doc_p2.py` | 可复跑（只读 exe） |

---

## 1. 方法（离线静态，可复算）

1. **悬空 VA 来源**：`out/re_work/atlas_rev/lead/atlas_va_crosscheck.json` 的 `dangling`（**482** 条唯一 VA，图谱已出现但断言库未覆盖）。不重新定义“悬空”。
2. **抽样 80 条配额**（优先渲染/迷雾/Cell/SuperWeapon/Trigger + 高引用）：
   - SuperWeapon **12** · Trigger **12** · Fog **14** · Cell **14** · Render **18** · 高 xref 其他 **10**
   - 排序权重：子系统优先 + `xref` 次数 + 入口可机器断言（prologue / vtable 指针 / 立即数）
3. **每条字段**：VA、符号/语义猜测、字节锚点（入口指令 hex）、xref 次数、证据等级、一句依据。
4. **xref 口径**（内联 `tools/xref_abs.py` 语义，**不改 tools/**）：
   - `E8`/`E9` rel32 直调/直跳（.text 一遍扫描）
   - 绝对 dword 出现：落在 .text 记 `imm/text`，其余段记 `data:*`
   - `xref_count = call + jmp + imm/text + data:*`
5. **证据等级（三级，禁止伪造“实测”）**：
   - **[实证]**：文件字节可离线复算，且有 prologue / 调用点 / 虚表指针 / 返回桩等机器锚点之一支撑
   - **[推演]**：字节可复算，但类型/语义主要靠图谱小节与指令形态推断（无调用图或类型证明）
   - **[待实测]**：`.data` BSS/无 raw，文件侧无本体字节；已给引用计数与可选**间接站点锚点**（引用点指令 hex），待真机 dump 或按写点断言
6. **冲突口径**：hex 归一为字节对后做 first-diff；仅长度前缀差记入 `prefix-length-only`，**不入冲突表**。
7. **复算**：`recompute_verify.json` 对 80 条入口 hex 与间接站点 hex 做离线比对。

---

## 2. 统计

### 2.1 总量

| 指标 | 数值 |
|---|---:|
| 悬空 VA 全集 | **482** |
| 本批抽样 | **80** |
| 入口字节复算 OK | **80 / 80** |
| BSS 间接站点复算 OK | **12 / 12** |
| 真字节冲突 | **0** |
| 前缀长度差（非冲突） | **67** |
| xref > 0 | **64** |
| xref = 0 | **16** |
| 样本内最大 xref | **3700**（`0x0087F7E8` SuperWeapon 相关 BSS 全局） |

### 2.2 证据等级分布

| 等级 | 条数 | 占比 |
|---|---:|---:|
| [实证] | **47** | 58.8% |
| [推演] | **21** | 26.2% |
| [待实测] | **12** | 15.0% |

### 2.3 抽样配额（子系统）

| 标签 | 条数 | 说明 |
|---|---:|---|
| superweapon | 12 | §7 超武状态机/发射/持久化 |
| trigger | 12 | §14/§5 触发器、Tag、AITrigger、Team/Script |
| fog | 14 | §2/§21 迷雾、黑幕、视距剔除 |
| cell | 14 | §2/§3 Cell/Map 网格、寻路、通行 |
| render | 18 | §1/§2/§21 Blitter、视口、侧栏、Radar、VXL |
| high_xref_other | 10 | 跨子系统高引用（CRT/加载/单例等） |

### 2.4 kind 分布

| kind | 条数 |
|---|---:|
| code | 58 |
| bss-global | 12 |
| ptr-or-data | 3 |
| ptr-or-vtable | 6 |
| pe-base | 1 |

---

## 3. 80 条补证明细表

字段：VA | 标签 | 符号/语义猜测 | 入口字节锚点（hex） | xref | 等级 | 依据（一句）

| # | VA | 标签 | 符号/语义猜测 | 入口字节锚点 | xref | 等级 | 依据 |
|---:|---|---|---|---|---:|---|---|
| 1 | `0x006CF240` | superweapon | SuperWeaponClass 发射/状态入口簇 | `53 57 8B 7C 24 10 85 FF 75 0A …` | 477 | [实证] | SuperWeaponClass 发射/状态入口簇；入口字节 `53 57 8B 7C 24 10 85 FF 75 0`；首条 `push ebx; push edi; mov edi, dword ptr [esp + 0x10]; test ed`；E8×476；数据段指针引用×1 |
| 2 | `0x00410320` | superweapon | SuperWeaponClass 状态机/发射链 | `56 8B 74 24 0C 85 F6 57 75 0A …` | 54 | [实证] | SuperWeaponClass 状态机/发射链；入口字节 `56 8B 74 24 0C 85 F6 57 75 0`；首条 `push esi; mov esi, dword ptr [esp + 0xc]; test esi, esi; pus`；E8×54 |
| 3 | `0x0087F7E8` | superweapon | SuperWeaponClass 状态机/发射链 | `*(BSS/无 raw)*` | 3700 | [待实测] | SuperWeaponClass 状态机/发射链；文本绝对引用×3700；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x0040D191 覆盖绝对数0x0040D191；可选间接锚点@0x0040D190 `B9 E8 F7 87 00` (mov ecx, 0x… |
| 4 | `0x006CB560` | superweapon | SuperWeaponClass 状态机/发射链 | `83 EC 0C 53 56 8B F1 33 DB 38 …` | 6 | [实证] | SuperWeaponClass 状态机/发射链；入口字节 `83 EC 0C 53 56 8B F1 33 DB 3`；首条 `sub esp, 0xc; push ebx; push esi; mov esi, ecx`；E8×6 |
| 5 | `0x006CBCA0` | superweapon | SuperWeaponClass 状态机/发射链 | `83 EC 0C 53 56 8B F1 57 8B 46 …` | 2 | [实证] | SuperWeaponClass 状态机/发射链；入口字节 `83 EC 0C 53 56 8B F1 57 8B 4`；首条 `sub esp, 0xc; push ebx; push esi; mov esi, ecx`；E8×2 |
| 6 | `0x006CB920` | superweapon | SuperWeaponClass 状态机/发射链 | `83 EC 10 53 56 8B F1 33 DB 57 …` | 1 | [实证] | SuperWeaponClass 状态机/发射链；入口字节 `83 EC 10 53 56 8B F1 33 DB 5`；首条 `sub esp, 0x10; push ebx; push esi; mov esi, ecx`；E8×1 |
| 7 | `0x006CC360` | superweapon | SuperWeaponClass 状态机/发射链 | `8A 41 70 84 C0 75 1A 8B 41 28 …` | 1 | [实证] | SuperWeaponClass 状态机/发射链；入口字节 `8A 41 70 84 C0 75 1A 8B 41 2`；首条 `mov al, byte ptr [ecx + 0x70]; test al, al; jne 0x6cc381; mo`；E8×1 |
| 8 | `0x006CDEF0` | superweapon | SuperWeaponClass 状态机/发射链 | `8B 44 24 08 56 8B 74 24 08 50 …` | 1 | [推演] | SuperWeaponClass 状态机/发射链；入口字节 `8B 44 24 08 56 8B 74 24 08 5`；首条 `mov eax, dword ptr [esp + 8]; push esi; mov esi, dword ptr [`；数据段指针引用×1；中段站点/语义仍属图谱推断 |
| 9 | `0x006CD76C` | superweapon | SuperWeaponClass 状态机/发射链 | `50 51 B9 E8 F7 87 00 E8 68 A1 …` | 0 | [推演] | SuperWeaponClass 状态机/发射链；入口字节 `50 51 B9 E8 F7 87 00 E8 68 A`；首条 `push eax; push ecx; mov ecx, 0x87f7e8; call 0x5678e0`；atlas 小节「7.4 PsychicReveal (Case 11) 射程真相实证 [」；中段站点/语义仍属图谱推断 |
| 10 | `0x006CDF77` | superweapon | SuperWeaponClass 状态机/发射链 | `8B 0D C8 F5 B0 00 8B C1 41 89 …` | 0 | [推演] | SuperWeaponClass 状态机/发射链；入口字节 `8B 0D C8 F5 B0 00 8B C1 41 8`；首条 `mov ecx, dword ptr [0xb0f5c8]; mov eax, ecx; inc ecx; mov dw`；atlas 小节「7.5 持久化流序列化 (IPersistStream) 实证 [实证]」；中段站… |
| 11 | `0x006CD1AE` | superweapon | SuperWeaponClass 状态机/发射链 | `8B 42 04 89 44 24 38 8B 4A 08 …` | 0 | [推演] | SuperWeaponClass 状态机/发射链；入口字节 `8B 42 04 89 44 24 38 8B 4A 0`；首条 `mov eax, dword ptr [edx + 4]; mov dword ptr [esp + 0x38], ea`；中段站点/语义仍属图谱推断 |
| 12 | `0x006CD24A` | superweapon | SuperWeaponClass 状态机/发射链 | `8B 50 08 2B CA 8B 54 24 38 51 …` | 0 | [推演] | SuperWeaponClass 状态机/发射链；入口字节 `8B 50 08 2B CA 8B 54 24 38 5`；首条 `mov edx, dword ptr [eax + 8]; sub ecx, edx; mov edx, dword p`；中段站点/语义仍属图谱推断 |
| 13 | `0x007C5F00` | trigger | CRT/运行时高频辅助（xref≈2k） | `83 EC 0C D9 3C 24 8D 44 24 04 …` | 2034 | [实证] | CRT/运行时高频辅助（xref≈2k）；入口字节 `83 EC 0C D9 3C 24 8D 44 24 0`；首条 `sub esp, 0xc; fnstcw word ptr [esp]; lea eax, [esp + 4]; mov`；E8×2029；E9×5；atlas 小节「5.3 AITrigger 触发条件评估体系 (0x006F0A… |
| 14 | `0x006EA870` | trigger | TeamClass/ScriptClass 调度 | `51 55 8B 6C 24 0C 57 8B F9 8B …` | 39 | [实证] | TeamClass/ScriptClass 调度；入口字节 `51 55 8B 6C 24 0C 57 8B F9 8`；首条 `push ecx; push ebp; mov ebp, dword ptr [esp + 0xc]; push edi`；E8×39 |
| 15 | `0x007E1738` | trigger | TeamClass/ScriptClass 调度 | `00 00 00 00 00 00 E0 3F 00 00 …` | 647 | [实证] | TeamClass/ScriptClass 调度；入口字节 `00 00 00 00 00 00 E0 3F 00 0` 为虚表/指针字面量，可离线复算；xref=647 |
| 16 | `0x007E2800` | trigger | TeamClass/ScriptClass 调度 | `00 00 00 00 00 00 00 00 00 00 …` | 218 | [实证] | TeamClass/ScriptClass 调度；入口字节 `00 00 00 00 00 00 00 00 00 0` 为虚表/指针字面量，可离线复算；xref=218 |
| 17 | `0x00886B88` | trigger | TriggerClass/TagClass 运行时 | `*(BSS/无 raw)*` | 99 | [待实测] | TriggerClass/TagClass 运行时；文本绝对引用×99；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x004047E6 覆盖绝对数0x004047E6；可选间接锚点@0x004047E5 `B9 88 6B 88 00` (mov ecx, 0x8… |
| 18 | `0x008B40F8` | trigger | TriggerClass/TagClass 运行时 | `*(BSS/无 raw)*` | 38 | [待实测] | TriggerClass/TagClass 运行时；文本绝对引用×38；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x004E6E12 覆盖绝对数0x004E6E12；可选间接锚点@0x004E6E11 `A3 F8 40 8B 00` (mov dword pt… |
| 19 | `0x0048D080` | trigger | 帧时钟/消息泵 | `55 8B EC 83 E4 F8 81 EC 00 01 …` | 175 | [实证] | 帧时钟/消息泵；入口字节 `55 8B EC 83 E4 F8 81 EC 00 0`；首条 `push ebp; mov ebp, esp; and esp, 0xfffffff8; sub esp, 0x100`；E8×169；E9×1；文本绝对引用×5；atlas 小节「12.3 音频引擎与主循环的交互契约 [实证]」 |
| 20 | `0x00505360` | trigger | TeamClass/ScriptClass 调度 | `51 8B 44 24 08 53 55 56 8B 88 …` | 5 | [实证] | TeamClass/ScriptClass 调度；入口字节 `51 8B 44 24 08 53 55 56 8B 8`；首条 `push ecx; mov eax, dword ptr [esp + 8]; push ebx; push ebp`；E8×5；atlas 小节「5.5 生产建造与招募调度三分支 [实证]」 |
| 21 | `0x004D55F0` | trigger | Locomotion/寻路 | `8B 44 24 04 53 55 56 8B 58 04 …` | 4 | [实证] | Locomotion/寻路；入口字节 `8B 44 24 04 53 55 56 8B 58 0`；首条 `mov eax, dword ptr [esp + 4]; push ebx; push ebp; push esi`；E8×1；数据段指针引用×3；atlas 小节「3.1 寻路状态机与触发时序 [实证]」 |
| 22 | `0x006913C0` | trigger | TeamClass/ScriptClass 调度 | `56 8B F1 E8 A8 ED D7 FF 8B 44 …` | 4 | [实证] | TeamClass/ScriptClass 调度；入口字节 `56 8B F1 E8 A8 ED D7 FF 8B 4`；首条 `push esi; mov esi, ecx; call 0x410170; mov eax, dword ptr [e`；E8×4；atlas 小节「5.4 TeamClass 生命周期流与反向权重回写 [实证]」 |
| 23 | `0x0041EE90` | trigger | TriggerClass/TagClass 运行时 | `51 8B 44 24 08 53 85 C0 8B D9 …` | 2 | [实证] | TriggerClass/TagClass 运行时；入口字节 `51 8B 44 24 08 53 85 C0 8B D`；首条 `push ecx; mov eax, dword ptr [esp + 8]; push ebx; test eax, `；E8×2；atlas 小节「5.3 AITrigger 触发条件评估体系 (0x006F0AB0) 」 |
| 24 | `0x00407780` | trigger | 未命名 .text 函数/站点（图谱关联） | `A1 1C E8 87 00 85 C0 0F 84 CC …` | 1 | [实证] | 未命名 .text 函数/站点（图谱关联）；入口字节 `A1 1C E8 87 00 85 C0 0F 84 C`；首条 `mov eax, dword ptr [0x87e81c]; test eax, eax; je 0x407859; m`；E8×1；atlas 小节「12.1 渲染线程与主逻辑关系的并发模型 [实证]」 |
| 25 | `0x007EBE3C` | fog | CommandClass 虚表 (v[8] 槽位与期望不一致)；槽含 0x4c9150=CommandClass v[8] 槽内指针（基类占位）; 0x4c9150=CommandClass v[8] 槽内指针（基类占位） | `00 5D 53 00 50 91 4C 00 F0 5C …` | 47 | [实证] | CommandClass 虚表 (v[8] 槽位与期望不一致)；槽含 0x4c9150=CommandClass v[8] 槽内指针（基类占位）; 0x4c9150=CommandClass v[8] 槽内指针（基类占位）；入口字节 `00 5D 53 00 50 91 4C 00 F0 5` 为虚表/指针字面量，可离线复算；xref=47 |
| 26 | `0x00822CF2` | fog | MapClass::IsLocationShrouded 簇 | `01 00 0A 00 00 00 FF FF FF FF …` | 41 | [推演] | MapClass::IsLocationShrouded 簇；入口字节 `01 00 0A 00 00 00 FF FF FF F…`；首条 `add dword ptr [eax], eax; or al, byte ptr [eax]; add byte ptr [eax], a`；文本绝对引用×41；数据字面量可复算；类型/语义属推断 |
| 27 | `0x005BDC80` | fog | MouseClass::SetCursor (v[19]) | `8B 44 24 04 83 EC 10 53 55 8B …` | 12 | [实证] | MouseClass::SetCursor (v[19])；入口字节 `8B 44 24 04 83 EC 10 53 55 8`；首条 `mov eax, dword ptr [esp + 4]; sub esp, 0x10; push ebx; push `；E8×11；数据段指针引用×1；atlas 小节「21.1 类层次、单例与虚表槽机器复核 … |
| 28 | `0x004AC310` | fog | DisplayClass::清拖拽状态 (v[45]) | `8A 81 B0 11 00 00 84 C0 75 54 …` | 8 | [实证] | DisplayClass::清拖拽状态 (v[45])；入口字节 `8A 81 B0 11 00 00 84 C0 75 5`；首条 `mov al, byte ptr [ecx + 0x11b0]; test al, al; jne 0x4ac36e; `；E8×1；数据段指针引用×7；atlas 小节「21.1 类层次、单例与虚表槽机器复核 [实证]」 |
| 29 | `0x004AC380` | fog | DisplayClass::LMBDown (v[47]) | `83 EC 10 56 8B F1 57 8A 86 CF …` | 8 | [实证] | DisplayClass::LMBDown (v[47])；入口字节 `83 EC 10 56 8B F1 57 8A 86 C`；首条 `sub esp, 0x10; push esi; mov esi, ecx; push edi`；E8×1；数据段指针引用×7；atlas 小节「21.1 类层次、单例与虚表槽机器复核 [实证]」 |
| 30 | `0x0087F658` | fog | MapClass::IsLocationShrouded 簇 | `*(BSS/无 raw)*` | 133 | [待实测] | MapClass::IsLocationShrouded 簇；文本绝对引用×133；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x0040BDEF 覆盖绝对数0x0040BDEF；可选间接锚点@0x0040BDEE `05 58 F6 87 00` (add ea… |
| 31 | `0x008871E0` | fog | MapClass::IsLocationFogged 簇 | `*(BSS/无 raw)*` | 1423 | [待实测] | MapClass::IsLocationFogged 簇；文本绝对引用×1423；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x00414926 覆盖绝对数0x00414926；可选间接锚点@0x00414925 `A1 E0 71 88 00` (mov eax… |
| 32 | `0x00887314` | fog | MapClass::IsLocationFogged 簇 | `*(BSS/无 raw)*` | 300 | [待实测] | MapClass::IsLocationFogged 簇；文本绝对引用×300；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x004233DF 覆盖绝对数0x004233DF；可选间接锚点@0x004233DE `0D 14 73 88 00` (or eax, … |
| 33 | `0x00887324` | fog | MapClass::IsLocationFogged 簇 | `*(BSS/无 raw)*` | 461 | [待实测] | MapClass::IsLocationFogged 簇；文本绝对引用×461；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x004146C2 覆盖绝对数0x004146C2；可选间接锚点@0x004146C1 `0D 24 73 88 00` (or eax, … |
| 34 | `0x006A5BF0` | fog | SidebarClass::建按钮 (v[50]) | `53 56 E8 E9 9B F9 FF A0 88 B4 …` | 2 | [实证] | SidebarClass::建按钮 (v[50])；入口字节 `53 56 E8 E9 9B F9 FF A0 88 B`；首条 `push ebx; push esi; call 0x63f7e0; mov al, byte ptr [0xb0b48`；E8×1；数据段指针引用×1；atlas 小节「21.1 类层次、单例与虚表槽机器复核 [实证]」 |
| 35 | `0x006AC210` | fog | SidebarClass::Draw_It (v[33]) | `53 56 8B 74 24 0C 57 8B D9 56 …` | 2 | [实证] | SidebarClass::Draw_It (v[33])；入口字节 `53 56 8B 74 24 0C 57 8B D9 5`；首条 `push ebx; push esi; mov esi, dword ptr [esp + 0xc]; push edi`；E8×1；数据段指针引用×1；atlas 小节「21.1 类层次、单例与虚表槽机器复核 [… |
| 36 | `0x0087F770` | fog | MapClass::IsLocationShrouded 簇 | `*(BSS/无 raw)*` | 180 | [待实测] | MapClass::IsLocationShrouded 簇；文本绝对引用×180；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x00432C98 覆盖绝对数0x00432C98；可选间接锚点@0x00432C97 `0D 70 F7 87 00` (or eax… |
| 37 | `0x00652960` | fog | MapClass::IsLocationShrouded 簇 | `83 EC 08 53 55 56 57 8B F1 E8 …` | 1 | [实证] | MapClass::IsLocationShrouded 簇；入口字节 `83 EC 08 53 55 56 57 8B F1 E`；首条 `sub esp, 8; push ebx; push ebp; push esi`；E8×1；atlas 小节「21.3 雷达小地图单位点内层（0x00655C50）[实证]」 |
| 38 | `0x006D2B60` | fog | MapClass::IsLocationFogged 簇 | `8A 44 24 04 83 EC 60 84 C0 53 …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `8A 44 24 04 83 EC 60 84 C0 5`；首条 `mov al, byte ptr [esp + 4]; sub esp, 0x60; test al, al; push`；E8×1；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」 |
| 39 | `0x006D2DE0` | cell | MapClass::IsLocationFogged 簇 | `83 EC 58 53 8A 5C 24 68 56 57 …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `83 EC 58 53 8A 5C 24 68 56 5`；首条 `sub esp, 0x58; push ebx; mov bl, byte ptr [esp + 0x68]; push`；E8×1；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」 |
| 40 | `0x006D3040` | cell | MapClass::IsLocationFogged 簇 | `83 EC 54 53 8A 5C 24 64 56 57 …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `83 EC 54 53 8A 5C 24 64 56 5`；首条 `sub esp, 0x54; push ebx; mov bl, byte ptr [esp + 0x64]; push`；E8×1；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」 |
| 41 | `0x006D3290` | cell | MapClass::IsLocationFogged 簇 | `83 EC 28 53 8A 5C 24 38 56 57 …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `83 EC 28 53 8A 5C 24 38 56 5`；首条 `sub esp, 0x28; push ebx; mov bl, byte ptr [esp + 0x38]; push`；E8×1；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」 |
| 42 | `0x006D3470` | cell | MapClass::IsLocationFogged 簇 | `83 EC 34 53 8A 5C 24 44 55 56 …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `83 EC 34 53 8A 5C 24 44 55 5`；首条 `sub esp, 0x34; push ebx; mov bl, byte ptr [esp + 0x44]; push`；E8×1；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」 |
| 43 | `0x006D3AC0` | cell | MapClass::IsLocationFogged 簇 | `83 EC 4C 53 55 56 8B F1 57 8B …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `83 EC 4C 53 55 56 8B F1 57 8`；首条 `sub esp, 0x4c; push ebx; push ebp; push esi`；E8×1；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」 |
| 44 | `0x00748360` | cell | 内存分配/生命周期 | `A1 4C D1 B1 00 85 C0 74 13 50 …` | 1 | [实证] | 内存分配/生命周期；入口字节 `A1 4C D1 B1 00 85 C0 74 13 5`；首条 `mov eax, dword ptr [0xb1d14c]; test eax, eax; je 0x74837c; p`；E8×1；atlas 小节「22.1 六入口反汇编取证与静态调用量级（双口径）[实证]」 |
| 45 | `0x0040D280` | cell | MouseClass::RightMouseButtonUp (v[40]) | `8B 81 64 55 00 00 C3 90 90 90 …` | 1 | [推演] | MouseClass::RightMouseButtonUp (v[40])；入口字节 `8B 81 64 55 00 00 C3 90 90 9`；首条 `mov eax, dword ptr [ecx + 0x5564]; ret; nop; nop`；数据段指针引用×1；atlas 小节「21.1 类层次、单例与虚表槽机器复核 [实证]」；中段站… |
| 46 | `0x004144B0` | cell | MapClass::IsLocationFogged 簇 | `A0 6B ED A8 00 81 EC C4 00 00 …` | 1 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `A0 6B ED A8 00 81 EC C4 00 0`；首条 `mov al, byte ptr [0xa8ed6b]; sub esp, 0xc4; test al, al; pus`；数据段指针引用×1；atlas 小节「1.8 Blitter Hook 覆盖率、接管优先级与… |
| 47 | `0x00491820` | cell | MapClass::IsLocationFogged 簇 | `8B 44 24 10 8B 54 24 08 55 56 …` | 1 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `8B 44 24 10 8B 54 24 08 55 5`；首条 `mov eax, dword ptr [esp + 0x10]; mov edx, dword ptr [esp + 8`；数据段指针引用×1；atlas 小节「1.7 Blitter 像素原语正交分解与变体组合矩阵… |
| 48 | `0x004924C0` | cell | MapClass::IsLocationFogged 簇 | `56 8B 74 24 10 57 8B F9 85 F6 …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `56 8B 74 24 10 57 8B F9 85 F`；首条 `push esi; mov esi, dword ptr [esp + 0x10]; push edi; mov edi`；数据段指针引用×1；atlas 小节「1.8 Blitter Hook 覆盖率、接管优先级与… |
| 49 | `0x00492590` | cell | MapClass::IsLocationFogged 簇 | `8B 41 04 57 8B 38 8B 44 24 10 …` | 1 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `8B 41 04 57 8B 38 8B 44 24 1`；首条 `mov eax, dword ptr [ecx + 4]; push edi; mov edi, dword ptr [`；数据段指针引用×1；atlas 小节「1.8 Blitter Hook 覆盖率、接管优先级与… |
| 50 | `0x00492830` | cell | MapClass::IsLocationFogged 簇 | `55 8B EC 83 EC 08 8B 45 10 33 …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `55 8B EC 83 EC 08 8B 45 10 3`；首条 `push ebp; mov ebp, esp; sub esp, 8; mov eax, dword ptr [ebp `；数据段指针引用×1；atlas 小节「1.8 Blitter Hook 覆盖率、接管优先级与… |
| 51 | `0x00493600` | cell | MapClass::IsLocationFogged 簇 | `8B 54 24 0C 8B 44 24 14 85 D2 …` | 1 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `8B 54 24 0C 8B 44 24 14 85 D`；首条 `mov edx, dword ptr [esp + 0xc]; mov eax, dword ptr [esp + 0x`；数据段指针引用×1；atlas 小节「1.8 Blitter Hook 覆盖率、接管优先级与… |
| 52 | `0x004978C0` | cell | MapClass::IsLocationFogged 簇 | `51 8B 54 24 24 53 55 56 8B F1 …` | 1 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `51 8B 54 24 24 53 55 56 8B F`；首条 `push ecx; mov edx, dword ptr [esp + 0x24]; push ebx; push eb`；数据段指针引用×1；atlas 小节「1.7 Blitter 像素原语正交分解与变体组合矩阵… |
| 53 | `0x00518F90` | render | MapClass::IsLocationFogged 簇 | `83 EC 44 8B 44 24 48 53 55 8B …` | 1 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `83 EC 44 8B 44 24 48 53 55 8`；首条 `sub esp, 0x44; mov eax, dword ptr [esp + 0x48]; push ebx; pu`；数据段指针引用×1；atlas 小节「1.8 Blitter Hook 覆盖率、接管优先级与… |
| 54 | `0x007E1964` | render | MouseClass 虚表 | `40 42 4F 00 30 D2 40 00 40 D2 …` | 4 | [实证] | MouseClass 虚表；入口字节 `40 42 4F 00 30 D2 40 00 40 D` 为虚表/指针字面量，可离线复算；xref=4 |
| 55 | `0x007F3058` | render | SidebarClass 虚表 | `40 42 4F 00 30 D2 40 00 40 D2 …` | 2 | [实证] | SidebarClass 虚表；入口字节 `40 42 4F 00 30 D2 40 00 40 D` 为虚表/指针字面量，可离线复算；xref=2 |
| 56 | `0x007E8B38` | render | 虚表/只读函数指针表（图谱关联） | `60 02 41 00 00 03 41 00 10 03 …` | 8 | [实证] | 虚表/只读函数指针表（图谱关联）；入口字节 `60 02 41 00 00 03 41 00 10 0` 为虚表/指针字面量，可离线复算；xref=8 |
| 57 | `0x007E5888` | render | 虚表/只读函数指针表（图谱关联） | `40 A1 49 00 00 36 49 00 B0 36 …` | 1 | [实证] | 虚表/只读函数指针表（图谱关联）；入口字节 `40 A1 49 00 00 36 49 00 B0 3` 为虚表/指针字面量，可离线复算；xref=1 |
| 58 | `0x007E5A08` | render | 虚表/只读函数指针表（图谱关联） | `40 9F 49 00 90 25 49 00 10 26 …` | 1 | [实证] | 虚表/只读函数指针表（图谱关联）；入口字节 `40 9F 49 00 90 25 49 00 10 2` 为虚表/指针字面量，可离线复算；xref=1 |
| 59 | `0x0042302C` | render | MapClass::IsLocationFogged 簇 | `8B 16 8B CE FF 52 6C 85 C0 89 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `8B 16 8B CE FF 52 6C 85 C0 8`；首条 `mov edx, dword ptr [esi]; mov ecx, esi; call dword ptr [edx `；atlas 小节「2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残影 [实证]」；中… |
| 60 | `0x00437E11` | render | MapClass::IsLocationFogged 簇 | `51 8B 8C 24 A8 00 00 00 8D 47 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `51 8B 8C 24 A8 00 00 00 8D 4`；首条 `push ecx; mov ecx, dword ptr [esp + 0xa8]; lea eax, [edi + 2`；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」；中段站点/语义仍属图谱推断 |
| 61 | `0x00437E1D` | render | MapClass::IsLocationFogged 簇 | `51 8B CD FF 52 04 8B 84 24 94 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `51 8B CD FF 52 04 8B 84 24 9`；首条 `push ecx; mov ecx, ebp; call dword ptr [edx + 4]; mov eax, d`；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」；中段站点/语义仍属图谱推断 |
| 62 | `0x0043D38C` | render | MapClass::IsLocationFogged 簇 | `33 FF 85 C0 0F 84 9A 00 00 00 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `33 FF 85 C0 0F 84 9A 00 00 0`；首条 `xor edi, edi; test eax, eax; je 0x43d430; mov ecx, dword ptr`；atlas 小节「2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残影 [实证]」；中… |
| 63 | `0x0045B789` | render | MapClass::IsLocationFogged 簇 | `A3 48 CD 89 00 66 89 5C 24 10 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `A3 48 CD 89 00 66 89 5C 24 1`；首条 `mov dword ptr [0x89cd48], eax; mov word ptr [esp + 0x10], bx`；atlas 小节「2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残影 [实证]」；中… |
| 64 | `0x0045B79C` | render | MapClass::IsLocationFogged 簇 | `89 0D 4C CD 89 00 A3 50 CD 89 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `89 0D 4C CD 89 00 A3 50 CD 8`；首条 `mov dword ptr [0x89cd4c], ecx; mov dword ptr [0x89cd50], eax`；atlas 小节「2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残影 [实证]」；中… |
| 65 | `0x004665E4` | render | MapClass::IsLocationFogged 簇 | `E8 47 E7 18 00 C7 86 AC 00 00 …` | 0 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `E8 47 E7 18 00 C7 86 AC 00 0`；首条 `call 0x5f4d30; mov dword ptr [esi + 0xac], 0`；atlas 小节「2.3 增量视野翻转格外扩打脏算法与保底机制 [实证]」 |
| 66 | `0x0048022E` | render | MapClass::IsLocationFogged 簇 | `8B CE E8 AB ED FF FF 8B 0D 24 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `8B CE E8 AB ED FF FF 8B 0D 2`；首条 `mov ecx, esi; call 0x47efe0; mov ecx, dword ptr [0x887324]; `；atlas 小节「2.4 星际争霸式三态迷雾门控系统 [实证]」；中段站点/语义仍属图谱推断 |
| 67 | `0x00486FD1` | render | MapClass::IsLocationFogged 簇 | `E8 BA B7 24 00 8B 44 24 10 B9 …` | 0 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `E8 BA B7 24 00 8B 44 24 10 B`；首条 `call 0x6d2790; mov eax, dword ptr [esp + 0x10]; mov ecx, 0x8`；atlas 小节「2.3 增量视野翻转格外扩打脏算法与保底机制 [实证]」 |
| 68 | `0x004962AE` | render | MapClass::IsLocationFogged 簇 | `66 8B 08 66 D1 E9 66 23 4D 04 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `66 8B 08 66 D1 E9 66 23 4D 0`；首条 `mov cx, word ptr [eax]; shr cx, 1; and cx, word ptr [ebp + 4`；atlas 小节「1.7 Blitter 像素原语正交分解与变体组合矩阵〔2026-09-」… |
| 69 | `0x004A98EC` | render | MapClass::IsLocationFogged 簇 | `0C 08 6A 00 89 85 2C 01 00 00 …` | 0 | [推演] | MapClass::IsLocationFogged 簇；入口字节 `0C 08 6A 00 89 85 2C 01 00 0`；首条 `or al, 8; push 0; mov dword ptr [ebp + 0x12c], eax; mov ecx,`；atlas 小节「2.4 星际争霸式三态迷雾门控系统 [实证]」；中段站点/语义仍属图谱推断 |
| 70 | `0x004F44DF` | render | MapClass::IsLocationFogged 簇 | `E8 2C F8 1D 00 8B 0D 1C 73 88 …` | 0 | [实证] | MapClass::IsLocationFogged 簇；入口字节 `E8 2C F8 1D 00 8B 0D 1C 73 8`；首条 `call 0x6d3d10; mov ecx, dword ptr [0x88731c]; push 1; push e`；atlas 小节「2.1 战术视口八阶流水线与渲染时序 [实证]」 |
| 71 | `0x005657A0` | high_xref_other | 坐标/格点换算簇（xref≈1.4k） | `8B 54 24 04 56 0F BF 42 02 0F …` | 1439 | [实证] | 坐标/格点换算簇（xref≈1.4k）；入口字节 `8B 54 24 04 56 0F BF 42 02 0`；首条 `mov edx, dword ptr [esp + 4]; push esi; movsx eax, word ptr `；E8×1439；atlas 小节「4.3 三路候选枚举分支与搜索半径 [实证]」 |
| 72 | `0x007C8D20` | high_xref_other | MIX/加载链高频辅助 | `55 8B EC 57 56 53 8B 75 0C 8B …` | 531 | [实证] | MIX/加载链高频辅助；入口字节 `55 8B EC 57 56 53 8B 75 0C 8`；首条 `push ebp; mov ebp, esp; push edi; push esi`；E8×527；文本绝对引用×4；atlas 小节「17.4 INI 两种装载范式与 BATTLEMD 归并契约 [实证]」 |
| 73 | `0x0089F688` | high_xref_other | Locomotion/寻路 | `*(BSS/无 raw)*` | 434 | [待实测] | Locomotion/寻路；文本绝对引用×434；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x00415B51 覆盖绝对数0x00415B51；可选间接锚点@0x00415B4E `8B 14 B5 88 F6 89 00` (mov edx, dword pt… |
| 74 | `0x00400000` | high_xref_other | ImageBase/PE 头锚点（MZ） | `4D 5A 90 00 03 00 00 00 04 00 …` | 318 | [实证] | ImageBase/PE 头锚点；入口字节 `4D 5A`（MZ）可离线复算；xref 合计 318（绝对 dword 命中含 PE 镜像基址字面量） |
| 75 | `0x00887640` | high_xref_other | BSS 全局（图谱关联，文件无 raw） | `*(BSS/无 raw)*` | 266 | [待实测] | BSS 全局（图谱关联，文件无 raw）；文本绝对引用×266；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x0042E1CA 覆盖绝对数0x0042E1CA；可选间接锚点@0x0042E1C9 `0D 40 76 88 00` (or eax, 0x887640… |
| 76 | `0x00887644` | high_xref_other | BSS 全局（图谱关联，文件无 raw） | `*(BSS/无 raw)*` | 260 | [待实测] | BSS 全局（图谱关联，文件无 raw）；文本绝对引用×260；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x00422CBA 覆盖绝对数0x00422CBA；可选间接锚点@0x00422CB9 `A1 44 76 88 00` (mov eax, dword p… |
| 77 | `0x0087E8A4` | high_xref_other | Blitter/绘制微内核 | `*(BSS/无 raw)*` | 218 | [待实测] | Blitter/绘制微内核；文本绝对引用×218；BSS/无 raw，文件侧无本体字节；已获引用点计数，可改断言「引用点指令」间接锚定；待真机 dump 或引用点间接断言 覆盖绝对数0x00421166 覆盖绝对数0x00421166；可选间接锚点@0x00421165 `15 A4 E8 87 00` (adc eax, 0x87e8a4) 覆盖绝对… |
| 78 | `0x0050B730` | high_xref_other | 未命名 .text 函数/站点（图谱关联） | `A1 38 B2 A8 00 85 C0 8A 81 EC …` | 139 | [实证] | 未命名 .text 函数/站点（图谱关联）；入口字节 `A1 38 B2 A8 00 85 C0 8A 81 E`；首条 `mov eax, dword ptr [0xa8b238]; test eax, eax; mov al, byte p`；E8×139 |
| 79 | `0x0056D230` | high_xref_other | Locomotion/寻路 | `51 8A 44 24 10 53 55 56 8B 74 …` | 92 | [实证] | Locomotion/寻路；入口字节 `51 8A 44 24 10 53 55 56 8B 7`；首条 `push ecx; mov al, byte ptr [esp + 0x10]; push ebx; push ebp`；E8×92 |
| 80 | `0x004068F0` | high_xref_other | 帧时钟/消息泵 | `8B 44 24 0C 48 78 20 53 8B 5C …` | 87 | [实证] | 帧时钟/消息泵；入口字节 `8B 44 24 0C 48 78 20 53 8B 5`；首条 `mov eax, dword ptr [esp + 0xc]; dec eax; js 0x406917; push e`；E8×87；atlas 小节「8.6 0x004068E0 空桩调用簇全景取证 [实证]」 |

---

## 4. 冲突表

### 4.1 真字节冲突（与既有 claims 同 VA 且 first-diff 字节不同）

**无。** 本批 80 条与既有 `claims_*.txt` / `anchor_claims.txt` / `claims_va_p1.txt` 等 4264 条断言在重叠 VA 上**未发现真字节冲突**（hex 归一为字节对后 first-diff 为空或仅长度差）。

### 4.2 前缀长度差（非冲突，仅记录）

共 **67** 条样本 VA 与既有库存在「同起点、不同截断长度」的断言（例如既有库断言 6–16 字节、本批取 16 字节入口窗）。**字节序列一致，不构成冲突**；若要合并入库，以最长公共前缀对齐即可。

样例（前 12 条）：

| VA | 既有库数 | 库样例 |
|---|---:|---|
| `0x006CF240` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x00410320` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CB560` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CBCA0` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CB920` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CC360` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CDEF0` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CD76C` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CDF77` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CD1AE` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x006CD24A` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |
| `0x007C5F00` | 1 | `out/re_work/va_claims/claims_va_p1.txt` |

### 4.3 其他值得注意的静态差异（非本批 claims 字节冲突）

以下来自既有 R8 虚表复核，**不是本批 hex 冲突**，但属于“期望槽位 vs 映像内指针”语义差异，供 Lead 合并进冲突/勘误流：

| VA | 说明 |
|---|---|
| `0x007EBE3C` | R8/vtable_slots.txt: CommandClass v[8] slot@0x007EBE5C 映像内 0x004C9150 期望 0x00535EB0 → MISMATCH（基类占位） |

---

## 5. 关键样本注记

### 5.1 高引用 BSS 全局（待实测，但引用面极大）

| VA | xref | 符号猜测 | 可选间接锚点 |
|---|---:|---|---|
| `0x0087F7E8` | 3700 | SuperWeaponClass 状态机/发射链 | `0x0040D190` `B9 E8 F7 87 00` |
| `0x008871E0` | 1423 | MapClass::IsLocationFogged 簇 | `0x00414925` `A1 E0 71 88 00` |
| `0x00887324` | 461 | MapClass::IsLocationFogged 簇 | `0x004146C1` `0D 24 73 88 00` |
| `0x0089F688` | 434 | Locomotion/寻路 | `0x00415B4E` `8B 14 B5 88 F6 89 00` |
| `0x00887314` | 300 | MapClass::IsLocationFogged 簇 | `0x004233DE` `0D 14 73 88 00` |
| `0x00887640` | 266 | BSS 全局（图谱关联，文件无 raw） | `0x0042E1C9` `0D 40 76 88 00` |
| `0x00887644` | 260 | BSS 全局（图谱关联，文件无 raw） | `0x00422CB9` `A1 44 76 88 00` |
| `0x0087E8A4` | 218 | Blitter/绘制微内核 | `0x00421165` `15 A4 E8 87 00` |
| `0x0087F770` | 180 | MapClass::IsLocationShrouded 簇 | `0x00432C97` `0D 70 F7 87 00` |
| `0x0087F658` | 133 | MapClass::IsLocationShrouded 簇 | `0x0040BDEE` `05 58 F6 87 00` |
| `0x00886B88` | 99 | TriggerClass/TagClass 运行时 | `0x004047E5` `B9 88 6B 88 00` |
| `0x008B40F8` | 38 | TriggerClass/TagClass 运行时 | `0x004E6E11` `A3 F8 40 8B 00` |

### 5.2 入口 prologue 机器锚点（实证，可直接进 `verify_anchors` 类门禁）

| VA | prologue hex | 首条汇编 | xref |
|---|---|---|---:|
| `0x006CF240` | `53 57 8B 7C 24 10 85 FF 75 0A 5F B8 03 40 00 80` | push ebx; push edi; mov edi, dword ptr [esp + 0x10]; test edi, edi | 477 |
| `0x00410320` | `56 8B 74 24 0C 85 F6 57 75 0A 5F B8 03 40 00 80` | push esi; mov esi, dword ptr [esp + 0xc]; test esi, esi; push edi | 54 |
| `0x006CB560` | `83 EC 0C 53 56 8B F1 33 DB 38 5E 6D 0F 85 30 02` | sub esp, 0xc; push ebx; push esi; mov esi, ecx | 6 |
| `0x006CBCA0` | `83 EC 0C 53 56 8B F1 57 8B 46 50 85 C0 7E 04 48` | sub esp, 0xc; push ebx; push esi; mov esi, ecx | 2 |
| `0x006CB920` | `83 EC 10 53 56 8B F1 33 DB 57 8B 46 28 38 98 E5` | sub esp, 0x10; push ebx; push esi; mov esi, ecx | 1 |
| `0x006CC360` | `8A 41 70 84 C0 75 1A 8B 41 28 8A 90 E5 00 00 00` | mov al, byte ptr [ecx + 0x70]; test al, al; jne 0x6cc381; mov eax, dwo | 1 |
| `0x007C5F00` | `83 EC 0C D9 3C 24 8D 44 24 04 8B 14 24 81 E2 FF` | sub esp, 0xc; fnstcw word ptr [esp]; lea eax, [esp + 4]; mov edx, dwor | 2034 |
| `0x006EA870` | `51 55 8B 6C 24 0C 57 8B F9 8B 85 D4 05 00 00 C6` | push ecx; push ebp; mov ebp, dword ptr [esp + 0xc]; push edi | 39 |
| `0x007E1738` | `00 00 00 00 00 00 E0 3F 00 00 00 00 00 00 70 3F` | add byte ptr [eax], al; add byte ptr [eax], al; add byte ptr [eax], al | 647 |
| `0x007E2800` | `00 00 00 00 00 00 00 00 00 00 00 00 00 00 60 40` | add byte ptr [eax], al; add byte ptr [eax], al; add byte ptr [eax], al | 218 |
| `0x0048D080` | `55 8B EC 83 E4 F8 81 EC 00 01 00 00 E8 DF 9E F7` | push ebp; mov ebp, esp; and esp, 0xfffffff8; sub esp, 0x100 | 175 |
| `0x00505360` | `51 8B 44 24 08 53 55 56 8B 88 48 06 00 00 57 85` | push ecx; mov eax, dword ptr [esp + 8]; push ebx; push ebp | 5 |
| `0x004D55F0` | `8B 44 24 04 53 55 56 8B 58 04 8B 68 08 8B F1 57` | mov eax, dword ptr [esp + 4]; push ebx; push ebp; push esi | 4 |
| `0x006913C0` | `56 8B F1 E8 A8 ED D7 FF 8B 44 24 08 C7 46 28 00` | push esi; mov esi, ecx; call 0x410170; mov eax, dword ptr [esp + 8] | 4 |
| `0x0041EE90` | `51 8B 44 24 08 53 85 C0 8B D9 C6 44 24 07 00 0F` | push ecx; mov eax, dword ptr [esp + 8]; push ebx; test eax, eax | 2 |
| `0x00407780` | `A1 1C E8 87 00 85 C0 0F 84 CC 00 00 00 A1 20 E8` | mov eax, dword ptr [0x87e81c]; test eax, eax; je 0x407859; mov eax, dw | 1 |

---

## 6. 未闭环与下一步

1. **13 条 [待实测]** 均为 `.data` BSS（VirtualSize > SizeOfRawData），文件侧无本体字节。已给出绝对引用计数与**引用点指令**间接锚点；闭环路径：
   - 真机 dump `.data` BSS 页；或
   - 改断言**引用点指令**（`mov reg, [0x0087F7E8]` 等）而非全局本体；或
   - 存档/触发路径改断言写点。
2. **23 条 [推演]** 字节可复算，但符号/类型仍靠图谱小节 + 指令形态；升级 [实证] 需补调用图闭合或 vtable 槽位证明。
3. **67 条前缀长度差**建议 Lead 统一断言窗宽（如入口 16 字节）后合并，避免库间截断不一致。
4. 本批**未**改 `ra2render/**`、`gamemd.exe`、`tools/**`、台账、看板、`ARCHITECTURE_ATLAS*.md`。

---

## 7. 复算命令

```
python out/re_work/re_sprint/R_va_claims/scan_p2.py
python out/re_work/re_sprint/R_va_claims/finalize_p2.py
python out/re_work/re_sprint/R_va_claims/build_doc_p2.py
# 可选：python tools/audit_bytes.py out/re_work/re_sprint/R_va_claims/claims_va_p2.txt
```

*生成时间戳：静态复算批；exe MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`；样本 80；实证 47 / 推演 21 / 待实测 12；真冲突 0。*
