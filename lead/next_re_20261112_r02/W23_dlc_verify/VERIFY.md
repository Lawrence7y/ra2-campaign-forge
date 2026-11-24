# VERIFY.md · W23 清单/包信任链 + `verify` 漂移检测（SEAL-CHAIN01，TOOL_VERSION 0.7）

本卡基于 W22 `ra2forge_patched_v6`（PKG-IDENT01）继续演进，回答 W21 `UNCOVERED.md` §3
记录的威胁面：**伪造/误改清单可驱动 `uninstall` 删除已知文件**。W22 给清单写入了
`package_id` / `package_digest`，但**没有任何校验链**——`package_digest` 只写不验。

W23 做两件事：① 新增只读 `verify` 命令（漂移检测）；② `install` 额外写一个
**受保护记录**（install seal），`uninstall` / `verify` 校验它。

> **能力边界（先读这个，不得引用时夸大）**
> seal 是**防误操作与意外损坏**的机制，**不是**抗恶意攻击的机制：
> **能改清单的人同样能重算 seal**。它检测的是「安装之后有人/某工具无意改了清单」
> 这类事故；对蓄意篡改（改清单 + 同步改 seal）**无效**。本卡任何输出都
> **不**声称「安全可信」「防篡改」「签名」。

---

## 1. `verify` 命令

```
python -m ra2forge verify --game <GAME_DIR> [--json]
```

只读。**不写、不删任何东西**；`gamemd.exe` 不是必需（可以对归档副本做校验）。

检查项（全部逐项报告，一次跑完）：

| # | 检查 | 说明 |
|---|---|---|
| 1 | 清单结构 | JSON 可解析；`files[]` 每条有纯文件名 + 64 位十六进制 sha256；seal 世代清单（tool ≥ 0.7）必须有字符串 `package_digest` |
| 2 | `package_digest` 自洽性 | 用清单**自己的** `files[].name + files[].sha256`（按名排序、`\n` 连接）重算摘要，与记录值比对。⚠️ **这只能证明清单内部一致，不能证明磁盘上是什么**——磁盘由第 3 项负责 |
| 3 | 磁盘漂移 | 每个 `files[]` 条目在磁盘上的实际 sha256 vs 记录值：`ok` / `changed` / `missing`（读不了记 `unreadable`，按漂移计） |
| 4 | 孤儿 | 磁盘上存在、清单不认识的 ra2forge 特征文件：`*.ra2forge.bak`、`*.ra2forge.removed.bak`、`*.ra2forge-stage*`。清单/ seal 本身不计。**孤儿只列出，不影响退出码** |
| 5 | install seal | seal 世代清单必须存在 seal 且与清单规范化字节匹配；旧清单走降级模式（§4） |

`--json`：同一份报告输出为 JSON 对象（`structural` / `digest` / `seal` / `files[]` /
`orphans` / `counts` / `exit_code` / `exit_code_meaning`），退出码与文本模式完全一致。

### 退出码表（同时写在 `verify --help` 与 `uninstall --help` 里）

| 码 | 含义 |
|---|---|
| **0** | 全部 ok。孤儿只列出**不改变退出码**；目录里没有安装记录也是 0（"nothing to verify"，输出有明确说明行） |
| 1 | 校验本身未能运行（意外错误） |
| 2 | 命令行用法错误（argparse） |
| **5** | 清单结构不可用（非 JSON / 必需字段缺失或畸形） |
| **6** | `package_digest` 不匹配——清单自身记录不自洽（S4 类） |
| **7** | seal 世代清单（tool ≥ 0.7）的 **seal 文件缺失** |
| **8** | seal 存在但 **不匹配 / 损坏 / 是别名（链接）** |
| **9** | 漂移：被记录的文件在磁盘上 **changed 或 missing** |

多类问题并存时，**退出码取最严重的一类**（5 > 6 > 7/8 > 9），但**所有发现都仍然逐项列出**。
例：清单 sha 被改（digest 不匹配 + seal 不匹配 + 磁盘 changed 同时出现）→ exit 6，三类都有输出。

---

## 2. install seal（受保护记录）

### 2.1 写入

`install` 成功写完 `ra2forge_install.json` **之后**，紧接着写
**`ra2forge_install.json.seal`**（同一 game 目录，同一套 staged + alias-proof 原语
`_stage_text_and_replace`）：

```json
{
  "tool": "ra2forge",
  "kind": "install-seal",
  "tool_version": "0.7",
  "package_id": "<清单的 package_id>",
  "package_digest": "<清单的 package_digest>",
  "manifest_sha256": "<64 hex>",
  "sealed_at": "<ISO 时间>"
}
```

**`manifest_sha256` 的定义**：对清单文件字节的 SHA-256，取**规范化字节** = 文件字节按
UTF-8 解码（容忍 BOM）→ `\r\n` 与孤立 `\r` 归一为 `\n` → 重新 UTF-8 编码。
换行归一是刻意的：它是文本编辑器重存能在不动内容的前提下造成的唯一差异（防误操作导向）；
**其他任何内容差异**（改一个字段、删一条目、重排缩进）都会改变哈希。

### 2.2 校验点

| 场景 | 行为 |
|---|---|
| `verify` | seal 状态作为独立检查项报告（`ok / missing / mismatch / corrupt / aliased`），映射退出码 7/8 |
| `uninstall` | **第一条 unlink 之前**整体门禁：seal 世代清单的 seal 缺失 → **拒绝整个 uninstall**（exit 7，报告 `refused="seal_missing"`）；不匹配/损坏/别名 → 拒绝（exit 8）。清单、被记录文件、备份槽**全部原样不动**，输出明确写 `uninstall REFUSED` + 原因 + 恢复路径 |
| `install` | **不做门禁**（见 §6 边界声明 3）；但既有记录的 seal 异常会以 **notice（不阻塞）** 明确披露 |

seal 槽位本身适用与清单相同的五个身份判据（符号链接 / 硬链接 / 非常规文件 / 真实路径
不在 game 目录 / 解析到不同名字）——seal 是链接 → `aliased`，拒绝读取而非跟随。

### 2.3 生命周期

- `uninstall` 完整完成（无拒绝条目）时，seal 与清单**一起删除**（`removed ra2forge_install.json.seal`）；有拒绝条目时两者都保留；
- **只有 seal 本身校验通过**才会随清单删除——旧清单+陈旧 seal 的组合只警告、不动那个 seal；
- install 中途失败回滚：seal 写失败时，**清单回滚到上一版确切字节**（或删除新清单），
  安装从不把「有清单无 seal」的半成品状态留在盘上。

### 2.4 恢复路径（seal 意外丢失/损坏时）

1. 先 `verify` 看漂移报告，确认清单是你要的那份；
2. **重装同一个包**：`python -m ra2forge install --package <同一包> --game <目录>`
   ——重装会重写清单并写入新 seal（内容不变的文件走 `unchanged`）；
   *例外*：如果清单的 `package_id` 是 `unknown`（未盖章包装的），PKG-IDENT01 会要求
   `--adopt-legacy`，即 `install --adopt-legacy`（S5 用例实测）；
3. 再 `uninstall` 即可正常卸载。

**没有提供 `--rebuild-seal` 类命令**（有意为之）：任何「就地重算 seal」的命令都会同时
为篡改者服务；重装路径足够且语义明确。

### 2.5 明确边界（必须原样引用，不得夸大）

1. seal 检测**事故**：误编辑、误删除、工具 bug 造成的清单变化；
2. seal **不**防蓄意攻击：能改清单的攻击者能重算 seal（本机无密钥体系，清单是纯文本）；
3. 不声称「安全可信 / 防篡改 / 签名」；W21 §3 的完整威胁（伪造清单骗过 uninstall）只在
   「攻击者懒得连 seal 一起改」的前提下被缓解——这正是「防误操作 ≠ 抗恶意」的准确表述。

---

## 3. `--force` 与 seal 的关系

- `uninstall --force` 的既有语义**不变**：「删除字节已变的被记录文件」；
- seal 门禁是**另一道门**：seal 缺失/不匹配时 `--force` **不**能越过（实测 S5/S6：两次
  `--force` 均 exit 7/8，快照逐字节不变）；
- `install --force` 本就没有任何效果（W22 PKG-IDENT01 起就如此），v0.7 不改变；
- 文档（两个 `--help`、VERIFY.md、拒绝输出文案）与实现一致：拒绝文案里原话
  `--force does NOT bypass this refusal`。

---

## 4. 旧清单（无 seal）降级策略

`tool version < 0.7`（或 version 缺失/不可解析）= seal 之前世代，**向后兼容优先**：

- `verify`：**警告但完整运行**——结构检查、磁盘漂移检查照做；跳过 digest/seal 检查
  （输出明确写 `DEGRADED` 与 skipped 原因）；**绝不因「旧」而误报全部 ok**——漂移照常
  报 exit 9（S7a 实测：真实 ra2youli 清单副本 → exit 9 + DEGRADED 警告）；
- `uninstall`：警告后照常执行（输出加一行 `legacy manifest (...): no install seal
  expected - proceeding WITHOUT seal protection (degraded mode ...)`）；其余行为与 v0.6
  逐字节一致（C1 实测，归一化该警告行后 v5 参考输出完全一致）；
- 陈旧 seal（旧清单旁边躺着一个 `.seal`）：作为残留物警告，**不删除**（不是本工具写的
  生命周期产物，绝不静默消费）；
- seal 世代清单（tool ≥ 0.7）缺 seal → **不是**降级，是拒绝（exit 7）——降级只属于
  seal 之前的世代。

---

## 5. 回归证据（W23 regress_dlc_v7.py）

- **22 用例 / 全 PASS / 脚本 exit 0**（W22 的 14 用例原判据全保留、指向 v0.7；新增 S1–S8）；
- 关键用例（详见 `out/S*.log`，每条含命令+原始输出+退出码+逐项判据）：
  - **S1** 装后 verify：exit 0，`4 ok / 0 changed / 0 missing`，digest OK，seal OK，`--help` 退出码表在；
  - **S2** 改 Y.MAP 1 字节：exit 9，`CHANGED Y.MAP (recorded …, disk …)`；**digest 仍 OK**——
    演示「digest 只证记录自洽，不证磁盘」；恢复字节后回到 exit 0；
  - **S4** 改清单一条 sha256：exit 6（digest 不匹配），seal 同时 mismatch（清单字节变了），
    磁盘检查把同一文件标 changed——三类并列、取最重；
  - **S5** 删 seal 后 uninstall：exit 7 拒绝、快照逐字节不变、`--force` 仍 exit 7、
    重装同包后卸载恢复；
  - **S6** 篡改/损坏 seal 后 uninstall：exit 8 拒绝并说明原因（mismatch / corrupt 两种形态）；
  - **S7** 真实 v0.3 清单副本 verify：不崩溃、DEGRADED 警告、exit 9（无假 ok）；
    全部匹配的 v0.3 状态 → exit 0 但警告仍在（绝不静默升级语义）；
  - **S8** 手放 `X.MAP.ra2forge.bak` / `*.removed.bak`：列入孤儿，exit 0（文档行为）。

## 6. 与 W21/W22 的衔接 + 本卡自身的边界声明

1. **W21（ORPHAN-FIX01）→ W22（PKG-IDENT01）→ W23（SEAL-CHAIN01）**：W21 修「升级后
   孤儿残留」；W22 给清单/包加身份（`package_id` / `package_digest` / 世代溯源）；
   W23 给**清单本身**加完整性链，并把 W22 只写不验的 `package_digest` 接上校验。
2. **verify 的 digest 检查 ≠ 磁盘证明**：`package_digest` 重算用的就是清单里写的 sha256；
   清单整体伪造且自洽时（攻击者连 digest 一起算好），digest 检查会**通过**——磁盘漂移
   检查（第 3 项）才是对着磁盘的。两者职责不同，输出里分别标注。
3. **install 不做 seal 门禁**（按任务书范围：seal 校验点 = uninstall/verify）。已知残余面：
   既有记录 seal 异常时，install 仍会重写记录并盖新章（有 notice 披露，不阻塞）。
   理由：install 本就**替换**信任锚；install 的孤儿清理另有 per-file sha 判据兜底。
4. **卸载恢复的例外**：未盖章包（package_id `unknown`）的恢复重装需要 `--adopt-legacy`
   （§2.4），这是 PKG-IDENT01 的既有语义，不是本卡新增门。
5. **seal 只在本地单机目录内有效**：复制游戏目录到别处时 seal 随行仍然自洽（哈希绑定的是
   清单内容，不是机器），但它提供的仍是「清单自安装以来未被改过」这一件事，别无其他。
