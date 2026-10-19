---
name: verify-workflow
description: 对"必须实证而非声称"的任务做端到端操作验证时使用：开工前身份核验与修前快照、执行中独立退出码与写入边界自证、收尾零写入证明与逐字转录、负控先行（先证明检查本身能击穿坏样本）、证据分级（[实证]/[推演]/[待实测]）与常见假绿戳穿。配套工具 tools/verify_kit/，派卡模板 docs/re/dispatch/VERIFY_CARD_TEMPLATE.md。
---

# 操作验证工作流（verify-workflow）

把一次"我验证过了"变成**别人可复核、可复跑、可证伪**的证据链。
本技能是**可执行的操作流程 + 工具**；判据清单见
`docs/re/LESSONS_20261003_RE_INSTRUMENTS.md`（42 条仪器/方法论教训，带逐条来源）。
两者分工：**LESSONS 回答"什么算证据/哪里有坑"（判据），本技能回答"按什么顺序
敲哪些命令、产出哪些原始件"（操作）**。写报告时两边都要引：流程按本技能走，
结论强度按 EVIDENCE_STANDARD 与 LESSONS 判。

流程由 VERIFY-KIT01 于 2026-10-03 全程实录验证
（`out/re_work/work_chain/CONTINUE_20261003/lead/verify_kit/VERIFY_KIT_REPORT.md`）：
四工具负控 26/26；全仓修前/修后快照 32,060→32,285 文件，228 处变化 100% 机器归因
（本卡 3 / 钩子状态 3 / 并行会话 222 / 不可归因 0）。下文凡标 `[实证]` 的步骤均
出自该实录；标 `[建议]` 的步骤未实践，照搬前先自己过一遍负控。

## 阶段 0 · 派卡

复制 `docs/re/dispatch/VERIFY_CARD_TEMPLATE.md`，填空后发出。卡面八项必备
（写域、身份指纹、必做步骤、独立退出码口径、负控、证据强度边界、独占要求、
"不得伪造输出"）沿用 `skill/harness-dispatch/SKILL.md` §3.4。

## 阶段 1 · 开工前：身份核验 + 修前快照 + 写域声明

1. **身份核验**：对将要操作/断言的目标文件（脚本、二进制、INI、快照基线）
   先钉"文件名 + 字节数 + sha256"。目标物是会漂移的：现网游戏目录存在并行
   真机局自写 INI、二进制副本消失的先例（PERF-RENDER01 两份快照原件双双
   失踪）⇒ 每次真机动作前**复断言**指纹，不是开工钉一次就完。
2. **修前快照**：对你可能碰到的目录树做 snapshot（含排除口径），这是收尾
   "零写入证明"的 pre 侧。排除口径越宽结论越弱，报告必须附排除清单。
3. **写域声明**：逐条绝对路径列出允许写入的目录；"其他一律只读"写进卡面；
   实例独占（同一真机实例同时只允许一个任务操作）写进卡面。

```bash
# Bash · 身份核验
sha256sum <目标文件...> | tee <原始件目录>/identity.sha256
stat -c '%s bytes  %n' <目标文件...> >> <原始件目录>/identity.sha256
# Bash · 修前快照（tools/verify_kit）
export PYTHONDONTWRITEBYTECODE=1
python -B tools/verify_kit/snapshot.py <目标目录或仓库根> \
  --out <原始件目录>/pre_snapshot.json \
  --exclude ra2youli --exclude ra2bench --exclude .mimosa \
  --exclude __pycache__ --exclude "*.pyc"
```

```powershell
# PowerShell · 身份核验
Get-FileHash -Algorithm SHA256 <目标文件...> | Format-Table -AutoSize
Get-Item <目标文件...> | Select-Object Name, Length, LastWriteTimeUtc |
  Tee-Object -FilePath <原始件目录>\identity.ps.txt
# PowerShell · 修前快照（python 工具跨壳同一命令）
$env:PYTHONDONTWRITEBYTECODE = "1"
python -B tools/verify_kit/snapshot.py <目标目录> --out <原始件目录>\pre_snapshot.json `
  --exclude .mimosa --exclude __pycache__ --exclude *.pyc
```

实例锚点 `[实证]`：verify_kit 自身交付时对全仓做 32,060 文件 / 4.56GB 修前
快照（`lead/verify_kit/cmd/02_pre_repo_snapshot`）；验收台账要求"工具现盘
指纹"先于结论（ACCEPTANCE.md L360–361，转引）。

## 阶段 2 · 执行中：独立退出码 + 边界自证 + 进度留痕

1. **独立退出码**：每一步的退出码由 runner（或 shell）写入独立 `.exitcode`
   文件；**退出码绝不内嵌进输出文件**——反例
   `vrepo/raw/03_validate.txt` 第 2 行 `__EXIT_CODE=0`（同一进程自述，
   ACCEPTANCE.md L36 定性"零个独立 .exitcode 件、跨包不可比"）。
2. **写入边界自证**：新写的脚本/派发的命令清单先过 boundary_scan；
   扫描器必须配正负对照（见阶段 4），否则"0 命中"只是扫描器可能失能。
3. **进度留痕**：原始件按 `NN_名字` 编号进 `<report>/raw/` 或 `cmd/`；
   三件套（输出 / .exitcode / .cmdline）一一对应；失败件**保留**，改名加
   前缀（如 `00_wsl_bash_misresolution__*`）而不是删掉重跑。

```bash
# Bash · 工具口径（推荐）：三件套自动落盘
export PYTHONDONTWRITEBYTECODE=1
python -B tools/verify_kit/run_rc.py --out <原始件目录>/cmd/01_step \
  -- python -B your_tool.py --args
# Bash · 裸壳口径
your_cmd > <原始件目录>/cmd/01_step 2>&1; rc=$?; printf '%d' "$rc" > <原始件目录>/cmd/01_step.exitcode
# Bash · 管道口径：$? 是 tee 的，必须取第一个
your_cmd 2>&1 | tee <原始件目录>/cmd/01_step; rc=${PIPESTATUS[0]}; printf '%d' "$rc" > <原始件目录>/cmd/01_step.exitcode
# Bash · 边界扫描（写完代码先自证）
python -B tools/verify_kit/boundary_scan.py your_script.py --exclude __pycache__
```

```powershell
# PowerShell · 裸壳口径
your_cmd 2>&1 | Tee-Object -FilePath <原始件目录>\cmd\01_step
Set-Content -Path <原始件目录>\cmd\01_step.exitcode -Value $LASTEXITCODE
# PowerShell · 工具口径同一命令；rc 用 $LASTEXITCODE
python -B tools/verify_kit/run_rc.py --out <原始件目录>\cmd\01_step -- python -B your_tool.py --args
"rc=$LASTEXITCODE"
# PowerShell · 派 shell 子命令时钉死 bash 身份（裸名 bash 会命中 WSL bash，本机实证）
python -B tools/verify_kit/run_rc.py --out <原始件目录>\cmd\01_step -- "D:\Git\usr\bin\bash.exe" -c "exit 3"
```

实例锚点 `[实证]`：本技能四工具的全部自测转录即按三件套留痕
（`lead/verify_kit/cmd/`）；裸名 bash 派生被 WSL 截胡、`/d/` 路径失败、
UTF-16 横幅污染输出——失败件保留为
`cmd/00_wsl_bash_misresolution__*` 后改用绝对路径重录。
进度中段自检 `[实证]`：长反汇编必须断言"解码覆盖字节数 == 区间字节数"，
否则单次 disasm 静默截断到 ~11%（SCAN-RECHECK01：155,215 vs 1,392,527）。

## 阶段 3 · 收尾：零写入证明 + 回归对照 + 逐字转录

1. **零写入证明**：修后快照（与 pre **逐字同参**）→ diff → 期望
   `VERDICT: zero-writes`（rc=0）。`MTIME_ONLY` 逐条归因后写进报告
   （读受护 .py 也可能 touch mtime——mtime-only ≠ 写入，但必须说明）。
   快照有 `errors`（不可读文件）时结论降级陈述。
2. **回归对照**：修前修后同一判据、同一口径各跑一遍最小回归
   （先例：V-REPO01 ra2forge 六子命令 + validate + build + manifest 全链），
   两边原始件都在才算"无回归"。
3. **逐字转录**：报告里的命令输出段**程序化生成**（从 raw 件拼装），
   不手抄。数字必须能指回原始件；同一数值两个时点不同（例：M27/M25 台账
   相差 49 秒得出两个"绝对真值"）⇒ 引用现值必须钉时点。

```bash
# Bash · 收尾三连（快照参数与 pre 逐字一致！）
export PYTHONDONTWRITEBYTECODE=1
python -B tools/verify_kit/snapshot.py <同一目标> --out <原始件目录>/post_snapshot.json \
  --exclude ra2youli --exclude ra2bench --exclude .mimosa --exclude __pycache__ --exclude "*.pyc"
python -B tools/verify_kit/diff_snapshot.py <原始件目录>/pre_snapshot.json <原始件目录>/post_snapshot.json
echo "diff_rc=$?"   # 期望 0
```

```powershell
# PowerShell · 同一 python 命令；rc 显式回显
python -B tools/verify_kit/diff_snapshot.py <原始件目录>\pre_snapshot.json <原始件目录>\post_snapshot.json
"diff_rc=$LASTEXITCODE"
```

实例锚点 `[实证]`：verify_kit 交付后全仓 diff 零越界（见报告"授权边界"节）；
`[实证]` pyc 副作用披露：import 式枚举会写 `__pycache__`，必须
`PYTHONDONTWRITEBYTECODE=1` + `python -B` 并在报告披露（EXP001-H）；
`[实证]` 判例：自记 EXIT=0 ≠ 验收方亲跑 = PENDING（W3-SYN 三档判例，转引）。

## 阶段 4 · 负控：先证明检查能击穿坏样本

**顺序铁律：任何"检查通过"的绿灯，先展示同一检查能击穿一个已知坏样本；
击穿不了，绿灯作废。** 三个必做负控（可从 selftest/run_selftest.sh 整体复跑）：

```bash
export PYTHONDONTWRITEBYTECODE=1
# 负控 1 · 快照/差分能检出写入：造 4 种变化各一（增/删/改/仅mtime）
python -B tools/verify_kit/snapshot.py <临时目录>/seed --out <临时目录>/pre.json
echo more >> <临时目录>/seed/a.txt; touch <临时目录>/seed/b.txt
rm <临时目录>/seed/c.txt;            echo new > <临时目录>/seed/d.txt
python -B tools/verify_kit/snapshot.py <临时目录>/seed --out <临时目录>/post.json
python -B tools/verify_kit/diff_snapshot.py <临时目录>/pre.json <临时目录>/post.json
# 期望：rc=1，VERDICT: WRITES-DETECTED，ADDED/REMOVED/CONTENT_CHANGED/MTIME_ONLY 各 1

# 负控 2 · 边界扫描的正负对照：脏样本命中、净样本零命中
python -B tools/verify_kit/boundary_scan.py <临时目录>/dirty_fixture.py    # 期望 rc=1 FINDINGS
python -B tools/verify_kit/boundary_scan.py <临时目录>/clean_fixture.py    # 期望 rc=0 CLEAN

# 负控 3 · 退出码独立性：失败命令的 rc 独立成文件、不在输出里
python -B tools/verify_kit/run_rc.py --out <临时目录>/nc6 -- python -B -c "import sys; sys.exit(3)"
test "$(cat <临时目录>/nc6.exitcode)" = "3" && echo ASSERT-PASS
grep -c "__EXIT_CODE" <临时目录>/nc6 || echo "not embedded: OK"
```

"击穿修前版本"的一般形式：把负控样本换成**你要修的那个 bug 的最小复现件**，
在修复动作之前跑你的新检查/新门禁，必须报红；修完再跑，转绿。两头都留原始件。
修复类卡另加一条：**死接线开关必须负控**——故意触发它（如 `--force`），
观察行为确实改变，才证明开关活着（DLC-STRICT01：CLI install --force 从未
被接线，怎么测都绿）。

实例锚点 `[实证]`：上述负控全部实录于 `lead/verify_kit/cmd/`（NC-1…NC-7）；
`[实证]` 自排除掩码的对照对：掩码开 = CLEAN、`--no-self-exclude` = FINDINGS
（证明掩码不是橡皮图章）。

## 阶段 5 · 证据分级：[实证] / [推演] / [待实测]

- `[实证]`：本卡亲手跑出、原始件在盘、退出码独立采集。三者缺一不可。
- `[推演]`：由 `[实证]` 经逻辑/静态分析得出，未单独复跑；必须写明推理链，
  且**不得升格**为 `[实证]`。引用他会话产物最高只给 `[推演]`（转引标注来源）。
- `[待实测]`：没跑过。**禁止伪装成已验证**；skill/流程里即标"未实践，仅为建议"。
- 判例（转引 W3-SYN）：执行者自记 EXIT=0 ≠ Lead 亲跑 ⇒ 该结论=PENDING。
- 报告"未闭合项"一节必须收拢所有 `[待实测]`，不许散失。

## 阶段 6 · 常见假绿清单（症状 / 为什么假绿 / 怎么戳穿）

| # | 症状 | 为什么假绿 | 怎么戳穿 | 实例锚点 |
|---|---|---|---|---|
| 1 | 输出文件里内嵌 `__EXIT_CODE=0` | 输出与"退出码"同进程自述，可谎报、跨包不可比 | 退出码由 runner/shell 写独立 `.exitcode`，再 `test "$(cat x.exitcode)" = …` 复核 | `vrepo/raw/03_validate.txt:2` + ACCEPTANCE.md L36 `[实证]` |
| 2 | 管道后取 `$?` 当子命令 rc | 拿到的是 tee/管道末端的 rc | Bash 用 `${PIPESTATUS[0]}`；PS 用 `$LASTEXITCODE`；或干脆经 run_rc | 本卡实录中冒烟命令即踩 `[实证]` |
| 3 | 扫描器 0 命中当"干净" | 正则锚定/词表错误可使扫描器恒 0 命中 | 必配阳性对照（植入样本）+ 排除范围声明 | SCAN-RECHECK01 零命中普查（32 维持/3 推翻）`[实证]` |
| 4 | 单次反汇编"全覆盖" | capstone `disasm()` 首个坏字节处静默截断，只覆盖 ~11% | 断言解码覆盖字节数==区间字节数；遇停前进 1 字节重同步 | SCAN-RECHECK01（155,215 vs 1,392,527）`[实证]` |
| 5 | heredoc 落盘的交付件 | >11KB heredoc 静默截断，文件比源短且不报错 | 落盘后 assert 字节数/sha256 与源一致 | SCAN-RECHECK01 `[实证]` |
| 6 | "只读枚举"跑完目录变脏 | import 式枚举落 `__pycache__`，污染零写入证明 | `PYTHONDONTWRITEBYTECODE=1` + `python -B`；跑前后 diff | EXP001-H `[实证]` |
| 7 | 拷贝 rc=0 就当成功 | 对目录占位符拷贝"成功"实为拷进目录（语义错） | 拷后 size/sha 断言；预检目标类型显式失败 | DLC-STRICT01 shutil.copy2 实例 `[实证]` |
| 8 | mtime 变了=有人写了 / 没内容变化=没人动过 | 读受护文件也可能 touch mtime；三值必须分离 | diff 三值（新增/删除/内容变化 vs 仅 mtime）+ 内容哈希为准 + 逐条归因 | ANCHOR-RECHECK01 + 本卡 NC-2b `[实证]` |
| 9 | 目标物拿起来就用 | 现网二进制/INI 会漂移（并行真机局自写 INI、副本消失） | 开工 sha256 钉扎 + 每次真机动作前复断言 + 行级基线 | live-binary-churn / PERF-RENDER01 `[实证]` |
| 10 | 自动评分器给出合理数字 | 评分器可能选错文件，数字来自错误样本 | 评分输入文件身份断言；显式传实选文件名（ScenIndex 会漂移） | ra2bench H1（177/724 误选被吞）`[实证]` |
| 11 | 开关怎么测都绿 | 死接线：开关从未被调用 | 负控：故意触发，观察行为差 | DLC-STRICT01 CLI install --force `[实证]` |
| 12 | 执行者自报 EXIT=0 | 自述≠亲跑；通道静默失败率不可忽略 | 验收方独立复跑；卡面强制开工留痕（`_STARTED.md`） | W3-SYN 判例 + harness-dispatch §5 `[实证]` |
| 13 | diff 红了全算自己头上（或全撇清） | 并发会话同时写盘 | 跑次 bracket + 时间窗归因；diff 后逐条归因写进报告 | W3-S4B / CS1b 先例 `[实证]` |
| 14 | 报告数字与原始件对不上 | 手抄漂移；同一现值两个时点两个"真值" | 转录段程序化生成；数字钉时点 + 指回原始件 | M27/M25 台账 49 秒时点差 `[实证]` |
| 15 | 子 shell 身份想当然 | 裸名 bash 在 Windows PATH 可能命中 WSL bash；路径语义/编码全变 | 绝对路径钉死（`D:\Git\usr\bin\bash.exe`）；原始字节捕获让异类输出自己现形 | 本卡 `cmd/00_wsl_bash_misresolution__*` `[实证]` |
| 16 | 检查工具自身从未被测过 | 工具可能恒绿（掩码失效/词表空/正则死） | 负控 2 + 掩码开/关对照（`--no-self-exclude`） | 本卡 NC-5 `[实证]` |

## 工具速查

| 工具 | 一句话 | 退出码 |
|---|---|---|
| `tools/verify_kit/snapshot.py` | 目录→JSON（relpath/size/mtime_ns/sha256） | 0 成功 / 2 错误 |
| `tools/verify_kit/diff_snapshot.py` | 两快照差分 + zero-writes 结论 | 0 零写入 / 1 有写入 / 2 错误 |
| `tools/verify_kit/boundary_scan.py` | 被禁 API 词元扫描（词表可配、自引用可掩码） | 0 干净 / 1 有命中 / 2 错误 |
| `tools/verify_kit/run_rc.py` | 独立退出码采集（三件套落盘） | 透传子命令 / 124 超时 / 127 无法启动 / 2 用法错误 |
| `tools/verify_kit/selftest/run_selftest.sh` | 负控全套一键自测 | 0 全 PASS / 1 有 FAIL |

统一口径：`PYTHONDONTWRITEBYTECODE=1` + `python -B`；输出三件套
`<NN名>` / `<NN名>.exitcode` / `<NN名>.cmdline`；工具用法细节见
`tools/verify_kit/README.md`。本技能自身的验证实录：
`out/re_work/work_chain/CONTINUE_20261003/lead/verify_kit/VERIFY_KIT_REPORT.md`。
