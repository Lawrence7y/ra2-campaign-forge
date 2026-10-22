# R-032 异族盲验

方法：只读 `ra2youli/gamemd.exe`（未修改）。自写 PE 读取器按 5 个真实段表
（`.text` 0x401000/0x3DF38D、`.rdata` 0x7E1000/0x30074、`.data` 0x812000/0x367BE4、
`.rsrc` 0xB7A000/0x18128、`.detour` 0xB93000/0x2718）判界，越界返回空字节；
反汇编用「从函数入口开始的链式递归解码 + ESP 增量记账」，不按线性扫描切函数，
除 `jmp/ret` 之外的条件跳转全部入队，冷块不遗漏。
ESP 记账规则：push −4 / pop +4 / `sub esp,imm` / `add esp,imm` / `lea esp,imm` /
`call` 后按被调函数的 `ret imm16` 回收。于是每个 `[esp+N]` 都能换算成
「相对函数入口 ESP 的偏移」：**+4 = 第 1 个 dword 参数，+8 = 第 2 个**，依此类推；负值 = 局部变量。

---

## Q1 ReadString 及 7 个函数的栈参数个数

> 结论表里的「参数个数」= 从 `[esp+4]`起的**栈实参 dword 槽**数，与 `ret imm16 / 4` 必须一致。

| 地址 | ret imm16（字节） | 栈参数个数 | 依据指令（`eff` = 相对入口 ESP 的偏移） | 置信度 |
|---|---|---|---|---|
| `0x528A10` | `0x14` = 20 (`C2 14 00`) | **5 dword = 5** | `0x528A18 [esp+0x28]`→+16；`0x528A26 [esp+0x2c]`→+20；`0x528A31 [esp+0x1c]`→+4；`0x528A3D [esp+0x20]`→+8；`0x528B80 [esp+0x28]`→+12；`0x528BD5 [esp+0x38]`→+20 | 高 |
| `0x526810` | `0x04` (`C2 04 00`) | **1** | `0x526810 mov edx,[esp+4]`（入口未动 ESP，eff=+4）；`0x5268E3 mov ebx,[esp+0x20]`（delta=−28）→+4 | 高 |
| `0x526960` | `0x04` (`C2 04 00`) | **1** | `0x526960 mov edx,[esp+4]` eff=+4；`0x5269BD/0x5269E6 lea [esp+0x18]`（delta=−20）→+4，同一槽取地址 | 高 |
| `0x526CC0` | `0x08` (`C2 08 00`) | **2** | `0x526CC0 [esp+4]` eff=+4；`0x526D4B [esp+0x1C]`（delta=−20）→+8 | 高 |
| `0x5283D0` | `0x10` = 16 (`C2 10 00`) | **4 dword 槽 = 3 个逻辑参数**（ptr, ptr, double） | `0x5283D7 [esp+0x18]`→+4；`0x5283E5 [esp+0x1C]`→+8；`0x528525/0x528588 fld qword [esp+0x28]`（delta=−28）→+12 起 8 字节。4+4+8=16 | 高 |
| `0x5276D0` | `0x0C` (`C2 0C 00`) | **3** | `0x5276D7 [esp+0x18]`→+4；`0x5276E5 [esp+0x1C]`→+8；`0x52782F [esp+0x20]`/`0x5278C6 [esp+0x28]`（delta=−20/−28）同为 +12 | 高 |
| `0x5295F0` | `0x0C` (`C2 0C 00`) | **3** | `0x5295F7 [esp+0x18]`→+4；`0x529607 [esp+0x24]`（delta=−28）→+8；`0x52974B mov al,byte [esp+0x28]`（delta=−28）→+12（只取 1 字节，典型 bool 默认值） | 高 |
| `0x529160` | `0x10` (`C2 10 00`) | **4** | `0x529178 [esp+0x428]`（delta=−1060）→+4；`0x529189 [esp+0x42C]`→+8；`0x529324 [esp+0x434]`（delta=−1064）→+12；`0x529307 [esp+0x434]`（delta=−1060）→+16 | 高 |

### 字节级 ret 核对（每个出口都验过，不是抽样）

```
0x528A10  ret sites: 0x528BC6 C2 14 00 | 0x528BFA C2 14 00            -> 5
0x526810  ret sites: 0x52691A C2 04 00 | 0x526933 C2 04 00 | 0x52693E C2 04 00  -> 1
0x526960  ret sites: 0x526A14 C2 04 00 | 0x526A1E C2 04 00            -> 1
0x526CC0  ret sites: 0x526D80 C2 08 00 | 0x526D8A C2 08 00            -> 2
0x5283D0  ret sites: 0x528538 C2 10 00 | 0x528593 C2 10 00 | 0x52859F C2 10 00  -> 4 dword
0x5276D0  ret sites: 0x527838 | 0x527874 | 0x5278B7 | 0x5278D5 | 0x5278E1
                     （5 个出口全是 C2 0C 00）                        -> 3
0x5295F0  ret site : 0x529756 C2 0C 00                                -> 3
0x529160  ret site : 0x52934A C2 10 00                                -> 4
0x672360  ret site : 0x6723C7 C2 04 00                                -> 1
0x7480D0  ret sites: 0x748141 C3 | 0x74814D C3 | 0x748152 C3           -> 0
0x66D3A0  ret sites: 0x66D472 C2 04 00 | 0x66D47B C2 04 00            -> 1
0x672440  ret site : 0x6725E9 C2 04 00                                -> 1
0x474C70  ret sites: 0x474D2A C2 10 00 | 0x474D4A C2 10 00            -> 4 dword
0x4767C0  ret site : 0x476A1D C2 28 00                                -> 10 dword
```

### 0x528A10 的完整判据

```
00528a10  sub  esp, 0xc          ; delta = -12
00528a13  xor  eax, eax
00528a15  push ebx               ; -16
00528a16  push ebp               ; -20
00528a17  push edi               ; -24   <== 之后所有 [esp+N] 都以 -24 为基点
00528a18  mov  edi, [esp+0x28]   ; 0x28-0x18 = +16 -> ARG4 (buffer)
00528a1c  cmp  edi, eax / je     ; buffer == NULL -> 失败
00528a26  cmp  [esp+0x2c], 2     ; 0x2c-0x18 = +20 -> ARG5 (size); size < 2 -> 失败
00528a31  mov  ebx, [esp+0x1c]   ; +4   -> ARG1 (section)
00528a3d  mov  edx, [esp+0x20]   ; +8   -> ARG2 (key)
00528a49  mov  ecx, [ebp+4]      ; this->缓存节名
00528a78  push ecx / push edx / lea ecx,[esp+0x18] / call 0x4A1DE0  ; CString(section|key)
00528b80  mov  ecx, [esp+0x28]   ; +12  -> ARG3 (default)
00528bc9  push edx / push ecx / push edi ; (size, default, buffer)
00528bd0  call 0x7C91D0          ; strncpy(buffer, default, size)  [ret 0]
00528bd5  mov  eax, [esp+0x38]   ; -36+0x38 = +20 -> ARG5 再次使用
00528bde  mov  byte [edi+eax-1], 0 ; buffer[size-1] = '\0'
00528bc6  ret  0x14              ; 20 字节 = 5 dword
00528bfa  ret  0x14              ; 第二个出口，同样 0x14
```

判据链：

1. 两个出口 `0x528BC6`、`0x528BFA` 的机器码都是 `C2 14 00`（已逐字节核对），
   → 被调者清 20 字节 → **恰好 5 个 dword 参数**。
2. ESP 记账后，全函数读到的最大正偏移是 **+20**，没有任何 +24/+28 的读 → 没有第 6 个参数。
3. 语义自洽，且能对上 650 个调用点：`+4`/`+8` 只用于构造临时 CString 去查 map；
   `+12` 作为失败时的默认串（`0x528BD0` 的 strncpy 源）；`+16` 是输出 buffer
   （`0x528BBB` 只把 `buffer[0]=0`）；`+20` 先 `>=2` 守卫再用于 `buffer[size-1]=0`，
   并以 `count ≤ size` 传给 strncpy。
4. `this` 在 ECX（`0x528A1E mov ebp,ecx`），不是栈参数。
   → 「`ReadString(section,key,default,buffer,size)`，5 个栈参数 + this 在 ECX」**成立**。

### 陷阱：`0x672389` 一带 5 条连续 push，而 `0x526CC0` 只有 2 个参数

```
00672385  lea  ecx, [esp+0xc]      ; 32 字节栈缓冲
00672389  push 0x20                ; 槽(5)  size
0067238b  push ecx                 ; 槽(4)  buffer
0067238c  push 0x889f64            ; 槽(3)  default = 空串（BSS）
00672391  push esi                 ; 槽(2)  i
00672392  push edx                 ; 槽(1)  "VehicleTypes"
00672393  mov  ecx, edi            ; this = INIClass
00672395  call 0x526CC0            ; ret 8：只吃槽(1)(2)，栈上留 (3)(4)(5)
0067239a  push eax                 ; 压 ReadString 的 key
0067239b  mov  eax, [0x7f0cb0]     ; "VehicleTypes"
006723a0  push eax                 ; 压 ReadString 的 section
006723a3  call 0x528A10            ; ret 0x14：一次清 20 字节 = 刚压的 2 + 预留的 3
```

**成因**：这 5 条 push 不是一次调用的实参表，而是**为后面那个 5 参数调用预先铺好的实参槽**。
`0x526CC0` 只声明 2 个参数（`C2 08 00`，被调者清 8 字节），它取走最上面 2 个 dword，
下面 3 个 dword 原样留在栈上；随后 2 条 `push` 再补 2 个 dword，正好拼成
`0x528A10` 需要的 5 个 dword，被它的 `ret 0x14` 一次性清掉。

- **那 3 个 dword 的去向**：成为 `0x528A10` 的 ARG3/ARG4/ARG5
  = `default = 0x889F64`（空串）、`buffer = &[esp+0xc]`、`size = 0x20`。
- 反向验证：若「这 5 条 push 都是 `0x526CC0` 的实参」，则 `ret 8` 与 `ret 0x14`
  无法同时成立（返回时栈失衡 12 字节）。两条 `ret` 是字节级的硬证据，
  所以「数 push 条数」这条启发式在这里必然出错。
- 附带坑：`0x889F64` > `0x87E000`，落在 BSS，盘上**没有字节**。
  只有按段表判界的 `read()` 才能得出「它是空串」；否则会把 `.data` 尾部的其它字节读成默认值。

---

## Q2 loader 的键处理机制

### 0x672360（`0x6723C7 ret 4`）逐条结论

```
00672360  mov  eax, [0x7f0cb0]        ; 全局槽 -> 0x839E18 "VehicleTypes"
00672365  sub  esp, 0x20              ; 32 字节输出缓冲
0067236b  mov  edi, [esp+0x30]        ; +4 = INIClass*
0067236f  push eax
00672372  call 0x526960               ; n = CountKeys("VehicleTypes")   [读完取 [node+0x30]]
00672377  mov  ebx, eax               ; 上界
00672379  xor  esi, esi               ; i = 0        <== 循环变量
0067237b  test ebx, ebx / jle 0x6723ba
0067237f  mov  edx, [0x7f0cb0]
00672385..00672392  预留 5 个实参槽（见 Q1 陷阱）
00672395  call 0x526CC0               ; key = GetKeyName("VehicleTypes", i)
0067239a  push eax                    ; 该 key 成为 ReadString 的 key
0067239b  mov  eax, [0x7f0cb0]
006723a0  push eax                    ; section
006723a3  call 0x528A10               ; ReadString(section, key, "", buf, 0x20)
006723a8  test eax, eax
006723aa  je   0x6723b5               ; 失败/空 -> 跳过注册
006723ac  lea  ecx, [esp+0xc]         ; ECX = &buf（值是 C 字符串指针）
006723b0  call 0x7480D0               ; 用「值」去注册
006723b5  inc  esi
006723b6  cmp  esi, ebx / jl 0x67237f
006723ba  xor  eax, eax
006723c1  setg al                     ; 返回值 = (n > 0)
006723c7  ret  4
```

1. **是循环。** 循环变量 `esi`（`0x672379` 置 0，`0x6723B5 inc esi`，`0x6723B6 cmp esi,ebx`，
   `0x6723B8 jl`）。上界 `ebx` 来自 `0x672372 call 0x526960`，
   即「`[VehicleTypes]` 节里**键的个数**」——**运行期从 INI 数出来的**，不是编译期常量。
   该节不存在时 `0x526960` 返回 0，`jle` 直接跳过循环体并返回 false。
2. **两个调用都在，参数明确**：
   - `0x672372 call 0x526960`：ECX = INIClass（`0x672370 mov ecx,edi`），
     栈参数 1 个 = `"VehicleTypes"`（`0x67236F push eax`，eax 来自 `0x7F0CB0`）。
   - `0x672395 call 0x526CC0`：ECX = INIClass（`0x672393 mov ecx,edi`），
     栈参数 2 个 = `"VehicleTypes"`（`0x672392 push edx`）、`i`（`0x672391 push esi`）。
3. **键名是当「键」用，不是当数据/类型名直接注册。** 硬判据：
   `0x67239A push eax`（eax 就是 `0x526CC0` 的返回值）→ 落在 `0x528A10` 的 ARG2；
   `0x6723A0 push [0x7f0cb0]` 补 ARG1；`0x6723A3 call 0x528A10` 把**取到的值**写进
   `[esp+0xc]` 的 32 字节缓冲；`0x6723AC lea ecx,[esp+0xc]` 才把这个**缓冲**当 ECX 交给 `0x7480D0`。
   → 注册进去的是「值」，键名只做一次查表。
   （键可以是任意名字，引擎不看键名；真正被当作类型 ID 的是 `KEY=` 右边那个字符串。）
4. **取值失败/为空时，不注册。** 判据：`0x6723A8 test eax,eax` / `0x6723AA je 0x6723B5`
   → 直接跳到 `inc esi`，**绕开 `0x6723B0 call 0x7480D0`**。
   （`0x528A10` 失败时会在 `0x528BBB` 把 `buffer[0]` 置 0 并返回 0，
   所以「键不存在」和「值为空串」都走这条跳过路径。）
5. **键名不是字面量立即数。** 函数体内只有两个常量：`0x67238C push 0x889F64`
   （BSS 空串，作 ReadString 的 default）和 `0x7F0CB0` 这个**全局指针槽**
   （其值是 `0x839E18` → `"VehicleTypes"`）。键名 100% 来自 `0x526CC0`。
   → 因此「这个函数读了哪些键」在静态分析上**不能**回答：键集合由运行期 INI 内容决定。
   能静态回答的只有「读哪个节」（`0x7F0CB0` → `"VehicleTypes"`）和
   「遍历该节**全部**键」。其它 `0x6723xx` 系列 loader 同理，各自挂不同的 `0x7F0Cxx` 槽
   （`0x7F0C94`=Colors、`0x7F0CB8`=Sides、`0x7F0CC4`=TerrainTypes、`0x7F0CAC`=Countries、
   `0x7F0CC0`=BuildingTypes、`0x7F0CBC`=SuperWeaponTypes、`0x7F0CB4`=AircraftTypes 等，
   见 `0x7F0C78`–`0x7F0CF4` 这一整片指针槽）。

### 0x66D3A0（`0x66D472 ret 4`）与 0x672360 的结构差异

```
0066d3a0  mov  eax, [0x7f0c94]      ; "Colors"
0066d3a8  push ebp / mov ebp,[esp+0x10]  ; ARG1 = INIClass*
0066d3ad  push eax / mov ecx,ebp / call 0x526810   ; FindSection("Colors")
0066d3b7  setne al / test al / je 0x66d475         ; <== 存在性守卫，缺失直接 return false
0066d3cd  call 0x526960                            ; 键个数
0066d3e9  call 0x526CC0                            ; 第 i 个键 -> esi
0066d3f6  lea eax,[esp+0x10] / lea edx,[esp+0x14]
0066d3fe  push eax                                 ; ARG4 = 3-int 默认值（0x66D404..0x66D40E 置 0,0,0）
0066d3ff  push esi                                 ; ARG3 = key
0066d400  push ecx                                 ; ARG2 = section
0066d401  push edx                                 ; ARG1 = 3 字节输出
0066d402  mov ecx,ebp / call 0x474C70              ; ret 0x10
0066d418  mov cx,[eax] / mov [esp+0x1c],cx         ; 取回 3 字节
0066d422  mov dl,[eax+2] / mov [esp+0x1e],dl
0066d42d  call 0x626AB0                            ; ecx=key, edx=&3字节 -> 追加进全局列表
0066d432..0066d45B  两次 call 0x68C9C0(id=1) / (id=0x35)
0066d472  ret  4
```

差异（全部有地址支撑）：

- **有存在性守卫**：`0x66D3B0 call 0x526810`，其结果只被当**布尔**用
  （`0x66D3B5 test eax,eax` / `0x66D3B7 setne al` / `0x66D3BC je 0x66D475`）。
  `0x526810` 内部是「对 arg1 做 strlen 建 CString 哈希 → 查 `this+0x28` 的哈希表 →
  命中则 `mov [esi+0x38],eax` 缓存节点并返回节点载荷」的查表函数（`ret 4`、1 个参数），
  我**没有**追清它的载荷语义，所以这里只主张「非零 = 该名字存在」这一用法。
  `0x672360` 没有这一步，靠「键个数 ≤ 0」隐式判定。
- **读的是复合值，不是字符串**：走 `0x474C70`（`ret 0x10`，签名
  `(out3byte*, section, key, int3_default*)`），内部先 `sprintf("%d,%d,%d")`（字面量 `0x8189B0`）
  造默认串、再用 `0x528A10` 读、再用 `0x7CA530` 按 `"%d,%d,%d"` 解析回 3 个整数。
  `0x672360` 只读一个字符串。
- **不回建对象**：读到后走 `0x626AB0`（ecx=key, edx=&3字节；往 `0xAC48F0` 全局列表按名追加）
  和两次 `0x68C9C0`（按 name + 类别 id 在 `0xB054D4`/`0xB054E0` 表中线性查找，
  未命中就 new `0x33C` 字节 + `0x68C710` 构造，如 `0x68CA15`/`0x68CA26`–`0x68CA37`），
  类别 id 分别是 **1** 和 **0x35**（`0x66D432 6A 01`、`0x66D449 6A 35`）。
  它没有 `0x7480D0` 那种「new 0xE78 字节 UnitTypeClass」的路径。
- **返回布尔**：`0x66D46C mov al,1` / `0x66D475 xor al,al`；
  `0x672360` 返回 `setg`（键数 > 0）。

### 0x672440（`0x6725E9 ret 4`）与 0x672360 的结构差异

```
00672440  sub esp,0x24
00672443  mov eax,[0x7f0cb8]        ; "Sides"
00672451  call 0x526960             ; 键个数（无 FindSection 守卫）
00672458  push 0x83d0c8 / call 0x4068E0   ; 调试输出 "Processing sides.\n"
00672485  call 0x526CC0             ; 第 i 个键 -> ebx
0067248E/00672492 0x6A46D0(key)     ; 在 0x8B4124/0x8B4130 全局向量里按名线性查找，返回下标或 -1
00672497  cmp eax,-1 / jne 0x6724BD ; 已存在则复用
0067249C  push 0xb4 / call 0x7C8E17 ; new 0xB4 字节
006724B0  call 0x6A4550             ; 构造 +(自动追加进 0x8B4124 向量)
006724C3  mov ebp,[edx+eax*4]       ; ebp = 该 Side 对象
006724D0  call 0x4068E0             ; "Side %d: %s \n"
0067250A  call 0x4767C0             ; 读 10-dword 结构（ret 0x28，默认串用 0x889F64 空串）
00672567..006725C2  内层循环 [ebp+0xA8] 次：0x4068E0("  %s\n") + 写 [obj+0xBC]
006725E9  ret 4
```

差异：

- **自己做查名 + new + 追加**：`0x6A46D0` 线性查找 + `0x6A4550` 构造入表，
  表是 `0x8B4124`（指针数组）/`0x8B4130`（计数）——与 `0x7480D0` 用的
  `0xA83CE4`/`0xA83CF0` 是**两套不同的全局表**，对象类型也不同（`0xB4` vs `0xE78` 字节）。
- **每个键只消费一次，紧接着做多字段读取**：`0x4767C0`（10 个 dword 实参，`ret 0x28`），
  而不是「读一个字符串就注册」。
- **有内层循环**：`0x672567`–`0x6725C2`，上界 `[ebp+0xA8]`；`0x672360` 只有单层。
- **有大量调试字符串**：`0x83D0C8 "Processing sides.\n"`、`0x83D0B8 "Side %d: %s \n"`、
  `0x83D0B0 "  %s\n"`；`0x672360` 一条都没有。
- 返回同样是 `setg`（键数 > 0）。

补一条「预留槽、但由调用者回收」的同型实例（在 `0x529160` 内，字节已核对）：

```
005292e1  push 0x400                 ; 槽(3)
005292e6  push eax                   ; 槽(2)  src
005292e7  lea  eax, [esp+0x2c]       ; 槽(1)  dst
005292ec  call 0x7C91D0              ; ret 0 —— 自己不回收任何栈
005292f1  add  esp, 0xc              ; 调用者一次性回收 12 字节
```

`0x7C91D0` 是 `ret`（`C3`，0 个栈参数、cdecl 风格），3 条 push 全由调用者的
`add esp,0xc` 清掉。所以「push 条数」与「被调函数声明的参数个数」在这类 cdecl 调用上
**根本不相等**，这也是为什么不能用 push 计数当判据。
`0x672440` 里有一例**和 Q1 陷阱完全同型**、且可逐字节验算的复用：

```
006724c6  lea  eax,[ebp+0x24]      ; 名字字段指针
006724c9  push eax                 ; (a)
006724ca  push esi                 ; (b)
006724cb  push 0x83d0b8            ; (c) "Side %d: %s \n"
006724d0  call 0x4068E0            ; 该地址上就是 C3（裸 ret，ret 0）——3 条 push 无人回收
006724d5  sub esp, 0x10           ; 再开 4 个 dword（也是临时 CString 的 16 字节）
006724e0  push esi / call 0x477B60 ; ret 4（CString 拷贝构造）
006724eb  push ebx                 ; 
00672504  push [0x7f0cb8]          ; "Sides"
00672505  push ecx                 ; 
0067250a  call 0x4767C0            ; ret 0x28 = 10 个 dword
```

实测的 delta 序列（我的遍历器逐条打印，不用手算，省得算错）：

```
006724c6  d=-52  lea  eax,[ebp+0x24]
006724c9  d=-52  push eax          -> 之后 -56   (a) 名字指针
006724ca  d=-56  push esi          -> -60        (b) 索引
006724cb  d=-60  push 0x83d0b8     -> -64        (c) "Side %d: %s \n"
006724d0  d=-64  call 0x4068E0     -> 仍是 -64   （被调者裸 ret 0，什么都不清）
006724d5  d=-64  sub  esp,0x10     -> -80        4 个 dword 槽
006724e0  d=-80  push esi          -> -84
006724e3  d=-84  call 0x477B60     -> 回到 -80   （ret 4）
006724eb  d=-80  push ebx          -> -84        键名
00672504  d=-84  push eax          -> -88        "Sides"
00672505  d=-88  push ecx          -> -92        局部地址
0067250a  d=-92  call 0x4767C0
```

`0x4767C0` 入口 ESP = 我的 −92 再减 4（call 压返回地址）= **−96**，
所以它的 10 个实参分别落在 entry−92, −88, −84, −80, −76, −72, −68, −64, −60, −56：

| 实参 | entry 偏移 | 内容 | 压入点 |
|---|---|---|---|
| ARG1 | −92 | `ecx = lea [esp+0x38]`（该点 delta=−92 → eff **−28**，局部输出结构） | `0x672505` |
| ARG2 | −88 | `"Sides"`（节名） | `0x672504` |
| ARG3 | −84 | `ebx`（键名） | `0x6724EB` |
| ARG4–7 | −80…−68 | 16 字节块（`sub esp,0x10` 开的槽；`0x477B60` 拷贝一个 CString 进去）——**槽数确定，语义未逐条确认** | `0x6724D5` + `0x477B60` 拷贝 |
| **ARG8** | **−64** | **`"Side %d: %s \n"`** | `0x6724CB`（日志实参 c） |
| **ARG9** | **−60** | **`esi`（索引）** | `0x6724CA`（日志实参 b） |
| **ARG10** | **−56** | **`[ebp+0x24]`（名字指针）** | `0x6724C9`（日志实参 a） |

余额验算（用实测 delta）：`ret 0x28` 后 ESP = −92 + 40 = **−52**（遍历器在
`0x67250F` 处确实报 −52）；随后 `0x6725DF`–`0x6725E3` 四条 `pop`（+16）→ −36，
`0x6725E6 add esp,0x24`（+36）→ **0**，`0x6725E9 ret 4` 清调用者的 1 个实参。**完全平衡**。

**关键发现：`0x4068E0` 本身就是一条 `C3`（裸 `ret`）。**
这个「调试打印」在**本二进制里**被编译成空桩——调用它不产生任何输出、也不清任何栈，
但**它的 3 条实参 push 照旧存在**，于是被下一个真正的调用（`0x4767C0`）当作
ARG8/9/10 消费。这才是「push 条数离谱」的物理成因：失效的日志调用留下的实参槽被复用了。

补充一个反向证据，说明这不是我的模型巧合：`0x4068E0` 共 **1672** 个 `E8 rel32` 调用点
（raw 扫描），抽样前 200 个里只有 **113** 个紧跟 `add esp,imm`、**87** 个不紧跟——
也就是说这个桩的调用者在栈清理上**本来就不一致**。凡是靠「push 条数」或
「call 后面有没有 add esp」推断签名的做法，在它周围都会翻车。

一致性交叉验证（只取最硬的两条）：
- `0x4767C0` 入口 `0x4767C0 mov edx,[esp+0xc]`（delta 0，入口未动栈）→ eff = **+12 = ARG3**，
  紧接着 `0x4767E1 push edx`；`0x4767D5 mov eax,[esp+0xb0]`（delta −168）→ eff = **+8 = ARG2**，
  `0x4767E2 push eax` 排在它前面 → 合起来就是 `0x528A10(section=ARG2, key=ARG3, ...)`。
  这与调用点 `(0x672504 push "Sides" → ARG2, 0x6724EB push ebx → ARG3)` **完全对上**。
- `0x474C70` 内 `0x474C7B mov esi,[esp+0xa0]`（delta −144）→ eff = **+16 = ARG4**（3-int 默认值）；
  `0x474CB6 mov ecx,[esp+0xa4]`（delta −156）→ eff = **+8 = ARG2**（section）；
  `0x474CA1 mov eax,[esp+0xb4]`（delta −168）→ eff = **+12 = ARG3**（key）；
  `0x474D03 mov eax,[esp+0xac]`（delta −168）→ eff = **+4 = ARG1**，是被写入的 3 字节输出。
  → `0x474C70(out, section, key, default3int)` 与 `0x66D3A0` 的调用点
  `(局部 3 字节, "Colors", 键名, 0,0,0)` 完全对上。
  注意 `0x474C70` 内部**没有** `[esp+0xac]` 之外的写回，所以 ARG1 = out 而不是 ARG2/3。

→ 那 3 条日志 push **就是 `0x4767C0` 的 ARG8/9/10**，被它的 `ret 0x28` 一并清掉。
这是 Q1 陷阱的镜像版本：

- Q1（`0x672360`）：先铺 5 个槽，被调者只吃 2 个，**余下 3 个被下一个调用吃**；
- 这里：先 push 3 个日志实参，被调者是 `ret 0` 的裸桩，**这 3 个被下一个调用吃**。

两个方向都证明：**push 条数既会高估也会低估参数个数**。唯一可靠判据是
「被调函数自己的 `ret imm16`」，并用调用点的 ESP 余额做交叉验算。

顺带推出一个结论：`0x4767C0` 的 ARG8 是**格式化/标签字符串**
（这里传的是 `"Side %d: %s \n"`），ARG9/ARG10 是它的两个变参——
也就是说这个 INI 读取函数接受一个「调试标签 + 两个值」的尾部实参，
不是普通的数据参数。这一点纯靠 `ret 0x28` 与栈槽对齐推出来的。

---

## Q3 加未知类型名的后果

以 `0x672360` 循环末尾的 `0x6723B0 call 0x7480D0` 为起点（ECX = 值字符串指针）：

```
007480d0  push esi / push edi
007480d2  mov  edi, ecx                 ; 名字
007480d4  push edi
007480d5  push 0x817474                 ; "<none>"
007480da  call 0x7C8D20                 ; 大小写不敏感比较
007480e4  je   0x74814E                 ; == "<none>" -> 返回 NULL
007480e6  push edi
007480e7  push 0x817694                 ; "none"
007480ec  call 0x7C8D20
007480f6  je   0x74814E                 ; == "none"   -> 返回 NULL
007480f8  mov  eax, [0xa83cf0]          ; 全局 Unit 类型数量
007480fd  xor  esi, esi
00748101  jle  0x748126
00748103  mov  eax, [0xa83ce4]          ; 全局 Unit 类型指针数组
00748109  mov  ecx, [eax+esi*4]
0074810c  add  ecx, 0x24                ; 对象的 ID 字符串字段
0074810f  push ecx / push edi
00748110  call 0x7C8D20                 ; name == 已有 ID ?
0074811a  je   0x748142                 ; 命中 -> 返回既有对象
00748121  inc  esi / cmp esi,eax / jl 0x748103
00748126  push 0xe78                    ; 0xE78 = 3704 字节
0074812b  call 0x7C8E17                 ; operator new
00748135  je   0x74814E                 ; 分配失败 -> NULL
00748137  push edi
00748138  mov  ecx, eax
0074813a  call 0x7470D0                 ; 构造 + 自动追加全局表
0074813f  pop edi / pop esi / ret       ; 返回新对象（0x748141 C3）
00748142  mov  edx,[0xa83ce4]           ; <== 命中分支
00748149  mov  eax,[edx+esi*4]          ; 返回既有对象
0074814c  pop esi / ret                 ; 0x74814D C3
0074814E  pop edi / xor eax,eax         ; <== 两条 "none" 分支汇合处
00748151  pop esi / ret                 ; 0x748152 C3
```

`0x7480D0` 的三个出口都是裸 `C3`（`ret` 无立即数），即**0 个栈参数**，
名字只通过 ECX 传入。

- **它做了什么检查**：
  1. `0x7480DA call 0x7C8D20`，字面量 `0x817474` 解出 **`"<none>"`**；
  2. `0x7480EC call 0x7C8D20`，字面量 `0x817694` 解出 **`"none"`**。
  `0x7C8D20` 自身在 `0x7C8D4A`–`0x7C8D68` 做了 `sub al,0x41 / cmp al,0x1A / sbb cl,cl / and cl,0x20`
  的 A–Z 折叠，所以是**不分大小写**的整串比较（`"NONE"`、`"None"` 也会命中）。
  3. 否则在 `0xA83CE4`（数组）/`0xA83CF0`（计数）里线性 `strcmp(name, obj+0x24)`
     （`0x748103`–`0x748124` 循环），命中就返回既有对象（`0x748142`）。
- **名字不在已知集合里时：新建条目。** 既不返回失败，也不静默跳过。
  路径：`0x748126 push 0xE78` → `0x7C8E17`（new）→ `0x74813A call 0x7470D0`。
  `0x7470D0` 内部 `0x7470DE call 0x710AF0` 构造基类，四个 vtable
  `0x7F6218/0x7F61FC/0x7F61F4/0x7F61EC` 的 RTTI 全部解出为 **`.?AVUnitTypeClass@@`**；
  并且 `0x7471E8`–`0x747235` 会把新对象写进 `[0xA83CE4 + ecx*4]` 并 `inc [0xA83CF0]`
  ——**自动注册进全局 Unit 类型表**。
  唯一的「失败」出口是 `0x748135 je 0x74814E`（new 返回空）。
- 由此判断：**往 `[VehicleTypes]` 里加一个引擎不认识的名字会「成功新建」**，
  不会报错，也不会静默无效。反例仅两个保留字：`"<none>"`、`"none"`（大小写不敏感），
  它们返回 NULL 并被 `0x6723AA` 那条路径跳过。
- 该路径**全程没有任何报错/断言调用**（无 `0x4068E0` 格式化输出、无 `0x7C8E25` 之类），
  所以连日志都不会留。
- 注意：初始 `0xA83CE4`/`0xA83CF0` 都在 BSS（> 0x87E000，盘上无字节），
  加载后为 0 → 「数组为空」这一事实是静态推出的，不是运行期观测。

---

## 我踩到的坑

1. **ESP 基准算错**。第一版把 eff 算成 `disp − delta`，符号反了，
   `0x528A10` 的 `[esp+0x1c]` 被算成 ARG16。正确关系是 `eff = disp + delta`
   （delta 是 push 后的负值）：`sub esp,0xc` + 3 个 push = −24，于是 `0x528A10` 的
   `[esp+0x1c]` = 0x1c − 0x18 = **+4**。所有参数结论都依赖这一步。
2. **线性扫描会 DESYNC**。`0x5297A8` 是 `0x5295F0` 的跳转表
   （`0x529787 jmp dword [edx*4+0x5297A8]`，表项 `0x52979A`/`0x52978E`/`0x52974B`），
   顺序反汇编会把它读成 `lcall 0x5297,0x8e005297` 之类垃圾并污染后面整段。
3. **「5 条 push = 5 个参数」是错的**（见 Q1 陷阱）。硬约束是「被调函数 `ret imm16`
   + 调用点栈平衡」必须同时成立，`0x526CC0` 的 `C2 08 00` 与 `0x528A10` 的 `C2 14 00`
   正好互补成 5 个实参。
4. **`0x889F64` 在 BSS**：盘上无字节。若 `read()` 不按段表判界，
   会把别处的字节读成「默认字符串」，`0x672360` 里 `push 0x889f64` 的含义就全错（它是 ""）。
5. **`0x5283D0` 的 ret 是 0x10，但只有 3 个逻辑参数**（第 3 个是 8 字节 double）。
   只数「参数名」或只数「ret/4」会得出不同数字，必须两者对齐。
6. **绝对地址立即数搜不到调用者**。`.data` 里搜 `0x672360`/`0x7480D0` 一无所获，
   差点判定「无调用者」。它们是 `E8 rel32` 直接调用：按 `next_ip + rel32` 反算才找到
   `0x668E80 call 0x672360`、`0x6723B0 call 0x7480D0`，以及 650 个 `0x528A10` 调用点、
   69 个 `0x526960` 调用点。**不要用「立即数出现次数」判 xref。**
7. **`0x526CC0` 的返回值语义容易看错**：它不是「键名指针数组[i]」，
   而是 `[node+0x18] → [+4] 链` 走 i 步后取 `[+0xC]`（`0x526D5D`–`0x526D7B` 的循环）。
   不影响参数个数，但影响「键名当什么用」的判断。
8. **`0x7480D0` 的 ECX 是裸 `char*`**，不是 CString 对象：
   `0x6723AC lea ecx,[esp+0xc]` 传的是栈缓冲首地址，`0x7480D2 mov edi,ecx` 后直接当字符串用。
   把它当「CString 的 this」会推错两层解引用。
9. **ESP 余额自检是必要的**。对每个函数，我要求「每个 ret 出口处 delta 必须回到 0」。
   13 个函数全通过（`0x528A10`/`0x526810`/`0x526960`/`0x526CC0`/`0x5283D0`/`0x5276D0`/
   `0x5295F0`/`0x529160`/`0x672360`/`0x7480D0`/`0x66D3A0`/`0x672440`/`0x474C70`），
   唯一不过的是 `0x4767C0`——它内部有我的遍历器未建模的循环回边（`0x4768C6`/`0x476A14`
   一带的多次入边），同一 `ret 0x28` 上出现多个不同的 delta 值。
   这正是「不要从函数中间开始反汇编」的量化判据：余额不平就说明流模型错了，
   此时该函数的结论必须降级。**`0x4767C0` 我只保留两条结论**：
   ① `ret` 字节是 `C2 28 00`，即 10 个 dword；
   ② 它的 **ARG2 = section、ARG3 = key**（由它自己两处置信读推断：入口
   `[esp+0xc]`→+12=ARG3、`0x4767D5 [esp+0xB0]`(delta −168)→+8=ARG2）。
   至于 ARG8/9/10 的内容，我的依据**只在调用者一侧**（`0x672440` 的余额平衡），
   不依赖 `0x4767C0` 的内部流——所以那条结论仍然成立，但它是「调用者证据」而非
   「被调者证据」。
10. **`0x4068E0` 是裸 `C3`（0 参数、cdecl 风格），且它前面 `0x4068DF` 是 nop 填充**：
    紧邻 `0x4068D1` 还有另一个 `C3`。在这类「单字节 ret + nop 对齐」的 libc 风格函数上，
    把 `0x4068E0` 当成「取格式化字符串的函数入口」会漏掉真正的入口
    （真正的可变参实现是 `0x4068F0`，`C2 10 00`）。

---

## 置信度边界

- **高**：Q1 全部 8 个函数。`ret imm16` 是 `C2 xx 00` 字节级核对；每个参数读的 ESP 偏移
  都逐条列出，且与 `sub esp` 布局、调用点栈平衡三方自洽。
  `0x528A10` = 5 个栈参数 + this 在 ECX，置信度高。
- **高**：Q2 关于 `0x672360` 的 5 条结论（是循环 / 两个调用及其实参 / 键名作键 /
  失败不注册 / 键名非字面量）。
- **做不到**：静态**枚举**该 loader 会读哪些键。键名来自运行期 INI 的键表，
  代码里只有节名常量。这一问在静态分析范畴内不可回答；可回答的只有
  「节名 = `0x7F0CB0` → `"VehicleTypes"`」和「遍历该节全部键」。这不是判据不足，
  是问题本身在静态域内无解。
- **高**：Q3。两个字面量 `"<none>"`/`"none"` 的 VA 与文本、线性查 `obj+0x24`、
  `0xE78` 字节 new、`0x710AF0` + RTTI `.?AVUnitTypeClass@@`、`0x7471E8` 追加入表、
  全程无报错调用——都有地址支撑。
- **高**：`0x66D3A0` / `0x672440` 的**结构差异**：守卫有无、读复合值 vs 读串、
  走哪张全局表、有无内层循环、有无调试输出，全部逐指令核对过，
  且 `0x672440` 的 `call 0x4767C0` 处做了完整 ESP 余额验算（−92 → ret 0x28 → −52
  → 4 pop → −36 → add esp,0x24 → 0），10 个实参逐个对上。
- **中**：把 `0x66D3A0` 命名为 "Read_Colors"、`0x672440` 命名为 "Read_Sides"。
  节名常量是硬的（`0x7F0C94`→`"Colors"`、`0x7F0CB8`→`"Sides"`），
  但「这个 loader 的最终产物在游戏里叫什么」没有追到底：
  `0x68C9C0` 的类别 id `1` / `0x35` 分别注册进 `0xB054D4`/`0xB054E0` 表，
  而这些表对应哪个 C++ 类，我没有跟到 RTTI，故不给结论。
- **已排除的一个假矛盾**：`0x66D3A0` 在 `0x66D41B` 处把取回的 3 字节写到
  `eff = +4`（即 ARG1 的槽）。一开始我误以为「写回了调用者的参数」是记账错误；
  核对后确认这是**死槽复用**：ARG1（`INIClass*`）在 `0x66D3A9` 就已装进 `ebp`，
  其栈槽从此无用，于是被借作 4 字节暂存（只写 3 字节，`0x66D429 lea edx,[esp+0x1c]`
  再取地址传给 `0x626AB0`）。所以这里没有残差，先前那个「≤4 字节残差」的怀疑作废。
- **未做**：没有运行游戏、没有挂调试器、没有修改任何文件（除本报告）。
  所有「BSS 初始为 0」来自段表与盘上无字节的推断，不是运行期观测。
