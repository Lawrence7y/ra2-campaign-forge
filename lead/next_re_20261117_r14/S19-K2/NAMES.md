# S19-K2 · NAMES.md — T2 批量定名表

> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476` 亲测一致。依据均可独立复算（`EVIDENCE/t2_naming_evidence.txt`、`work/gather_evidence.py`、`work/gen_evidence.py`）。
> 分级按 STATUS_BOARD「升级硬规矩」：字节级证据（imm32 串引用 + call 锚点 / IAT 导入名）方可 `[已证]`。18 条全部当前为 `sub_`（11 `[未证]` + 7 `[静态推断]`），本卡为首次定名。

| entry | name | 依据类型 | 依据地址（逐条可查） | 分级 |
|---|---|---|---|---|
| 00443860 | EVA_NewRallyPointEstablished_Trigger | 串引用+调用锚点 | `mov ecx,[0x818E58]="EVA_NewRallyPointEstablished"` @0x443A64 → `call 0x752700`@0x443A69 | `[已证]` |
| 0044F820 | EVA_BuildingOnLine_Trigger | 串引用+调用锚点 | `mov ecx,[0x8190C8]="EVA_BuildingOnLine"` @0x44FD15 → `call 0x752700`@0x44FD1A | `[已证]` |
| 004571E0 | EVA_Infiltration_Trigger | 串引用+调用锚点 | 7 处 `mov ecx,[EVA_*]="EVA_RadarSabotaged/…/EVA_NewTechnologyAcquired"` → `call 0x752700`（见 EVIDENCE） | `[已证]` |
| 00458200 | EVA_StructureAbandoned_Trigger | 串引用+调用锚点 | `mov ecx,[0x81926C]="EVA_StructureAbandoned"` @0x4582D3 → `call 0x752700`@0x4582D8 | `[已证]` |
| 004FB0E0 | EVA_CannotDeployHere_UnitReady_Trigger | 串引用+调用锚点 | `EVA_CannotDeployHere`@insn 0x4FB0F2 + `EVA_UnitReady`@insn 0x4FB3BF → `call 0x752700` | `[已证]` |
| 0050E010 | EVA_RobotTanksBackOnline_Trigger | 串引用+调用锚点 | `mov ecx,[EVA_RobotTanksBackOnline]` → `call 0x752700`（EVIDENCE） | `[已证]` |
| 00522910 | EVA_StructureGarrisoned_Trigger | 串引用+调用锚点 | `mov ecx,[EVA_StructureGarrisoned]` → `call 0x752700`（EVIDENCE） | `[已证]` |
| 00686570 | EVA_BattleControlTerminated_Trigger | 串引用+调用锚点 | `mov ecx,[EVA_BattleControlTerminated]` → `call 0x752700`（EVIDENCE） | `[已证]` |
| 006A87F0 | EVA_NewConstructionOptions_Trigger | 串引用+调用锚点 | `mov ecx,[EVA_NewConstructionOptions]` → `call 0x752700`（EVIDENCE） | `[已证]` |
| 006A8B30 | EVA_ConstructionComplete_Trigger | 串引用+调用锚点 | `mov ecx,[EVA_ConstructionComplete]` → `call 0x752700`（EVIDENCE） | `[已证]` |
| 006CC080 | EVA_SuperWeaponReady_Trigger | 串引用+调用锚点 | 10 处 EVA 超级武器就绪串 → `call 0x752700`（EVIDENCE） | `[已证]` |
| 007393C0 | EVA_CannotDeployHere_Trigger | 串引用+调用锚点 | `mov ecx,[EVA_CannotDeployHere]` → `call 0x752700`（EVIDENCE） | `[已证]` |
| 00432BD0 | Bink_Goto | IAT 导入 | `call dword[0x7E15AC]=binkw32!_BinkGoto@12` @0x432BDE | `[已证]` |
| 00432C30 | Bink_Pause | IAT 导入 | `call dword[0x7E15B0]=binkw32!_BinkPause@8` @0x432C3E | `[已证]` |
| 00433020 | Bink_Wait | IAT 导入 | `call dword[0x7E15C0]=binkw32!_BinkWait@4` @0x433027 | `[已证]` |
| 004331F0 | Bink_CopyToBuffer | IAT 导入 | `call dword[0x7E15B8]=binkw32!_BinkCopyToBuffer@28` @0x433251 | `[已证]` |
| 00432E40 | Bink_DoFrame | IAT 导入 | `call dword[0x7E15BC]=binkw32!_BinkDoFrame@4`（函数体内，F1 锚点） | `[已证]` |
| 00752B70 | LoadTauntVOX_Files | 串引用 | `taunts\tau*%02i.wav` ×10 串引用（仅文件名表，函数角色属推断） | `[静态推断]` |

## 判据说明（为何不是「看起来像」）
- **EVA 组**：不是按"函数里出现 EVA 字样"命名，而是要求**同一函数体内** `mov ecx,[串地址]`（imm32 字节级）**紧邻** `call 0x752700`（F1 已证 EVA 播放锚点 `VoxClass::Play`）。每个函数给出串数据 VA + 指令地址 + call 地址，三元组可独立复算。
- **Bink 组**：pefile 解析 IAT（`0x7E1590..0x7E15C0` 13 个 binkw32 导入），函数体内 `call dword[0x7E15xx]` 的绝对 IAT 地址与导入名一一对应，字节级。仅对「单次调用即主体」的 OO 包装定名；`0x432750`（Open/多 API）、`0x432C70`（MovieLoop）等不按单导入命名。
- **不可定者保持 `sub_`**：音频管理类里 `VocClass`/`VoxClass` 无自身 RTTI TD（只有 `VectorClass<VocClass*>` 等模板名），按纪律 5 fail-closed，不据头文件名猜类名；`AudioController::sub_406xxx` 6 条无串/无导入、字段访问不特异，保持占位。
