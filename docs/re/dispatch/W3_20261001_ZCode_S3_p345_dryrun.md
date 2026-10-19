# W3-ZC-S3 · P-3/P-4/P-5 补丁**干跑（dry-run）验证器**（独立会话包 · 不碰 ra2render、不碰真机）

> 本包可在**独立 ZCode 会话**与 Z1/Z2/Z3 并行：它**不写 `ra2render/**`、不写游戏二进制、不启动游戏**，只在**副本**上执行补丁并对拍字节。
> 写作用域唯一：`out/re_work/zcode_live/W3_20261001/prep_p345/**`。**禁止**写 `ra2render/**`、`ra2youli/**`、`ra2bench/**`、`docs/**`、`tools/**`。

## 为什么需要它

代码轨（Z4）真正去打 P-3/P-4/P-5 之前，必须先用一个**可重放的干跑器**证明：
1. 三包补丁在**真实字节**上能装、能读回、能回滚；
2. 窗口长度、守卫条件、rel32 重定位**全部与规格一致**；
3. 不会误伤相邻指令（已知 5 条「落地即错」缺陷 B-1…B-5）。

这样真机/部署步骤才不是"第一次跑就是生产"。

## 输入（只读）

1. `out/re_work/agy/W3_20261001/static_prep_verify/BYTE_TABLE_CORRECTED.md`（**W3-A5 独立复算后的修正字节表**，权威）
2. `out/re_work/agy/W3_20261001/static_prep_verify/DEFECTS_EVALUATION.md`（B-1…B-5 逐字节实证）
3. `out/re_work/qc/W2_20261001/static_prep/{particle,crt,audio}/{BYTE_TABLE.md,DESIGN.md,CLAIMS.txt}`
4. `ra2youli/gamemd.exe`（**只读源**，sha256 `73201cc021497c95…`）

## 任务

写一个 `apply_p345.py`，要求：

1. **沙箱副本**：先把 `ra2youli/gamemd.exe` 复制到 `out/re_work/zcode_live/W3_20261001/prep_p345/sandbox/gamemd.exe`，**一切写操作只针对副本**；脚本启动时断言源文件 sha256 == `73201cc021497c95…`，收尾再断言一次。
2. **安装前守卫（任一不过即拒绝安装并报错退出，不得静默继续）**：
   - 每处**原字节逐字节核对**（P-3 两槽 `C0 CE 62 00` / `80 E2 62 00`；P-4 `0x007C8E17` 原 6B `6A 01 FF 74 24 08`、`0x007C8B3D` 原 9B `FF 74 24 04 E8 A2 08 00 00`；P-5 `0x00750920` 原 6B `51 A0 AC 64 84 00`、`0x007509E0` **原 5B** `A0 AC 64 84 00`）
   - **窗长校验**：P-5.2 窗**必须恰为 5B**；断言 `0x007509E5` 仍是 `53`（`push ebx`）——这是 B-5 的守卫
   - **指令边界校验**：同盟判定入口必须用 `0x004F9A50`；断言 `0x004F9AAE` 处解码为 3 字节 `8B 40 30`（跨住 `0x004F9AB0`）——这是 B-1 的守卫
   - **rel32 重定位校验**：P-4 delete 跳板内 `call` 必须写成 `E8 4A 92 CC FE`（落点 `0x007C93E8`）；**不得**照抄原 9B —— 这是 B-3 的守卫
   - **SBH 闭区间**：若涉及尺寸门，断言实现为 `size <= 1016`（机器码 `ja` @ `0x007C947A`；阈值 `[0x0087C584]=0xF8 03 00 00`）—— B-4 的守卫
   - **cave 区间零重叠**：安装前对全部 cave 区间做两两相交断言
3. **安装**：把补丁字节写入副本对应 FileOffset（`FileOffset = VA − 0x400000`）。
   > 【W3-Lead勘误 E-W3-01】改前：FileOffset = VA − 0x400000；改后：FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)（本镜像 .text/.rdata/.data 为 VA − 0x400000，但 .rsrc/.detour 为 VA − 0x6FC000）；依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
4. **读回对拍**：重新打开副本，逐处读回并与**期望新字节**比对（等于规格即 PASS）。
5. **回滚**：`--rollback` 用备份把副本还原为原字节，并断言副本 sha256 == 源 sha256（**逐字节回到出厂**）。
6. **`--dry-run`**：只做守卫与计划输出，不写盘。

## 交付物

- `out/re_work/zcode_live/W3_20261001/prep_p345/apply_p345.py`
- `verify_p345_dryrun.py`：一条命令跑完 `--dry-run` → 安装 → 读回 → 回滚 → 最终 sha 断言，**EXIT=0**，输出原文贴回报
- `REPORT.md`：守卫清单、每处 VA/FileOffset/原字节/新字节/窗长、读回结果、回滚结果、**"5 条落地即错缺陷各自被哪条守卫拦住"** 对照表
- 回报按 10 节骨架；`[0]` 直接回答：**干跑是否全 PASS；有任一处规格与 A5 修正表不一致吗**

## 纪律

- **禁止**写 `ra2render/**`、`ra2youli/**`、`ra2bench/**`、`D:\Red2/**`、`docs/**`、`tools/**`
- **禁止**启动游戏 / 注入 / 调试；不得改任何真实游戏二进制（只动沙箱副本）
- 收尾贴 `ra2youli/gamemd.exe` 与 `ra2bench/gamemd.exe` 的 sha256（须与开工一致）+ `python tools\verify_anchors.py`（须 323/323 PASS）**原文**
- 若发现 A5 修正表与真实字节冲突，**以真实字节为准**并在 `[3]` 单列勘误（A5 也可能有错）
- 额度纪律：GLM-5.3-Flash 用尽即切 **step-5-preview**，并在 `[META]` 注明切换时点
