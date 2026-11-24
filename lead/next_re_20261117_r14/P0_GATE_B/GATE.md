# P0-GATE-B · GATE.md — ②-b 拒绝闸静态定位

> 卡号 P0-GATE-B｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读；开工/收尾同值）｜ImageBase 0x400000
> 工具：Python 3.12.10 / capstone 5.0.7（`skipdata=True`）/ pefile 2024.8.26；脚本见 `work\`，原始输出见 `EVIDENCE\`。
> 分级仅 `[已证]` / `[静态推断]` / `[未证]`。证据路径相对本卡目录。

---

## 结论（一句话）

**拒绝闸找到了（结构 `[已证]`、在放置场景的可达性 `[静态推断]`）：它在 `0x47C620` 体内，是该函数对 `0x47C3D0`（`CellClass::FindTechnoNearestTo`）的两次「选择子=0」调用——`0x47C738` 与 `0x47C805`。判据是「head A（`[cell+0xE4]`）上只要有任一 `[obj+0x14]&1` 的对象即返回 al=0 拒绝」，**不按 WhatAmI 分类**，因此 WhatAmI=15(步兵)/1(单位) 从未被比较却被拒绝。卡面预设的「`0x47C3D0` 选择子=1 分支」在**放置路径上被证伪**（5 个 setg 站点全在运动函数）。**

---

## T2 · `0x47C3D0` 完整解剖（真入口 `0x47C3D0`，`ret 0xc` @ `0x47C4BC`，尾部 `0x47C4C8` 起 nop 填充）

完整不截断反汇编：`EVIDENCE\47c3d0_clean_full.txt`（88 行）与 `EVIDENCE\47c3d0_full_disasm.txt`。

### 签名（栈参取值集合与最大值，纪律 F）
- 调用约定：`this`=ecx（CellClass*），3 个栈参数（`ret 0xc` = 12 B）。
  - `[ebp+8]` = arg1 = `CellStruct*`（待查坐标；`mov edx,[ebp+8]` @0x47C3D9，`[edx]`/`[edx+4]` 取 X/Y）
  - `[ebp+0xc]` = arg2 = **选择子（byte）**（`mov al,[ebp+0xc]` @0x47C400）
  - `[ebp+0x10]` = arg3 = 排除对象指针（`cmp esi,[ebp+0x10]` @0x47C432）
- 栈参 `[esp+N]` 取值集合 = `{0x1c, 0x20, 0x24}`（相对进入时 esp，对应 arg1/arg2/arg3）；最大 `N=0x24`。函数内另用 `[esp+0x10/0x14/0x18/0x24/0x28/0x44]` 为局部变量，均在 0x34 帧内，非入参。
- `this` 来源（纪律 A，thiscall 回溯）：`0x47C736 mov ecx,edi`（edi = 外层 `0x47C620` 的 `this`，取自 GetCellAt 返回值 `mov ecx,eax` @0x47C2AC / 0x449480）⇒ **ecx = CellClass\***。`[已证]`

### 选择子语义（**关键**）`[已证]`
```
0047C400  mov   al, byte [ebp+0xc]     ; 选择子
0047C403  test  al, al
0047C405  je    0x47C40F
0047C407  mov   ecx, [ecx+0xE8]        ; 选择子!=0 → head B (AltObject/桥上链)
0047C40D  jmp   0x47C415
0047C40F  mov   ecx, [ecx+0xE4]        ; 选择子==0 → head A (FirstObject/地面链)
```
- **选择子=0 → 读 `[cell+0xE4]`（head A）；选择子=1（任意非零）→ 读 `[cell+0xE8]`（head B）。** 与 §978 / YRpp `CellClass` 两链语义一致。
- 这是 `0x47C3D0` 体内**唯一**一处选择子分支（1 个 `test al,al` + 2 个链头加载）。`[已证]`

### 函数语义：类型无关（**这是全卡最硬的一条**）`[已证]`
- 遍历选中链：`mov al,[esi+0x14]; and al,1; … je skip`（`0x47C427-0x47C430`）——唯一对象过滤器是 `[obj+0x14]&1`（在册/活动标志），**不是 WhatAmI**。
- `cmp esi,[ebp+0x10]` @0x47C432 排除 arg3 指定对象。
- `call [edx+0x48]` @0x47C440 取对象坐标 → fild/fmul/faddp → `call 0x4CAC40`(`sqrt`) → `call 0x7C5F00`(`_ftol`) ⇒ 按**到 arg1 坐标的距离**选最近者。
- **全函数 `call [reg+0x2C]`（WhatAmI 虚调用）计数 = 0**（脚本 `work\t_final_verify.py`，输出 `EVIDENCE\t_final_verify.txt`）。
- ⇒ **`0x47C3D0` 的「选择子=1 分支」不检查步兵占格，也不检查任何 WhatAmI**；它只是把 head B 上最近的对象按距离返回。`0x47C3D0` 自己读 `[cell+0xE8]`（`0x47C407`），这是 §972 所说的「被调函数确实读 +0xE8」。

### 返回值含义 `[已证]`
返回链上满足过滤、距 arg1 最近的对象指针（`mov eax,[esp+0x14]` @0x47C4B2）；空链/全被过滤 → 返回 0（`xor esi,esi` @0x47C3E1，`mov eax,esi` @0x47C4BF）。

### 5 个「setg 选择子=1」调用点（§978 提及）—— 均不在放置路径 `[已证]`
| 站点 | 选择子来源 | 归属函数（区间包含） | 路径 |
|---|---|---|---|
| `0x4B2BCD` | `cmp esi,edx; setg al; push eax` | `0x4B2630` (size 8503) | 运动/Foot AI |
| `0x4B30B2` | `cmp edi,eax; setg cl; push ecx` | `0x4B2630` (size 8503) | 运动/Foot AI |
| `0x516A41` | `cmp ebp,edx; setg cl; push ecx` | `0x5164D0` (size 1809) | 运动 |
| `0x6A221D` | `cmp esi,edx; setg al; push eax` | `0x6A1C80` (size 8470) | 运动 |
| `0x6A2702` | `cmp edi,eax; setg cl; push ecx` | `0x6A1C80` (size 8470) | 运动 |
证据 `EVIDENCE\t2_setg_sites.txt`、`EVIDENCE\t2_setg_containing.txt`。
⇒ 这 5 处选择子运行期可为 1，但都属**运动/桥上链维护**，与 `0x43F180` 放置主循环、`0x47C620` 的 10 个调用点**无交集**。**卡面「闸门在 0x47C3D0 选择子=1 分支」的假设在放置路径上不成立**（DISAGREE D1）。

---

## T2-b · 拒绝闸本体：`0x47C620` 内的类型无关占用判定

`0x47C620` 真入口 `0x47C620`，最后 `ret 0xc` @`0x47CA79`（函数体 `0x47C620..0x47CA7B`，约 2656 B；比 §983 所述「640 B」大，因其只测了前段——纪律 B：截断≠不存在）。完整反汇编 `EVIDENCE\47c620_full2_disasm.txt`。

### 已证字节事实（与 §983 一致）
- WhatAmI 比较仅 `6`(@0x47C668/0x47C7B3/0x47C825)、`0x24`(@0x47C694)、`2`(@0x47C723/0x47C7EA)；**无 15、无 1**。`[已证]`
- 读 `[cell+0xE4]` 5 次（0x47C657/0x47C683/0x47C712/0x47C79E/0x47C7D9）；**读 `[cell+0xE8]` 0 次**。`[已证]`
- `ret 0xc` ⇒ 3 栈参；`[esp+0x1c]`(arg1, int/索引)、`[esp+0x20]`(arg2, 指针，读 +0x16BF/+0x16BE/+0x16B7/+0xE58/+0xE54)、`[esp+0x24]`(arg3, 指针，`cmp eax,[esp+0x24]` @0x47C84D/0x47C8F9)。`[已证]`
- 开头 `mov eax,[0xA8E7AC]; cmp eax,0; jne 0x47CA70`（`0x47C620/0x47C62E`）⇒ 重入计数器非 0 直接 `mov al,1` 放行。

### **拒绝闸（类型无关）—— `[已证]` 结构 / `[静态推断]` 放置场景可达**
```
0047C738  call  0x47C3D0     ; arg1=&CellStruct, arg2=0(选择子=0→head A), arg3=0
0047C73D  cmp   eax, ebp     ; ebp=0
0047C73F  jne   0x47C853     ; 命中任一对象 → 0x47C853: xor al,al ; REJECT
0047C745  push  ebp ; push 0x24
0047C74A  call  0x47C4D0     ; FindObjectOfType(0x24) 补一道 Terrain 检查
0047C751  je    0x47C85F     ; 无 Terrain → 继续
...
0047C805  call  0x47C3D0     ; 另一分支同样选择子=0
0047C80A  cmp   eax, ebp
0047C80C  jne   0x47C818     ; 命中 → 后续 cmp WhatAmI,6（0x47C825）仍可 REJECT
```
- 两次 `0x47C3D0` 调用的压栈序列均为 `push ebp; lea ecx,[esp+0x14]; push ebp; push ecx`（`xor ebp,ebp`@0x47C62A ⇒ ebp=0）⇒ **arg2(选择子)=0**，只扫 head A。证据 `EVIDENCE\47c620_full2_disasm.txt`。
- 第一个闸（`0x47C73F→0x47C853`）的判据**完全类型无关**：`0x47C3D0` 只要返回非 0（head A 上有任一 `[obj+0x14]&1` 对象）就拒绝。步兵 `WhatAmI=15` 在 head A 上时会被此闸命中——**这正是「15/1 从未被比较却被拒绝」的机制**。`[静态推断]`（可达性取决于 HouseClass 标志 `[arg2+0x16BF/0x16BE/0x16B7/0xE58]` 与全局 `[0xA8E9A0]`，静态未定值，见 UNKNOWNS U1）
- 第二闸（`0x47C805→0x47C818→cmp eax,6 @0x47C825`）则在命中后再按 WhatAmI 复核，属 §983 已描述的 6/0x24 类检查。

### `0x47C620` 的 10 个调用点归属（详见 `CALLSITES.tsv`）
- 放置路径 2 个：`0x43F2AE`（`0x43F180` 主循环逐格）、`0x449482`（vslot107 can-place）。
- 其余 8 个：`0x47EE93`、`0x58865F`、`0x58886E`、`0x5FC6FA`、`0x6D5A98`、`0x6D5D33`、`0x716209`、`0x71C554`——归属函数见 `CALLSITES.tsv`，均非 `0x43F180` 放置主循环（纪律 D：用函数区间包含，非 entry_at_or_before）。
- **等价形式穷举（纪律 E）：** E8 direct=10；`jmp` 尾跳=0；`0x47C620` 作为 LE dword 全镜像出现=0；`mov/lea reg,0x47C620`+间接 call=0；`call [reg+disp]` 前后 10 条内出现 0x47C620 立即数=0。⇒ **含等价形式总数仍为 10。** 证据 `EVIDENCE\t1_callsites_scan.txt`、`EVIDENCE\t1_d_equiv.txt`。
- 注意区分：「10 个调用点」≠「10 个调用者函数」（纪律 8）：`0x588570`/`0x588750`、`0x6D59D0`/`0x6D5C50` 是 4 个不同函数。`[已证]`

---

## T3 · 放置路径上 WhatAmI∈{15,1} 的比较：全镜像有、放置路径无

脚本 `work\t3_whatami_scan.py`；输出 `EVIDENCE\t3_whatami_scan.txt`。

| 口径 | 值 | 分级 |
|---|---|---|
| 全 `.text` WhatAmI 虚调用 `call [reg+0x2C]` 总数 | 1109 | `[已证]` |
| 其后 5 条内 `cmp …,15` | 107 | `[已证]` |
| 其后 5 条内 `cmp …,1` | 172 | `[已证]` |
| `cmp reg,0xF` 全镜像 | 见 `EVIDENCE\t3_whatami_scan.txt`（基线，数量大，很多非 WhatAmI） | `[已证]` |
| **`0x43F180` / `0x449440` / `0x47C620` 三函数内 WhatAmI-虚调用后 `cmp 15`/`cmp 1`** | **0** | `[已证]` |

- `0x43F180` 内 `cmp ebx,0xF`×2（0x43FA75/0x43FAC9）是 `[edi+0x6ED]` 字节字段（设施方向/尺寸），`cmp [eax+0xEC],1`(0x43F2F4) 是 CellClass 字段——**都不是 WhatAmI**。`[已证]`
- ⇒ **放置链上没有任何一处「明确拒绝 Infantry/Unit 占格」的按类型判定。**
- ⇒ 与 T2-b 合读：拒绝闸是**按「格上是否有任一对象」（类型无关）**的判定，不是按 WhatAmI 分类。这是本卡对 §983 悖论的解答。`[静态推断]`（闸的结构 `[已证]`，它在真机那一格是否确由本闸拒绝仍受可达标志影响）

---

## T4 · `0x43F180` 放置主循环逐道检查（mode 1/3 挂链路径）

完整反汇编 `EVIDENCE\43f180_full_disasm.txt`（707 指令 / 2443 B）；检查映射 `EVIDENCE\t4_checkmap.txt`。
> `0x43F218`/`0x43F2AE`/`0x43F678` 是**函数体内指令地址**，非函数入口（§M4 / a-M4 VERDICT）。归属函数 = `0x43F180`（atlas size 2443，RTTI 名 `.?AVBuildingClass@@` 经 COL `0x7FC360`→TD `0x818D60` 确认，`EVIDENCE\t_final_verify.txt`）。

| # | 地址 | 判据 | 失败去向 | 会因「格上有步兵」失败？ |
|---|---|---|---|---|
| 0 | 0x43F198 | `call 0x6F4A70`（基类 slot73 前置），`test al` | `je 0x43F5E0` → return 0 | 否（基类前置） |
| 1 | 0x43F1B6 | `cmp ebp,3; ja 0x43FAFC` → 跳表 `0x43FB0C`（[0]=0x43F1CA / [1]=0x43F1E9 / [2]=0x43F9A6 / [3]=0x43F1E9） | 越界→0x43FAFC | 否（mode 分派） |
| 2 | 0x43F1F1 | `cmp [house+0xE58],0` | `je 0x43F5EF`（mode3 特化子路径） | 否 |
| **3** | **0x43F218** | `call [esi+0x1AC]` = **vtable slot+0x1AC=`0x449440`**（`EVIDENCE\t4_vtable_check.txt`），`test eax` | **`jne 0x43F5D8` → `call 0x6F4A70`(push 0) → return 0（整次放置失败）** | **是**：`0x449440` 内 `0x449482 call 0x47C620`，映射 `al`：`neg/sbb/and 0xF9/add 7` ⇒ `0x47C620` 返 0→`0x449440` 返 **7**→此 `jne` 命中。步兵格被 `0x47C620` 的类型无关闸拒绝即走此路 |
| 4 | 0x43F2AE | `call 0x47C620`（双层格循环内）`test al` | `je 0x43F504`（跳过该格后续处理，继续内层循环） | 是（同上，但非整次中止，是跳过该格） |
| 5 | 0x43F2D9 | `cmp [cell+0x38], [owner+0x294]` | `je 0x43F504` | 否（格 overlay/归属比对） |
| 6 | 0x43F2F4 | `cmp [cell+0xEC],1` | `je 0x43F504` | 否（CellClass 字段） |
| 7 | 0x43F5AF | `test [esp+0x23],al`（累积成功标志） | `je 0x43F5D8` | 间接受 3/4 影响 |
| 8 | 0x43F678 | 短路路径（mode≠3，0x43F658）第二处 `call [esi+0x1AC]`=`0x449440`，`test eax` | `jne 0x43F5E0` → return 0 | 是（同 #3） |
| 9 | 0x43F691 | `call 0x5683C0`（挂链包装） | —（成功路径） | 否 |

- **会因「格上有步兵」失败的是 #3（`0x43F218`）与 #8（`0x43F678`）的 `call [vptr+0x1AC]`=`0x449440`**，其后端 `0x47C620` 的类型无关闸（`0x47C738/0x47C73F→0x47C853`）把步兵当作「格上任一对象」拒绝。`[静态推断]`（可达标志未定，见 U1）
- 放置主循环「检查道数」核心数字：**9 道判据**（含 mode 分派与前置，`EVIDENCE\t4_checkmap.txt` 的 test/cmp→jcc 条目）。口径说明：§2 记「全函数只有 2 处 grid 操作调用」是另一量纲（grid 调用次数），与本卡「判据道数」不同，本卡不混用、不改 §2。复算：`python work\t4_checkmap.py`。

---

## 核心数字（可独立复算）
1. **`0x47C620` 调用点总数（含等价形式）= 10**：`python work\t1_callsites.py`（E8=10, jmp=0）+ `python work\t1_d_equiv.py`（imm 命中=同一 10 条；data-ptr=0；lea/mov+间接=0）。
2. **`0x47C3D0` 选择子=1 分支数 = 1**（函数体内 `test al,al` 一处，选择子 1 读 `+0xE8`）；放置路径上选择子=1 调用数 = **0**（`0x47C620` 两次调用均 arg2=0）；全镜像动态选择子(setg)站点 = 5（全在运动函数）。复算：`python work\t_final_verify.py`、`EVIDENCE\t2_setg_sites.txt`。
3. **放置路径 WhatAmI 15/1 比较数 = 0**；放置主循环判据道数 = 9（`EVIDENCE\t3_whatami_scan.txt`、`EVIDENCE\t4_checkmap.txt`）。
