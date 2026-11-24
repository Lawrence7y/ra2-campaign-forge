# S20-K1 UNKNOWNS（未决项）

| # | 未决 | 证据现状 | 需补取证 | 分级 |
|---|---|---|---|:---|
| U1 | 4 个 Type 类（AnimType/ParticleType/PSysType/VoxelAnimType）GetSize 通道B 分配对=0 | 通道A `B8 imm C3` 已证；构造器走 TClassFactory 注册，无直接 `push size;call new` 现场 | 查各 Type 的 find-or-create 工厂（如 KB ScriptTypeClass `0x691C00` 型 `push size;call 0x7C8E17`），或确认 YRpp 类型类由 `TClassFactory::Create` 统一分配 | `[未证]` |
| U2 | AnimClass `+0xC8/+0xCC` 精确语义（帧号/循环计数 vs 宿主指针） | 写者 0x421EE5/0x421EEE（ctor）+ AI 20+ 读者已证；类型未定 | 回溯 AI 中 0x423ADC 起 `+0xC8` 来源与下游调用（`IsCellShrouded` 等），追 ecx 链 | `[静态推断]` |
| U3 | ParticleClass `+0x9C/+0xA0/+0xA4` 的写点归属 | 16 读者已证（Draw 0x62CF36 等）；写点在 AI/Update 方法集内未稳定捕获（this 传播跨栈） | 全 `.text` 扫 `[reg+0x9C]` 写并对齐 Particle AI 函数区间（R14 纪律17：函数区间包含） | `[静态推断]` |
| U4 | ParticleSystemClass `+0xBC` 向量的元素 stride / 容量语义 | ctor 0x62DC64 + Update 0x62DF2B `lea [+0xBC]` 已证为向量对象起点 | 追 `VectorClass::Add/Remove` 对该对象的 `[+4]Items/[+0x10]Count` 访问，定 stride | `[未证]` |
| U5 | ParticleClass `+0x12C` StateAI 读者 | ctor 写 0x62B739/0x62BA4B 已证，方法集内读者 0 | 全 `.text` 扫 `+0x12C` 读并归 Particle 函数区间 | `[未证]` |
| U6 | `+0x199 IsFogged` 是否真属"淡出" | 读写点已证为**硬切**（`jne 0x4238A3`）+ 黑雾压暗（0x42362C 置 0），无渐变公式 | 无需（旧文档淡出说已否，见 DISAGREE D3） | `[未证]`（若追问淡出公式） |
| U7 | T5 S07 接口细节（FX Draw 进入 Blitter 的具体 slot / 形状绘制族） | 只做接口定位：DrawIt 0x6D3D10→协调 0x6D8DB0→v65→v69；Draw 0 直接调用者 | S07 已入账结论不重做；如需细化另开卡追 `0x4AED70/0x4BBC90/0x55AF60` 调用链 | `[未证]`（本卡未展开） |
| U8 | `0x5F3E70`（ParticleClass v[23]）是否真为共享 ObjectClass 默认 AI 而非 Particle 自有 | vtable 槽值实测 = 0x5F3E70，7 直接调用者（来自多类）；语义未逐条验 | 反汇编 0x5F3E70 出口/读字段，与 ObjectClass 默认槽对比 | `[静态推断]` |
| U9 | 接口 vtable（obj_off=4/8/0xC）各 6/1/1 槽的 this 调整跳板 | 表存在+槽数已证，槽体未逐条解码 | 参照 KB §0.2 逐条反汇编跳板（sub [esp+4],off; jmp 主实现） | `[未证]` |

> 所有未决均为"证据不足"，按纪律不猜名、不按偏移定语义；已入账主结论（T1/T2/关键字段/槽11/12/65/69）不受影响。
