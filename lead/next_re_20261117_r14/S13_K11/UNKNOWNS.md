# S13-K11 UNKNOWNS

1. D-39 裁决未定：虚函数的环③（体内合同）与环④（体外 vt 引用）是否物理同源、有效环数是否只算 3，Lead 未裁。本卡 9 行 direct call=0、仅活 vptr 安装，与 K8/K10 同形，受该裁决约束；grade 交 [已证] 但 Lead 未裁前不得并入。
2. 0048AE90 无全局 C7 05 安装：raw-masked 扫描（C7 05 <disp32> <imm32=0x7E5144>）全 .text 0 命中；仅有 6 处栈/this 级活 vptr 写。它是否满足卡面 ④ 的“活 vptr 安装点（C7 05 <global>,<vt>）”字面形式，由审计/合并员裁；本卡按 a-S13-K10 VERDICT §5 的同类处理（栈/this 级写算 ④ 外证）照实报。
3. 本卡 9 行均不在 function_atlas.tsv（atlas 12,916 行无这些 entry）：函数边界由反汇编自定（首字节非 E8/E9/EB、前驱 ret + 0xCC/0x90 填充、8 行 23 指令 / 0040F5E0 19 指令完整落到 ret），未用 atlas entry+size。
4. 判别力数字 1,843/1,975 = 93.3% 引自卡面与 a-S13-K10 审计，非本卡自算；本卡未独立重跑族内基线（卡面明示“不要重新普查全族”），仅靠 ①类属独立复算 + ②槽位唯一落点 + ③结构证据三件可分离事实。
5. exact 派发锚 0x4386AB / 0x43942B 的全局对象（如 0x89C668 BombClass 向量）只覆盖本批中 BombClass 一类的槽4 派发；其余 7 个 slot4 类 + 0040F5E0 未逐一找到专属 exact 派发锚，④ 外证一律以活 vptr 安装点为准。
6. 本卡只产出 delta，不改盘上 coverage.tsv / 台账；name 与语义按 RTTI 实际类写，D-37（容器模板 S13/S22 归属）未裁，本卡不自行改 subsystem。
