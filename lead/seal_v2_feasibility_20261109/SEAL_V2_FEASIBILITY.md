# SEAL V2 FEASIBILITY — seal v2 可行性成件：本机能力清点 / M2·M3 真实代价 / 下一代 seal 最小方案

- 件型：撰写员成件（聚合评估员回件 + 复核员回件 + 本会话自证实跑）
- 日期：2026-11-10；写域：`lead/seal_v2_feasibility_20261109/`（本件是其中唯一新建成件，另增自证脚本 `_svw_fingerprints.py`）
- **结论状态：`unconfirmed`**（复核 verdict = `partial`，按交付规则「refuted 或 partial 标 unconfirmed」触发；见 §6.1）
- 零真机：本任务全程未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
- 只读域（本任务未改一字）：两件台账（`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`）、`lead/ordering_evidence_20261109/`、`lead/cert_realcheck_20261109/`、`lead/seal_chronology_20261109/`、`lead/oracle_spec_20261109/`、`lead/falsifiable_no_relax_20261109/`、`lead/gate_r9sem_20261109/`。
- 证据源三层，逐条注明归属：**[评]** = 评估员回件（26,788 B，`_svv_evaluator_reply.json`，ranCommands=22）；**[复]** = 复核员回件（verdict=partial，ranCommands=18）；**[本]** = 本会话实跑（每条给出命令与输出）。
- 上游旧案不翻案：旧 seal「前提层不成立 / `INTEGRITY_OK_BUT_UNCONFIRMED`」维持不变（`SEAL_CHRONOLOGY.md:348-352` 实读；本件不重开时间案）。

---

## 1 目的与边界

**本件只做三件事**：① 本机签名/时间戳/网络/git 能力清点（三态：存在 / 不存在 / 存在但版本或功能不支持）；② M2（现成身份体系签名）与 M3（RFC3161 TSA + 透明日志）的真实代价逐项判；③ 下一代 seal（seal_v2）最小可行方案设计与落地顺序。

**本件不做（边界，全部为禁令）**：
1. 不生成任何新 seal（写域内唯一 `*seal*.json` 是格式定义 `_sv_seal_v2.schema.json`，非 seal 实例）；
2. 不安装任何工具；
3. 不生成任何密钥（未跑 `--quick-generate-key`、未跑 ssh-keygen 裸命令、未触发证书创建）；
4. 不发任何内容到外网（无 POST、无请求体、无 TS query、未发送任何仓库内容或派生摘要）；
5. 不 commit、不 push（本会话 `git rev-parse HEAD` = `26574589aa8401e8f3f2934680a1ea7109bafa2d`，与任务开始时一致 [本]）。

**纪律**：Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 hashlib 实算；引用必须追到「实跑命令+输出」或「文件:行」；拿不到写「未验」。**★ 本机缺某工具 ≠ 该方案不可行**——凡写「缺」必附「装什么/做什么、多久、谁批准」（§2.6）。

---

## 2 ★ 本机能力清点

### 2.1 which 三态表（逐项给依据）

| 工具 | 三态 | 版本 / 路径 | 依据 |
|---|---|---|---|
| git | **存在** | 2.54.0.windows.1，`D:\Git\cmd\git.EXE` | 编排方基线 `git_version.out`；[评] `git commit -h` 列出 `-S, --[no-]gpg-sign[=<key-id>]`，`git help -c` 列 `user.signingKey`/`gpg.program`/`gpg.format`/`commit.gpgSign`/`gpg.ssh.allowedSignersFile` |
| gpg | **存在**（编排方 which 报 null 是 PATH 差异） | GnuPG 2.4.9，`D:\Git\usr\bin\gpg.exe`（Git Bash `/usr/bin/gpg`） | [评] PowerShell `Get-Command gpg` 实跑 PRESENT；`--dump-options` 含 `--detach-sign`/`--local-user`/`--batch`/`--quick-generate-key`/`--pinentry-mode`/`--passphrase`/`--faked-system-time`；Pubkey 含 EDDSA/ECDSA/RSA。[复] 独立确认同路径与旗标 |
| openssl | **存在×2，但双拷贝不齐**（★ 收窄②，见 §6.1） | Git /mingw64 3.5.6 与 `D:\Anaconda\Library\bin` 3.0.18 | [评] 两套均含 `ts`/`cms`/`dgst`。[复] 收窄：`cms -no_signing_time` **仅 mingw 3.5.6 有**、Anaconda 3.0.18 无；Anaconda 副本 `ts -query` 在裸 Git Bash 实跑 rc=1（`Can't open C:\Program Files\Common Files\ssl/openssl.cnf`），需 `OPENSSL_CONF=D:\Anaconda\Library\ssl\openssl.cnf` 后 rc=0；mingw 副本 0 配置 rc=0 |
| curl | **存在**（口径差，★ 收窄④） | 编排方 which 指 system curl 8.21.0；[评] 实测 PATH 首位是 mingw 副本 8.19.0 | 编排方基线 + [评]/[复] 口径登记（两套均可用，不构成分歧） |
| ssh-keygen | **存在×2** | Git OpenSSH_10.3p1 与 Windows OpenSSH_9.5p2 | [评] 两套 `-Y sign` 实跑均回 `Too few arguments for sign: missing namespace`（⇒ -Y sign 子命令在）；[复] 版本号修正为 9.5p2 |
| certutil | **存在但版本/功能不支持目标功能** | `C:\Windows\system32\certutil.EXE` | [评] `certutil -?`：`-sign -- 重新签名 CRL 或证书`（不支持任意文件 detached 签名）、`-hashfile` 仅哈希、`-get-sth`/`-get-sth-consistency` 是 CT STH 读取客户端 |
| powershell | **存在** | 5.1.26100.9711 | [评] `Add-Type System.Security` 后 `SignedCms_OK`/`CmsSigner_OK`；`Set-AuthenticodeSignature` 存在 |
| minisign / signify / cosign / age / gpg2 / signtool | **不存在**（均非必需） | — | [评] which 全 null；替代路径已在本机（openssl cms / ssh-keygen -Y / gpg detached） |
| python / sqlite3 / gh | **存在** | Python 3.12.10（hashlib/certifi）；sqlite3 3.51.0；gh 2.93.0 已登录（scopes `gist`,`read:org`,`repo`） | 编排方基线 + [评] |
| openssl ts 旗标 `-sha256` | **help 文本不列、旗标实际可用**（★ 收窄③） | — | [复] 两套 `ts -query -help` grep `-sha256` 计 0；但 mingw 实跑 `ts -query -sha256 -data <f> -out .tsq` rc=0、读回 `Hash Algorithm: sha256` |

### 2.2 密钥库现状

- **GPG secret key = 0 把**。[评] 命令级：`gpg --list-secret-keys` rc=0 且仅输出 `directory ... created`/`trustdb created`；`--list-secret-keys --with-colons` rc=0 空输出。[复] 文件级（更硬）：`~/.gnupg` 无 `private-keys-v1.d`，仅 `public-keys.d/pubring.db`。
- **`~/.ssh` 仅三文件**：`known_hosts`、`known_hosts.old`、`lightsail-us-east-2.pem`（[评] 只列名，内容未读，能否作签名密钥**未验**）。
- **Windows 证书库**（[评] `certutil -store -user My` 逐张实跑）：7 张全部 `HasPrivateKey=True`；其中 **5 张 EKU=代码签名（OID 1.3.6.1.5.5.7.3.3）**，thumbprint 前缀 `CDA0E29436D1341D` / `C83DD829BFB7203A` / `9C47A1E16A12C55B` / `8457541C47892A2B` / `107F9F1457AE0096`；1 张服务器身份验证（30705FA3→1.3.6.1.5.5.7.3.1）、1 张加密文件系统（061A293C→1.3.6.1.4.1.311.10.3.4）[复] OID 对照；**全部自签（Subject==Issuer）**、提供程序=Microsoft Software Key Storage Provider、`无法以纯文本方式导出私钥` ⇒ 有可用签名密钥但**无第三方 CA 身份链**。[复] 独立确认 7/7 与五 thumbprint 吻合。
- 副作用如实登记 [评]：`gpg --list-secret-keys` 自动创建 `~/.gnupg`（编排方基线 `NO_GNUPG_DIR`）；`rm` 报 `Device or resource busy`，残留 `public-keys.d/pubring.db`（含 0 把 secret key）。本会话未运行 gpg，无新增副作用。

### 2.3 网络可达性（纪律：仅 TCP connect+close 与 curl -I；探测政策写于 `_sv_net_probe.py` 首部 NET PROBE POLICY [评]）

| 目标 | 结果 | 依据 |
|---|---|---|
| TCP 9 个目标 | **9/9 OK** | [评] `_sv_net_probe.py` |
| `example.com` | HEAD 200（Date 2026-11-09T14:54:11GMT） | [评] |
| `freetsa.org/` 与 `/tsr` | 302 / **403（HEAD 被拒）** | [评] |
| `freetsa.org/files/cacert.pem`、`/files/tsa.crt` | 200、200（`/files/tsa.pem` 404） | [评] |
| `http://timestamp.digicert.com/` | 404；**https 同主机 rc=35 握手失败** | [评] |
| `rekor.sigstore.dev/` 与 `/api/v1/log` | 首轮 8s rc=28 → 20s 重试 200 / 405 | [评] |
| `fulcio.sigstore.dev/`、`http://timestamp.sectigo.com/` | 404 | [评] |

- **DNS 全落 198.18.0.0/15**（RFC 2544 基准段），`curl -v` 显示 `Established connection to freetsa.org (198.18.0.43 port 443) from 198.18.0.1` [评] ⇒ **疑似透明代理/仿真网络，对第三方独立性的影响未验**。[复] nslookup freetsa.org→198.18.0.43 逐字一致。
- **全部未验**：POST 往返、CA 链下载、genTime 可信性、透明日志 inclusion proof（纪律禁止 POST 仓库派生内容）。
- 定性：**M3 不是「本机不可行」**（TCP/握手/HEAD 通）；但「端到端可用」一个都还没证。

### 2.4 git 状态

- `git rev-parse HEAD` = `26574589aa8401e8f3f2934680a1ea7109bafa2d`（main）[本]；`git log -1 --format='%G?'` = `N` [本] ⇒ HEAD 无签名；[评] `git verify-commit HEAD` rc=1。
- 签名四键 `user.signingKey`/`gpg.program`/`gpg.format`/`commit.gpgsign` 全未配（rc=1）；`user.name=ZCode` / `user.email=zcode@local` 已配 [评]。
- **`GIT_COMMITTER_DATE` 可写实证**：`GIT_COMMITTER_DATE='2000-01-01T00:00:00+0000' git var GIT_COMMITTER_IDENT` 返回 `ZCode <zcode@local> 946684800 +0000` [评]，[复] 复现。
- `lead/cert_realcheck_20261109/_cr_seal.json` 未跟踪（`git ls-files --error-unmatch` rc=1 + `git status --porcelain` = `??`）[评]；写域整体 `?? lead/seal_v2_feasibility_20261109/` [本]。
- remote origin = github.com/Lawrence7y/ra2-campaign-forge；gh 2.93.0 已登录 [评]。

### 2.5 ★ 时间态：ctime 在本机不得用于定序

- **W32Time 服务 Stopped**：[本] `MSYS_NO_PATHCONV=1 /c/Windows/System32/w32tm.exe /query /status` → `发生下列错误: 服务尚未启动。 (0x80070426)`（[复] 同值闭合了评估员未取到该项的缺口；[评] 评估员在 Git Bash 被路径转换破坏，未取到）。注册表 `NtpServer=time.windows.com,0x9`、`Type=NTP` [评]。
- **本地三时间可写**：[评] 写域内覆写实证——新建后 ctime=mtime=T，同路径覆写后 ctime 不变（delta 0.0）、mtime +1.202s ⇒ `mtime>ctime` 为普通覆写常态。
- **被点名的 328.702 s 不构成异常**：`_cr_seal.json` st_ctime=1794220056.272236 / st_mtime=1794220384.9740431，差 328.702s；`_cr_build_seal.py` ctime=mtime=1794220380.4750667，builder.mtime−seal.ctime=324s [评]；成因 = 两次生成 + 同路径覆写（`ORDERING_EVIDENCE.md:110` 实读：CLI 库 rowid 635245→635250→635535→635544 记录链）；全库 `lead/` 下 `mtime−ctime>328.7` 有 507 件（`ORDERING_EVIDENCE.md:96-97` 记 506 件，点值漂移差 1，`:97` 自述）。`ORDERING_EVIDENCE.md:89` 的 328.701807s 与 `:94` 记载的 `impossible_under_normal_fs=True` **是上游判错**——[复] 独立复核确认「上游 impossible_under_normal_fs=True 是错的」。
- **推论**：mtime/ctime/atime 在本机一律不得用于定序（`ORDERING_EVIDENCE.md:123` 把三者与 git commit 时间/邮件 Date 头统列为「B 弱旁证（不抵赖）」）；seal_v2 格式必须把 fs_stat 显式降级为 `trust: weak_local_metadata`（§5.1）。

### 2.6 ★ 缺口清单：装什么 / 做多久 / 要谁批准（「缺工具」必附代价）

| 缺口 | 是否阻塞 | 补齐动作 | 时长 | 批准人 |
|---|---|---|---|---|
| minisign/signify/cosign/age 不存在 | **不阻塞**（openssl cms / ssh-keygen -Y / gpg detached 全可替代） | 若仍要装：winget/scoop 单包安装 | 安装耗时**未验**（禁令未装） | 安全负责人 |
| GPG secret key = 0 | **不阻塞签名路径**（改用 Windows 证书库 5 张代码签名证书，0 生成 0 安装） | 或批准 `gpg --batch --pinentry-mode loopback --passphrase '' --quick-generate-key <uid> ed25519 sign 0` 生成 1 把 | 生成耗时**未验**（铁律禁止，未实跑） | 安全/项目负责人 |
| Windows 证书库证书可签但未签过 | 不阻塞 | 首次 SignedCms 签名演练（只签测试字节） | 分钟级（类型已加载成功）[评] | 证书使用授权（谁的证书谁批） |
| TSA POST / CA 链下载 | 不阻塞 M3 设计，阻塞 M3 实证 | 放行 freetsa.org:443 + 批准发送仓库派生摘要 + 下载 cacert.pem/tsa.crt | 一次往返 + 一次下载，实测时长**未验** | 安全负责人（外发内容） |
| 透明日志写入（rekor 等） | 不阻塞设计 | OIDC 身份 + 外部写入批准；CLI 路径才需装 cosign | 安装耗时**未验** | 安全 + 运营 |
| **A 无写权的带外载体** | **★ 唯一真正阻塞可交付性的缺口**——不是工具，是账号/组织隔离 | 新建独立账号 / 采购存证服务 / 指定独立持有者 | 组织流程，无法估 | 项目/安全负责人 |
| W32Time 未启用 | **不阻塞 TSA 路径**（genTime 由 TSA 提供，不依赖本机 NTP） | `w32tm` 启用 + 域同步 | 分钟级 | 管理员 |
| 自建 TSA / PKI+HSM / 透明日志运维 | 不阻塞（M3 有外部替代） | 采购 + 建设 | 项目级 | 采购 + 安全 + 管理层 |

---

## 3 ★ M2 真实代价（现成身份体系做签名）

### 3.1 路径 A：detached 签名（gpg 分离签名 / Windows 证书 CMS）

命令序列 [评]（标注执行状态）：

```text
# 0 生成密钥（唯一前置；★ 本任务禁令未执行，耗时未验）
gpg --batch --no-tty --pinentry-mode loopback --passphrase '' \
    --quick-generate-key <uid> ed25519 sign 0          # 非交互路径（默认 --full-generate-key 走 pinentry 要交互）
# 1 验收密钥在库（无交互）
gpg --list-secret-keys --with-colons                   # 验收：至少一行 sec:
# 2 导出公钥 + 指纹（无交互；python -I -X utf8 + hashlib 算公钥文件 sha256）
gpg --armor --export <FPR> -o _sv_pubkey.asc
# 3 带外发布：<FPR> 与 sha256(_sv_pubkey.asc) 在 t0 发到 A 无写权载体
#   （同账号 gist 不算带外；需人与组织交互，见 §2.6 批准行）
# 4 对只读件出分离签名（无交互；输出写本写域）
gpg --detach-sign --local-user <FPR> -o _sv_cr_seal.json.asc -- <abs _cr_seal.json>
# 5 验签（无交互；验证方不需要本机私钥）
gpg --verify _sv_cr_seal.json.asc <abs _cr_seal.json>  # 验收：rc=0；改任一字节 rc!=0
# 6（可选，实为 M3）RFC3161 TSA，见 §4.3
```

**Windows 证书 CMS 替代路径（0 生成 0 安装）** [评]：PowerShell 5.1 `SignedCms`/`CmsSigner` 类型加载成功（SignedCms_OK/CmsSigner_OK），对任一只读件出 detached CMS（`ContentInfo`+`Sign()`，`-Binary`/`-NoDetached` 语义与 gpg 等价）；验证端 `SignedCms.CheckSignature(True)` 只需公钥。前置 = 证书使用授权（§2.6）。**注意**：5 张证书全自签 ⇒ 签名可验「密钥↔内容」，验不出「组织身份链」。

### 3.2 路径 B：`git commit -S`

前置 5 条 [评]：① 有签名密钥（GPG secret key，或 `gpg.format=ssh` + `allowedSignersFile`）② `user.signingKey` 或 `-S<keyid>` ③ `gpg.program`（编排方 PATH 需显式指到 `D:/Git/usr/bin/gpg.exe`）④ 可读 user.name/email ⑤ 文件先 `git add`。**本机今天直接跑会失败：0 把 GPG secret key——这是「缺密钥/缺配置」，不是「方案不可行」** [评]。

与路径 A 的差异 [评]：

- **多**：tree 级内容寻址（`git cat-file -p HEAD`：tree/parent/author/committer 明文头）+ parent DAG 因果偏序 + 现成 `verify-commit`/`%G?` + push 形成带外副本；
- **少/风险**：非单文件签名（单文件需经 tree→blob 推导或另出 detached sig）；仓库本地可重写（rebase/--amend，`ORDERING_EVIDENCE.md:139`）；**签名覆盖的 author/committer 时间字段本身可写**（`GIT_COMMITTER_DATE` 实证 946684800）；若 A 持 key 仍可同域双改（重新 commit 并同步改 seal+常量）；副作用面大（写 `.git/index/config`/对象库，均在本任务写域外）。

### 3.3 ★ 关键问题：签名是否给时间背书？——否

四条本机证据：

1. `gpg --dump-options` 含 **`--faked-system-time`**（[评][复] 双确认）；
2. `GIT_COMMITTER_DATE='2000-01-01...'` 实跑返回 946684800 [评][复]；
3. `openssl cms` 含 `-no_signing_time`（**仅 mingw 3.5.6 副本**，★ 收窄②）[复]；
4. W32Time Stopped（0x80070426，§2.5）[本]。

精确表述 [复]（修正编排方提示语「默认签名不含时间戳」的不精确）：**OpenPGP v4 分离签名并非「不含时间戳」，而是内嵌一个签名者可任意书写的创建时间字段**——RFC 4880 §5.2.3.4 原文「Signature Creation Time … (4-octet time field) The time the signature was made. MUST be present in the hashed area.」（子包类型 2）；GnuPG 手册证实 `--faked-system-time`「only useful for testing; it sets the system time back or forth」。⇒ **签名里的时间戳是自报字段、无第三方背书 ⇒ 签名不能作时间证明**。包级实验未跑（0 把 secret key + 禁生成密钥 + 全史 198 commit `%G?=N` 无样本可 `--list-packets`）[复]，双方如实标未跑。

### 3.4 与上游「M2 低代价把 T1/T4/T6/T8 升密码级」逐条核对（T1–T8 出处 `_os_ORACLE_SPEC.md:173-182` 实读）

| 判据 | M2 单独能否升密码级 | 依据 |
|---|---|---|
| T1 作者身份可验证 | **部分**：升到「密钥↔内容」密码级；key→真人映射仍靠 ID_REG 带外预注册（`_os_ORACLE_SPEC.md:175`）；若要求 ID_REG 确在 V1 前公布则又回到时间问题 | [评] §2(c) |
| T2 集合交为空 | 不需 M2（纯集合运算本就可技术核） | `_os_ORACLE_SPEC.md:176` |
| T4 标注早于 V1（t0<t1<t2） | **不能**：签名不解决「何时产生」（§3.3 四证据）；必须配 TSA + 独立 t2 锚 | `_os_ORACLE_SPEC.md:178`「无 PKI 时本地 mtime 只是弱旁证」 |
| T6 作者↔分片绑定 | **能**：逐分片 detached 签名即密码级，不需 TSA | `_os_ORACLE_SPEC.md:180` |
| T8 抗同域双改 | **结构性一半能**：带外公钥指纹/带外签名使 A 无法「同步重写 seal+常量+内容后仍产出有效签名」——`SEAL_CHRONOLOGY.md:279` 自己承认「结构性能做到，不可否认的密码级做不到」；**「不可否认」一半不能**（`ORACLE_SPEC.md:125`「无 PKI 时技术上为零」实读） | [评] §2(c) |
| T3 未见 V1 输出 / T5 不可派生 / T7 多源 | 与 M2 无关（认知状态/制度层，见 §5.4） | `ORACLE_SPEC.md:123` |

**上游矛盾逐字核实**（[评] 提出、[复] 逐行核实存在、[本] 实读确认原文本在）：

- `ORDERING_EVIDENCE.md:150`：「真正把时间做成密码级事实的是 M2（…）或 M3（…）」——把 M2 也算进「时间做成密码级事实」；
- 同件 `:166`（方案丙行）：「M2 把『谁、何时、哪份内容』绑定到人，T1/T4/T6/T8 由制度级升密码级（`SEAL_CHRONOLOGY.md:330`）；M3 时序成为可验证事实、真正不可否认」——同样把 T4 归给 M2；
- 但 `SEAL_CHRONOLOGY.md:141`：「**唯一**能把『确系事前/确系事后』判成密码级事实的路径」是 M3（`ORACLE_SPEC.md:133` 同指 M3「把时序做成可验证事实」）；
- `SEAL_CHRONOLOGY.md:279` 给出**正确分层**（T8 结构性=能 / 不可否认=不能），而 `:283`（「M2…即可把 T1/T4/T6/T8 从制度级升到密码级」）、`:325`（「把 T1/T4/T6/T8 一次升到密码级」）、`:330`（M2 行同）**未沿用**。

[复] 裁定（本件沿用）：`:141` 正确；`:283`/`:325`/`:330` 把 T4 归属 M2 是**过度声明**。台账内部措辞不一致，本件只登记不改只读件。

### 3.5 「低代价」的边界

- **技术接入层成立**：0 安装（gpg/openssl/curl/git/ssh-keygen/PowerShell 全在）、5–6 条命令、0–1 次密钥生成（Windows 证书路径 0 生成）。
- **总量不成立**：1 次带外发布 + ≥2 具名见证人 + 302 项双盲标注 ≈50.33 人时 / 端到端 60–95 人时 / 5–8 工作日（`SEAL_CHRONOLOGY.md:329`、`:333`「最小成本 ≠ 最小工作量…省不下 50+ 人时」、`ORACLE_SPEC.md:309`「不得由 A 代标」——三处实读），**M2 只是在必经流程上补签名，没有新增人力、也压缩不了既有人力** [评]。

---

## 4 ★ M3 真实代价（RFC3161 TSA + 透明日志）

### 4.1 RFC3161 前提逐条判

| 前提 | 判定 | 依据 |
|---|---|---|
| CA 链验证 | **本机可做但未验** | [评] 两套 `openssl ts -verify` 均支持 `-CAfile`/`-untrusted`/`-CAstore`；本机 `/mingw64/etc/ssl/cert.pem`、`D:/Anaconda/Library/ssl/cacert.pem` 在盘；freetsa `cacert.pem`/`tsa.crt` HEAD 200——但未下载、未实跑 verify ⇒ **未验** |
| 可信时间源 | **本机不可做，TSA 路径不需要本机做** | W32Time Stopped（0x80070426 [本]）；genTime 由 TSA 提供并签名，不依赖本机 NTP [评] |
| 联外网 | **本机可做（TCP/HEAD 层）** | §2.3 表；写入端点 POST **未验** |
| 需采购项 | 商业 TSA 配额 / 自建 PKI+HSM+审计 / 透明日志运维 / OIDC 身份 | [评]；免费 freetsa 无 SLA、无法律级不可否认、CA 自签 ⇒ **信任锚必须随 seal 一并公布** |
| 端口事实 | `https://timestamp.digicert.com` rc=35 握手失败（http 404 可达）[评][复]；DigiCert HTTPS TSA 路径判不了 | §6.4 |

### 4.2 ★ 透明日志：本机自建 = 方案本身不可行（非缺工具）

- 依据 `ORDERING_EVIDENCE.md:140`（实读）：CLI 会话库 `part` 表「本地 sqlite 可写、无签名、非密码学强制；`count=622897 < max(rowid)=648627`（约 2.5 万 rowid 缺口）、有 `time_updated` 列 ⇒ **不是 append-only 日志**；窗口 635000–636000 的 1001 行中 **182 次** `time_created` 倒退」。
- [复] 独立复算（sqlite3 `mode=ro` over WAL，读后无新文件）：`count(*)=627,007 < max(rowid)=652,737`（缺口 25,730，随活库增长点值漂移）；**窗口 rowid 635000..636000 相邻 `time_created` 倒退 = 182 次，与台账逐字复现**（历史行不变故可精确复现）。
- 相关佐证：`SEAL_CHRONOLOGY.md:132`「本会话未找到任何独立的（带外的、不受本地写域控制的）时间证据」；`_os_ORACLE_SPEC.md:182` / `ORACLE_SPEC.md:108` / `SEAL_CHRONOLOGY.md:269`：T8 要求承诺+标注包+常量**至少一者在 A 写域外**，且「至少一个锚的写 ACL 不含 A」是**确定性判断**。
- **判据不是「日志不可改」而是「日志写 ACL 不含 A 且其时间由日志运营方签名」** [评]。append-only 只是难改不是不能改；immudb/WORM 只要 admin 凭据在 A 手里仍不满足。⇒ 必须**外部化**：rekor / CT log / 独立机构存证 / 独立账号载体。**本机自建透明日志与 CLI DB 同级，属方案本身不可行**（不是「缺 cosign」这类工具缺口）。

### 4.3 本机现在能做的最小 M3（全部未验）

[评] 给出、[复] 修正旗标与环境的命令序列（★ 本任务纪律禁止 POST，未执行）：

```text
# mingw 副本 0 配置可用；若用 D:\Anaconda 副本必须先：
#   set OPENSSL_CONF=D:\Anaconda\Library\ssl\openssl.cnf   （★ 收窄②：缺省 rc=1）
openssl ts -query -sha256 -cert -digest <64hex> -out _sv_req.tsq   # 旗标 -sha256 实测可用（help 不列，★ 收窄③）
curl -sS -H 'Content-Type: application/timestamp-query' \
     --data-binary @_sv_req.tsq https://freetsa.org/tsr -o _sv_resp.tsr
openssl ts -reply -in _sv_resp.tsr -text                            # 读 genTime
openssl ts -verify -queryfile _sv_req.tsq -in _sv_resp.tsr \
            -CAfile cacert.pem -untrusted tsa.crt
```

产出物：`.tsq`/`.tsr`/genTime 文本。**POST 往返 / CA 链验证 / genTime 可信性 / inclusion proof 全部未验**（纪律禁止发送仓库派生摘要）。

---

## 5 ★ 下一代 seal 最小可行方案（seal_v2）

### 5.1 格式定义（冻结件：`_sv_seal_v2.schema.json`，11,988 B [本]）

- **CANON(x)** = `json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',',':')) + "\n"`（UTF-8）；**H = sha256** [评]。
- **seal 不含自身 sha**（自指悖论；上游实测 seal_self_sha_in_V1=[]）[评]。
- `subject.items` 沿用 `_cr_seal.json:1-40` 实读字段：`file_sha256`/`bytes`/`evidence_span_sha256`/`anchor`/`evidence_lines`（另 `quote`/`roles`/`oracle`）。
- **`time_anchors` ≥2 条不同源且 ≥1 条 `carrier_outside_A_write_domain=true`**；fs_stat 类锚显式 `writable:true` / `trust:weak_local_metadata`，**永不用于定序**（§2.5）[评]。
- **`commitment`**：t0 的 `H(P)` + 载体定位；**`predicate_run_anchor`**：独立 t2 锚（**最易漏**——缺它则「seal 早于 V1」不成立）[评]。
- **`signers` 逐分片**：每分片独立密钥/回执，`key_generated_by_this_run` 必须为 false（§2.6：密钥生成须走批准通道）[评]。
- **`provenance` 三层**：`cryptographic_claims` / `institutional_only_claims`（必含 `adjudicator_did_not_see_V1_outputs`、`key_to_person_mapping`）/ `unverified` [评]。

### 5.2 schema 反向保险（防「把制度写成密码学」）——本会话 grep 实证

`_sv_seal_v2.schema.json`：`:139` `carrier_outside_A_write_domain: const true`（time_anchors 内）；`:194` `key_generated_by_this_run: const false`；`:226` `cognitive_independence_is_provable: const false`；`:227` `fs_times_used_for_ordering: const false`；`:208` provenance 必含三层 [本]。
复核骨架对应硬闸 `_sv_verify_skeleton.py`（实读）：`:150-153` `TIME_ANCHORS_LT_2_DISTINCT_SOURCES` / `NO_CARRIER_OUTSIDE_A_WRITE_DOMAIN`；`:156-159` `FS_TIMES_USED_FOR_ORDERING` / `COGNITIVE_INDEPENDENCE_OVERCLAIM`；`:180-181` 缺 RFC3161 令牌即报 `NO_RFC3161_TOKEN__TIME_IS_INSTITUTIONAL_ONLY`；`:188-195` `V1_FIRST_RUN_ANCHOR_NOT_INDEPENDENT` / `T0_T1_T2_NOT_EVALUATED_WITHOUT_TWO_TSA_GENTIMES`；`:200-204` 制度声明缺项即 `COGNITIVE_INDEPENDENCE_NOT_DECLARED_AS_INSTITUTIONAL`；`:208-209` PASS 注记「仅指枚举的技术检查通过，绝不意味着盲标注/独立性已证」。
schema 性质自证 [评]：按内容解析 `IS_SEAL_INSTANCE=False`，64-hex 字面量 0 个，仅 20 处 `^[0-9a-f]{64}$` 模式串 ⇒ 是格式定义不是 seal 实例。

### 5.3 生成骨架与复核骨架（均未执行）

- `_sv_build_skeleton.py`（11,141 B [本]）与 `_sv_verify_skeleton.py`（10,104 B [本]）：[复] `ast.parse` 通过、从未执行；无 socket/urllib/requests imports、无 keygen 串、有 `__main__` 守卫、网络仅 `--allow-network` 门控 [复] S5。
- 复核骨架验收面（§5(b)#7）：不需私钥；缺签名/缺带外锚/缺 t2 锚/文件哈希不符/time_anchors<2 任一即显式 FAIL；**同域双改演练必须 FAIL**（对照 `CERT_REAL_CHECK.md:509` 实读现状：同域同步重写后 `VERDICT=PASS, seal_ok=true, n_pass=5, n_fail=0`——旧管道的实证漏洞）。

### 5.4 ★ 对照 `_fnr_check.py:73-76` 四项逐条判（密码学 / 制度 / 做不到）

[本] 实读 `_fnr_check.py:73-76` 原文：

```python
# Let ORACLE: I -> {0,1} be a ground-truth label produced BEFORE V1 is run,
# by an adjudicator who does not see V1's outputs and did not author V1,
# with a published SHA256 seal. truth=1 means "the required semantic content
# is genuinely delivered in this artifact", judged role-by-role.
```

| # | 四项要求 | seal_v2 能给到哪一级 | 依据 |
|---|---|---|---|
| ① | produced **BEFORE V1 is run** | **部分能（密码学）**：TSA genTime + 独立 t2 锚可复算 t0<t1<t2；缺 TSA 则降级制度级必须标 `UNVERIFIED`（verify 骨架 `:194-195` 缺两个 genTime 即 FAIL） | §3.3/§4.1；[评] 4(b)① |
| ② | **does not see V1's outputs** | **完全做不到（制度）**：「读没读过，从产物上不可判定」（`ORACLE_SPEC.md:123` 实读）；「未见本身为制度性假设，非技术可证事实」（`ORACLE_SPEC.md:163` 实读）；`SEAL_CHRONOLOGY.md:144` 同 | [评] 4(b)② |
| ③ | **did not author V1** | **部分能（密码学+制度）**：T6 逐分片签名 + T1 `H(ID_REG)` 带外 + T2 集合交为空可技术核；key→真人、无共同汇报线仍靠制度（本机可用证书全自签、身份链为零） | `_os_ORACLE_SPEC.md:175-176/:180`；[评] 4(b)③ |
| ④ | **published SHA256 seal** | **能完全满足（密码学）**：64-hex 在 t0 前公布到 A 无写权载体，第三方对收到的字节重算；**同账号 gist 不算带外** | `SEAL_CHRONOLOGY.md:139`；[评] 4(b)④ |

[复] ⑤ 专项核查：未发现把制度保证写成密码学保证（schema 反向保险 + verify 骨架显式 FAIL 双保险，§5.2）。措辞级提醒沿用：「不可回改…密码级」严格说是**篡改可检出**（改任一字节验签即败）而非「改不了」——无实质越界 [复]。

### 5.5 三档使用判据（防越声称）

| 档 | 组成 | 允许声称 | 禁止声称 |
|---|---|---|---|
| 日常自检 | 现有 `_cr_seal.json` + hashlib + stat（0 安装） | 内容完整性、当前字段值 | 独立 / 预注册 / 不可否认；**ctime/mtime 不得用于定序** |
| 对外交付 | + detached 签名（gpg 或 Windows 证书 CMS）+ 带外公钥指纹 + commit-then-reveal + ≥2 见证人 | 内容绑定 + 作者↔分片绑定（密钥级）+ 抗事后换件 | 时序密码级（「seal 早于 V1」）；组织身份链（证书全自签） |
| 需要不可否认 | + RFC3161 TSA 令牌 + 第三方 append-only 日志 + 独立 t2 锚 + 预注册 ID_REG/A_REG/P/κ/覆盖=1.0/ACL 日志 + ≥2 真第三方 | 时序**部分**可验（genTime 可信性仍以 TSA 运营为前提）；抗同域双改（演练 FAIL） | 「未见 V1 输出」已证；把 `INTEGRITY_OK_BUT_UNCONFIRMED` 升格 PASS（`SEAL_CHRONOLOGY.md:352`「特别禁止…降格成弱 PASS」实读） |

---

## 6 复核回件（绑定行格式）+ 结论 + 未验项

### 6.1 复核回件如实记（verdict = partial ⇒ 本件标 unconfirmed）

复核员对评估员回件的裁定：**`partial`**——四大核心结论全部经独立重跑成立（签名不能给时间背书 / 本机透明日志与 CLI DB 同级属方案级不可行 / 制度·密码学分层 / 旧 seal 判词维持），能力清点主体准确，但存在 **4 处需收窄的次要失实**（无一推翻主结论）[复]。复核员绑定行（逐字转录，绑定对象 = 评估员回件 JSON 原文，存档 `_svv_evaluator_reply.json`）：

被核对象 SHA256 = d589eff19655c7c3efebe9c7789e279fd15b1ed9094a800a889167140bdd118c，字节数 = 26788

复核员第二绑定行（被核报告现盘件 `_sv_FEASIBILITY.md`）：

被核对象 SHA256 = 68c3debd4f6617a604829c570f887ec2afc61ffc3d7fe90aaa6da3ef54d92586，字节数 = 63478

**4 处收窄（全部并入正文，标注 ★ 收窄①–④）**：

1. **★ 收窄①（字节数不符）**：评估员回件称 `_sv_FEASIBILITY.md` 62,443 B，现盘 63,478 B（+1,035 B，mtime 11-09 23:44，改动不可追溯；其余 3 件 11,988/11,141/10,104 全吻合）。[本] 本会话复核：`ls -la` 现盘 63,478 B；hashlib 实算 = 复核员第二绑定行同值（§6.1），差异**维持登记**，评估员回件的字节数字段按现盘为准。
2. **★ 收窄②（openssl 双拷贝抹平）**：`cms -no_signing_time` 仅 mingw 3.5.6 有；Anaconda 3.0.18 的 `ts -query` 在裸 Git Bash 无 `OPENSSL_CONF` 时 rc=1。评估员 §3(c) 命令块原样照跑会失败——本件 §4.3 已给修正版。
3. **★ 收窄③（help 不列旗标）**：「`ts -query -help` 列 `-sha256`」不实（两套 grep 计 0）；旗标 mingw 实测可用（rc=0，读回 `Hash Algorithm: sha256`）。
4. **★ 收窄④（口径差）**：curl 8.19.0=mingw 副本 vs 编排方 which 指 system 8.21.0；Windows OpenSSH 实为 9.5p2。均为口径差异非错。

**2 处措辞张力（[复] 提出，本件结论已按其收窄）**：(a) 「补齐 TSA+独立 t2 锚后『seal 早于 V1』= 密码级」须带「**部分**」限定——t2 锚的内容真实性（锚确系 V1 首跑时由诚实非 A 方产生）仍是制度前提；(b) 「今天 0 安装做到密码级」隐含已有签名密钥——GPG 路径今天 0 把（需批准生成），**实际 0 安装路径是 Windows 证书库 5 张自签代码签名证书**（且需证书使用授权）。

[复] 加分闭合：评估员 5(c)#7 的 w32tm 项，[复] 以 `MSYS_NO_PATHCONV=1` 取到「0x80070426 服务尚未启动」；[本] 本会话独立复跑同值（§2.5），该未验项**闭合**。

[复] 自报险情（如实转录）：复核中曾误以无参 `ssh-keygen.exe` 取版本号（该命令默认开始生成 ed25519 密钥对），因 head 截断管道 + 无 TTY 未落盘，`ls ~/.ssh` 复核无任何 `id_*` 文件——未违铁律。[本] 本会话未运行裸 ssh-keygen，无同类事件。

**本会话自证（[本]）**：`python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\seal_v2_feasibility_20261109\_svw_fingerprints.py"`（hashlib，只读）输出 **TOTAL=14 MATCH=14 MISMATCH=0**——7 件编排方基线、5 件评估员补算台账、2 件复核员绑定件全部与绑定值逐件相等。只读域在任务收尾时点未被改动的结论以该 14/14 为准。

### 6.2 结论：部分能

**一句话**：**部分能**——下一次 seal 能做到「内容完整性 + 逐分片身份/密钥绑定 + 带外承诺 + 篡改可检出」的可验证（本机今天 0 安装可做，前提是走 Windows 证书库路径并取得证书使用授权；GPG 路径需先批准生成 1 把密钥）；补齐 RFC3161 TSA + 独立 t2 锚并获外发批准后，「seal 早于 V1」也**部分**升为可复算事实（t2 锚本身的内容真实性仍是制度前提）；但「标注者未见 V1 输出 / 标注独立」**永远不能**靠 seal 技术证明，只能靠制度（`ORACLE_SPEC.md:123/:163`、`SEAL_CHRONOLOGY.md:144`）。

成立条件（缺一降档）：① `H(P)`/`H(seal_bytes)` 在 V1 之前发布到 A 无写权载体；② 每分片带 detached 签名且信任锚带外；③ TSA + 独立 t2 锚；④ 逐层标注哪些靠制度；⑤ TSA POST / CA 链 / 外部日志写入获批准并**实跑验证**（当前全部未验）。旧 seal「前提层不成立 / `INTEGRITY_OK_BUT_UNCONFIRMED`」维持不变。

### 6.3 落地顺序（10 步）与验收判据

| 步 | 内容 | 验收判据 |
|---|---|---|
| 0 | 能力清点 | 本件 §2（[本] 14/14 指纹 + which 三态）；HEAD 未变、写域无签名产物 |
| 1 | 选信任根（0 安装） | Windows 证书库 5 张代码签名证书（0 生成，需使用授权）**或** 批准生成 1 把 GPG Ed25519（耗时未验）；产出公钥/证书指纹 + 带外公布位置且写 ACL 不含 A。验收：`Get-ChildItem Cert:\CurrentUser\My \| ? HasPrivateKey` 非空 或 `gpg --batch --list-secret-keys` 非空 |
| 2 | 冻结格式与规范化 | `_sv_seal_v2.schema.json` + CANON/H；用纯样例对象验证「两种键序 → 同一 digest」且 seal 无自身 sha |
| 3 | t0 带外承诺 | V1 首跑前独立载体上出现 `H(P)` 与 `H(seal_bytes)` 的 64-hex，带不受 A 控制的时间；第三方 hashlib 重算相等且能在 A 账号外取到 |
| 4 | 生成 seal_v2 + detached 签名 | 逐文件 sha256/bytes 全 match；`gpg --verify`（或 `SignedCms.CheckSignature`）在只有公钥环境 rc=0；改任一字节非 0 |
| 5 | TSA + 透明日志（需批准） | `openssl ts -verify` rc=0 且 genTime 落在 t0..t2；rekor entry + inclusion proof；**POST 未获批准则整步标 `UNVERIFIED`**，不得写成时序已证 |
| 6 | 独立 t2 锚（最易漏） | 非 A 方在 V1 首跑时另出一条锚；t0<t1<t2 由两条独立第三方时间凭证复算成立；缺此项则「早于」不成立 |
| 7 | 第三方复核脚本 | `_sv_verify_skeleton.py` 落地：不需私钥、缺任一锚显式 FAIL；**同域双改演练必须 FAIL**（对照 `CERT_REAL_CHECK.md:509` 现状 PASS） |
| 8 | 制度层并行 | ID_REG/A_REG/P/κ 门槛/覆盖=1.0/ACL 日志/≥2 具名裁决者/302 项全覆盖预注册；「未见 V1 输出」写为制度性假设 |
| 9 | 结论表述 | 逐层分开写、T1–T8 逐条报状态、未验项标 `UNVERIFIED`、不得升格 PASS（`SEAL_CHRONOLOGY.md:352`） |

### 6.4 判不了什么（如实列）

1. TSA POST 往返 / genTime 可信性 / freetsa CA 链能否本机 `openssl ts -verify` 成功（纪律禁止 POST）；
2. 透明日志写入端点 + inclusion proof + OIDC 签发；
3. 198.18.0.x 出口是什么（疑似透明代理/仿真网络）及是否削弱第三方独立性；
4. `~/.ssh/lightsail-us-east-2.pem` 内容与能否作签名密钥（只列名未读）；
5. Windows 5 张代码签名证书能否实际产出 detached CMS 签名（只 Add-Type 加载类型，未签任何字节）；
6. 生成 GPG 密钥实际耗时（禁令未跑）；
7. NtSetInformationFile 类接口改 ctime（沿用 `ORDERING_EVIDENCE.md:112` 未验）；
8. 同域双改演练（未重跑 `CERT_REAL_CHECK.md:509`，只读纪律）；
9. 「标注者未见 V1 输出」认知状态（产物上不可判定，`ORACLE_SPEC.md:123`）；
10. 旧 seal 时间与本案结论（维持不变，不重开）；
11. 安装 minisign/cosign 耗时与审批周期；自建 TSA/透明日志采购成本与工期；
12. `git gpg.format=x509` + gsm 路径（`git help -c` 只列键，未实跑）；
13. DigiCert HTTPS TSA 路径（rc=35 握手失败，http 404 可达）；
14. ~~本机时钟与 UTC 真实同步~~ → **已闭合**：`w32tm /query /status` = 0x80070426 服务尚未启动（[复] 首取，[本] 复跑同值）；但「时钟若启动后与 UTC 偏差多少」仍判不了。

**签名包级实验**（--list-packets 看签名内嵌时间字段）未跑：0 把 secret key + 禁生成密钥 + 全史 commit `%G?=N` 无样本 [复]。

### 6.5 未验项汇总（正文逐处已标，此处汇总）

POST/CA 下载/genTime 验证/inclusion proof；DNS 出口性质；lightsail pem 内容；CMS 实签；GPG keygen 耗时；NtSetInformationFile；同域双改演练重跑；minisign/cosign 安装耗时与审批；x509 git 签名路径；DigiCert HTTPS；工具安装时长（§2.6 全列）；t2 锚内容真实性（制度前提，技术不可判）。

### 6.6 纪律自检

- 零真机：无 gamemd.exe/ra2loader/YURI.exe/taskkill/活进程内存读取。零采样代码：无 hook/MiniDump/SuspendThread/StackWalk/探针注入/动态内存解析。
- 只读域未改：`_svw_fingerprints.py` 收尾实算 14/14 MATCH（含两件台账、五只读目录件）。
- 未生成 seal/未装工具/未生成密钥/未 commit/未 push：HEAD 仍 `26574589aa8401e8f3f2934680a1ea7109bafa2d`；写域 `git status --porcelain` = `??`（未跟踪）[本]。
- 本会话网络使用：**零**（无 TCP 探测、无 HEAD、无 POST；评估员的历史探测政策与政策声明见 `_sv_net_probe.py` 首部）。
- 写域新增：本件 `SEAL_V2_FEASIBILITY.md` 与 `_svw_fingerprints.py`（`_svw_` 前缀，本任务写域内）；未触碰 `_sv_*`、`_svv_*` 既有件。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 hashlib。
