# S16-PADD · PROGRESS（最终）

- 卡号 S16-PADD（补余量卡）｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读，自算一致）｜Python 3.12.10 + capstone 5.0.7 + pefile（无 venv、无 pip）
- 开工 19:02 落骨架；必读已核：R14_COMMON §1/§6/§7/§8.1/§8.2 技术⑦/§8.5/§8.6 六条/§8.7 九条；PENDING D-38/40/41/42；S16_N1/N2、S16-K1、M32 先例。

## 一、盘上重算（⑨ 停机核验，不照抄卡面）
| 量 | 本卡自算 | 卡面 | 一致 |
|---|---|---|---|
| S16 coverage 全行 | 92 | — | — |
| S16 atlas∩coverage（分母 n） | **90** | 90 | ✓ |
| named_S(R14) | **81** | 81 | ✓ |
| proved（atlas 内 [已证]） | **46** | 46 | ✓ |
| 门槛 | named ceil(.9×90)=81 / proved ceil(.5×90)=45 | 同 | ✓ |
| 余量（补前） | named **0** / proved **+1** | 同 | ✓ |
- atlas 外 2 行 = `004F8440`/`004F9370`，不计入分母（PANEL 口径）。

## 二、结论
- **Task A（补 named）：0 行** —— 无法定名，见 UNKNOWNS U1。
- **Task B（补 proved）：3 行** —— 均四环齐 + ③b，见 coverage_delta.tsv。
- **补后：named 81/90（余量 0，未改善）；proved 49/90=54.44%（余量 +4）**。
- delta 行数 3 = 自报 3（判据 7 ✓）。

## 三、Task A 取证（为何 0 行）
- 9 个 sub_ 候选（S16_N1 用掉 8 个后剩余）：00430BA0/0053A6C0/0053D8E0/0053DDA0/0065E660/006CE240/006CE2D0/006CE320/0071AB60；加 27 个 slotN 行。
- 通道一（YRpp `CALL/JMP_THIS(0x…)` 地址绑定）：本卡自写扫描器（已在 6 个已知正例 53A0E0/53AE50/6CE270/6CE2C0/53AF40/595740 上验证命中）扫 YRpp 全部 2275 个文本文件（.h/.cpp/.txt/.html/.source），**36/36 候选 0 绑定**（`work/scan_yrpp2.py`）。与 S16_N2「YRpp 2188 文件全扫 0 命中」独立一致。
- 通道二（跨项目独立源）：S16_N2 已穷 docs/re/re_atlas/台账/CONFLICT_CLASS2 —— 仅 0065E660 有 docs/re 名（已被 S16_N2 以 ⑱ 归属冲突 fail-closed 否决，且 docs/re 按 §8.5 主条非合法通道）。
- ⇒ 无一候选有合法异源通道。**按 §8.5「只有一条通道不写 delta」，Task A 交 0 行。**

## 四、Task B 取证（3 行）
| entry | name | ②（全部持有表 / ⑯） | ③b 档位与入口相对锚 | ④ 站点 |
|---|---|---|---|---|
| 006CDEB0 | SuperClass::slot3 | vt `0x7F3FE8` slot3 唯一持有（COL `0x80B610`→TD `0x8423E0`/`.?AVSuperClass@@`），单表⇒归 SuperClass | ③b② + ③b③：`+0x04 test eax,eax` 空指针闸、`+0x08 mov eax,0x80004003`(E_POINTER)、`+0x10..+0x30` 从 `[0x7E9580/84/88/8C]` 装 4 vptr 到 out+0/+4/+8/+C | ctor `0x6CAF90` 于 `0x6CAFF9 mov [esi],0x7F3FE8`（live，实例 site 不共用，非 atexit）|
| 006CE7C0 | SuperWeaponTypeClass::slot3 | vt `0x7F4090` slot3 唯一持有（COL `0x80B6C8`→TD `0x842600`/`.?AVSuperWeaponTypeClass@@`），单表⇒归本类 | ③b② + ③b③：同型，`+0x08 mov eax,0x80004003`、`+0x10..+0x30` 装 4 vptr `[0x7E9570/74/78/7C]` | ctor `0x6CE5B0` 于 `0x6CE669 mov [ebp],0x7F4090`（live）|
| 006CE800 | SuperWeaponTypeClass::slot5 | vt `0x7F4090` slot5 唯一持有（同上 RTTI），单表⇒归本类 | ③b② + ③b③：`+0x14 call 0x410380 → +0x19 test eax,eax → +0x1B jl 0x6CE8BE` 负值错误码传播（被调 0x410380 `+0x09 mov eax,0x80004003`、`+0x23 test/jl`）；`+0x38..+0x4F` 装 4 vptr `[0x7F4090/74/6C/64]` | ctor `0x6CE5B0` 于 `0x6CE669 mov [ebp],0x7F4090`（live）|
- 三行 direct call 全 0（虚函数结构，D-39）；环④ 均为 **exact 活 vtable 派发**（构造器装活表 + vt[slot]==entry + 写点在行外 + site 不共用），与 M32 保留 13 行同口径，非「VT imm32 引用」弱口径。
- ③b 基率：S16 `[静态推断]` 池 N=37，seed 20261119，2000 次抽 3 不放回：K=15、p=0.405405、E[3]=1.216216、MC=1.211500（D-42 忠实检测器；`work/baselines.txt`）。`K=N·p` 恒等式不作校验（判据 3）。

## 五、纪律自检
- 16 条纪律逐条核：寄存器/thiscall 溯源（本卡无 thiscall 语义判断）、逐字符写值、区间包含归属、双通道至少一条不依赖 atlas（② 走 raw RTTI 字节 + COL/TD 反查）、未改 coverage.tsv / 台账 / 游戏文件、未 commit、未建 venv。
- 交付：PROGRESS.md / UNKNOWNS.md / DISAGREE.md / coverage_delta.tsv / EVIDENCE/ / work/。
