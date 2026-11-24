# R17-B3-REVIEW · 对 R17_AUDIT_R9 的 B3「12 处 ctor 装表写」独立复核

目标 ra2youli\gamemd.exe | 4,825,360 B | SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476（独立重算一致，与 R9 同）
独立实现 work.py / stage2–5.py（capstone 5.0.7，本工具链未 import/复用 R9 任何脚本）。只读 `rb` 打开；无进程、无调试。
反汇编全部锚点对齐：PE→节表→operator new thunk 0x7C8E17 → call 目标 0x7C9442 → **三 host 入口地址**逐条线性解码，覆盖率 36 / 325 / 290 条指令，三条均 `FULL` 覆盖到实测 fn_end（无残留字节）。
中间产物：stage1.json / stage2_sites.json / stage3_prologue.json / stage4.txt / disasm_anchored.txt（654 行）。

## 总判定：**部分成立 —— 8/12 成立，4/12 不成立（全部在第 5 项 G5 失败）**

12 处 site 全部**真实存在**且**操作数形态**与 R9 描述逐字节相同。但「构造器装表写」这一**结论**只在 2 个 host 上成立：
0x43B680（4 处）与 0x43B740（4 处）。**0x43BCF0 的 4 处不成立** —— 该函数不是构造器，不返回 this。

**与前源：DISAGREE（局部）**。前源没有为任何一处给 G1–G5，只给了「mov [esi/ebp+off], imm32」的操作数形态 + 位置断言，就跨到了「ctor 装表」。第 5 项（收尾返回 this）在 0x43BCF0 上失败，前源整段漏检。

---

## C3 · 槽内容 —— **一致（4/4 MATCH）**

| 槽 | 期望 | 实测 dword | 所在节 |
|---|---|---|---|
| 0x7E3E90 | 0x410590 | 0x410590 | .text ✔ |
| 0x7E3E98 | 0x410580 | 0x410580 | .text ✔ |
| 0x7E3EA0 | 0x4105E0 | 0x4105E0 | .text ✔ |
| 0x7E3EBC | 0x410260 | 0x410260 | .text ✔ |

无差集。上下文亦一致：[0x7E3E90]=0x410590 与 [0x7E3E94]=0x7FC2C8 交替，至 0x7E3EB4=0x410230 / 0x7E3EB8=0x7FC360 / 0x7E3EBC=0x410260 —— 即 0x7E3EBC 是**下一个 vftable 的首项**，不是链尾 slot。四槽指向的 0x410260/0x410580/0x410590/0x4105E0 均在 .text，确为函数指针，不是字符串/常量。

## C2 · 位置断言 —— **12/12 均成立**，但两处 fn_end 与 R9 不同

| host | 实测 fn_end | 字节依据 | R9 报的 fn_end | 评价 |
|---|---|---|---|---|
| 0x43B680 | **0x43B740** | 0x43B73D `c2 04 00` = ret 4；0x43B740 起 `8b 44 24 08 53 55 56 57 8b f1 50 e8` = 下一函数 | 0x43B740 | 一致 |
| 0x43B740 | **0x43BCDE** | 0x43BCDB `c2 08 00` = ret 8；0x43BCDE 起 `6a 01 8b ce e8` | 0x43BCDE | 一致 |
| 0x43BCF0 | **0x43C0D0** | 0x43C0C9 `c3` = ret；0x43C0CA–0x43C0CF = `90 90 90 90 90 90` 六字节 NOP 填充；0x43C0D0 起 `83 ec 2c a1 e0 71 88 00` = 下一函数 | 0x43C0CA | **R9 早报 6 字节**：把 ret 操作数的位置当成 fn_end，漏了 NOP 填充 |

位置断言 host ≤ site < fn_end：12/12 通过（最紧的 0x43BD13 距 0x43C0D0 仍有 0x3BD 字节余量）。**用 R9 的 0x43C0CA 也仍然通过**，故此处不是判决点，仅记录偏差。

## C1 · 逐处 G1–G5

### host 0x43B680（4 处，**全部 PASS**）
- **G1 非栈** PASS。`c7 06`/`c7 46 xx`，基址只有 esi；该函数**无栈帧**（无 push ebp / mov ebp,esp / sub esp）。0x43B687 的 push eax 是传参，不是临时槽。
- **G2 是 this** PASS。0x43B685 `8b f1` mov esi,ecx 是唯一 esi 写入；之后只写 eax/edx/ecx 标量，site 前 esi 未被重载。
- **G3 非析构** PASS。收尾 0x43B73A `8b c6` mov eax,esi / 0x43B73C pop esi / 0x43B73D `c2 04 00` ret 4。全区间无 `mov dword [esp+x],1`、无对本对象 `test al,1`、无 delete thunk（0x7C8B3D）调用、无基类析构。
- **G4 前序分配或基类构造** PASS。0x43B687–0x43B688：push arg（取 [esp+4] 入参）/ call **0x6F4300** = 基类 ctor。核验：0x6F4300 首条 callee 是 0x65A7E0（祖父 ctor），自身即 thunk 形式的派生构造入口。派生 set 归位后再写 vftable 指针，正是 MSVC 构造器形态。
- **G5 返回 this** PASS。0x43B73A mov eax,esi，ret 4 为 __thiscall 单栈参，自洽。

### host 0x43B740（4 处，**全部 PASS**）
- **G1 非栈** PASS —— **这是最容易误判的一处**。0x43BA00 的操作数是 `c7 45 00` = `[ebp]`，字面上像经典的「[ebp+..] 局部」翻车形态。实测：0x43B94A `8d 6e 04` **lea ebp,[esi+4]** 在 site 之前已把 ebp 从栈帧基址改写为 this+4 派生指针；本函数根本没有 push ebp/mov ebp,esp 帧建立指令（入口只 push ebx/ebp/esi/edi 后 0x43B748 mov esi,ecx）。故 [ebp] 不是栈，**且与 0x43B725 的 [esi+4] 写的是同一个槽 0x7E3EA0**。
- **G2 是 this** PASS。esi=ecx（0x43B748）；ebp=esi+4。两者皆 this 派生。
- **G3 非析构** PASS。0x43BCD5 `8b c6` mov eax,esi / pop edi/esi/ebp/ebx / 0x43BCDB `c2 08 00` ret 8。无删除签名。
- **G4 前序基类构造** PASS。0x43B74A–0x43B74B：push arg / call **0x6F2B40** = 基类 ctor（其首条 callee 0x6F2B46 → 0x65A750，同族祖父 ctor）。
- **G5 返回 this** PASS。

### host 0x43BCF0（4 处，**G5 失败 → 全部不成立**）
- **G1 非栈** PASS。`c7 06`/`c7 46 xx`，基址 esi；入口 push ecx 占位 + push edi 与 [esp+..] 参数读取收支自洽，无 esp 基址写。
- **G2 是 this** PASS。0x43BCF4 `8b f1` mov esi,ecx；0x43BCF7 lea edi,[esi+0x6B4]，site 只写 [esi]。
- **G3 非析构** PASS，但**必须点明一处已排除的近似反例**：0x43BD46–0x43BD5A 有 `push ebp(0)` / `call 0x554A80` / `push 1` / `call dword [eax+0x20]`。这不是 scalar deleting destructor —— 其 ecx 取自 **[esi+0x614] 成员指针**（0x43BD3A、0x43BD52 显式重载），前后把 [esi+0x614] 清 0，属释放成员对象；判断对象是 this 的依据（test al,1 / [esp+..],1 / push esi 后 call 删除器）**零命中**。全三 host 区间此类签名零命中。
- **G4 不适用（记录为「非构造器」而非失败）**。site 之前**没有 operator new、没有基类 ctor 调用**，也没有帧建立；0x43BD2E 的 call 0x405C00 是**成员子对象重建**（与 0x43BD1A call 0x406060 成对，是 destroy/construct 成员），不是基类构造。
- **G5 返回 this —— FAIL**。函数尾部 0x43C0B6–0x43C0C9：
  ```
  0x43c0b6  8bce                 mov ecx, esi
  0x43c0b8  c6450d00             mov byte ptr [ebp+0xd], 0
  0x43c0bc  895d08               mov dword ptr [ebp+8], ebx
  0x43c0bf  e83c842b00           call 0x6f4500
  0x43c0c4  5f 5e 5d 5b 59       pop edi/esi/ebp/ebx/ecx
  0x43c0c9  c3                   ret
  ```
  **全函数 290 条指令内不存在 mov eax,esi**（grep 实测）。返回值 eax 由 callee 0x6F4500 决定。构造器必须把 this 交回给 operator new / 上层，此处不交回。
- 旁证（可独立复现）：0x43BC10 `push eax; call 0x7C8E17` 才是本函数的 **operator new** 调用，**物理位置在 4 处 site 之后**；其返回值 mov edi,esi 存到 buffer（0x43BC16 mov edi,eax）。即 site 写的是**已存在对象**的 vftable，是该函数的「复位」步骤，不是「就地构造新对象」。0x7C8E17 = push 1 / push [esp+8] / call 0x7C9442（operator new(size,1)）；0x7C8B3D = push [esp+4] / call 0x7C93E8（operator delete(ptr)）—— 这一对在本函数内成对出现，进一步指向 Reset/Reinit 语义。

## C4 · 与前源分歧点

前源错在**第 5 步**（也是唯一一步）：它没有验证 host 是否返回 this，把「B2 批评」用力过猛地把 12 处等量齐观。具体：
1. **12 处当同类是错的**。0x43B680/0x43B740 是构造器（返回 this，ret 4/ret 8），0x43BCF0 是重初始化例程（不返回 this）。前源表格把三者并列成一张表，读者会以为整段都是装表。
2. **fn_end 报错**：0x43BCF0 的 fn_end 应为 **0x43C0D0**（ret 后的 6 字节 NOP 填充），前源写 0x43C0CA。不改变位置断言结论（0x43BD13 < 0x43C0CA 仍成立），但违反「字节实测」要求。
3. **G2 的 [ebp] 处前源没给依据**。0x43BA00 的 [ebp] 在字面上就是失败形态 ①（把栈临时写当装表）。结论碰巧对，但依据缺失，属于「蒙对」。本复核用 0x43B94A lea ebp,[esi+4] 补齐。

## 我额外排除了哪些失败形态

1. **栈临时写**：逐个 site 检查操作数基址 —— 10 处 esi（=ecx）、1 处 esi+disp、1 处 ebp。ebp 那处用 0x43B94A 的 lea 证明是 this+4；三 host 入口均无 `mov ebp,esp`，故 [ebp+..] 不可能是栈。
2. **析构器 / scalar deleting destructor**：全三 host 扫描 `mov dword [esp+..],1`、对象上的 `test al,1`、`push esi` 后接 delete thunk —— 零命中。0x43BCF0 内唯一像删除序列的 0x43BD4C–0x43BD5A 已证明作用于 [esi+0x614] 成员对象，不是 this。
3. **位置错配**：12 处全部落在实测 [host, fn_end) 内，且反汇编覆盖率 FULL（到达 fn_end 无残留字节），排除「函数边界画错导致 site 其实属于别的函数」。
4. **把分配写在 site 之后误判为构造器**：0x43BCF0 的 operator new 在 site 之后出现，正是判它非构造器的旁证之一。
5. **槽内容错**：4 槽逐一读 dword 复核，全 MATCH 且全在 .text，排除「指向字符串/常量」的可能。

## 交付影响（给 lead 的建议，不擅自改 R9）

- R9「B3 发现取用者」这一**发现**成立：12 处立即数写确实存在，位置断言全部通过，四槽内容断言全部正确。
- R9「12 处均为 ctor 装表写」这一**结论**应收窄为 **8 处（0x43B680 ×4、0x43B740 ×4）为 ctor 装表**；**0x43BCF0 ×4 为对象重初始化写 vftable，不构成独立 ctor 装表证据**（不返回 this）。
- 「无取用者从全称否定改局部否定」的**方向不变**（8 处 ctor 写已足以否定全称否定），故 B3 的**下游结论不受影响**；受影响的是**计数与登记口径**（12 处 → 8 处 ctor + 4 处 reinit），以及 0x43BCF0 的 fn_end（→0x43C0D0）。

## 产物清单

- VERDICT.md（本文）
- g1g5.tsv（12 行逐处 G1–G5 + 位置断言 + 判定）
- byte_checks.tsv（SHA/HOST/FN_END/SITE/G2_THIS/G4_BASE/G5_EPI/NEW_SEM/DEL_SEM/C3_SLOT 逐条字节）
- work.py（读取/解码/槽值/fn_end 实测）
- stage2.py / stage5.py、stage1.json / stage2_sites.json / stage3_prologue.json / stage4.txt、disasm_anchored.txt（654 行，三 host 全量锚点对齐反汇编）
