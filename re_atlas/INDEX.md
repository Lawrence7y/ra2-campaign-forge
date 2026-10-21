# RE-ATLAS · 地址总表 (INDEX)

> 以 VA 为主键的可查询索引。每行：VA → 名称 → 作用 → 证据 → 置信度。
> 置信度：**实证**（本线字节复算）/ **语料实证**（他线做过字节复算且未翻案）/
> **推演** / **社区**。
> 生成口径与校验器见 `tools/`；数据快照见 `evidence/`。

**目标二进制**：`ra2youli/gamemd.exe`
sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
ImageBase `0x00400000`，入口 `0x007CD80F`。

**规模**：语料命名点 1,304 个（.text 内）；递归遍历发现函数入口 15,224 个；
命名覆盖率 **3.62%**（551/15,224，保守下界）。

---

## A. 全局单例与标量

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x00887324` | `TacticalClass*` | 战术主视口单例指针（一级解引用） | ATLAS §11.1 | 社区 |
| `0x0087F7E8` | `MapClass` 实例 | 全图网格/瓦片/迷雾宿主 | ATLAS §11.1；`0x0072A0AE mov ecx,0x87F7E8` | 实证（旁证） |
| `0x00A8B230` | `ScenarioClass*` | 局内剧本、航点、触发器、RNG(+0x218) | ATLAS §11.1 | 社区 |
| `0x008871E0` | `RulesClass*` | rulesmd.ini 全局规则单例 | ATLAS §11.1 | 社区 |
| `0x00A83D4C` | `HouseClass::Player` | 本地人类玩家阵营指针 | ATLAS §11.1；`0x0050B71A` 读后严格比对 | **实证** |
| `0x00A80228` | `HouseClass::Array` | 参战阵营动态向量 | ATLAS §11.1 | 社区 |
| `0x0087E8B8` | `PathFinder` | 寻路工作区（生成戳 +0x28） | ATLAS §11.1 | 社区 |
| `0x00887888` | `SpatialGrid` | 20×20 粗空间网格，400 桶×24B | ATLAS §11.1 | 社区 |
| `0x00A8ED84` | `CurrentFrame` | 全局逻辑帧计数器 | claims `0x0055DE73/79/81` 三处字节断言 | **实证** |
| `0x008464AC` | `VoicesEnabled` | 音频主开关 | ATLAS §11.1 | 社区 |
| `0x00A8B238` | 游戏模式标志 | 非 0 ⇒ 联机/多人；0 ⇒ 单人 | 本线 `0x0050B6F0`：`a1 38 b2 a8 00` + `85 c0` + `75 1d` | **实证**（本线新增） |
| `0x00AC51FC` | `CurrentFrameCRC` | 当前帧混合 CRC | ATLAS §11.1 | 社区 |
| `0x00B04474` | `LatestFramesCRC[256]` | 过去 256 帧 CRC 环 | ATLAS §11.1 | 社区 |
| `0x008B4204` | `NetworkQueue[16384]` | 网络指令环形队列 | ATLAS §11.1 | 社区 |
| `0x0087E2A8` | `VoicePool[300]` | 音效通道池 | ATLAS §11.1 | 社区 |

---

## B. 类虚表与实例尺寸（RTTI 独立复算）

> 虚表地址 **20/20 与 ATLAS 一致、0 不一致**（`evidence/vtable_xcheck.txt`）。
> 实例尺寸由 `vtable[12]` 体首 `mov eax, imm` 解出；**该前提并非对所有类成立**，
> 不成立者标 `—`。

| 类 | 虚表 VA | 虚函数数 | 实例尺寸 | 置信度 | 备注 |
|:---|:---|---:|---:|:---|:---|
| `AbstractClass` | `0x007E1F50` | 24 | 待解 | 实证（VT） | 根类，+6 接口 |
| `ObjectClass` | `0x007EF060` | 122 | 待解 | 实证（VT） | |
| `MissionClass` | `0x007EDCC0` | 157 | 待解 | 实证（VT） | |
| `RadioClass` | `0x007F0508` | 161 | 待解 | 实证（VT） | |
| `TechnoClass` | `0x007F4960` | 309 | 待解 | 实证（VT） | |
| `FootClass` | `0x007E8C94` | 341 | 待解 | 实证（VT） | |
| `UnitClass` | `0x007F5C70` | 344 | 2280 (`0x8E8`) | **实证** | `v[12]=0x00746DD0` |
| `InfantryClass` | `0x007EB058` | 343 | 1776 (`0x6F0`) | **实证** | `v[12]=0x005232F0` |
| `AircraftClass` | `0x007E22A4` | 341 | 1752 (`0x6D8`) | **实证** | `v[12]=0x0041C170` |
| `BuildingClass` | `0x007E3EBC` | 322 | 1824 (`0x720`) | **实证** | `v[12]=0x00459E70` |
| `BulletClass` | `0x007E46E4` | 125 | 352 (`0x160`) | **实证** | `v[12]=0x0046B540` |
| `AnimClass` | `0x007E3354` | 124 | 456 (`0x1C8`) | **实证** | `v[12]=0x00426530` |
| `ParticleClass` | `0x007EF954` | 123 | 312 (`0x138`) | **实证** | `v[12]=0x0062D970` |
| `ParticleSystemClass` | `0x007EFB9C` | 122 | 256 (`0x100`) | **实证** | `v[12]=0x00630200` |
| `HouseClass` | `0x007EA8A0` | 24 | 90296 (`0x160B8`) | **实证** | `v[12]=0x00504730` |
| `CellClass` | `0x007E4EEC` | 24 | 328 (`0x148`) | **实证** | `v[12]=0x00487E70` |
| `SuperClass` | `0x007F3FE8` | 24 | 128 (`0x80`) | **实证** | `v[12]=0x006CE210` |
| `TeamClass` | `0x007F4730` | 24 | 160 (`0xA0`) | **实证** | |
| `TeamTypeClass` | `0x007F47D0` | 27 | **248 (`0xF8`)** | **实证（翻案）** | `v[12]=0x006F20B0`；ATLAS 记 288 **错** |
| `AITriggerTypeClass` | `0x007E2A50` | 27 | **272 (`0x110`)** | **实证（翻案）** | `v[12]=0x0041FFE0`；ATLAS 记 256 **错** |
| `MapClass` | `0x007ED404` | 30 | — | 实证（VT） | 继承 `GScreenClass` |
| `RadarClass` | `0x007F0344` | 54 | —（`v[12]` 非 GetSize） | 实证（VT） | 见 CONFLICTS G-4 |
| `WWMouseClass` | `0x007F7B2C` | 18 | —（`v[12]` 非 GetSize） | 实证（VT） | 见 CONFLICTS G-5 |

完整 988 类清单：`evidence/rtti/hierarchy.txt`（继承链）与 `evidence/rtti/classes_meta.json`（每类 vtable / 槽数 / 基类链）。

---

## C. 关键函数（按子系统）

### C.1 时钟

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x004093B0` | `Clock::Now` | 间接分发入口：读 `[0x0087E848]` 函数指针后 `jmp eax` | claims `0x004093B0/B5/B9` | 语料实证 |
| `0x00409360` | `Clock::Init` | QPF 初始化 | claims `0x00409360` | 语料实证 |
| `0x004093C0` | `Clock::ReadQPC` / `Clock::NowQpc` | 读高精计时器 | claims `0x004093C0` | 语料实证 |
| `0x00409320` | `Stream::Get_Unread_Bytes` | `[ecx+0x34] − [ecx+0x38]` | claims `0x00409320` | 语料实证 |

### C.2 空间索引

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x004134A0` | `SpatialGrid::AddObject` | 读对象坐标 → 换算桶坐标 → 压入对应桶 | ATLAS §4；`0x004134B3 call [eax+0x1B8]` 取坐标 | 语料实证 |
| `0x004135D0` | `SpatialGrid::RemoveObject` | 从桶移除 | 语料 | 社区 |
| `0x004137A0` | `SpatialBucket::Next` / `SpatialGrid::NextCandidate` | 桶内迭代器；`test [ecx+0x2590]` 空即返回 0 | 本线反汇编 | **实证（新增）** |
| `0x00412B40` | `SpatialGrid::InitQuery` | 查询初始化 | 语料 | 社区 |

### C.3 归属与可见性闸

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x0050B6F0` | **`HouseClass::IsPlayerControl`** | 单人读 `+0x1EC/+0x1ED`；联机 `cmp ecx, [0xA83D4C]` | 本线全函数反汇编 | **实证（本线裁定）** |
| `0x006DA380` | **`TacticalClass::GetObjectAt`** | 鼠标下对象解析，扫 `0xB0CEC8`，硬拦未探测隐形 | 语料 + 本线入口确认 | 语料实证（本线裁定命名） |
| `0x00656EC0` | **`RadarClass::Refresh`** | 雷达主循环（含地形缓存 + 视口矩形 + 画点） | 语料 | 语料实证（本线裁定命名） |

### C.4 可见性 / 裂缝

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x00568273` | 裂缝隐匿保护 1 | `mov [ecx+0x134], ebx` | claims `0x00568273` | 实证 |
| `0x00577EC5` | 裂缝隐匿保护 2 | `mov [eax+0x134], edi` | claims `0x00577EC5` | 实证 |
| `0x00577B60` | 裂缝隐匿保护 3 | `mov [eax+0x134], ebx` | claims `0x00577B60` | 实证 |
| `0x00508F88` | 间谍卫星状态检查 | `cmp byte [eax+0x16A5], 0` | claims `0x00508F88` | 实证 |
| `0x00508F8F` | 间谍卫星门控短跳 | `je 0x00508FF6`（无卫星跳过揭开黑雾） | claims `0x00508F8F` | 实证 |

### C.5 CRT / 内存

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x007C8E17` | CRT `operator new` 路径 | `push 1; push [esp+8]` | claims | 语料实证 |
| `0x007C8B3D` | CRT `operator delete` 包装 | `push [esp+4]; call free` | claims | 语料实证 |
| `0x006C6400` | `DynamicVectorClass::AddItem` | 线性扩容 +10 缺陷 | ATLAS §10 | 语料实证 |
| `0x004068E0` | Release 空桩 | `ret; nop×3`，1,672 处直调 | claims `0x004068E0` | **实证** |

---

### C.6 触发器 / 队伍脚本派发（R2-1，详见 `kb/10_map_triggers.md`）

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x006DD8B0` | `TActionClass::Execute` | 触发器动作执行；`sub esp,0x240` | 本线入口反汇编 | **实证** |
| `0x006DFDEC` | Action 跳表 | 145 dword，145/145 在 .text，143 唯一 | `dump_trigger_tables.py` | **实证** |
| `0x006DD8E7` | Action 派发点 | `jmp [edx*4+0x6DFDEC]` | 字节 | **实证** |
| `0x006DFDDB` | Action 共享 epilogue | `mov al,1; pop×4; add esp,0x240; ret 0x10` | 字节 | **实证**（动作 38/91/92 共用） |
| `0x006E9050` | `TeamClass::AI` | 队伍脚本执行；`[edi+0x3C]` 状态比较后早退 | 本线入口反汇编 | **实证** |
| `0x006E9F74` | Team 动作跳表 | 65 dword，65/65 在 .text，**65 唯一** | `dump_trigger_tables.py` | **实证** |
| `0x0071E940` | `TEventClass::HasOccured` | 事件判定；`[ebp+0x2C]`=事件 Kind | 本线入口反汇编 | **实证** |
| `0x0071F218` | 事件一级跳表 | **12 dword / 12 唯一目标** | `dump_trigger_tables.py` | **实证** |
| `0x0071F248` | 事件二级选择表 | **49 字节**，值=一级表下标（0..11），`0x0B`=兜底 | `evidence/trigger_tables.txt` 全文 | **实证** |
| `0x0071E964` | 事件派发点 | `jmp [edx*4+0x71F218]` | 字节 | **实证** |
| `0x0071EC63` | 事件兜底 | 既是 `ja` 目标，又是选择值 11 的目标 | 字节 + 机器输出 | **实证** |
| `0x0071F27C` | 事件二级门 | 2 目标门 + 选择表 `0x71F284` | 语料 | 语料实证（未复核） |
| `0x0071F2C0` | 事件三级 | 14 目标 + 选择表 `0x71F2F8` | 语料 | 语料实证（未复核） |
| `0x0071F328` | 事件四级 | 10 目标 + 选择表 `0x71F350` | 语料 | 语料实证（未复核） |

**关键读表规则**：事件是**两级**查表 `table1[table2[kind-0x0D]]`，
不是 `table1[kind-0x0D]`。49 槽中仅 **12 槽**有专属实现，**37 槽**走兜底。
Action / Team 两表是**单级**绝对地址数组。

---

## D. 数据/字符串锚点（claims PART 2–4 摘要）

完整 323 条见 `docs/re/anchor_claims.txt`；本线已全量复算 **323/323 PASS**
（`evidence/claims_verify.txt`）。此处只列高频引用者：

| VA | 内容 | 说明 |
|:---|:---|:---|
| `0x00826444` | `"RA2MD.INI"` | 主配置文件名 |
| `0x00840D4C` | `"LANGUAGE.MIX"` | 语言 MIX |
| `0x00840D5C` | `"LANGMD.MIX"` | 尤复语言 MIX |
| `0x008189C8` | Base64 字母表 | `A`–`Z a`–`z 0`–`9 + /` |
| `0x008108AE` | `hint=0xFD` + `"StgCreateDocfile"` | 导入名表项，确证 `ole32!StgCreateDocfile` |
| `0x00825C08` / `0x00825C14` | `"PrivateKey"` / `"PublicKey"` | 联机加密 |

---

## 查询方式

```bash
# 按 VA 查语料里所有叫法（含来源文件与出现次数）
python -c "import json;m=json.load(open('re_atlas/evidence/symbol_map.json',encoding='utf-8'))['map'];print(json.dumps(m.get('0x00656EC0'),ensure_ascii=False,indent=1))"

# 取任意 VA 的前 N 条指令 + 原始字节
python re_atlas/tools/disas.py 00656EC0

# 复算 323 条 claims
python re_atlas/tools/verify_claims.py

# 复核某个类的尺寸（含"该槽是否 GetSize"门禁）
python re_atlas/tools/xcheck_sizes.py
```
