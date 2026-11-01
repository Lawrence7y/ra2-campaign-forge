# XVERIFY_CHANPROBE_20261027 —— X 观测通道探针 `_x_channel_probe_20261027.py` 异族审计判定书

## 0. 身份与方法声明

- 审计代理：ZCode 会话模型 `new-provider-3/qoder-cn:qfmodel`（异族：相对执行者 GLM/qoder 会话；与 v2:751「审阅权在 Codex」不冲突——本书只是异族核验件，不构成审定）。
- 立场：不信执行者自陈，一切以盘面字节 + 亲跑实测为准。被审件与设计件、v2、台账全程只读；本代理唯一写入 = 本判定书 + `_auditprobe_` 前缀临时脚本（§5 副作用登记）。
- 运行纪律：全部亲跑均设 `PYTHONDONTWRITEBYTECODE=1`；用 Python 3.12（`AppData\Local\Programs\Python\Python312`）。
- 方法口径：结构判据一律用**本代理自写最小 PNG 解码器**（只 import zlib/struct，不调用被审件任何函数）；被审件 `png_parse` 仅作「交叉口径」打印，不作判据来源。另设第三口径 Pillow 12.2（`im.load()` 强制全解）与第四口径 gdi.GetPixel 屏幕真值。
- 身份核对（先于一切）：
  - `_x_channel_probe_20261027.py` sha256=`a1cd4dbb51a36857095d570861862087c3c3916ddf615bb42d3f6799da9439e5` ✔ 与委托单钉值全字符合（certutil 实测）。
  - `_drive_c2_x_probe_v2.py` sha256=`65e086e75ba897a4c83bac4fac3ac0c88a983f14dbfd015878ed2b5dea82c3e5` ✔（65e086e7…）。

## A1 零发射证明 —— **CONFIRMED**

**静态（口径一 grep）**：全件 grep `Popen|CreateProcess|WinExec|ShellExecute|startfile|os.system|spawn` 命中 = **零**（仅 :10 文档注释提及「无 popen 游戏路径」）。`subprocess` 唯一实调用点：

```
:433  subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=20)
```

`ctypes.WinDLL` 仅 gdi32/user32（:44-45），**无 kernel32**，无 OpenProcess/TerminateProcess 类句柄原语；`os.` 属性使用 = 零。

**静态（口径二 AST）**：`ast.walk` 全件枚举调用点中含 exec/spawn 语义者仅 4 类：`u32/gdi32` 绘图 API、`RuntimeError`、`spec.loader.exec_module(V)`（:366，导入 v2 模块——v2 模块级只有常量+ctypes 绑定，其 `subprocess.Popen` 仅存在于 `_r_popen:196` 函数体且 `bind_real_ops()` 无模块级调用（grep `^bind_real_ops()`=0），导入不触发任何进程创建）、`subprocess.run(tasklist)`。

**实测（口径三 运行时拦截）**：`_auditprobe_a1_spawnwatch.py` 把 `subprocess.run/Popen/os.system` 全部包上记录器后驱动三模式：

```
--live rc=3 期间进程创建=[]
--selftest rc=0 期间进程创建=[]
--preflight spawn: ('subprocess.run', "['tasklist', '/FO', 'CSV', '/NH']")
   仅 tasklist=True
```

**`--live` 实测 rc=3**（两次独立亲跑一致），打印「永久拒」。残留进程核验见 A5（tasklist 直查空）。
否定式断言第二口径：grep / AST / 运行时钩子三口径同结论。

## A2 判定器与真实工件 schema 对合 —— **FALSIFIED**（子项 A2-b）；rec/timeline 侧 CONFIRMED（子项 A2-a）

### A2-a `_rec / timeline.json / close_delivery / shots 元数据`：**CONFIRMED**

逐项对照 v2 `fire_arm` 实际写盘：

| 探针验的字段 | v2 写盘点 | 对合 |
|---|---|---|
| C1 八必备键 `verdict/close_delivery/gamemd_pid/closed_at_s/close_rows_n/battle_tl_n/except_before/exit_kind` | AST 枚举 fire_arm `rec[...] =`/`rec.update`/`setdefault`/初始字面量：8/8 键在成功路径全部写入（:577, :605, :643/658, :684, :714, :724, :678） | ✔ |
| C2 `verdict∈{OK,PARTIAL}` | :551 `"verdict":"OK"`；:729/733 FAIL；:523-524 PARTIAL 降级 | ✔ |
| C3/C4 `post_ok/post_err/win_pid` | :678-680 `{"post_ok":ok_post,"post_err":err_post,"target_hwnd":hwnd,"win_pid":wpid,"win_tid":wtid,"t":…}` | ✔ |
| timeline 三键 `battle_tl/pre5/close_rows` | :717-719 `json.dumps({"battle_tl":tl,"pre5":pre5,"close_rows":rows})` | ✔ |
| C5 `len(close_rows)==close_rows_n` | :714 `rec["close_rows_n"]=len(rows)`（同写 :717 全量 rows） | ✔ |
| C6 `len(battle_tl)==battle_tl_n ∧ len(pre5)==5` | :643/:658 `battle_tl_n=len(tl)`；:665-668 pre5 恒 5 | ✔ |
| C7 行键 `t/wait/code/exitstate/frame/hwnd/singleton/tick` | :695-701 row 恒含 8 键（+`code_read_ok`）；三态 dict 值不改键名 | ✔ |
| C9 `shots` 段 tag/path/t | :426-434 `screenshot_best_effort` 追加 `{"tag","path","t"}`；tag 名 `battle_end/menu_ready/pre_close/post_close_end` 与探针期望集兼容 | ✔ |
| C10 自然退 ⇒ `final_exitcode` int | :723/:727 | ✔ |

即「探针验的 rec/timeline 字段 v2 就是这么写的」——A2-a 无一漏项。

### A2-b `shots` 像素落盘形态：**FALSIFIED —— v2 真实截图与探针/判据的像素口径根本不对合**

v2 `_capture`（:257-289）生产路径：`GetDIBits` 取 **32bpp**（:277 `biBitCount=32`），随后逐像素写入 **步长 4 的缓冲**：

```
:279  size = w * hh * 4
:283  rgb = bytearray(size)
:284  for i in range(0, size, 4):
:285      rgb[i] = raw[i + 2]; rgb[i + 1] = raw[i + 1]; rgb[i + 2] = raw[i]   # ⇒ RGBX，每像素后跟 1 个 0
:286  H7.write_png_no_filter(Path(out_png), w, hh, bytes(rgb), w * 3)          # ★ 却按 w*3 步长切行
```

`write_png_no_filter`（h7:2680）按 `raw[y*stride : y*stride+w*3]` 取行 ⇒ 每行错位 3/4 像素的**几何剪切**，且其 D-115 段再对**已被 v2 换过一次**的字节**二次 B/R 交换**（h7 自身 capture_frame 的正确口径是 `biBitCount=24, stride=pad4(w*3)`，h7:2490/2491 —— v2 两处都不符）。

实测（`_auditprobe_a2v_capture.py`，同屏先后 v2 路径 vs 探针 `capture_desktop`，第三方 Pillow 与自写解码器双解）：

```
[3] 独立解码 v2  : err=None w=5376 h=1451 chunks=['IHDR(13)','IDAT(4459232)','IEND(0)'] :: IDAT=23403179 期望=23403179 OK filter全0
[3] 独立解码 probe: err=None …同结构…
[4] 探针 png_parse(v2产物) ⇒ 接受（S1 会绿）
[5] 同屏双路径逐像素：不同像素=7064717/7800576 (0.9057)
```

屏幕真值锚（`_auditprobe_a3_groundtruth.py`，gdi.GetPixel，同进程先载 h7 取 DPI-aware）：

```
   ( 100, 100) 屏幕=(236,236,238) probe=(236,236,238)✓ v2=(238,236,236)✗(=R/B互换)
   (1280, 200) 屏幕=(147,147,147) probe=(147,147,147)✓ v2=(248,248,248)✗
   ( 300,1200) 屏幕=(236,236,238) probe=(236,236,238)✓ v2=(238,236,236)✗(=R/B互换)
结论：探针与屏幕真值一致 5/5 有效点 ；v2 产物一致 0/5
```

（两点 GetPixel=CLR_INVALID 落在虚拟框非监视器区，已剔除；同进程背靠背复测 `_auditprobe_a3_swaptest.py`：逐点与探针相同=7.6%、R/B 互换=3.0%、其余 89.4% ⇒ v2 产物既非正确也非单纯反色，系剪切+乱序。）

**后果**：真实发射时 v2 写盘的 shots 是「结构合法、内容已损坏」的 PNG；探针 S1/S2 对它**恒绿**。探针宣称「截图主张在真实工件形态上证过」不成立——它证的是**自己写自己读**的同族环（且其合成 fixture 120×80 走同一 png_write），从未与**发射器写侧**配对验证。判 A2-b **FALSIFIED**。
第二口径：损坏性由 Pillow（接受 ⇒ 非「解码器不兼容」）+ 屏幕真值（v2 全错/探针全对）+ 同屏差分（0.9057）+ 仿真复现（错行 8/8）四路独立钉死。

## A3 PNG 双侧独立性 —— 探针同族环 **CONFIRMED 无 vacuous**；但独立性检验暴露 A2-b 缺陷

`_auditprobe_a3_png.py`（自写解码器，零 import 被审件函数）解 `c2ab_x/_preflight/20261027T125912/desktop.png`：

```
magic OK, file=1577573 bytes
chunks=['IHDR(13)','IDAT(1577516)','IEND(0)']
IHDR=(w=3584,h=967,depth=8,ctype=2,cm=0,fm=0,il=0)
IDAT zlib 解压=10398151 = 967*(1+3584*3) ；967 行 filter 全 0；IEND 存在且 CRC 全过
全像素(非采样)异于首像素占比=0.8942 (3099139/3465728)
[交叉] probe.png_parse=3584x967 与我解码器逐字节一致=True
```

第三口径 Pillow 12.2：完整解码 OK，且**逐像素字节与自写解码器、probe.png_parse 三方全一致**（`_auditprobe_a3_pillow.py`：`Pillow vs my_decode=True`、`Pillow vs probe.png_parse=True`）。⇒ 该桌面帧是真规范 PNG、非同族互庇；S2 的 0.8942（探针采样 0.8927）为真非全黑。
写侧对合旁证：h7 `write_png_no_filter`（按其自身 24bpp+pad4 正确口径喂已知像素图）产物被我的解码器逐像素解回 = **D-115 屏幕色=文件色成立**（41×7 全对），probe.png_parse 亦逐字节一致 ⇒ h7 写侧 ↔ 规范读侧对合成立；探针 png_write 与 h7 png_write 在各自正确口径下产物**逐字节同构**（filter0/8,2/CRC 全同）。
结论：A3 命题「同族互解⇒恒真风险」在探针自身件上不成立（其 png_write/png_parse 两侧均经外部规范口径证实）；但**跨件配对**（v2 写 × 探针读）经同一独立性框架证伪（见 A2-b）。
否定式断言第二口径：magic/长度/CRC/filter 由自写解码器与 Pillow 双引擎复算；「三方像素一致」为交叉非循环（解码器代码独立成文于 `_auditprobe_a3_png.py`）。

## A4 负控真闸复跑 —— **CONFIRMED**（无漏抓；另记 BLIND-SPOT-3 见 A6）

亲跑 `--selftest` **两次**：`RC1=0`、`RC2=0`，两次输出同：

```
selftest: 主判定红=0 负控漏抓=0 缺ID=[] ⇒ ALL-PASS
```

探针自带 7 变异全命中（post_fail→C3、stub_PNG→S1、all_black→S2、truncated_png→S1、tail6_only→C5、bt_dropped→C6、missing_keys→C1）。

自加变异（`_auditprobe_a4_mutations.py`，临时副本 + 直调 `judge_artifacts`，不动被审件）：

```
[OK] M1_winpid  期望 C4=红 实得 red=True        （win_pid=9999≠gamemd_pid=4242）
[OK] M2_delshot 期望 C9=红 实得 red=True        （删 post_close_end 段）
[OK] M3_verdict … C2 红  [OK] M4_posterr … C3 红  [OK] M5_nopre5 … C6 红
[OK] M6_notick  … C7 红  [OK] M7_naturalnoexit … C10 红  [OK] M8_emptyshots … S1 红
```

⇒ 任务指定两新变异（C4、C9）与另 6 项全部被抓，无「新变异不被抓」于 C 系。
非红向补充：M10 `battle_tl=[]∧battle_tl_n=0 ⇒ C6 不红`（登记口径，接受）；M11 三态 dict 行 ⇒ C7 不红（键名在 ⇒ 判据正确宽容）。M9 见 A6。
第二口径：M1–M8 每项打印全 ID 状态表复核「指定 ID 红且非误伤其余」——全表仅目标 ID 翻转。

## A5 preflight 实核复跑 —— 实质五检 **CONFIRMED**；R1 记**环境脆性缺陷**（BLIND-SPOT-2）

亲跑 `--preflight`（本会话 harness 环境，`PYTHONUTF8=1` 被注入）：

```
H1 gamemd 73201cc021497c95 ✔  H1 loader ebddf6a61273c874 ✔  H1 h7 d019e8beecfb5fd8 ✔  H1 probe b063052cd02df28c ✔
H2 c2_dll edb9a0cde129c105… ✔（全 64 位另由独立脚本复算 = edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de）
I1 identity:批准根内⇒True   ok ✔   I2 identity:批准根外⇒False   outside_approved_root:…ra2youli\RA2 ✔
S1 桌面截屏规范可解 3584x967 frac=1.0000 ✔  S2 非全黑 ✔   N1 ini 四模式 g1/e1、g1/e0、g1/default、g0/default 全 ✔
[RED] R1 tasklist  AttributeError("'NoneType' object has no attribute 'splitlines'")   ⇒ rc=1 NOT-READY
```

五母本哈希**第二口径**：绕开探针、自写 hashlib 脚本逐一复算（上行括注）与 `v2:58-62` 钉值**逐字符等**；探针常量（:37-41）与 v2 常量字面同值。
R1 红因诊断：本机 `tasklist /FO CSV` 在代码页 936 下第 11 行含非 UTF-8 字节（`\xd4\xdd\xc8\xb1`，服务名列 GBK）；探针 :433 `text=True` 无 `encoding=`，UTF-8 模式（`sys.flags.utf8_mode=1`，`PYTHONUTF8=1` 注入）下解码线程抛 `UnicodeDecodeError` → `stdout=None` → `None.splitlines()` → R1 记红。
第二口径复跑：`-X utf8=0` + `PYTHONIOENCODING=utf-8` ⇒ **14/14 全绿 rc=0 GO-READY**（记录 `…/_preflight/20261027T164535/`）。⇒ R1 逻辑正确、判据真实，但**实现不抗码页**：就绪闸被环境脆断误拦（fail-safe 方向，非造假）。同会话另证：stdout 走 GBK 时探针 :360 打印 `⇒`(U+21D2) 抛 `UnicodeEncodeError` 崩件（同族脆性）。
残留进程独立核验（不依赖探针）：`tasklist /FI "IMAGENAME eq gamemd.exe"`、`…rc4_loader.exe` 两次实跑均空；CSV 原始字节流 grep `gamemd.exe/rc4_loader.exe` 命中 `[]`。**无任何游戏进程被本审计启动**（禁止面遵守）。
否定式断言（「无残留」）第二口径：探针 R1（绿态）+ 直查 tasklist 过滤器 + 原始字节流检索三路同空。

## A6 已知局限诚实披露 —— **CONFIRMED 诚实**；C5 盲区 **BLIND-SPOT-CONFIRMED**

- 台账 §442（`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:19092-19107`）与设计件均未称探针「完备」：§442 自陈「异族复核到盘前只作**本线候选**（不自我封已核）」；「投递记录完备」是**被证主张的名字**，非对探针覆盖面自封。设计件 :125/:141 的「不构成完备二分」指静态链归因，非本件。唯一过度处 = §442「本件在零发射前提下把这三类主张**钉实**」——A2-b 已证「截图」类只在其自写自读环内成立，未对发射器写侧成立（记 BLIND-SPOT-1 于清单，属主张外推越界，非「完备」宣称）。
- C5 逻辑复核（探针 :210-212）：`ok5 = len(rows)==close_rows_n ∧ (exit_kind 自然退 ∨ len(rows)>=6)`。实测（`_auditprobe_a6_c5blind.py`）：fixture 40 行截尾且计数同步改小 ⇒ keep=5 **红**；**keep=6,7,10,20,39 全部 C5=绿**——不止「恰好 6 行」，**任意 ≥6 的计数同步截尾均不红**（探针自带 tail6_only 用 keep=3 才显得是闸）。另：judge 完全不读 `watch_s/closed_at_s/row.t` 时间轴 ⇒「30 行谎报 30 但窗应产 ~400 行」类截尾亦绿。
- 影响评估：真实 watch 窗 0.1 s 节奏 × 40 s ≈ 400 行 ≫ 6，且 v2 写侧 :717 为全量 `rows`，**作弊动机面（尾 6 再犯）恰是它要防的历史事故形态**；同步谎报需 rec 与 timeline 两处协同造假，而两者同由同一次 `fire_arm` 落笔 ⇒ 现实不可达。判 **BLIND-SPOT-CONFIRMED、可接受**；但「批次发射就绪」结论不受其威胁的**前提**是 C5 闸只防「形态回退」不防「计数造假」——该前提须在台账写明（现 §442 未写 ⇒ 入清单）。

## 总判

**可作发射就绪判据 = 有条件（否，直至两项修复）。**

探针自身工程质量：**通过**——A1 零发射铁证三口径、A4 负控真闸（含指定新变异全抓）、A5 实质检全绿且哈希钉与 v2 字面同值、A3 其 PNG 环经第三方解码器+屏幕真值独立证实、A6 无「完备」自封。

但按「批次发射就绪判据」的职能，探针存在**一个致命对合缺口 + 两个非致命缺陷**：

1. **（致命，须修后复验）A2-b**：探针 S1/S2 从未与**发射器写侧**配对；v2 `_capture:279-286` 以步长 4 写 RGBX 却按步长 3 切行、叠加 h7 D-115 二次 B/R 交换 ⇒ 真实发射的 shots 为结构合法、几何剪切+乱色的废帧，而探针判据**恒绿**。修 v2 之前，「截图非全黑/规范可解」不构成通道有效证据；或探针增 **S3**（预检时把 `OPS["capture_screen"]`=v2 真实现纳入同一判定器，与 `capture_desktop` 同屏对合，容差判像素一致）。本审计已给出 S3 的可跑原型（`_auditprobe_a2v_capture.py` 即现成判据：v2-vs-探针同屏差异 0.9057 ⇒ S3 红）。
2. **（非致命）BLIND-SPOT-2**：R1 `subprocess.run(text=True)` 无编码钉（`encoding="utf-8", errors="replace"` 或 bytes 手剥即可根除）；:360/:262 打印含 U+21D2 在 GBK stdout 下崩件。皆为 fail-safe/可用性缺陷，不造假。
3. **（可接受）BLIND-SPOT-3**：C5 防「形态回退」不防「计数同步造假」（任意 ≥6 截尾均绿；时间轴未交叉）。真实窗行数 ≫6 且 rec/timeline 同源落笔 ⇒ 对就绪结论无实质威胁；须在 §443 登记时如实带注。

批次发射建议：**v2 `_capture` 步长 bug 不修复、S3 不落地前，本探针不得单独签发「通道就绪」**；A1/A4/A5/A6 各项按现件即可复用。

## BLIND-SPOT 清单

| # | 面 | 定性 | 证据 | 对就绪影响 |
|---|---|---|---|---|
| BS-1 | S1/S2×v2 写侧从未配对；v2 `_capture` 出帧结构合法但剪切乱色，判据恒绿 | **致命（发射前必修）** | A2-b/A3：同屏差分 0.9057、gdi 真值 v2 0/5、Pillow 照收 | 高——「通道有效」短窗确认会被废帧骗过 |
| BS-2 | R1/tasklist 不抗码页（UTF-8 模式红/GBK stdout 打印崩） | 缺陷（fail-safe 向） | A5：同件两环境 rc=1 vs rc=0 | 中——就绪闸可能误拦；不造假 |
| BS-3 | C5 仅「≠6」阈：任意 ≥6 计数同步截尾均绿；行时间轴/密度未交叉 | 盲区（可接受） | `_auditprobe_a6_c5blind.py`：keep=6..39 全绿 | 低——真实窗 ≫6 行、rec/timeline 同源落笔 |
| BS-4 | C9 只验 tag 在录，不验 path 文件真实存在（rec 谎报可绕；S1 兜底依赖 rec 自诚实） | 微盲 | 代码 :230-233；S1 解不到文件 ⇒ 红的前提是 path 真 | 低（S1 联动兜底） |
| BS-5 | preflight `probe_sha256_at_run` 恒 null（:444）——自录不封印 | 微瑕 | `_pf.json` 全记录此字段为 null | 低（本审计以 certutil 外部封核替代） |

## 否定式断言 × 第二口径交叉表

| 否定式断言 | 第二（三）口径 | 结果 |
|---|---|---|
| A1「探针无游戏 popen 路径」 | grep / AST 枚举 / 运行时钩子拦截复跑 | 三口径同：唯一 subprocess.run=tasklist |
| A1「导入 v2 不触发进程」 | v2 grep `^bind_real_ops()`=0 + Popen 仅在 `_r_popen` 体内 + spawnwatch 实测 --preflight 全程序列仅 tasklist | 一致 |
| A5「无 gamemd/loader 残留」 | 探针 R1（绿态记录）+ 直查 `tasklist /FI IMAGENAME` + CSV 原始字节流检索 | 三路同空 |
| A3「桌面帧非同族互庇的真帧」 | 自写解码器（零 import 被审件）/ Pillow `im.load()` / probe.png_parse 三方逐字节一致 + gdi 真值采样 | 一致 |
| A2-b「v2 产物内容损坏」（对「就绪」的否定） | 屏幕真值 GetPixel（v2 0/5、探针 5/5）+ 同进程背靠背差分（相同 7.6%/互换 3.0%）+ 仿真复现（错行 8/8）+ Pillow 亦接受（排除「严格度差异」解释） | 四路同判损坏 |
| A6「探针未被声称为完备」 | §442 原文 + 设计件 grep「完备」（仅 :125/:141 静态链语境）+ 探针 docstring 无完备字样 | 一致（唯一过度=「钉实」外推，已入 BS-1 定性） |
| A4「无漏抓」（对 8 自加变异的否定式） | 变异全 ID 状态表打印复核（仅目标 ID 翻转，无误伤） | 一致 |

## 5. 副作用登记（本审计唯一写入）

- 判定书：`lead/qc161_u0400_trip/x_ingame_close_20261026/XVERIFY_CHANPROBE_20261027.md`（本件）。
- 临时审计脚本/件（`_auditprobe_` 前缀，均于 `x_ingame_close_20261026/`）：`_auditprobe_a3_png.py`、`_auditprobe_a4_mutations.py`、`_auditprobe_a2v_capture.py`、`_auditprobe_a3_pillow.py`、`_auditprobe_a3_groundtruth.py`、`_auditprobe_a3_swaptest.py`、`_auditprobe_a3_thirdparty.ps1`（弃用，见下）、`_auditprobe_a1_spawnwatch.py`、`_auditprobe_a6_c5blind.py`。
- 被审件自产的 preflight 目录（跑件所致，非审计改写）：`c2ab_x/_preflight/20261027T162918`（R1 红态记录）、`20261027T164300`（空目录，GBK-stdout 试验：:360 打印 U+21D2 崩于 I1 的 add() 内、截屏步之前，无 _pf.json ⇒ BS-2 实证）、`20261027T164535`（utf8=0 全绿 GO-READY）、`20261027T165423`（spawnwatch 拦截态：R1 因 Popen 钩子被拒而红，属审计 instrumentation 非件缺陷）。临时 PNG/解码件在 `%TEMP%\auditprobe_a3\`。
- 纪律核验：`__pycache__/_x_channel_probe_20261027.cpython-312.pyc` mtime 全程 = `2026-10-27 12:56:10`（执行者原值，本审计未刷新）；被审件/v2/设计件/台账 sha256 与开工值一致（未改）。
- 未部署、未启动任何游戏进程、未点确认、未动存档。System.Drawing（PS5.1）本机缺程序集 ⇒ 第三口径改用 Pillow 12.2 达成，`.ps1` 留档弃用原因在文内。
