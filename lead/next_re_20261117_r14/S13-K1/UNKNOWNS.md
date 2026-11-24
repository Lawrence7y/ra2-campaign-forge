# S13-K1 UNKNOWNS

| # | 未决项 | 影响 | 下一步定位思路 |
|---|---|---|---|
| U1 | WeaponTypeClass +0xBC/+0xC0/+0xC4/+0xD8/+0xDC/+0xE0/+0xF4/+0xF8/+0xFC/+0x101、+0x120..+0x128 的字段名 | 10+ 个 ctor 写偏移无 INI 键锚点 | 三个 0x1C 步长的子对象（`0x7E4DD8`/`0x7EB6D4` vptr，见 ctor 0x771F00）是 `DynamicVectorClass<T*>`；扫描 `[weapon+0xBC]` 的 Add/Remove 调用者反推语义 |
| U2 | WarheadTypeClass +0x104..+0x111、+0x18C..+0x1B5 的字段名 | 少数 ctor 偏移无 INI 键 | +0x18C/+0x1A8 是带 vptr 的子对象（`0x7F0D3C`/`0x7E4DD8`，ctor 0x75D1F2）；查 Warhead `Anim`/`Impact` 相关 vtable 读点 |
| U3 | BulletClass 28 个字段仅 2 个锚定语义（+0xAC=Type*、+0xE8/F0/F8=double 坐标），其余 `[未证]` | BulletClass 运行时字段语义弱 | 更完整地扫 Draw(0x468090)/0x468670 的 `this` 读点 + 沿 `+0xAC`(Type*) 的二级访问定位；真机读子弹对象内存验证 |
| U4 | 解析器字符串 `0x817474`/`0x817694`（被 0x75E3B0/0x46C790 拒绝）的精确字面量 | 不影响字段布局 | `python -c` 读该 VA 的 cstr |
| U5 | Verses 的 11 项分别对应哪种 ArmorType（NONE/GUN/ARMOR/…）顺序 | 倍率矩阵元素的语义映射 | 查 `[0x7E3808]` 常数与伤害计算处对 `Verses[i]` 的索引来源（ArmorType 枚举），在 S13 后续卡做 |

说明：以上均不改变 LAYOUT.md 的字段表/一致性结论；U1–U3 是"偏移已实证、语义名未锚"，U4–U5 是精细语义，均标 `[未证]` 而非强猜。
