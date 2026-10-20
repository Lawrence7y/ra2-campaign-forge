# P1「启动版本校验门」rebase 到 P2 基线 —— 交付回执

执行者：子代理 actor#1（P1版本门移植）
性质：纯离线补丁副本；未部署、未编译、未运行游戏；`D:\Project\ra2-campaign-forge\ra2render\` 下未写入任何字节。

## 1. 基线

| 项 | 值 | 取证 |
|:--|:--|:--|
| 在用母本 cpp sha256（改前） | `656e6b4e48cdd251f42d55c6da7b5e6b5a354284924437396c63e60588daada1` | 会话首条 `sha256sum` 三文件 |
| 同上（改后） | `656e6b4e48cdd251f42d55c6da7b5e6b5a354284924437396c63e60588daada1` | 末尾同一命令复测，逐字节未变 |
| 头文件改前/改后 | `10410c98642dc51ae1426be179e091440257fd42434e84f82d5b8059e9cf0c07` / 同值 | 同上 |
| ini 改前/改后 | `27c9a60c55a8a1b422d3ef06b90e3d343a93eb523a600286c937198b363ecee4` / 同值 | 同上 |
| 母本字节数 / 行尾 | 241,267 B / 4,006 行 / 全 CRLF（CRLF=4006, LF=4006, 无孤立 LF/CR） | python 统计 |
| P1 源 diff | `p1_src.diff`（= goal3_versioncheck_20261019 的 unified diff，sha256 `8a1b7fb48b1f29606b80c429ef2693a49d21910c490f6627b08b0e9e58f8a5ca`，逐字节相同副本） | `sha256sum` 两处同值 |

## 2. 成品

| 文件 | 字节 | sha256 |
|:--|--:|:--|
| `blitter_hooks_p2rebase.cpp` | **261,746** | **`4431f4a422411966a217289c8c864ff1caac5f50795a52cc2112a734a1a29dfe`** |
| `p1_on_p2.diff` | 32,861 | `636d4e5e142424c5aa7ade9bc9cd21707b9c22b19565600c5ec94ab49f8d8aa1` |

成品行尾与母本一致：CRLF 4,313 个、LF 4,313 个、无孤立 CR/LF；4,314 行；无 BOM。

## 3. Hunk 对照表

| # | P1 原 hunk（旧基线 b461ed21） | 施加到当前基线后的 hunk | 定位行 | 处理 |
|:--|:--|:--|--:|:--|
| 1 | `@@ -1,6 +1,8 @@` | `@@ -1,6 +1,8 @@` | 1 | **fuzzy（fuzz 2）**：P2 在 `#include <cstdlib>` 之后插入了 17 行 G3-SPLIT 注释块，P1 原 hunk 的尾随 context（旧 `ForgeTelemetry` + `g_targetScanInterval = 8`）在当前源码该处已不存在。补丁工具丢弃 2 行尾随 context 后精确落位；新增两行（bcrypt 头 + pragma）一字不差落在成品第 4–5 行。**这是本次唯一需 fuzz 的 hunk，也是唯一语义冲突点** |
| 2 | `@@ -3672,19 +3674,30 @@` | `@@ -3792,19 +3794,30 @@` | 3,792 | 整块精确匹配，行号偏移 **+120**（P2 在上方净增 120 行） |
| 3 | `@@ -3693,87 +3706,368 @@` | `@@ -3813,87 +3826,368 @@` | 3,813 | 整块精确匹配，行号偏移 **+120** |
| 4 | `@@ -3810,67 +4104,80 @@` | `@@ -3930,67 +4224,80 @@` | 3,930 | 整块精确匹配，行号偏移 **+120** |

hunk 2/3/4 的 body 与 P1 源 diff **逐行相同**（32/32、381/381、94/94 行）；hunk 1 仅尾随 2 行 context 不同，`+` 行集合完全相同。核对方式：解析两份 diff 的 hunk body 逐行比对，hunk 2/3/4 得 `body_equal=True`。

内容完整性交叉验证：
- P1 源 diff 的 **335 行新增内容**在成品中出现 **335/335**（缺失 0）。
- P1 源 diff 的 28 行删除内容中仅 1 行仍存在：`uintptr_t orig = *reinterpret_cast<uintptr_t*>(targetAddr);` —— 属**预期**：P1 把该赋值上移进 V2 逐点门（移到 `VirtualProtect` 之前），新代码里同样有这条语句，是"同一语句换位置"而非残留。
- P2 的 cpp diff 6 个 hunk 的 **160 行新增内容**在成品中 **160/160**，40 行删除内容 **0 行残留** ⇒ P2 改动零丢失。

## 4. 13 个安装点：expectOrig 逐个核对

| # | 成品行 | vtable 槽 | hook 变量 | hook 函数 | outOrig | **expectOrig（第 5 参）** |
|--:|--:|:--|:--|:--|:--|:--|
| 1 | 4103 | `ADDR_VTABLE_BLIT_TRANS_XLAT_ALPHA_ZREAD + 4` | hook1 | `BlitterHooks::Hook_BlitTransXlatAlphaZRead` | `g_pOrigBlitTransXlatAlphaZRead` | `ADDR_VFUNC_BLIT_TRANS_XLAT_ALPHA_ZREAD` |
| 2 | 4110 | `ADDR_VTABLE_BLIT_TRANS_XLAT_G + 4` | hook2 | `BlitterHooks::Hook_BlitTransXlat_G` | `g_pOrigBlitTransXlat_G` | `ADDR_VFUNC_BLIT_TRANS_XLAT_G` |
| 3 | 4117 | `ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G + 4` | hook3 | `BlitterHooks::Hook_RLEBlitTransXlat_G` | `g_pOrigRLEBlitTransXlat_G` | `ADDR_VFUNC_RLE_BLIT_TRANS_XLAT_G` |
| 4 | 4124 | `ADDR_VTABLE_BLIT_TRANS_G + 4` | hook4 | `BlitterHooks::Hook_BlitTrans_G` | `g_pOrigBlitTrans_G` | `ADDR_VFUNC_BLIT_TRANS_G` |
| 5 | 4131 | `ADDR_VTABLE_BLIT_TRANS_DARKEN_G + 4` | hook5 | `BlitterHooks::Hook_BlitTransDarken_G` | `g_pOrigBlitTransDarken_G` | `ADDR_VFUNC_BLIT_TRANS_DARKEN_G` |
| 6 | 4138 | `ADDR_VTABLE_BLIT_PLAIN_G + 4` | hook6 | `BlitterHooks::Hook_BlitPlain_G` | `g_pOrigBlitPlain_G` | `ADDR_VFUNC_BLIT_PLAIN_G` |
| 7 | 4145 | `ADDR_VTABLE_ENTRY_TECHNO_AUTO_TARGET` | hook7 | `TargetHooks::Hook_Techno_SelectAutoTarget` | `g_pOrigTechnoSelectAutoTarget` | `ADDR_ORIG_TECHNO_AUTO_TARGET` |
| 8 | 4152 | `ADDR_VTABLE_ENTRY_UNIT_AUTO_TARGET` | hook8 | `TargetHooks::Hook_Unit_SelectAutoTarget` | `g_pOrigUnitSelectAutoTarget` | `ADDR_ORIG_UNIT_AUTO_TARGET` |
| 9 | 4159 | `ADDR_VTABLE_ENTRY_UNIT_DRAW` | hook9 | `FogHooks::Hook_Unit_Draw` | `g_pOrigUnitDraw` | `ADDR_ORIG_UNIT_DRAW` |
| 10 | 4166 | `ADDR_VTABLE_ENTRY_INFANTRY_DRAW` | hook10 | `FogHooks::Hook_Infantry_Draw` | `g_pOrigInfantryDraw` | `ADDR_ORIG_INFANTRY_DRAW` |
| 11 | 4173 | `ADDR_VTABLE_ENTRY_AIRCRAFT_DRAW` | hook11 | `FogHooks::Hook_Aircraft_Draw` | `g_pOrigAircraftDraw` | `ADDR_ORIG_AIRCRAFT_DRAW` |
| 12 | 4180 | `ADDR_VTABLE_ENTRY_BUILDING_DRAW` | hook12 | `FogHooks::Hook_Building_Draw` | `g_pOrigBuildingDraw` | `ADDR_ORIG_BUILDING_DRAW` |
| 13 | 4187 | `ADDR_VTABLE_ENTRY_BULLET_DRAW` | hook13 | `FogHooks::Hook_Bullet_Draw` | `g_pOrigBulletDraw` | `ADDR_ORIG_BULLET_DRAW` |

- 每个 `hookN` 的取值行就在调用点正上方一行，`hookN` 绑定的函数与 expectOrig 常量名一一对应（Blitter→BlitterHooks / Techno·Unit SelectAutoTarget→TargetHooks / 四个 Draw→FogHooks）。
- 13 个 expectOrig 引用的宏**全部在母本头文件中各存在 1 处定义**（逐名 `grep -c "define <name> "` 全为 1），无未定义符号。
- 除 13 个安装点外，P1 还给 13 个**还原点**（`RemoveVTableHooks`，成品 4226 行起）补了第 5 参，取值为对应的 `union_cast<uintptr_t>(&XxxHooks::Hook_...)`，与安装点同源、逐一对应。
- 合计 `PatchVTablePointer(` 匹配 27 处 = 1 处定义 + 26 处调用（13 装 + 13 卸），**全部 5 参形态，第 5 参均非空**。

## 5. 自检实跑记录

### (a) 标记计数
```
$ python - <<'PY'
b=open('blitter_hooks_p2rebase.cpp','rb').read(); t=b.decode('utf-8')
print('bytes', len(b)); print('G3-SPLIT', t.count('G3-SPLIT'), 'VER-GATE', t.count('VER-GATE'))
PY
bytes 261746
G3-SPLIT 30 VER-GATE 11
```
✅ G3-SPLIT = **30**（P2 全保留），VER-GATE = **11**（P1 全含入）。

### (b) 27 处调用的参数形态
逐调用点数括号层数、按顶层逗号切参（脚本输出摘录）：
```
DEF   params=5 -> uintptr_t expectOrig
 2 args=5 five=True | exp=ADDR_VFUNC_BLIT_TRANS_XLAT_ALPHA_ZREAD | hook=hook1
 ...
14 args=5 five=True | exp=ADDR_ORIG_BULLET_DRAW | hook=hook13
15 args=5 five=True | exp=union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTransXlatAlphaZRead) | ...
 ...
27 args=5 five=True | exp=union_cast<uintptr_t>(&FogHooks::Hook_Bullet_Draw) | ...
ALL_5ARG = True
```
✅ 13/13 安装点 5 参、第 5 参非空；26/26 调用全 5 参。

### (c) 反向重建（`patch -R`）
对成品副本执行：
```
$ cd _verify && patch -p1 -R --binary --forward -i ../p1_on_p2.diff -o rev.txt ra2render/blitter_hooks_p2rebase.cpp
patching file rev.txt (read from ra2render/blitter_hooks_p2rebase.cpp)
PATCH_R_EXIT=0
656e6b4e48cdd251f42d55c6da7b5e6b5a354284924437396c63e60588daada1 *rev.txt
```
✅ 反向还原结果 sha256 = `656e6b4e…daada1`，**与在用源码逐字节相同**。

正向闭合（同一 diff 再打回去）：
```
$ patch -p1 --binary --forward -i ../p1_on_p2.diff -o fwd.txt rev.txt
PATCH_FWD_EXIT=0
4431f4a422411966a217289c8c864ff1caac5f50795a52cc2112a734a1a29dfe *fwd.txt
```
✅ = 成品 sha256，双向闭合。

另跑 `--fuzz=0` 严格正向（母本副本 `_verify/fuzz/m.txt` → `out.bin`）：`FUZZ0_EXIT=0`，`out.bin` sha256 = `4431f4a4…`，同样命中成品。

### 未跑项（如实声明）
- **`-p1` 路径剥离测试未跑通**：在项目树内建 `…/ra2render/blitter_hooks.cpp` 目标树时，Mimosa 钩子以"Bash 直接写源码"拒绝了该命令（命令文本含受护路径）。替代验证 = 对**逐字节等同母本**的副本（`rev.txt`，sha 已核）显式指定目标施加同一 diff，正反向均 rc=0 且哈希命中两端；diff 头两行已用 `head -2 | cat -A` 确认就是 `--- a/ra2render/blitter_hooks.cpp` / `+++ b/ra2render/blitter_hooks.cpp`。
- **未编译、未运行**：本轮只做文本层 rebase，未调用 `cl`，未验证 bcrypt 头/库在 x86 vcvars 环境可用性，也未真机验证三道门的白名单/原值。

### (d) 母本未变
首条命令与末条命令各测一次，三文件哈希同值（见第 1 节）。✅ 母本未变。

## 6. 调整与理由（逐条）

1. **hunk 1 依赖 fuzz 2 落位**。P2 把 17 行 G3-SPLIT 注释块插在 include 区与旧的 `ForgeTelemetry` 之间，P1 原 hunk 的 2 行尾随 context 失配。补丁工具丢弃尾随 context 后落位，新增内容完整；成品第 4–5 行为 bcrypt 两行、第 6 行空行、第 7 行起是 P2 注释块。**不改 P1 内容，只接受位置漂移**。
2. **hunk 2/3/4 只重算行号（+120），内容零改动**，已用 body 逐行比对证实。
3. **成品由 `patch -o` 从母本副本生成，而非手工拼接**：这样"成品 = 母本 + P1 diff"由工具保证，且与"反向重建"互为闭环。
4. **expectOrig 一律沿用 P1 原文的常量名**，未改写成字面量——避免与母本头文件常量漂移（P1 原注释亦明令"禁漂移常量"）。

## 7. 目录内的异常与外来材料（如实记录）

本目录在 16:35–16:42 期间**存在另一个并发写入者**（非本代理）。它写出了：
- `blitter_hooks_p2rebase.txt`（261,843 B，sha `6e81569e…`）：**内容有缺陷** —— `ForgeTelemetry g_telemetry = …` 出现 **2 次**（第 7、26 行），旧的 `int g_targetScanInterval = 8;` 与 P2 新的 `= 1` **同时存在**，即 P1 hunk 1 被叠加到了错误锚点。该文件**不是**本任务交付物，已移入 `_discarded_foreign_1638/`。
- 同源的 diff、report.json、rebase_receipt.json、另一份 RECEIPT：一并移入 `_discarded_foreign_1638/` 留档，**不作为交付**。
- 期间本代理的成品 `.cpp` 曾被删除/覆盖两次，均已从 `_verify/` 校验副本重新生成并复核 sha = `4431f4a4…`。

本代理交付的 `p1_on_p2.diff` 是 **16:42 由 `diff -u` 对（母本, 成品）直接生成**（32,861 B，4 hunk），与外来 diff（32,709 B）不是同一文件。

## 8. 成品结构抽检

- `ForgeTelemetry g_telemetry =` 出现 **1** 次；`g_targetScanInterval = 8` 残留 **0** 处；`^int g_targetScanInterval` 在成品第 28 行为 `= 1`（P2 原版默认）。
- P1 三道门函数均存在且各被调用一次：`VerifyGameVersionGate`(出现 2 = 定义+调用)、`VerifyVtableEntries`(2)、`VerifyCodeSites`(2)；`VerGateSha256Hex`(3)、`VerGateParseHeader`(2)。
- `VerifyCodeSites` 引用的 `GapProtectLogBytes` 在成品中出现 12 次（定义 1 + 调用 11），该辅助函数在 P2 基线中本就存在（母本 3441 行），未因 rebase 失效。
- 9 处改码位点常量与 13 处虚表常量全部在母本头文件有定义（含 `ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G` = 0x007E55C0，:15）。

## 9. 复现

```
# 成品（对母本副本施加 P1 源 diff）
patch -p1 --binary --forward -o product.cpp -i p1_src.diff mother_copy.cpp
# diff（母本 → 成品）
diff -u --label a/ra2render/blitter_hooks.cpp --label b/ra2render/blitter_hooks.cpp \
     ra2render/blitter_hooks.cpp product.cpp > p1_on_p2.diff
# 反向
patch -p1 -R --binary -i p1_on_p2.diff -o rev.cpp product.cpp
sha256sum rev.cpp   # 期望 656e6b4e…daada1
```
