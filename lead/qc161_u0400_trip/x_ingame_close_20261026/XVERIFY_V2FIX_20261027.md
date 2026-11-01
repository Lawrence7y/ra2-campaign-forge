# XVERIFY_V2FIX_20261027 — A2-b 截图缺陷修复轮 · 异族独立判定书

- 判定代理身份：GLM-5.3（异族审计执行线）；被审执行线=qfmodel 执行者。本文一切以盘面字节 + 亲跑实测为准，不信执行者自陈。
- 判定日期：2026-10-27。工作根：`D:\Project\ra2-campaign-forge`。Python=Python312。全程 `PYTHONDONTWRITEBYTECODE=1`。
- 零游戏纪律：全程未启动 gamemd.exe/rc4_loader.exe；仅跑 `--faulttest/--selftest/--preflight` 与 `--live`（后者走替身/硬闸 rc=3）。收尾 tasklist 证无游戏进程残留。
- Scratch（仓库外，TEMP 域）：`C:\Users\Administrator\AppData\Local\zcode_v2fix_audit\`，前缀 `_v2fix_*`（损坏副本 `_v2fix_broken.py`、负控装置 `_v2fix_negctl.py`、普查 `_v2fix_gdi_census.txt`、`shots/`）。未改任何既有仓内文件；无 git 操作。

---

## V1 — 哈希与修复区字节（CONFIRMED）

盘面 sha256 实核（`hashlib` 全文件字节）：

| 件 | 盘面 sha256 | 钉值 | 结果 |
|---|---|---|---|
| `_drive_c2_x_probe_v2.py` (47566 B) | `94881cc2d55d8eb012ff8d5ab447a7c469457c1d9c301f6f75d8a48303b6aafe` | 同 | ✓ |
| `_x_channel_probe_20261027.py` (24238 B) | `597e9359c2148537f098b5bb19aadc98576beb088325df6d87f38754f4935b16` | 同 | ✓ |
| `selfcheck_mutation_v2.py` (6823 B) | `8c74bba6d8ddae6b34a00a8c1a5b0fb81d287617b7ce16f820e4e1a41b766d9d` | 同 | ✓ |
| `X_CONTROL_DESIGN_20261026.md` (24712 B) | `4ebc7143be101d919df4143a7a5a6703f401e31f9bab3d16bad8ddab141f7971` | 同 | ✓ |
| `XVERIFY_CHANPROBE_20261027.md` (20207 B) | `b7e5aa4a4ff17d50d5f06b9c34e0e460ea2708595fba5e4fe98a48f51dae1102` | 同 | ✓ |

v2 `_capture`（`:257-292`）全函数体逐条：

1. **BIH biBitCount==24**：`:277 bih = BIH(40, w, -hh, 1, 24, 0, 0, 0, 0, 0, 0)`（注释「★ 24bpp，同 h7:2489」）。结构 `:270-276` 字段序完整（含 biCompression 第 6 位=0=BI_RGB，负高=-hh 自上而下）。✓
2. **stride==pad4(w*3)**：`:278 stride = ((w * 3 + 3) // 4) * 4`（注释「★ pad4 行距，同 h7:2491」）。✓
3. **缓冲 size==stride*hh**：`:279 buf = _c.create_string_buffer(stride * hh)`。✓（非旧缺陷的 `w*hh*4`）
4. **GetDIBits argtypes 全 wt 类型、无 `_c.UINT` 残留**：`:280-281 gdi32.GetDIBits.argtypes = [wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT, _c.c_void_p, _c.c_void_p, wt.UINT]`。全盘 grep `_c\.UINT` 命中 0（`:271-276` 结构体内的 `_c.c_uint` 是 ctypes 合法成员，非 `wintypes.UINT` 缺失名；执行者自曝曾误用 `_c.UINT`→AttributeError，已改 `wt.UINT`，验无残留）。`restype` 用 `_c.c_int`（ctypes 合法）。✓
5. **write_png_no_filter 交 buf.raw + stride（实参非 w*3）**：`:289 H7.write_png_no_filter(Path(out_png), w, hh, buf.raw, stride)`。✓
6. **无自留 B/R 交换残留**：grep 交换式（`rgb[i]...= `、`[0::3]`、`[2::3]`、`, 2] =` 等）命中 0；`_capture` 内不做任何逐像素反色，全权交写入器一次 D-115 交换。✓
7. **BitBlt/GetDIBits 失败抛 TripFail；ReleaseDC 在 finally**：`:284-287` `if not BitBlt: raise TripFail(...get_last_error())`；`if GetDIBits(...)==0: raise TripFail(...)`；`:290-291 finally: u.ReleaseDC(None, hdc)`；`set_last_error(0)` 于 `:283`。✓

对照 h7 自家口径（`qc151_trip.harness7.py` 亲读：`:2490 bi.biPlanes,bi.biBitCount=1,24` / `:2491 stride=((w*3+3)//4)*4` / `:2492 buf=create_string_buffer(stride*h)` / `:2500 write_png_no_filter(out_png,w,h,buf.raw,stride)`）——v2 `_capture` 与 h7 逐字同构。（细枝：v2 `:277` 行内注释引「h7:2489」实指 biWidth/biHeight 负高行，24bpp 行准确号是 h7:2490；注释引用 1-off，纯 cosmetic，不影响功能，登记备查。）写入器 `:2680` 定义：`raw[y*stride:y*stride+w*3]` 切行丢 padding、`px[0::3],px[2::3]=line[2::3],line[0::3]` 单次 B/R 交换、每行前置 filter byte 0（D-114）、`colortype=2`。⇒ **V1 全 7 子项 CONFIRMED**。

---

## V2 — 套件复跑（CONFIRMED，全 rc 符合预期）

| 命令 | 期望 rc | 实跑 rc | 关键读数 |
|---|---|---|---|
| `_drive_c2_x_probe_v2.py --faulttest` | 0 | **0** | 16 项 `[OK]` 全过，末「== FAULTTEST: ALL PASS ==」（FT1-FT12，含 FT12 截图通道「3 shots」） |
| `selfcheck_mutation_v2.py` | 0 | **0** | 基线 ALL PASS；杀 9 / 存活 0 / 盲区 0（M1-M9 各打红对应 FT），锚点在 v2 新字节上仍有效 |
| `_drive_c2_x_probe_v2.py --live` | 3 | **3** | 先预检（含「残留游戏进程=0」），末「!! live 硬闸：APPROVED_THIS_ROUND=False」 |
| `_drive_c2_x_probe_v2.py --live --approved`（双口径，更强） | 3 | **3** | 同硬闸 rc=3（`APPROVED_THIS_ROUND :754` 永假；`--approved` 参数存在 `:999` 但 `:1014 not (a.approved and APPROVED_THIS_ROUND)` 仍拦；闸在 :1014-1016，prompt 所称「:1011」为近似，实际行号已亲验） |
| `_x_channel_probe_20261027.py --selftest` | 0 | **0** | 12 判定（C1-C10/S1/S2）全 OK + 10 负控变异全 catch；末「主判定红=0 负控漏抓=0 ⇒ ALL-PASS」 |
| `_x_channel_probe_20261027.py --preflight` | 0 | **0** | 15 查全 `[OK]` red=0 GO-READY，含 **S3 diff=0.2552**（<0.5，非黑 frac=0.9300 @5376×1451）；S1/S2 桌面态 @3584×967 |
| `_x_channel_probe_20261027.py --live` | 3 | **3** | 「!! 永久拒：本探针永不启动游戏」 |
| `tasklist`（收尾） | 无游戏进程 | — | grep gamemd/rc4_loader 命中 0（GREP_RC=1） |

新 preflight 落盘记录 `c2ab_x/_preflight/20261027T184826/_pf.json`：`red:0 checks:15`，逐查 OK（已 Read 核对）。⇒ **V2 CONFIRMED**。

---

## V3 — 修复负控（最重要，CONFIRMED：S3 口径双向可证，非装饰）

装置（全自写，判据不 import 被审件 `png_parse`）：
- 把 v2 复制到 TEMP scratch（原钉 `94881cc2` 校验通过后），在**副本**里把 `_capture` 改回旧缺陷形态：`BIH(40,w,-hh,1,32,...)` + `buf=create_string_buffer(w*hh*4)` + 手动 B/R 就地交换 + 末 `H7.write_png_no_filter(out,w,hh,bytes(rgb),w*3)`（stride 传 w*3）。副本 sha256=`ae5a2a54…`（与原 v2 异，仅 scratch）。
- 同进程背靠背双采（先 v2 `capture_screen` 后探针 `capture_desktop`，h7 导入使进程 DPI-aware→物理态）。
- 自写最小 PNG 解码器（zlib+struct；校 magic/块 CRC/IHDR(depth8,colortype2)/IDAT 解压长==h*(1+3w)/逐行 filter==0），逐像素比对。

实测（同法两次原 v2 + 一次损坏副本）：

| 场景 | 尺寸 | 逐像素差分 | 判据 | 结果 |
|---|---|---|---|---|
| 损坏副本（旧缺陷形态） | 5376×1451 | **0.9042** | ≥0.75 ⇒ 抓得住回归 | ✓ 打红 |
| 原版 v2（修复后）run1 | 5376×1451 | **0.2369** | <0.5 ⇒ 对合成立 | ✓ 未打红 |
| 原版 v2（修复后）run2 | 5376×1451 | **0.3052** | <0.5 | ✓ 未打红 |

副本 0.9042 落在旧审计签名带（7064717/7800576=0.90567，盘面 `_recheck_a2v_afterfix.out` 与 `gt_v2/gt_probe` 复算 0.8992/0.9057 皆≈0.90），远高于 0.75 阈；修复后 0.24–0.31 落在桌面动画噪声地板（同法 v2-vs-v2=0.3099、probe-vs-probe=0.3196，见 V6）。⇒ **S3 阈值 <0.5 对「剪切+二次交换」回归确为活判据，修复双向得证。V3 CONFIRMED**。

---

## V4 — 探针 C8/S3/R1 新逻辑独立复验（CONFIRMED）

亲读 `_x_channel_probe_20261027.py`：

- **C8 时间轴单调+衔接+窗跨度**（`:216-232`）：三轴 `close_rows/battle_tl/pre5` 各取 `t` 判 `== sorted`（mono，:222）；`order`（:223-225）校 `max(bt)<=max(pre5)` ∧ `max(pre5)<=min(rows)` ∧ `|（min(rows)-min(pre5))-5.0|<3.0`（5 s pre 窗衔接）；`span_ok`（:226-230）非自然退 ∧ 有 watch_s 时校 `rows[-1]-rows[0] >= watch_s-4.0`（窗跨度）。⇒ 同步截断（计数同改）会破 mono/order/span 之一；`sync_truncation` 变异（keep=10，:348）实证打红（V2 selftest `[OK] N:sync_truncation ⇒ C8 red=True`）。口径与 §443/§3a 所述「时间轴互校封堵 BS-2/6 同步截断盲区」一致。✓
- **S3 v2 写侧×判器同屏背靠背**（`:437-465`）：`V2m.bind_real_ops()` 载 h7（→DPI-aware）后先 `V2m.OPS["capture_screen"](v2shot)`，再 `capture_desktop(pshot)`（先 v2 后探针，顺序正确，:448/450）；**尺寸同态检查** `if (w2,h2)!=(wp,hp): add S3 False`（:454-456，跨态直接判红，杜绝旧「比逻辑帧」假红）；同态才逐像素 `frac=nd/tot`，判据 `ok3 = frac<0.5 and f2>=NONBLACK_MIN`（:461）。⇒ 与 §3a「先 v2 截再探针截、尺寸同态检查、差分阈值<0.5」所述**逐字吻合**。✓
- **R1 tasklist 码页修**（`:484-491`）：`subprocess.run([...], capture_output=True)`→`cp.stdout.decode("utf-8", errors="replace")`（bytes 捕获+replace，中文标题码页差不影响 ASCII 进程名匹配 `ln.lower().startswith('"gamemd.exe')`）。argv 列表免 MSYS 转义坑（:485 注释）。✓
- **执行者自曝两坑闭合**：① `_c.UINT`→`wt.UINT`（探针 `_bind_gdi:150` 与 v2 `:280` 均用 `ctypes.c_uint`/`wt.UINT`，全盘无 `_c.UINT`，V1 第 4 子项已验）；② 跨 DPI 态比较→同态背靠背（S3 `:454` 尺寸同态守卫 + `:438-440` 注释实证「h7 导入设 DPI-aware⇒逻辑 3584×967/物理 5376×1451 两态，对合须同态背靠背」；本 preflight 盘面同帧即见 S1/S2@3584×967、S3@5376×1451 两态）。⇒ **V4 CONFIRMED**。

（附·异族屏幕真值第二口径：本代理自写装置对修复后 v2 PNG 与 live `gdi32.GetPixel` 逐点比色——8 点中 5 点 EXACT（文件 RGB==屏幕 RGB），**0 点 swapped**，3 点 OTHER 全落虚拟屏黑边（screen=ffffff 死区/文件=000000，与审计书「2 点 CLR_INVALID 剔除」同类）。⇒ D-115 单次交换「屏幕色=文件色」由异族 GetPixel 独立证实，无二次反色。）

---

## V5 — 全仓 stride 同类坑普查（CONFIRMED，无第二生产错点）

普查范围=`lead/`+`out/re_work/` 全 527,476 个 .py，命中含 `GetDIBits`/`BitBlt` 者 **89 文件**；`write_png_no_filter(` 调用点（非 def）逐一定位。

**A. 发射器/驱动家族（生产截屏路径，喂 write_png_no_filter 者）**——逐个 24bpp+pad4+`buf.raw`/`stride`，**全对**：
- h4 `:1825/1921`、h5 `:1887/1983`、h6 `:2500/2596`、h7 `:2500/2596`（capture_frame + capture_frame_desktop 两径）— 均 `biBitCount=24` / `stride=((w*3+3)//4)*4` / `buf=create_string_buffer(stride*h)` / `write_png_no_filter(...,buf.raw,stride)`。普查旗标 `24:True pad4:True buf_stride:True`。✓
- out 下 harness 家族（harness3/harness3_u8/carrierfix/fullscreen/failfast/x_patch/eviddiff/qc213p2/qc214_patched + 十余 `.unapproved_*` 快照）同口径，逐个 `24:True pad4:True stride_w3:False buf_stride:True`。✓
- **v2 `_drive_c2_x_probe_v2.py:289`（本轮修复件）**：`24:True pad4:True stride_w3:False buf_stride:True manualswap:False` — 修后正确（与 A 类同口径，且无捕获侧自留交换）。✓
- 普查里 harness 文件 `manualswap:True` 系**误报旗标**：正则命中了 h7 写入器内部那**唯一合法** D-115 交换（`:2707 px[0::3],px[2::3]=...`），而非捕获侧交换；捕获区 `2434-2502` 亲 grep 无交换式（见 V4 附）。⇒ 非缺陷。

**B. 探针 png_write（packed 3 字节自洽）**：`_x_channel_probe_20261027.py` `capture_desktop` 走 32bpp→手动 `rgb[i]=raw[i+2]...` 打包为**紧排** `w*h*3` 缓冲→`png_write`（`seg=rgb[y*w*3:(y+1)*w*3]`，`stride` 概念=w*3 且缓冲本就 w*3）⇒ 自洽正确（其 32→24 打包后行距==w*3==缓冲步长，无剪切）。普查 `32:True png_write:True buf_w4:True`。✓ 与「h7 stride=w*4 却喂 w*3」的缺陷形态**结构不同**，非坑。

**C. 归档/审计/负控件（非生产发射路径，喂 write_png_no_filter stride=w*3 者）— 皆为刻意复现件，非第二错点**：
- `selftest_rebuild.py:116`（`stride=w*3` 重建旧帧做 D113/114/115 对照实验）— 归档 selftest，非截屏驱动。
- `_auditprobe_a3_png.py:170`（`W3*3` 喂 write_png_no_filter，注释「v2:_capture:286 逐字复现」）— 审计书目录内**故意的缺陷仿真件**。
二者是「证明缺陷存在」的负控样本，不是发射产物路径。⇒ 不计为现场错点。

**D. 其它 out 下 32bpp 探针**（qc58/qc61/qc63/qc72/qc79/qc81/qc84-qc99 printwindow/wait/gdi_black 家族）：用 `GetDIBits` 32bpp，写出器为各自内建 packed PNG（`write_png_correct`/`_write_png`）或 PIL，喂给 write_png_no_filter 者 0。qc94_gate `write_png_correct`（`stride=w*4` 读 BGRX→pack 紧排 rgb→`write_png_correct` 用 `stride=w*3` 但缓冲=w*3 紧排）自洽；QC97_probe1（`stride=4` 采样 / `w*3` 为 PIL positive control）为 header A/B 诊断件。均非 v2 那类「stride 错配」缺陷。

**普查结论**：生产截屏路径（h4/h5/h6/h7/v2/探针/harness 家族）口径全对；唯 v2 一处曾错（本轮已修，V1/V3 证实）；喂 write_png_no_filter 的 stride=w*3 两处均为审计/仿真的刻意负控样本，非第二生产现场。⇒ **§3a「无第二现场」CONFIRMED；V5 无 FALSIFIED 级发现**。

---

## V6 — 台账/条目主张对账（CONFIRMED）

**六钉值**逐一盘面 sha256 实测（见 V1 表 + 下）全部一致：
- `94881cc2`（v2）✓ · `597e9359`（探针）✓ · `4ebc7143`（设计件）✓ · `b7e5aa4a`（chanprobe 审计书）✓ · `8c74bba6`（自检件）✓ · `77bb6d6c`（静态审计书 `XVERIFY_X_STATIC_20261026.md` 15418 B，本代理实算=`77bb6d6cab7b056de18b51fa4ca9d2d56bd96268942d500bb5a7d5cb8c7eb8cd`）✓

**§443**（`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:19113-19143`）：
- 「审计书 b7e5aa4a…20207 B」✓ · 「v2 65e086e7…→94881cc2」✓ · 「探针 a1cd4dbb…→597e9359」✓ · 「设计件 b66466b6…→4ebc7143」✓ · 「自检件 8c74bba6 未动」✓ · 「静态审计 77bb6d6c 未动」✓。四路同证读数：同屏差分 0.9057（=7064717/7800576=0.905666，审计书 :77 ✓）、修复后背靠背 0.2541、v2-vs-v2 噪声地板 0.3099、probe-vs-probe 0.3196。

**D-10**（`PENDING_DECISIONS.md:18-27`）：列 v2=94881cc2／自检 8c74bba6／设计终值 4ebc7143／静态审计 77bb6d6c／探针=597e9359，且注「b7e5aa4a A2-b FALSIFIED 抓到 stride 真缺陷⇒按红项纪律修复，FT16/16+变异9/9 复跑、live rc=3 不变」——与 V1/V2 实测**全一致**。✓

**§3a**（`X_CONTROL_DESIGN_20261026.md:226-250`）四数盘面依据核验：
- 「0.2541」：本代理亲跑 preflight 新值 diff=**0.2552**（同态，<0.5），历史盘面 `_pf.json`（record 20261027T173724）字面 `diff=0.2541` ✓ 有盘依据。
- 「0.9057」：审计书 `_recheck_a2v_afterfix` 家族 + 本代理损坏副本负控复算 0.9042、`gt_v2` 复算 0.8992、7064717/7800576=0.905666 ✓ 四点聚≈0.90 有盘依据。
- 「3584×967 / 5376×1451 两态」：本代理**新 preflight 同帧即证**——S1/S2 桌面截屏@3584×967（未载 h7 之逻辑态）、S3 v2 写侧@5376×1451（bind_real_ops 载 h7 后物理态）。✓ 有盘依据且异族复现。
- 「无第二现场」：V5 全仓普查证实生产截屏路径无第二 stride 错点（唯二 stride=w*3 喂 write_png_no_filter 者皆审计/仿真负控件）。✓

---

## 否定式断言第二口径表（凡「无/仅/全」类断言，皆另立独立口径复核）

| 否定式主张 | 第一口径 | 第二（异族）口径 | 判定 |
|---|---|---|---|
| 「修复后无 B/R 二次交换残留」 | 结构代码 grep | 异族 `GetPixel` 逐点比色：5/5 EXACT、0 swapped | 成立 |
| 「全仓仅 v2 一处 stride 坑，无第二现场」 | §3a 散文 | V5 全 527K py / 89 GDI 文件普查 + write_png_no_filter 调用点逐一分类 | 成立 |
| 「live 硬闸永关死」 | 单一 --live | 双口径 `--live` 与 `--live --approved` 皆 rc=3；`APPROVED_THIS_ROUND:754` 永假、闸 :1014 | 成立 |
| 「FT/变异非装饰」 | v2 faulttest 自陈 | 独立 `selfcheck_mutation_v2.py` 杀 9/存活 0/盲区 0 | 成立 |
| 「S3 判据非恒绿」 | v2 自测 0.2541 | 异族损坏副本负控 0.9042 打红 + 原版 0.24/0.31 未红（双向） | 成立 |
| 「六钉值与盘面一致」 | 台账散文 | hashlib 全文件字节重算（含 77bb6d6c 静态书实算匹配） | 成立 |

---

## 总判

**A2-b 截图缺陷修复轮交付包：可交 Codex 审定（D-10=「有条件是」）。**

- V1 修复区字节全 7 子项 CONFIRMED（含 argtypes 无 `_c.UINT` 残留、无二次交换残留、ReleaseDC in finally、GetDIBits/BitBlt 抛 TripFail）。
- V2 套件复跑 CONFIRMED（faulttest 16/16、变异 9/9/0/0、双口径 live rc=3、selftest 12+10、preflight 15/15 GO-READY 含 S3 diff=0.2552、probe live rc=3、tasklist 零残留）。
- V3 负控 CONFIRMED（S3 双向：损坏副本 0.9042≥0.75 打红、原版 0.24/0.31<0.5 未红⇒判据非装饰）。
- V4 探针 C8/S3/R1 新逻辑 CONFIRMED（口径与 §3a/§443 逐字吻合，两坑闭合；异族 GetPixel 5/5 正色佐证）。
- V5 全仓普查 CONFIRMED（无第二生产 stride 错点）。
- V6 台账对账 CONFIRMED（六钉值 + §3a 四数皆有盘面依据，含异族新帧复现）。

**「有条件」而非「无条件」的唯一保留**：以上全部在**零真机发射**（替身 + 硬闸 rc=3）下证得；「截图通道对真实发射产物有效」的最终一里，须在 Codex 依 D-10 裁决批准、翻 `APPROVED_THIS_ROUND` 后跑一趟真实最小批次（本线建议 P0→P0N 短窗先行）才能定谳。本修复轮交付包本身字节自洽、判据活性双向成立、无第二现场，达到「交 Codex 审定」门槛。

---

## 附·审计窗口内并发漂移登记（异族亲验，供 Codex 审定 D-10 时知悉）

执行线（qfmodel）在本判定书撰写期间对两份台账做了**追加式**改动，本代理如实登记并独立核：

- **`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`**：§443（19113–19142）本代理 V6 引文所据字节**未改**（19134–19140 复读与引文逐字一致）；其后**新追加** §444（19144）与 §445（19149）。属追加非改写，V6 判定不受影响。
- **§444 开机会话主张**「LastBootUpTime=10-26 15:14:25」：本代理 `wmic os get LastBootUpTime` 独立读得 `2026年10月26日 15:14:25` ⇒ **盘面独立证实**。据此 D-10 批次建议由「六臂≈16–20 min」收为「五臂 P0→P0N→P1→P2→P3 + P3m 可选末臂≈13–17 min」（§444 已改 PENDING_DECISIONS.md D-10 条目②）。
- **§445 挂账（非本修复轮范围，但属第二处「缺断言」类纪律洞）**：主张 v2 全文无 `carrier_len/CARRIER_PATH_MAX≤130` 断言（旧 `_drive_c2_ab.py:62` 定义 130、`:387` 断言，v2 未继承）。本代理 grep 独立复验：**v2 命中 0**（`130/CARRIER_PATH_MAX/carrier_len` 全无），旧件 `_drive_c2_ab.py:62/387` 确有其闸 ⇒ §445 主张**成立**。实算载体路径长（本代理 `c2ab_x`(58)＋tag＋`/ct/c`+9零）≈94–105、最长文件路径≈124，均 ≤130 ⇒ **无现实阻断**，属「恰好满足而非断言把关」的软洞。执行线已自裁「挂账勿现在动（改件=制造假红）+到盘与红项一并处理+重钉第 N 版」。**本判定书不就此 FALSIFY A2-b 修复轮**（它不涉 `_capture`/stride/探针新逻辑），仅作 D-10 审定的知情项列出。
- **`PENDING_DECISIONS.md`** 亦于 19:14 被改（git diff 显示 195 行波动，含 D-10 段），本代理所核 D-10 六钉值段落当前字节仍与 V6 引文一致。

⇒ 上述并发漂移**不推翻** V1–V6 任一判定；仅提示 Codex：D-10 现况为「五臂+P3m 可选」批次建议，且 v2 尚挂一条「路径长断言缺失」软洞待修复轮后单独重钉。
