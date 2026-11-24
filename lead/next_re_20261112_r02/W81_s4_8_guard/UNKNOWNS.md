# W81 UNKNOWNS

1. **check desc 中的历史计数**：`S4_8e` 的断言文本保留 W60/W77 原文 `"(3 changed + 2 added)"`（任务红线：三条 check 文本逐字不动）。恢复全包后实际为 3 changed + 3 added（第 3 条是 `docs/ONE_PACKAGE_AT_A_TIME.md`）。desc 不参与判定；已在 `s4_cases.py:841-844` 注释与本卡 S4_8_GUARD_FIX.md 说明。若 Lead/W60 归属方认为 desc 也应更新计数，那是单行文本改动，不影响判定。
2. **夹具迁移依赖**（沿袭 W77 UNKNOWNS 的提醒）：S3_19/S3_20/S3_22/S4_8 读**卡根**的 `s1_revision\`、`TRACK_B_gates.json`、`baseline_v14\W46_resolve_integration\ra2forge_patched_v14\`。本卡已从 W77 卡只读复制（W77 侧又是从 W60/W46 侧复制的）。未来再迁移该套件的卡仍需一并复制。
3. **`expected_added` 顺序敏感**：判定用列表精确相等（`added == expected_added`，added 经 `sorted()`）。白名单必须保持字典序（`docs/...` < `ra2forge/...`）。本次首跑曾因把 docs 放在列表末尾而 FAIL（判定逻辑如实工作，非缺陷），已修正为字典序。
4. **反向验证的 S4_8.log 覆盖**：反向验证跑 S4_8 会覆盖 `out\S4_8.log`；FAIL/PASS 两版已分别留存为 `out\REVERSE_STRAY_S4_8_FAIL.log` / `out\REVERSE_STRAY_REMOVED_S4_8_PASS.log`，最终全量跑已把 `out\S4_8.log` 重写为干净 PASS 版。
5. **未加"可选增强"第四条 check**：见 DISAGREE.md 第 1 条——S4_8e 恢复全包后 `added == expected_added` 本身就是"包根下除白名单外无其它新文件"的显式白名单断言，再加一条是重复断言且会令断言数偏离 W77 基线 844。
