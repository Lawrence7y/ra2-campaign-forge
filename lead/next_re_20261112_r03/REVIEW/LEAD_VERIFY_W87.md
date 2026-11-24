# LEAD_VERIFY_W87 · 第三徽章「不改 exe」判决签发（含我逐字节复核 + 三处引用订正）

> 记录人：Lead｜时间：2026-11-14 12:2x（Asia/Shanghai）｜卡：**W87**｜执行：**`call-agy` / `agy` `gemini-4-hydrogen-high`（effort=high）**
> 运行实况：`conversation_id=7a4bcd26-6671-4465-b06c-0bf4c716c3eb`｜`status=SUCCESS`｜`elapsed=827.6 s`｜handoff `W87_third_badge_noexe\AGY_HANDOFF.md`｜只读卡（未启动游戏、未注入、未附加调试器、未改任何二进制）
> 我的独立复核脚本：`_lead_verify_w87.py`（PE 节表 + 原始字节 + capstone 定点反汇编 + 源码文本核对）

## 1 · 签发：四条路线的判决

| 路线 | W87 判决 | 我是否采信 | 关键依据（我已逐条核过承重项） |
|---|---|---|---|
| **R1 运行时改对话框模板（经 `ddraw.dll` 进程内拦截）** | **A · 保持 `gamemd.exe` 哈希可行** | **采信（技术可行性）**，但**不批准落地**（见 §3） | 创建链三级地址 + IAT 槽全部逐字节吻合（§2） |
| **R2 改用非 `STATIC` 类（`BUTTON`）** | **C · 不可行** | **采信，且这是本轮最有价值的一条** | 四条断链，其中"`STATIC` 靠 `HTTRANSPARENT` 穿透、`BUTTON` 会截胡"由 `WM_COMMAND` 分支实测支持（§2.2） |
| **R3 复用既有控件 `1820`/`1959`/`1960`** | **C · 不可行** | **采信** | 三者都在用（`1820` 与 `1771` 在 `0x602F4F/0x60356F` 并列；`1959/1960` 是 `all1`/`sov1` 字幕槽）；56 处 `SetWindowLongA` 中 **0** 处用 `GWL_ID` |
| **R4 对话框外部化（INI/MIX/散装）** | **C · 不可行** | **采信** | 资源 API 全收敛于 `0x4A3B40`（3 个调用点）；8 个 dialog 创建点无一读外部模板；655,360 B 双编码扫描 0 命中且带正例校验 |

**对唯一问题的回答**：**技术上可行，唯一路径是 R1，且可保持 `gamemd.exe` SHA-256 严格不变** —— 因为 `gamemd.exe` 不自检 `ddraw.dll`，而 `ddraw.dll` 是进程内的第三方件。**但"可见"仍需另行解决**（第三徽章像素美术不存在），并且要接受 `ddraw.dll` 变成本项目要分发的东西。

## 2 · 我亲自复核的部分（这一步是本签发件的核心，不是转述）

### 2.1 对话框创建链 —— 三条字节断言，逐条实测
| 地址 | 实测字节 | 反汇编 | 结论 |
|---|---|---|---|
| `0x0052DF48`（foff `0x12DF48`） | `BA 00 EC 52 00` | `mov edx, 0x52EC00` | ✅ 与 W87 一致（**我第一次写期望串时手误打成 `BO`，是我的错，W87 原文是对的**） |
| `0x0052DF4D`（foff `0x12DF4D`） | `B9 94 00 00 00` | `mov ecx, 0x94`（资源 id **148**） | ✅ |
| `0x006226CB`（foff `0x2226CB`） | `FF 15 50 14 7E 00` | `call dword ptr [0x007E1450]` = `USER32!CreateDialogIndirectParamA` | ✅ |

⇒ **`RT_DIALOG 148` 的创建走 `CreateDialogIndirectParamA`，传入 `lpDialogFunc=0x0052EC00`**。这条成立，W87 的 R1 才有前提。

### 2.2 `WM_COMMAND` 分支只认两个按钮 —— 实测成立
我定点反汇编 `0x0052ECB1` 起：
```
0x0052ECB3  and eax, 0xffff
0x0052ECB8  cmp eax, 0x40e
0x0052ECBD  je  0x52ecf1
0x0052ECBF  cmp eax, 0x686
0x0052ECC4  jne 0x52f3dc      ← 其余全部退出
```
⇒ **`WM_COMMAND` 只处理 `0x40E`(GUI:Load) 与 `0x686`(GUI:Back)，没有任何 `0x6EA/0x6EB/0x6EC` 分支** —— W87 的"断链 3"成立。

`[一处我自己的口径错并已自我纠正]` 我第一次把扫描窗开到 420 B，越过 `0x52F3DC` 后进入了 `0x52EDxx` 的**鼠标命中分支**，于是打出 `cmp ebx,0x6ea`，看起来像"`WM_COMMAND` 也认徽章 id"。**这是我窗口开太宽造成的伪证**。它反而正面印证了 W87 的 R2 论断：**徽章 id 只在鼠标/命中路径被处理，不在 `WM_COMMAND` 路径** —— 两条路径是分开的。

### 2.3 版本守卫是否覆盖 `ddraw.dll` —— 成立，但**比 W87 说的更强**
W87 说「`ra2forge\version_guard.py` 的 `L1_FIELDS` 不含 `ddraw.dll`」。实测：
- **仓库 `ra2forge\` 目录下根本没有 `version_guard.py`**（`Get-ChildItem ra2forge` 只列 `install.py/builder.py/design.py/...`；`grep L1_FIELDS|ddraw` 于该目录 **0 命中**）。
- 该文件只存在于**候选副本**：`W43/.../ra2forge_patched_v13`、`W46/.../v14`、`W60/.../v15`、`W77/.../v16`、`W81/.../v16b`。
- 在 `W81/ra2forge_patched_v16b/ra2forge/version_guard.py`（16,413 B）中实测：
  - `L1_FIELDS = ("c01_full_sha256","c02_text_sha256","c04_size_of_image","c04_number_of_sections","c04_has_detour_section","c04_sections","c08_size","c13_abs_path")` —— **全是 `gamemd.exe` 维度**；
  - 该文件内 **`ddraw` 出现 0 次**（大小写都不出现）。

⇒ **W87 的实质断言成立，而且结论更硬：不是"守卫漏了 ddraw"，而是"仓库发货源码里连守卫都没有"**。这条我单列为 §4 的待登记事项。

### 2.4 三处**引用订正**（W87 原文写错路径/文件名，实质不受影响）
1. `ra2forge\version_guard.py` → **该路径在仓库中不存在**。正确表述应为「候选副本 `ra2forge_patched_v16b\ra2forge\version_guard.py`」；仓库侧无此文件。
2. W87 说「`S1_REASON_CODES` 预留了 `DDRAW_IDENTITY_MISMATCH`」—— 该枚举**不在 `version_guard.py`，而在 `s3_contract.py:138`**（`lead/next_re_20261112_r02/W81_s4_8_guard/ra2forge_patched_v16b/ra2forge/s3_contract.py`）；`W38/VERSION_GUARD_CONTRACT.md:295` 与 `guard_contract_schema.json` 亦登记该码。**枚举确实存在，但 `classify()` 不据此阻断 `ddraw.dll`** —— 实质成立。
3. 我自己的订正：`_lead_imports_dialog.py` 用 capstone **线性扫描**曾得"0 处引用"，是**假阴性**（线性反汇编失步）；字节扫描才得真值。已在前序记录，此处再记一次以免后人复用该脚本的错误结论。

## 3 · 与「独立裁决 Q2」的对接（**这一节决定本卡产物的地位**）
裁决（`RULING_GPT61SOL.md` Q2）明确：**本轮正式产品路线选"丙"（继续借官方战役入口）；甲与乙均不进交付**；并且明确指出**乙（进程内模板拦截/改 `ddraw.dll`）实质上是"项目自己的进程内代码与拦截行为"，现行反注入纪律没有放行它，应按当前不允许执行处理**。

⇒ 因此：
- **W87 的 R1=A 是"技术可行性判决"，不是"批准落地"。** R1 恰好就是裁决里的"乙"。
- 本卡产品价值记为 **知识件 + 代价评估**：它把"未来若要启用，需要哪些前置"钉到了地址级（IAT `0x007E1450`、`0x006226CB`、模板 664 B→696 B 追加第 14 项、`cDlgItems 13→14`）。
- **不得**把本卡结论写成"追加式战役菜单可见已可交付"。产品文案仍只能写"**安装了自定义战役**"。

## 4 · 一条需要项目登记的**新事实**（不是 W87 的错，是我核出来的）
> **B 线的版本守卫不在仓库发货源码里**：`ra2forge/` 下没有 `version_guard.py`，也没有 `s3_contract.py` 的 reason-code 枚举；两者只存在于 `lead/.../ra2forge_patched_v1x` 候选副本。
> 含义：任何"本项目会拒绝未知构建"的说法，**在当前仓库源码层面不成立**，除非安装的是打过补丁的候选树。这条会影响 B 线的对外表述与 C 线的发行口径，需在台账登记并由归属方决定是否合入主干。

## 5 · 边界（不夸大）
- **未做动态验证**：R1 从未实现、从未在真机上试过；"插入第 14 项后 `1771` 会被引擎子类化为 `Static` 并参与命中/初始化"是 `[静态推断]`，不是实测。
- **`0x52F191` 对 `0x6EB` 跳过 `0x4D7`** 的运行时后果 `[未证]`（W87 自己列在 UNKNOWNS #1）——这意味着即使插入控件，点击/高亮也**未必**正常。
- **美术问题未解**：没有第三枚徽章的像素；"可见"仍需要改版 `CAMPAIGN.PCX`（Mod 侧散装/MIX 投放，不改 exe）或自绘。**W87 明确说这不属于逆向问题**。
- 本次只核了 1 个镜像 / 1 个 `ddraw.dll` 版本；`RT_DIALOG 148` 的控件集与坐标换分辨率/语言可能不同。

## 6 · 签发语
`[签发]` W87 的 **R2/R3/R4 = 不可行**采用；**R1 = 保持 `gamemd.exe` 哈希的技术可行路径成立**，但其承重地址经我逐字节复核无误，**同时明确：按 Q2 裁决，R1 本轮不落地、不交付**。
`[签发]` 第三槽的性质再确认：这是**零售版被砍掉的官方 Boot Camp 入口**（元数据齐全），不是我们发明的功能位。
`[订正]` §2.4 三处引用按本文改写；引用本卡时不得再用"`ra2forge\version_guard.py`"这个不存在的路径。
