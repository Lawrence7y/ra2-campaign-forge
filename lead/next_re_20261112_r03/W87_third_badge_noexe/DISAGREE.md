# W87 · DISAGREE（与既有事实 1–8 的交叉核对记录）

> 核对范围：`lead\next_re_20261112_r03\W87_third_badge_noexe\EVIDENCE\` 本次静态反汇编与二进制解析实测结果，对照 W87 任务书列出的「已签发既有事实 1–8」。

## 总结论

**无实质性推翻（NO DISAGREE）**。既有事实 1–8 在核心判断与关键地址上均成立；其中第 3、4、6、8 条在本卡的独立重算/反汇编中获得直接字节级印证，另有 **2 项非冲突性细节补充（Precision Notes）** 需记录在案，因为它们直接影响 R1/R2/R3 的工程评估。

---

## 逐条核对表

| 编号 | 既有事实摘要 | 核对结果 | 本次实测依据 / 补充说明 |
| :--- | :--- | :--- | :--- |
| 1 | `0x52EC00–0x52F3E8` 认得 `0x6EA`/`0x6EB`/`0x6EC`，`0x52F134..189` 推送三槽 id | **一致** `[本次实测]` | `wndproc_52EC00_full.txt`：确认 `0x52F12B..0x52F18F` 对 `0x6EA`/`0x6EC`/`0x6EB` 发送 `0x4D5` 与 `0x4D4`。 |
| 2 | `[0x825C68/6C/70]` → `all1`/`sov1`/`tut1`，经 `0x46CC90` 查表 | **采用前序结论** `[静态读码]` | 本次主要核对窗口过程与控件加载链，未重新展开 `0x46CC90` 内部；与 `0x52F23A/24A/25A` 引用一致。 |
| 3 | `RT_DIALOG 148`（664 B，`cDlgItems=13`，无 `1771`，有 `1770`/`1772`/`1820`/`1959`/`1960`） | **完全一致** `[本次实测]` | `r2_r3_final_check_stdout.txt` L10–28 直接解开 `work\gamemd.exe` `.rsrc` (`foff 0x487270`, 664 B, `trailing=0 B`)：`dlgVer=0x0001 sig=0xFFFF style=0x40000040 cDlgItems=13 rect=(0,0,533,369)`；`1770`@(125,34) 174×87 (`style=0x50000007 ex=0x20`)；`1772`@(125,216) 173×86 (`style=0x50000007 ex=0x20`)；`1820`@(449,29) 61×33 (`style=0x50000007 ex=0x20`)；`1959`@(4,123) 415×13 (`style=0x50000001 ex=0`)；`1960`@(3,304) 420×13 (`style=0x50000001 ex=0`)；无 `1771`。 |
| 4 | 命中走 `ChildWindowFromPointEx` + `GetDlgCtrlID`，不靠坐标常量；两徽章为透明 `WS_EX_TRANSPARENT` STATIC | **一致，附精化** `[本次实测]` | 1. `0x52EC00` 中 `WM_NCHITTEST` (`0x52ED60`)、`WM_LBUTTONDOWN` (`0x52EEFA`)、`WM_LBUTTONUP` (`0x52F1CF`) 及基类辅助 `0x622B50` (`WM_NCHITTEST` `0x622CCB`) 均传 `uFlags=1` (`CWP_SKIPINVISIBLE`) 调用 `ChildWindowFromPointEx` + `GetDlgCtrlID`，无类/风格过滤。<br>2. **补充 A**：`0x52F191..0x52F1C1` (`0x497` 初始化) 向 `0x6EA`/`0x6EC` 发送消息 `0x4D7`，**但跳过了 `0x6EB`**。<br>3. **补充 B**：虽然点击命中无坐标常量，但 `0x60866C` (`0x7A7`=1959) 与 `0x60869E` (`0x7A8`=1960) 对字幕 STATIC 写有布局结构体常量 `(10, 0xC6, 0x262)` / `(10, 0x1F9, 0x262)`。 |
| 5 | 第三徽章像素资源不存在（MIX/`CAMPAIGN.PCX`/`.rsrc` 无第三徽章图） | **采用前序结论** `[静态读码]` | 与本次检查一致；且未发现除 `RT_DIALOG 148` 以外的菜单背景或控件资源。 |
| 6 | 第三槽元数据齐全（`1771`/`tut1`/`BootCampSelect`/`STT:CampaignAnimTutorial`/`DESC:TUT1`） | **一致** `[本次实测]` | 除 `0x6041E5..0x60421C` 返回 `STT:CampaignAnimTutorial` 外，本次在 `0x602F77..0x602F92` 与 `0x603576..0x603591` 也实测见到 `(dlg=0x94, id=0x6EB)` 与 `0x6EA`/`0x6EC` 并列识别。 |
| 7 | `.rsrc` 补丁路线技术可行但破坏 `gamemd.exe` 哈希，与版本守卫冲突 | **一致** `[本次实测]` | 已复核 `W81/version_guard.py` (`L1_FIELDS`) 与 `W38/VERSION_GUARD_CONTRACT.md`，`gamemd.exe` SHA-256 属于 L1 强守卫对象。 |
| 8 | `ddraw.dll` 为第三方 `cnc-ddraw`（SHA-256 `85e0f7d5...`），运行时加载入进程 | **完全一致** `[本次实测]` | `EVIDENCE\file_hashes.txt` 复算 SHA-256 精确吻合；`work\ddraw.dll`（411,648 B）内含 15 处 `cnc-ddraw` 字符串；`gamemd.exe` `.rdata` IAT `0x007E1048` 显式导入 `DDRAW.dll!DirectDrawCreate`（跳板 `0x007C89D4`）。 |
