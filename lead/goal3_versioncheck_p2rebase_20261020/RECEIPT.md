# P1 版本校验门 rebase 到 P2 基线 —— 交付记录

- 日期：2026-10-20 16:5x
- 执行：主会话（指挥官）
- 性质：**离线补丁副本**，未部署、未编译、未运行游戏

## 一句话结论

P1「启动版本校验门」补丁已成功 rebase 到含 P2「玩法配置拆分」的当前母本上，成品同时保留
P2 的 30 处 `G3-SPLIT` 与 P1 的 11 处 `VER-GATE`，27 个 `PatchVTablePointer` 调用点全部补齐第 5 参
`expectOrig`，双向 `patch` 验证 rc=0。

## 交付物

| 文件 | 字节 | sha256（前16） | 说明 |
|:--|--:|:--|:--|
| `blitter_hooks_p2rebase.txt` | 261,843 | `6e81569e76434700` | **成品**（CRLF，与母本一致）。施用者改名为 `ra2render/blitter_hooks.cpp` |
| `p1_on_p2.diff` | 32,709 | `ebdcd634e626d114` | 相对当前母本的 unified diff（CRLF） |
| `p1_on_p2.report.json` | 990 | `2300dcb4e406fe29` | hunk 定位表 |
| `p1_src.diff` | 32,759 | `8a1b7fb48b1f2960` | P1 原始 diff（对照用，未改动） |
| `rebase_receipt.json` | 1,508 | `818c8415a42abccb` | 母本前后 sha 自证 |

## 基线

- 母本：`ra2render/blitter_hooks.cpp`
- sha256 前后均为 `656e6b4e48cdd251f42d55c6da7b5e6b5a354284924437396c63e60588daada1`（**未改动**）
- 241,267 B / 4,006 行 / CRLF

## Hunk 定位表

P1 原始 4 个 hunk 全部定位成功：

| # | P1 原位置 | 当前基线位置 | 替换长度 | 定位方式 |
|:--|:--|:--|--:|:--|
| 1 | `-1,6` | 第 1 行 | 3 | 前导 context 锚（P2 在 include 后插入了 G3-SPLIT 注释块，原 6 行上下文不连续）|
| 2 | `-3672,19` | 第 3,792 行 | 19 | 整块精确匹配 |
| 3 | `-3693,87` | 第 3,813 行 | 87 | 整块精确匹配 |
| 4 | `-3810,67` | 第 3,930 行 | 67 | 整块精确匹配 |

## 语义核验（15/15 全过）

| 检查项 | 结果 |
|:--|:--|
| `#include <bcrypt.h>` 存在 | ✅ |
| `#pragma comment(lib, "bcrypt.lib")` 存在 | ✅ |
| `PatchVTablePointer` 定义含第 5 参 `expectOrig` | ✅ |
| `VerifyGameVersionGate()` 定义存在 | ✅ |
| `VerifyVtableEntries()` 定义存在 | ✅ |
| `VerifyCodeSites()` 定义存在 | ✅ |
| `VerGateSha256Hex` 存在 | ✅ |
| `VerGateParseHeader` 存在 | ✅ |
| `InstallVTableHooks` 在写入前调用三道门 | ✅ |
| P2 的 `G3-SPLIT` 30 处全保留 | ✅ |
| P1 的 `VER-GATE` 11 处全含入 | ✅ |
| `ForgeTelemetry` 定义保留 | ✅ |
| `g_targetScanInterval` 定义保留 | ✅ |
| `PatchVTablePointer` 调用总数 | 27 |
| 带第 5 参的调用数 | 27/27 |

## 双向 patch 验证（系统 patch 工具）

| 步骤 | 命令 | 结果 |
|:--|:--|:--|
| 正向 | `patch -p1 --batch --fuzz=0 -i p1_on_p2.diff` | **rc=0**（全部 hunk 成功） |
| 反向 | `patch -p1 -R --batch --fuzz=0 -i p1_on_p2.diff` | **rc=0** |
| 反向还原比对 | 与母本做 CRLF 归一化比对 | **逐字节相同** |

> 说明：系统 `patch` 会打印 `Stripping trailing CRs from patch`（它默认把 CRLF 差异规范化）。
> 这不影响施加正确性——反向还原后与母本内容完全一致。施用时若需保留 CRLF，
> 加 `--binary`，或直接用 `blitter_hooks_p2rebase.txt` 覆盖。

## 施用步骤（待批准）

```bash
cd D:\Project\ra2-campaign-forge
# 1) 备份
copy ra2render\blitter_hooks.cpp ra2render\blitter_hooks.cpp.pre_vergate
# 2) 施用（二选一）
#    A. 用 diff
cd ra2render && patch -p0 --binary -i ..\out\re_work\work_chain\CONTINUE_20261003\lead\goal3_versioncheck_p2rebase_20261020\p1_on_p2.diff
#    B. 用成品覆盖（改名）
#    copy ..\out\re_work\...\goal3_versioncheck_p2rebase_20261020\blitter_hooks_p2rebase.txt ra2render\blitter_hooks.cpp
# 3) 核验
python tools\verify_hooks.py --json out\vh_vergate.json   # 期望 exit 0
# 4) 编译
cd ra2render && cl /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /LD dllmain.cpp blitter_hooks.cpp /Fe:ra2render.dll /link /MACHINE:X86 /SUBSYSTEM:WINDOWS kernel32.lib user32.lib winmm.lib bcrypt.lib
```

## 风险与未覆盖

1. **未编译**：本次只做文本层 rebase，未跑 `cl`。编译期错误（例如 `bcrypt.h` 在 vcvarsall x86 环境下的可用性）未验证。
2. **未真机**：`VerifyGameVersionGate` 的白名单哈希、`VerifyVtableEntries` 的 13 处期望原值、
   `VerifyCodeSites` 的 9 处原字节，全部继承 P1 原实现，未在本轮重算。
3. **P1 核验遗留**：原 `QC_P1_VERIFY.md` 已登记 10 项观察，其中 D1「任意 1 字节篡改 ⇒ 整体不安装」
   被判 REFUTED（实际只覆盖 `.text`/13 槽位/9 位点/PE 关键字段）。本 rebase 不改动该实现。
4. **未与 SBH 守卫合批**：② 的 `EnableSbhGuard` 补丁（另一工作流）尚未落地，两者将来需同锚合并。

## 复现

```bash
cd D:\Project\ra2-campaign-forge\scratch\p1_rebase
python byte_transplant.py --root D:/Project/ra2-campaign-forge   # 生成 diff + 成品
python check_artifact.py                                          # 15 项语义核验
```
