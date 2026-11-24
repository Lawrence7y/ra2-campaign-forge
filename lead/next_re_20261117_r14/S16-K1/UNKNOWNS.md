# S16-K1 UNKNOWNS

| # | 未知 | 现状 | 定位思路 | 级 |
|---|---|---|---|---|
| 1 | 玩家点击超武按钮的**原始 UI 消息入口** | 追到 House 方法 `0x4FAE50`（17 调用者，含 UI/AI/触发器），但哪个 sidebar/button 消息最终调它未逐条落实 | 从 `0x4FAE50` 的 17 个调用点反查：对 `0x4C78F3`/`0x6EFDB4`/`0x509Axx` 逐function追 `[esp+8]`（SW 槽索引）来源与 button-command 表；查 sidebar cameo click 的 `0x6A99AC` 同族函数 | 未证 |
| 2 | `SuperWeaponTypeClass+0x9C`（INI `WeaponType`）读者 | 写点 `0x6CEA8C` 已证；全 `.text` 未见以 SWType* 为基的读 | 从 `0x772FA0` 返回值语义反查：可能只是 `Sound/Weapon` 类型名字串 ID，供其他模块读；扫 `mov eax,[reg+0x9C]` 且 `ecx` 来自 SuperClass+0x28 | 未证 |
| 3 | `SuperWeaponTypeClass+0xB8/+0xE4/+0xF8/+0xFC` 读者 | ctor/loader 写点已证，读点未找到 | `+0xF8 Range`：PsychicReveal case 11 实测**不读**，只取 `Rules+0xFEC`；读点可能在鼠标瞄准范围圈（`0x6DC1C6` 一带，本卡反汇未命中，需重定位） | 未证 |
| 4 | `SuperClass+0x3C/+0x48/+0x4C/+0x54` 读者 | ctor/Grant/Load 写点已证；未找到直接读 | `+0x54` 只 `lea` 作声效坐标参数；`+0x3C` 疑为 `FlashSidebarTabFrames` 镜像，实际 ShouldFlashTab 读 Type+0xE8（`0x6CE1C4`）；扫 `[reg+0x3C]` 的 `cmp`/`add` | 未证 |
| 5 | `SW.AuxBuildings`（复数）INI 键 | 镜像中 0 命中；实际键是 **`AuxBuilding`**（单数，`0x842664`）→ `+0xC8` | 查 `[General]` / `rulesmd.ini` 是否有复数键由其他模块解析；若不存在，以单数键为正准 | 未证 |
| 6 | `GetCameoChargeState 0x6CBEE0` 的浮点公式细节 | 已见 `Rules+0x760` 乘除与 `54.0` 常数，未逐条对账 | 对 `0x6CBEE0..0x6CC06D` 做 x87 栈追踪；重点 `0x6CBF5F/64/72`、`0x6CC048` | 未证 |
| 7 | `ChargeToDrainRatio` 默认数值 | kb/30 记默认 8；本卡只读到写点 `0x67185D`，未在 ctor 找到默认 | 查 RulesClass ctor 对 `+0x760` 的 `fld/fstp`；或真机读 `[0x8871E0]+0x760`（需真机授权，本卡未申请） | 未证 |
