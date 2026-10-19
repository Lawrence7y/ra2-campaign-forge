# 六大落地补丁包 P-1～P-6 落地前静态一致性复核报告
# Landing Pack Preflight Static Consistency Audit

> **文档标识**：`docs/re/landing_pack_preflight_audit.md`  
> **任务阶段**：落地前静态一致性复核（离线、只读二进制、不启动真机）  
> **复核对象**：`docs/re/pending_execution_master_table.md` + `landing_pack_*.md` + `landing_equivalence_static_proof.md`  
> **权威二进制**：`ra2youli/gamemd.exe`（ImageBase `0x00400000`，`FileOffset = VA - 0x00400000`）  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **EXE MD5**：`4f37486e5b0dbe2ae5f45aeee0f98367`（与总表声明 **一致**）  
> **机读产物**：`out/re_work/landing_audit/audit_json.json`、`preflight_claims.txt`、`preflight_table.md`  
> **写作用域**：仅新建 `out/re_work/landing_audit/**` 与本文；既有 landing_pack / 总表 / ra2render / ra2youli **未改动**

---

## 〇、结论（先看这里）

| 判定项 | 结果 |
|:---|:---|
| **P-1.1～P-6.2 原字节 vs gamemd.exe** | **17/17 PASS**（脚本逐字节扫，非手打） |
| **S23 claims（31 条）** | **31/31 PASS** |
| **E9 rel32 落点（9 条）** | **9/9 OK**（目标 = 声明跳板槽） |
| **跳板槽位重叠** | **0 重叠**（0x01B00000 页布局自洽） |
| **H-D5 `0F B6 C0` / 禁 `83 E0 FF`** | 跳板偏移 `+0x10` 已是 `0F B6 C0`，全跳板无 `83 E0 FF` |
| **音频早退 ABI** | PlayGlobal `33 C0 C2 08 00`；PlayAt `33 C0 C2 04 00`（xor eax,eax + ret N） |
| **已知关键约束收录于总表** | 12/15 已收录；**3 项缺失（见勘误表 E-1～E-3）** |
| **总判定** | **可落地，但须先订正 4 处（E-1～E-4）**；其中 E-1/E-2 为跨文档知识风险，E-3 为状态标注缺口，E-4 为机械写入完整性缺口。**字节本身无一错误。** |

> 一句话：**实施方按总表机械写入，字节面不会踩坑**；会踩坑的是「去读了仍写错的源文档」和「总表未标明 P-2 在 ra2render 代码轨尚未落地」。

---

## 一、逐项复核表（P-1.1～P-6.2）

口径：`tools/audit_bytes.py` 同款段映射；对 `.text/.rdata` 与 `VA-0x00400000` 完全等价（已逐点验证）。

| ID | 名称 | VA | 总表FileOffset | 实际FileOffset | 节 | 期望原字节 | EXE 实测 | 结果 |
|:---|:---|:---:|:---:|:---:|:---:|:---|:---|:---:|
| P-1.1 | M-8 H-D1 校验探针 | `0x0064C6F2` | `0x0024C6F2` | `0x0024C6F2` | .text | `0F 85 69 05 00 00` | 同 | **PASS** |
| P-1.2 | M-8 H-D2 断开快照 | `0x0064CC61` | `0x0024CC61` | `0x0024CC61` | .text | `A0 80 48 B0 00` | 同 | **PASS** |
| P-1.3 | M-8 H-D5 帧CRC环 | `0x0064DE75` | `0x0024DE75` | `0x0024DE75` | .text | `5F 5E 5D 5B 83 C4 14 C3` | 同 | **PASS** |
| P-1.4 | M-8 H-D6 主事件流 | `0x0064C911` | `0x0024C911` | `0x0024C911` | .text | `E8 9A A3 E7 FF` | 同 | **PASS** |
| P-1.5 | M-8 H-D6b 次事件流 | `0x0064CC0A` | `0x0024CC0A` | `0x0024CC0A` | .text | `E8 A1 A0 E7 FF` | 同 | **PASS** |
| P-2.1 | M-10 Gap1 局部开图 | `0x00568273` | `0x00168273` | `0x00168273` | .text | `89 99 34 01 00 00` | 同 | **PASS** |
| P-2.2 | M-10 Gap2 全图开图 | `0x00577EC5` | `0x00177EC5` | `0x00177EC5` | .text | `89 B8 34 01 00 00` | 同 | **PASS** |
| P-2.3 | M-10 Gap3 重遮蔽 | `0x00577B60` | `0x00177B60` | `0x00177B60` | .text | `89 98 34 01 00 00` | 同 | **PASS** |
| P-2.4 | M-10 SpySat 门控 | `0x00508F8F` | `0x00108F8F` | `0x00108F8F` | .text | `74 65` | 同 | **PASS** |
| P-2.5 | G-07 TYPE 还原表 | 动态 | — | — | 运行时 | 字段备份 | 非字节补丁 | **N/A** |
| P-3.1 | M-9 Particle 槽69 | `0x007EFA68` | `0x003EFA68` | `0x003EFA68` | .rdata | `C0 CE 62 00` | 同（→`0x0062CEC0`） | **PASS** |
| P-3.2 | M-9 PSys 槽69 | `0x007EFCB0` | `0x003EFCB0` | `0x003EFCB0` | .rdata | `80 E2 62 00` | 同（→`0x0062E280`） | **PASS** |
| P-4.1 | CRT operator new | `0x007C8E17` | `0x003C8E17` | `0x003C8E17` | .text | `6A 01 FF 74 24 08` | 同 | **PASS** |
| P-4.2 | CRT operator delete | `0x007C8B3D` | `0x003C8B3D` | `0x003C8B3D` | .text | `FF 74 24 04 E8 A2 08 00 00` | 同 | **PASS** |
| P-5.1 | Audio PlayGlobal | `0x00750920` | `0x00350920` | `0x00350920` | .text | `51 A0 AC 64 84 00` | 同 | **PASS** |
| P-5.2 | Audio PlayAt | `0x007509E0` | `0x003509E0` | `0x003509E0` | .text | `A0 AC 64 84 00` | 同（5B） | **PASS** |
| P-6.1 | L4 视口 jge | `0x006D3D99` | `0x002D3D99` | `0x002D3D99` | .text | `0F 8D 98 00 00 00` | 同 | **PASS** |
| P-6.2 | L4 RegisterCellAsVisible | `0x006DA7D0` | `0x002DA7D0` | `0x002DA7D0` | .text | `A1 F4 F7 87 00 ...` | `A1 F4 F7 87 00` 窗口确认 | **PASS\*** |

\* P-6.2 总表原字节列以 `...` 截断（见勘误 **E-4**）；已实测入口前 5 字节与声明一致，但**不足以机械回滚**。

### 1.1 次级锚点（约束相关）

| 锚点 | VA | 实测 | 期望 | 结果 |
|:---|:---:|:---|:---|:---:|
| SpySat 9B 窗口 | `0x00508F88` | `80 B8 A5 16 00 00 00 74 65` | 同（`cmp [eax+0x16A5],0; je`） | **PASS** |
| PlayGlobal 原生禁用分支 | `0x0075092E` | `33 C0 59 C2 08 00` | `xor eax,eax; pop ecx; ret 8` | **PASS** |
| PlayGlobal `ret 8` | `0x00750931` | `C2 08 00` | 同 | **PASS** |
| PlayAt 原生禁用分支 | `0x007509EC` | `33 C0 5B C2 04 00` | `xor eax,eax; pop ebx; ret 4` | **PASS** |
| PlayAt `ret 4` | `0x007509EF` | `C2 04 00` | 同 | **PASS** |
| CRT new 后继 | `0x007C8E1D` | `E8 20 06 00 00` | call `0x007C9442` | **PASS** |
| CRT free 例程 | `0x007C93E8` | `56 8B 74 24 08 ...` | 可读 | **PASS** |

### 1.2 替换字节自检（E9 rel32）

| ID | 新字节 | 长度 | rel32 落点 | 结果 |
|:---|:---|:---:|:---|:---:|
| P-1.1 | `E9 09 39 4B 01 90` | 6/6 | `0x01B00000` | **OK** |
| P-1.2 | `E9 DA 33 4B 01` | 5/5 | `0x01B00040` | **OK** |
| P-1.3 | `E9 06 22 4B 01 90 90 90` | 8/8 | `0x01B00080` | **OK** |
| P-1.4 | `E9 AA 37 4B 01` | 5/5 | `0x01B000C0` | **OK** |
| P-1.5 | `E9 F1 34 4B 01` | 5/5 | `0x01B00100` | **OK** |
| P-4.1 | `E9 24 73 33 01 90` | 6/6 | `0x01B00140` | **OK** |
| P-4.2 | `E9 3E 76 33 01 90 90 90 90` | 9/9 | `0x01B00180` | **OK** |
| P-5.1 | `E9 9B F8 3A 01 90` | 6/6 | `0x01B001C0` | **OK** |
| P-5.2 | `E9 5B F8 3A 01` | 5/5 | `0x01B00240` | **OK** |
| P-6.1 Full | `E9 99 00 00 00 90` | 6/6 | `0x006D3E37`（原 jge 目标） | **OK** |

### 1.3 跳板内部机器码

| 跳板 | 声明长度 | 实测 | 关键位 | 结果 |
|:---|:---:|:---:|:---|:---:|
| TRAMP_HD5 @ `0x01B00080` | 48B | 48B | `+0x10 = 0F B6 C0`；无 `83 E0 FF`；尾 `5F 5E 5D 5B 83 C4 14 C3` | **OK** |
| TRAMP_P4_CRT_NEW @ `0x01B00140` | 39B | 39B | `jmp 0x007C8E1D` | **OK** |
| TRAMP_P4_CRT_DEL @ `0x01B00180` | 35B | 35B | `call 0x007C93E8` | **OK** |
| TRAMP_P5_AUD_PG @ `0x01B001C0` | 36B | 36B | 尾 `61 9D 33 C0 C2 08 00`；`jmp 0x00750926` | **OK** |
| TRAMP_P5_AUD_PA @ `0x01B00240` | 35B | 35B | 尾 `61 9D 33 C0 C2 04 00`；`jmp 0x007509E5` | **OK** |

### 1.4 Cave 布局重叠扫描

`0x01B00000` 页内 27 个声明区间（跳板 9 + 助手 2 + 计数 9 + 指针 7 + 环 1）**零重叠**。槽间空隙为对齐余量（22～413B），属正常。  
**观察（非缺陷）**：`p_HD2_Snapshot @ 0x01B00504` 与 `p_HD6_Log @ 0x01B0050C` 之间 `0x01B00508` 未分配——与 `landing_pack_net_fix.md` 槽位表一致，实施方勿自行挪用。

---

## 二、文档间冲突表（总表 vs landing_pack vs S23）

| # | 主题 | 总表口径 | landing_pack 口径 | S23 / 其它 | 判定 | 处置 |
|:---:|:---|:---|:---|:---|:---|:---|
| C-1 | 原字节（P-1～P-6） | 17 条 | 与总表一致（gap_spysat/net_fix 逐条对得上） | S23 31 条全 MATCH | **无冲突** | 可直接写入 |
| C-2 | `EnableMemoryPool` 默认 | `0` + 启动期锁定 | `crt_audio_particle` 正文 `=0`；**仍残留「改前 =1」订正痕迹**（L155/L538） | mp_landing 亦有「改前 1」 | **残留旧值** | 实施方**只认最终值 0**；见风险 R-4 |
| C-3 | `EnableParticleFog` 默认 | `0` | 正文 `=0`；残留「改前 =1」（crt L432/L539） | mp_landing L232 已标冲突并改 0 | **残留旧值** | 同上，只认 0 |
| C-4 | `EnableMinimapFog` | `0`（API 强制 0；注「ini 现值 1」） | gap_spysat 建议写 `0` | `ra2render.ini` 现值 **`0`**（注释里才有 1） | **总表「ini 现值 1」已过时** | 见 E-5 |
| C-5 | H-D5 取模 | `0F B6 C0`，禁 `83 E0 FF` | net_fix / equivalence 同 | S23 无此位（跳板内） | **一致** | — |
| C-6 | 音频早退 | `xor eax,eax; ret 8` / `ret 4` | crt 同（并给出原生禁用分支字节） | S23 只锚入口 | **一致** | — |
| C-7 | Blitter 实例尺寸 | **未提及** | landing_pack **未写 12** | `blitter_microkernel_deep_dive.md:40,45` **仍写「统一 12 字节」**；同文 L1029 / ATLAS R1 已勘误为 **4/8/12/16，P0 微内核 8 字节** | **源文档残留错误** | **E-1** |
| C-8 | WarheadTypeClass.Verses | **未提及**（总表 `SW+0xB0` 是 **超武 RechargeTime**，不同字段） | landing_pack **未写 Verses 偏移** | `weapons_damage_production.md` **多处仍写 Verses=+0xB0**；ATLAS §16.3 勘误为 **+0xA0** | **源文档残留错误** | **E-2** |
| C-9 | ra2render 3×6B NOP 落地状态 | 表内按「可安装补丁」列出，**未标注代码轨尚未落地** | gap_spysat 规格完整 | `ARCHITECTURE_ATLAS_REV` §20.6：**ra2render 全源码 grep `568273/577EC5/577B60` 0 命中 ⇒ 未落地，裂缝静默失能（P0）** | **总表状态缺口** | **E-3** |
> 【W3 勘误 · W3-A6/ISSUE-STALE-P2-LANDING】改前：568273/577EC5/577B60` 0 命中 ⇒ 未落地；改后：P-2.1~P-2.3 裂缝三点 NOP 已于 09-30 完整落地进 blitter_hooks.cpp:3273-3287 并完成三处 DLL 同步；真机 A3 验收 PASS (带窗口限定)。；依据：ra2render/blitter_hooks.cpp:3273-3287, 3417-3446; out/re_work/zcode_live/gap_p21_a3/RESULT_GAP_P21_A3.md:18-23；分级：P0
| C-10 | 细规格文件名 | 任务书写 `landing_pack_equivalence_static_proof.md` | 实际为 `landing_equivalence_static_proof.md`（无 `pack_`） | — | **命名不一致** | **E-6**（仅提示） |
| C-11 | P-6.2 原字节完整性 | `A1 F4 F7 87 00 ...` | l4 规格有完整窗口 | S23 未锚 P-6.2 | **截断** | **E-4** |

---

## 三、落地风险清单

### 3.1 ABI / 平栈

| 风险点 | 规格状态 | 说明 |
|:---|:---|:---|
| P-3 剔除早退 | **已正确**：`ret 8`（2 个压栈参数） | `__thiscall` + `pLocation/pBounds`；用 `ret 4`/裸 `ret` 会撕栈 |
| P-5 PlayGlobal 早退 | **已正确**：`xor eax,eax; ret 8` | `__fastcall`，栈上 8B；严禁 `-1` / 裸 `ret` |
| P-5 PlayAt 早退 | **已正确**：`xor eax,eax; ret 4` | 栈上 4B；同上 |
| P-4 new/delete | **已正确**：caller 清栈，跳板两出口均不 `ret N` | `__cdecl`；助手缺省必须 `RetZeroStub`（`33 C0 C3`），**禁用 `NoopHelper`（`C3` 不置 EAX）** |
| P-1 H-D1 EFLAGS | **已正确**：`pushfd` 在前，`test [esp+0x20], 0x40` 读 ZF | 顺序颠倒会读错槽 |
| P-1 H-D5 尾声 | **已正确**：重放 `pop edi..ebx; add esp,0x14; ret` | 8B 全在跳板内 |

### 3.2 跳板布局

| 风险点 | 结论 |
|:---|:---|
| 槽位重叠 | **无**（机读 27 区间零重叠） |
| rel32 硬编码 | **9/9 落点正确**；`0x01B00000` 失败时**整项跳过**，禁止改基址后复用这些 hex |
| `.detour` 节 | 总表/落地包均**明文禁止**（VA `0x00B93000`，含 6980B 非零 `Dtr\0`） |
| 页内空隙 | `0x01B00508` 未分配；`0x01B00263-0x01B003FF` 等空隙勿挪用 |

### 3.3 联机红线

| 风险点 | 总表收录 | 说明 |
|:---|:---|:---|
| P-2 混端联机 | **是**（§〇.3） | `Cell+0x134` 进 `.SAV`，一端补丁一端原版必 DESYNC |
| P-2 全员同值 | **是** | `EnableGapProtection` / `EnableSpySatGate` 强一致性 |
| MpActive 判定 | **是（F-10 已订正）** | `*(u8*)0x00A8D5F8 & 0x02`；**勿用 `0xA8ED84`（那是 CurrentFrame）** |
| MP 裁决键 | **是（F-09 已补）** | `TargetScanKey/Interval`、`EnableThreatRetention`、`MpStateWrites`、`MpAutoDowngrade`、`EnableMinimapFog` |
| 纯表现层包 | **是** | P-1/P-3/P-4/P-5/P-6 各端可独立配置 |

### 3.4 INI 门控默认值（最终权威值 = 总表 §3.1）

| 键 | 最终默认 | 联机规则 | 坑 |
|:---|:---:|:---|:---|
| `SyncEarlyLog/SyncSnapshotOnDesync/SyncMirror/SyncCmdMirror` | `0` | 可选 | 无 |
| `EnableGapProtection` | `1` | **全员同值** | 无 |
| `EnableSpySatGate` | `1` | **全员同值** | 无 |
| `EnableSpySatRadarSweep` | `1` | 触发 G-07 备份 | 须先备份再写 TYPE |
| `EnableParticleFog` | `0` | 各端独立 | 残留「改前 =1」文字，**勿抄** |
| `EnableMinimapFog` | `0` | **全员同值**；API 强制 0 | 键缺失/漏配→静默全开；总表「ini 现值 1」过时 |
| `EnableMemoryPool` | `0` | 各端独立 | **启动期单次锁定，严禁局内热切**（跨堆 → `0xC0000374`）；残留「改前 =1」 |
| `EnableAudioThrottling` | `1` | 各端独立 | 无 |
| `MaxSoundsPerFrame` / `SoundMinIntervalFrames` | `4` / `2` | — | 无 |
| `L4DirtyMode` | `force-full` | 各端独立 | `vision-dirty` 须 350 格全刷保底 |
| `TargetScanKey/Interval` | `position` / `8` | 联机强制 `position`/`1` | `pointer`+ASLR 必 DESYNC |
| `EnableThreatRetention` | `1` | **联机强制 0** | 无 |
| `MpStateWrites` / `MpAutoDowngrade` | `0` / `1` | 联机强制 0 / 1 | 无 |

### 3.5 其它红线

- **严禁挂钩 `0x0048D000`**（`Game::CallBack`，非地表查询）——总表已收录。
- **严禁 inline patch `0x0062CEC0` / `0x0062E280`**，只写虚表槽 69。
- **P-4 块头 8B、返回 `pBlock+8`、8 字节对齐**；释放投毒 `0xDEADBEEF`。
- **G-07 先备份 `SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0` 再写**；`RemoveVTableHooks` 还原。

---

## 四、勘误表（原文不删字，此处指出）

| 编号 | 位置 | 原文（保留） | 应为 | 影响面 | 优先级 |
|:---:|:---|:---|:---|:---|:---:|
| **E-1** | `blitter_microkernel_deep_dive.md:40,45`（及图注「12 字节」） | 「所有 Blitter 对象的分配大小统一为 **12 字节**」「Blitter 内存对象布局 (12 字节)」 | **按成员数分级 4/8/12/16**；**P0 微内核对象 = 8 字节**。按 12B 声明 `this+0x08` **越界 4 字节**。同文 L1029 已自勘误 | 若实施方按 12B 写 Blitter 结构体 → 越界读写 | **P0** |
| **E-2** | `weapons_damage_production.md:19,128,142,208,215,229,563,845` | `WarheadTypeClass.Verses[11]` 位于 **`Warhead+0xB0`** / `+0xB0+armor*8` | **`Verses[0]` 起于 `+0xA0`**（覆盖 `+0xA0…+0xF7`）；`+0xB0` 实为 `Verses[2]`。权威见 `ARCHITECTURE_ATLAS.md` §16.3 | 按 +0xB0 写会静默错位 8 个 double | **P0** |
| **E-3** | `pending_execution_master_table.md` §一 P-2.1～P-2.3 | 按「可安装」列出 3×6B NOP | 应增注：**ra2render 代码轨当前 0 命中（未落地）**，属「纸面已定谳、代码未写」；PsychicReveal 仍清 `Cell+0x134`，裂缝保护缺口仍在（见 `ARCHITECTURE_ATLAS_REV` §20.6） | 实施方可能误以为已装、跳过写入 | **P0** |
| **E-4** | `pending_execution_master_table.md` §一 P-6.2 原字节列 | `A1 F4 F7 87 00 ...` | 补全可回滚窗口（至少入口 5B：`A1 F4 F7 87 00`，并标注函数序言后续 `83 EC 0C 85 C0`）；「原生 API 调用（非 Hook）」项若不写字节，应标 **N/A（非字节补丁）** | 回滚表无法机械还原 | **P1** |
| **E-5** | `pending_execution_master_table.md` §3.1 覆盖规则表 `EnableMinimapFog` 行 | 「**ini 现值 1**」 | **`ra2render.ini` 现值已为 `0`**（L117）；注释中仅历史提及 1 | 误导验收基线 | **P2** |
| **E-6** | 任务书 / 口头引用 | `landing_pack_equivalence_static_proof.md` | 实际文件名 **`landing_equivalence_static_proof.md`** | 脚本按名索引会 miss | **P3** |

> **未删改任何原文**：以上仅在本报告登记，源文档保持原样。

---

## 五、已知关键约束收录核对（任务书逐条）

| 约束 | 总表是否收录 | 证据位置 | 结论 |
|:---|:---:|:---|:---|
| 跳板禁写 `.detour`；首选 `VirtualAlloc @ 0x01B00000`；失败跳过安装 | **是** | §〇.2（F-07）、§2.1.1 | **OK** |
| H-D5 取模 `0F B6 C0`，禁 `83 E0 FF` | **是** | §一 P-1.3、§2.1.2、TC-ST-01 | **OK** |
| PlayGlobal 早退 `xor eax,eax; ret 8`；PlayAt `ret 4` | **是** | §一 P-5.1/5.2、§2.5.1、TC-ST-05 | **OK** |
| 3×6B Gap NOP 三址 + SpySat `74 65→EB 65` | **是** | §一 P-2.1～2.4、§2.2 | **OK** |
| ra2render 中 3×6B NOP **尚未落地** | **否** | — | **E-3** |
| Blitter 实例 8B 非 12B | **否**（landing_pack 亦未写错） | 源 deep_dive 仍错 | **E-1** |
| WarheadTypeClass.Verses 起于 +0xA0 | **否**（总表 SW+0xB0 是另一字段） | 源 weapons 文档仍错 | **E-2** |

---

## 六、机读产物索引

| 文件 | 内容 |
|:---|:---|
| `out/re_work/landing_audit/audit_json.json` | 全量机读：master_claims / secondary / doc_extracted / s23 / replacement_selfcheck / known_constraint_coverage |
| `out/re_work/landing_audit/preflight_claims.txt` | 断言库（可再喂 `tools/audit_bytes.py`） |
| `out/re_work/landing_audit/preflight_table.md` | 逐项复核表（脚本生成） |
| `out/re_work/landing_audit/extract_and_verify.py` | 抽取+核对脚本 |
| `out/re_work/landing_audit/dump_anchors.py` | 锚点 dump |
| `out/re_work/landing_audit/scan_constraints.py` / `scan_known_issues.py` | 约束扫描 |
| `out/re_work/landing_audit/check_trampoline.py` | rel32/布局/跳板长度 |
| `out/re_work/landing_audit/crosscheck_docs.py` | 跨文档 hex/INI 对拍 |
| `out/re_work/landing_audit/finalize_claims.py` | S23 + 约束覆盖收口 |

---

## 七、复现方法

```text
python out/re_work/landing_audit/extract_and_verify.py
python out/re_work/landing_audit/dump_anchors.py
python out/re_work/landing_audit/check_trampoline.py
python out/re_work/landing_audit/finalize_claims.py
python tools/audit_bytes.py out/re_work/landing_audit/preflight_claims.txt --json out/re_work/landing_audit/audit_bytes_rerun.json
```

全程只读 `gamemd.exe`，未写 `ra2render/**`、`ra2youli/**`、台账与既有 landing_pack。

---

## 八、§九台账草稿（给执行台账追加用；**本文不改原总表**）

> 建议以「附录：落地前预检订正」形式并入下一次总表修订；原文条目保留，仅追加订正行。

### §九 落地前预检订正附录（草稿 · 2026-09-29 · landing_audit）

#### 9.1 字节面结论
1. P-1.1～P-6.2 共 17 条原字节、9 条 E9 rel32、5 条跳板机器码，**全部与 `gamemd.exe` 一致**（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`）。
2. S23 31 条断言 **全 MATCH**，可作为落地后回归对拍基线。
3. 跳板页 `0x01B00000` 布局 **零重叠**；`VirtualAlloc` 失败 → **整项不安装**（F-07 口径已收录）。

#### 9.2 须先订正（合入前）
| 序 | 编号 | 动作 | 责任文档 |
|:---:|:---:|:---|:---|
| 1 | E-1 | 在 Blitter 规格处标注：**P0 微内核实例 8 字节**（非 12）；禁止按 12B 声明 `this+0x08` | blitter_microkernel_deep_dive.md（勘误指针）+ 实施结构体 |
| 2 | E-2 | 在伤害链规格处标注：**`WarheadTypeClass.Verses` 起于 `+0xA0`**（`+0xB0`=`Verses[2]`） | weapons_damage_production.md（勘误指针） |
| 3 | E-3 | 总表 P-2.1～P-2.3 增注：**ra2render 代码轨未落地（grep 0 命中）**，裂缝保护缺口仍在 | pending_execution_master_table.md |
| 4 | E-4 | 补全 P-6.2 原字节或标 N/A | pending_execution_master_table.md |

#### 9.3 可直接机械写入清单（无订正项）
- P-1.1～P-1.5 五处 `E9 rel32` + TRAMP_HD1/2/5/6/6B  
- P-2.1～P-2.3 三处 `90×6`、P-2.4 `EB 65`  
- P-3.1/P-3.2 虚表槽 69（`PatchVTablePointer`，禁 inline）  
- P-4.1/P-4.2 两处 `E9 rel32` + TRAMP_P4_* + P-M1…P-M5  
- P-5.1/P-5.2 两处 `E9 rel32` + TRAMP_P5_*（早退 `33 C0 C2 08 00` / `33 C0 C2 04 00`）  
- P-6.1 默认写 `E9 99 00 00 00 90`（force-full）  
- INI 最终默认值按 §3.4（**忽略文中「改前」旧值**）

#### 9.4 安装后必做对拍（继承 TC-ST-01…06）
1. 5 处 Hook 机器码 + H-D5 `+0x10=0F B6 C0`  
2. Gap 3×`90×6` + SpySat `EB 65` + TYPE 备份 4 字段  
3. 虚表槽指向 Hook 且函数体出口 `ret 8`  
4. `PoolBlockHeader==8`、返回 8 对齐、释放投毒  
5. PlayGlobal/PlayAt 早退 `eax=0` + `ret 8`/`ret 4`  
6. `0x006D3D99` Full 模式字节 + 全工程无 `0x0048D000` 挂钩  

#### 9.5 遥测与回滚（不变）
- 回滚表按总表 §4.1；G-07 走 `RestoreSpySatBuildingTypes()`。  
- 热卸载五阶段次序不变；第四阶段 `VirtualFree(0x01B00000)`。

---

## 九、签署栏

| 项 | 值 |
|:---|:---|
| 复核方式 | 离线静态字节扫描 + 跨文档 grep 对拍 |
| 真机 | **未启动**（按任务约束） |
| 字节面结论 | **可落地** |
| 文档面结论 | **N=4 处须先订正（E-1～E-4）**；E-5/E-6 为低优先级提示 |
| 残余风险 | 实施方若绕过总表去读 `weapons_damage_production.md` / `blitter_microkernel_deep_dive.md` 旧段落，会踩 E-1/E-2 |
