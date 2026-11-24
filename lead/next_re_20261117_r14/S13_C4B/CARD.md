# S13-C4B · 只做 **3 条**：补了③语义后，S13 的 C4 行能不能升 `[已证]`

> ⚠️ **本卡任务面被刻意砍到最小**。上一张卡（`S13-C4`，10 条）**零产出**：只有 CARD.md，一个交付文件都没写。
> ⇒ **本卡硬要求：开工 10 分钟内必须先落盘 `PROGRESS.md` 骨架**（含「已开始」「第 1 条候选地址」两行），否则视为失败。

## 唯一任务：3 条，回答一句话问题
从 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_D39\EVIDENCE\classification.tsv` 取 **subsystem=S13 且 class=C4** 的行（应 76 行，自己数），
**只挑 3 条**（挑最有希望的：体内有镜像内串 / 固定全局读写 / `call <已证函数>`）。

对每条尽力补四环，然后回答：
**「补了③语义之后，这 3 条能升 `[已证]` 的各有几条？如果不能，缺的是哪一环？」**

## ④ 只接受（这是本卡的判定核心）
- `direct call`：`E8` 在**指令边界**、`site+5+rel32==entry`、调用者 ≠ 本行体内；
- 或 `exact 虚派发`：接收者是**静态 global**、该 global 的 vptr **由构造器安装（活值）**、`vt[slot]==entry`、site 不被多行共用。

## 🔴 严禁（本项目已因此 FAIL 3 次）
- `atexit` 析构器装的虚表（`push <dtor>; call 0x7C978A`）—— **那不是活 vptr**；
- 「entry 在自己虚表里是第 K 槽」式**槽号匹配**；
- slot-baseline（「某 slot 在已证 owner 里存在」）；
- 用「恰命中 N / P=R=100%」当证据（**那可能是判据自证**，本项目已实证 17 行→3 行）。

## 分档（每行给一个）
- **P1** 四环齐全 ⇒ 可升 `[已证]`
- **P2** ①②③ 齐但 ④ 无解 ⇒ **补语义也没用**（这是本卡最想知道的答案）
- **P3** 连③ 也补不出

## 强制自证
- **⑨ 停机核验**：盘上 S13 **n=240 / named=216 / proved=89**（以盘上为准）。
- **⑲ 自检**：capstone 5.0.7 无 `op.index`（index 在 `op.mem.index`，无 index 返 **0 非 None**）。
- **⑱ 按 entry 地址查全库冲突**（只报不改名）。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_C4B\`
`PROGRESS.md`（≤30 行，**第一行写结论**；10 分钟内先落骨架）/ `C4_CLASSIFY.tsv`（3 行：`entry / ① / ② / ③ / ④ / P档 / 理由`）/ `EVIDENCE\` / `work\`
**不要求 `coverage_delta.tsv`**（本卡是验证卡；若 P1 有行，在 PROGRESS 里列出地址即可，由 Lead 另派合并卡）。
**严禁建 venv / pip install / import 其他卡 work 代码。**

## 交付的一句话（本卡真正的产出）
「**这 3 条里 P1 = ? / P2 = ? / P3 = ?；若 P2 占多数，则 S13 无法靠补语义达标，必须依赖 D-39 裁决。**」