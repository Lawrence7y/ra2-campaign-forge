# S20-K1 LAYOUT — 粒子/Anim 类布局与虚表语义字节级取证

> 卡号 S20-K1｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（W180 全值复核一致）｜ImageBase `0x400000`
> 全部地址 VA（hex）。工具 Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26。
> 分级：`[已证]`=字节级（RTTI/ imm32/ 读写指令/ 指令边界）；`[静态推断]`=有部分字节证据但语义需推；`[未证]`=无证据。
> 复算脚本全部在 `work/`，原始输出全部在 `EVIDENCE/`（未截断）。**目标二进制只读，未写入。**

---

## T1 · RTTI 实测类清单（禁止按头文件名推断，R14 §8.1 错源④/⑧）

### 1.1 复算链（fail-closed）

1. TypeDescriptor 名串在 `.data`（如 TD `0x8177C8` → name `0x8177D0` = `.?AVAbstractClass@@`）。
2. COL 在 `.rdata`，字段：`+0=sig(0) / +4=obj_off / +8=cd_off / +0xC=TD / +0x10=CHD`。
   **严格取 `COL+0xC → TD`，`TD+8` 取名**；读 `COL[+8]` 会拿到 cd_off（错源⑧，曾致 `0x414B9E` 误标）。
3. `vtable[-1] = COL`（`.rdata` 中值等于 COL 地址的 dword 位置 `vt = loc+4`）。
4. 槽数 = 从 `vt` 起**连续指向 `.text` 的 dword 个数**，无任何 atlas 过滤（错源⑦：TClassFactory slot4 被 JSON 漏 1）。

**总量校验**：TD=988 / COL=1214 / vtable=1214 / **总槽数=14,044**，与 R14_COMMON §8.1 审计基线（14,044 槽 / 1,214 表）**逐字节相符**，未受害于 `vtables_v2.json` 错源①（JSON 13,351 槽，794 表各少 1 末槽）。
（`work/t1_rtti.py` / `EVIDENCE/T1_rtti_summary.txt`、`T1_rtti_vtables.tsv`、`T1_rtti_cols.tsv`、`T1_rtti_typedescriptors.tsv`）

### 1.2 S20 归属类（类名以 RTTI 字符串为准；实例类 + 类型类）

每个类有 4 张 vtable（多继承，`obj_off` = 0/4/8/0xC，与 KB `11_class_layouts.md` §0.2 的 4-vptr 前缀一致）；主表 = `obj_off=0`。

| 类（RTTI 名去 `.?AV@@`） | TD | COL | vtable 基址 | 主表槽数 | 表末(第一非 .text dword) | 分级 |
|---|---|---|---|---:|---|:---|
| AnimClass | 0x8182C8 | 0x7FBA60 | **0x7E3354** | **124** | 0x7E3544 | `[已证]` |
| ParticleClass | 0x8366E8 | 0x807BE8 | **0x7EF954** | **123** | 0x7EFB40 | `[已证]` |
| ParticleSystemClass | 0x836748 | 0x807CA0 | **0x7EFB9C** | **122** | 0x7EFD84 | `[已证]` |
| VoxelAnimClass | 0x845E50 | 0x80CDF8 | **0x7F6318** | **122** | 0x7F6500 | `[已证]` |
| AnimTypeClass | 0x818330 | 0x7FBBB0 | 0x7E3608 | 41 | 0x7E36AC | `[已证]` |
| ParticleTypeClass | 0x8370D0 | 0x8082F0 | 0x7F0188 | 40 | 0x7F0228 | `[已证]` |
| ParticleSystemTypeClass | 0x836F18 | 0x808238 | 0x7F00A8 | 40 | 0x7F0148 | `[已证]` |
| VoxelAnimTypeClass | 0x845E70 | 0x80CEB0 | 0x7F6548 | 40 | 0x7F65E8 | `[已证]` |

接口表（同一 TD）：AnimClass `0x7E3338`(6)/`0x7E3330`(1)/`0x7E3328`(1)；ParticleClass `0x7EF938`(6)/`0x7EF930`(1)/`0x7EF928`(1)；ParticleSystemClass `0x7EFB80`(6)/`0x7EFB78`(1)/`0x7EFB70`(1)；VoxelAnimClass `0x7F62FC`(6)/`0x7F62F4`(1)/`0x7F62EC`(1)。

> **与旧文档差异**：文档中 ParticleClass 槽 69 表项写 `0x7EFA68`、ParticleSystemClass 写 `0x7EFCB0` —— 本卡实测 `0x7EF954+0x114=0x7EFA68`、`0x7EFB9C+0x114=0x7EFCB0`，**吻合**。文档将 ParticleSystem/Particle 的 vtable 称"主表"，RTTI 证实它们确为 `obj_off=0` 的主表，无冲突（详见 DISAGREE.md）。

---

## T2 · GetSize 双向核对（每主类 2 条独立通道）

通道 A = `v[12]` 体 `B8 <imm32> C3`；通道 B = 构造器分配点 `push <imm32>; call 0x7C8E17`（operator new 包装）+ 紧邻 `call <ctor>`（ctor 由 `mov [obj],vt` 写主虚表识别）。

| 类 | v[12] 地址 | 通道A (hex/dec) | WhatAmI v[11] | 通道B 分配对 | 闭合 |
|---|---|---:|---:|---:|:---|
| AnimClass | 0x426530 | 0x1C8 / 456 | 4 | **155** 对（如 `push@0x414C27→call ctor 0x421EA0@0x414C73`） | `[已证]` |
| ParticleClass | 0x62D970 | 0x138 / 312 | 22 (0x16) | **8** 对（如 `push@0x62E397→call ctor 0x62B5E0@0x62E3CB`） | `[已证]` |
| ParticleSystemClass | 0x630200 | 0x100 / 256 | 24 (0x18) | **24** 对（如 `push@0x441E7B→call ctor 0x62DC50@0x441EED`） | `[已证]` |
| VoxelAnimClass | 0x74AB10 | 0x148 / 328 | 41 (0x29) | **5** 对（如 `push@0x469D99→call ctor 0x7493B0@0x469DD5`） | `[已证]` |
| AnimTypeClass | 0x428E70 | 0x378 / 888 | — | 0（构造器走 TClassFactory 注册） | 通道A `[已证]`/双向`[未证]` |
| ParticleTypeClass | 0x645910 | 0x318 / 792 | — | 0（同上） | 通道A `[已证]`/双向`[未证]` |
| ParticleSystemTypeClass | 0x644920 | 0x310 / 784 | — | 0（同上） | 通道A `[已证]`/双向`[未证]` |
| VoxelAnimTypeClass | 0x74BA00 | 0x308 / 776 | — | 0（同上） | 通道A `[已证]`/双向`[未证]` |

交叉校验：`v[11]` WhatAmI 与 v[12] GetSize 各为 `mov eax,imm;ret`（69 类零冲突口径，R14 §2）；槽值即函数，**未做"像不像函数"二次筛选**（错源②/坑：会误杀 6B 虚函数）。
（`work/t2_getsize.py`、`t2_vt_writes.py`、`t2_getsize_b_v3.py` / `EVIDENCE/T2_getsize_channelA.txt`、`T2_getsize_channelB_v3.txt`）

---

## T3 · 字段布局（写者+读者双重支撑；偏移不定语义 R14 §6-4）

来源：以 4 主类全部 vtable 槽实现 + 构造器为方法集，capstone detail 跟踪 `ecx→this` 传播的 `[reg+disp]` 读写（`work/t3_field_census.py`）；逐函数核验见 `work/t3_verify2.py` / `EVIDENCE/T3_field_semantic_functions.txt`。完整普查见 `EVIDENCE/T3_field_census.tsv`（214 行）。
头部 4 vptr：`+0/+4/+8/+0xC`（RTTI obj_off 0/4/8/0xC 实证，与 KB §0.2 一致）。

### 3.1 AnimClass（size 0x1C8）

| 偏移 | 宽度 | 类型 | 写者地址（全部/采样） | 读者地址（采样） | 语义 | 分级 |
|---|---:|---|---|---|---|:---|
| +0x00 | 4 | vptr×4 | 0x42201C/0x422047/0x422028/0x422030 | 大量 | 主表 0x7E3354 + 3 接口 | `[已证]` |
| +0xC8 | 4 | ptr | 0x421EE5（ctor） | 0x423ADC/0x423B05/0x423B23 等 20+（AI） | 动画主状态/宿主对象指针（AI 反复读，参与 +0x19D 可见性写） | `[静态推断]`（读写`[已证]`，具体类型未定） |
| +0xCC | 4 | int | 0x421EEE（ctor） | 0x4xxx（AI 9 读） | 帧/进度计数 | `[静态推断]` |
| +0x184 | 4 | int | 0x421FC2(ctor)、0x424393(Update dec回写)、0x4247E5(循环随机重挂) | 0x424386(Update)、0x425472(Save)、0x422C70(DrawIfVisible 门) | **DelayTimer 延迟倒计时**：每帧 dec，>0 时 DrawIfVisible `xor al,al;ret 0xC` 跳绘制；减至 0 调 0x424CE0 启动；循环末由 AnimType+0x2E0 随机重挂 | `[已证]` |
| +0x198 | 1 | bool | 0x421F??（ctor 0） | 0x423AD2(AI)、Draw 门 | 状态标志（AI 首读 + Draw 判） | `[静态推断]` |
| +0x199 | 1 | bool | 0x421FF7(ctor 0)、0x4519B2(建筑附属动画置 1) | 0x423014(Draw) 配 AnimType+0x374 硬切 | IsFogged（旧文档名，读写点实证；硬切非淡出） | `[静态推断]` |
| +0x19D | 1 | bool | 0x423B5C/0x423B7F/0x423B88/0x423BB8/0x423BC1/0x421FF?（6 写，AI/ctor） | Draw 0x422FEC `jne 0x4238A3` 硬切 | 地表不可见标志（AI 写、Draw 读硬切） | `[已证]` |

> **勘误**：旧文档 `fx_draw_chain.md` §2.2/§7-Q1 曾把 `+0x184` 猜作"隐藏 bool"，S3 及其 R7 §19.5 改判 `int DelayTimer`。本卡字节证据（dec + DrawIfVisible 门 + 减至 0 触发 0x424CE0）**支持 DelayTimer 判定**。

### 3.2 ParticleClass（size 0x138）

| 偏移 | 宽度 | 类型 | 写者地址 | 读者地址（采样≥3） | 语义 | 分级 |
|---|---:|---|---|---|---|:---|
| +0x9C/+0xA0/+0xA4 | 12 | CoordStruct int×3 | 由 AI/Update 写（普查 0x9C 读 16 次；写点在 ctor 0x62B5xx 系列） | Draw 0x62CF30(lea)/0x62CF36([+9C]) + 14 其它 | Location (X,Y,Z leptons) | `[静态推断]`（读写`[已证]`，字段名沿用旧文档） |
| +0xAC | 4 | ParticleTypeClass* | 0x62B5F4(ctor)、0x62D9CD | Draw 0x62CED6/0x62CEF3/0x62CF65（16 读） | Type 指针（ctor 形参写入、Draw 反复读类型标志） | `[已证]` |
| +0x124 | 4 | ParticleSystemClass* | 0x62B721(ctor) | （采样读在 ParticleSystem 侧） | 所属粒子系统 | `[静态推断]` |
| +0x12C | 1 | byte | 0x62B739/0x62BA4B(ctor) | 0（方法集内未采到） | 生命周期状态机 | `[未证]` |
| +0x12F | 1 | byte | 0x62B754(ctor) | Draw 0x62CFC4 | Translucency（半透明级） | `[静态推断]` |

### 3.3 ParticleSystemClass（size 0x100）

| 偏移 | 宽度 | 类型 | 写者地址 | 读者地址（采样≥3） | 语义 | 分级 |
|---|---:|---|---|---|---|:---|
| +0x9C | 12 | CoordStruct | Update/Draw 读写（普查 12 读） | Draw 0x62E32A(lea) | Location/发射源 | `[静态推断]` |
| +0xAC | 4 | PSysTypeClass* | 0x62DC6A(ctor)、0x62DF31(Update) | Draw 0x62E287（5 读） | Type 指针 | `[已证]` |
| +0xBC | — | vector 对象基址 | ctor `lea 0x62DC64` | Update `lea 0x62DF2B`（3 读 lea/+0xBC） | Particles 动态向量对象起点（YRpp `DynamicVectorClass`） | `[静态推断]`（容器身份`[已证]`，元素 stride 未定） |
| +0xE0 | 4 | ptr | 0x62DCC3(ctor)、0x62DF71(Update) 等 4 写 | 3 读（含 Draw 链） | Owner (TechnoClass*) | `[静态推断]` |
| +0xF4 | 4 | int | 0x62DCFA(ctor=0x1d=29)、0x62DF94(Update) | Draw 0x62E352 | **SpotlightRadius 默认 29**（ctor 写 29、Draw 读参与光照锥） | `[已证]` |
| +0xFC | 4 | HouseClass* | 0x62DD10/0x62FF6D(ctor) | （方法集内 0 读，外部读在剔除链） | OwnerHouse | `[静态推断]` |

> 字段语义边界：`+0x94` 在别的类是函数指针（R14 错源⑥ / KB §12），本卡**未跨类套用**；`+0xBC` 只断言"向量对象起点"，不断言元素步长。

---

## T4 · 更新入口与虚表槽语义

### 4.1 主 vtable 关键槽（完整 491 槽见 `EVIDENCE/T4_vtable_slots.tsv`）

| 槽 | 偏移 | AnimClass | ParticleClass | PSysClass | VoxelAnimClass | 语义（证据） | 分级 |
|---:|---:|---|---|---|---|---|:---|
| 11 | +0x2C | 0x426580→4 | 0x62D980→0x16 | 0x630210→0x18 | 0x74AB20→0x29 | WhatAmI (`mov eax,imm;ret`) | `[已证]` |
| 12 | +0x30 | 0x426530→0x1C8 | 0x62D970→0x138 | 0x630200→0x100 | 0x74AB10→0x148 | GetSize (`B8 imm C3`) | `[已证]` |
| 23 | +0x5C | 0x423AC0 | 0x5F3E70(共享默认) | 0x62FD60 | 0x749F30 | AI/Update（vtable 槽派发；Anim 的 0x423AC0 内逐帧写 +0x19D） | `[静态推断]` |
| 65 | +0x104 | 0x422C70(包装读+0x184再转) | 0x5F4B10(共享) | 0x5F4B10(共享) | 0x749B20(包装) | DrawIfVisible（`ret 0xC`；Anim 包装加 DelayTimer 门） | `[已证]` |
| 69 | +0x114 | 0x422CA0 | 0x62CEC0 | 0x62E280 | 0x749B70 | Draw（`ret 8` 形态；0 直接调用者，纯虚表派发） | `[已证]` |

⚠ 遵守纪律：`0x508F60` 曾被错标"每帧迷雾总入口"（R14 §962），实为 SpySat 翻转器；本卡**只按虚表槽 + 读写指令定语义，不按函数名反推**。

### 4.2 每帧更新入口（调用链，字节实证）

- **AnimClass**：逻辑更新 = v[23] `0x423AC0`（0 直接调用者 ⇒ 纯虚表派发；函数内 20+ 处读写 +0xC8、写 +0x19D、+0x184 dec 在 `0x424386`）。
- **ParticleSystemClass**：`0x62DF20`（直接调用者 `0x6C59CF`，LogicClass 区）、`0x62E070`（直接调用者 `0x630233`）——与 Draw `0x62E280` **完全分离**。
- **Draw 链（接口定位，T5）**：`Map::DrawIt 0x6D3D10`（调用者 `0x4F44DF/F4/0x4F4515`）→ `0x6D465F call 0x6D8DB0`（Object 绘制协调）→ v[65] → v[69]。所有 Draw 实现 0 直接调用者，纯虚表派发，与旧 FX 文档一致；S07 层/Blitter 已入账结论不重做。
（全部调用点见 `EVIDENCE/T4_update_callsites.tsv`；全 .text `E8 rel32` 单通道穷举）

---

## 结论与分级汇总

- 8 个 S20 类的 RTTI 名/TD/COL/vtable/槽数 `[已证]`；总量 1214 表/14044 槽**复现审计基线**。
- 4 个实例类 GetSize 双通道闭合 `[已证]`（0x1C8/0x138/0x100/0x148）；4 个 Type 类仅通道 A `[已证]`。
- 11 个字段有字节级读写证据（其中 +0x184 DelayTimer、+0x19D、+0xAC Type、+0xF4 SpotlightRadius 语义 `[已证]`；其余 `[静态推断]`）。
- 4 张主表的槽 11/12/65/69 语义 `[已证]`；更新入口调用链字节实证。
- 未决项见 `UNKNOWNS.md`；与旧文档/台账差异见 `DISAGREE.md`。
