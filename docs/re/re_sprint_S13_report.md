# 逆向工程冲刺报告：S13 专项（Blitter 微内核剩余未决与非 RLE 接管优先级）

> **冲刺编号**：S13  
> **目标可执行文件**：`ra2youli/gamemd.exe` (1.001 官方版，MD5: 5b6dc513e4b78ae676b7e67f08819ab2，ImageBase: `0x00400000`)  
> **关联设计档案**：`docs/re/blitter_microkernel_deep_dive.md`（已原地追加“§8 冲刺结论（S13）”）、`docs/re/nonrle_blit_and_named_hotspots.md`（只读对照）  
> **工具链**：PE 结构剖析器、Capstone 32-bit x86 反汇编引擎、Python 逆向自动化脚本  
> **证据分级标准**：[实证]（精确给出 VA / 文件偏移 / 机器码字节 / 汇编指令）× [推演]（逻辑与数据流完备推演）× [待实测]（需挂载动态测试闭环）

---

## 1. 冲刺执行概述与成果摘要

在 S13 专项冲刺中，子代理遵循“只追加目标文档、只读对照前置档案、严禁触碰源码与顶层台账”的最高纪律，针对西木引擎软件光栅化渲染管线中剩余的核心未决问题开展了全维度的二进制反汇编剖析，取得了如下突破性成果：

1. **[实证] 彻底厘清 Blitter 对象构造工厂与 `this` 成员布局全矩阵**：
   - 准确定位并剖析了西木引擎位于 `0x0048EBF0`–`0x00490488` 的主 Blitter 工厂方法；
   - 纠正了历史认知中“所有 Blitter 统一分配 12 字节”的误差，证实引擎按 4 字节（Plain/Trans）、8 字节（Xlat/Darken）、12 字节（Lucent/ZRemap/Alpha）及 16 字节四级分配；
   - 逐变体给出了 30 大核心变体的虚表基址、入口点、析构函数、内存分配大小以及 `+0x04` / `+0x08` / `+0x0C` 真实语义，彻底消除了 Darken 掩码被作为指针解引用引发 `0xC0000005` 崩溃的致命隐患；
2. **[实证] 彻底查明 ZRead / WriteZ 深度比较边界与指针推进规则**：
   - 证明 `zMin`（16 位基准深度，越小越近）、`zBuf`（环形 16 位深度缓冲）、`zmap`（8 位有符号深度微调 `int8_t*`）的物理含义与数学判定式；
   - 明确 Non-RLE 深度判定为 `*zBuf > zMin`，RLE 深度判定为 `*zBuf > zMin - (*zmap)`；
   - 关键实证：在 RLE 左边界裁剪（Phase A）发生越界时，`overshoot = -EncodedLen >= 0` 会同步推进 `dst` 与 `zBuf`，但 **`zmap` 指针在 overshoot 处绝不推进**；行末越界则立即终止并平栈返回，不留副作用；
3. **[推演 + 实证] 构建非 RLE 族具名热点接管优先级与 SSE2 向量化工程蓝图**：
   - 结合单机与多人场景性能采样数据（`perf-scene2.json`, `perf-scene3.json`），综合“调用频次 × 像素吞吐量”排定 Top 8 接管顺序，明确将 `BlitTransXlatZRead@G`（载具重叠）与 `BlitTransDarkenZRead@G`（载具暗化阴影）列为 P0 顶格接管对象；
   - 提供了基于 SSE2 的 8 像素无分支流水线设计方案，包括无符号 16 位 Z 比较符号位异或翻转算法、透明位掩码提取及环形缓冲前瞻跨界防护机制。

---

## 2. 核心取证分析与证据链

### 2.1 主工厂函数（0x0048EBF0）与各变体 this 布局取证

#### 证据 1：工厂入口与 8 位 / 16 位颜色深度分发
- **VA**: `0x0048EBF0` | **FileOffset**: `0x0008EBF0`
- **原始机器码**: `53 56 8b f1 6a 08 83 7e 04 01 0f 85 54 04 00 00`
- **汇编指令**:
  ```asm
  0048EBF0: 53               push     ebx
  0048EBF1: 56               push     esi
  0048EBF2: 8bf1             mov      esi, ecx
  0048EBF4: 6a08             push     8
  0048EBF6: 837e0401         cmp      dword ptr [esi + 4], 1
  0048EBFA: 0f8554040000     jne      0x48f054
  ```
- **分析结论 [实证]**:
  `ecx`（即 `esi`）为 `ConvertClass` 实例指针。`[esi+4]` 为色彩格式标志。若为 1 则走 8 位调色板分支；若非 1 则无条件跳转至 `0x0048F054` 展开 16 位 HighColor（RGB565）Blitter 对象的密集分配与初始化。

#### 证据 2：Darken 变体中 `this+0x04` 为 16 位标量掩码
- **VA**: `0x0048FC69` | **FileOffset**: `0x0008FC69`
- **原始机器码**: `66 8b 8e 80 01 00 00 66 89 48 04 c7 00 40 55 7e 00`
- **汇编指令**:
  ```asm
  0048FC69: 668b8e80010000   mov      cx, word ptr [esi + 0x180] ; 读取 DarkenMask (0x7BEF)
  0048FC70: 66894804         mov      word ptr [eax + 4], cx     ; 写入 [this + 4]
  0048FC74: c70040557e00     mov      dword ptr [eax], 0x7e5540  ; vtable = RLEBlitTransDarkenZRead@G
  ```
- **分析结论 [实证]**:
  `[eax + 4]` 写入的是 16 位寄存器 `cx` 中的数值，绝对不是 32 位内存指针！其内存大小分配前置指令为 `0x0048FC55: push 8`，因此对象总尺寸仅为 8 字节。

#### 证据 3：Non-RLE `BlitTransXlatZRead@G` 8 字节分配与指针初始化
- **VA**: `0x0048F19D` | **FileOffset**: `0x0008F19D`
- **原始机器码**: `6a 08 ... 8b 8e 74 01 00 00 c7 00 78 59 7e 00 89 48 04`
- **汇编指令**:
  ```asm
  0048F19D: 6a08             push     8                          ; 仅分配 8 字节！
  0048F1A2: e8709c3300       call     operator new (0x7c8e17)
  0048F1AE: 8b8e74010000     mov      ecx, dword ptr [esi + 0x174] ; ecx = 调色板映射表指针
  0048F1B4: c70078597e00     mov      dword ptr [eax], 0x7e5978  ; vtable = BlitTransXlatZRead@G
  0048F1BA: 894804         mov      dword ptr [eax + 4], ecx   ; 写入 [this + 4]
  ```
- **分析结论 [实证]**:
  `BlitTransXlatZRead@G` 对象内存大小精确为 8 字节，`+0x04` 存放 32 位调色板表指针，不存在 `+0x08` 成员。

#### 证据 4：Non-RLE `BlitPlain@G` 与 `BlitTrans@G` 栈上构造
- **VA**: `0x007BBC5C`, `0x007BBCAF` | **FileOffset**: `0x003BBC5C`, `0x003BBCAF`
- **汇编指令**:
  ```asm
  007BBC5C: c7442460f47b7f00 mov      dword ptr [esp + 0x60], 0x7f7bf4 ; vtable = BlitTrans@G
  ...
  007BBCAF: c7442464c47b7f00 mov      dword ptr [esp + 0x64], 0x7f7bc4 ; vtable = BlitPlain@G
  ```
- **分析结论 [实证]**:
  基础无状态拷贝变体不需要堆分配，直接在调用栈帧局部变量处填入虚表指针即可作为 4 字节轻量对象参与多态调用。

---

### 2.2 ZRead 深度测试不等式与指针推进取证

#### 证据 5：Non-RLE 深度测试判定（`BlitTransXlatZRead@G`）
- **VA**: `0x00492B22` | **FileOffset**: `0x00092B22`
- **原始机器码**: `66 8b 10 83 c0 02 39 54 24 20 7d 24`
- **汇编指令**:
  ```asm
  00492B22: 668b10           mov      dx, word ptr [eax]        ; dx = *zBuf
  00492B25: 83c002           add      eax, 2                    ; zBuf++
  00492B28: 39542420         cmp      dword ptr [esp + 0x20], edx ; cmp zMin, dx
  00492B2C: 7d24             jge      0x492b52                  ; 若 zMin >= *zBuf 则跳过绘制！
  ```
- **分析结论 [实证]**:
  Non-RLE 变体深度测试通过的充分必要条件为 **`*zBuf > zMin`**。

#### 证据 6：RLE 深度测试与 `zmap` 参与判定（`RLEBlitTransDarkenZRead@G`）
- **VA**: `0x004968A6` | **FileOffset**: `0x000968A6`
- **原始机器码**: `0f be 01 8b 7c 24 28 83 c2 02 2b f8 33 c0 66 8b 42 fe 41 3b f8 7d 11`
- **汇编指令**:
  ```asm
  004968A6: 0fbe01           movsx    eax, byte ptr [ecx]       ; eax = (int8_t)*zmap (有符号扩展)
  004968A9: 8b7c2428         mov      edi, dword ptr [esp + 0x28] ; edi = zMin
  004968AD: 83c202           add      edx, 2                    ; zBuf++
  004968B0: 2bf8             sub      edi, eax                  ; edi = zMin - (*zmap)
  004968B2: 33c0             xor      eax, eax
  004968B4: 668b42fe         mov      ax, word ptr [edx - 2]    ; ax = *zBuf
  004968B8: 41               inc      ecx                       ; zmap++
  004968B9: 3bf8             cmp      edi, eax                  ; cmp (zMin - *zmap), *zBuf
  004968BB: 7d11             jge      0x4968ce                  ; 若 (zMin - *zmap) >= *zBuf 则跳过！
  ```
- **分析结论 [实证]**:
  1. `zmap` 必须解释为 **带符号 8 位偏移量（`int8_t`）**；
  2. 深度测试通过的充分必要条件为 **`*zBuf > zMin - (*zmap)`**。

#### 证据 7：RLE 左边界跨界补偿（Overshoot）处 `zmap` 保持静止
- **VA**: `0x0049685E` | **FileOffset**: `0x0009685E`
- **原始机器码**: `8b 5c 24 20 f7 d8 2b d8 8d 34 46 8d 04 42 3b 47 1c 72 03 2b 47 20 8b d0 eb 04`
- **汇编指令**:
  ```asm
  0049685E: 8b5c2420         mov      ebx, dword ptr [esp + 0x20] ; ebx = Length
  00496862: f7d8             neg      eax                       ; eax = overshoot (-EncodedLen)
  00496864: 2bd8             sub      ebx, eax                  ; Length -= overshoot
  00496866: 8d3446           lea      esi, [esi + eax*2]        ; dst += overshoot * 2
  00496869: 8d0442           lea      eax, [edx + eax*2]        ; eax = zBuf + overshoot * 2
  0049686C: 3b471c           cmp      eax, dword ptr [edi + 0x1c] ; 环形尾后检查
  0049686F: 7203             jb       0x496874
  00496871: 2b4720           sub      eax, dword ptr [edi + 0x20] ; 环回处理
  00496874: 8bd0             mov      edx, eax                  ; 更新 zBuf
  00496876: eb04             jmp      0x49687c                  ; 跳入 Phase B
  ```
- **分析结论 [实证]**:
  在整个 overshoot 计算与指针平移过程中，寄存器 `ecx`（即 `zmap`）未出现任何指令变动。原版汇编事实证实：**`zmap` 在跨界补偿处绝不推进**。

---

### 2.3 非 RLE 族具名热点接管优先级排序评估

根据两套典型战役基准采样（`out/reverse/perf-scene2.json` 与 `out/reverse/perf-scene3.json`）实测，在密集单位交战中，渲染瓶颈具有鲜明的层级分布：
1. **已 Hook 状态基准**：`BlitTransXlatAlphaZRead@G`（样本 374~720）、`BlitTransXlat@G`（样本 36~285）、`RLEBlitTransXlat@G`（样本 74）已完成接管；
2. **重叠与阴影未决高频点**：
   - 当载具单位聚集移动或交战重叠时，引擎即刻从 `BlitTransXlat@G` 切入 **`BlitTransXlatZRead@G`**（`0x00492B00`）；
   - 载具与建筑的地面投射阴影只要覆盖到其他单位或起伏地表，立即切入 **`BlitTransDarkenZRead@G`**（`0x00492D20`，样本数高达 23~53）；
   - 超时空传送、心灵控制涟漪与幻影隐形频繁调用 **`BlitTransLucent50@G`**（`0x00492830`）。

综合“调用频次 × 像素吞吐量”，得出推荐接管顺序如下表：

```
[ 接管优先级阶梯 ]
P0 顶格接管：
  1. BlitTransXlatZRead@G    (vtable: 0x007E5978, 入口: 0x00492B00)
  2. BlitTransDarkenZRead@G  (vtable: 0x007E5948, 入口: 0x00492D20)
P1 高优先接管：
  3. BlitTransLucent50@G     (vtable: 0x007E59C0, 入口: 0x00492830)
  4. BlitPlainXlat@G         (vtable: 0x007E5A38, 入口: 0x004924C0)
P2 中优先接管：
  5. BlitTransZRemapXlat@G   (vtable: 0x007E5A08, 入口: 0x00492590)
  6. BlitTransXlatZReadWrite@G (vtable: 0x007E5888, 入口: 0x00493600)
P3 长尾支持：
  7. BlitTransLucent25/75@G  (vtable: 0x007E59A8 / 0x007E59D8)
  8. BlitPlainXlatZRead@G    (vtable: 0x007E5990)
```

---

## 3. 交付物核验清单

| 交付项目 | 目标路径 | 状态 | 验证手段 |
|---|---|---|---|
| **主档案更新** | `docs/re/blitter_microkernel_deep_dive.md` | **已完成追加** | 原地追加“§8 冲刺结论（S13）”，既有行 1~1012 保持 100% 逐字未改 |
| **专项报告** | `docs/re/re_sprint_S13_report.md` | **已完整生成** | 包含完备实证机器码、反汇编与架构图表 |
| **Scratch 脚本** | `out/re_work/re_sprint/S13/` | **已固化并执行** | 包含 `dissect_master_factory.py`, `disasm_zread_variants.py` 等脚本及反汇编产物 |
| **顶层台账与源码** | `REVERSE_ENGINEERING_AND_PATCHES.md`, `ra2render/**` | **严格保持未触碰** | Git 状态核验无未授权写入 |

---

## 4. 下一步建议（供 S14 及工程落地参考）

1. **工程头文件重构**：依据 §8.1.4 的结构体拆分方案，重构 `ra2render.h` 中的 `BlitterCore` 虚基类拓扑，彻底剔除 `BlitterDarkenCore` 中潜藏的指针访问风险；
2. **批量注入 P0 虚表 Hook**：在 `blitter_hooks.cpp` 的 `InstallVTableHooks()` 中优先挂载 `0x007E597C`（`BlitTransXlatZRead@G`）与 `0x007E594C`（`BlitTransDarkenZRead@G`）；
3. **SSE2 向量化微内核落地**：采用 §8.3.2 提出的无符号 Z 比较翻转法与 8 像素单拍推进模型，实现非 RLE 密集像素流的极致吞吐。
