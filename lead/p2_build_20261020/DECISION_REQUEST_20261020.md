# GOAL-3T 决策请求（2026-10-20 08:4x）

GitHub 公开仓：https://github.com/Lawrence7y/ra2-campaign-forge

## 背景

- P2 离线阶段 0–3 已完成：三母本覆盖（`27c9a60c/656e6b4e/10410c98`）、只编译（新 DLL `39cbd665`）、`verify_hooks.py` 已跑、部署包备好但**未部署**。
- 独立核验（GLM 5.3，异族）判定 **CONFIRMED**：六项全 PASS、无阻断。
- `verify_hooks.py` 的 `[5]` v1.6.0 四键检查在 P2 后报红：四键已迁 `[Gameplay]` 且读取改走 `GetGameplayIntEx`；`[1][2][3][4]` 全 OK。核验员判为「预期口径差异，非配对/对称回归」。

## 决策项

### D1 `verify_hooks [5]` 口径

- A. 现在离线更新检查器（识别 `[Gameplay]` / `GetGameplayIntEx`），独立核验后落盘；
- B. 先做 P2 部署+冒烟，之后再更新（**推荐**）；
- C. 保持现状，仅作为已知口径差异记录。

推荐 B 的理由：冒烟是主证据；检查器更新属于工具口径维护，排在冒烟后不阻塞部署，且需要独立核验。

### D2 P2 部署包

是否批准由**主会话在用户在场时**执行 `deploy.cmd` + 冷启冒烟（四玩法键读回为关），失败则 `rollback.cmd`？

推荐：**批准**。包已 CONFIRMED；脚本只写 `GAMEDIR`、不启动游戏；回滚链完整（`deploy.cmd` 先备份现行件，`rollback.cmd` 默认取最新 `backup_*`）。

### D3 排期

是否维持：P2 部署+冒烟 → T55k → #4 批 4 安慰剂 1 趟 → 批 3？

推荐：**维持**。

### D4 源码公开

`blitter_hooks.cpp` / `ra2render.h` 全文件上传被本地安全钩子拦（要求 Write/Edit，241KB 不实际）；已上传 `cpp.diff` / `h.diff`（完整改动面）+ RECEIPT/判定书。是否以 diff + 记录为决策依据即可？还是要求主会话走受控路径上传全文件？

推荐：**diff + 记录足够决策**；全文件非必要。

## 依据件（仓内路径）

- `lead/GOAL_THREE_TARGETS_20261018.md`
- `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`（§276–§280）
- `lead/p2_build_20261020/RECEIPT_BUILD.md`
- `lead/p2_build_20261020/DEPLOY.md`
- `lead/p2_build_20261020/cpp.diff`、`h.diff`
- `lead/p2_build_20261020/verify_hooks.json`
- `lead/goal3_configsplit_20261019/RECEIPT.md`、`QC_P2_VERIFY_R2.md`、`ra2render.ini`
- `tools/verify_hooks.py`

请逐项回复 **D1–D4** 的选择（A/B/C 或 批准/不批准），并给出理由。
