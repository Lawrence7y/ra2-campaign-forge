# ra2forge FORGE-2 收口报告：R1–R5 内容裁决落地 + 依赖方修复（MCP / ra2opt / DESIGN）

> 任务卡 **FORGE-2** · 执行方 **DSH 子代理** · 工作区 `D:\Project\ra2-campaign-forge`
> 基线二进制 `ra2youli\gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（**只读**，改动前后一致，LastWriteTime 2026/09/25 16:10:48 未变）
> 证据等级：[实证] = VA+原始字节（`tools/audit_bytes.py` 复算）或 文件:行；[推演]；[待实测]
> 快照口径：本报告全部数字来自 2026-09-27 10:03–10:12 的本会话快照；期间工作区无其它会话写入（ra2youli 内最新 mtime 为 09:31:17，早于本任务首次写入 10:03:46）

---

## [0] 结论摘要

1. **R1–R5 全部落地**：条目 ID 固定 `RA2F1`（`[Battles] 15=RA2F1`，不占用官方 1..14 与官方条目名），`campaign.id` 可选覆盖并带字符集/长度/官方 ID 校验；顺序仍 `ECH01→ECH02→ECH03→空`（R2）；`Description` 读自设计文件 `campaign.description`（R3，源码里无硬编码）；图标保持苏军（R4 未改动）；末关写 `EndOfGame=yes`（R5）。
2. **构建期自检加严**：地图链 → `NextScenario` + `EndOfGame` 双断言（读盘字节），`BATTLEMD98.INI` 也**读回磁盘**断言（索引/id/首关/Description/无官方条目名），任一不符即 `BuildError`。
3. **依赖方 D1–D5 全部修完**：MCP 安装改走 `ra2forge.install.install_package`（整包 + 备份 + 清单，可卸载还原）；描述串补 “loose, appended”；ra2opt 体检与自检夹具认散装 `BATTLEMD98.INI`；DESIGN.md 新增两节。
4. **门禁与套件全绿**：`verify_anchors` **323/323 PASS**；`audit_bytes claims_forge2.txt` **18/18 OK**；FORGE-2 新套件 **72/72 PASS**；FORGE-1 套件（已按 R1/R3/R5 更新过期断言，51→58 条）**58/58 PASS**；`ra2opt selftest` **36 项全通过**。
5. **最大风险（未闭环）**：末关 `EndOfGame=yes` 的**通关行为**、`[Battles]` 索引归并、以及「删掉散装 `BATTLEMD.INI` 后引擎是否回退 MIX 内官方件」仍需真机验证（§4）；本机 `ra2youli\` 仍是旧版安装，**本任务未改动该目录任何文件**。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| R1 | 条目名改 `RA2F1`、不占官方条目名、`campaign.id` 可选 + 校验 | **已落地**：默认 `RA2F1`；设计提供 `campaign.id` 时优先（ASCII 字母开头、`[A-Za-z0-9_]`、1..16 字符、拒绝 `ALL\d+/SOV\d+`）；`[Battles]` 仍用索引 15 | [实证] | `ra2forge/design.py:32-34`（常量）、`:218-246`（`campaign_battle_id`）、`:83`（validate 调用）；`ra2forge/builder.py:279-292`（`battle_id_for`）、`:106`（build 调用）；产物 `out/forge2_verify/build/钢铁残响/BATTLEMD98.INI` = `15=RA2F1` |
| R2 | 顺序 ECH01→ECH02→ECH03 不回归 | **保持**：三图 `NextScenario=ECH02.MAP / ECH03.MAP / 空`（读回字节断言） | [实证] | `out/forge2_verify/build/钢铁残响/ECH0{1,2,3}.MAP`；`out/re_work/forge2/verify_output.txt` F2-1a |
| R3 | `Description` = 设计文件 `campaign.description`，禁止硬编码 | **已落地**：`Description` 与设计文件逐字节相同（GBK），源码无该文案；缺失时回退 `campaign.name` 并 warning | [实证] | `ra2forge/builder.py:294-302`（`_battle_ini` 用 `design_mod.description_for(camp)`）；`ra2forge/design.py:250-254`（`description_for`）、`:86-89`（缺失 warning）；产物 `BATTLEMD98.INI` `Description=` 行 |
| R4 | 图标保持苏军 | **未改动**：`campaign.side` 默认 `soviet`，本卡无图标相关写入 | [实证] | `git` 无仓库；本卡改动清单 §[5] 不含图标路径；`examples/demo_campaign.json:5` `"side": "soviet"`（**未改**） |
| R5 | 末关 `NextScenario` 空 + `EndOfGame=yes` | **已落地**：末关（链尾）写 `EndOfGame=yes`，其余 `no`；引擎确实从 `[Basic]` 读该键 | [实证] | `ra2forge/maplib.py:111`（默认值）、`:225`（写出）；`ra2forge/builder.py:86`（链尾 = `not chain[i]`）、`:147-183`（读回断言，`EndOfGame` 在 172-177）；引擎侧 VA `0x68A10E`（claims #8–#11） |
| D1 | MCP 只复制 mix ⇒ 游戏里看不到 | **已修**：`tool_build` 改调 `install_mod.install_package(mix.parent, game)`，安装失败不再伪装成构建失败 | [实证] | `mcp/ra2forge_mcp.py:52-84`（调用在 `:73`）；验证 F2-4（stdio 端到端）：装出散装 `BATTLEMD98.INI` + 3 图 + mix + 清单，官方 `BATTLEMD.INI` 哈希不变，可卸载还原 |
| D2 | MCP 描述串补 “loose, appended” | **已补** | [实证] | `mcp/ra2forge_mcp.py:120-123`；F2-4 断言 `"loose, appended" in description` |
| D3 | ra2opt 以 `BATTLEMD.INI` 判定已装战役包 | **已追加散装 `BATTLEMD98.INI` 识别**（保留旧形态，不误报空目录） | [实证] | `ra2opt/audit.py:174-192`（`battlemd98_ini`/`battlemd98_head`）、`:463-475`（finding）；F2-5 四场景（new / legacy / mix-only / bare） |
| D4 | 假战役夹具补新命名 | **已追加** `BATTLEMD98.INI`（`15=RA2F1`）并纳入 `pristine` 与「不碰战役产物」断言 | [实证] | `ra2opt/tests.py:394-402`（夹具）、`:410`（pristine）、`:442-448`（断言）、`:475`（用例名）；F2-6 + `ra2opt selftest` 36 项全通过 |
| D5 | DESIGN.md 增两节 | **已增**：①《关卡链与 NextScenario（含可选单关 next 覆盖）》②《产物命名与安装形态（散装 BATTLEMD98.INI + expandmd98.mix 只放资源 + 迁移须知）》 | [实证] | `docs/DESIGN.md`（134 → 159 行；另在顶层结构补 `campaign.id`、mission 表补 `next` 行） |
| 验证1 | 重生成产物 + 读回字节自证 | **已完成**：`out/forge2_verify/build/钢铁残响/`，F2-1a~F2-1e 全 PASS | [实证] | `out/re_work/forge2/verify_console.txt`、`verify_output.txt` |
| 验证2 | FORGE-1 套件仍全 PASS | **58/58 PASS**（更新 3 处过期断言，见 §[3]） | [实证] | `out/re_work/forge1/verify_console.txt`、`out/re_work/forge1/verify_output.txt` |
| 验证3 | MCP 安装路径端到端（D1） | **已完成**（真起 MCP stdio 子进程 + 临时游戏目录） | [实证] | F2-4，`out/re_work/forge2/verify_console.txt` |
| 迁移 | 纸面迁移规程（不执行） | **已按新裁决改写**（见文末附录；FORGE-1 §5 第 3 步作废） | 纸面规格 | §[3] 第 1 条 |

---

## [2] 关键证据块

全部 18 条机器可读断言：`out/re_work/forge2/claims_forge2.txt`，复算 `python tools\audit_bytes.py out\re_work\forge2\claims_forge2.txt --verbose` → **OK=18 MISMATCH/NOREAD=0**。

**(a) R5 的引擎依据（新增，FORGE-1 未取）** —— 引擎从 `[Basic]` 读 `EndOfGame`：

```text
0x83E138 = 45 6e 64 4f 66 47 61 6d 65 00 00   # [.data] "EndOfGame"
0x82BF9C = 42 61 73 69 63 00                  # [.data] "Basic"（段名）
0x68A10E  68 38 E1 83 00   push 0x83e138      # "EndOfGame"
0x68A113  68 9C BF 82 00   push 0x82bf9c      # "Basic"
0x68A118  8B CF            mov ecx, edi
0x68A11A  E8 D1 F4 E9 FF   call 0x5295f0      # INI 读取助手（bool）
0x68A11F  88 86 AC 34 00 00  mov byte ptr [esi + 0x34ac], al   # 结果落进场景对象
0x68B143  68 38 E1 83 00   push 0x83e138      # 第二处读点（全局 INI 对象 0x7F0E4C）
```
同一函数内紧跟其后读取的键是 `TimerInherit`（0x68A0F0 push 0x83E144）、`MultiplayerOnly` 等，正是我们已经在写的 `[Basic]` 键集合 —— 故「`EndOfGame` 是地图 `[Basic]` 的引擎识别键」为 **[实证]**；「`yes` 让通关后回主菜单」仍是 **[待实测]**（U-FORGE2-1）。
官方末关样例：`extracted/yr_maps/map_133A0CB2.map:261-267`（`[Basic]` … `EndOfGame=yes`）。

**(b) 条目注册路径（沿用 FORGE-1，本次复算）**：

```text
0x52CBA0  68 A8 61 82 00   push 0x8261A8  -> "BATTLEMD*.INI"
0x52CBA9  FF 15 08 12 7E 00  call [0x7E1208] = FindFirstFileA
0x52CCCD  68 98 61 82 00   push 0x826198  -> "BATTLEMD.INI"（回退）
0x46CE10  83 EC 24         sub esp,0x24          # [Battles] 列表函数起点（前有 NOP 填充）
0x46CE1C  E8 3F 9B 0B 00   call 0x526960         # push 0x81B1D8 "Battles" -> 取条目数
0x81B1C8  46 69 6E 61 6C 4D 6F 76 69 65 00 00 43 44 00 00 42 61 74 74 6C 65 73 00
                          # "FinalMovie\0\0CD\0\0Battles\0"
0x46CD1E  68 C8 B1 81 00   push 0x81B1C8  # 条目读取器读 FinalMovie（同处读 CD / Scenario）
```
⇒ 注册文件必须散装（FS 通配看不到 MIX 内条目）；条目按 id 挂载。**措辞勘误见 §[3] 第 4 条**。

**(c) 产物读回（R1/R2/R3/R5 一次自证）** —— `out/forge2_verify/build/钢铁残响/`：

```text
ECH01.MAP  14226 B  NextScenario=ECH02.MAP  EndOfGame=no
ECH02.MAP  13606 B  NextScenario=ECH03.MAP  EndOfGame=no
ECH03.MAP  15483 B  NextScenario=           EndOfGame=yes   （FORGE-1 为 15482 B / EndOfGame=no）
BATTLEMD98.INI 453 B sha256=4e34175689248917…
  [Battles]
  15=RA2F1
  [RA2F1] CD=2 / Scenario=ECH01.MAP / FinalMovie= / Description=<设计文件 campaign.description 原文>
expandmd98.mix 43361 B：3 个条目（ECH01/02/03.MAP 的 CRC），0 个 INI
```

---

## [3] 勘误

| 目标 文件:行 | 改前（原文） | 改后（文本） | 理由 | 影响面 |
|---|---|---|---|---|
| `docs/re/ra2forge_fix_forge1.md` §5.3（及 `out/re_work/forge1/SUPPLEMENT_R1-R5.md` 迁移“次选”一条） | 「次选：以 `extracted/found_battlemd.ini` 为模板重建 `[ALL1]/[SOV1]` 两条官方条目（**注意**：该样例含 RA2 调试占位条目 `ALL02...SOV07`，正式版未必相同…）」 | 「**不要**用 `extracted/found_battlemd.ini` 还原官方文件；正确做法：把被旧版改写的散装 `BATTLEMD.INI` **备份为 `.ra2forge.bak` 后删除**，引擎自然回退到 MIX 内的官方同名件」 | 用户裁决；该样权威性未定（MB1 U-MB1-4），拿它当官方原文风险高于直接删除 | **产品决策级**；已同步改 `README.md`、`docs/DESIGN.md`、本报告附录 |
| `docs/re/ra2forge_fix_forge1.md` §3.2 / §9、`README.md` 格式依据节 | 条目 ID = `RA2F<crc16(战役名)>`（如 `RA2FD4D6`） | 条目 ID = 固定 `RA2F1`（`campaign.id` 可覆盖） | 用户裁决 R1：不要按名字派生，避免同一包换名后注册成另一条 | 产品决策级；`README.md` 已改，FORGE-1 报告保留为历史快照 |
> **【勘误 2026-09-27 · 见 §5 第 3 步】**本表上一行（`ra2forge_fix_forge1.md` §5.3）的「改后」文本曾写「备份后删除散装 `BATTLEMD.INI`，引擎自然回退 MIX 内官方件」——该结论已被 Lead 实测**推翻**（无任何 MIX 含官方 `BATTLEMD.INI`）。正确迁移是从 `extracted/found_battlemd.ini` **恢复**该文件，详见 §5 第 3 步。
>
> 【W3 勘误 · Forge P-6 / 4点-4】改前：无任何 MIX 含官方 `BATTLEMD.INI`（17 个 MIX 全扫）；改后：嵌套 MIX 内实证存在官方 `BATTLEMD.INI`（`ra2md.mix → 嵌套 MIX 0xFBE0D09D → 0x07E280DD`，2,733 B，sha256 `7e40691a…` 与 `extracted/found_battlemd.ini` 逐字节相同）；但引擎删散装后是否回退读 MIX 内件仍属未闭环（U-FORGE2-3）；且 `extracted/all_inis/*.ini` 首行被工具写坏，禁止用其替代；依据：`out/re_work/qc/W2_20261001/forge/scripts/battlemd_authority.py`；分级：[实证]

| `docs/re/ra2forge_fix_forge1.md` §6 U-FORGE1-3 | 「末关 `NextScenario=` 空 + `EndOfGame=no` 是否被接受为战役结束」 | 已裁决：末关写 `EndOfGame=yes`（官方末关惯例） | 用户裁决 R5 + 新证据（§[2]a） | 产品决策级 |
| `README.md`、`ra2forge/builder.py` docstring、`docs/re/ra2forge_fix_forge1.md` §2 第 2 条 | 「引擎在 **0x46CE10** 按战斗 ID 归并」 | 精确化：`0x46CE10` 是 **[Battles] 列表读取函数**（`push "Battles"` → `call 0x526960` 取条目数 → `0x526CC0` 逐条取 32 字节字符串）；「跨文件按 id 归并」是 [推演]（由 `[Battles]` 段以 id 为键、条目段 `[SOV1]` 用同名 id 推得） | 原措辞把 [推演] 写成了 [实证] 口吻；本卡新增反汇编见 §[2]b | 文档级 |
| `mcp/ra2forge_mcp.py:109`（FORGE-1 §8 第 2 条） | 描述串已含 `BATTLEMD98.INI` | 补注 `(loose, appended)` | 用户/Lead 已登记；本卡授权修 | MCP 使用方文案 |
| `ra2forge/builder.py:33`、`ra2forge/cli.py` 等 | （无） | 顺手：`import zlib` 随 `battle_id_for` 去哈希后成为死引用，已删 | 卫生 | 无 |
| **新增勘误（本卡发现，非任务卡列举）** | `mcp/ra2forge_mcp.py` 输出 `json.dumps(..., ensure_ascii=False)` 写 `sys.stdout`，Windows 下按 ANSI 码页（cp936）编码 | 启动时把 stdio 重配为 UTF-8（`_force_utf8_stdio`） | 实测：对含中文的 `build_campaign` 结果，子进程输出 `0xb8` 起头的 GBK 字节，**标准 MCP 客户端按 UTF-8 解码会失败**（本卡 F2-4 首次跑即因此报 `UnicodeDecodeError` 而失败）；改后同一调用输出合法 UTF-8 | MCP 通道正确性；已在 `out/re_work/forge2/verify_console.txt` 留证 |

其余既有文档/结论未发现需要更正之处；**未改写任何他人文档**（详见 §[5]）。

---

## [4] 未闭环清单

| ID | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 级别 |
|---|---|---|---|---|
| U-FORGE2-1 | 末关 `EndOfGame=yes` 的实际通关行为（是否正常回主菜单、是否影响评分界面） | 需运行期 | 真机：装包后打通 ECH03，观察回主菜单/结算；异常则删该行回退 `no`（`ra2forge/maplib.py:107` 单点开关） | **P1** |
| U-FORGE2-2 | `[Battles] 15=RA2F1` 与官方 1..14 的共存/归并（是否要求连续索引） | 需运行期 INI 合并跟踪 | 真机：官方 `BATTLEMD.INI` + 本 `BATTLEMD98.INI` 同目录，看战役列表是否多出一条；或在 `0x46CE10` 下断看遍历次数 | **P1**（沿用 FORGE-1 U-FORGE1-1） |
| U-FORGE2-3 | 删除散装 `BATTLEMD.INI` 后引擎是否**回退**到 MIX 内的官方同名件 | 回退分支（`0x52CCCD` 的 `push 0x826198`）之后走的是哪个打开例程（是否 MIX 感知的文件类）未逐指令跟完 | 真机：备份+删除散装件后进游戏看官方两条战役是否恢复；或在 `0x826198` 字符串引用处下断看 `CreateFile`/`MixFileClass::Find` 路径 | **P1**（迁移规程的地基） |
| U-FORGE2-4 | MCP UTF-8 修复在真实 MCP 客户端（ZCode Desktop）中的表现 | 需在客户端里注册并调用 | 用桌面客户端连 `mcp/ra2forge_mcp.py`，跑 `build_campaign` 看中文路径是否正常 | P2 |
| U-FORGE2-5 | 新条目在战役 UI 的落位/名称显示（R1 后条目名变短为 `RA2F1`） | 需运行期 | 真机进「新战役」看列表 | P2（沿用 U-FORGE1-4） |

---

## [5] 写作用域合规声明

**改动文件清单**（大小 / 起止时间，均为 2026-09-27）：

| 类别 | 路径 | 字节 | 时间 |
|---|---|---|---|
| 产品代码（R1/R3/R5） | `ra2forge/design.py` | 12940 | 10:03:46 |
| 产品代码 | `ra2forge/builder.py` | 29921 | 10:03:57 |
| 产品代码 | `ra2forge/maplib.py` | 22172 | 10:03:52 |
| 产品代码（版本 0.3） | `ra2forge/install.py` / `ra2forge/__init__.py` | 11821 / 284 | 10:03:57 |
| D1/D2（+UTF-8 修复） | `mcp/ra2forge_mcp.py` | 8119 | 10:07:51 |
| D3 / D4 | `ra2opt/audit.py` / `ra2opt/tests.py` | 26107 / 27877 | 10:04:41 |
| D5 + R1 字段文档 | `docs/DESIGN.md` | 12434 | 10:05:03 |
| 产品 README | `README.md` | 10276 | 10:09:00 |
| FORGE-1 套件（过期断言更新） | `out/re_work/forge1/verify_forge1.py` | 24693 | 10:05:17 |
| 本卡新增 | `out/re_work/forge2/{verify_forge2.py,gen_claims.py,claims_forge2.txt,verify_output.txt,verify_console.txt,verify_anchors_out.txt,audit_bytes_out.txt}` | 28242 / 3861 / 1953 / 8238 / 17803 / 1515 / 3472 | 10:06–10:12 |
| 本卡新增 | `docs/re/ra2forge_fix_forge2.md`（本文件） | 见文件 | 10:12 |
| 产物再生成 | `out/forge2_verify/**`（build 三关 + BATTLEMD98.INI + mix + 报告；id_override / no_description / mcp_build / mcp_nogame_build / _gamedirs），`out/forge1_verify/**`（重跑 FORGE-1 套件按其内建路径重写） | — | 10:06–10:12 |

> 说明：FORGE-1 套件把工作目录硬编码为 `out/forge1_verify`，任务卡要求「重跑该套件」，故其产物被新版代码重写（内容随之更新），已在此登记；未改动该套件以外的其它 out/ 目录。

**未触碰清单**（全部只读，未写入任何字节）：
- `ra2youli/**`（用户游戏目录）—— 证据：`gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`，LastWriteTime `2026-09-25 16:10:48`；`BATTLEMD.INI` 241 B / `ECH01-03.MAP` 14217/13597/15482 B / `expandmd98.mix` 43702 B / `ra2forge_uninstall.txt` 136 B 的 mtime 全为 `2026-09-25 16:44:52`（早于本任务首次写入）；目录内最新 mtime 为 `ra2render.log 2026-09-27 09:31:17`（本任务开工前，属 ra2render 会话）。
- `ra2render/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、其它 `docs/re/*.md`、`out/钢铁残响/**`、`extracted/**`（仅读）、`examples/demo_campaign.json`（仅读，保持无 `campaign.id` 以覆盖默认路径）。
- 未启动游戏、未注入、未改 exe、无伪造实测。

---

## [6] 门禁实跑输出（原文粘贴）

```text
$ python -X utf8 tools\verify_anchors.py
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
```
（完整：`out/re_work/forge2/verify_anchors_out.txt`）

```text
$ python -X utf8 tools\audit_bytes.py out\re_work\forge2\claims_forge2.txt --verbose
0x52cba0   68 a8 61 82 00             68 a8 61 82 00         OK     [.text] push 0x8261A8 -> "BATTLEMD*.INI" (battle list wildcard) | push 0x8261a8
0x52cba9   ff 15 08 12 7e 00          ff 15 08 12 7e 00      OK     [.text] call [0x7E1208] = FindFirstFileA | call dword ptr [0x7e1208]
0x52cccd   68 98 61 82 00             68 98 61 82 00         OK     [.text] fallback push 0x826198 -> "BATTLEMD.INI" | push 0x826198
0x8261a8   42 41 54 54 4c 45 4d 44 2a 2e 49 4e 49 00 42 41 54 54 4c 45 4d 44 2a 2e 49 4e 49 00 OK     [.data] "BATTLEMD*.INI" (loose FS wildcard only)
0x826198   42 41 54 54 4c 45 4d 44 2e 49 4e 49 00 42 41 54 54 4c 45 4d 44 2e 49 4e 49 00 OK     [.data] "BATTLEMD.INI" (fallback name)
0x83e138   45 6e 64 4f 66 47 61 6d 65 00 00 45 6e 64 4f 66 47 61 6d 65 00 00 OK     [.data] [Basic] key "EndOfGame"
0x82bf9c   42 61 73 69 63 00          42 61 73 69 63 00      OK     [.data] [Basic] section name "Basic"
0x68a10e   68 38 e1 83 00             68 38 e1 83 00         OK     [.text] push 0x83E138 "EndOfGame" (read site A) | push 0x83e138
0x68a113   68 9c bf 82 00             68 9c bf 82 00         OK     [.text] push 0x82BF9C "Basic" (section argument of the same call) | push 0x82bf9c
0x68a11a   e8 d1 f4 e9 ff             e8 d1 f4 e9 ff         OK     [.text] call 0x5295F0 - INI read helper (bool) | call 0x5295f0
0x68a11f   88 86 ac 34 00 00          88 86 ac 34 00 00      OK     [.text] mov [esi+0x34AC], al - the EndOfGame flag lands in the scenario object
0x68b143   68 38 e1 83 00             68 38 e1 83 00         OK     [.text] push 0x83E138 "EndOfGame" (read site B, global INI object)
0x83e19c   4e 65 78 74 53 63 65 6e 61 72 69 6f 00 4e 65 78 74 53 63 65 6e 61 72 69 6f 00 OK     [.data] [Basic] key "NextScenario" (the level chain)
0x81b1c8   46 69 6e 61 6c 4d 6f 76 69 65 00 00 43 44 00 00 42 61 74 74 6c 65 73 00 ... OK     [.data] campaign entry keys "FinalMovie"/"CD" + section "Battles"
0x46cd1e   68 c8 b1 81 00             68 c8 b1 81 00         OK     [.text] push 0x81B1C8 "FinalMovie" (campaign entry reader) | push 0x81b1c8
0x46ce10   83 ec 24                   83 ec 24               OK     [.text] sub esp,0x24 - battle-list routine (function start after NOP padding) | sub esp, 0x24
0x46ce1c   e8 3f 9b 0b 00             e8 3f 9b 0b 00         OK     [.text] call 0x526960 with section "Battles" (enumerates the list) | call 0x526960
0x827b04   44 45 53 43 3a 43 75 72 73 6f 72 43 68 65 61 74 00 00 ... OK     [.data] "DESC:" CSF label namespace (official Description style)
合计 18 条：OK=18  MISMATCH/NOREAD=0
```
（完整：`out/re_work/forge2/audit_bytes_out.txt`）

```text
$ python -X utf8 out\re_work\forge2\verify_forge2.py
summary: 72/72 PASS, 0 FAIL
log written: out\re_work\forge2\verify_output.txt

$ python -X utf8 out\re_work\forge1\verify_forge1.py
summary: 58/58 PASS, 0 FAIL
log written: out\re_work\forge1\verify_output.txt

$ python -X utf8 -m ra2opt selftest
  ok    safe: 不动 LAA / DetailLevel
  ok    safe: 只改 PE 头栈字段的 4 个字节
全部通过：36 项
```
（完整实录：`out/re_work/forge2/verify_console.txt`、`out/re_work/forge1/verify_console.txt`）

**FORGE-1 套件的更新（3 处过期断言，另 +4 条 R5 断言）**：

| 原断言 | 为何过期 | 改后 |
|---|---|---|
| `F4-3 battle id is a self-owned RA2F**** id`（正则 `RA2F[0-9A-F]{4}`） | R1 取消了 `RA2F<crc16>`，默认变 `RA2F1`（`RA2F1` 不匹配 4 位十六进制） | 改为「等于设计文件的 `campaign_battle_id`」+「demo（无 `campaign.id`）得到 `RA2F1`」+「不再是名字哈希」 |
| `F4-3 battle entry carries a Description`（只判非空） | R3 要求 Description **来自设计文件**，非空判断不足以证伪旧文案 | 改为「== 设计文件 `campaign.description`」+「不是 `钢铁残响（3关）`」+「不含 `DESC:`」 |
| （无：链只查 NextScenario） | R5 定了末关 `EndOfGame=yes`，链相关字节已变 | 新增 4 条：三图 `EndOfGame` 读回 + 末图原始字节含 `EndOfGame=yes` |
| 其余 51 条 | 不受 R1/R3/R5 影响 | 原样保留 |

---

## [7] 风险与红线

| 红线 | 是否触及 | 说明 |
|---|---|---|
| ① 同步语义 / 命令序 | **否** | 只改本仓 Python 生成器/打包器与文档；未改引擎代码、未注入、未改 exe（MD5 前后一致） |
| ② 随机数消费序 | **否** | 同上；产物只影响战役注册文本与地图内 `[Basic]` 文本 |
| ③ 存档结构 | **否** | 不新增/改动任何存档块（`EndOfGame` 是地图 INI 键，不写存档） |
| ④ 渲染像素等价性 | **否** | 未触及渲染路径 |

**安装路径的破坏面（需要用户决策的部分）**：
1. 本机 `ra2youli\` 仍是**旧版安装**（散装 `BATTLEMD.INI` 241 B 覆盖了官方 `[ALL1]/[SOV1]`，且三图断链、mix 内还塞着旧 INI）——**本任务未改动该目录**，迁移按附录执行（纸面）。
2. 迁移若不删旧 `BATTLEMD.INI` 覆盖件，两个文件会被引擎一起归并：本战役仍能启动（自有 ID `RA2F1` 不撞官方），但官方列表会继续被旧文件改写。
3. `EndOfGame=yes` 是**按官方末关惯例**落的；真机若发现通关异常，删掉末关那一行即可回退（U-FORGE2-1）。

---

## [8] 交付物清单

| 类别 | 路径 | 说明 |
|---|---|---|
| 产品代码 | `ra2forge/design.py`、`ra2forge/builder.py`、`ra2forge/maplib.py`、`ra2forge/install.py`、`ra2forge/__init__.py`（0.3.0） | R1/R3/R5 + 读回自检 |
| 依赖方 | `mcp/ra2forge_mcp.py`（整包安装 + 描述串 + UTF-8 stdio）、`ra2opt/audit.py`、`ra2opt/tests.py` | D1–D4 |
| 文档 | `docs/DESIGN.md`（+2 节及 `campaign.id`/`next` 字段说明，134→159 行）、`README.md`、`docs/re/ra2forge_fix_forge2.md`（本文件，215 行） | D5 + 迁移 |
| 断言 | `out/re_work/forge2/claims_forge2.txt` **18 条**（`gen_claims.py` 生成，逐条字节自检后才写出） | §[6] |
| 验证脚本 | `out/re_work/forge2/verify_forge2.py`（72 条断言）、`out/re_work/forge1/verify_forge1.py`（58 条） | — |
| 日志/证据 | `out/re_work/forge2/verify_console.txt`（17.8 KB 全实录）、`verify_output.txt`、`verify_anchors_out.txt`、`audit_bytes_out.txt`；`out/re_work/forge1/{verify_console.txt,verify_output.txt}` | — |
| 产物 | `out/forge2_verify/build/钢铁残响/{ECH01-03.MAP, BATTLEMD98.INI, expandmd98.mix, BUILD_REPORT.txt, INSTALL.txt, story.md}`；`out/forge2_verify/{id_override,no_description,mcp_build,mcp_nogame_build,_gamedirs}/**` | 可复算 |

---

## [9] 待裁决项

| # | 分叉 | 现状 | 建议 | 需谁决定 |
|---|---|---|---|---|
| 1 | `[Battles]` 索引 15 是否保留 | 仍 15（不占官方 1..14） | 保留；若真机显示要求连续索引，再改「官方最大索引+1」并接受非确定性 | Lead/用户（U-FORGE2-2） |
| 2 | `EndOfGame=yes` 是否维持 | 已落 | 真机通关一次；异常则回退 `no`（单行） | 用户（U-FORGE2-1） |
| 3 | MCP 是否还输出人类可读中文 | 现已 UTF-8（合法 JSON-RPC） | 保持 UTF-8；若某些客户端仍异常，可退到 `ensure_ascii=True`（全 ASCII 转义，零编码风险） | Lead（U-FORGE2-4） |
| 4 | 迁移是否由本仓工具一键完成 | `uninstall --legacy` 对无备份的旧覆盖件只**告警不删**（`--drop-legacy-battlemd` 才改名移开，名字为 `.ra2forge.removed.bak`） | 与 R5 迁移裁决一致；若要求「备份为 `BATTLEMD.INI.ra2forge.bak` 后删除」成为默认行为，需另开小卡（会改动 FORGE-1 场景 D 的断言） | Lead/用户 |
| 5 | 本机 `ra2youli\` 是否执行迁移 | 未动（只读） | 由用户按附录执行 | **用户** |

---

## 附：迁移规程（纸面，**本次未执行**；已按 R1–R5 裁决修正 FORGE-1 §5）

适用：在 FORGE-1 之前装过 ra2forge 包的游戏目录（散装 `BATTLEMD.INI` 被改写、三图 `NextScenario` 断链、`expandmd98.mix` 内还塞着 INI）。

1. **人工保险**：把 `BATTLEMD.INI`、`ECH01-03.MAP`、`expandmd98.mix`、`expandmd98.mix.ra2forge.bak`、`ra2forge_uninstall.txt` 复制到游戏目录外一份存档目录。
2. **清旧安装**：`python -m ra2forge uninstall --game "<游戏目录>" --legacy`
   - 删掉旧版散装地图；旧 mix 有 `.bak` 则还原；删旧清单 `ra2forge_uninstall.txt`。
3. **处理被改写的官方 `BATTLEMD.INI`（本卡修正点 · 已于 2026-09-27 现场执行）**：
   - 该文件已被旧版覆盖（首行 `; Generated by RA2 Campaign Forge (overrides official battlemd.ini)`，241 B，无备份）；
   - 【勘误 2026-09-27 · Lead 实测推翻】**删除散装 `BATTLEMD.INI` 不会回退到 MIX** —— Lead 用 mixlib 扫过游戏目录全部 17 个 MIX（`ra2/ra2md/langmd/language/expandmd01/expandmd98/maps01/maps02/mapsmd03/movies01/movies02/movmd03/multi/multimd/theme/thememd/wdt`），**无任何 MIX 含官方 `BATTLEMD.INI`**（唯一命中的是 ra2forge 自己的 `expandmd98.mix`）。官方该文件原本是**散装件**、被旧版就地覆盖 ⇒ **删除它会让官方战役列表彻底消失**。
   - **正确做法（已实际执行并通过验证）**：① 备份为 `BATTLEMD.INI.ra2forge.bak`；② **把 `extracted/found_battlemd.ini`（2,733 B，官方原文）复制回 `BATTLEMD.INI`**；③ 清旧包；④ 装新版（`BATTLEMD98.INI` 追加 `15=RA2F1`）。实测结果：官方 `1..14` 恢复 + 本战役作为 `15` 追加，互不影响。
   - **禁止**「备份后删除」这条旧指引（它假定 MIX 内有官方同名件，已被实测推翻）；`uninstall --legacy --drop-legacy-battlemd` 仅适用于「打算另想办法补回官方文件」的场景。
4. **装新版**：`python -m ra2forge build --design examples/demo_campaign.json --out out --install "<游戏目录>"`
   - 现在产出散装 `BATTLEMD98.INI`（`[Battles] 15=RA2F1`，只追加）+ 只含地图的 `expandmd98.mix`；安装器逐文件留 `.ra2forge.bak` 并写 `ra2forge_install.json`。
5. **验收**：启动 `gamemd.exe` → 单人游戏 → 战役；官方两条战役按钮/列表**保持原样**，列表里**多一条**本战役（Description 为设计文件里的战役级简介）；第 1 关通关应进第 2 关，第 3 关通关按 `EndOfGame=yes` 结束。
6. **回滚**：`python -m ra2forge uninstall --game "<游戏目录>"` 逐文件还原；第 2/3 步的旧版残留用第 1 步的人工存档目录覆盖回去。
