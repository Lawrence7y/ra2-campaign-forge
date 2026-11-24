基准镜像（只读）：D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R7-REJECT-LAYER · 勘误表（只增不改）

> 本页为新增勘误，不回改 `R17_R7_REJECT_LAYER\REPORT.md` 的任何既有字节；该报告 mtime 未变。
> 字节核对仅只读上述基准镜像对应 8 字节（VA→raw 偏移 = `0x1000 + (VA − 0x401000)`，.text 节），未做反汇编。
> 三处勘误均按「① 原文片段（逐字抄）② 权威值 ③ 字节依据 ④ 定谳出处」记录。

---

## 勘误 1 · `jne` 指令起始：0x47C73D → 0x47C73F

**① 原文片段（逐字抄）**
- `R17_R7_REJECT_LAYER\sites.tsv:8`（`decide_occupied` 行的地址列把该 jne 挂在 `0047C73D`）：
```
decide_occupied	0x47C853 fail exit	0047C73D	3B C5 0F 85 0E 01 00 00	cmp eax,ebp / jne 0x47C853	eax = 0x47C3D0() = nearest blocking object at cell
```
- `R17_AUDIT_R8\VERDICT.md` A1 节对原状的逐字引述：「执行方对：jne 起始 0x47C73F；R7 挂在 0x47C73D 是错的，但目标 0x47C853 正确。」
- 注：`REPORT.md` §Q3 链路块当前列作 `0x47C73D 3B C5 cmp eax,ebp` / `0x47C73F 0F 85 0E 01 00 00 jne 0x47C853`（已分列），但 `sites.tsv` 的 `0047C73D` 挂载行仍保留原错，故一并勘入。

**② 权威值**：`jne` 指令起始 = `0x47C73F`（`0F 85 0E 01 00 00`）；跳转目标 `0x47C853` 本身正确、保留不变。`0x47C73D` 处实为 `3B C5`（`cmp eax,ebp`）。

**③ 字节依据**：基准镜像 `0x47C73D` 起 8 字节 = `3B C5 0F 85 0E 01 00 00` → 前 2 B `3B C5` 为 cmp，jne 自第 3 B 起；`0x47C73F` 起 8 字节 = `0F 85 0E 01 00 00 55 6A` → 前 6 B 即 `0F 85 0E 01 00 00`，rel32=`0x0000010E`，目标 `0x47C73F+6+0x10E=0x47C853`。

**④ 定谳出处**：`R17_AUDIT_R8\addr_authority.tsv`（`0x47C73F` 行，kind=`真错`，who_is_right=执行方）；`R17_AUDIT_R8\VERDICT.md` A1 节 & 必改项 2；台账 `§1057` 事项 2/3（五条必改之②③、事项 3 地址权威表 A1 实质）。

---

## 勘误 2 · `xor al,al` 地址：0x47C853 → 0x47C856（0x47C853 = `5F` pop edi）

**① 原文片段（逐字抄）**
- `R17_R7_REJECT_LAYER\REPORT.md:135`：
```
2. **该格失败的产出点**：`0x47C853` 起 `32 C0`（`xor al,al`）+ `C2 0C 00`（`ret 0xC`）→ `al=0`。
```
- 同文件 `:116` 的链路行把 `xor al,al` 挂在 `0x47C853` 行首：
```
0x47C853  5F 5E 5D 32 C0 5B 83 C4 08 C2 0C 00     ; xor al,al ; ret 0xC  -> al=0
```

**② 权威值**：`xor al,al` 指令起始 = `0x47C856`（`32 C0`）。`0x47C853` = `5F`（`pop edi`），`0x47C854`=`5E`（pop esi）、`0x47C855`=`5D`（pop ebp）。

**③ 字节依据**：基准镜像 `0x47C853` 起 8 字节 = `5F 5E 5D 32 C0 5B 83 C4` → 前 3 B 为 `5F 5E 5D`（三次 pop），`32 C0` 自第 4 B 起即 `0x47C856`；`0x47C856` 起 8 字节 = `32 C0 5B 83 C4 08 C2 0C` → 首 2 B `32 C0`。

**④ 定谳出处**：`R17_AUDIT_R8\addr_authority.tsv`（`0x47C853` = `5F` pop edi 与 `0x47C856` = `32 C0` xor al,al 两行，kind=`真错`）；`R17_AUDIT_R8\VERDICT.md` A1 节（`0x47C850 起：24 | 74 0C | 5F(@0x47C853 pop edi) | 5E | 5D | 32 C0(@0x47C856 xor al,al) | 5B | 83 C4 08 | C2 0C 00(@0x47C85C)`）及必改项 3；台账 `§1057` 事项 2/3。

---

## 勘误 3 · 1 字节笔误：0x47C615 不是 `C2 08 00`（实为 `5E` pop esi；`C2 08 00` 在 0x47C616）

**① 原文片段（逐字抄）**
- `R17_R7_REJECT_LAYER\REPORT.md:18`（§0(a) 锚点表 `0x47C620` 行）：
```
| `0x47C620` | OK | `0x47C619..0x47C61F` 是 7×`90`，此前 `0x47C615`=`C2 08 00`；`0x47C620`=`A1 AC E7 A8 00` |
```
- `R17_AUDIT_R7\VERDICT.md` 非必改小注对原状的逐字引述：「`REPORT.md` §0(a) 写「`0x47C615`=`C2 08 00`」，实读 `0x47C615`=`5E`(pop esi)、`C2 08 00` 在 `0x47C616`」。

**② 权威值**：`0x47C615` = `5E`（`pop esi`）；`C2 08 00`（`ret 8`）起始 = `0x47C616`。锚点 `0x47C620` 及其余字节均正确，仅为相邻一字节记位偏差，登记为笔误、不升级为结论必改项。

**③ 字节依据**：基准镜像 `0x47C615` 起 8 字节 = `5E C2 08 00 90 90 90 90` → 第 1 B `5E`，`C2 08 00` 自第 2 B（`0x47C616`）起，随后 `0x47C619..0x47C61F` 为 7×`90`；`0x47C616` 起 8 字节 = `C2 08 00 90 90 90 90 90`。

**④ 定谳出处**：`R17_AUDIT_R7\VERDICT.md` 非必改小注；台账 `§1056` 事项 11 / `numbers.tsv` 行 59–61 / `SELFCHECK.md` 第 14 条（该笔误的实际登记处；本卡指定引用的 `§1057` 未另载此项，故按 `§1056` 原文引）；`0x47C620` 入口权威值亦见 `R17_AUDIT_R8\VERDICT.md` A3 节。
