# Blit 覆盖面「6/108 → Top10」优先级表与缺口清单

> 任务：MIMO-BLITTOP ｜ 执行：MiMo ｜ 模式：accept-edits（新建文档 + 脚本；不改代码）
> 基线：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`【只读，已复核】
> 产出：排序依据 + 108 项缺口清单 + Top10 + Top3 落地前提 + 真机插桩规格（交代码轨 ZCode 落地）
> 证据等级：`[实证]` / `[推演]` / `[待实测]` —— 严格区分，禁止把估算当实测

---

## 1. 结论摘要

1. **现状**：软件 blit 实现族 108 个（Blitter 57 + RLEBlitter 51），当前仅 Hook **6/108**（全部为 `@G` 16 位 RGB 非 RLE/RLE 基础变体）。
2. **遥测缺口**：`ra2render.log` 的 `[ra2render-telemetry]` **只有总量**（BlitCalls / BlitPixels / TargetScans），**无按函数分解**。不能从既有日志得到「每函数调用数 × 像素」分布。**[实证]** 见 §2。
3. **排序结论**：Top10 以三类静态证据排序（§5）。Top3 = `BlitTransXlatZRead@G`（单位重叠本体）→ `BlitTransDarkenZRead@G`（单位重叠影子）→ `RLEBlitTransXlatZRead@G`（步兵重叠本体 RLE）。这三项是单位绘制主路径在**重叠场景**下的真正热点变体，也是文档已定谳的 P0/P1。
4. **最大风险**：像素等价。RLE 族有 `overshoot` 偏移与 `zmap` 推进规则（原版存在 off-by-overshoot 缺陷，**严禁擅自纠正**），非 RLE 族有 Z 环绕（`0x00887644`）。见 §6。
5. **本卡不改代码**：`ra2render/**` 由 ZCode 独占；本卡只产出排序依据与规格。

---

## 2. E1 遥测可用性判定

**产物**：`out/re_work/mimo_blittop/log/telemetry_fields.txt`

### 2.1 可得字段（`ra2render.log` 3153 条 telemetry 行）

| 字段 | 出现次数 | 说明 |
|---|---:|---|
| `BlitCalls` | 3153 | **总量**调用次数 |
| `BlitPixels` | 3153 | **总量**像素（Mpx） |
| `TargetScans` | 3153 | 寻敌扫描次数 |
| `节流率` | 3153 | Target 节流百分比 |
| `平抑` | 3153 | 平抑次数 |
| `迷雾剔除机动单位` | 3129 | 迷雾门控 |
| `半透明迷雾格子` | 3110 | 迷雾 |
| `渲染单位` | 3129 | 渲染单位数 |
| `建筑剔除` / `弹道剔除` | 2913 | 迷雾 |
| `小地图灰化像素` / `雷达灰化*` | 1423–1490 | 雷达 |

### 2.2 不可得字段（本卡关心但日志中不存在）

- `PerFuncCalls` / `PerFuncPixels` / `BlitByFunction` / `FuncName` / `BlitCallsByTemplate` / `PixelsByTemplate`
- **任何形式的按函数 / 按模板分解**

### 2.3 口径声明（强制）

> ra2render-telemetry **只有总量**：`BlitCalls: N, BlitPixels: M Mpx`（无按函数分解）。
> **若要得到「每函数调用数 × 像素」分布，必须真机插桩（见 §7），不得编数。**

### 2.4 总 BlitCalls / BlitPixels 随行序量级曲线（摘录，全量见产物）

| 采样# | 行号 | BlitCalls | BlitPixels (Mpx) | TargetScans |
|---:|---:|---:|---:|---:|
| 0 | 189 | 1,842,127 | 204 | 4,059 |
| 390 | 1532 | 4,447,735 | 683 | 15,763 |
| 702 | 2044 | 6,237,668 | 755 | 24,225 |
| 1092 | 2434 | 18,602,819 | 1,460 | 84,667 |
| 1560 | 3235 | 1,710,020 | 426 | 2,128 |
| 2184 | 4062 | 4,478,887 | 433 | 139,939 |
| 2808 | 7713 | 665,768 | 102 | 18,264 |
| 3152 | 11328 | 914,494 | 132 | 24,587 |

> ★ 这是「总量随会话/行序」的量级，**不是按函数分解**。峰值 18.6M calls / 1460 Mpx 出现在复杂场景段（行 2434 附近），与 perf 采样「复杂场景 blit 族占忙时 16.55%」量级吻合（**[推演]** 旁证，非同一 run）。

### 2.5 日志劫持虚表原文交叉核对（E2 用）

日志含 `成功劫持虚表 [?$...::v1]: 原入口 0x... -> 新入口 0x...` 原文，**原入口 VA 恒定**（无 .reloc，静态地址即运行时地址），新入口随 DLL 基址漂移。六项 blit 原入口：

| 名称 | 原入口 VA（日志 + 源码一致） |
|---|---|
| `?$BlitTransXlatAlphaZRead@G::v1` | `0x00494B60` |
| `?$BlitTransXlat@G::v1` | `0x004912B0` |
| `?$RLEBlitTransXlat@G::v1` | `0x004960A0` |
| `?$BlitTrans@G::v1` | `0x007BC890` |
| `?$BlitTransDarken@G::v1` | `0x00492670` |
| `?$BlitPlain@G::v1` | `0x007BC7F0` |

---

## 3. E2 覆盖现状表（已 Hook 6 项）

**来源**：`ra2render/blitter_hooks.cpp:2969-3007`（InstallVTableHooks）+ `ra2render/ra2render.h:12-27`（ADDR_VTABLE_*）+ `ra2render.log` 启动行交叉核对。

| # | RTTI 修饰名 | 虚表 VA | 被改槽(+4) | 原入口 VA | 位深/语义 | Hook 方式 | 证据锚点 |
|---:|---|---|---|---|---|---|---|
| 1 | `?$BlitTransXlatAlphaZRead@G` | `0x007E56F0` | `0x007E56F4` | `0x00494B60` | 16 位 · 透明/Xlat/alpha/ZRead | 虚表槽 1 | `ra2render.h:12` / `blitter_hooks.cpp:2975` / log L5 |
| 2 | `?$BlitTransXlat@G` | `0x007E5A20` | `0x007E5A24` | `0x004912B0` | 16 位 · 透明/Xlat（阵营色） | 虚表槽 1 | `ra2render.h:18` / `blitter_hooks.cpp:2981` / log L6 |
| 3 | `?$RLEBlitTransXlat@G` | `0x007E55C0` | `0x007E55C4` | `0x004960A0` | 16 位 · RLE/透明/Xlat | 虚表槽 1 | `ra2render.h:15` / `blitter_hooks.cpp:2987` / log L7 |
| 4 | `?$BlitTrans@G` | `0x007F7BF4` | `0x007F7BF8` | `0x007BC890` | 16 位 · 透明（跳过色键） | 虚表槽 1 | `ra2render.h:21` / `blitter_hooks.cpp:2993` / log L152 |
| 5 | `?$BlitTransDarken@G` | `0x007E59F0` | `0x007E59F4` | `0x00492670` | 16 位 · 透明/变暗（阴影） | 虚表槽 1 | `ra2render.h:24` / `blitter_hooks.cpp:2999` / log L153 |
| 6 | `?$BlitPlain@G` | `0x007F7BC4` | `0x007F7BC8` | `0x007BC7F0` | 16 位 · 不透明 | 虚表槽 1 | `ra2render.h:27` / `blitter_hooks.cpp:3005` / log L168 |

**Hook 口径**：只改 vtable+4（Blit 槽）；CallBlit0/1/2 为薄包装转发，虚表改完自动跟随。**[实证]**（`nonrle_blit_and_named_hotspots.md:57`）

---

## 4. E3 覆盖缺口清单（108 项全量）

**产物**：`out/re_work/mimo_blittop/table/gap_inventory_108.md` + `.tsv`（108 行机器可读）

- 来源：`out/reverse/m1_blit_targets.txt`（MSVC RTTI 解析，非人工标注）
- 统计：Blitter 57 + RLEBlitter 51 = 108；已 Hook **6/108**；未 Hook **102**
- 虚函数槽：Blitter 5 槽（dtor / Blit / CallBlit0 / CallBlit1 / CallBlit2）；RLEBlitter 3 槽（dtor / Blit / CallBlit）
- 位深：`@G`（16 位 RGB）主导；`@E`（8 位调色板）共 15 项
- 语义粗计：含 ZRead 48；含 ZReadWrite 24；含半透明/Lucent 40；含 Alpha 32；含 Warp 12

### 4.1 全量 108 行（摘要）

完整 108 行见产物 `gap_inventory_108.md`（每行：RTTI / 位深 / 语义 / 虚表 VA / 各槽入口 VA / 是否已 Hook）。此处摘录已 Hook 6 + 语义最热的 14 项：

| # | 族 | RTTI | 语义 | 虚表 | Blit 入口 | Hook |
|---:|---|---|---|---|---|---|
| 42 | Blit | `?$BlitTransXlatAlphaZRead@G` | 透明/Xlat/alpha/ZRead | `0x007E56F0` | `0x00494B60` | ✅ |
| 53 | Blit | `?$BlitTransXlat@G` | 透明/Xlat | `0x007E5A20` | `0x004912B0` | ✅ |
| 105 | RLE | `?$RLEBlitTransXlat@G` | RLE/透明/Xlat | `0x007E55C0` | `0x004960A0` | ✅ |
| 9 | Blit | `?$BlitTrans@G` | 透明 | `0x007F7BF4` | `0x007BC890` | ✅ |
| 10 | Blit | `?$BlitTransDarken@G` | 透明/变暗 | `0x007E59F0` | `0x00492670` | ✅ |
| 2 | Blit | `?$BlitPlain@G` | 不透明 | `0x007F7BC4` | `0x007BC7F0` | ✅ |
| **59** | Blit | `?$BlitTransXlatZRead@G` | 透明/Xlat/ZRead | `0x007E5978` | `0x00492B00` | 否 |
| **24** | Blit | `?$BlitTransDarkenZRead@G` | 透明/变暗/ZRead | `0x007E5948` | `0x00492D20` | 否 |
| **110** | RLE | `?$RLEBlitTransXlatZRead@G` | RLE/透明/Xlat/ZRead | `0x007E5560` | `0x004965B0` | 否 |
| **72** | RLE | `?$RLEBlitTransDarkenZRead@G` | RLE/透明/变暗/ZRead | `0x007E5540` | `0x00496820` | 否 |
| 34 | Blit | `?$BlitTransLucent50@G` | 透明/50% 半透明 | `0x007E59C0` | `0x00492830` | 否 |
| 17 | Blit | `?$BlitPlainXlat@G` | 不透明/Xlat | `0x007E5A38` | `0x004924C0` | 否 |
| 62 | Blit | `?$BlitTransZRemapXlat@G` | 透明/ZRemap/Xlat | `0x007E5A08` | `0x00492590` | 否 |
| 60 | Blit | `?$BlitTransXlatZReadWrite@G` | 透明/Xlat/ZReadWrite | `0x007E5888` | `0x00493600` | 否 |

---

## 5. E4 优先级排序（Top10）

### 5.1 三类静态证据口径

| 证据类 | 来源 | 口径 | 局限 |
|---|---|---|---|
| **(a) 调用点密度** | `tools/xref_scan.py` / `xref_abs` 批扫 gamemd.exe | 相对 call/jmp 目标落在 blit 入口；绝对 dword 引用（imm/data） | ★虚函数主路径是 `call [vtable+4]` **间接派发**，直接 call 入口 ≈ 0。xref 只能给出「虚表槽被字面引用次数」（vtRef）作弱代理。**[实证]** 产物 `xref/xref_density.tsv` |
| **(b) 语义热度** | `rle_blit_family.md` / `nonrle_blit_and_named_hotspots.md` / `blitter_microkernel_deep_dive.md` / `HOOK_POINT_MATRIX.md` / `ARCHITECTURE_ATLAS.md` | 单位绘制主路径 / 爆炸半透明 / ZRead 遮蔽 / 步兵 RLE 的既有定谳 | 文档级定谳，非本次新实测 |
| **(c) 已知实测旁证** | `out/reverse/perf-profile.md` + `docs/REWRITE_RESEARCH.md:168-181` | 采样剖析：blit 族占忙时 11.55%→16.55%；`BlitTransXlatAlphaZRead@G` 复杂场景独占 **15.64%**（已 Hook）；`BlitPlain@G` 0.7%（已 Hook） | 采样是「时间占比」非「每函数调用×像素」；且已 Hook 项已被测量，**未 Hook 项无直接实测** |

### 5.2 Top10 表

排序规则：语义热度（重叠主路径 > 半透明 > 不透明）× 实现可复用性 × 落地风险（像素等价难度）优先；xref 作弱代理；已 Hook 项不入表。

| 排名 | 函数 | 语义 | 排序依据（分级） | 预估收益档 | 落地风险（像素等价难度） |
|---:|---|---|---|---|---|
| 1 | `?$BlitTransXlatZRead@G` | 透明/Xlat/ZRead | [实证] nonrle §2 P0「单位重叠本体主路径」；[实证] ARCHITECTURE_ATLAS `0x007E5978`；[推演] 重叠时替代已 Hook 的 `BlitTransXlatAlphaZRead` 更瘦路径 | **高**（重叠单位本体） | 中：Z 逐像素比较 + `zBuf` 环绕（`0x00887644`）；无 overshoot/zmap |
| 2 | `?$BlitTransDarkenZRead@G` | 透明/变暗/ZRead | [实证] nonrle §2 P0「单位重叠影子路径」；[实证] `HOOK_POINT_MATRIX:107` P1；SIMD 收益最大（纯 dst RMW） | **高**（重叠阴影） | 中：同上 Z 环绕 + DarkenMask（`this+0x04` 是 **uint16 值**非指针，解引用会 Crash） |
| 3 | `?$RLEBlitTransXlatZRead@G` | RLE/透明/Xlat/ZRead | [实证] HOOK_POINT_MATRIX:104 P1「步兵重叠本体深度遮挡」；[实证] rle_blit §3.5/§9 已定谳 overshoot+zmap 规则；[推演] 步兵数量大 | **高**（步兵重叠本体） | **高**：overshoot 偏移 + zmap 推进（原版 off-by-overshoot **严禁纠正**）+ EncodedLen 左裁剪 |
| 4 | `?$RLEBlitTransDarkenZRead@G` | RLE/透明/变暗/ZRead | [实证] HOOK_POINT_MATRIX:105 P1「步兵重叠影子」；[实证] blitter_microkernel §3.2；DarkenMask 致命缺陷预警 | **高**（步兵重叠影子） | **高**：同 #3 + DarkenMask（`this+0x04` 为掩码值） |
| 5 | `?$BlitTransLucent50@G` | 透明/50% 半透明 | [实证] nonrle §2 P1「超时空/心灵/隐形半透明」；公式 `((s>>1)&m)+((d>>1)&m)` 完美 SIMD | 中高（爆炸/超时空） | 低：移位+掩码混色，无 Z/zmap |
| 6 | `?$BlitPlainXlat@G` | 不透明/Xlat | [实证] nonrle §2 P1「不透明帧也常带阵营色」；纯查表写入 | 中（阵营色帧） | 低：无透明跳过、无 Z |
| 7 | `?$BlitTransZRemapXlat@G` | 透明/ZRemap/Xlat | [实证] nonrle §2 P2；双查表 `xlat[remap[idx]]` | 中（深度重映射单位） | 中：双重 gather |
| 8 | `?$BlitTransXlatZReadWrite@G` | 透明/Xlat/ZReadWrite | [实证] nonrle §2 P2；回写 `zBuf[i]=zMin` | 中（重叠+深度写回） | 中：Z 环绕 + 回写值必须是 `zMin` |
| 9 | `?$BlitTransLucent25@G` / `?$BlitTransLucent75@G` | 透明/25%·75% 半透明 | [实证] nonrle §2 P3；与 Lucent50 同模板参数化 | 中低 | 低：与 #5 共享模板 |
| 10 | `?$RLEBlitTransDarken@G` | RLE/透明/变暗 | [推演] 非 Z 版步兵阴影；rle_blit §4.2；DarkenMask 同 #2 | 中低（步兵影子） | 中：RLE overshoot + DarkenMask |

### 5.3 xref 调用点密度（弱代理，全量见产物）

```
   #  call+jmp   imm  vtRef  allCJ  HK  name
   5         0     0      4      0   N  ?$BlitPlainXlatAlpha@G
   1         0     0      3      0   N  ?$BlitPlain@E
   2         0     0      3      0   Y  ?$BlitPlain@G
  ...
  42         0     0      2      0   Y  ?$BlitTransXlatAlphaZRead@G
```

**口径声明**：全部 108 项的直接 `call/jmp` 到入口 VA = **0**。blit 函数经虚表间接派发（`call [vtable+4]`），静态 xref 无法计数运行期调用次数。`vtRef`（虚表地址被 dword 字面引用次数）是唯一静态代理，量级 2–4，区分度不足。**因此排序主依据是 (b) 语义热度 + (c) 已知实测旁证；(a) 仅作弱验证。[实证]**

---

## 6. E5 前三项落地前提

### 6.1 Top1 `?$BlitTransXlatZRead@G`（单位重叠本体）

| 项 | 值 |
|---|---|
| 目标虚表槽 | `0x007E597C`（vtable `0x007E5978` + 4） |
| 原入口 VA | `0x00492B00` |
| FileOffset | `0x00092B00` |
| 原序言 8 字节 | `8B 54 24 0C 8B 44 24 14` |
| 反汇编 | `mov edx, [esp+0xC]` / `mov eax, [esp+0x14]` |
| 调用约定 | `__thiscall` `ret 0x20`（8 DWORD） |
| slots | `0x0049A000` `0x00492B00` `0x00492BA0` `0x00492B70` `0x00492BD0` |

**像素语义要点**：
```c
while (length-- > 0) {
    uint16_t zb = *zBuf++; zbuf_wrap();          // Z 环绕：0x00887644 描述符
    int idx = *src++;                             // 无论 Z 是否通过都推进
    if (zb > zMin && idx) *dst = xlat[idx];       // 透明跳过 idx==0
    dst++;
}
```
- 透明判据：`idx==0` 跳过
- Z 判定：`zBuf[i] > zMin`（严格大于，`jge` 跳过）
- **src/dst/zBuf 每像素齐头并进**（位置对齐密集流，与 RLE 根本不同）`[实证]` nonrle §2.2

**像素等价对拍要点**：
1. Z 环绕必须正确：`*(void**)0x00887644`，`+0x1C=BufferEnd`、`+0x20=BufferSize`；`zBuf++` 后 `if (zBuf >= End) zBuf -= Size`。**现有 `Hook_BlitTransXlatAlphaZRead` 的 SIMD 忽略了环绕，是已知缺陷**（`blitter_microkernel_deep_dive.md:414`）——新实现**严禁**复现该缺陷。
2. **严禁**引入 EncodedLen / overshoot 语义（那是 RLE 族专属）。
3. Z 失败也必须 `src++` / `dst++`（汇编 `jge` 只跳过「读索引+写像素」）。

### 6.2 Top2 `?$BlitTransDarkenZRead@G`（单位重叠影子）

| 项 | 值 |
|---|---|
| 目标虚表槽 | `0x007E594C`（vtable `0x007E5948` + 4） |
| 原入口 VA | `0x00492D20` |
| FileOffset | `0x00092D20` |
| 原序言 8 字节 | `8B 54 24 0C 8B 44 24 14` |
| 调用约定 | `__thiscall` `ret 0x20` |
| slots | `0x0049A040` `0x00492D20` `0x00492DB0` `0x00492D80` `0x00492DE0` |

**像素语义要点**：
```c
if (zb > zMin && idx) *dst = (*dst >> 1) & this->DarkenMask;
```
- `this+0x04` 是 **`uint16_t DarkenMask`（值，典型 `0x7BEF`）**，**不是指针**
- ★**致命缺陷预警**：若解引用 `XlatTable`（把掩码当指针），直接 `0xC0000005` Crash（`blitter_microkernel_deep_dive.md:59`）

**像素等价对拍要点**：
1. DarkenMask 读取方式必须是值读取，**严禁**按 `XlatTable` 指针解引用。
2. Z 环绕同 Top1。
3. 写入是 RMW（读-改-写）：`*dst = (*dst >> 1) & mask`，**不能**换成其他混色公式。

### 6.3 Top3 `?$RLEBlitTransXlatZRead@G`（步兵重叠本体 RLE）

| 项 | 值 |
|---|---|
| 目标虚表槽 | `0x007E5564`（vtable `0x007E5560` + 4） |
| 原入口 VA | `0x004965B0` |
| FileOffset | `0x000965B0` |
| 原序言 8 字节 | `51 8B 44 24 14 8B 54 24` |
| 反汇编 | `push ecx` / `mov eax, [esp+0x14]` / `mov edx, [esp+...]` |
| 调用约定 | `__thiscall` `ret 0x28`（10 DWORD） |
| slots | `0x0049A820` `0x004965B0` `0x00496690` |

**像素语义要点**（RLE 族，与非 RLE 根本不同）：
- **EncodedLen = 左裁剪跳过像素数**（不是「编码长度」）`[实证]` rle_blit §9.2
- 阶段 A：解码跳过 EncodedLen 像素（只推 src，不动 dst）
- overshoot 修正：`overshoot = -EncodedLen`；`Length -= overshoot`；`dst += overshoot`；`zBuf += overshoot`（Z* 变体）
- 阶段 B：透明游程 `dst/zBuf/zmap += n`；实体像素逐个推进
- Z 测试：`zBuf[i] > (uint16_t)(zMin - zmap[i])`，`zmap[i]` 是 **signed char**（`movsx`）

**像素等价对拍要点（★严禁擅自纠正）**：

1. **overshoot 处的 zmap 推进**：原版在 `0x004965F0`/`0x004965F3` 推进了 `dst` 和 `zBuf`，**故意不推进 `zmap`**。这是已定谳的 **原版 off-by-overshoot 缺陷**（假说 b 属实，`rle_blit_family.md:810`）。
   > **SSE2 接管准则：必须原样复现原版逻辑（阶段 A 的 overshoot 不推进 zmap），不得私自「修正」该 overshoot 偏移。** `[实证]` rle_blit §9.1
2. **ZRead 推进规则**：阶段 A 完全不碰 zmap；overshoot 也不碰；只有阶段 B 的每个像素/游程推进（`inc ecx` / `add ecx, n`）。
3. **Z 测试方向**：`zBuf[i] > zMin - zmap[i]`（z 越大越靠前）。写反会把前后景弄颠倒。
4. **ZReadWrite 回写值**（若扩展）：必须是 `(uint16_t)(zMin - zmap[i])`，不能是 `zBuf[i]` 原值。
5. **EncodedLen 语义**：左裁剪跳过像素数，由调用方 `Draw_SHP (0x00437A10)` 计算为 `ClippedRect.X - OriginalRect.X`（`rle_blit_family.md:842`）。
6. **透明游程只推 dst/zBuf/zmap 不推 src**；实体像素推 src。与非 RLE 的「三者齐头并进」根本不同。

---

## 7. E6 真机插桩规格（纸面，交代码轨）

**目标**：得到「每函数调用数 × 像素」分布，以实测替换 §5 的语义热度推演。

### 7.1 计数点位置

在 **虚表槽 1（Blit）入口**（而非每个实现内部）插桩，对全部 108 个虚表统一处理：

```
for each vtable in 108:
    orig = vtable[1]                     # 原 Blit 入口
    vtable[1] = &Thunks[i]               # 108 个 trampoline
```

每个 `Thunks[i]`：
```
Thunks[i]:
    lock inc  [g_BlitCalls + i*4]        # 原子递增调用计数
    ; 从栈参读 length（非 RLE: [esp+0xC]；RLE: [esp+0xC]=Length）
    add     [g_BlitPixels + i*4], length # 像素累加（可用非原子 + 帧末汇总）
    jmp     orig                          # 尾调用原实现
```

### 7.2 开销 / 原子性考虑

| 项 | 建议 | 理由 |
|---|---|---|
| 调用计数 | `lock inc` 或 per-CPU + 汇总 | blit 可能多线程？——当前引擎单线程渲染，**普通 `inc` 即可**（`clock_frame_loop.md` 已证主逻辑单线程）`[实证]` |
| 像素累加 | 非原子 `add` | 性能敏感；误差可接受 |
| 采样节流 | 每 N 次调用或按帧汇总写盘 | 避免日志风暴（现有 telemetry 已是节流口径） |
| 频率 | 帧末或每 5s 输出一行 per-func 分解 | 与现有 `[ra2render-telemetry]` 行格式对齐 |

### 7.3 字段命名（建议）

```
[ra2render-blit-func] frame=12345
  ?$BlitTransXlatZRead@G calls=12345 pixels=67890
  ?$BlitTransDarkenZRead@G calls=2345 pixels=12340
  ... (仅输出 calls>0 的项)
```

### 7.4 可机械验证的验收判据

1. **守恒**：`sum(per-func BlitCalls) == BlitCalls`（总量）；`sum(per-func BlitPixels) == BlitPixels`（总量）。允许 ±1% 采样误差（若节流）。
2. **单调**：per-func 计数非负、单调不减。
3. **覆盖**：重放同一对局，Top10 表排名的 Kendall τ 与实测排名 ≥ 0.6（允许语义热度与实测偏差，但方向应一致）。
4. **零侵入**：插桩前后像素输出 bit-identical（已有像素对拍 harness 口径）。
5. **可关闭**：`ra2render.ini` 加 `BlitFuncTelemetry=0/1`，默认 0 时零开销（不装 trampoline）。

---

## 8. 排序依据方法论与局限

1. **xref 弱代理已如实声明**（§5.3）：虚函数间接派发导致静态 xref 无法给出真实调用密度。**不编数**。
2. **语义热度来自文档定谳**，不是本次新实测。每条已标 `[实证]`（指文档已有 VA+字节级定谳）或 `[推演]`。
3. **已知实测旁证**（15.64% / 0.7%）测的是**已 Hook 6 项**；未 Hook 项无直接实测。Top10 收益档是**预估**（`[推演]`），待 §7 插桩实测校准。
4. **「每函数调用数 × 像素」的 ROI 排序**在插桩前无法闭环——本表给的是「可辩护的优先级」，不是「实测 ROI 排序」。

---

## 9. 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 阻塞级别 |
|---:|---|---|---|---|
| 1 | 每函数调用数 × 像素 | 遥测只有总量；虚函数间接派发无静态 xref | 按 §7 插桩；重放 U0800_Accelerated_Skirmish + Brutal AI 场景 | **P0**（排序校准） |
| 2 | zmap 语义三假说中 (a) 的适用面 | 常规渲染 zmap=NULL 走全零兜底，overshoot 缺陷不暴露 | 构造 zmap 非平凡 SHP（高程阴影），对拍 overshoot 行 | P1 |
| 3 | Top10 收益档实测 | 无 per-func 分布 | 同 #1 | **P0** |
| 4 | 8 位 `@E` 族是否在现代渲染路径出现 | 现代 16 位模式下可能死代码 | 插桩后看 calls 是否 >0 | P2 |

---

## 10. 附录

### 10.1 产物清单

| 路径 | 说明 |
|---|---|
| `docs/re/blit_coverage_top10.md` | 本文件 |
| `out/re_work/mimo_blittop/log/telemetry_fields.txt` | E1 遥测字段 + 曲线 |
| `out/re_work/mimo_blittop/log/parse_telemetry.py` | E1 脚本 |
| `out/re_work/mimo_blittop/table/gap_inventory_108.md` | E3 全量 108 行 |
| `out/re_work/mimo_blittop/table/gap_inventory_108.tsv` | E3 机器可读 |
| `out/re_work/mimo_blittop/table/parse_m1_targets.py` | E3 脚本 |
| `out/re_work/mimo_blittop/xref/xref_density.tsv` | E4(a) 全量 xref |
| `out/re_work/mimo_blittop/xref/xref_density_summary.txt` | E4(a) 摘要 |
| `out/re_work/mimo_blittop/xref/prologues.txt` | E5 序言字节 |
| `out/re_work/mimo_blittop/xref/xref_density.py` | E4+E5 脚本 |
| `out/re_work/mimo_blittop/claims/claims.txt` | 14 条字节断言 |

### 10.2 门禁

- `python tools/verify_anchors.py` → **323/323 PASS**（原文见回报 [6]）
- `python tools/audit_bytes.py out/re_work/mimo_blittop/claims/claims.txt` → **14/14 OK**

### 10.3 写作用域合规

- 只写：`docs/re/blit_coverage_top10.md` + `out/re_work/mimo_blittop/**`
- 未触碰：`ra2render/**`、`ra2youli/**`、`out/reverse/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、其他 `docs/re/*.md`
- gamemd.exe MD5 复核：`4f37486e5b0dbe2ae5f45aeee0f98367`（与任务卡一致）

---

## 附录 L1 · Lead 保留判定（2026-09-28）

> 判定人：Lead。**不改写正文**，仅在文末追加保留判定；正文所有结论与证据表照旧有效。

1. **E4c「已知实测旁证」降级为 `[待 H1 重测]`**（★P1 口径）：本文 §E4 (c) 引用的 `out/reverse/perf-profile.md` 与 `docs/REWRITE_RESEARCH.md:168-181` 的占比数字（`11.55%→16.55%`、`15.64%`），其采样场景名为 `U0800_Accelerated_Skirmish`，而该图真机**只实例化 21/22 单位**（国家默认开局部队，非地图负载）⇒ 已由 `MIMO-H1VOID` 判为**作废**（见 `out/loadbench/H1_REMEASURE_RUNBOOK.md §0`）。
   ⇒ **上述百分比不得再作为低负载热点证据引用**；Top10 排序的**主依据 = (a) 语义/结构 + (b) 既有定谳文档**，而 (c) 只作**待重测的方向性提示**。
   ⇒ 本判定**不改变 Top3 结论**（Top3 的语义依据独立于该采样）。
2. **Lead 独立复算（不采信回报，自写脚本读字节）**：3 处序言（`0x492B00` / `0x492D20` / `0x4965B0`）与 3 处 vtable 槽（`0x7E597C → 0x492B00`、`0x7E594C → 0x492D20`、`0x7E5564 → 0x4965B0`）**6/6 MATCH**；`E8/E9` 直呼三入口全 exe 命中 **0**（复核其 E4a）；其 `claims.txt` 经 `tools/audit_bytes.py` **14/14 OK**。
3. **裁决其 [9] 两项待裁决**：
   - **① Top10 收益档口径 → 批准其建议**：保留现「高/中高/中/中低」四档作初值，**插桩实测后按 `pixels×calls` 百分位回填**（避免空窗）；回填时须同时声明「原档为语义预估」。
   - **② 插桩与 Top3 Hook 的批次 → 批准「先插桩→实测→再定序」**（而非先 Hook 再插桩）。理由：插桩是**只读遥测**（不改像素、不进同步契约），风险低于 Hook；且它把 Top10 从「语义预估」升级为「实测排序」，直接降低像素等价返工概率。
4. **联动提示（给代码轨）**：`docs/re/rle_blit_family.md` 的「loadbench 显示步兵 RLE 是真热点」一句已由 Lead 就地加【勘误】（同源低负载采样）⇒ 实施 Top3 时以该文档的**像素语义/对拍要点**为准，**不要**以「真热点」措辞作为优先级依据。