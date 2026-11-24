# seal v2 可行性评估（`_sv_FEASIBILITY.md`）

唯一写域：`lead/seal_v2_feasibility_20261109/`，全部产物前缀 `_sv_`。
纪律自检：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；只读域未改；未生成任何 seal、未安装任何工具、未生成任何密钥、未 commit、未 push、未向外部发送任何本仓库内容（网络探测仅 TCP 握手与 HTTP HEAD，无请求体）。Python 一律 `python -I -X utf8` + 绝对路径，指纹一律 `hashlib`。

本件只做**能力清点与方案设计**。凡「本机缺工具」与「方案本身不可行」分开写，绝不互相冒充。

---

## 0 绑定行（逐件，格式固定）

复核对象: lead/PENDING_DECISIONS.md
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419

复核对象: lead/GOAL_THREE_TARGETS_20261018.md
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

复核对象: lead/ordering_evidence_20261109/ORDERING_EVIDENCE.md
被核对象 SHA256 = 04217b1321f7b9fc576fae39be43c5718e0ced65ee4212b5cfc11807dbb99da0，字节数 = 47952

复核对象: lead/cert_realcheck_20261109/_cr_seal.json
被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395

复核对象: lead/cert_realcheck_20261109/_cr_build_seal.py
被核对象 SHA256 = 2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574，字节数 = 5376

复核对象: lead/cert_realcheck_20261109/_cr_real_verify.py
被核对象 SHA256 = 3d8ab1092ebf85efe3cc84e22c1eeb98b867a16f44d07cf877f1e2b4eb5c30fa，字节数 = 21178

复核对象: lead/falsifiable_no_relax_20261109/_fnr_check.py
被核对象 SHA256 = 94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2，字节数 = 28811

复核对象: lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md
被核对象 SHA256 = 6b5eda3e58c439c576d3e6e6f8c91220e9b36201280f7672eb4c9ca9140b55ea，字节数 = 55693

复核对象: lead/oracle_spec_20261109/ORACLE_SPEC.md
被核对象 SHA256 = 7f9316ddfa33f405281bd2d33b0e22be7f7cc60c7d00dd070901b1392993a4a0，字节数 = 49318

复核对象: lead/oracle_spec_20261109/_os_ORACLE_SPEC.md
被核对象 SHA256 = 5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156，字节数 = 52542

复核对象: lead/cert_realcheck_20261109/CERT_REAL_CHECK.md
被核对象 SHA256 = fa3a45b7fd96ea8c3130a02227f6b6748bf4f196a5f714a51d3850e6d98ef014，字节数 = 53782

复核对象: lead/falsifiable_no_relax_20261109/FALSIFIABLE_NO_RELAX.md
被核对象 SHA256 = c54694849bb2ad84126c86d692f53ca3ba7362e33ede3a4c45dffebf275de0da，字节数 = 45824

以上共 12 条绑定行：前 7 件与编排方【实跑：基线指纹】逐件一致；后 5 件（`SEAL_CHRONOLOGY.md` / `ORACLE_SPEC.md` / `_os_ORACLE_SPEC.md` / `CERT_REAL_CHECK.md` / `FALSIFIABLE_NO_RELAX.md`）为本会话补算，另对 `ORDERING_EVIDENCE.md` 再次复算与基线同值。探针 `_sv_probe_readonly.py` 在收尾时二次复算 7 件基线，`MATCH_BASELINE= True` ×7；`git rev-parse HEAD` 仍为 `26574589aa8401e8f3f2934680a1ea7109bafa2d`；写域内只有 `_sv_` 前缀文件，无 `.sig/.asc/.p7s/.key/ seal*.json/.tsr`。

### 0.1 独立复核：ctime 事实（本题背景要求）

实跑命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/seal_v2_feasibility_20261109/_sv_probe_readonly.py`

```
lead\cert_realcheck_20261109\_cr_seal.json   st_ctime=1794220056.272236  st_mtime=1794220384.9740431  mtime-ctime=328.702 s
lead\cert_realcheck_20261109\_cr_build_seal.py st_ctime=1794220380.4750667 st_mtime=1794220380.4750667  mtime-ctime=0.0 s
builder.mtime − seal.ctime = 324.202831 s → 整数 324 s
```

写域内覆写实证（同一探针 C 段，文件已 unlink）：

```
after create : ctime=1794235971.9403656 mtime=1794235971.9403656
after rewrite: ctime=1794235971.9403656 mtime=1794235973.142162
ctime_delta=0.0  mtime_delta=1.202  mtime>ctime after rewrite = True
```

全库扫描（同一探针 D 段）：`lead/` 下 `total_files_under_lead = 9983`，`count_mtime_minus_ctime_gt_328.7 = 507`（样例最大 `lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` 798834.9 s）。与 `ORDERING_EVIDENCE.md:89`、`:96-97`、`:110` 的 328.701807 s / 506 件 /「Windows 上 st_ctime 是创建时间、mtime>ctime 是普通覆写常态」方向一致；计数差异是并发写入造成的点值漂移（`:97` 已自述 `- 506 件` 是点值）。

**结论（独立复核通过）**：上游 `impossible_under_normal_fs = True` 是错的。任何基于 `st_ctime` 的定序论证在本机都不成立为强证据；ctime 只能作「目录项创建时刻」的弱旁证。`ORDERING_EVIDENCE.md:112` 明记 `NtSetInformationFile` 类接口改 ctime「未实跑，未验」，本任务同样**未验**。

---

## 1 第一步：能力清点（本机到底有什么）

### 1(a) 逐项三态（自己重跑，不沿用编排方结果）

实跑命令（Bash，Git Bash）：

```
for t in git gpg gpg2 minisign signify openssl curl ssh-keygen ssh certutil powershell cosign age sqlite3 python python3; do p=$(command -v "$t" 2>/dev/null); ... done
git --version ; openssl version -a ; curl --version ; ssh -V ; python -I -X utf8 -V ; sqlite3 --version
gpg --version ; openssl ts -help ; openssl list -commands
powershell -NoProfile -Command "Get-Command gpg,minisign,signify,cosign,openssl,curl,ssh-keygen,certutil,signtool,git ..."
```

| 工具 | 三态 | 实跑依据（路径 / 版本 / 目标功能） |
|---|---|---|
| `git` | **存在** | Bash `/mingw64/bin/git`；PowerShell `D:\Git\mingw64\bin\git.exe`；`git version 2.54.0.windows.1`。目标功能 `commit -S` 支持：`git commit -h` 输出 `-S, --[no-]gpg-sign[=<key-id>]`；`git help -c` 含 `user.signingKey` / `gpg.program` / `gpg.format` / `commit.gpgSign` / `tag.gpgSign` / `gpg.ssh.allowedSignersFile` / `gpg.minTrustLevel` |
| `gpg` | **存在**（编排方 `which` 报 `null` 是 PATH 差异，不是缺工具） | Git Bash `/usr/bin/gpg` = `D:\Git\usr\bin\gpg.exe`（PowerShell `Get-Command gpg` 实跑 PRESENT）；`gpg (GnuPG) 2.4.9`，Pubkey 含 `EDDSA`/`ECDSA`/`RSA`，Hash 含 `SHA256`；`gpg --dump-options` 含 `--detach-sign --local-user --output --batch --quick-generate-key --pinentry-mode --passphrase --yes --faked-system-time` |
| `minisign` | **不存在** | Bash `ABSENT`；PowerShell `ABSENT` |
| `signify` | **不存在** | Bash `ABSENT`；PowerShell `ABSENT` |
| `openssl` | **存在，两套，都支持目标功能** | Bash `/mingw64/bin/openssl` = `OpenSSL 3.5.6 7 Apr 2026`；Anaconda `D:\Anaconda\Library\bin\openssl.EXE` = `OpenSSL 3.0.18 30 Sep 2025`（编排方 which）。两套 `openssl list -commands` 都含 `ts`、`cms`、`dgst`、`x509`、`verify`；两套 `openssl ts -query -help` 都列出 `-query / -data / -digest / -cert / -out / -sha256` 与 `-verify / -CAfile / -untrusted`；`openssl cms -help` 含 `-sign -verify -binary -nodetach -content -md -signer` |
| `curl` | **存在** | `curl 8.19.0 (x86_64-w64-mingw32)`，Features 含 `SSL SSPI HSTS HTTPS-proxy`；`curl -h all` 含 `-I / --data-binary / --cacert / -X / -H` |
| `ssh-keygen` | **存在，两套，都支持 SSH 签名** | Git Bash `/usr/bin/ssh-keygen`（`OpenSSH_10.3p1`）；Windows `C:\Windows\System32\OpenSSH\ssh-keygen.EXE`。实跑 `ssh-keygen -Y sign` 与 `/c/Windows/System32/OpenSSH/ssh-keygen.EXE -Y sign` 均返回 `Too few arguments for sign: missing namespace`（证明 `-Y sign` 子命令存在）；`ssh-keygen -h` 列出 `-Y sign / -Y verify / -Y find-principals / -Y check-novalidate` |
| `certutil` | **存在但版本/功能不支持目标功能**（对「任意文件 detached 签名」） | `/c/Windows/system32/certutil`；`certutil -store -user My` 可用；`certutil -?` 中 `-sign -- 重新签名 CRL 或证书`（不是任意数据签名）、`-hashfile` 只算哈希、`-get-sth` / `-get-sth-consistency` 是 CT 日志 STH **读取**客户端（不是日志写入器）。缺口由 PowerShell `SignedCms` 补上（见下） |
| `powershell` | **存在** | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.EXE`，`5.1.26100.9711`。`Add-Type -AssemblyName System.Security` 后 `SignedCms_OK=System.Security.Cryptography.Pkcs.SignedCms` / `CmsSigner_OK=System.Security.Cryptography.Pkcs.CmsSigner`；`Set-AuthenticodeSignature` 命令存在 |
| `cosign` | **不存在** | Bash `ABSENT`；PowerShell `ABSENT` |
| 附加 | | `age` 不存在、`gpg2` 不存在、`signtool` 不存在；`sqlite3 3.51.0` 存在；`Python 3.12.10` 存在；`gh version 2.93.0 (2026-05-27)` 存在且已登录（`gh auth status`：`Logged in to github.com account Lawrence7y (keyring)`，scopes `'gist', 'read:org', 'repo'`） |

**★ 关键区分**：编排方【本机可用能力清点】里 `gpg: null` 与 `openssl` 只报 Anaconda 一套，是**编排方 PATH 不含 `D:\Git\usr\bin` / `D:\Git\mingw64\bin`** 造成的。本会话在 Bash 与 PowerShell 双视图下实跑确认 `gpg 2.4.9` 与 `OpenSSL 3.5.6` 都在本机。这是「清点口径差异」，**不是本机缺 gpg**。真正缺的只有 `minisign / signify / cosign / age / gpg2 / signtool`，且它们**不是必需**（见 4(d)）。

### 1(b) 密钥库现状（直接决定 M2「低代价」真假）

**① gpg secret key —— 无。**
实跑 `gpg --list-secret-keys`：`rc=0`，输出仅两行初始化信息：
```
gpg: directory '/c/Users/Administrator/.gnupg' created
gpg: /c/Users/Administrator/.gnupg/trustdb.gpg: trustdb created
```
`gpg --batch --no-tty --list-secret-keys --with-colons`：`rc=0`，**空输出**。`gpg --batch --no-tty --list-keys --with-colons` 仅 `tru::1:...:1:5`（trustdb 行），无公钥。`gpgconf --list-dirs` 报 `homedir:/c/Users/Administrator/.gnupg`。⇒ secret key 数 = 0、public key 数 = 0。

- **要不要交互**：默认 `gpg --full-generate-key` 走 `pinentry`（本机 `/usr/bin/pinentry` 存在），需交互式回答姓名/邮箱/口令 —— **要交互**。改成 `gpg --batch --no-tty --pinentry-mode loopback --passphrase '' --quick-generate-key "<uid>" ed25519 sign 0` 可**完全非交互**（`--batch / --quick-generate-key / --pinentry-mode / --passphrase / --yes` 均在 `gpg --dump-options` 实跑清单内）。
- **要多久**：**未验**。本任务铁律禁止生成任何密钥，故本会话**没有实跑密钥生成**，无法给实测秒数；任何「几秒/几十秒」都只能是未测估计，本报告不给这个数。可给的是机制事实：ED25519 生成不需大素数搜索，RSA 需熵与素性检验；两者耗时差异未实测。
- **副作用如实登记**：编排方基线是 `NO_GNUPG_DIR`；按要求实跑 `gpg --list-secret-keys` 时 GnuPG **自动创建**了 `~/.gnupg`。本会话已尝试清理，`rm -rf` 报 `rm: cannot remove '.../public-keys.d/pubring.db': Device or resource busy`（gpg-agent/keyboxd 占用）；残留 `~/.gnupg/public-keys.d/pubring.db` 一个文件，`find ... -name '*.key' -o -path '*private-keys-v1.d*'` 计数 **0**（无 secret key）。这是唯一发生在写域之外的副作用，未触碰任何只读域文件（7 件指纹 MATCH_BASELINE=True）。

**② `~/.ssh` 下有什么（只列文件名，不读内容）**
实跑 `ls -1 "$HOME/.ssh"`：
```
known_hosts
known_hosts.old
lightsail-us-east-2.pem
```
纪律要求只列名，故**未读任一文件内容**。`lightsail-us-east-2.pem` 是否为可用签名密钥、是什么算法、**未验**。⇒ 不能把 SSH 签名路径写成「已有现成密钥」。编排方 `ssh_dir` 清点与此一致。

**③ Windows 证书库 `certutil -store -user My`**
实跑 `certutil -store -user My`（Python 按 `mbcs` 解码输出，3440 字符，`certificate_headers=7`）+ PowerShell `Get-ChildItem Cert:\CurrentUser\My`：

| Thumbprint(前16) | Subject | HasPrivateKey | KeyUsage/EKU | NotAfter |
|---|---|---|---|---|
| CDA0E29436D1341D | CN=50BDFD77-8903-4850-9FFE-6E8522F64D5B | True | 代码签名 | 2031/6/7 |
| C83DD829BFB7203A | CN=Lawrence7Y | True | 代码签名 | 2029/8/15 |
| 9C47A1E16A12C55B | CN=B2250643-15B9-4016-82B3-C97EAFA5DABD | True | 代码签名 | 2029/8/28 |
| 8457541C47892A2B | CN=B2250643-15B9-4016-82B3-C97EAFA5DABD | True | 代码签名 | 2029/8/26 |
| 30705FA3BCC7DB33 | CN=localhost | True | 服务器身份验证 | 2027/5/28 |
| 107F9F1457AE0096 | CN=B2250643-15B9-4016-82B3-C97EAFA5DABD | True | 代码签名 | 2029/8/18 |
| 061A293C4C496F94 | CN=Administrator | True | 加密文件系统 | 2126/5/10 |

`certutil` 输出逐证含 `签名与公钥匹配`、`根证书: 使用者与颁发者匹配`、`提供程序 = Microsoft Software Key Storage Provider`、`无法以纯文本方式导出私钥`。

⇒ **有可用于签名的证书**：5 张 `HasPrivateKey=True` + EKU=代码签名，私钥在 CNG/KSP 内（不可明文导出），可用 PowerShell `SignedCms` / `Set-AuthenticodeSignature` 对任意字节签名。**但全部自签（颁发者=使用者，根证书自匹配），无第三方 CA 链**⇒ 信任锚只能是「证书指纹/公钥带外公布」，**不是 PKI 级身份认证**。

**★ 对 M2「低代价」的判定**：`_os_ORACLE_SPEC.md:224`、`SEAL_CHRONOLOGY.md:330` 说的「一对现成密钥」在 GPG/SSH 路径上**不成立**（0 把）；但在 **Windows 证书库路径上成立**（5 张带私钥的代码签名证书，零安装、零生成）。所以 M2 的真实代价不是「低」，而是**换一条技术路径后接近零**；代价转移到「证书私钥在 KSP 中不可导出、验签方必须用同一张证书、第三方身份仍需带外登记」。这是「本机缺 GPG 密钥」，**不是**「M2 方案不可行」。

### 1(c) 网络可达性（只做 TCP 连通性 / HTTP HEAD）

**纪律声明（写在报告里并已遵守）**：本会话所有网络操作 = `socket.create_connection()` 后立刻 `close()`（无载荷）+ `curl -sS -I`（HTTP HEAD，无 `-d/--data/--upload-file/--form/--json`，无 POST，无 TS query）。**未发送本仓库任何内容、任何派生摘要、任何文件名到外网**。命令与输出见 `_sv_net_probe.py` 及其实跑输出。

```
=== NET PROBE POLICY ===
TCP connect()+close only; curl -I (HEAD) only; NO request body, NO repo bytes, NO TS query.

TCP_OK  example.com:443 peer=('198.18.0.42',443)
TCP_OK  github.com:443 peer=('198.18.0.43',443)
TCP_OK  freetsa.org:443 peer=('198.18.0.43',443)
TCP_OK  www.freetsa.org:443 peer=('198.18.0.44',443)
TCP_OK  timestamp.digicert.com:80 peer=('198.18.0.45',80)
TCP_OK  timestamp.digicert.com:443 peer=('198.18.0.45',443)
TCP_OK  timestamp.sectigo.com:80 peer=('198.18.0.46',80)
TCP_OK  rekor.sigstore.dev:443 peer=('198.18.0.47',443)
TCP_OK  fulcio.sigstore.dev:443 peer=('198.18.0.48',443)

curl -I https://example.com              → HTTP/1.1 200 OK   (Date: Mon, 09 Nov 2026 14:54:11 GMT)
curl -I https://freetsa.org/             → HTTP/1.1 302 Found (nginx / PHP 7.4.13)
curl -I https://freetsa.org/tsr          → HTTP/1.1 403 Forbidden
curl -I http://timestamp.digicert.com/   → HTTP/1.1 404 Not Found
curl -I https://timestamp.digicert.com/  → rc=35 schannel: failed to receive handshake
curl -I https://rekor.sigstore.dev/      → 首轮 8s rc=28 超时；加长到 20s → HTTP=200
curl -I https://rekor.sigstore.dev/api/v1/log → 首轮 8s rc=28 超时；20s → HTTP=405
curl -I https://fulcio.sigstore.dev/     → 20s HTTP=404
curl -I https://freetsa.org/files/cacert.pem → HTTP=200
curl -I https://freetsa.org/files/tsa.crt    → HTTP=200
curl -I https://freetsa.org/files/tsa.pem    → HTTP=404
curl -I http://timestamp.sectigo.com/  → HTTP=404
```

补充观察（`curl -sS -I -v https://freetsa.org/index_en.php`）：`Trying 198.18.0.43:443` → `Established connection to freetsa.org (198.18.0.43 port 443) from 198.18.0.1` → `HEAD /index_en.php HTTP/1.1` → `< HTTP/1.1 200 OK`。`socket.getaddrinfo` 对 example/github/freetsa/digicert/rekor/fulcio 全部返回 `198.18.0.x`。⇒ 出口是 `198.18.0.0/15` 段（RFC 2544 基准测试保留段），**疑似透明代理/仿真网络，不是公网直连**；HEAD 拿到了真实 HTTP 头，但该路径对「第三方独立性」的影响**未验**。代理环境变量只有 `NO_PROXY`（长度 101，仅打印长度，未打印值）。

**判定**：
- 按题目给的判据「若不通，M3 就不是代价高而是本机不可行」——**本次是通的**（TCP 全 OK；freetsa 与 rekor 的 HEAD 有响应），所以 **M3 不是「本机不可行」**。
- 但**只到握手/HEAD 层**：TSA 的 `POST /tsr`、rekor 的 `POST /api/v1/log/entries`、inclusion proof、OIDC 取 token 全部**未验**（纪律禁止 POST 任何仓库派生内容）。`/tsr` HEAD 403 与 `/api/v1/log` HEAD 405 只说明「端点存在且不接受 HEAD」，**不等于写入可用**。
- 结论分两句写：**「本机网络使 M3 具备可达性，不是不可行」**；**「M3 的写入端点与真实 TSA 令牌未验，因此不能写成已可用」**。两者不等价，也不与「代价高」混淆。

### 1(d) git 仓库状态与 `git commit -S` 前置条件

实跑输出：
```
git rev-parse --is-inside-work-tree → true
git symbolic-ref --short HEAD       → main
git rev-parse HEAD                  → 26574589aa8401e8f3f2934680a1ea7109bafa2d
git log -1 --format='...G? %G? ...' HEAD → G_status=N, G_signer=, G_key=, G_fingerprint=
git verify-commit HEAD              → rc=1（无签名）
git config --show-origin --get-regexp '^(user\.(name|email|signingkey)|gpg\.|commit\.gpgsign|tag\.gpgsign)'
                                    → file:.git/config  user.name ZCode
                                      file:.git/config  user.email zcode@local
git config --get user.signingkey    → rc=1（未配）
git config --get gpg.program        → rc=1（未配）
git config --get gpg.format         → rc=1（未配，默认 openpgp）
git config --get commit.gpgsign     → rc=1（未配）
git config --get user.name / user.email → ZCode / zcode@local（已配）
git remote -v → origin https://github.com/Lawrence7y/ra2-campaign-forge.git (fetch/push)
git cat-file -p HEAD → tree d6c0baa36033fc3c52ba07988683a27ae5b38875 / parent e026498... /
                        author ZCode <zcode@local> 1793532933 +0800 / committer 同
GIT_COMMITTER_DATE='2000-01-01T00:00:00+0000' git var GIT_COMMITTER_IDENT → ZCode <zcode@local> 946684800 +0000
GIT_AUTHOR_DATE='1999-12-31T23:59:59+0000'   git var GIT_AUTHOR_IDENT   → ZCode <zcode@local> 946684799 +0000
git ls-files --error-unmatch -- lead/cert_realcheck_20261109/_cr_seal.json → rc=1 "did not match any file(s) known to git"
git status --porcelain -- .../_cr_seal.json → ?? lead/cert_realcheck_20261109/_cr_seal.json
git check-ignore -v -- .../_cr_seal.json → rc=1（未被忽略）
```

**`git commit -S` 的前置条件（给实跑依据，不凭记忆）**：
1. git 二进制支持 `-S`：本机 `git commit -h` 明列 `-S, --[no-]gpg-sign[=<key-id>]`（已实跑）。
2. 一个签名密钥 + 让 git 找到它。三条路：`user.signingKey` + `gpg.program`（openpgp，需 GPG **secret key** —— 本机 **0 把**）；或 `gpg.format=ssh` + `gpg.ssh.allowedSignersFile` + ssh-agent 中的签名密钥（本机 `.ssh` 无可断言的签名密钥，内容未读）；或 `gpg.format=x509` + `gpgsm`（`git help -c` 列出 `gpg.format`，本会话**未实跑 x509 路径，标未验**）。
3. `commit.gpgsign=true` 或命令上带 `-S`（`git help -c` 列出 `commit.gpgSign` / `tag.gpgSign` / `gpg.minTrustLevel`）。
4. 可用的 `user.name` / `user.email`（本仓库已配，但 `zcode@local` 不是可核验的外部身份）。
5. 被签文件必须先进索引（`git add`），否则 `-S` 只签一个不含该文件的 tree。

⇒ **`git commit -S` 在本机今天直接跑会失败**（缺密钥），原因是「本机缺密钥/缺配置」，**不是**「签名 commit 方案不可行」。装/配成本见 4(d)。注意 PATH：编排方 `which git=D:\Git\cmd\git.EXE`，而 `gpg` 在 `D:\Git\usr\bin\gpg.exe`，若用编排方 PATH 需显式 `git config gpg.program`。

---

## 2 第二步：M2 的真实代价

### 2(a) 最小 M2 路径：gpg detached signature（**完整命令序列；以下全部不执行，只给命令**）

前提：本机 0 把 GPG secret key，故第 0 步是**前置采购/批准步骤**，不是「现成密钥」。每一步都注明交互性、带外发布、产出文件。

```bash
# ── 步骤 0（前置；本任务未执行；需批准「生成长期身份凭证」）──────────────
# 0a 交互路径：会弹 pinentry，问姓名/邮箱/口令 → 【要交互】
gpg --full-generate-key
# 0b 非交互路径（推荐；【不需要交互】，但仍是生成密钥，本任务禁止）
gpg --batch --no-tty --pinentry-mode loopback --passphrase '' \
    --quick-generate-key 'seal-signer <seal-signer@example.invalid>' ed25519 sign 0
#    产出：~/.gnupg 下新增密钥材料（在写域之外）。耗时【未验】。
#    ★ 若改用 1(b)③ 里 Windows 证书库的现成私钥，则整步 0 可跳过，零生成、零安装。

# ── 步骤 1（只读检查，【无交互】，只产生 stdout）────────────────────────
gpg --batch --no-tty --list-secret-keys --with-colons
#    验收：至少一行 'sec:...'；否则中止，不许继续签。

# ── 步骤 2（导出公钥；【无交互】；产出公钥文件，不是密钥、不是 seal）──────
gpg --batch --no-tty --armor --export '<FPR>' \
    > 'D:/Project/ra2-campaign-forge/lead/<写域>/_sv_pubkey.asc'
'C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.EXE' -I -X utf8 -c \
    "import hashlib,pathlib; p=pathlib.Path(r'D:/.../_sv_pubkey.asc'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
#    产出：_sv_pubkey.asc + 一个 64-hex 公钥文件指纹。

# ── 步骤 3 ★【带外发布公钥指纹】───────────────────────────────────────
#    把 <FPR> 与 sha256(_sv_pubkey.asc) 在 t0（V1 首跑之前）发到 A 无写权的载体：
#    独立账号下的公开 gist / 邮件列表存档 / 第三方 append-only 日志 / ≥2 名具名见证人各留副本+回执。
#    【要人与组织交互，需批准】；本任务未执行、未联网发布。
#    ★ 若载体与 A 同账号（本机 origin 与 gh 登录都是 Lawrence7y），不满足 T8「A 写域之外」。

# ── 步骤 4（detached 签名；【无交互】；只读 _cr_seal.json，不改它）────────
gpg --batch --yes --no-tty --armor --detach-sign \
    --local-user '<FPR>' \
    --output 'D:/Project/ra2-campaign-forge/lead/<写域>/_sv_cr_seal.json.asc' \
    -- 'D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_cr_seal.json'
#    产出：_sv_cr_seal.json.asc（签名 sidecar，不是新 seal）。

# ── 步骤 5（复核；【无交互】；不需要本机私钥即可在别处用公钥复现）────────
gpg --batch --no-tty --verify \
    'D:/.../_sv_cr_seal.json.asc' \
    'D:/.../lead/cert_realcheck_20261109/_cr_seal.json'
#    验收：gpg: Good signature from ...；改 seal 任一字节后必须返回非 0。

# ── 步骤 6（可选，真正买「时间」；【设计，未执行，需批准向外部发送摘要】）──
openssl ts -query -sha256 -cert \
    -digest "$(sha256-of-canonical-seal-bytes)" -out 'D:/.../_sv_req.tsq'
curl -sS -H 'Content-Type: application/timestamp-query' \
     --data-binary '@D:/.../_sv_req.tsq' https://freetsa.org/tsr -o 'D:/.../_sv_resp.tsr'
openssl ts -reply -in 'D:/.../_sv_resp.tsr' -text
openssl ts -verify -queryfile 'D:/.../_sv_req.tsq' -in 'D:/.../_sv_resp.tsr' \
     -CAfile 'D:/.../cacert.pem' -untrusted 'D:/.../tsa.crt'
#    产出：.tsq / .tsr；★ 本任务未执行（铁律：不发任何本仓库内容/派生摘要到外网）。
```

产出物清单：`_sv_pubkey.asc`（公钥）、`_sv_cr_seal.json.asc`（detached 签名）、可选 `.tsq/.tsr`（时间戳令牌）、以及一条**带外记录**（不在本机）。**没有新 seal、没有新密钥被本任务创建**。

### 2(b) `git commit -S` 路径（**同样只给命令，不执行、不 commit、不 push**）

```bash
git config --local user.signingkey '<FPR>'                      # 写 .git/config，需批准
git config --local gpg.program 'D:/Git/usr/bin/gpg.exe'        # 编排方 PATH 需显式指定
git config --local commit.gpgsign true                         # 或只在命令上带 -S
git add -- 'lead/cert_realcheck_20261109/_cr_seal.json' 'lead/<写域>/_sv_pubkey.asc'
git -c user.name='ZCode' -c user.email='<可核验邮箱>' commit -S'<FPR>' -m 'seal v2: register pre-V1 commitment'
git verify-commit HEAD                                        # 验收：Good signature
git cat-file -p HEAD                                          # 看 tree/parent/author/committer 时间字段
git show --signature --format=fuller HEAD
# ★ 只有 push 才形成带外副本；本任务不 push。push 需批准。
```

**与 detached signature 相比：多了什么**
- **tree 级内容绑定**：签名覆盖整个 commit 对象（tree SHA-1 + parent + author/committer + message），不是单文件；tree/blob 由内容寻址，父子 commit 构成 DAG 因果偏序（`ORDERING_EVIDENCE.md:139` 已把 `④ git 跟踪` 判为「机制上部分可用」）。
- **现成校验入口**：`git verify-commit` / `git log --show-signature` / `%G?`；本会话实跑 `git log -1 --format='%G?'` 得 `N`（当前 HEAD 无签名）。
- **可形成带外载体**：`origin` 存在（`git remote -v` 实跑），`gh 2.93.0` 已登录且带 `repo`/`gist` scope ⇒ push/gist 是**可达**的第三方记录（但需 A 无写权的独立账号，见 3(b)）。

**少了什么 / 多出的风险**
- **不是单文件签名**：把 `_cr_seal.json` 单独交给第三方时，commit 签名不直接覆盖该文件字节；第三方要先顺着 tree→blob 推到该路径，或另出 detached sig。detached sig 直接覆盖文件字节，验收更短。
- **时间字段本身就是可写的**：实跑 `GIT_COMMITTER_DATE='2000-01-01T00:00:00+0000' git var GIT_COMMITTER_IDENT` → `946684800 +0000`，`GIT_AUTHOR_DATE` 同理 → `946684799 +0000`；`git cat-file -p HEAD` 显示 author/committer 时间戳就是 commit 对象里的明文头。**签名只证明「某人用某把 key 签了这个含该日期的字节串」，不证明那天真的发生过**。
- **仓库本地可重写**：未 push 的 commit 可 `rebase`/`--amend`/重置 HEAD，`ORDERING_EVIDENCE.md:139` 已记「本地 commit 时间可改、未 push 可 rebase/amend、无签名时不带身份」。
- **同域双改仍可能**：A 若持有 key，可重新生成一个新 commit 并同步改 seal 与校验器常量；T8 要求锚在 A 写域之外（`_os_ORACLE_SPEC.md:182`），单靠 commit 签不满足。
- **副作用面更大**：`git add` 写 `.git/index`、`git config` 写 `.git/config`、`commit` 写对象库，都在本任务写域之外；detached sig 只在写域产一个 `.asc`。

### 2(c) ★ 关键问题：签名之后「seal 早于 V1」变强了吗？逐条核

**先把命题拆开**：
- (P1) 「这份 seal 内容此后没被改」→ **签名确实解决**（密码级），前提：公钥指纹（信任锚）在 A 写域之外、且已被独立记录。
- (P2) 「seal 是什么时候产生的」→ **签名不解决**。证据：① `gpg --dump-options` 实跑含 `--faked-system-time`（GPG 签名时间由签名者控制）；② `GIT_COMMITTER_DATE` / `GIT_AUTHOR_DATE` 实跑可任意覆盖；③ `openssl cms -help` 含 `-no_signing_time`；④ `ORDERING_EVIDENCE.md:142` 判「本地时钟可改」，本机 `W32Time` 服务实跑为 `Stopped`（注册表 `NtpServer=time.windows.com,0x9`, `Type=NTP`）。⇒ 签名里的「时间」是**签名者写进去的一个字段**，不是可信时间源。
- (P3) 「seal 早于 V1」= `t0 < t2` → 需要一个**不受 A 控制的 t0 时间凭证**，且 **t2（V1 首跑）也必须有独立锚**，否则不等式的一端仍是可写本地时间。只有 TSA（或等价的第三方 append-only 日志 + 其自身带签名的时间）能给出 t0；只有另一个独立锚能给出 t2。

**对用户判断的裁定：方向正确，但一刀切过宽，须逐条拆。**

| 项 | 定义（`_os_ORACLE_SPEC.md:175-182`、`ORACLE_SPEC.md:112`） | M2 单独（签名 + 公钥指纹带外公布，**无 TSA**）能给什么 | 是否需要 TSA / 带外日志 |
|---|---|---|---|
| **T1** 作者身份可验证 | `ID_REG` 每条含 `adjudicator_id` + 认证材料；`H(ID_REG)` 在 V1 前**带外公布**，不在 A 写域 | **部分升密码级**：把内容绑定到一把 key（`%GK`/fingerprint 可复算）。但「这把 key = 那个真人」仍靠带外 `ID_REG` 预注册与机构认证；本机 5 张可用证书全自签 ⇒ 无第三方身份链 | 身份映射**靠制度**；不需要 TSA。但若要求「`ID_REG` 确在 V1 之前」，则仍需 t0 时间锚 |
| **T4** 标注时间早于 V1 | `t0 H(P) < t1 H(labels) < t2 V1 首跑`，三者时间凭证可比对，且 `H(labels)` 在 t2 前出现在**不受 A 控制**的载体 | **不能升密码级**。签名时间可伪造、commit 日期可写、本机 mtime/ctime 可写（§0.1 已复核）。签名只给「签过」，不给「何时签」 | **必须配 TSA（或等价第三方带签名时间）+ 独立 t2 锚**。用户对 T4 的判断**完全成立** |
| **T6** 作者与标注内容绑定（防挂名） | 每个 `adjudicator_id` 对**自己的**分片产出可核验认证材料（签名/回执），禁单一共享字符串 | **能升密码级**：逐分片 detached 签名正是 `T6` 定义里的「签名」，与「何时」无关 | **不需要 TSA**。用户对 T6 的断言**过宽** |
| **T8** 不可否认 / 抗同域双改 | 承诺哈希 + 标注包 + 校验器常量**至少三者之一**在 A 写域之外（带外签名 / 第三方存证 / 公证 / append-only 日志）；演练须 FAIL | **结构性一半能升**：带外公布的公钥指纹/带外签名使 A 无法「同步重写 seal + 常量 + 内容」后仍产出有效签名 ⇒ 抗同域双改接近密码级。`SEAL_CHRONOLOGY.md:279` 自己也承认「结构性能做到，不可否认的密码级做不到」 | **「抗同域双改」不需要 TSA；「不可否认」需要** —— 因为签名时间可回填，A 可事后补签并声称密钥失窃/签名在先；`ORACLE_SPEC.md:125` 明记「无 PKI 时不可否认性技术上为零」 |

**逐条对上游「M2 低代价把 T1/T4/T6/T8 升密码级」（`ORDERING_EVIDENCE.md:166`、`:150`、`SEAL_CHRONOLOGY.md:283`/`:325`/`:330`、`_os_ORACLE_SPEC.md:224`、`ORACLE_SPEC.md:132`）核**：

1. `ORDERING_EVIDENCE.md:150` 写「真正把时间做成密码级事实的是 M2 ... 或 M3」——**这一句与同件 `:166` 及 `ORACLE_SPEC.md:133` 自相矛盾**：`:166` 明确「M3 时序成为可验证事实」，`ORACLE_SPEC.md:133` 明确「M3（PKI+RFC3161+透明日志）把时序做成可验证事实」。`SEAL_CHRONOLOGY.md:141` 也写「M3 ... 唯一能把『确系事前/确系事后』判成密码级事实的路径」。⇒ **`:150` 的 M2 归属应改判：M2 不产生可信时间**。
2. `SEAL_CHRONOLOGY.md:325`/`:330` 的「一次升到密码级」对 **T6 成立、T1 部分成立、T8 只对结构性一半成立、T4 不成立**。`SEAL_CHRONOLOGY.md:279` 已给出正确的分层，但 `:283`/`:325`/`:330` 未沿用 ⇒ 台账内部存在**措辞不一致**，本件只登记，不改只读件。
3. **对「seal 早于 V1」这个具体命题**：用户判断**成立**，且比他说的更强 —— 即使加了 TSA，也还必须有**独立的 t2（V1 首跑）锚**，且 `H(P)` 的公布必须发生在 V1 之前（`ORDERING_EVIDENCE.md:165` 乙方案：事后补公布只能证明「从现在起没改」）。`ORDERING_EVIDENCE.md:171` 的总判断（三方案无一能救本案）**维持不变**：本案是**过去没做**，不是**以后做不到**。
4. **另有一条不可省**：`ORACLE_SPEC.md:123`/`:161`、`SEAL_CHRONOLOGY.md:144` 明记「签名 / PKI / TSA 把谁、何时、哪份内容绑定到人，但买不到签名前的所见所闻（内容绑定 ≠ 认知状态绑定）」。⇒ 即便 M3 全上，「标注者未见 V1 输出」仍**只能靠制度**。因此 `ORDERING_EVIDENCE.md:166` 的「M3 真正不可否认」对**时间**成立，对**盲/独立**不成立。

**M2 真实代价（给数字，不给「低」）**：
- 工具安装：**0 分钟、0 次安装**（`gpg 2.4.9`、`openssl`（两套）、`curl`、`git`、`gh`、`powershell` 全部已在；见 1(a)）。
- 密钥：GPG 路径 **1 次密钥生成**（生成耗时**未验**，本任务禁止），交互 1 次（若走 batch 则 0 次交互）；**Windows 证书库路径 = 0 次生成、0 次安装**（5 张现成带私钥代码签名证书）。
- 命令数：**5–6 条**（2(a) 步骤 1/2/4/5 + 步骤 3 的发布）。
- 人力/带外：**1 次带外发布**（需要 A 无写权的载体；同账号 gist 不算）+ **≥2 名具名见证人各留副本**（`ORACLE_SPEC.md:131`、`:309`）。
- 组织成本：公钥指纹/证书身份的**预注册与身份绑定**，1 次审批。
- 不可压缩的人力（与 M1/M3 共享）：`SEAL_CHRONOLOGY.md:329`/`:333`、`ORACLE_SPEC.md:309` 记 **302 项双盲标注 ≈50.33 人时，端到端 60–95 人时 / 5–8 工作日**，M2 **一点也省不掉**。⇒ 「M2 低代价」这个说法**只在「技术接入」这一窄层成立**，在「整套可交付的独立 ORACLE」层不成立。

---

## 3 第三步：M3 的真实代价与不可行点

### 3(a) RFC3161 实装前提逐条判

| 前提 | 判定 | 实跑依据 |
|---|---|---|
| **CA 证书链**（验证 TSA 签名） | **本机可做**（未执行） | 两套 `openssl ts -verify` 均支持 `-CAfile / -untrusted / -CApath / -CAstore`；本机已有 `/mingw64/etc/ssl/cert.pem`、`/mingw64/etc/ssl/certs`、`D:/Anaconda/Library/ssl/cacert.pem`，Python `certifi` 可导入（`import ssl,certifi` rc=0）；freetsa `https://freetsa.org/files/cacert.pem` HEAD **200**、`.../tsa.crt` HEAD **200**、但 `.../tsa.pem` 是 404。本任务**只 HEAD，未下载、未做 `-verify` 实跑**，故「链能否在本机验证成功」标**未验**。freetsa 是自签 CA ⇒ trust anchor 必须随 seal 一并公布，否则第三方无法复验 |
| **时间源** | **本机不可做（服务停）/ 需运维启用**；但 **TSA 路径不依赖本机 NTP** | `w32tm /query /status` 在 Git Bash 被路径转换破坏，输出 `命令 D:/Git/query 未知`（**未取到 status，标未验**）；改用注册表读：`NtpServer=time.windows.com,0x9`、`Type=NTP`，但 `(Get-Service W32Time).Status = Stopped`。本机 `date -u` = `2026-11-09T14:56:30Z` 与 example.com 的 `Date: ... 14:54:11 GMT` 一致到分钟（只作旁证，不作时间源证据）。RFC3161 的 `genTime` 由 TSA 提供，本机时钟只用于「比较」，所以**TSA 时间本身可做**；「本地可信时间」需管理员启用 W32Time（**需批准，未执行**） |
| **联外网** | **本机可做（握手/HEAD 层）**；**写入端点未验** | 1(c) 全表：`freetsa.org:443`、`timestamp.digicert.com:80/443`、`timestamp.sectigo.com:80`、`rekor.sigstore.dev:443`、`fulcio.sigstore.dev:443` 全 `TCP_OK`；freetsa `/` 302、`/tsr` 403（HEAD 被拒，符合只收 POST）、`cacert.pem`/`tsa.crt` 200；rekor `/` 200（20s）、`/api/v1/log` 405（20s）。`https://timestamp.digicert.com/` HEAD rc=35 握手失败，但 `http://` 404 可达 ⇒ DigiCert 的 HTTPS 路径**未验**。DNS 全落 `198.18.0.x`，`curl -v` 显示经 `198.18.0.1` 出口 ⇒ 第三方独立性受该路径影响，**未验** |
| **需采购** | 分类判 | ① **免费 TSA（freetsa）无需采购**，但无 SLA、无法律级不可否认、CA 自签；② **商业 TSA 配额 / 自建 TSA（TSA 证书 + 私钥 + HSM + 审计）需采购 + 安全团队批准**；③ **自建透明日志运维需采购/运维**；④ **OIDC 身份（fulcio/sigstore）需账号与批准**。`fulcio.sigstore.dev` HEAD 404 只说明根路径无内容，签发端点**未验** |
| **客户端工具** | **本机可做，0 安装** | `openssl ts -query`（两套都支持 `-data/-digest/-sha256/-cert/-out`）、`curl --data-binary/-H`、`openssl ts -reply -text`、`openssl ts -verify` 全部在机；`certutil -get-sth` / `-get-sth-consistency`（CT STH 读取）也在机，但它是**CT 日志读取客户端，不是日志写入器**，不能替代透明日志 |

### 3(b) ★ 透明日志（append-only）最要紧的一条

**判断：若日志也在本机，它就不是带外载体，与 CLI DB 同级 —— 这是「方案本身不可行」，不是「本机缺工具」。装任何工具、升级任何数据库都救不了。**

依据（逐条实读）：
- `ORDERING_EVIDENCE.md:140` 把 CLI 会话库 `db.sqlite` 判为「**本地 sqlite 可写、无签名、非密码学强制**」，并实跑给出 `count=622897 < max(rowid)=648627`、`182 次 time_created 倒退`、有 `time_updated` 列 ⇒ **不是 append-only 日志**；结论「可证同一会话内的记录顺序」，**不能证绝对物理时刻、不能判认知状态**。
- `ORDERING_EVIDENCE.md:171`、`SEAL_CHRONOLOGY.md:132`：「本会话未找到任何独立的（带外的、不受本地写域控制的）时间证据」。
- `_os_ORACLE_SPEC.md:182`（T8）、`ORACLE_SPEC.md:108`（C2）、`SEAL_CHRONOLOGY.md:269`：判据是「承诺哈希 + 标注包 + 校验器常量**至少三者之一**位于 `A` 写域之外」，且「至少一个锚的写 ACL 不含 A」是**确定性判断**。
- 推理：本机日志与产物共享 ① 同一可写文件系统；② 同一管理员/同一账号；③ 同一本地时钟（`W32Time` Stopped、mtime/ctime 可写，§0.1 已实证）；④ 同一 A 写域。⇒ A 若要伪造，可同步改产物 + 日志 + 常量 + 日志时间字段，与改 `db.sqlite` 无任何区别。**append-only 只是「难改」，不是「不能改」，更不是「A 无写权」**。即便换成 immudb / 触发器只追加 / WORM 磁盘，只要 admin 凭据与介质在 A 手里，仍不满足 T8。
- `CERT_REAL_CHECK.md:509`（经 `SEAL_CHRONOLOGY.md:274`/`:344` 引用）现状「同域双改可造 PASS」正是这个失效模式的实证（本任务**未重跑该演练**，只读纪律，沿用既有输出件）。

**⇒ 必须外部化**：`rekor.sigstore.dev`（本次 HEAD 可达）、CT log、独立机构存证/公证、**独立账号**下的公开只读 gist/邮件列表存档。判据不是「日志不可改」，而是「**日志的写 ACL 不含 A，且其时间由日志运营方签名**」。这一条与工具无关，所以是**方案级的必要条件**；本机不缺实现 append-only 的技术，缺的是**一个不在自己手里的载体**（属于组织/采购，不是技术）。

### 3(c) 本机现在就能做的最小 M3（命令集；**未验**）

免费 TSA 选 **`freetsa.org`**（本次 TCP_OK + `/` 302 + `/tsr` HEAD 403 + `cacert.pem`/`tsa.crt` HEAD 200，是唯一在本次探测中把「端点 + CA 链」都探到的）。

```bash
# ① 生成 RFC3161 查询（只含 seal 的 SHA-256 digest；-cert 要求 TSA 回带证书）
'D:/Anaconda/Library/bin/openssl.EXE' ts -query -sha256 -cert \
    -digest '<64hex = sha256(canonical_seal_bytes)>' \
    -out 'D:/Project/ra2-campaign-forge/lead/seal_v2_feasibility_20261109/_sv_req.tsq'

# ② POST 到免费 TSA（★ 本任务未执行：会向外部发送仓库派生摘要，需批准）
curl -sS -H 'Content-Type: application/timestamp-query' \
     --data-binary '@D:/.../_sv_req.tsq' \
     https://freetsa.org/tsr \
     -o 'D:/.../_sv_resp.tsr'

# ③ 读 genTime（本地，无网络）
'D:/Anaconda/Library/bin/openssl.EXE' ts -reply -in 'D:/.../_sv_resp.tsr' -text

# ④ 离线验证（CA 链需先下载；本次只 HEAD，未下载）
openssl ts -verify -queryfile 'D:/.../_sv_req.tsq' -in 'D:/.../_sv_resp.tsr' \
     -CAfile 'D:/.../cacert.pem' -untrusted 'D:/.../tsa.crt'
```

产出：`_sv_req.tsq`（DER 查询，含 `messageImprint` = seal 的 SHA-256）、`_sv_resp.tsr`（RFC3161 令牌，含 TSA 签名的 `genTime` + `messageImprint` + TSA 证书链）、`-text` 的 `genTime` 文本、验证返回码。

**如实写「未验」的部分**（不得写成已可用）：
- **POST 往返未验**：纪律「不发任何本仓库内容到外网（连通性探测只做握手/HEAD）」。`/tsr` 的 403 是 HEAD 被拒，**不能**推断 POST 会返回有效令牌。
- **CA 链下载与 `-verify` 未验**：只做了 `cacert.pem`/`tsa.crt` 的 HEAD 200，未下载、未校验证书链、未跑 `openssl ts -verify`。
- **genTime 可信性未验**：没拿到任何真实令牌，无法判 TSA 时钟、策略 OID、证书有效期。
- **透明日志写入未验**：rekor `/` 200、`/api/v1/log` 405（20s 超时下）只证明端点活着；`/api/v1/log/entries` 的 POST、inclusion proof、OIDC token 全部未验；`cosign` 未安装。
- **第三方独立性未验**：DNS 全落 `198.18.0.x`、出口 `198.18.0.1`，疑似透明代理；该路径是否削弱「带外」属性未验。
⇒ **结论：命令集已具备、握手/HEAD 可达，M3 不是「本机不可行」；但实取时间戳标 `UNVERIFIED`，不能据此宣布时序已证。**

---

## 4 第四步：下一代 seal 的最小可行方案（本任务真正交付）

配套文件：`_sv_seal_v2.schema.json`（JSON Schema Draft 2020-12 级格式定义）、`_sv_build_skeleton.py`（生成骨架，**未执行**）、`_sv_verify_skeleton.py`（复核骨架，**未执行**）。三者均不生成 seal、不生成密钥、不联网。

### 4(a) 格式定义与两条骨架

**核心不变量**
- `CANON(x) = json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',',':')) + "\n"`，UTF-8 编码；`H(x) = hashlib.sha256(CANON(x)).hexdigest()`。沿用 `_cr_build_seal.py:105` 的 `ensure_ascii=False, indent=2, sort_keys=True` 排序键传统，但改用紧凑分隔符使字节唯一。
- **不自引用**：seal 文件内**不含自身 sha**（`ORDERING_EVIDENCE.md` 已实跑 `seal_self_sha_in_V1=[]`，且自指哈希逻辑上不可能）。对外承诺的 64-hex = `sha256(seal 文件的原始字节)`，第三方对**收到的字节**重算即可，不需要本机密钥。
- **签名是 detached**，签的字节 = seal 文件原始字节；验签只需**带外公布的公钥**（或证书），不需要本机私钥。
- **签名不覆盖签名自身**，避免循环；`signers[].signature_sha256` 只是 sidecar 的指纹，不参与被签字节。

**顶层结构（Schema 见 `_sv_seal_v2.schema.json`）**：`seal_version` / `subject`（沿用 `_cr_seal.json` 的 `items[].file_sha256 / bytes / evidence_span_sha256 / evidence_lines / anchor`，实读 `_cr_seal.json:1-40` 与 `:105` 的序列化）/ `subject.items_sha256` / `time_anchors`（≥2 条不同源且 ≥1 条带外）/ `commitment`（t0 的 `H(P)` 与载体定位）/ `predicate_run_anchor`（**独立 t2 锚**）/ `signers`（逐分片）/ `payload_sha256` / `provenance`（明确标注哪些层靠制度）。

**四条要求的落地**
| 要求 | 实现 |
|---|---|
| 内容绑定 | `subject.items[]` 每项 `path / sha256 / bytes / evidence_lines / evidence_span_sha256`，`subject.items_sha256 = H(items)`；可选 `predecessor_seal_sha256` 做哈希链（内容因果偏序，`ORDERING_EVIDENCE.md:275` ②） |
| 时间绑定 ≥2 不同源 | `time_anchors[0] = {kind:"fs_stat", writable:true, trust:"weak_local_metadata"}`（本机 stat，§0.1 已证其不可作定序强证据，只作弱旁证）；`time_anchors[1] = {kind:"rfc3161", tsa_url, tsq_sha256, tsr_sha256, gen_time_utc, tsa_cert_sha256, tsa_ca_sha256, trust:"third_party_time"}`；或 `kind:"transparency_log"`。TSA 不可用时的**降级**载体 = `kind:"witness_archive"`（独立账号 gist / 邮件列表 Date 头 / ≥2 名具名见证人回执），必须显式 `trust:"institutional_only"`，**不许标成密码级** |
| 不可回改 | `signers[].detached_signature`（gpg detached 最低；本机可改用 Windows cert store 的 `SignedCms` detached，零生成）+ 带外公布的公钥指纹 + 带外公布的 `H(seal_bytes)` |
| 可复核 | `_sv_verify_skeleton.py` 只吃「seal 文件 + 原文件 + 公钥/证书 + .tsr + CA 链」；重算每个 `file_sha256/bytes`、重算 `H(payload)`、验签、验 TSA、查 ≥2 源、查 t0<t2；**不需要本机密钥**；任一必需锚缺失即显式 `FAIL`（不许 silent pass） |

**★ 一条容易被漏掉、但决定成败的设计**：`t0 < t2` 的**两端都要锚**。`predicate_run_anchor` 必须由**非 A 方**在 V1 首跑时产生（另一条 TSA 令牌或透明日志条目）。只锚 t0 而 t2 仍是本地 mtime，等于把不等式的一端放回可写元数据，`ORDERING_EVIDENCE.md:165` 的「事后补公布只证从现在起未改」会再次生效。

生成骨架 `_sv_build_skeleton.py` 要点（完整可读代码在该文件，本任务**未执行**）：只读 `subject` 文件 → `hashlib` 逐件算 → 采集 `os.stat` 三时间并显式标 `writable:true` → 组装 `payload` → 写 seal 字节 → 用**已存在**的 key 做 detached 签（若无 key 直接 `abort`，**绝不生成密钥**）→ 可选接 TSA → 全程不写 subject 文件、不改只读域。复核骨架 `_sv_verify_skeleton.py` 要点：只用公钥；逐件重算哈希与字节数；`gpg --verify` 或 `SignedCms.CheckSignature`；`openssl ts -verify`；检查 `len(time_anchors)>=2` 且 `>=1` 条的 `carrier_outside_A_write_domain == true`；检查 `t0 < t1 < t2`；缺项/不符 → `FAIL` 并列出 `missing[]`。

### 4(b) 逐条对照 `_fnr_check.py:73-76` 四项要求

实读 `_fnr_check.py:73-76`（实跑输出见 `_sv_probe_readonly.py` E 段）：
```
73: # Let ORACLE: I -> {0,1} be a ground-truth label produced BEFORE V1 is run,
74: # by an adjudicator who does not see V1's outputs and did not author V1,
75: # with a published SHA256 seal. truth=1 means "the required semantic content
76: # is genuinely delivered in this artifact", judged role-by-role.
```

| 要求 | 这套 seal 能满足吗 | 依据 / 仍必须靠制度的部分 |
|---|---|---|
| **① BEFORE V1 is run** | **部分能，且是这套方案的主要增量** | 技术上：`H(P)` 在 t0 带外公布 + TSA `genTime` + **独立的 t2 锚**，使 `t0<t1<t2` 可复算（`_os_ORACLE_SPEC.md:178` T4、`ORACLE_SPEC.md:112`）。但 seal 只能证明「**承诺/封印字节**早于 V1」，不能证明「ORACLE 标签的语义判断」早于 V1 —— 标签须走 commit-then-reveal 在 t1 交 `H(labels)`（`ORDERING_EVIDENCE.md:165` 乙）。TSA POST 未获批准时，此项降级为制度级，**必须标 `UNVERIFIED`，不许写成已证** |
| **② 未见 V1 输出** | **完全不能靠 seal** | `ORACLE_SPEC.md:123`（「读没读过，从产物上不可判定」）、`:161`（「签名 / PKI / TSA ... 买不到签名前的所见所闻」）、`:163`（「未见本身为制度性假设，非技术可证事实」）、`SEAL_CHRONOLOGY.md:144`（「无论哪条都不能判标注者没看过答案」）。只能靠 `INPUT_MANIFEST ∩ V1_OUTPUTS = ∅` + ACL 隔离日志 + 双盲分片 + ≥2 具名见证人（T3/T5，`_os_ORACLE_SPEC.md:177/:179`） |
| **③ 非 V1 作者** | **部分能** | 技术可核：逐分片签名把内容绑定到 key（T6）、`H(ID_REG)` 带外预注册（T1）、`set(B_ids) ∩ set(A_ids) == ∅` 集合判据（T2，`_os_ORACLE_SPEC.md:176`）。**仍靠制度**：key→真人的映射、无共同汇报线、账号盗用/代签/挂名（`ORACLE_SPEC.md:122`）；本机可用证书全自签，身份链为零，格外需要机构预注册 |
| **④ 已公布 SHA256 seal** | **能完全满足（这是主产出）** | 64-hex `sha256(seal_bytes)` 在 t0 之前公布到 A 无写权载体；第三方对收到的字节重算比对；加 detached 签名 + TSA 后「已公布 + 内容绑定 + 不可回改」全为密码级。**条件**：载体与 A **不同账号/不同组织**（本机 `origin` 与 `gh` 登录都是 `Lawrence7y`，同账号 gist **不算**带外 —— 见 3(b)）；且公布确在 V1 之前 |

**额外边界（不属四项但必须写）**：这套 seal **不修** `ORACLE_SPEC.md:110`（C4 全覆盖 FAIL：5/302、coverage 只在 detail）、`:108`（C2 常量与封印同域）、`SEAL_CHRONOLOGY.md:333` 点名的工程缺口（给 `no_relaxation_check` 增 `artifact_text` / `seal_path` 两槽、把 coverage 做成真 FAIL）。seal 是**证据格式**，不是**标注流程**；302 项双盲标注的 50.33–95 人时一点不省。

### 4(c) 「什么时候该用哪一档」判据

| 档 | 触发条件 | 配什么方案 | 能声称什么 / 不能声称什么 | 代价（本次实跑口径） |
|---|---|---|---|---|
| **日常自检** | 同一信任域内改完文件想确认没被自己改坏；不对外 | 现有 `_cr_seal.json` + `hashlib` 逐件重算 + `os.stat` 三时间 | 只能声称 `INTEGRITY_OK_BUT_UNCONFIRMED`（`SEAL_CHRONOLOGY.md:348/:350`）。**不得**声称独立/预注册/不可否认；ctime 在本机**不得**用于定序（§0.1） | 0 安装、0 命令的新增；已有脚本 `_cr_build_seal.py:89/:105`、`_cr_real_verify.py` |
| **对外交付** | 要给别人一份「我确实封了这份内容」的凭证，但无法律争议预期 | `seal_v2` + **detached 签名**（gpg 或本机 Windows cert store `SignedCms`）+ 公钥指纹带外公布 + `H(P)` 在 t0 的 commit-then-reveal + ≥2 名具名见证人各留副本 | 可声称「内容密码级绑定 + 不可回改 + 带外承诺可复核」。**不得**声称时序密码级（无 TSA）、不得声称盲/独立 | 工具 0 安装；密钥：走证书库 0 生成 / 走 GPG 1 次生成（耗时未验）；5–6 条命令；1 次带外发布 + 1 次审批；人力 50.33–95 人时**不省** |
| **需要不可否认** | 会面临「你事后补的吧」的争议，或外部审计/交付验收 | 上一档 **+ RFC3161 TSA 令牌（freetsa 或商业 TSA）+ 第三方 append-only 透明日志（rekor / CT / 机构存证）+ 独立 t2 锚 + 预注册 `ID_REG`/`A_REG`/`P`/κ/覆盖=1.0 + ACL 日志 + ≥2 名真第三方** | 可声称「`t0<t1<t2` 时序为可验证事实、时间不可否认」。**仍不得**声称「未见 V1 输出 / 标注独立」已证（只能写制度担保）；不得把 `UNCONFIRMED` 升格 PASS | 工具 0 安装（openssl/curl/gh 已在）；**需批准**：TSA POST、CA 链下载、OIDC 身份、外部日志写入、W32Time 启用；**需采购**：商业 TSA / 自建 PKI+HSM / 独立载体与存证服务；人力 60–95 人时 + 5–8 工作日（`SEAL_CHRONOLOGY.md:329`、`ORACLE_SPEC.md:309`）。POST 与 inclusion proof **未验** |

### 4(d) 「装什么、装多久、要谁批准」（对真实缺口给清单）

**先明确：本任务的总结论不是「本机缺工具所以做不到」**。整机已具备 `gpg 2.4.9 / openssl×2（含 ts+cms）/ curl / git 2.54 / ssh-keygen×2（-Y sign）/ powershell（SignedCms）/ certutil / gh 2.93（已登录）/ python 3.12（certifi）`，**核心路径 0 安装**。缺的是**密钥/载体/授权**，不是工具。逐项列真实缺口：

| 缺口 | 装什么 | 装多久 | 要谁批准 | 是否阻塞 |
|---|---|---|---|---|
| `gpg` 无 secret key | **不用装**（`gpg` 已在）。要么生成 1 把（1 次非交互命令），要么改用本机 5 张带私钥代码签名证书 + `SignedCms` ⇒ **0 装 0 生成** | 生成耗时**未验**（本任务禁止生成密钥） | 生成长期身份凭证需**安全/项目负责人批准**；用现有证书需**证书使用授权** | 不阻塞方案，只阻塞「今天立刻签」 |
| `minisign / signify / cosign / age / gpg2 / signtool` 不存在 | **不必装**。若坚持：minisign/cosign 各 1 个二进制（官网或 GitHub Releases）、`age` 1 个二进制 | **未验**（未下载、未安装，纪律禁止安装工具） | 需**运维/安全批准** + 网络下载批准 | **不阻塞**（gpg / ssh-keygen -Y / SignedCms / openssl cms 已全覆盖） |
| TSA 写入（POST） | **不用装**（`openssl ts -query` + `curl --data-binary` 已在） | 一次往返；**未验**（未 POST） | **必须批准**：向外部发送仓库派生摘要；并允许出口到 `freetsa.org:443` | 阻塞「时序密码级」这一层 |
| TSA CA 链 | **不用装**，需下载 `cacert.pem` / `tsa.crt`（HEAD 已 200） | 2 次 GET；**未验** | 需**外部下载批准** | 阻塞 `openssl ts -verify` |
| 透明日志写入 | 不装 `cosign` 也可走 rekor REST（curl POST）；用 CLI 才需装 `cosign` | 安装时长**未验**；POST 往返**未验** | 需 **OIDC 身份 + 外部写入批准** | 阻塞「第三方 append-only 锚」 |
| **A 无写权的带外载体** | **不是工具，是账号/组织隔离**：独立账号 gist、邮件列表存档、机构存证、公证、rekor | **组织流程，非可测时长**（本任务未估） | **需项目/安全负责人批准新建独立账号或采购存证服务** | **这是唯一真正阻塞可交付性的缺口**，且与技术无关（3(b)） |
| 本机可信时间 | 不用装，启用 `W32Time`（当前 `Stopped`） | 未执行 | **管理员批准** | 不阻塞 TSA 路径（genTime 来自 TSA） |
| 自建 TSA / 自建透明日志 + HSM | 需采购 PKI/HSM/审计与运维 | **未估**（超出本任务范围） | **安全 + 采购 + 管理层** | 只在「不用任何第三方托管」时才需要 |

---

## 5 第五步：结论与边界

### 5(a) 一句话

**部分能**：下一次 seal **能做到「可验证」**——内容完整性、逐分片身份/密钥绑定、带外承诺与不可回改可在**本机今天**用现有工具做到密码级；若再补齐 RFC3161 TSA 令牌、**独立的 V1 首跑 t2 锚**、以及 A 无写权的带外载体，「seal 早于 V1」也能做成密码级可验证事实；**但「标注者未见 V1 输出 / 标注独立」永远不能靠 seal 技术证明，只能靠制度**（`ORACLE_SPEC.md:123/:161`、`SEAL_CHRONOLOGY.md:144`）。条件：① `H(P)`/`H(seal_bytes)` 在 V1 之前发布到 A 无写权载体；② 每条带 detached 签名且信任锚带外；③ TSA + 独立 t2 锚；④ 逐层标注哪些是制度担保、哪些是密码级；⑤ TSA POST / CA 链 / rekor 写入获批准并实跑验证（当前**未验**）。

**同时明确**：本案**旧** seal 的结论**不变**——`ORDERING_EVIDENCE.md:171` / `SEAL_CHRONOLOGY.md:350` 的 `前提层不成立` / `INTEGRITY_OK_BUT_UNCONFIRMED` 维持；「过去没做」≠「以后做不到」。

### 5(b) 落地顺序与验收判据

| # | 做什么 | 验收判据（可实跑） |
|---|---|---|
| 0 | 能力清点（**本任务已完成**） | 1(a)–(d) 每条有实跑命令+输出；7 件基线 `MATCH_BASELINE=True`；`HEAD` 未变；写域只有 `_sv_` 前缀且无 `.sig/.asc/.key/ seal*.json/.tsr` |
| 1 | **选信任根**（0 安装） | 二选一并落文：Windows cert store 现成代码签名证书（`Get-ChildItem Cert:\CurrentUser\My \| ? HasPrivateKey` 非空 —— 本任务已实跑 7/7 True、其中 5 张代码签名）或申请批准生成 GPG 密钥；产出「公钥/证书指纹 + 该指纹的带外公布位置」，且该位置写 ACL 不含 A |
| 2 | **冻结格式与 canonicalization** | 写死 `CANON`/`H` 与 `_sv_seal_v2.schema.json`；用**纯样例对象**（非真实 seal）验证「同一对象两种键序 → 同一 digest」相等；验证 seal 内不含自身 sha |
| 3 | **t0 带外承诺** | 在 V1 首跑**之前**，独立载体上出现 `H(P)` 与 `H(seal_bytes)` 的 64-hex；该记录带不受 A 控制的时间（TSA `genTime` 或第三方 Date 头）；第三方用 `hashlib` 重算相等，且能在 A 账号之外取到该记录 |
| 4 | **生成 `seal_v2` + detached 签名** | 每个覆盖文件 `sha256/bytes` 重算全 match；`gpg --verify`（或 `SignedCms.CheckSignature`）在**只有公钥**的环境返回 0；改 seal 任一字节返回非 0 |
| 5 | **TSA + 透明日志**（需批准） | `openssl ts -verify` 返回 0 且 `genTime` 落在 `t0..t2`；rekor 返回可查 entry + inclusion proof；**若 POST 未获批准，整步标 `UNVERIFIED`，不得把第 4 步写成时序已证** |
| 6 | **独立 t2 锚**（最易漏） | V1 首跑时刻由非 A 方产生另一条 TSA/日志锚；`t0 < t1 < t2` 由两条独立第三方时间凭证复算成立。缺此项 ⇒「早于」不成立 |
| 7 | **第三方复核脚本** | 不需任何私钥；缺签名 / 缺带外锚 / 缺 t2 锚 / 文件哈希不符 / `time_anchors<2` 任一即显式 `FAIL`；**同域双改演练必须 FAIL**（对照 `CERT_REAL_CHECK.md:509` 现状 PASS，`SEAL_CHRONOLOGY.md:274`） |
| 8 | **制度层并行** | `ID_REG`/`A_REG`/`P`/κ 门槛/覆盖=1.0/ACL 日志/≥2 具名裁决者/302 项全覆盖 全部预注册留痕；「未见 V1 输出」显式写为**制度性假设** |
| 9 | **结论表述** | 逐层分别写，T1–T8 逐条报状态，未验项标 `UNVERIFIED`；不得把 `INTEGRITY_OK_BUT_UNCONFIRMED` 升格为 PASS（`SEAL_CHRONOLOGY.md:352`） |

### 5(c) 这一步判不了什么（如实列）

1. **TSA POST 往返、`genTime` 可信性、freetsa CA 链能否在本机 `openssl ts -verify` 成功** —— 只做 HEAD（`/tsr` 403、`cacert.pem`/`tsa.crt` 200），未下载、未 POST、未验证 ⇒ **未验**。
2. **透明日志写入端点 / inclusion proof / OIDC 签发** —— rekor `/` 200、`/api/v1/log` 405（20s 超时下）；`fulcio.sigstore.dev` 根 404 ⇒ 写入链路 **未验**。
3. **`198.18.0.x` 出口到底是什么** —— `getaddrinfo` 全落该段、`curl -v` 显示 `from 198.18.0.1`；是否透明代理/仿真网络、是否削弱第三方独立性 ⇒ **未验**。
4. **`~/.ssh/lightsail-us-east-2.pem` 内容与是否可作签名密钥** —— 按纪律只列文件名，未读内容 ⇒ **未验**。
5. **Windows 证书库里 5 张代码签名证书能否成功对任意字节产出 detached CMS 签名** —— 只 `Add-Type` 加载了 `SignedCms`/`CmsSigner` 类型并确认 `Set-AuthenticodeSignature` 存在，**未签任何字节** ⇒ **未验**。
6. **生成 GPG 密钥的实际耗时** —— 纪律禁止生成密钥，未实跑 ⇒ **未验**（不给估计秒数）。
7. **本机时钟是否与 UTC 真实同步** —— `W32Time` 服务 `Stopped`；`w32tm /query /status` 在 Git Bash 被路径转换破坏（`命令 D:/Git/query 未知`），未取到 status ⇒ **未验**。
8. **`NtSetInformationFile` 类接口改 ctime** —— 沿用 `ORDERING_EVIDENCE.md:112` 的「未实跑，未验」，本任务同样**未验**。
9. **同域双改演练** —— `CERT_REAL_CHECK.md:509` 现状 PASS 沿用既有输出件，本任务**未重跑**（只读纪律，`SEAL_CHRONOLOGY.md:275` 亦标未独立复跑）。
10. **「标注者未见 V1 输出」这一认知状态** —— 产物上不可判定（`ORACLE_SPEC.md:123/:163`、`SEAL_CHRONOLOGY.md:144`）⇒ 判不了，只能制度担保。
11. **旧 seal 的时间与本案结论** —— 已由 `ORDERING_EVIDENCE.md:171` / `SEAL_CHRONOLOGY.md:350` 定论为 `前提层不成立` / `INTEGRITY_OK_BUT_UNCONFIRMED`；本任务不重开、不翻案。
12. **安装 minisign/cosign 的实际耗时、审批周期；自建 TSA/透明日志的采购成本与工期** —— 未安装、未采购、超出本任务范围 ⇒ **未验 / 未估**。
13. **`git` 的 `gpg.format=x509` + `gpgsm` 签名路径** —— `git help -c` 只列出配置键，本会话未实跑该路径 ⇒ **未验**。
14. **DigiCert 的 HTTPS TSA 路径** —— `https://timestamp.digicert.com/` HEAD `rc=35` 握手失败，`http://` 404 可达 ⇒ HTTPS 路径 **未验**（故最小 M3 选 freetsa）。

---

## 6 纪律与副作用登记

- 只读域（两件台账、`ordering_evidence_20261109/`、`cert_realcheck_20261109/`、`seal_chronology_20261109/`、`oracle_spec_20261109/`、`falsifiable_no_relax_20261109/`、`gate_r9sem_20261109/`）**只读**：收尾二次复算 7 件基线指纹 `MATCH_BASELINE=True` ×7，并补算 5 件被引台账指纹（§0）。
- 唯一写域 `lead/seal_v2_feasibility_20261109/`，全部 `_sv_` 前缀：`_sv_probe_readonly.py`（已执行）、`_sv_net_probe.py`（已执行）、`_sv_FEASIBILITY.md`（本件）、`_sv_seal_v2.schema.json`（格式定义，**不是 seal 实例**）、`_sv_build_skeleton.py` / `_sv_verify_skeleton.py`（骨架，**未执行**）。
- **未生成任何新 seal、未安装任何工具、未生成任何密钥、未 commit、未 push**；`git rev-parse HEAD` 仍 `26574589aa8401e8f3f2934680a1ea7109bafa2d`。
- **写域产物按内容分类判定（非按文件名）**：`find -type f \( -name '*.sig' -o -name '*.asc' -o -name '*.p7s' -o -name '*.key' -o -name '*.tsr' -o -name '*.tsq' -o -name '*.pem' -o -name '*_pubkey*' -o -name '*_published*' \) -print` 空输出（无任何签名/密钥/令牌产物）。唯一按文件名匹配 `*seal*.json` 的是 `_sv_seal_v2.schema.json`；对它按内容解析：顶层键 `$id/$schema/title/description/type/properties/required/additionalProperties`，`IS_SEAL_INSTANCE=False`，正则 `(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])` 命中 0 个（无任何真实哈希值），仅 20 处 `^[0-9a-f]{64}$` 模式串 ⇒ **它是格式定义，不是 seal**。六个写域产物：`_sv_probe_readonly.py`（已执行）、`_sv_net_probe.py`（已执行）、`_sv_FEASIBILITY.md`（报告）、`_sv_seal_v2.schema.json`（SCHEMA）、`_sv_build_skeleton.py` / `_sv_verify_skeleton.py`（骨架，`ast.parse` 通过、从未执行）。
- 网络：仅 TCP `connect()+close()` 与 `curl -I`，无请求体、无 POST、无上传；**未发送本仓库任何内容或派生摘要到外网**。
- 零真机、零采样代码：无 gamemd.exe / ra2loader / YURI.exe、无 taskkill、无活进程内存读取、无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
- **副作用如实登记**：编排方基线 `NO_GNUPG_DIR`。按题目要求实跑 `gpg --list-secret-keys` 时 GnuPG 自动创建 `~/.gnupg`（`gpg: directory ... created` / `trustdb created`）。已尝试清理，`rm -rf` 报 `Device or resource busy`（`public-keys.d/pubring.db` 被 gpg-agent/keyboxd 占用）；残留该目录含**唯一一个文件** `public-keys.d/pubring.db`，`find` 计 secret key 文件 **0**。`/tmp/_sv_certutil_raw.txt`（certutil 解码用临时文件）已删除。未生成密钥、未改任何只读域文件。
- Python 一律 `python -I -X utf8` + 绝对路径；所有指纹 `hashlib.sha256`；引用均为「实跑命令+输出」或「文件:行」，拿不到的一律写「未验」。

---

*本件实跑 Bash 工具调用 22 次（每次含上列多条命令），Write 工具 6 次；未调用任何真机/采样/签名/密钥生成/提交/发布动作。*
