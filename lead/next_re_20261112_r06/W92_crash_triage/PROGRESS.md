# W92 PROGRESS

- 2026-11-14 16:20 建卡目录；定位 12 份 except 原件（W88 6 / W91 5 / ra2youli 1），唯一名复制到 `work\`，并列 sha256。
- 2026-11-14 16:26 `EVIDENCE\parse_except.py` 完成：12 份 → `signatures.json`；确认 archived/late 成对逐字节相同、W91_sandbox==W91_P2 → 独立现场 6 个。发现 P1 是 EIP=0（与卡片摘要不符），同步给 Lead。
- 2026-11-14 16:33 `EVIDENCE\pe_disasm.py`：三处可读 EIP 的 Bytes at CS:EIP 与镜像 32/32 一致（无运行态补丁迹象）；确认 0x47C538 链走查代码（[ecx+0xE4]→[esi]→call [eax+0x2C]→cmp 6→[esi+0x30]）；确认镜像 = ra2youli\gamemd.exe = W88/W91 三处 trip 实际运行镜像（sha 73201CC0…）。
- 2026-11-14 16:44 `EVIDENCE\pe_disasm2.py`：函数入口/规模/ret 形态；调用方定位（0x439CAD、0x6D16C2 direct call、0x6F7CBE call [edx+0x2E4]）；RTTI 审计 → 镜像无 RTTI；R03 转述地址 0x51BF90/0x51C2D3 镜像核对通过；S4 判决 = vptr 被堆指针覆盖 + 假虚表槽值 0。
- 2026-11-14 16:47 `EVIDENCE\pe_disasm3.py`：155 个 vtable 阵列，69 个槽 11 = `mov eax,N; ret` 且 N 唯一 → 槽 +0x2C = WhatAmI 实证；模式计数（FF 50 2C ×482 等）。
- 2026-11-14 16:50 `CRASH_SIGNATURES.md`（签名表 + 三段证据 + 机制归并 + 未证项）、`UNKNOWNS.md`、`DISAGREE.md`、卡根 `signatures.json` 落盘完毕。
