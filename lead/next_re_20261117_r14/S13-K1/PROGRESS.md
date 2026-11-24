# S13-K1 PROGRESS

## 结论表（分级 + 证据路径）

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | 四类 RTTI TypeDescriptor/vftable/槽数：Weapon 0x7F73B8(27)、Warhead 0x7F6B30(27)、BulletType 0x7E4948(40)、Bullet 0x7E46E4(125) | 已证（RTTI 实测 + .rdata 定界 双通道） | `EVIDENCE/rtti_extract.txt` |
| 2 | GetSize：Weapon 0x160 / Warhead 0x1D0 / BulletType 0x2F8 / Bullet 0x160（slot12 `mov eax,imm;ret`） | 已证（双通道：vtable slot12 + 解析器 `push imm` 分配） | `EVIDENCE/verify_slots.txt`、`EVIDENCE/resolvers.txt` |
| 3 | 四类的字段表（INI loader 写点反推 + 构造器默认写） | 已证（写者/读者同址双支撑；多数锚 INI 键） | `EVIDENCE/ini_fields.tsv`、`EVIDENCE/ctor_offsets.tsv`、`LAYOUT.md` |
| 4 | 字段表 max_end ≤ GetSize（0x15D≤0x160 / 0x1CC≤0x1D0 / 0x2F8=0x2F8 / 0x159≤0x160） | 已证 | `EVIDENCE/field_tables.txt`、`LAYOUT.md §5` |
| 5 | `Warhead=` → ReadString → 0x75E3B0 解析 → `[weapon+0xAC]=WarheadTypeClass*`；`Projectile=` → 0x46C790 → `[weapon+0xA0]=BulletTypeClass*` | 已证（逐条反汇编，非就近 E8 推断） | `EVIDENCE/inspect_special.txt`、`EVIDENCE/resolvers.txt` |
| 6 | `Verses` = double[11] @Warhead+0xA0..+0xF7（护甲倍率矩阵，strtok ',' × atoi × 常数） | 已证（loader 循环 + 构造器 rep movsd 双通道） | `EVIDENCE/inspect_special.txt`、`ctor_candidates_detail.txt` |
| 7 | 函数边界通道 A(ret+padding, atlas-independent) == 通道 B(atlas) 逐字节相等 | 已证 | `EVIDENCE/dump_fields_stdout.txt` |

分级口径：`[已证]`=RTTI/双通道/逐条反汇编实测；本卡无 `[静态推断]`/强猜；明确未决项见 `UNKNOWNS.md`。

## 核心数字（3 个）

1. **四类的字段数（排除 4 个 vptr 槽）**：WeaponTypeClass **78**、WarheadTypeClass **69**、BulletTypeClass **50**、BulletClass **28**。
   复算：`EVIDENCE/ctor_offsets.tsv` ∪ `EVIDENCE/ini_fields.tsv` 的 distinct `(class,off)`，去掉 `off∈{0,4,8,C}`；`python work/merge_fields.py` 逐类打印。
2. **max_end vs GetSize**：`0x15D/0x1CC/0x2F8/0x159` vs `0x160/0x1D0/0x2F8/0x160` —— **四类全部吻合（≤）**。
   复算：每字段 `off + width` 取 max；width 取 loader store 宽度（ReadDouble=8、bool=1、其余=4）。`LAYOUT.md §5`。
3. **WeaponTypeClass 写者站点数**：**57 个** loader store 站点（`ini_fields.tsv` 中 class=WeaponTypeClass 的 `store_site` 全为独立地址）+ 构造器默认写站点（`ctor_offsets.tsv`，77 个 `mov [esi+off],reg` 站点，含 3 个 ctor 变体）。
   复算：`csv` 计 `EVIDENCE/ini_fields.tsv` 行（=57，含 1 个 converter store）与 `ctor_offsets.tsv` 的 sites 列。

## 复跑入口（全部只读目标）

```
python work/rtti_extract.py          # RTTI → TD/COL/vftable/槽数
python work/verify_slots.py          # slot11/12 立即数 + slot25 loader 入口
python work/dump_s13k1_fields.py     # INI 键→字段（skipdata=True，双通道边界）
python work/ctor_fields.py           # ctor 写偏移（thiscall ecx 溯源）
python work/inspect_special.py       # Warhead/Projectile/Verses 逐条反汇编
python work/check_resolvers.py       # name→type* 解析器 + push imm 分配
python work/merge_fields.py          # 合并 + max_end
python work/gen_layout.py            # 生成 LAYOUT.md
```
