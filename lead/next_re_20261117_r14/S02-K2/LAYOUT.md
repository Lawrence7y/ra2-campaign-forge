# S02-K2 · LAYOUT.md — SBH/内存池布局 + 异常链

## 1 · SBH（MSVC 小内存块堆 / small-block heap）布局

> 全部地址/字节实证见 `EVIDENCE/T3_heap_globals.txt`、`EVIDENCE/T3_sbh_dump.txt`。这是 MSVC 6 静态 CRT 自带的 small-block heap（`_sbh_heap_init` 族），**不是**游戏对象池；与 S02 的 CRT malloc 包装同簇。

### 1.1 全局量（写点 + 读点双支撑）

| 全局 | 宽度 | 写者全集（唯一/全部） | 读者（≥1，多在此列） | 语义 | 分级 |
|---|---|---|---|---|---|
| `[0xB78B9C]` | dword | `0x7CF6CA mov [0xb78b9c],eax`（eax=`HeapCreate` 返回值 @0x7CF6C2） | `0x7CF6DA/0x7CF72D/0x7CF751/0x7CF786/0x7DCE92…`（HeapAlloc/HeapFree/HeapDestroy 的 hHeap 参数） | SBH 后端 Win32 堆句柄 | `[已证]`（写点唯一 + 多读点 + API 语义） |
| `[0xB78B98]` | dword | `0x7CF794 mov [0xb78b98],eax`（eax=`HeapAlloc(0x140)` @0x7CF78C） | `0x7CF6FF mov eax,[0xb78b98]`（alloc 循环基址）、`0x7CF743 push [0xb78b98]`（free）、`0x7DCE92…` | SBH 描述符表基址（0x140=320 B 块） | `[已证]` |
| `[0xB78B94]` | dword | `0x7CF7A3 and [0xb78b94],0`（init 清零） | `0x7CF6F0 cmp [0xb78b94],0`、`0x7CF739 cmp ebx,[0xb78b94]`（循环上界） | 已建立的 32K 区域（region）数 | `[已证]` |
| `[0xB78B90]` | dword | `0x7CF79C and [0xb78b90],0` | alloc/free 内部（位图/计数） | 区域位图/已用计数 | `[静态推断]`（写点已证，读者未逐一列全） |
| `[0xB78B8C]` | dword | `0x7CF7AA mov [0xb78b8c],1` | — | SBH 初始化标志 | `[静态推断]` |
| `[0xB78B84]` | dword | `0x7CF7B1 mov [0xb78b84],0x10` | — | 最小块粒度 = 0x10（16 B） | `[已证]`（imm 写点） |
| `[0xB782C4]` | dword | 全镜像 `.text` **0 写点**（只在 `.data` 有初值） | `0x7C9430 push [0xb782c4]`（malloc 的 SBH 句柄）、`0x7D1059/0x7D33D5 cmp [0xb782c4],0` | CRT malloc 用的 top-level 堆句柄（非 SBH 后端，是 CRT 自留句柄） | `[静态推断]`（读点已证，写点在 .initterm 或运行期另行初始化，本卡未取到） |

### 1.2 尺寸档位与结构大小（双向核对）

| 项 | 值 | 依据（≥2 点闭合） | 分级 |
|---|---|---|---|
| 描述符表分配尺寸 | **0x140 B（320）** | `0x7CF77F push 0x140` → `HeapAlloc` @0x7CF78C → 结果存 `[0xB78B98]`；消费端 `0x7CF70C lea esi,[eax+0xC]` + `add esi,0x14` 遍历 ⇒ 每表项 **0x14 B**，`0x7CF743` 尾部再分配一块 | `[已证]` |
| 区域（region）跨度 | **0x100000 B（1 MB）**，提交 **0x4000 B（16 KB）** | `0x7CF70F push 0x4000` / `0x7CF714 push 0x100000` / `0x7CF719 push [esi]` → `VirtualAlloc`（edi=`[0x7E1290]`）@0x7CF71B | `[已证]` |
| 区域尺寸类步长 | **0x204 B（516）** | `0x7CF80D imul ecx,esi,0x204`（free 路径）+ `0x7CF739` alloc 循环同 stride（隐式）⇒ 单一 stride，**双向** | `[静态推断]` |
| 块大小档位 | 16 B 粒度起步（`[0xB78B84]=0x10`）；类 index = `(size>>4)-1`（`0x7CF82F sar ecx,4; 0x7CF834 dec ecx`），上限 0x3F（`0x7CF832 push 0x3f`）；free bitmap 位宽 32（`0x7CF84D cmp ecx,0x20 / 0x7CF852 mov edi,0x80000000; shr edi,cl`） | `[静态推断]` |
| 空闲链/位图 | 位图基 `eax + esi*4 + 0x44`（`0x7CF85F and [eax+esi*4+0x44],edi`）；链/计数 `ecx+size+4`（`0x7CF859 lea ecx,[ecx+eax+4]`, `0x7CF863 dec byte [ecx]`） | `[静态推断]`（写点单条，读者为同一 free 函数内多处） |

> **§981 槽契约**：SBH 是 C 结构、**无 vtable**，不存在"槽 12 = GetSize"问题；其结构大小由 `HeapAlloc` 立即数 + 消费 stride 双点闭合，不假定任何虚表槽。

### 1.3 字段表（每条该类自己的写点 + 读点双支撑）

| 偏移 | 宽度 | 类型 | 写者全集 | 读点 | 语义 | 分级 |
|---|---|---|---|---|---|---|
| `+0x0` | dword | region 指针 | `0x7CF719 push [esi]`（VirtualAlloc 返回写回，alloc） | `0x7CF6FF mov eax,[0xb78b98]` → `lea esi,[eax+0xC]` | 描述符表内区域指针数组 | `[静态推断]` |
| `+0xC` | dword | region base | init `0x7CF7B1` 后由 alloc 写 | `0x7CF70C lea esi,[eax+0xC]`；`0x7CF7FB sub esi,[ecx+0xC]`（free 中减基址定位 region） | 区域内存基址（用于 `shr esi,0xF` 求 region index） | `[已证]`（读点 2 + 运算闭合） |
| `+0x10` | dword | 描述符表末指针 | init 写 | `0x7CF7F6 mov eax,[ecx+0x10]`（free 取表末） | 描述符表上界 | `[静态推断]` |
| `+0x14`/step | 20 B | 表项 stride | `0x7CF735 add esi,0x14` | `0x7CF739 cmp ebx,[0xb78b94]`（循环） | 每 region 描述符 20 B | `[已证]`（stride 写读成对） |
| `+0x44` | dword×N | 空闲位图 | `0x7CF85F and [eax+esi*4+0x44],edi` | 同函数 `0x7CF857 shr edi,cl` 后 `and` 再 `dec byte [ecx]` | 32 档空闲块位图 | `[静态推断]` |

## 2 · 异常 / 崩溃守卫链（T4）

### 2.1 安装点

- `0x006BE07F push 0x6BB990` → `0x006BE084 call dword ptr [0x7E1144]` = **`SetUnhandledExceptionFilter(0x6BB990)`**。IAT `[0x7E1144]`=`KERNEL32!SetUnhandledExceptionFilter`（pefile 实测）。
- 处理函数 `0x6BB990` 是 **6 字节尾跳桩**：`mov eax,[ecx]; mov edx,ecx; mov ecx,[eax]; jmp 0x4C8FE0`（`EVIDENCE/T4_chain_disasm.txt`）。atlas gap（前序 atlas `0x6BB8E0+175=0x6BB98F`，后序 `0x6BB9A0`），按"前驱 ret+nop + 非 jcc 目的 + jmp 目标为已知函数"独立定界。
- 另有 2 处 `SetUnhandledExceptionFilter` @ `0x7D9FB1`/`0x7D9FC3`（CRT `_set_invalid_parameter` 类安装，非游戏崩溃日志链）。

### 2.2 except.txt 写入点（可验证锚点 —— **找到**）

- 函数 `0x4C8FE0`（atlas gap，`0x4C8FD4 ret` + 4 nop 后，`0x6BE06F` 直接 jmp 到此 ⇒ 真入口）：
  - `0x4C8FE4 push 0x822204`（`"Exception_Dialog()\n"`）→ printf
  - `0x4C8FF1 call 0x53E6B0`（`Game::ModalDialog` / 模态事件泵）
  - `0x4C9005 call 0x4C85E0`（imagehlp 崩溃转储：查 `EVIDENCE/T4_string_search.txt`：`SymInitialize failed`/`SymLoad failed`/`Exception occurred at %08X`/`Exception code is %d`/`Access address:%08X`）
  - **`0x4C901C push 0x8221F8`（字符串 `"except.txt"`，`.data`，全镜像唯一 1 处）→ `0x4C9021 call [0x7E11BC]` = `CreateFileA(GENERIC_WRITE, share=0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL)`**
  - `0x4C903A call [0x7E11AC]` = `lstrlenA`（取日志长度）→ `0x4C9047 call [0x7E11A0]` = **`WriteFile`** → `0x4C904E call [0x7E11E0]` = `CloseHandle`
  - 对照 `ra2youli\except.txt`：26,272 B / 2026-11-13 06:29:17（未变，本卡只读）。

### 2.3 链（异常发生 → 处理 → 写日志 → 退出）

```
[异常发生] 访问违例 / 除零 / 断点等
   ↓ (Windows SEH 顶层分发，调用已注册的 UnhandledExceptionFilter)
[已安装处理器] 0x6BB990  ← SetUnhandledExceptionFilter @ 0x6BE084 安装
   ↓ 尾跳 jmp
[0x4C8FE0] 崩溃处理器入口：打印 "Exception_Dialog()" (0x822204)
   ↓ call
[0x4C85E0] imagehlp 取证：LoadLibrary("IMAGEHLP.DLL") → SymInitialize/SymLoad/SymGetSymFromAddr
            格式化 "Exception occurred at %08X" / "Exception code is %d" / "Access address:%08X"
   ↓ 若递归计数 [0x820E5C]==0（0x4C8FFB-0x4C9001，否则跳过写文件）
[0x4C901C] CreateFileA("except.txt" @0x8221F8, GENERIC_WRITE, CREATE_ALWAYS) @0x4C9021
   ↓
[0x4C9047] WriteFile(句柄, 格式化日志) → CloseHandle @0x4C904E
   ↓
[0x4C9054..] 检查若干全局对象（0x887308/0x88730C/0x88731C…）的虚方法 [+0x6C]
   ↓
[0x4C90EF] "Dump exception info\n" → call 0x4C84E0；cmp eax,0x481
   ↓
[退出]  TerminateProcess（IAT [0x7E11B0]，调用点 0x664667/0x7CBE38）或
         游戏自身退出路径；直接写进程内存/注入均未发生（本卡静态）。
```

> 边界说明：`0x4C8FE0` 写入函数与 `0x4C85E0` 取证函数均未在我方 atlas 以完整函数录入（`0x4C8FE0` 在 atlas gap）。按纪律 2：4 项全满足（16B 对齐? `0x4C8FE0 % 16 = 0`；前驱 `0x4C8FDC..DF` 4×nop；非 jcc 目的——`0x6BE06F jmp` 直接指向；序言 `push ecx/push esi/mov esi,edx`），故判为真入口。

## 3 · 停机核验（纪律 9）

| 锚点 | 已入账 | 本卡实测 | 结论 |
|---|---|---|---|
| 目标 SHA-256 | `73201CC0…F67476` | 全值一致 | ✓ |
| `.text` 全指令数 | 1,394,120（+66 skipdata） | 1,394,186（含 66 skipdata） | ✓ 口径差异同一次反汇编 |
| `except.txt` | 26,272 B / 2026-11-13 06:29:17 | 未变 | ✓ |
| coverage 数据行 | 18,431 | 18,431 | ✓ |
| ②-a：30 调用点/26 可达 | 只引用不重做 | 未重做（D-35 裁决前按 A 不打补丁） | ✓ |
| 63 B int3 洞 / 3,944 initterm | 只引用不重做 | 未重做 | ✓ |
