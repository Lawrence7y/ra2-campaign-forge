# S09-F1 UNKNOWNS

| # | 未知 | 现状 | 定位思路 | 级 |
|---|---|---|---|---|
| 1 | `GetEvent` 类型码语义命名（1/2/4/5/6 的 LDown/LUp/Move/RDown/RUp） | 字节只保证 1/2/4 同走「3-word 鼠标坐标展开」；5/6 未在本卡逐条解码 | 全量展开 `0x54F050..0x54F2C0` 的 `cmp cx` 分支，每种码跟踪消费 word 数与展开目的寄存器 | 未证 |
| 2 | 快捷键→CommandClass 索引的绑定表 | CommandClass::Array `0x87F658`、v[8]=Execute 已证；键→索引映射在 INI([Hotkeys]) 侧 | 追 `0x4C`xxx 命令注册簇构造时的 `push <id>; call 0x535C00`，与 INI 键名对账 | 未证 |
| 3 | `0x732D00` 的真实语义 | 实测为 6B `mov al,[0xB0FE65]; ret`（读全局字节），与线索文档称的「obj 已在选中组」不符 | 扫 `[0xB0FE65]` 写点定其语义（可能为多选/拖拽模式标志） | 静态推断 |
| 4 | `0x48DCD0` 40 类分派中每类对应的全局数组 | 已证 4 个数组锚点（0xA83CE4/0xA83C6C/0xA8E34C/0xA8B21C），jt `0x48DD10` 的 40 项未逐一解出 | dump `0x48DD10` 全 40 项 + `0x48DD24` 索引表，逐项标类（Building/Unit/Infantry/Aircraft/SuperWeapon…） | 未证 |
| 5 | Event 体 stride（`0x73` vs `0x73B`） | Body 基 `0xA802D4`，`lea edi,[ecx*3+0xA802D4]` 见 `ecx` 已预乘；精确 stride 未对账 | 单条事件 dump + 对照 YRpp `NetworkEvents.h`；看 `0x4C6970` 内 ecx 的乘数链 | 未证 |
| 6 | 选中集第二容器 `0xA8ECB8` 的角色 | 已证 Items `0xA8ECBC`/Count `0xA8ECC8` 被 `0x732D10` 遍历，与主集 `0xA8EC78` 并存 | 追 `0x732D10` 调用者与 `0x732D00/0x7327D0` 的分工（可能=link/attach 从属集） | 未证 |
| 7 | 对话框绘制入口细节 | 仅定位 `DialogBoxParamA`@`0x4C8579/0x52D0DF`、`CreateDialogParamA`@`0x5BC551/0x775B66/0x775CA6` | 按 S07 边界，未深入对话框资源模板与控件绘制 | 未证（边界外） |
| 8 | `0x6DA5C0` 过滤中 v[0x138]/v[0x14C] 的具名 | 已证为 `call [vft+0x138]`/`call [vft+0x14C]` 布尔谓词，未见符号名 | 用 RTTI/vft 反查 ObjectClass 主表槽 312/332 的实现函数并追语义 | 未证 |
