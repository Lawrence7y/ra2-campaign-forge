# W177-KA · INVENTORY.md

> 源目录 `lead\next_re_20261117_r14\W177-J\`（只读）。时间为文件 mtime，UTC；本地 = UTC+8。可信度：高=原始落盘/可哈希；中=派生日志或脚本产物；低=辅助/目测。

## 1. 文件清单（按 mtime 排序）
| 文件 | 是什么 / 何时写 (UTC) | 可作什么用 | 可信度 |
|---|---|---|---|
| `work\w177_core.py` | 真机 Mem/RPM 封装；01:36:53 | 理解读数机制（不 import） | 中 |
| `work\w177_click.py` | 前台校验点击；01:37:13 | 核对 click 成功语义 | 中 |
| `work\w177_key.py` | 合成键；01:42:39 | MCV 展开路径 | 中 |
| `work\wb_probe.py` | building 枚举/RTTI/player_house；03:55:18 | 核对 limbo/owner 读取 | 中 |
| `work\wc_probe.py` | NAPOWR 类型清单；06:08:12 | 核对下单对象 | 中 |
| `work\dsnap.py` | RTTI 链读取（COL+0xC→TD+8）；09:54:54 | 核对 arg2 类身份方法 | 中 |
| `work\disas_callsites.py` | 0x47C620 调用点反汇编；16:16:11 | 静态调用点来源 | 中 |
| `EVIDENCE\callsite_arg2.txt` | 调用点+prologue 反汇编文本；16:16:16 | arg2=[esp+0x20] 与两处 call 证据 | 中（文本，未独立复算其全部） |
| `work\baseline.py` | 文件哈希/锁记录脚本；16:19:06 | 复算基线 | 中 |
| `work\baseline_before.json` | 开局前 gamemd/ddraw/ini/except 哈希 + LIVE_LOCK；16:19:11 | 完整性/授权核验 | 高 |
| `work\j_main.py` | 真机主脚本（launch→nav→deploy→order→pickup→闭环→高频采样→点击）；16:20:19 | 重建执行轨迹/字段定义 | 中（代码） |
| `work\__pycache__\*.pyc` | 7 个导入缓存；16:21:43–16:21:53 | 证明脚本被 import/运行 | 低 |
| `work\sidebar_locate.py` / `sidebar_locate_regen.py` | 侧栏像素定位两版；16:22:52 / 16:23:48 | 图标中心 2336,472 来源 | 中 |
| `work\regen\sidebar_grid.json` | 重生成网格；16:24:44 | 定位复现（与 EVIDENCE 版不完全同哈希） | 中 |
| `work\game.pid` / `my_pids.txt` | pid 26712 / 启动器 36804+26712；16:25:17 | 会话归属 | 高 |
| `EVIDENCE\j_menu_check.png` | 菜单截图；16:25:38 | 进局前状态（仅目测） | 低（辅助） |
| `EVIDENCE\j_sk_setup.png` | 遭遇战设置；16:25:42 | nav 路径旁证（仅目测） | 低 |
| `EVIDENCE\j_ingame.png` | 展开基地后、下单前；16:25:55 | **无 ghost 配对区域基线** | 低（辅助，非同帧） |
| `EVIDENCE\sidebar_grid.json` | 侧栏网格选定 tile；16:25:55 | icon [2336,472] 来源 | 高 |
| `EVIDENCE\j_ghost_picked.png` | 拿起 ghost 后；16:26:09 | ghost 已拿起旁证（目标区仍绿=0） | 低 |
| `EVIDENCE\j_hover_anchor.png` | 悬停锚点格；16:26:10 | ghost 覆盖目标区，辅助 | 低 |
| `EVIDENCE\j_after_click.png` | 点击后；16:26:11 | 前后同色，不能判拒 | 低 |
| `EVIDENCE\j_flag_samples.jsonl` | 8,885,788 B；24,828 行高频只读采样；16:26:12 | **核心原始证据**：标志序列/帧/格链 | 高 |
| `work\run_checkpoint.json` / `EVIDENCE\j_run.json` | 最终日志，二者哈希逐字节相同；16:26:12 | 阶段判定/落格结论 | 高 |
| `work\baseline_after.json` | 收尾文件哈希/LIVE_LOCK；16:26:24 | 证明游戏文件未变 | 高 |
| `work\branch_recompute.py` | 派生判定脚本；16:27:44 | 与本卡对照（**未 import**） | 中 |
| `EVIDENCE\branch_recompute.txt` | 派生分支判定；16:27:52（最后落盘文件） | 静态选支对照 | 中 |

## 2. 时间序执行轨迹（UTC；本地 +8）
1. 01:36–09:54：复用旧真机工具链（core/click/key/probe/dsnap）落盘，准备阶段。
2. 16:16：静态核 arg2 调用点（callsite_arg2.txt）。
3. 16:19：baseline_before（LIVE_LOCK=W177-J）。
4. 16:20–16:24：写 j_main.py、导入缓存、侧栏定位两版与 regen。
5. 16:25:17：启动 gamemd.exe pid 26712（game.pid）；16:25:38 菜单截图 → 16:25:42 遭遇战设置 → 16:25:55 进局并展开 MCV（j_ingame + sidebar_grid）。
6. 16:26:09：下单后拾取 ghost（j_ghost_picked）；16:26:10 闭环到 hover [113,62]（j_hover_anchor）；16:26:11 点击 target [113,63]（j_after_click）。
7. 16:26:12：写 JSONL + run_checkpoint + j_run（同秒）；采样覆盖 frame 669–719、点击 frame 677。
8. 16:26:24：baseline_after（4 文件哈希与 before 一致）。
9. 16:27:44–16:27:52：写 branch_recompute.py/.txt；**此后无 PROGRESS.md/交付物** ⇒ 中断点在「判定已产出、正式交付未写」之后。无 `j_abort_*`、无 `main_ok=true` 记录，说明主流程跑完而非中途失败退出。
