# S13-K5 UNKNOWNS

## U1 — 分母口径未裁（必须 Lead/用户裁决）
240 口径含 92 行容器模板实例化；coverage_README.md 的 class_to_sub 建议把这些归 S22。本卡只登记两种分母，不宣布达标/未达标。需输入：是否采用 148 口径、是否同步把 92 行 subsystem 改 S22/sem=container_template 的合并指令。

## U2 — 与 0x75E3B0 的「同型」边界
创建核心同型（name filter + registry scan + push size→new→ctor），但返回约定不同：0x75E3B0 返回对象指针/NULL；0040F510/0046C440 返回注册索引/-1。本卡按真实语义命名 FindOrMakeIndex，未把先例名当巧合。

## U3 — 两个额外 thunk 的登记边界
0046B990/0046B9A0 字节上可证为 return-address adjust + tail-jmp thunk（目标已逐条至 ret），但名字仍是 BulletClass::slotN 占位名，且本卡派工只要求 6 行入 delta。故 census 记为「可证(行为级未入 delta)」，不把 proved 从 74 抬到 76。若 Lead 要求按行为级 proved 计入，可另开 2 行 delta。

## U4 — death_handler 真名仍未语义闭合
00708080 是唯一残余真名行，但入口到 ret 是 1846B 复杂死亡处理路径；本卡没有完成全部写入点/所有分支的行为级证明，故 grade 不动。

## U5 — 164 行缺链性质
"不可证(缺链)"只表示本卡字节判据下不能升语义，不是证明语义不存在；多数行的缺环是字段偏移语义锚点、对象 RTTI/ctor 注册闭环或 INI 键→字段写回配对。逐行见 EVIDENCE/byte_census.tsv。
