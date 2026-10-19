# R-02 专章：西木内嵌 MSVC 6.0 SBH（Small Block Heap）深度取证

> [META]
> 任务=R-02 / SBH freelist 深潜 · 执行=R 轨逆向取证代理 · 日期=2026-09-30
> 目标二进制：`ra2youli/gamemd.exe`（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x00400000`）
> 写作用域：本文件 + `out/re_work/re_sprint/sbh/**`；二进制只读，未打补丁
> 上游定谳：`docs/re/except_zc11_forensics.md`（崩溃点 `0x007CFC9F`，毒值 `EDX=FE00FFFF`）
> 参考：`docs/re/crt_memory_pool_deep_dive.md`（只读共享）
> 证据分级：`[实证]` 字节+反汇编可复算 · `[推演]` 由代码逻辑推断 · `[待实测]` 需运行时

---

## [0] 结论速览（≤12 行）

1. **[实证]** SBH 全部机制在原版 `.text` `0x007CF77F`–`0x007CFFC7` 一带，与 CRT 入口 `0x007C8E17/0x007C8B3D/0x007C93E8/0x007C946E` 成链。
2. **[实证]** size-class 公式 `block=(req+0x17)&~0xF`，`class=(block>>4)-1`，**64 类**（`0..0x3F`），双 dword 位图按 **bit=31-class**（MSB=class0）分高低半（`0..0x1F` / `0x20..0x3F`）。
3. **[实证]** Region 描述符步长 `0x14`，字段：`+0` 类位图 lo、`+4` 类位图 hi、`+8` 未提交 page-group 位图、`+0xC` 1MB base、`+0x10` heap_info 指针。
4. **[实证]** 每 Region = `VirtualAlloc(0x100000)`，切 32 个 32KB page-group（`offset>>0xF`）；heap_info = `HeapAlloc(0x41C4)`。
5. **[实证]** free 节点布局确认：`[node]=size(bit0=INUSE)`、`[node+4]=next`、`[node+8]=prev`，尾部 `+size-4` 存 size 副本；用户指针 = `node+4`。
6. **[实证]** 崩溃时 **`EDI=4`** → 被读毒的是 **class 4**（80B 块 / req 57..72）的 freelist，**不是** 在途 `push 0x98` 的 class 9。
7. **[实证]** 毒值落在 **heap_info 的 freelist-head 数组内部**（`EAX=heap_info=0x1498EC08`，group=7，`head->next @ 0x1498FB8C`），属**分配器元数据**而非用户块体。
8. **[实证]** `FE00FFFF` 作为 imm32 在 gamemd.exe / ra2render.dll 映像内 **0 次命中** → 非分配器投毒、非代码立即数。
9. **[推演] 主候选**：UAF 把业务数据写进 free 节点的 `next`（+4），unlink 时被提升为 `head->next` → 下次分配同 class 读毒崩溃。
10. **[推演]** `FE00FFFF` 位拆 = 两个 int16 LE `(0xFFFF,0xFE00)=(-1,-512)`，或两枚 RGB565 像素（白/纯红）；栈内 `FFFF0000` 同族。
11. **[推演] 已反证**：未初始化槽位（`MEM_COMMIT` 清零 + 建堆自链）；纯 double-free（只会自环，不产生 `FE00FFFF`）。
12. **[待实测]** class 4（57..72B）在 U0200 负载下对应的具体对象类型，需 live dump / harness 确认。

---

## [1] `__sbh_alloc_block` 逐指令语义

入口 `0x007CFB13`（fileoff `0x3CFB13`）。完整反汇编：`out/re_work/re_sprint/sbh/recompute_disasm.txt`。

### 1.1 参数与 size-class 计算（`0x7CFB13`–`0x7CFB62`）

| 地址 | 指令 | 语义 |
|---|---|---|
| `0x7CFB13` | `push ebp; mov ebp,esp; sub esp,0x14` | 标准序 |
| `0x7CFB19` | `mov eax,[0xB78B94]` | `eax = region_count` |
| `0x7CFB1E` | `mov edx,[0xB78B98]` | `edx = region_array_alloc` |
| `0x7CFB26` | `lea eax,[eax+eax*4]; lea edi,[edx+eax*4]` | `edi = base + count*0x14` = **数组末尾** |
| `0x7CFB2D` | `mov eax,[ebp+8]` | `eax = req` |
| `0x7CFB33` | `lea ecx,[eax+0x17]; and ecx,0xFFFFFFF0` | **`block=(req+0x17)&~0xF`** |
| `0x7CFB39` | `mov [ebp-0x10],ecx` | 保存 block |
| `0x7CFB3C` | `sar ecx,4; dec ecx` | **`class=(block>>4)-1`** |
| `0x7CFB40` | `cmp ecx,0x20; jge` | class≥32 → 高半位图 |
| `0x7CFB45` | `or esi,-1; shr esi,cl` | `esi = 0xFFFFFFFF >> class` = 低半掩码（bits `0..31-class`，对应 class `class..31`） |
| `0x7CFB53` | `add ecx,-0x20; or eax,-1; xor esi,esi; shr eax,cl` | 高半：`[ebp-8]=掩码`，`esi=0`（低半无兴趣） |

> [实证] 公式与掩码构形与 MSVC 6.0 `sbh.c` 同源：+0x17 实为 `(req+8) 上对齐到 16`（4B 头 + 最小 freelist 12B → 最小块 16B）。

### 1.2 Region 扫描（`0x7CFB63`–`0x7CFBDF`）

两轮线性扫，步长 `0x14`：

1. **`0x7CFB63`–`0x7CFB8A`**：从 `[0xB78B8C]`（cur region）起，对每个 region 读 `bitmap_lo&mask`、`bitmap_hi&mask`，或非 0 → 命中（该 region 有 ≥class 的空闲块）。
2. **`0x7CFB8F`–`0x7CFBAD`**：从 region 数组头再扫一轮（覆盖 cur 之前的部分）。
3. **`0x7CFBAF`–`0x7CFBDD`**：仍无 → 找 `region+8 != 0`（还有未提交 page-group）的 region；再无 → `call 0x7CFE1C` 申请新 region。
4. `0x7CFBED`：`call 0x7CFECD` 提交新 page-group；`0x7CFBF4` 检查 `[heap_info] != -1`。

### 1.3 取块 / 分裂 / 摘链（`0x7CFC08`–`0x7CFDC7`）— **崩溃就在这段**

| 地址 | 指令 | 语义 |
|---|---|---|
| `0x7CFC08` | `mov [0xB78B8C],ebx` | 更新 cur region |
| `0x7CFC0E` | `mov eax,[ebx+0x10]` | `eax = heap_info` |
| `0x7CFC11` | `mov edx,[eax]` | `edx = last_group`（`-1` 表示无） |
| `0x7CFC1B` | `mov ecx,[eax+edx*4+0xC4]; mov edi,[eax+edx*4+0x44]` | 该 group 的 hi/lo 位图 |
| `0x7CFC2F` | …`lea ecx,[eax+0x44]` | 从 group 0 起线性找第一个命中的 group |
| `0x7CFC6A` | `imul ecx,0x204` | group 步长 `0x204` |
| `0x7CFC70` | `lea ecx,[ecx+eax+0x144]` | **`freelist_base = heap_info + group*0x204 + 0x144`** |
| `0x7CFC7A`–`0x7CFC96` | 位扫描 `shl ecx,1 / jl` | 从 bit31 往下找 → `EDI` = **class** |
| `0x7CFC98` | `mov ecx,[ebp-0xC]` | `ecx = freelist_base` |
| **`0x7CFC9B`** | **`mov edx,[ecx+edi*8+4]`** | **`edx = head[class]->next`（free 节点指针）** |
| **`0x7CFC9F`** | **`mov ecx,[edx]`** | **读节点 size —— 毒值 `FE00FFFF` 解引用，AV 崩溃** |
| `0x7CFCA1` | `sub ecx,[ebp-0x10]` | `remainder = node_size - block` |
| `0x7CFCA9` | `sar esi,4; dec esi; cmp esi,0x3F; jle / push 0x3F` | remainder class，**上限 0x3F** |
| `0x7CFCB5` | `cmp esi,edi; je 0x7CFDCA` | remainder class == 取出 class → 不分裂，整块给出 |
| `0x7CFCBD` | `mov ecx,[edx+4]; cmp ecx,[edx+8]` | **双向链完整性**：`next==prev` → 该 class 仅此一块 |
| `0x7CFCC5` | `cmp edi,0x20; jge` | 摘链时按低/高位图清 bit |
| `0x7CFD26` | `mov ecx,[edx+8]; mov edi,[edx+4]; mov [ecx+4],edi` | **`prev->next = next`** |
| `0x7CFD33` | `mov ecx,[edx+4]; mov edi,[edx+8]; mov [ecx+8],edi` | **`next->prev = prev`** |
| `0x7CFD42`–`0x7CFD58` | remainder 重新入链 | `node->next=head->next; node->prev=&head; head->next=node; next->prev=node` |
| `0x7CFDC7`–`0x7CFDE3` | 写 size/尾 size | `[block]=size`、`[block+size-4]=size`；分配块写 `size\|1` |
| `0x7CFE14` | `lea eax,[edx+4]` | **返回用户指针 = block+4** |

> [实证] `head` 为 8 字节步长的哨兵：`head+4=next`、`head+8=prev`（`head+8` 与下一 class 槽 `+0` 重叠，`+0` 不用）。空表时 `head->next==head`。

---

## [2] size-class 分桶表（字节级）

### 2.1 公式与生成代码锚点

```
block = (req + 0x17) & ~0xF          ; 0x7CFB33  8D 48 17 / 83 E1 F0
class = (block >> 4) - 1             ; 0x7CFB3C  C1 F9 04 / 49
class ∈ [0, 0x3F]                    ; 0x7CFB40  83 F9 20 / 0x7CFDAD  83 FE 3F
bit  = 31 - class  (MSB-first)       ; insert 0x7CFD7B  BB 00 00 00 80 / D3 EF
low  = class 0..0x1F  → *_bm_lo
high = class 0x20..0x3F → *_bm_hi (bit = class-0x20)
```

### 2.2 全 64 类（落盘 `sizeclass_table.csv`，此处摘要 + 关键点）

| class | block | user=block-4 | req 范围 | 备注 |
|---:|---:|---:|---:|---|
| 0 | 16 | 12 | 0..8 | 最小块；freelist 需 12B |
| 1 | 32 | 28 | 9..24 | |
| 2 | 48 | 44 | 25..40 | |
| 3 | 64 | 60 | 41..56 | |
| **4** | **80** | **76** | **57..72** | **[实证] 崩溃被读毒的 class** |
| 9 | 160 | 156 | 137..152 | 在途 `push 0x98` 对应 class |
| 19 | 320 | 316 | 297..312 | ParticleClass 0x138 |
| 22 | 368 | 364 | 345..360 | BulletClass 0x160 |
| 28 | 464 | 460 | 441..456 | AnimClass 0x1C8 |
| 31 | 512 | 508 | 489..504 | 低半最后一档 |
| 32 | 528 | 524 | 505..520 | 高半第一档 |
| **63** | **1024** | **1020** | **1001..1016** | 上限=threshold `0x3F8` |

> [实证] 游戏对象落点：Particle→19、Bullet→22、Anim→28；崩溃毒 class 4 **不在**这三类 → UAF 写入者更可能是小结构（节点/短向量/小名表），而非 Anim/Bullet/Particle 本体。

### 2.3 阈值与旁路

- `__sbh_threshold` = `0x3F8` @ `0x0087C584`（fileoff `0x47C584`，字节 `F8 03 00 00`）`[实证]`
- `heap_alloc 0x7C9473`：`req > threshold` → `(req+0xF)&~0xF` → `HeapAlloc(hHeap)`（`hHeap=[0xB78B9C]`）`[实证]`
- SBH 失败（返回 NULL）也会掉到 Win32 兜底（`0x7C9497`）`[实证]`
- 运行时可调：`0x7CF768` `__sbh_set_threshold`（上限校验 `0x3F8`）`[实证]`

---

## [3] Region 描述符与 heap_info 布局

### 3.1 全局状态

| 地址 | 含义 | 初始化锚点 |
|---|---|---|
| `0xB78B84` | region 数组容量（init `0x10`=16） | `0x7CF7B1` `C7 05 ... 10 00 00 00` |
| `0xB78B88` | 最近一次提交的 group 下标 | free 尾 `0x7CFE00` 比较 |
| `0xB78B8C` | region 数组基址（cur） | `0x7CF7AC` |
| `0xB78B90` | cur region 下标缓存 | `0x7CF79C` 清零 |
| `0xB78B94` | region 计数 | `0x7CF7A3` / `0x7CFEBC` `inc` |
| `0xB78B98` | region 数组 HeapAlloc 指针 | `0x7CF794`；扩容 `0x7CFE55` |
| `0xB78B9C` | `_crtheap` 句柄 | `0x7CF6CA` |

> [实证] 扩容：`0x7CFE2F` `lea eax,[ecx+ecx*4+0x50]; shl eax,2` = `(cap+0x10)*0x14` 后 `HeapReAlloc`（IAT `0x7E12A4`），容量 `+= 0x10`。

### 3.2 Region 描述符（步长 `0x14`，`[实证]`）

| 偏移 | 类型 | 语义 | 锚点 |
|---|---|---|---|
| `+0x00` | DWORD | **类空闲位图 lo**：bit(31-class)=class 0..31 有空闲 | `0x7CFB74` `mov edi,[ebx]`；`0x7CFD84` `or [ebx],edi` |
| `+0x04` | DWORD | **类空闲位图 hi**：class 32..63 | `0x7CFB71` `mov ecx,[ebx+4]`；`0x7CFDAE` |
| `+0x08` | DWORD | **未提交 page-group 位图**（bit=group，1=可提交；init `-1`） | `0x7CFEBC` `or [esi+8],-1`；`0x7CFFBE` `and [eax+8],~(1<<g)` |
| `+0x0C` | PVOID | **1MB base**（`VirtualAlloc`） | `0x7CFE9A` `mov [esi+0xC],eax`；`__sbh_find_block` `sub edx,[eax+0xC]` |
| `+0x10` | PVOID | **heap_info**（`HeapAlloc(0x41C4)`） | `0x7CFE80` `mov [esi+0x10],eax` |

### 3.3 heap_info（`0x41C4` 字节，`[实证]`）

| 偏移 | 尺寸 | 语义 |
|---|---|---|
| `+0x000` | DWORD | last_group（init `-1`；`0x7CFEC5` `or [eax],-1`） |
| `+0x004` | BYTE×64 | `cls_grp_cnt[class]`：有多少 group 有该 class 空闲（0→1 时置 region 位图） |
| `+0x044` | DWORD×32 | `grp_bm_lo[group]`：该 group 内 class 0..31 空闲位图 |
| `+0x0C4` | DWORD×32 | `grp_bm_hi[group]`：class 32..63 |
| `+0x144` | 32×64×8 | **freelist head**：`head(g,c) = +0x144 + g*0x204 + c*8`；`head+4=next`、`head+8=prev` |
| `+0x4144` | 0x80 | 尾部填充（对齐/预留） |

> [实证] `0x204 = 64*8 + 4`：每 group 的 head 区 512B + 4B 尾。

### 3.4 1MB Region → page-group → page

```
region base ──┬── group 0  (base+0x00000)   32KB = 8 page
              ├── group 1  (base+0x08000)
              ├── ...
              └── group 31 (base+0xF8000)
                    └── page i (4KB): [page+8]=-1 哨兵, [page+0xC]=0xFF0 size,
                        [page+0x10]=next, [page+0x14]=prev, [page+0xFF8]=0xFF0 尾 size
```

- group 下标 = `(ptr - base) >> 0xF`（`0x7CF805`）`[实证]`
- 提交：`VirtualAlloc(base + g*0x8000, 0x8000, MEM_COMMIT, PAGE_READWRITE)`（`0x7CFF0B`）`[实证]`
- 每页车出一块 `0xFF0` 空闲块，**直接挂 class 63**（`0x7CFF98` `mov [esi+ebx*4+0xC4],1`）`[实证]`

---

## [4] `__sbh_find_block` 检索逻辑（堆完整性校验用）

入口 `0x007CF7BD`（**无栈帧序言**，叶子函数；fileoff `0x3CF7BD`）`[实证]`

```asm
007CF7BD: A1 94 8B B7 00        mov  eax, [0xB78B94]      ; count
007CF7C2: 8D 0C 80              lea  ecx, [eax+eax*4]
007CF7C5: A1 98 8B B7 00        mov  eax, [0xB78B98]      ; base
007CF7CA: 8D 0C 88              lea  ecx, [eax+ecx*4]     ; end = base+count*0x14
007CF7CD: 3B C1                 cmp  eax, ecx
007CF7CF: 73 14                 jae  not_found             ; 空数组
007CF7D1: 8B 54 24 04           mov  edx, [esp+4]          ; ptr
007CF7D5: 2B 50 0C              sub  edx, [eax+0xC]        ; ptr - region.base
007CF7D8: 81 FA 00 00 10 00     cmp  edx, 0x100000         ; < 1MB ?
007CF7DE: 72 07                 jb   found
007CF7E0: 83 C0 14              add  eax, 0x14             ; 下一 region
007CF7E3: EB E8                 jmp  loop
007CF7E5: 33 C0                 xor  eax, eax              ; NULL = 非 SBH 块
007CF7E7: C3                    ret
```

**语义**：对 region 数组线性遍历，`ptr ∈ [base, base+0x100000)` 即命中，返回 **region 描述符指针**；否则 NULL（调用方转 `HeapFree`）。

> [实证] 这是**唯一**的归属判定：无魔数、无 tag、无边界交叉校验。因此 **UAF 后地址被复用为其它 class 块时，`find_block` 仍会成功返回同一 region** —— 校验钩子必须在此之上补强。

---

## [5] `__sbh_free_block` 语义（摘要）

入口 `0x007CF7E8`，`free_block(region, user_ptr)` `[实证]`

1. `node = user_ptr-4`；`size = [node]`；`[node]` bit0=INUSE。
2. **前向合并**：`next_size = [node + (size&~1)]`，bit0=0 表示下一块空闲 → 摘除下一块并 `size += next_size`（`0x7CF824`–`0x7CF8AB`）。
3. **后向合并**：`prev_size = [node-4]`（前块尾副本），bit0=0 表示前块空闲 → 回退指针合并（`0x7CF8BC`–`0x7CF968`）。
4. **入链**：按合并后 size 算 class（上限 `0x3F`），`node->next=head->next; node->prev=&head; head->next=node; next->prev=node`；更新 `cls_grp_cnt` / 两级位图（`0x7CF97A`–`0x7CFA08`）。
5. **写尾**：`[node]=size`、`[node+size-4]=size`（`0x7CFA06`）。
6. **page-group 回收**（`0x7CFA0C`–`0x7CFB0E`）：`dec [group_count]`；归零且非 cur group 时 `VirtualFree(base+g*0x8000, 0x8000, MEM_DECOMMIT)`，并置回 `region+8` 位图。

> [实证] 双向链摘链只写两对指针，**不做地址合法性校验**；`next/prev` 一旦被 UAF 污染，unlink 即把毒值提升到 `head->next`。

---

## [6] 毒值 `FE00FFFF` 来源分析

### 6.1 现场约束（`[实证]`）

| 约束 | 值 | 含义 |
|---|---|---|
| 崩溃指令 | `mov ecx,[edx]` @ `0x7CFC9F` | 读 **free 节点 size 字段** |
| `EDX` | `FE00FFFF` | 是 **指针值**（head->next），不是 size |
| `EDI` | `4` | 毒 class = **4**（80B / req 57..72） |
| `EAX` | `0x1498EC08` | heap_info |
| `ECX` | `0x1498FB68` | freelist_base = `heap_info+7*0x204+0x144` |
| 毒址 | `0x1498FB8C` = head(7,4)+4 | **heap_info 内部**（`HeapAlloc(0x41C4)` 块内） |
| 映像立即数 | `FE00FFFF` = **0 次** | 非代码常量、非分配器投毒 |

### 6.2 候选排序

| 序 | 候选 | 等级 | 支持证据 | 反证 / 缺口 |
|---|---|---|---|---|
| **1** | **UAF 业务数据写进 free 节点 `next`（+4），unlink 提升为 `head->next`** | `[推演]·主` | ①毒在 head 而非节点体，只能由 unlink 的 `head->next=node->next` 传播（`0x7CFD4C`）；②`FE00FFFF` 非分配器 fill（MSVC debug 用 `CD/DD/FD`，retail SBH 无 fill）；③U0200 713 单位高 churn；④栈内 `FFFF0000` 同族业务残值 | 未指认具体对象类型；class 4（57..72B）不是 Anim/Bullet/Particle 尺寸 |
| **2** | **double-free + 后续业务写** | `[推演]` | 威胁二同构（`crt_pool_risk_review.md`）；粒子/动画提前结束又析构 | 纯 double-free 只产生自环指针，**不产生 `FE00FFFF`**；必须叠加业务写 |
| **3** | **邻块越界写穿 heap_info** | `[推演]·弱` | heap_info 是 `HeapAlloc(0x41C4)`，与业务块同在进程堆；LFH 改变布局 | heap_info 在 CRT 堆，SBH 用户块在 VirtualAlloc 区，**不相邻**；越界需打到 CRT 堆邻块 |
| **4** | 未初始化槽位 | `[推演]·已反证` | — | `VirtualAlloc(MEM_COMMIT)` **清零页**；`0x7CFECD` 建堆自链 head；init 写 `-1` 哨兵。不会留下 `FE00FFFF` |
| **5** | 分配器自身写坏（size 计算/分裂错位） | `[推演]·弱` | — | 分裂写的是 `[block]`/`[block+size-4]`，不经 head->next；且 imm 扫描无毒值 |
| **6** | ra2render / LFH 环境间接 | `[待实测]·弱` | `HeapSetInformation(LFH)`×7/8 改变 CRT 堆布局 | SBH 自管 freelist，与进程 LFH 不共享链表；需 A/B |

### 6.3 毒值位拆（`[推演]`）

| 视图 | 解读 | 业务贴近度 |
|---|---|---|
| int16 ×2 LE | `(0xFFFF, 0xFE00)` = `(-1, -512)` | 坐标/光照/高度常用 `-1` 哨兵；`-512` 像高度或光强偏移 |
| RGB565 ×2 | `(0xFFFF, 0xFE00)` = 白 / 纯红 `(31,0,0)` | 精灵/调色板像素对；战场残影 |
| uint32 | `0xFE00FFFF` | 无已知枚举/魔数 |
| float bit | 指数 `0xFC` 极小负数 | 业务上不像有意浮点 |

> [实证] `.data` 中 `FE00` 作为 LE 16 位出现 100 次：指针表低位、`0xFFFFFFFE` 哨兵、光强阶梯（`0xFC/0xFD/0xFE/0xFF`）三类。`0000FEFF` 全映像仅 1 处（`0x60A898`，实为 `cmp edi,0xFE` 指令尾，**非数据**）。

### 6.4 传播路径重建（`[推演]`）

```
T0  free(N)  →  head->next = N ; N->next = head ; N->prev = head
T1  UAF 写 N+4 = FE00FFFF      （业务把 free 块当对象用）
T2  alloc(class4) 摘 N：
        head->next = N->next = FE00FFFF    ← 毒值进入 heap_info
T3  alloc(class4) 再取：
        edx = head->next = FE00FFFF
        mov ecx,[edx]  →  AV   ← 与崩溃现场完全同构
```

> [实证] T2 的写操作字节级对应 `0x7CFD4C` `mov [edx+4],edi`（入链时写 node->next）与 `0x7CFD52` `mov [ecx+4],edx`（`head->next=node`）；摘链 `0x7CFD26`–`0x7CFD39` 同样会传播。

---

## [7] 堆完整性校验钩子规格草案（供 M 轨 harness 门禁）

> [推演] 规格草案；落地与 A/B 由 M 轨执行。R 不改 `tools/bench_*.py`。

### 7.1 钩子点（按 ROI 排序）

| ID | 钩子位置 | 触发 | 检查项 | 失败动作 |
|---|---|---|---|---|
| H1 | `__sbh_alloc_block` `0x7CFD4C` 前 | 每次入链 | `node` 落在 `region.base .. +0x100000` 且 16B 对齐；`node->size` 与 class 匹配 | 记录 node/class/size，**不中断**（收集） |
| H2 | `__sbh_alloc_block` `0x7CFD52` 前 | 每次 `head->next=node` | `node` 或 `head` 合法；`node != FE00FFFF` 族 | 若为毒族 → 立即 dump + 断 |
| H3 | `__sbh_free_block` `0x7CF8A8` 后 | 合并完、入链前 | `size` 16B 倍数、`≤0x400`；尾副本 `== size` | 记录 |
| H4 | `__sbh_find_block` 命中后 | 每次 free/realloc 归属 | `ptr` 16B 对齐；`ptr-4` 的 size 在合法 class | 记录 |
| H5 | 周期（每 N 帧 / 每 K 次 alloc） | 全 region | 遍历 64 class：`head->next->prev==head`、`head->prev->next==head`、长度≤上限；位图 popcount 与 `cls_grp_cnt` 一致 | 计数超阈 → dump |
| H6 | 毒族哨兵 | 全程 | 扫描 heap_info head 数组与所有 free 节点 `next/prev` 是否命中毒族白名单 | 命中即 FAIL 门禁 |

### 7.2 毒族签名（harness `except_watch` 判据细化）

| 族名 | 模式 | 优先级 |
|---|---|---|
| `POIS_FE00FFFF` | `0xFE00FFFF` | P0（本次） |
| `POIS_FFFF0000` | `0xFFFF0000` | P1（栈内同族） |
| `POIS_XYFFFFxx` | 高 16 位 ∈ `{0xFE00,0xFF00,0xFFFF}` 且低 16 位 ∈ `{0x0000,0xFFFF,0xFE00}` | P1 |
| `POIS_SMALLINT` | `0x00000001..0x000000FF` 且非 16B 对齐指针形态 | P2 |
| `POIS_SELFFREE` | `next==self` 且非 head | P2（double-free） |

### 7.3 size-class 签名（判别被毒槽位类型）

| 观察 | 含义 |
|---|---|
| 毒 class ∈ {19,22,28} | Particle / Bullet / Anim 邻块或自身 |
| 毒 class ∈ {0..8} | 小结构 / 短向量 / 名表节点 |
| 毒 class ∈ {63} | page 顶 `0xFF0` 大块（合并异常） |
| 毒 class 与在途 req class 不同 | 污染是**存量 freelist**，非本次分配写坏 |

---

## [8] 未闭环项与下一步

| # | 项 | 等级 | 建议动作 |
|---|---|---|---|
| U1 | class 4（req 57..72B）在 U0200 下对应哪类对象 | `[待实测]` | live dump：在 `free_block` 处记录 (class, ret_addr) 直方图 |
| U2 | UAF 写者是哪条路径 | `[待实测]` | 在 `free_block` 后对该 node 布写监视（硬件断点/harness 影子内存） |
| U3 | LFH 弱相关（A11）能否排除 | `[待实测]` | A/B 三组：仅原版 / 注入 / 注入+EnableLFH=0，各 ≥8 局 |
| U4 | `0x7CFFC8`（realloc 形态函数）与 `0x7D0A20` 拷贝语义 | `[推演]` | 补一轮反汇编（本次未逐指令展开） |
| U5 | page-group 回收（`VirtualFree` DECOMMIT）后 head 是否清空 | `[推演]` | 对照 `0x7CFA0C`–`0x7CFB0E` 做一轮校验钩子试装 |
| U6 | 毒值业务字面（-1/-512 或 RGB565）归因 | `[待实测]` | 需要崩溃前后 heap dump 对比 |

**收敛建议**：M 轨按 §7 装 H2+H6（毒族门禁）即可把「注入态才复现」收敛为可观测事件；R 轨待 U1/U2 的 dump 回传后做对象归因。

---

## [9] 证据锚点

| 证据 | 路径 |
|---|---|
| 可复算脚本 | `out/re_work/re_sprint/sbh/recompute_sbh.py`（一键重放） |
| 全量反汇编 | `out/re_work/re_sprint/sbh/recompute_disasm.txt` |
| 分函数反汇编 | `out/re_work/re_sprint/sbh/disasm_sbh_core.txt`、`disasm_sbh_funcs.txt` |
| size-class 表 | `out/re_work/re_sprint/sbh/sizeclass_table.csv` |
| 布局推导 | `out/re_work/re_sprint/sbh/sizeclass_and_layout.txt` |
| 毒值取证 | `out/re_work/re_sprint/sbh/poison_forensics.txt`、`poison_counts.txt` |
| claims | `out/re_work/re_sprint/sbh/claims.txt` |
| 崩溃定谳（上游，只读） | `docs/re/except_zc11_forensics.md` |
| CRT 总览（只读） | `docs/re/crt_memory_pool_deep_dive.md` |
| 二进制 | `ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` |

**一句话**：SBH 是 64 类 × 双 dword 位图 × 32×32KB page-group 的经典 MSVC 小块堆；崩溃不在分配算术，而在 **class 4 freelist head→next 已是业务毒值 `FE00FFFF`**——最像 UAF 把业务双字写进 free 节点 `next` 后被 unlink 提升，下一步靠 harness 毒族门禁 + class 4 对象归因收口。
