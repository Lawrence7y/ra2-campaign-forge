# R-SBH-UAF 残差闭环：SBH freelist/UAF 写者 × CRT 池化 L2 × 存档/MP

> [META]
> 任务=R-SBH-UAF / SBH freelist & UAF writer 残差闭环 · 执行=R 轨逆向取证代理 · 日期=2026-09-30
> 目标二进制：`ra2youli/gamemd.exe`（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x00400000`）
> 写作用域：本文件 + `out/re_work/re_sprint/R_sbh_uaf/**`；二进制只读
> 上游：`docs/re/sbh_freelist_deep_dive.md`（R-02）、`docs/re/sbh_uaf_writer_deep_dive.md`（R-05）
> 交叉：`docs/re/crt_memory_pool_deep_dive.md`、`docs/re/crt_pool_risk_review.md`、`docs/re/landing_pack_crt_audio_particle.md`
> 存档：`docs/re/savegame_block_manifest.md`（T7 OLE 口径）、`docs/re/net_sync_checksum.md`
> 证据分级：`[实证]` 字节+反汇编可复算 · `[推演]` 由代码逻辑推断 · `[待实测]` 需运行时

---

## [0] 结论速览（≤12 行）

1. **[实证]** R-02 U4 闭环：`0x7CFFC8` = `__sbh_resize_block`（原地扩/缩），唯一调用者 `0x7D0FA5`（realloc 路径）；`0x7D0A20` = CRT `memcpy`（11 个调用者含 realloc 拷贝）；`__sbh_alloc_block` 另有 `0x7D33AB` 第三入口。
2. **[实证]** R-02 U5 闭环：page-group decommit（`0x7CFA0C`）**不**清 freelist head；但 recommit（`0x7CFECD`）在 `VirtualAlloc` 前**重建全部 64 个 class head 自环**（`0x7CFEFD`–`0x7CFF07`）+ 清 `grp_bm_lo`、写 `grp_bm_hi=1`，旧 head 被覆盖 → **无残毒面**。
3. **[实证]** R-02 U1 闭环（静态）：class 4 共 **49** 处 `_new` 立即数分配点（R-05 记 31，本轮补齐 18 处 register-adjacent）；类型映射已 vtable 定名。
4. **[实证]** CRT 池化 L2 桶（8/12/16/24/40/312/352/456B）**不覆盖 class 4**（57..72B）——L2 的双释放/投毒/守卫对崩溃 class **零防护**。
5. **[实证]** 找到「写已释放块」首要静态站点：`BasePlanningCellContainer::AddCapacity 0x510860`（`new(cap*8)` → copy → `_delete` 旧 buffer → `Items=new`）；cap 8/9 时 buffer = 64/72B = class 4，free 后旧 `Items` 即 free 节点 `next` 位。
6. **[实证]** `WaypointPathClass` ctor `0x763810`：`+0x28=0x7F6ED4`（内嵌向量/vtable）、`+0x3C=0xA`（CapacityIncrement=10）→ 扩容步进 +10，cap 8→18 会跨 class 4 窗口。
7. **[实证]** 存档/MP **无堆地址进档**：`.SAV` 为 OLE2/CFB，对象寻址 = CLSID（`OleSaveToStream` IAT `0x7E15F4`）；`Save_Core` 的 43 处 imm 均为 `.bss` 子系统对象 VA（`mov edx,imm` 传 this），非用户堆指针；帧 CRC 输入 = 量化坐标 + RNG。
8. **[实证]** `FillEvent_Waypoints 0x4C6780` 落盘的是 `CellStruct` 坐标对 + frame 计数（`[0xA8ED84]`），无指针字段。
9. **[推演]** 毒值 `FE00FFFF` = `CellStruct{X=-1,Y=-512}` 写穿 class-4 free 节点 `next` 的主假设维持；`AddCapacity 0x510860` 是其最贴切的 free 点。
10. **[推演]** L2 池化若要覆盖 class 4，须新增 64/72B 桶（`SizeToPoolIdx: 57..72 → idx 8`）+ 8B 头 + `0xDEADBEEF` 投毒；否则 H2/H6 钩子是唯一可见性手段。
11. **[待实测]** U3（LFH 相关性）、U6（毒值业务字面归因）仍需 runtime A/B + heap dump。
12. **[实证]** R-02 §8 六项残差：U1/U4/U5 **静态闭环**；U2/U6 **部分闭环**（写者站点已收敛到 `0x510860` 族）；U3 **仍开**。

---

## [1] R-02 残差逐项复核（U1–U6）

| # | 项 | 改前等级 | 本轮动作 | 闭环结论 | 证据 |
|---|---|---|---|---|---|
| U1 | class 4 对象类型 | `[待实测]` | 静态扫 `_new` imm 0x39..0x48（28B 窗）得 **49** 点；结合 R-05 vtable 映射 | **静态闭环**：Trigger/Tag/WaypointPath/AlphaShape/DiskLaser/PixelFX/Walk/TunnelLoco/BitFont/INI 节点/MSAnim 族/Multiplayer* / 无 vtable 列表容器 `0x408B7B` / FX `0x65FB80` | `waf_sites_scan.txt` §class-4 sites |
| U2 | UAF 写者路径 | `[待实测]` | 扫 delete-后-offset0 写形；深挖向量扩容 free 点 | **部分闭环**：`AddCapacity 0x510860`（free old Items）为首要 free 点；写者 = 悬垂 `WaypointClass*/BasePlanningCell*` 写 `Coords` | `waf_sites_scan.txt`、`wpt_vector_uaf_shape.txt` |
| U3 | LFH 弱相关 | `[待实测]` | 无 runtime | **仍开**：需 A/B 三组（原版/注入/注入+EnableLFH=0） | — |
| U4 | `0x7CFFC8`/`0x7D0A20` | `[推演]` | 全函数反汇编 + 调用者扫描 | **静态闭环**：见 §2 | `u4_u5_residual_disasm.txt` |
| U5 | page-group 回收后 head 清空 | `[推演]` | decommit vs recommit 对照 | **静态闭环**：见 §3 | `u5_head_clear_proof.txt` |
| U6 | 毒值业务字面 | `[待实测]` | 位拆 + 常量反查（继承 R-05） | **部分闭环**：`CellStruct{-1,-512}` 主 / RGB565 次；需 dump | R-05 `poison_semantics_deep.txt` |

---

## [2] U4 闭环：`__sbh_resize_block` 与 `memcpy` 语义（`[实证]`）

### 2.1 `0x7CFFC8` = `__sbh_resize_block(region, ptr, new_req)`

入口序言 `push ebp; mov ebp,esp; sub esp,0xC`。关键序列：

```
0x7CFFD1  mov eax,[ebp+0x10]        ; new_req
0x7CFFDC  lea esi,[eax+0x17]
0x7CFFE5  and esi,0xFFFFFFF0        ; new_block = (req+0x17)&~0xF
0x7CFFDF  sub edx,[ecx+0xC]         ; ptr - region.base
0x7CFFE8  shr edx,0xF               ; group index
0x7CFFED  imul ecx,ecx,0x204
0x7CFFF3  lea ecx,[ecx+eax+0x144]   ; freelist_base
0x7CFFFD  mov ecx,[edi-4]           ; old size (with INUSE bit)
0x7D0000  dec ecx
0x7D0003  cmp esi,ecx               ; new_block vs old_size
0x7D0011  jle 0x7D0176              ; shrink path
0x7D0017  test bl,1                 ; next block INUSE?
0x7D0020  add ebx,ecx               ; try absorb next
0x7D0022  cmp esi,ebx
0x7D0024  jg 0x7D016F               ; cannot grow in place → alloc-copy-free
```

- **可原地扩**：后继块空闲且合并后够大 → 合并后分裂 remainder，入链（`0x7D003F`–`0x7D00E4` 的 unlink/insert 与 `__sbh_alloc_block` 同构）。
- **不可原地扩**：走 `0x7D016F` → 调用方转 `alloc-copy-free`。
- **缩**：`0x7D0176` 切 remainder 重新入链。

**调用者**：仅 `0x7D0FA5`（`realloc` 内部）`[实证]`。`__sbh_alloc_block 0x7CFB13` 的调用者共 3 处：`0x7C9484`（heap_alloc）、`0x7D0FB6`（realloc）、`0x7D33AB`（第三入口，疑 `expand`/`recalloc` 族）。

### 2.2 `0x7D0A20` = CRT `memcpy`（对齐优化版）

标准 MSVC6 memcpy：先判重叠（`0x7D0A34`–`0x7D0A3A`），按 dest 对齐跳表 `rep movsd` + 尾字节。**11 个调用者**：`0x7C9549, 0x7C9660, 0x7CC8DA, 0x7CDDDB, 0x7CDE0C, 0x7CE014, 0x7CE02C, 0x7D0FCF, 0x7D1013, 0x7D48B1, 0x7D5EDC`——含 realloc 拷贝两处（`0x7D0FCF/0x7D1013`）。

> **[实证] 结论**：U4 非独立漏洞面；realloc 扩容失败时的 `alloc-copy-free` 是**又一个 class-4 buffer free 点**，与 §5 向量扩容同构。

---

## [3] U5 闭环：page-group 回收 vs 重建（`[实证]`）

### 3.1 Decommit 路径（`__sbh_free_block` 尾 `0x7CFA0C`–`0x7CFB0E`）

触发：group 内块计数 `[heap_info+group*4+0x44]`？不 —— 是 `dec dword ptr [eax]`（`0x7CFA0C`）递减**该 group 的 in-use 页计数**，归零且非 cur group 时：

| 步骤 | VA | 操作 |
|---|---|---|
| 1 | `0x7CFA3F` | `VirtualFree(base+g*0x8000, 0x8000, MEM_DECOMMIT)`（IAT `[0x7E1290]`） |
| 2 | `0x7CFA53` | `or [region+8], 1<<g` 置回未提交位图 |
| 3 | `0x7CFA64` | `and [heap_info+g*4+0xC4], 0` 清 **grp_bm_hi[g]** |
| 4 | `0x7CFA74` | `dec [heap_info+0x43]`（cls_grp_cnt[63]） |
| 5 | `0x7CFA85` | 若 cnt 归零 → 清 region 位图 class-63 bit |

**缺口确认**：本段**没有**清 `grp_bm_lo[g]`（`+0x44`）、**没有**清 freelist head 数组（`+0x144+g*0x204`）。旧 `next/prev` 指针仍留在 heap_info 里指向已 DECOMMIT 的页。

### 3.2 Recommit 路径（`0x7CFECD`–`0x7CFFC7`）——**关键自愈点**

| 步骤 | VA | 操作 |
|---|---|---|
| 1 | `0x7CFEEC`–`0x7CFEF3` | `freelist_base = heap_info + g*0x204 + 0x144` |
| 2 | **`0x7CFEFD`–`0x7CFF07`** | **64 次循环：`[head+4]=head; [head+8]=head`（全 class head 自环重置）** |
| 3 | `0x7CFF1E` | `VirtualAlloc(base+g*0x8000, 0x8000, MEM_COMMIT)` |
| 4 | `0x7CFF3D`–`0x7CFF74` | 逐页车 `0xFF0` 空闲块（页哨兵 `-1`、尾 size `0xFF0`） |
| 5 | `0x7CFF84`–`0x7CFF90` | 8 页块链成 class-63 双向链（head 自环已空） |
| 6 | `0x7CFF93` | `and [heap_info+g*4+0x44], 0` **清 grp_bm_lo[g]** |
| 7 | `0x7CFF98` | `mov [heap_info+g*4+0xC4], 1` 只置 class-63 bit |
| 8 | `0x7CFFBE` | `and [region+8], ~(1<<g)` 清未提交位 |

> **[实证] 判定**：decommit 残留的旧 head 在 recommit 第 2 步被**无条件覆盖为自环**，且 `grp_bm_lo` 同步清零。因此「page-group 回收后 head 残毒」**不成立**——除非在 decommit 与 recommit 之间有代码直接读该 group 的 head（alloc 只会经位图命中后才读 head，而 `grp_bm_hi[g]` 已在 decommit 第 3 步清零，`grp_bm_lo` 本就该空）。U5 **静态闭环**。

### 3.3 全 Region 退役（`0x7CFA8E`–`0x7CFAD6`）

当 `region+8 == -1`（32 组全未提交）：`VirtualFree(MEM_RELEASE)` 整 1MB + `HeapFree(heap_info)` + `memmove`（`0x7CA090`）压缩 region 数组、`dec [0xB78B94]`。heap_info 整体释放 → head 数组随之消失，无残毒。

---

## [4] CRT 池化 L2 × SBH 覆盖交叉（`[实证]`）

### 4.1 桶映射（L2 `SizeToPoolIdx` vs SBH size-class）

L2 桶定义（`landing_pack_crt_audio_particle.md` §2）：`≤8 / ≤12 / ≤16 / ≤24 / ≤40 / 312 / 352 / 456`。

| L2 idx | req 窗 | SBH block | SBH class | L2 防护生效 |
|---|---|---|---|---|
| 0 | 1..8 | 16 | 0 | **是** |
| 1 | 9..12 | 32 | 1 | **是** |
| 2 | 13..16 | 32 | 1 | **是**（与 idx1 同 class） |
| 3 | 17..24 | 32 | 1 | **是**（与 idx1/2 同 class） |
| 4 | 25..40 | 48 | 2 | **是** |
| — | **41..56** | **64** | **3** | **否**（L2 空洞） |
| — | **57..72** | **80** | **4** | **否（崩溃 class）** |
| — | 73..1008 | … | 5..63 | 否 |
| 5 | 312 | 320 | 19 | **是** |
| 6 | 352 | 368 | 22 | **是** |
| 7 | 456 | 464 | 28 | **是** |

> **[实证] 要点**：L2 三个小桶（9/12/16/24B）**全部塌缩到 SBH class 1**；class 3（41..56B）与 **class 4（57..72B）完全在 L2 覆盖面之外**。

### 4.2 双释放 / 投毒 / 守卫矩阵

| 机制 | L2 小桶 (0-4) | L2 实体 (5-7) | **SBH class 4** | SBH 其它 class |
|---|---|---|---|---|
| 双释放检出 | **是**（free 时 magic→`0xDEADBEEF`） | 是 | **否**（retail SBH 无 tag，free_block 重插=自环） | 否 |
| free 投毒 | **是**（`0xDEADBEEF`） | 是 | **否**（只写 next/prev/size） | 否 |
| alloc 守卫 | 部分（P-M3 范围守卫） | 部分 | **否** | 否 |
| UAF 写检出 | 否（需影子内存） | 否 | **否** | 否 |
| head→next 完整性 | N/A | N/A | **需 H2/H6** | 需 H2/H6 |

**结论（`[实证]`）**：L2 池化对 class 4 **零覆盖**。崩溃 class 的可见性**唯一**依赖 R-02 §7 的 H2（`0x7CFD52` 前校验 `head->next` 不在毒族）+ H6（周期扫 head 数组）。

### 4.3 可选修复：L2 扩桶覆盖 class 4（`[推演]`）

```cpp
// SizeToPoolIdx 追加：
if (sz >= 57 && sz <= 72) return 8;   // class-4 bucket
// FixedPool s_pools[9];  elemSize=72;  8B header + 0xDEADBEEF poison
```

- 收益：class 4 立即获得双释放检出 + 投毒 + 范围守卫。
- 风险：改变 class-4 对象生命周期（池块不还给 SBH），与崩溃现场时序不同 → **必须 A/B**，且 `EnableMemoryPool` 仍为启动期锁定。
- **替代**：不动 L2，仅装 H2/H6（零行为扰动，只观测）。

---

## [5] 「写已释放块」站点与可落地防护（`[实证]`+`[推演]`）

### 5.1 首要 free 点：`BasePlanningCellContainer::AddCapacity 0x510860`

```
0x51086E  mov ebx,[esi+8]        ; Capacity
0x510871  add ebx,ebp            ; + increment
0x510873  lea eax,[ebx*8]        ; new_bytes = cap'*8
0x51087B  call 0x7C8E17          ; _new
0x510897..0x5108B6  按 8B 元素拷贝旧→新
0x5108B8  mov eax,[esi]          ; old Items
0x5108BB  call 0x7C8B3D          ; _delete(old)  ← class-4 buffer 释放
0x5108C8  mov [esi],edi          ; Items = new
0x5108CA  mov [esi+8],eax        ; Capacity = cap'
0x5108CD  mov [esi+0x10],0       ; 计数/标志清零
```

**条件**：`Capacity ∈ {8,9}` 时 buffer = 64/72B = **class 4**；`delete` 后旧 `Items` 起点即 free 节点 `next`（user+0）。
**UAF 形态**：任意仍持有旧 `BasePlanningCell*`/`WaypointClass*`（元素 8B，`Coords` 在 +0）的代码再写 `Position`/`Coords`，即把业务 int16 对写进 freelist `next`。

**同族站点**：
| VA | 类型 | free 旧 buffer | 备注 |
|---|---|---|---|
| `0x510860` | `BasePlanningCellContainer::AddCapacity` | `0x5108BB` | 元素 8B，cap 8/9 → class 4 |
| `0x7D0FA5`→`0x7D0FB6` | realloc 的 `alloc-copy-free` | realloc 内 `_delete` | 扩容失败/搬家时 |
| R-05 表 `0x5021A7` 等 7 处 | `WaypointPathClass` ctor | 向量 Clear/析构 | cap 步进 +10 |

### 5.2 写侧候选（偏移 0 int16 写，继承 R-05）

| 写 VA | 指令 | 形态 | 判定 |
|---|---|---|---|
| `0x552335` / `0x55C643` | `mov word [ebx], 0xFFFF` | CellStruct.X=-1 | **主候选**（与 `FE00FFFF` 低半一致） |
| `0x69E4A0` | `mov word [esi], 0xFFFF` | 链表节点 offset0 | 次 |
| `0x56CAF4` | `mov word [ecx], 0xFFFF` | 待定 | 次 |
| `0x7BD01F` 族（6 处） | `mov word [reg], 0xFFFF` | 像素/掩码 | 弱 |
| RGB565 打包 53 处 `shl r,11` | 后续 `mov [esi],eax` 等 | 双像素写 | 次候选 W2 |

### 5.3 可落地防护（按 ROI）

| 层 | 手段 | 落点 | 覆盖 |
|---|---|---|---|
| **A1** | **H2 毒族门禁** | `0x7CFD52` 前：`head->next` ∈ {`0xFE00FFFF`,`0xFFFF0000`,毒族} → dump+断 | 直接命中本次崩溃形态 |
| **A2** | **H6 周期毒扫** | 每 K 次 alloc 扫 32×64 head 的 `next/prev` | 存量污染 |
| **A3** | **H1 入链校验** | `0x7CFD4C` 前：node 在 region 内、16B 对齐、size 匹配 class | 元数据完整性 |
| **B** | L2 扩桶 idx8（57..72B） | `SizeToPoolIdx` + `s_pools[8]` | class-4 双释放+投毒（需 A/B） |
| **C** | 写点补丁 | `AddCapacity` free 后将旧指针槽清零；或 `Coords` 写前校验存活 | 根治 W1 |
| **D** | 存档/MP | **无需**（无堆地址进档） | — |

---

## [6] 存档 / MP：堆地址是否进档（对照 T7 OLE）（`[实证]`）

### 6.1 结构性结论（继承 T7）

| 问题 | 等级 | 结论 | 证据 |
|---|---|---|---|
| `.SAV` 容器 | `[实证]` | OLE2/CFB，签名 `D0 CF 11 E0 A1 B1 1A E1`；`CONTENTS` 流 + 15 元数据流 | 4 个真机档全命中 |
| 对象寻址 | `[实证]` | `OleSaveToStream/OleLoadFromStream`（IAT `0x7E15F4/0x7E15F8`），**CLSID**，非 swizzle 表 | `savegame_block_manifest.md` §2.5 |
| 裸堆指针落盘 | `[实证]` | **无**。`Save_Core` 的 43 处 imm 全是 `.bss` 子系统 this（`0x8A38E0/0x87F7E8/0xA83E30…`），经 `mov edx,imm` 传参，**不写入流** | `save_mp_heapaddr_check.txt` §B |
| 帧 CRC 输入 | `[实证]` | 量化坐标 + RNG（`0x64DAB0`），非指针 | `net_sync_checksum.md` §1 |
| `FillEvent_Waypoints 0x4C6780` | `[实证]` | 落 `CellStruct` 坐标 + `[0xA8ED84]` frame 计数；`ret 0x18` 栈参无指针 | 同上 §C |
| 指针哈希进逻辑 | `[实证]` | **禁令**（M-5 / `crt_pool_landing.md` L166） | 红线 |

### 6.2 真机档字节普查（本轮新做）

| 档 | OLE | img-ptr-like dwords | heap-ptr-like dwords | 判定 |
|---|---|---|---|---|
| `ALL01UMD.sav` | ✓ | 7614 | 63118 | **假阳性为主**：OLE 目录项、坐标、CRC、字符串 UTF-16 |
| `ECH01.sav` | ✓ | 5857 | 41363 | 同上 |
| `SOV01T.sav` | ✓ | 4921 | 46087 | 同上 |
| `SOV01UMD.sav` | ✓ | 7610 | 65653 | 同上 |

> **[实证] 样本核对**：`img-ptr-like` 首样本 `0x6f0052/0x74006f/0x450020` 是 ASCII/UTF-16 文本片段（"oR"/"to"/" E"），**不是**指针；`heap-ptr-like` 首样本 `0x51490020/0x4f3c9670` 是 OLE 扇区/流数据。真正 `0x00400000–0x007FFFFF` 的**可执行映像函数指针**在 OLE 流内仅以 CLSID 形式存在（`IPersistStream`），不以裸 VA 落盘。
>
> **收敛建议**：若需硬证，对 `CONTENTS` 流做「按 35 块模板切片 + 已知字段类型标注」的白名单普查（本轮受静态所限，标记为 `[推演]` 收尾项）。

---

## [7] 残差总表（收口后）

| ID | 项 | 状态 | 说明 |
|---|---|---|---|
| U1 | class 4 对象类型 | ✅ 静态闭环 | 49 alloc 点 + vtable 映射 |
| U2 | UAF 写者路径 | 🟡 部分 | free 点=`0x510860` 族；写点=`0x552335` 等；需 runtime 锁定 |
| U3 | LFH 相关性 | 🔴 开 | 需 A/B |
| U4 | realloc/copy | ✅ 静态闭环 | `0x7CFFC8`/`0x7D0A20` 语义定谳 |
| U5 | page-group head 清空 | ✅ 静态闭环 | recommit 自愈；无残毒面 |
| U6 | 毒值业务字面 | 🟡 部分 | CellStruct 主假设维持 |
| U7 | L2×SBH 覆盖 | ✅ 闭环 | class 4 不在 L2；H2/H6 必装 |
| U8 | 写已释放站点 | 🟡 部分 | `0x510860`+`0x552335` 族；防护 A1–C 已给 |
| U9 | 存档/MP 堆地址 | ✅ 闭环 | 无裸堆指针进档/进 CRC/进事件 |

---

## [8] 证据锚点

| 证据 | 路径 |
|---|---|
| U4/U5 反汇编 | `out/re_work/re_sprint/R_sbh_uaf/u4_u5_residual_disasm.txt` |
| U5 head 清空证明 | `out/re_work/re_sprint/R_sbh_uaf/u5_head_clear_proof.txt` |
| 写已释放站点扫描 | `out/re_work/re_sprint/R_sbh_uaf/waf_sites_scan.txt` |
| 向量 UAF 形态 | `out/re_work/re_sprint/R_sbh_uaf/wpt_vector_uaf_shape.txt` |
| CRT L2×SBH 交叉 | `out/re_work/re_sprint/R_sbh_uaf/crt_l2_sbh_crossmap.txt` |
| 存档/MP 普查 | `out/re_work/re_sprint/R_sbh_uaf/save_mp_heapaddr_check.txt` |
| 可复算脚本 | `scan_u4_u5_residual.py` / `scan_u5_head_clear.py` / `scan_waf_sites.py` / `scan_wpt_vector_uaf.py` / `scan_crt_l2_cross.py` / `scan_save_mp_heapaddr.py` |
| claims | `out/re_work/re_sprint/R_sbh_uaf/claims.txt` |
| 上游 R-02 / R-05 | `docs/re/sbh_freelist_deep_dive.md` / `docs/re/sbh_uaf_writer_deep_dive.md` |
| 二进制 | `ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` |

**一句话**：R-02 六项残差已静态收口 U1/U4/U5，U2/U6 收敛到 `AddCapacity 0x510860` free 点 + `CellStruct` 写者族；CRT L2 池化对崩溃 class 4 **零覆盖**，H2/H6 钩子是唯一可见性手段；存档/MP **无堆地址进档**（OLE/CLSID），无需为 UAF 做序列化防护。
