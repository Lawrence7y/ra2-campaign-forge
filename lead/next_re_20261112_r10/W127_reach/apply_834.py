#!/usr/bin/env python3
"""Append §834: ②-a implementation artifacts + toolchain environment fact."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §834 · **②-a 修复已实现为可构建工件（6 个字节级验证过的 stub）+ 本机无 32 位工具链**（2026-11-15 13:20）

- **§834-1 [已证·六个例程的入口/出口语义（Ghidra 逐字节）]**
  | 例程 | 反编译签名 | this | 栈参 | 出口 | 语义 |
  |---|---|---|---|---|---|
  | `0x007241A0` | `void __thiscall(int*, char)` | ECX | 1 字节 | **`ret 4`** | 设置容器一个 byte 状态（`[this+0xC]`） |
  | `0x00724520` | `void __thiscall(int, u32)` | ECX | 1 dword | **`ret 4`** | `[this+0x228] = arg` |
  | `0x00724530` | `void __fastcall(int)` | ECX | 无 | **`ret`** | `[this+0x22C] = [this+0x228]`（保存） |
  | `0x00724540` | `void __fastcall(int)` | ECX | 无 | **`ret`** | `[this+0x228] = [this+0x22C]`（恢复） |
  | `0x00724580` | `u32 __thiscall(int, u32*)` | ECX | 1 dword | **`ret 4`** | 容器 add，**返回 al**（0=未插入） |
  | `0x00724730` | `void __thiscall(int*, int)` | ECX | 1 dword | **`ret 4`** | 容器 remove + 紧凑化 |

- **§834-2 [已证·为什么必须 hook，不能原地补丁]**
  - 六个例程的入口长度：`0x7241A0`=87B、`0x724520`=13B、`0x724530`=13B、`0x724540`=13B、`0x724580`=430B、`0x724730`=385B。
  - **最短的守卫形态**：`jecxz rel8`（2 字节，`E3 xx`）已经是最省的空判跳转，但 13 字节函数加上它仍需
    「`E3 xx` + 原体(13)」或「`85 C9 74 xx`(4) + 原体(10)」⇒ **最少 14–17 字节 > 13** ⇒ **原地放不下**。
  - `.detour` 段在 `SizeOfImage` 之外且 `Characteristics=RW`（不可执行）⇒ **不能当 code cave**（§827）。
  - ⇒ 结论：**只能运行时 hook**（整函数入口 detour）。这也让 §822-1 的"需要 code cave"结论有了明确的落地形式。

- **§834-3 [已证·搬迁长度（必须按整指令切、且 ≥5 字节容纳 `E9 rel32`）]**
  | 入口 | 搬迁字节数 | 搬迁内容 | resume |
  |---|---:|---|---|
  | `0x007241A0` | 5 | `mov al,[esp+4]` / `push esi` | `0x007241A5` |
  | `0x00724520` | 10 | `mov eax,[esp+4]` / `mov [ecx+0x228],eax` | `0x0072452A`（即 `ret 4`） |
  | `0x00724530` | 6 | `mov eax,[ecx+0x228]` | `0x00724536` |
  | `0x00724540` | 6 | `mov eax,[ecx+0x22C]` | `0x00724546` |
  | `0x00724580` | 8 | 4×push + `mov edi,[esp+0x14]` | `0x00724588` |
  | `0x00724730` | 6 | `sub esp,0xC` / `push ebp` / `mov ebp,ecx` | `0x00724736` |
  - **两个独立校验均通过**（`W128_fix\gen_entries.py` + `check_reloc.py`）：
    ① 入口字节与镜像逐字节相同（`verify_hook.py pre` → **PASS 6/6**）；
    ② **搬迁等价性**：把"stub 内搬迁字节 + resume 处原字节"拼接反汇编，与"从入口直接反汇编"的
    前若干条指令**逐条一致**，且 **resume 边界后的第一条指令也一致**（6/6 OK）。
    这排除了"长度够但切在指令中间"这类错误。

- **§834-4 [已证·stub 机器码（编译器无关，已用 capstone 反汇编自检）]**
  每个 stub 的形态固定为：
  ```
  85 C9              test ecx,ecx
  74 xx              jz  <null 路径>
  <搬迁字节，原样执行>
  E9 <disp32>        jmp <resume>        ← disp32 在安装时回填
  null:
  [31 C0]            xor eax,eax           （仅 0x724580 需要，返回值 0="未插入"）
  C2 ii 00 / C3      ret imm / ret         （与各自原出口一致）
  ```
  - 6 个 stub 长度：17 / 22 / 16 / 16 / 22 / 18 字节。
  - **null 路径不执行任何搬迁字节**，所以不会漏出 push/sub 的栈偏差（例如 `0x724730` 的 null 路径直接 `ret 4`，没有 `sub esp,0xC`）。
  - 生成器：`W128_fix\stub_gen.py`（产物 `stubs_generated.h` + `stubs.json`）。

- **§834-5 [已证·交付工件清单]**
  | 文件 | 作用 |
  |---|---|
  | `W128_fix\ra2nullguard.c` | DLL 源码（**无内联汇编**，stub 用字节数组；安装时 VirtualAlloc+回填 disp32） |
  | `W128_fix\stubs_generated.h` | 6 个校验过的 stub 字节数组 |
  | `W128_fix\gen_entries.py` | 从镜像计算搬迁长度/字节/resume |
  | `W128_fix\stub_gen.py` | 生成并自检 stub 机器码 |
  | `W128_fix\check_reloc.py` | 搬迁等价性校验 |
  | `W128_fix\verify_hook.py` | `pre`（磁盘镜像 6 处入口）/ `post --pid`（运行期核对 hook 是否装对） |
  - 安全设计：`Install()` **fail-closed** —— 入口字节与预期不符就拒绝安装；
    只对进程名 `gamemd.exe` 生效；`RA2NG_Uninstall()` 可完整还原；导出 `RA2NG_ReadEntry` 供外部探针核对。

- **§834-6 [已证·本机环境事实（会阻塞后续构建）]**
  | 项 | 实测结果 |
  |---|---|
  | `C:\msys64\mingw64\bin\gcc.exe` | 存在，但**只能出 x86_64**；`-m32` 编译**失败**（exit=1） |
  | `C:\msys64\mingw32\bin` | **空目录**（无 i686 gcc） |
  | `C:\msys64\{ucrt64,clang64}\bin` | 无 gcc/clang |
  | MSVC 2022 BuildTools | `VC\Tools\MSVC\14.44.35207` 存在，但**全盘找不到 `cl.exe`**（C++ 工作负载未安装） |
  - ⇒ **本机当前没有任何 32 位 C/C++ 工具链**，因此 `ra2nullguard.c` **尚未编译、更未真机验证**。
  - ⇒ 需要用户二选一：① 安装 i686 工具链（`pacman -S mingw-w64-i686-gcc`）或 MSVC x86 工作负载；
    ② 用用户自己的构建机编译。**在此之前，②-a 只能算"实现完成、未验证"。**
  - ⇒ 我没有替用户安装工具链（涉及网络与系统变更，属需授权操作）。

- **§834-7 [未证]**
  1. stub 在真实进程中的行为（未编译、未运行）。
  2. `Install()` 在 `DllMain` 里调用的时机是否绝对安全（目标 6 个例程在 UI/tooltip 路径，理论上不会在
     `LoadLibrary` 期间被调用，但**未真机验证**；已提供导出函数以便宿主在安全点显式调用）。
  3. 上界风险：`0x724580` 的 null 路径返回 0 后，调用者是否会因"插入失败"而走异常分支（静态看不会，见 §825-9）。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §834" in src:
    sys.exit("ABORT: §834 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §834", "ra2nullguard", "无 32 位"):
    print("  %-16s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
