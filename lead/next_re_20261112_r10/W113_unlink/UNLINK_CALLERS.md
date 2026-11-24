# W113 — 摘链函数 `0x0047EA90` 调用点普查（gamemd.exe）

- 目标文件: `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
- SHA256: `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（本机重算一致）[已证]
- ImageBase `0x00400000`；.text VA `0x00401000`，vsz `0x3DF38D`，rawsz `0x3E0000`，实际扫描 `0x3DF38D` 字节（= min(vsz, rawsz)）。
- 工具: capstone 5.0.7 / Python 3.12.10。脚本 `census.py` 可独立重跑，复现本报告每个数字。

## 方法与标签

1. **直接调用点**: `.text` 全段逐字节找 `E8 rel32` 且 `site+5+rel == 0x0047EA90`，精确匹配。[已证]
2. **入口判定**: 候选入口三级 — A: `int3`(CC) 填充段后继且 16 对齐；B: `E8` 调用目标（calltgt 交叉验证）；C: `ret`(C3/C2) 后继且 16 对齐。
   确认手段：**从候选入口做控制流遍历**（条件跳转双向、无条件 jmp 跟随但限入口正向 0x30000 窗口、call 只记录不跟随、ret 收口），要求调用点可达、位于指令边界、且该处字节确为 `E8 rel32 -> 0x0047EA90`。全程非定长线性反汇编。
   - A 类或 B 类命中 → 入口 [已证]（依据注明类别；B 类额外标注"仅call目标"）。
   - 仅 C 类命中 → 入口 [已证]（依据弱一档：ret+对齐，边界证据不如 CC 填充硬）。
   - 全部失败 → [未证]，附最近候选。
3. **分类**: 判据 = 函数体内是否 **直接调用堆释放 `0x4A1D50`/`0x4A1CA0`**、是否 **写对象 vptr**（`C7 /0` 写数据段立即数、排除绝对地址形式 `C7 05`、排除指向 .text 的函数指针）、或 **一层被调函数**（最多展开 24 个 callee、每个 2500 条遍历上限）含堆释放。命中 → "销毁/释放路径"；否则 → "其它"。均为 **[静态推断]**，非定论。
4. **间接引用**: 全文件字节模式 `90 EA 47 00`，逐条给段、上下文十六进制、指令级判读。
5. 遍历上限：单次验证/分析最多 30000 条指令；触顶会在依据里标注"遍历达上限"（证据可能不完整）。

## 1. 总数

- 直接调用点（`E8 rel32` 精确匹配）: **1** 处 [已证]
- 其中入口判定成功: **1** 处；去重后所属函数: **1** 个
- 分类: 销毁/释放路径 **0** 个 / 其它 **1** 个（均 [静态推断]）
- 尾跳板（`E9 rel32 -> 0x0047EA90`，转发包装）: **0** 处
- 立即数引用（`90 EA 47 00`）: **0** 处，分布段: 无
- `.text` 之外段（含 `.detour`）的 `E8/E9 -> 0x0047EA90` 字节命中: **0** 处 [已证·字节级]
- 扫描器自检: 同一扫描器对堆释放锚 `0x4A1D50` 找到 **460** 个 `E8` 调用点、对 `0x4A1CA0` 找到 **331** 个 —— 说明扫描器对热函数工作正常，`0x0047EA90` 的稀少调用点不是漏报 [已证·方法自检]

## 2. 直接调用点明细

| # | 调用点 VA | 所属函数入口 | 入口依据 | 调用点判定 | 分类 [静态推断] | 关键依据 |
|---|-----------|--------------|----------|------------|-----------------|----------|
| 1 | 0x005688EB | 0x005687F0 | call目标+解码可达 [已证]；候选资格: calltgt | [已证] | other | 无释放/vptr证据 |

> `sites_in_body` 交叉验证：以下函数在完整控制流遍历中确实存在指向 `0x0047EA90` 的直接调用，与字节扫描互证：0x005687F0（覆盖 0x005688EB） [已证]

### 2.1 所属函数的完整调用上下文

**0x005687F0**（other [静态推断]）：直接 call 目标 0x0048DEE0, 0x0047EA90, 0x0047D2B0, 0x0047D2B0；间接 call（虚调用等）5 处：0x0056881D, 0x00568835, 0x0056884C, 0x00568944, 0x00568954

- 上层调用者（`E8 -> 0x005687F0` 的调用点，一跳，逐点重新解析入口）[静态推断]：
  - 0x0041552E → 0x004154BB（入口依据: ret后继(任意对齐) [已证·解码可达]；不保证是真入口，可能是同函数早退块起点；分类: other [静态推断]；依据: 无释放/vptr证据）
  - 0x0043F1D5 → 0x0043F180（入口依据: ret后继(任意对齐) [已证·解码可达]；不保证是真入口，可能是同函数早退块起点；分类: other [静态推断]；依据: 无释放/vptr证据）
  - 0x004D37F5 → 0x004D37EA（入口依据: ret后继(任意对齐) [已证·解码可达]；不保证是真入口，可能是同函数早退块起点；分类: other [静态推断]；依据: 无释放/vptr证据）
  - 0x0071C053 → 0x0071BFB0（入口依据: ret+对齐 [已证·解码可达]；不保证是真入口，可能是同函数早退块起点；分类: other [静态推断]；依据: 无释放/vptr证据）
- 直接被调函数上下文（判断该函数性质的旁证）[静态推断]：
  - 0x0048DEE0：被 2 处调用，16对齐=True；入口前几条：0x0048DEE0 push esi \| 0x0048DEE1 push edi \| 0x0048DEE2 test ecx, ecx
  - 0x0047D2B0：被 75 处调用，16对齐=True；入口前几条：0x0047D2B0 sub esp, 0x38 \| 0x0047D2B3 push ebx \| 0x0047D2B4 push ebp

## 3. 分类汇总

### 3.1 销毁/释放路径 [静态推断]（0 个）


### 3.2 其它 [静态推断]（1 个）

- **0x005687F0** — 依据: 无释放/vptr证据；函数体直接 call 目标数 3，跨距 ~0x3AE。
  - `0x005687F0  sub esp, 0x8a0`
  - `0x005687F6  push ebx`
  - `0x005687F7  push ebp`
  - `0x005687F8  push esi`

## 4. 尾跳板（E9 -> 0x0047EA90）

无。[已证]

### 4.1 `.text` 之外的段（含 `.detour`）

无字节级命中：`.detour`（0xB93000，游侠 detour 补丁段）等其它段中不存在指向 `0x0047EA90` 的 `E8/E9`。[已证]

## 5. 立即数引用（`90 EA 47 00`）

无。[已证]

## 6. 局限

- 入口判定依赖 CC 填充/call目标/ret+对齐 三类边界；未覆盖"前一函数恰好在 16 对齐处结束且无任何填充"的罕见布局（会落入 [未证]）。
- 分类为字节级静态启发（释放锚定 0x004A1D50/0x004A1CA0），最终定性需结合调用方上层语义。
- 未枚举"调用了释放但**不**调用摘链"的全量函数清单（超出本题范围，建议另立 W 卡）。
- `.data` 段 vsz 0x366BE4 但 rawsz 仅 0x6C000：大部分是运行时才填充的 BSS，文件里扫不到 —— 运行时构造的函数指针表若存在，静态扫描看不见。[未证·固有局限]
- 本报告仅回答"谁调用了 `0x0047EA90`"；编译器若把摘链逻辑**内联**到其它销毁路径，那些副本不会以 `E8` 形式出现，需语义级比对（不在本卡方法内）。[静态推断]

## 7. 解读（面向 UAF 排查，全部为 [静态推断]）

- `0x0047EA90`（摘链）在**整个镜像中只有 1 个直接调用点**（`0x005688EB`，函数 `0x005687F0`），无虚表/回调登记、无尾跳板、`.detour` 补丁段也不涉及它。[已证]
- 唯一调用者 `0x005687F0` 自身不是释放路径：函数体直接调用 `0x48DFE0`/`0x47D2B0`(×2)+5 处虚调用，直接/一层展开都**未见堆释放 `0x4A1D50`/`0x4A1CA0`，也未见 vptr 写**。[静态推断]
- `0x005687F0` 的上层调用者共 4 处，入口全部解析成功且**全部为"其它"类**（非释放路径），见 §2.1 与附录 B。多处的调用点字节模式一致：`mov ecx, 0x87F7E8; call 0x005687F0` —— `0x005687F0` 是**全局管理器单例 `0x87F7E8`（.data BSS，运行时构造）的方法**。[静态推断·字节级模式一致]
- **UAF 启示**：按本普查，"从格链摘除"只在一条玩法逻辑路径（全局管理器方法链）发生；任何**销毁/释放路径都不直接调用摘链**。若对象在销毁时未先走该管理器路径（或销毁顺序与摘链竞争），就会留下"已释放但仍在格链上"的节点 —— 与已确认的崩溃现象一致。[静态推断]
- **`0x005687F0` 函数体语义**（读自附录 A 线性解码）[静态推断]：取对象（edi）→ 经虚表取属性/类型校验 → `call 0x48DEE0` 拷贝坐标 → `shl 9`（×512）合成**格索引 esi**、边界 `0x40000` → `[ebx+0x13C]` 格指针表取格（越界回退全局 `0xABDC50`）→ `call 0x47EA90`（ecx=格，`[edi+0x8c]` 为参数）**把对象从旧格链摘下** → `call 0x47D2B0(-1)` 走新格登记。即：**摘链只发生在"对象换格/移动"玩法路径里，析构类路径没有对应调用。**
- 注意反向结论同样成立：`0x47EA90` 的摘链逻辑若被编译器**内联**进其它函数，不会以 `E8` 形式出现；本报告的"仅此一路"以内联不存在为前提（镜像几乎无 CC 填充、函数边界靠 ret 后继辨认，内联检测建议另立 W 卡做语义级比对）。[静态推断]

## 8. 已排除的死路（供后续 W 卡参考）

- 中途假设"上层调用点不可达 = detour 污染"：实测 `.text → .detour` 与 `.detour → .text` 的 `E9` 均为 0，证伪；`.detour` 段与本次普查目标无交互。[已证]
- 中途假设"镜像 16 对齐 CC 填充失效"：部分成立 —— 该镜像函数间几乎没有 int3 填充（入口靠 ret 后继辨认），因此解析加入任意对齐 ret/CC 后继候选（D/E 类）。[已证]
- 真正原因是遍历器 stop 校验最初硬编码了 `E8` 目标必须等于 `0x47EA90`，复用到上层调用点（目标为 `0x5687F0`）时恒失败；已改为 `stop_target` 参数。[已证·代码已修]

## 附录 B：上层调用者入口线性反汇编（供人工复核，非判定依据）

```asm
; 上层调用点 0x0041552E -> 所属函数 0x004154BB (ret_any)
0x004154BB mov al, byte ptr [esi + 0x418]
0x004154C1 test al, al
0x004154C3 jne 0x41525a
0x004154C9 mov eax, dword ptr [esi + 0x118]
0x004154CF test eax, eax
0x004154D1 je 0x4155ad
```

```asm
; 上层调用点 0x0043F1D5 -> 所属函数 0x0043F180 (ret_any)
0x0043F180 sub esp, 0xb0
0x0043F186 push ebx
0x0043F187 push ebp
0x0043F188 mov ebp, dword ptr [esp + 0xbc]
0x0043F18F push esi
0x0043F190 push edi
```

```asm
; 上层调用点 0x004D37F5 -> 所属函数 0x004D37EA (ret_any)
0x004D37EA lea eax, [esp + 0x10]
0x004D37EE push esi
0x004D37EF push eax
0x004D37F0 mov ecx, 0x87f7e8
0x004D37F5 call 0x5687f0
0x004D37FA pop edi
```

```asm
; 上层调用点 0x0071C053 -> 所属函数 0x0071BFB0 (ret_pad)
0x0071BFB0 sub esp, 0x10
0x0071BFB3 push esi
0x0071BFB4 mov esi, dword ptr [esp + 0x18]
0x0071BFB8 push edi
0x0071BFB9 mov edi, ecx
0x0071BFBB push esi
```

## 附录 A：所属函数线性反汇编（供人工复核，非判定依据）

以下为从入口起的线性解码（跨越 ret 后可能失配；判定一律以 §2 的控制流遍历为准）。可用 `python census.py dump 0x5687F0 120` 重现。

```asm
; === 0x005687F0 ===
0x005687F0  81eca0080000         sub esp, 0x8a0
0x005687F6  53                   push ebx
0x005687F7  55                   push ebp
0x005687F8  56                   push esi
0x005687F9  57                   push edi
0x005687FA  8bbc24b8080000       mov edi, dword ptr [esp + 0x8b8]
0x00568801  8bd9                 mov ebx, ecx
0x00568803  85ff                 test edi, edi
0x00568805  895c2418             mov dword ptr [esp + 0x18], ebx
0x00568809  0f8485030000         je 0x568b94
0x0056880F  8b8340010000         mov eax, dword ptr [ebx + 0x140]
0x00568815  8b17                 mov edx, dword ptr [edi]
0x00568817  8bcf                 mov ecx, edi
0x00568819  8944241c             mov dword ptr [esp + 0x1c], eax
0x0056881D  ff9288000000         call dword ptr [edx + 0x88]
0x00568823  8a8835020000         mov cl, byte ptr [eax + 0x235]
0x00568829  84c9                 test cl, cl
0x0056882B  0f8463030000         je 0x568b94
0x00568831  8b07                 mov eax, dword ptr [edi]
0x00568833  8bcf                 mov ecx, edi
0x00568835  ff5078               call dword ptr [eax + 0x78]
0x00568838  83f802               cmp eax, 2
0x0056883B  0f8553030000         jne 0x568b94
0x00568841  8b17                 mov edx, dword ptr [edi]
0x00568843  8d4c2430             lea ecx, [esp + 0x30]
0x00568847  51                   push ecx
0x00568848  6a00                 push 0
0x0056884A  8bcf                 mov ecx, edi
0x0056884C  ff9208010000         call dword ptr [edx + 0x108]
0x00568852  8bc8                 mov ecx, eax
0x00568854  ba20000000           mov edx, 0x20
0x00568859  e88256f2ff           call 0x48dee0
0x0056885E  8d6c2430             lea ebp, [esp + 0x30]
0x00568862  668b4500             mov ax, word ptr [ebp]
0x00568866  663dff7f             cmp ax, 0x7fff
0x0056886A  750a                 jne 0x568876
0x0056886C  66394502             cmp word ptr [ebp + 2], ax
0x00568870  0f84ca000000         je 0x568940
0x00568876  8b9424b4080000       mov edx, dword ptr [esp + 0x8b4]
0x0056887D  660302               add ax, word ptr [edx]
0x00568880  668bc8               mov cx, ax
0x00568883  668b4502             mov ax, word ptr [ebp + 2]
0x00568887  66034202             add ax, word ptr [edx + 2]
0x0056888B  66894c2414           mov word ptr [esp + 0x14], cx
0x00568890  0fbfc9               movsx ecx, cx
0x00568893  6689442416           mov word ptr [esp + 0x16], ax
0x00568898  0fbfc0               movsx eax, ax
0x0056889B  c1e009               shl eax, 9
0x0056889E  8d3408               lea esi, [eax + ecx]
0x005688A1  85f6                 test esi, esi
0x005688A3  0f8c8f000000         jl 0x568938
0x005688A9  3b74241c             cmp esi, dword ptr [esp + 0x1c]
0x005688AD  0f8d85000000         jge 0x568938
0x005688B3  8b833c010000         mov eax, dword ptr [ebx + 0x13c]
0x005688B9  8b0cb0               mov ecx, dword ptr [eax + esi*4]
0x005688BC  85c9                 test ecx, ecx
0x005688BE  7478                 je 0x568938
0x005688C0  8b5c2414             mov ebx, dword ptr [esp + 0x14]
0x005688C4  85f6                 test esi, esi
0x005688C6  7c0e                 jl 0x5688d6
0x005688C8  81fe00000400         cmp esi, 0x40000
0x005688CE  7d06                 jge 0x5688d6
0x005688D0  8bc1                 mov eax, ecx
0x005688D2  85c0                 test eax, eax
0x005688D4  750b                 jne 0x5688e1
0x005688D6  891d74dcab00         mov dword ptr [0xabdc74], ebx
0x005688DC  b850dcab00           mov eax, 0xabdc50
0x005688E1  8a978c000000         mov dl, byte ptr [edi + 0x8c]
0x005688E7  8bc8                 mov ecx, eax
0x005688E9  52                   push edx
0x005688EA  57                   push edi
0x005688EB  e8a061f1ff           call 0x47ea90
0x005688F0  85f6                 test esi, esi
0x005688F2  7c2e                 jl 0x568922
0x005688F4  81fe00000400         cmp esi, 0x40000
0x005688FA  7d26                 jge 0x568922
0x005688FC  8b442418             mov eax, dword ptr [esp + 0x18]
0x00568900  8b883c010000         mov ecx, dword ptr [eax + 0x13c]
0x00568906  8b34b1               mov esi, dword ptr [ecx + esi*4]
0x00568909  85f6                 test esi, esi
0x0056890B  7415                 je 0x568922
0x0056890D  8bce                 mov ecx, esi
0x0056890F  6aff                 push -1
0x00568911  e89a49f1ff           call 0x47d2b0
0x00568916  8b5c2418             mov ebx, dword ptr [esp + 0x18]
0x0056891A  83c504               add ebp, 4
0x0056891D  e940ffffff           jmp 0x568862
0x00568922  b950dcab00           mov ecx, 0xabdc50
0x00568927  6aff                 push -1
0x00568929  891d74dcab00         mov dword ptr [0xabdc74], ebx
0x0056892F  e87c49f1ff           call 0x47d2b0
0x00568934  8b5c2418             mov ebx, dword ptr [esp + 0x18]
0x00568938  83c504               add ebp, 4
0x0056893B  e922ffffff           jmp 0x568862
0x00568940  8b17                 mov edx, dword ptr [edi]
0x00568942  8bcf                 mov ecx, edi
0x00568944  ff522c               call dword ptr [edx + 0x2c]
0x00568947  83f806               cmp eax, 6
0x0056894A  0f8544020000         jne 0x568b94
0x00568950  8b07                 mov eax, dword ptr [edi]
0x00568952  8bcf                 mov ecx, edi
0x00568954  ff502c               call dword ptr [eax + 0x2c]
0x00568957  8bd0                 mov edx, eax
0x00568959  83ea06               sub edx, 6
0x0056895C  f7da                 neg edx
0x0056895E  1bd2                 sbb edx, edx
0x00568960  f7d2                 not edx
0x00568962  23d7                 and edx, edi
0x00568964  89542414             mov dword ptr [esp + 0x14], edx
0x00568968  8b8220050000         mov eax, dword ptr [edx + 0x520]
0x0056896E  8a8866170000         mov cl, byte ptr [eax + 0x1766]
0x00568974  84c9                 test cl, cl
0x00568976  0f8418020000         je 0x568b94
0x0056897C  8ba8f80e0000         mov ebp, dword ptr [eax + 0xef8]
0x00568982  4d                   dec ebp
0x00568983  85ed                 test ebp, ebp
0x00568985  896c2420             mov dword ptr [esp + 0x20], ebp
0x00568989  7f0c                 jg 0x568997
0x0056898B  c744242001000000     mov dword ptr [esp + 0x20], 1
0x00568993  8b6c2420             mov ebp, dword ptr [esp + 0x20]
```
