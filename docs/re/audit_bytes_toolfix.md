# audit_bytes 工具链加固报告（PE 头映射 + BSS 断言替代方案）

> 范围：`tools/audit_bytes.py`（v2→v3）、新增 `tools/verify_bss_claims.py`
> 基线：`ra2youli/gamemd.exe` (YR 1.001) MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`（只读，未写）
> 日期：2026-01

---

## 1. 变更说明

### 1.1 PE 头映射缺口修复（audit_bytes v2→v3）

**问题**：v2 的 `va2off` 只遍历节表，首节（`.text` @ VA `0x00401000`）之前的 PE 头区域
（MZ 签名、PE 签名、可选头、节表）无法映射，导致 `0x00400000 = 4D 5A`（MZ）报 NOREAD。

**修复**：`sections()` 在节表前插入 PE-header 伪节：

```
PE-header  VA=0x00400000  VirtualSize=SizeOfHeaders  SizeOfRawData=SizeOfHeaders  rawptr=0
```

映射公式 `off = rawptr + (VA − base)` 对 PE 头退化为 `off = VA − ImageBase`，
与 PE 规范一致（头区文件偏移 = RVA）。`va2off` 本身无需改动。

本镜像 `SizeOfHeaders=0x1000`，头区覆盖 VA `[0x400000, 0x401000)`，
恰好与首节 `.text` 起始 `0x401000` 衔接，无空洞。

### 1.2 BSS 区域断言类型（audit_bytes v3 新增）

`.data` 节 `VirtualSize=0x367BE4 > SizeOfRawData=0x6C000`，
raw 覆盖 VA 上界 = `0x0087E000`，其上无文件字节（BSS）。
docs/re/va_claims_p1.md §2.5 的 65 条悬空 VA 全部 ≥ `0x0087E180`，落在 BSS。

**新增断言语法**（向后兼容——旧解析器要求 `=`，`bss 0xVA = virtual` 行在 v2 中被跳过）：

```
bss 0x0087E180 = virtual  # 区域断言：虚拟存在但无 raw
```

校验逻辑（`va_in_bss`）：VA 落在任一节的 `[base+SizeOfRawData, base+max(VS,RS))` 内即 PASS。
判定值：`BSS-OK` / `BSS-FAIL`。

### 1.3 BSS 断言替代方案（tools/verify_bss_claims.py）

两类可机器化的替代断言：

| 类型 | 语法 | 含义 | 覆盖力 |
|---|---|---|---|
| **A. bss-region** | `bss 0xVA = virtual` | 从节表推导「虚拟存在但无 raw」 | 65/65 = 100% |
| **B. text-xref** | `0xTEXTVA = HEX…` | `.text` 中引用该 BSS VA 的指令字节（写点/读点降级锚定） | 64/65 = 98.5% |

**text-xref 扫描策略**（混合定位 + capstone 验证）：
1. 用 4 字节 LE 模式在 `.text` 中定位候选命中；
2. 从命中点回溯 0–15 字节尝试反汇编，找覆盖命中字节的指令；
3. 验证该 4 字节确实是指令的 `mem.disp`（base=index=0）或非 call/jmp 的 `imm` 操作数；
4. 分类：`write` / `read` / `lea` / `push` / `imm`。

> 不用纯线性反汇编：4MB `.text` 上线性反汇编会脱轨（数据岛），漏掉真实引用
> （实测 `0x87f7f4` 的 `mov eax,[0x87f7f4]` 在线性扫描下被漏掉，混合扫描可稳定命中）。
> 不用纯字节模式：`e8 f7 87 00` 等 4 字节序列会撞上 `call rel32` 编码，造成数千条伪命中。

### 1.4 65 条 BSS 覆盖结果

| 指标 | 数量 | 占比 |
|---|---|---|
| 区域断言 bss-region PASS | **65/65** | **100.0%** |
| 存在 .text xref（任一类型） | **64/65** | **98.5%** |
| 存在写点 (write) | 28/65 | 43.1% |
| 存在读点 (read) | 38/65 | 58.5% |
| 区域或 xref 至少一项 | **65/65** | **100.0%** |
| 生成 xref 指令字节断言 | 394 条 | — |

唯一无 `.text` xref 的 VA：`0x008A0000`（仅区域断言覆盖）。
该地址可能仅由 `.data`/`.rdata` 指针表引用，或经寄存器间接访问，无绝对地址指令。

典型锚定示例：

| BSS VA | 写点示例 | 读点示例 |
|---|---|---|
| `0x0087F7F4` | — | `0x006DA7D0: mov eax, [0x87f7f4]`（RegisterCellAsVisible 入口） |
| `0x0087E8A4` | `mov [0x87e8a4], …` | `mov reg, [0x87e8a4]` ×36 |
| `0x0087F7E8` | — | —（3700 条 `mov ecx, 0x87f7e8` 地址物化，全局单例 this 指针） |
| `0x008871E0` | ×1 | ×539 |

---

## 2. 兼容性

| 项目 | v2 | v3 | 破坏性 |
|---|---|---|---|
| `va2off(secs, va)` 签名 | `(secs, va) → (off, name)` | 不变 | 无 |
| `sections(d)` 返回值 | `(name, base, vs, rs, rp)` 列表 | 前插 `PE-header` 伪节，同构元组 | 低：遍历者多一项；按名查找不受影响 |
| `parse_claims` 返回值 | `(ln, va, exp, label)` 4 元组 | `(ln, va, exp, label, kind)` 5 元组 | **有**：外部若 import 此函数需适配 |
| 字节断言语法 | `0xVA = HEX` | 不变 | 无 |
| BSS 断言语法 | 不存在 | `bss 0xVA = virtual` | 无（v2 解析器忽略无 `=` 或非 hex 行） |
| 自检 SELFTEST | 6 锚点 | 7 锚点（+MZ） | 无 |
| CLI | `claims.txt [--json] [--verbose] [--selftest]` | 不变 | 无 |

**结论**：对现有 claims 文件（`out/re_work/va_claims/claims_va_p1.txt` 等）完全向后兼容；
唯一 API 破坏是 `parse_claims` 返回 5 元组（当前无外部调用者）。

---

## 3. 回归命令原文与结果

### 3.1 口径自检

```bash
python tools/audit_bytes.py --selftest
```

```
=== 口径自检 ===
段        VA         rawptr     VA-rawptr    映射基准说明
PE-header 00400000  00000000  00400000    VA−0x400000 等价
.text    00401000  00001000  00400000    VA−0x400000 等价
.rdata   007E1000  003E1000  00400000    VA−0x400000 等价
.data    00812000  00412000  00400000    VA−0x400000 等价
.rsrc    00B7A000  0047E000  006FC000    ** 与 VA−0x400000 不等价，必须用段映射 **
.detour  00B93000  00497000  006FC000    ** 与 VA−0x400000 不等价，必须用段映射 **

VA         期望                       实际                       判定/标签
0x6ce210   b880000000c3             b880000000c3             OK SuperClass::Size()=0x80
0x6f936b   3bc1                     3bc1                     OK Greatest_Threat 严格大于比较点
0x750931   c20800                   c20800                   OK PlayGlobal ret 8
0x7509ef   c20400                   c20400                   OK PlayAt ret 4
0x6f8df0   83ec5c8b1534eca800       83ec5c8b1534eca800       OK Greatest_Threat 入口
0x7f7c80   0901000000000000c000000000000046 0901000000000000c000000000000046 OK IID_IPersistStream
0x400000   4d5a                     4d5a                     OK PE-header MZ（v3 映射）

自检结果：全部通过（7 条锚点，0 条不一致）
```

### 3.2 旧 claims 417 条回归

```bash
python tools/audit_bytes.py out/re_work/va_claims/claims_va_p1.txt --json out/re_work/audit_toolfix/regression_audit.json
```

```
合计 417 条：OK=417  MISMATCH/NOREAD=0
```

**对比 v2 基线**：`OK=416  MISMATCH/NOREAD=1`（`0x00400000` NOREAD）。
**NOREAD 归零**——PE 头映射缺口已闭合，无语义性 NOREAD 残留。

### 3.3 BSS 断言生成与校验

```bash
python tools/verify_bss_claims.py --vas-file out/re_work/audit_toolfix/bss65_vas.txt \
  --emit-claims out/re_work/audit_toolfix/claims_bss_p1.txt \
  --json out/re_work/audit_toolfix/bss_coverage.json
```

```
BSS 悬空 VA 覆盖统计  (共 65 条)
  区域断言 bss-region PASS : 65/65  (100.0%)
  存在 .text xref         : 64/65  (98.5%)
  存在写点 (write)        : 28/65  (43.1%)
  存在读点 (read)         : 38/65
  区域或 xref 至少一项     : 65/65  (100.0%)
  生成 xref 指令字节断言   : 394 条
```

```bash
python tools/audit_bytes.py out/re_work/audit_toolfix/claims_bss_p1.txt \
  --json out/re_work/audit_toolfix/audit_bss_p1.json
```

```
合计 459 条：OK=459  MISMATCH/NOREAD=0
```

（65 bss-region + 394 text-xref = 459）

---

## 4. 产物清单

| 文件 | 说明 |
|---|---|
| `tools/audit_bytes.py` | v3：PE 头映射 + BSS 区域断言 |
| `tools/verify_bss_claims.py` | BSS 断言替代方案（区域 + xref 扫描/生成） |
| `out/re_work/audit_toolfix/bss65_vas.txt` | 65 条 BSS 悬空 VA 清单（从 §2.5 抽取） |
| `out/re_work/audit_toolfix/claims_bss_p1.txt` | 生成的 459 条 BSS 断言 |
| `out/re_work/audit_toolfix/bss_coverage.json` | 覆盖统计（逐条 + 汇总） |
| `out/re_work/audit_toolfix/regression_audit.json` | 旧 417 条回归结果 |
| `out/re_work/audit_toolfix/audit_bss_p1.json` | BSS 断言审计结果 |
| `out/re_work/audit_toolfix/baseline_audit.json` | v2 基线（NOREAD=1）对照 |
| `out/re_work/audit_toolfix/extract_bss65.py` | §2.5 表格抽取脚本 |
| `out/re_work/audit_toolfix/_dump_pe.py` | PE 头字段探查 |
| `out/re_work/audit_toolfix/_diag_xref.py` | xref 扫描诊断 |
| `docs/re/audit_bytes_toolfix.md` | 本报告 |

---

## 5. 残留风险

| # | 残留 | 影响 | 建议 |
|---|---|---|---|
| 1 | `0x008A0000` 无 `.text` xref | 仅区域断言，无代码锚点 | 扫描 `.rdata` 指针表或真机 dump |
| 2 | 31 条无写点 | 读点/地址物化可锚定，写点缺失 | 真机断点跟踪写入路径 |
| 3 | text-xref 是降级锚定 | 锚的是「引用指令」非「对象本体」 | 需真机 dump 补全 BSS 初值 |
| 4 | `parse_claims` 返回 5 元组 | 外部 import 需适配 | 当前无外部调用者 |
| 5 | capstone 为硬依赖（xref 扫描） | 无 capstone 时无法生成 xref 断言 | 区域断言仍可用 |

---

## 6. §九 台账草稿（供 Lead 合并，勿由本轨直接写顶层台账）

```text
[v1.x.x] audit_bytes 工具链加固：PE 头映射 + BSS 断言替代方案
  范围: tools/audit_bytes.py v2→v3 + tools/verify_bss_claims.py（新增）
  基线: gamemd.exe MD5 4f37486e5b0dbe2ae5f45aeee0f98367（只读，未写）
  产物:
    - tools/audit_bytes.py                  （v3：PE 头映射 + bss-region 断言）
    - tools/verify_bss_claims.py            （BSS 断言替代方案：区域 + text-xref）
    - out/re_work/audit_toolfix/claims_bss_p1.txt   （459 条 BSS 断言）
    - out/re_work/audit_toolfix/bss_coverage.json   （覆盖统计）
    - out/re_work/audit_toolfix/regression_audit.json（旧 417 条回归）
    - docs/re/audit_bytes_toolfix.md        （本报告）
  修复:
    - 0x00400000 NOREAD → OK（PE 头 SizeOfHeaders 映射缺口已闭合）
    - 旧 417 条回归: OK=417 MISMATCH/NOREAD=0（v2 基线 NOREAD=1）
  BSS 覆盖（65 条悬空 VA）:
    - bss-region 区域断言: 65/65 = 100%
    - text-xref 代码锚定  : 64/65 = 98.5%（仅 0x008A0000 无 .text 绝对引用）
    - 写点覆盖: 28/65 = 43.1%    读点覆盖: 38/65 = 58.5%
    - 生成 xref 指令断言 394 条；合计 459 条 audit_bytes 全 PASS
  证据等级: 全部 [实证]（节表推导 + capstone 操作数验证，离线复算）；未启动真机
  兼容性: 字节断言语法/CLI/SELFTEST 向后兼容；parse_claims 返回值 4→5 元组
  风险/残留:
    - BSS 断言是降级锚定（区域 + 引用指令），对象本体初值需真机 dump
    - 0x008A0000 无 .text xref；31 条无写点
    - verify_bss_claims.py 的 xref 扫描硬依赖 capstone
  自证:
    python tools/audit_bytes.py --selftest → 全部通过（7 锚点）
    python tools/audit_bytes.py out/re_work/va_claims/claims_va_p1.txt
      → 417 条：OK=417 MISMATCH/NOREAD=0
    python tools/audit_bytes.py out/re_work/audit_toolfix/claims_bss_p1.txt
      → 459 条：OK=459 MISMATCH/NOREAD=0
```
