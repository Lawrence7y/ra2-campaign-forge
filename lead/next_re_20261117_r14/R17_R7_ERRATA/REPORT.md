基准镜像（只读）：D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R7-ERRATA · 执行报告

## 做了什么
- 只读打开 `R17_R7_REJECT_LAYER\REPORT.md`，逐字抄录三处原文片段；未写、未重命名、未改 mtime。
- 在同目录新建 `ERRATA.md`（独占创建，若已存在即报错退出，未覆盖），写入三处勘误，每处含①原文片段②权威值③字节依据④定谳出处。
- 只读核对基准镜像 `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` 对应 8 字节（.text VA→raw 偏移 `0x1000+(VA−0x401000)`），未反汇编。
- 报告按卡面要求落在 `R17_R7_ERRATA\REPORT.md`。

## 文件新建是否成功
- `R17_R7_REJECT_LAYER\ERRATA.md`：写入前检测为不存在，以独占标志 `wx` 新建成功。
- `R17_R7_ERRATA\REPORT.md`：目录原不存在，已创建并写入本报告。
- 三处勘误：全部写入（jne 0x47C73D→0x47C73F；xor al,al 0x47C853→0x47C856，0x47C853=5F pop edi；0x47C615 笔误→5E pop esi，C2 08 00 在 0x47C616）。

## 字节核对结果（只读 8 字节）
| VA | 起 8 字节 | 判定 |
|---|---|---|
| 0x47C73D | 3B C5 0F 85 0E 01 00 00 | 前 2 B `3B C5`=cmp eax,ebp，非 jne |
| 0x47C73F | 0F 85 0E 01 00 00 55 6A | 前 6 B `0F 85 0E 01 00 00`=jne 0x47C853 ✓ |
| 0x47C853 | 5F 5E 5D 32 C0 5B 83 C4 | 首字节 `5F`=pop edi，非 xor ✓ |
| 0x47C856 | 32 C0 5B 83 C4 08 C2 0C | 前 2 B `32 C0`=xor al,al ✓ |
| 0x47C615 | 5E C2 08 00 90 90 90 90 | 首字节 `5E`=pop esi；`C2 08 00` 自 0x47C616 起 ✓ |
| 0x47C616 | C2 08 00 90 90 90 90 90 | `C2 08 00`=ret 8 ✓ |

- 镜像 sha256 复核：`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，与卡面 `73201CC0…` 及 audit.py 断言一致（size=4,825,360 B）。
- 三处权威值与 `R17_AUDIT_R8\addr_authority.tsv` / `byte_checks.tsv` / `VERDICT.md` A1 及台账 `§1057` / `§1056` 登记一致。

## REPORT.md 未被改动的证明
- SHA-256（写前 = 写后）：`0EB3D37B41C8777BB9EA2FF7C645D6000D4F05B533AE5E5EC27E0D4FD7E4FB72`
- mtimeMs（写前 = 写后）：`1795239104954.8674`
- 报告全文字节数：11694
