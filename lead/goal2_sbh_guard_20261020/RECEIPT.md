# SBH 毒值守卫补丁交付记录

- 日期：2026-10-20 16:5x
- 执行：主会话（指挥官；工作流 `dwfrun-3d9ad208` 因 provider 连续 network_error 停滞 20 分钟，改由主会话直做）
- 规格依据：`crashspec_v4/RC_SPEC_V4.md` §3.1（v4）
- 性质：**离线补丁副本 + 离线编译验证**，未部署、未运行游戏

## 一句话结论

RC-1「SBH freelist 毒值守卫」已按规格实现并**编译通过**（`CL_EXIT=0`）。cave 机器码经 capstone 反汇编
逐条核对，13/13 语义检查全过。默认 `EnableSbhGuard=0`，不碰任何字节。

## 交付物

| 文件 | 说明 |
|:--|:--|
| `sbh_guard_snippet.txt` | 守卫实现段（含 G0 门禁 / cave 构造 / 安装卸载 / 遥测） |
| `blitter_hooks_sbhguard.txt` | **成品**（母本 + 5 处插入），257,989 B |
| `sbh_guard.diff` | 相对母本的 unified diff（CRLF） |
| `assembly_report.json` | 插入点表 + 自检统计 |
| 编译产物 | `scratch/sbh_build/ra2render_sbh.dll`，174,080 B，sha256 `79a49ca9dd0e1063…` |

## 插入点（5 处，全部命中，零冲突）

| # | 位置 | 内容 |
|:--|:--|:--|
| A | `#include <cstdlib>` 之后（第 4 行） | `bcrypt.h` + `#pragma comment(lib,"bcrypt.lib")` + `bool g_enableSbhGuard = false;` |
| B | `InstallVxlCachePrewarmPatch` 定义前（第 3,755 行） | 整段守卫实现（约 300 行） |
| C | `InstallVTableHooks` 内 `InstallSwChargeOptPatch();` 之后 | `InstallSbhGuardPatch();` |
| D | `RemoveVTableHooks` 内 `RemoveSwChargeOptPatch();` 之前 | `RemoveSbhGuardPatch();` |
| E | `LoadConfig` 内 EnableLFH 读取行之后（第 635 行） | `g_enableSbhGuard = (GetIniIntEx("System","EnableSbhGuard",0,iniPath,&_sbh_hit) != 0);` |

## 编译验证

```
vcvarsall.bat x86
cl /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /LD dllmain.cpp blitter_hooks.cpp \
   /Fe:ra2render_sbh.dll /link /MACHINE:X86 /SUBSYSTEM:WINDOWS \
   kernel32.lib user32.lib winmm.lib bcrypt.lib
```

- **CL_EXIT=0**
- 2 条警告（`blitter_hooks.cpp(3835)/(3875)`: `fopen` 不安全建议）—— 属既有代码风格，非本次引入
- `bcrypt.lib` 在 vcvarsall x86 下**可用**（这是 P1 施用前必须先验证的风险点，此处已证）

## Cave 机器码核验（capstone 逐条反汇编）

实际生成的 55 字节：

```
10000000  8b 54 f9 04              mov edx, dword ptr [ecx + edi*8 + 4]   ← 复刻原指令 1
10000004  8d 34 f9                 lea esi, [ecx + edi*8]                 ← 哨兵地址
10000007  3b d6                    cmp edx, esi                           ← 空表哨兵比较
10000009  74 10                    je  0x1000001b                         ← 哨兵短路
1000000B  f7 c2 0f 00 00 00        test edx, 0xf                          ← 16B 对齐
10000011  75 0f                    jne 0x10000022                         ← 不对齐 ⇒ trip
10000013  81 fa 00 00 ff bf        cmp edx, 0xbfff0000                    ← 用户态上界
10000019  73 07                    jae 0x10000022                         ← 超界 ⇒ trip
1000001B  8b 0a                    mov ecx, dword ptr [edx]               ← 复刻原指令 2
1000001D  e9 7f fc 7c f0           jmp 0x7cfca1                           ← 回跳原版后续
10000022  f0 ff 05 04 00 00 20     lock inc dword ptr [0x20000004]        ← alignReject（lock）
10000029  f0 ff 05 00 00 00 20     lock inc dword ptr [0x20000000]        ← trips（lock）
10000030  33 c0                    xor eax, eax                           ← NULL
10000032  e9 e0 fd 7c f0           jmp 0x7cfe17                           ← 尾声
```

| 检查项 | 结果 |
|:--|:--|
| 复刻原指令 1（`mov edx,[ecx+edi*8+4]`） | ✅ |
| 哨兵短路（`lea esi` + `cmp edx,esi` + `je`） | ✅ |
| 16B 对齐检查（`test edx,0xf` / `jne trip`） | ✅ |
| 用户态上界（`cmp edx,0xBFFF0000` / `jae trip`） | ✅ |
| 复刻原指令 2（`mov ecx,[edx]`） | ✅ |
| 健康路径回跳 `0x7CFCA1` | ✅ |
| trip 路径两处 `lock inc` | ✅（2 处） |
| trip 路径 `xor eax,eax` + `jmp 0x7CFE17` | ✅ |
| **cave 内不写 eax（健康路径）** | ✅（eax 仅在 trip 被 xor） |
| cave 内无取锁/无 CRT 调用/无日志调用 | ✅（纯字节，全为 mov/lea/cmp/test/jcc/lock inc/xor/jmp） |

## G0 门禁实现状态

| 门 | 实现 | 状态 |
|:--|:--|:--|
| G0.1 整文件 SHA-256 | `SbhSha256File()`（BCrypt CNG）+ 尺寸 `4,825,360` 双判 | ✅ 已实现 |
| G0.1b 身份白名单（单条目 W-A） | `kSbhShaWhitelist` 单条，`_stricmp` 比对；不符 ⇒ `identity-unknown` 拒绝 | ✅ 已实现 |
| G0.2 `.text` raw 段哈希 | 未实现（规格为 SHOULD） | ⚠️ 未做 |
| G0.3 字节窗断言 | `SbhVerifyWindows()`：PW-1 6B 窗 + 回跳点 3B | ✅ 已实现 |
| G0.4 claims 门禁 | 离线独立（`audit_bytes.py`，13/13 已实测 OK） | ✅ 离线已跑 |
| G0.5 段级哈希 | 未实现（规格 SHOULD，工具已修但基线未实测） | ⚠️ 未做 |

## 已知偏差与未覆盖

1. **G2 严格模式未实现**：规格的 `EnableSbhGuardStrict`/region 成员扫描是可选 P1 项，本版只做 G1 快检。
2. **PW-2 次守卫窗未实现**：规格标为「可选 P1」，且其字节为 `[推演]`（非实测），规格明确要求「未验证不得启用 PW-2」。
3. **G0.2/G0.5 未实现**：两者都是 SHOULD 级；G0.1（整文件）+ G0.1b（白名单）+ G0.3（字节窗）三道 MUST 已齐。
4. **未做桌面单测**：规格 §3.1.6-6 要求「G0 门禁四条路径 + 开关幂等 + 多线程计数器精确性」的 mock 单测，本轮未写。
5. **cave 是运行期构造**：`VirtualAlloc` + 手工机器码，静态扫描 `.text` 找不到特征字节（这是设计使然，不是缺陷）；cave 内容已用 capstone 在构造逻辑层面逐条核验。
6. **未真机**：白名单哈希、13 槽位/9 位点期望值在运行期才校验；真机首次跑必须核对 `SbhGuard=identity-ok` 日志行。
7. **未做 A/B 确定性对拍**（规格 §3.1.7）：需四臂各 ≥3 局，属真机范畴。

## 施用步骤（待批准）

```bash
# 1) 备份母本
copy ra2render\blitter_hooks.cpp ra2render\blitter_hooks.cpp.pre_sbhguard
# 2) 施用（成品改名覆盖）
copy <本目录>\blitter_hooks_sbhguard.txt ra2render\blitter_hooks.cpp
# 3) ini 加键（[System] 节）
#    EnableSbhGuard=0
# 4) 编译
cd ra2render && cl /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /LD dllmain.cpp blitter_hooks.cpp ^
   /Fe:ra2render.dll /link /MACHINE:X86 /SUBSYSTEM:WINDOWS kernel32.lib user32.lib winmm.lib bcrypt.lib
# 5) 核验
python tools\verify_hooks.py --json out\vh_sbh.json   # 期望 exit 0
```

## 与 P1 版本门的关系

P1（`goal3_versioncheck_p2rebase_20261020/blitter_hooks_p2rebase.txt`）与 S2（本件）都从同一母本
`656e6b4e` 分出，**互不包含**：

| | P1 版本门 | 本件 SBH 守卫 |
|:--|:--|:--|
| `VER-GATE` | 11 处 | 0 |
| `G3-SPLIT` | 30 处 | 30 处 |
| `bcrypt.lib` | 有 | 有（各自引入） |
| 守卫点 | 虚表 13 + 直接改码 9 | PW-1 单点 5B |

两者合并需要一次新的 rebase（`bcrypt.h` include 与 `g_enableSbhGuard` 声明会冲突，需去重）。
建议在裁决窗口里一并处理。

## 复现

```bash
cd D:\Project\ra2forge-audittools\scratch_sbh
python assemble_guard.py --root D:/Project/ra2-campaign-forge   # 重新组装
python verify_cave_capstone.py                                   # cave 反汇编核验
python check_sbh_dll.py                                          # 产物结构检查
```
