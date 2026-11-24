# S13-K8RECHK —— RULING-R15 D-39(C) ㉓ 复核（卡 S13-K8RECHK）

目标 ra2youli\gamemd.exe SHA-256 73201CC0…F67476（现场复算一致，4,825,360B，只读）。py3.12.10 + capstone 5.0.7(skipdata=True) + pefile，系统环境，未建 venv / 未 pip install / 未注入 / 未写 ra2youli\。写域仅本卡目录。

## 一、18 行逐行结论（实际行数 = 18，与卡面一致）

| entry | name | vt / slot | 宿主(ctor/dtor) | 结论 |
|---|---|---|---|---|
| 0075E510 | WarheadTypeClass::scalar_deleting_dtor | 7F6B30/8 | 实例ctor 0x75cec0等(堆) | 可辩护 |
| 0065BED0 | RadSiteClass::scalar_deleting_dtor | 7F0810/8 | 实例ctor 0x65b1e0(堆) | 可辩护 |
| 0040BBC0 | VectorClass\<BombClass*\> | 7E17EC/0 | atexit dtor 0x40b5c0/0x438590 | **不可辩护** |
| 0040BC10 | DynamicVectorClass\<BombClass*\> | 7E17CC/0 | initterm ctor 0x40b540/0x438550 | 可辩护 |
| 0040F8A0 | VectorClass\<WarheadTypeClass*\> | 7E1EA4/0 | atexit dtor 0x40f4d0 | **不可辩护** |
| 0040F8F0 | DynamicVectorClass\<WarheadTypeClass*\> | 7E1E84/0 | initterm ctor 0x40f490 | 可辩护 |
| 0040FE70 | VectorClass\<WeaponTypeClass*\> | 7E1EF4/0 | atexit dtor 0x40fb70 | **不可辩护** |
| 0040FEC0 | DynamicVectorClass\<WeaponTypeClass*\> | 7E1ED4/0 | initterm ctor 0x40fb30 | 可辩护 |
| 0046B8C0 | VectorClass\<BulletClass*\> | 7E4698/0 | atexit dtor 0x466320/0x4e68a0 | **不可辩护** |
| 0046B910 | DynamicVectorClass\<BulletClass*\> | 7E4678/0 | initterm ctor 0x4662e0/0x4e6860 | 可辩护 |
| 0048AFD0 | VectorClass\<DamageGroup*\> | 7E5144/0 | 无 global 写(栈局部) | 可辩护 |
| 0048B020 | DynamicVectorClass\<DamageGroup*\> | 7E5170/0 | 无 global 写(栈局部) | 可辩护 |
| 0054EB50 | VectorClass\<KamikazeControl*\> | 7ECE9C/0 | atexit dtor 0x54e2d0 | **不可辩护** |
| 0054EBA0 | DynamicVectorClass\<KamikazeControl*\> | 7ECE7C/0 | initterm ctor 0x54e260 | 可辩护 |
| 0062B330 | VectorClass\<ParasiteClass*\> | 7EF844/0 | atexit dtor 0x6291d0 | **不可辩护** |
| 0062B380 | DynamicVectorClass\<ParasiteClass*\> | 7EF824/0 | initterm ctor 0x629190 | 可辩护 |
| 0065C1B0 | VectorClass\<RadSiteClass*\> | 7F07C4/0 | atexit dtor 0x65b1a0 | **不可辩护** |
| 0065C200 | DynamicVectorClass\<RadSiteClass*\> | 7F07A4/0 | initterm ctor 0x65b160 | 可辩护 |

RTTI 链（COL=vt-4 → TD=COL+0xC → TD+8 内联名串）18/18 读通（fail-closed，未把 TD+8 当指针）；slot 值==entry 18/18。逐行 COL/TD/名/全部写点见 RECHECK_18.tsv 与 EVIDENCE\。

## 二、㉓ 三问答案

1. **该 vt 由构造器写入还是 atexit 析构器写入？** 7 张基类表（7E17EC/7E1EA4/7E1EF4/7E4698/7ECE9C/7EF844/7F07C4）的全部 global 写点都在 atexit 注册的 dtor 内（`push <dtor>; call 0x7C978A`），如 0x438552 push 0x438590 → 0x438586 call atexit；**不是活 vptr**。7 张派生表由 initterm 表（.data 0x812004 起 3944 项，真入口）内的 ctor 写入 → 活表。2 张 DamageGroup 表无 global 绝对写（仅栈局部 [esp+0x38]）；2 张普通类表由堆实例 ctor 写。
2. **同一 (site,slot) 是否被一活一死两行争抢？** 是，7 对：每个含 global 的容器族在 slot0 上，基类死表(dtored) 与派生表(ctored) 争抢同一 global（如 Bomb 0x87f5d8/0x89c668 的 slot0 同时被 7E17EC 与 7E17CC 写）。⇒ 7 个基类行必假。DamageGroup 与两个普通类无 global 争抢。
3. **是否由基类表变终态活表？** 否——7 个基类表从不是任何 global 的终态活 vptr，只在 atexit 析构窗口内瞬时装入。

## 三、检出力反证（§8.8 条 1）

独立复刻审计 t25.py 的 full4/ring3 判据（不复用 S13_K8\work）：
- S13 全池 240 行：恰命中 **23 行** = delta 的 18 候选 + 5 已接受先例；对其它 [静态推断]/[未证] 行 **0 命中**。
- [静态推断] 池 126 行：恰命中 **N=18**（即本卡 18 候选），误报 **M=0**（18 行全为 genuine `*_deleting_dtor`，占位 vslot 行一个未中）。
- 随机 16B 对齐 .text 起点 full4：seed 20261118/20261119/7 = 0/150、424242 = 1/150 ⇒ **1/600 = 0.167%**（X），远低于池中 18/126=14.3% 的命中率。

## 四、5 条先例 ㉓ 核查

004393F0 / 0046B5C0 / 0046C890 / 0062AF70 / 007730F0：full4 全 5/5 命中。其 vt（7E3D10/7E46E4/7E4948/7EF890/7F73B8）均 **NO_GLOBAL_WRITE**——为普通类 vtable，由堆实例 ctor 装活 vptr，无 atexit 注册、无成对争抢 ⇒ **5/5 过 ㉓**。delta 已按 RULING 补注「无直接调用者，仅虚派发见证」。

## 五、核心数字与差异

- 18 行：**可辩护 11 / 不可辩护 7**（=7 基类死表 / 成对争抢）。delta 只放 11 行，grade=[已证]，语义栏含「无直接调用者，仅虚派发见证」。
- 收益 **+11 非 +18**：S13 proved 89 → 100/240 = **41.67%**，仍 < 门槛 120（本条不产生达标）。
- **与裁决「9 对」不一致**：实测为 **7 对**死表/活表成对争抢（另 1 对 DamageGroup 无 global 不争抢、2 普通类无对）。若按「对=2 行」则 9 对=18 行与「11 可辩护」自相矛盾。建议 Lead 把 §8.8「9 对」更正为「7 对 / 7 行不可辩护」。
