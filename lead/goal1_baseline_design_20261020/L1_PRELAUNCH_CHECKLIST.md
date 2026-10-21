# L1 基线趟 · 发射前预检实测值（§7 清单）

**日期**：2026-10-20 13:1x  **性质**：离线预检，未启动游戏。
**变体**：`out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\`（新建，不改共享变体）
**裁决依据**：Notion U1–U9（台账 §300）；方案 `BASELINE_MEASURE_DESIGN.md`。

## A. 离线预检

| # | 检查 | 期望 | 实测值 | 判定 |
|:--|:--|:--|:--|:--|
| A1 | 母本二进制 | `73201cc0…f67476` / 4,825,360 B | `73201cc021497c95…` / 4,825,360 B | ✅ |
| A2 | 图哈希 | `0add791d…60bc` / 311,822 B | `0add791d11aea84d…60bc` / 311,822 B | ✅ |
| A3 | 图内 owner 分布 | `[Units]` 3360（h0/Computer 各 240）/ `[Infantry]` 2240（各 160） | `[Units]`=3360：`<human player>`/`Computer`/`Neutral`/`Special` 及其余 10 户 **各 240**；`[Infantry]`=2240：**各 160** | ✅ |
| A4 | 无 Structures 节 | 27 节，无 `Structures` | **27 节**，无 `Structures`、无 `Aircraft` | ✅ |
| A5 | INI 设置 | `ShortGame=no` / `GameSpeed=2` / `ScenIndex` 存在 | `:25 ShortGame=no`、`:22 GameSpeed=2`、`:20 ScenIndex=166`、`:21 Scenario=[2]0LoadBench_U0400.yrm` | ✅ |
| A6 | 呈现层常量 | `ddraw.ini=95949842…` / `ddraw.dll=85e0f7d5…` / `ra2render.dll=39cbd665…`（在位不加载） | `95949842fe6c0b25` / `85e0f7d530dfda13` / `39cbd66550141610`（+ `ra2render.ini=27c9a60c`） | ✅ |
| A7 | `windowed=false` | 第 1 行 `windowed=false`；第 21 行 `\x01false`（已知缺陷不改） | 第 1 行 `windowed=false` | ✅（缺陷登记 U9） |
| A8 | 残留进程 | 0 行 | 0 | ✅ |
| A9 | 载体目录干净 | 空/无旧 `c_*` | `qc161_u0400_trip/ct` = 0 项 | ✅ |
| A10 | 磁盘余量 | ≥5 GB | D: 410 GB 可用 | ✅ |
| A11 | 锚哈希 | `517889c6…` | `517889c68f037ab6…5ba636` | ✅ |
| A12 | `--carrier-create-files` 字符串已落回执 | 含空格项整体引号、字符串已抄进回执 | ~~**89 件已定（Notion U7 口径）**：84 项附加名 + `RA2MD Update.ico`；默认 5 件齐（gamemd `73201cc0` / ra2loader `e10f60c5` / ra2render.dll `39cbd665` / ra2opt_play.bat `4579a730` / except.txt `6694b75e`）。文件清单冻结于 `_src_L1_sf8_20261020_MANIFEST.json`（89 条，含 size+sha256）~~<br>**勘误 10-21：实为 88 件。** `RA2MD Update.ico` 只在 `ra2youli/` 与 `ra2bench/`，**不在 L1 变体**（`_src_L1_sf8_20261020/` 实际 88 件、`_src_L1_sf8_20261020_MANIFEST.json` 88 条，均实测无该件）；U7 的 89 件前提对 L1 变体不成立。依据：冻结清单（88 条）+ 源目录实测（88 件）+ 三次成功趟 `3146a7b` 均按 88 件执行 | ✅ 已解除（按 88 件） |

### A12 载体串（L1 用，~~**89 件**~~ → **勘误 10-21：88 件**，已定稿）

```
00000409.016,00000409.256,0ne.bat,BATTLEMD.INI,BINKW32.DLL,Blowfish.dll,Blowfish.tlb,Cbnacw32.dll,Conquer.dat,ConquerMD.dat,IsleLand.bat,PATCHW32.DLL,PServer.exe,RA2.ico,RA2MD.INI,RA2MD.ico,Ra2.lcf,Ra2.tlb,Readme.txt,RegSetup.exe,Register.exe,Register.ini,SetupReg.exe,WSOCK32.DLL,Wolapi.dll,Woldata.key,XMP29U2.MAP,XYR.dll,YURI.exe,[2]0LoadBench_U0400.yrm,becdrv.bat,changes.txt,ddraw.dll,ddraw.ini,directplay-win32.reg,directplay-win64.reg,dpwsockx.dll,drvmgt.dll,expandmd01.mix,game.exe,ipxconfig.exe,ipxwrapper.dll,langmd.mix,language.mix,launcher.bmp,launcher.txt,launchermd.bmp,license.txt,maps01.mix,maps02.mix,mapsmd03.mix,movies01.mix,movies02.mix,movmd03.mix,mph.exe,mphmd.exe,mswsock.dll,multi.mix,multimd.mix,notes.ico,patchget.dat,patchgetmd.dat,ra2.csf,ra2.exe,ra2.ini,ra2.mix,ra2md.csf,ra2md.exe,ra2md.lcf,ra2md.mix,ra2render.ini,secdrv.sys,subtitle.txt,subtitlemd.txt,theme.mix,thememd.mix,unins000.dat,wdt.mix,xlh.bat,xwis.dll,xwis0.dll,yuri.lcf,配置器.exe~~,RA2MD Update.ico~~
```

> **★ 勘误 10-21（追加式，不覆盖原文）**：上串末尾的 `,RA2MD Update.ico` 已划去，**不参与发射**。
> 该件只在 `ra2youli/` 与 `ra2bench/`，L1 源变体内不存在 ⇒ 上串实为 **83 项附加名**，
> 加默认 5 件 = **88 件**。三次成功趟（`l1a`/`l1c`/`l3` 等）与冻结清单均按 88 件执行。
> 依据：`_src_L1_sf8_20261020_MANIFEST.json`（88 条）+ 源目录实测 88 件 + 提交 `3146a7b`。

- 该串**不含** `--carrier-create-from` 的默认 5 件（脚本自动加）⇒ 目录 5+83 = **88**。（原写 5+84=89，勘误 10-21）
- `配置器.exe` 为非 ASCII 名；~~`RA2MD Update.ico` 含空格~~ ⇒ 参数整体需引号，且命令行编码须为 UTF-8/系统代码页一致。
  （**勘误 10-21**：`RA2MD Update.ico` 不在 L1 变体内，含空格项已不存在；引号仍保留以防回归。）
- 源在 `_src_L1_sf8_20261020/`（`XMP29U2.MAP` 已换为 sf8 `0add791d`）。

## B. 命令装配（草案，待 A12 定后填 trip-id/out-dir）

| # | 检查 | 值 |
|:--|:--|:--|
| 装1 | `--target-map` | `<变体>\XMP29U2.MAP`（**不是任何 .yrm**）✅ |
| 装2 | `--target-sha256` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` ✅ |
| 装3 | `--trip-id` | `QC161-U0800-L1` |
| 装4 | `--out-dir` | `lead\qc161_u0400_trip\l1_u0800_20261020`（后代）✅ |
| 装5 | 含 `--measure 1 --fullscreen --evid-diff` | 是 |
| 装6 | 不含 `--frozen-dump` | 是 |
| 装7 | `--probe-frames` ≥6 点、均 > 起始帧一半 | `3900,4200,4500,4800,5100,5400,5700,6000` |
| 装8 | 同刻只有一个真机趟 | 是（当前无在飞真机） |

## C. 趟中/趟后核对（照方案 §7-C，按 U3 裁决修正）

C7 依 Notion U3 **降为只记录**（写回 INI 不可信，判不了 GameSpeed 是否读 INI）；真正判别=L2 或读 `[0xA8B558]`（新开项）。V10 口径相应调整。

## 阻塞项

1. ~~A12 件数 88 vs 89~~ → **已解除（勘误 10-21）**：**实为 88 件**。原"按 Notion U7 定 89 件（含 `RA2MD Update.ico`）"不成立——该件不在 L1 变体内。详见 A12 行的追加勘误与串下方注记。
2. **A6 注记**：`ra2render.dll` 在载体中**在位但不加载**（S-4 零命中为硬门），这是 Arm A 的定义，不是缺陷。
3. 其余 A1–A12、装1–装8 全部实测通过 ⇒ **可发射**（仍需用户在场）。
