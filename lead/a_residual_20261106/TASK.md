# TASK · N-1 · 固定 A 残余引用并保存可核验的验收凭据

**派发**：2026-11-06 11:4x，总控会话。**模型**：`magpie/antigravity/gemini-3.8-flash$high`。**max_concurrency=2**。
**上游依据**：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` 的 N-1。
**唯一写域**：`lead/a_residual_20261106/`（新建目录，只写此目录内的新文件）。

---

## 0 背景

D-24 定谳的 A 步（清文档债）已完成，交付 `lead/re_line_20261105/A1_ERRATA_MAP/`，
**总判 PARTIAL**。四组里 W9 与 W7 判 CONFIRMED，W8 与 G5 判 PARTIAL，还有若干残余引用没有固定。

你的任务：**把残余逐条固定成可引用的账**，并留下机器可核的验收凭据。
**你不重做调查，不重新调查那 20 条/12 条** —— A1 已经查过，你只需要把残余钉死。

## 1 要读的（全部只读）

| 文件 | 看什么 |
|:--|:--|
| `lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md`（351 行） | §0 总判与分组表、§2 W9 二十条、§6 W8、§7 残余 mustFix |
| `lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W9.md` | W9-2 / W9-9 / W9-19 三条「部分落实」的具体缺口 |
| `lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W8.md` | W8-6 / W8-11 / W8-8 / W8-7 四条 |
| `lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_G5.md` | G5 五条 + 六项 mustFix |
| `lead/re_line_20261105/A1_ERRATA_MAP/reviews/G5_review.md` | 复核判 PARTIAL 的理由（探针 36/36→34/36 那条） |
| `lead/re_line_20261105/D24_RULING/RULING_D24.md` `:48` `:58` `:60` | A 步的授权与边界 |

## 2 交付物

### 2.1 `A_RESIDUAL_REFERENCES.md`

逐条固定**三类**残余，一条一行，不许合并：

| 类 | 内容 |
|:--|:--|
| **R1 部分落实** | W9-2 / W9-9 / W9-19 —— 每条写：原断言、当前限定表述、出处（文件:行）、档位（CONFIRMED/PARTIAL/UNVERIFIED）、还缺什么 |
| **R2 结构缺口** | W8 `:198` 的「生效声明」只显式点名 6/12 —— 列出被点名的 6 条、漏掉的 6 条，逐条标注「已落到正文哪一行 / 完全无落点 / 仅半承接」 |
| **R3 引用不可定位** | W8-7 被修原文在回件中不可定位（只能挂 `F7_review.md:193`）；W8-8 的 House 标签仅半承接 |

**每条都必须有「引用时怎么写」一栏** —— 即后续文档引用它时该用哪句话、带哪个限定词。
这是本件存在的意义：**让后来者不能把 PARTIAL 当 CONFIRMED 引用**。

### 2.2 `ACCEPTANCE_RECORDS.json`

严格 JSON，一个数组，每项固定字段：

```json
{
  "itemId": "R1-W9-2",
  "itemClass": "R1|R2|R3",
  "originalClaim": "原断言一句话",
  "boundedClaim": "限定后的表述",
  "evidence": "文件:行 或 命令+输出",
  "tier": "CONFIRMED|PARTIAL|UNVERIFIED",
  "unresolved": ["还缺什么"],
  "reviewerRole": "复核员角色名（不是名字，是角色）",
  "inputHashes": {"<被核文件相对路径>": "<64位hex>"},
  "artifactHashes": {"<本目录交付件相对路径>": "<64位hex>"},
  "decision": "ACCEPT|REJECT|PARTIAL",
  "timestamp": "<ISO8601>"
}
```

**约束**：
- `inputHashes` 必须是你**实算**的（`sha256sum` 或 Python hashlib），不许抄；
- `tier` 只能取三值之一，**PARTIAL 不许写成 CONFIRMED**；
- 若某项你判断「证据不足」，`decision` 写 `PARTIAL` 或 `REJECT`，并把缺什么写进 `unresolved`，**不许编造补齐**。

### 2.3 `check_a_residual.py`

确定性门禁，`python -I -X utf8` 跑，检查：
- 两个交付件都存在、JSON 可解析；
- 每条 `itemId` 唯一；`itemClass` 覆盖 R1/R2/R3 三类；
- 每项 12 个字段齐全且非空（`unresolved` 可为空数组但必须存在）；
- `inputHashes` 与 `artifactHashes` 里的每个哈希：**回文件系统实算比对**，不符就 FAIL；
- `A_RESIDUAL_REFERENCES.md` 里每条 R 项都能在 JSON 里找到对应 `itemId`（双向一致）。

退出码 0 = PASS。**exitCode 与完整输出写进交付说明。**

## 3 硬性纪律

1. **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存。
2. **零采样代码**。
3. **只读既有件**：`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、`ra2youli/**`、`out/re_work/**` 一律不得修改。唯一写域 = `lead/a_residual_20261106/`。
4. 不 commit、不 push。
5. `python -I -X utf8`，绝对路径。
6. 引用追到「文件:行」或「实算输出」，拿不到写「未验」。
7. **不许把 A1 的 PARTIAL 说成已完成** —— 你是来固定限定的，不是来升级档位的。

## 4 独立复核（必做）

写完后让一个**新上下文**做复核员：
- 逐条打开 `A_RESIDUAL_REFERENCES.md` 的 `文件:行`，核是否真说了那句话；
- 重跑 `check_a_residual.py`；
- **专项检查**：有没有任何一条把 `PARTIAL` 悄悄抬成 `CONFIRMED`，或把「无落点」写成「已承接」。

复核件 `review/A_RESIDUAL_REVIEW.md`，含被核对象 SHA256 + 字节数 + `checkedEveryRow: true/false`。
