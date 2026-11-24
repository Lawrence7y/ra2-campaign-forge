# APPLY · 把 ORPHAN-FIX01 应用到正式副本

## 补丁内容
- 唯一改动文件：`ra2forge/install.py`（+418/−67 行，含 docstring 规则段）。
- 补丁文件：`PATCH.diff`（`git diff --no-index <正式 ra2forge/install.py> <补丁 install.py>` 生成）。
- 全量补丁副本（可直接对照/回滚）：`ra2forge/` 子目录。
- 原包基线哈希（应用前自检用）：`ORIG_BASELINE.sha256.txt`。

## 应用步骤（在仓库根执行）
```bash
# 0) 确认正式副本仍是补丁时的基线（可选但推荐）
git -C D:\Project\ra2-campaign-forge status --porcelain ra2forge/
git -C D:\Project\ra2-campaign-forge apply --check lead/next_re_20261112_r02/W21_dlc_orphan/ra2forge_patched/PATCH.diff

# 1) 应用
git -C D:\Project\ra2-campaign-forge apply lead/next_re_20261112_r02/W21_dlc_orphan/ra2forge_patched/PATCH.diff
#   或整文件替换：
#   copy /Y lead\next_re_20261112_r02\W21_dlc_orphan\ra2forge_patched\ra2forge\install.py ra2forge\install.py

# 2) 冒烟（不碰真实游戏目录）
python -m py_compile ra2forge/install.py
python -c "import ra2forge.install as m; print(m.TOOL_VERSION)"   # 应输出 0.5
# 建议把 W21 的沙箱序列作为回归脚本收编（见 ORPHAN_FIX.md §5，输入全在 sandbox/ 下）
```

## 注意事项
1. **PATCH.diff 的路径头**是生成时的绝对路径（`a/D:\Project\...\ra2forge\install.py`），
   `git apply` 需要 `-C1` 容错或改用整文件替换；`--check` 先验证。
2. **版本混用**：v0.5 清单（含 `original_absent`/`removed_orphans` 字段）被未打补丁的
   0.4 代码读取不崩溃（字段被忽略），但 uninstall 会回到旧的"过度还原"行为——升级
   后尽快全量应用补丁，不要长期混用新旧代码操作同一游戏目录。
3. **行为变化点**（对外可见）：
   - 升级时输出新动作行 `removed/restored <name> (orphan: …)`；
   - 升级时旧文件 sha 不匹配（用户改过）→ strict 默认**拒绝升级**（risk），
     需按提示 `uninstall --force` 或手工处理后重跑；
   - 卸载带 `original_absent` 条目时输出 `removed <name>.ra2forge.bak (original absent …)`；
   - 中途失败时错误消息附带回滚报告（每行一个已回滚/未能回滚项）。
4. **不改**：`cli.py`、`builder.py`、legacy 卸载路径、备份槽命名、清单文件名。
