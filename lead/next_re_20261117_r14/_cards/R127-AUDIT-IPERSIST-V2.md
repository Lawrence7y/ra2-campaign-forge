# R127 跨家族审计卡（第二版）· hy4flash

你是 R127 的独立审计员，家族为 hy4。主会话家族为 deepseek。只做审计，不改任何文件。

## 更正说明（请先读这一段）

本卡第一版（发给了另一家族）第 5 条写错了：它要求复核「0x7ea564 与 0x7e36d4 两个 vtable 的
+0xc 槽值是否等于 0x429270 与 0x429360」。主会话实测 0x7e36d4 的 slot0 是 0x429360、
slot3（即 +0xc）是 0x429420。所以那个表述是错的，已在本版改正为按实测槽号核对。
如果你在别处看到「0x429360 在 +0xc」的说法，那是错的。

## 背景

镜像 ra2bench/gamemd.exe，sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，
4825360 字节，PE32 i386，ImageBase 0x400000。主会话本轮主张四条。

主张一（接口定名）：0x7f7c80 与其 .data 孪生 0x820270 是 IPersistStream；
0x7f7c70 与其 .data 孪生 0x818858 是 IPersist。依据是实参契约而非共现：
  (a) 导入表里 ole32!OleSaveToStream 在 0x7e15f4，ole32!OleLoadFromStream 在 0x7e15f8，各一槽。
  (b) 以 0x820270 作 riid 的 8 个 QI 站点，从 push 之后正向反汇编到 ret 为止，全部命中
      call dword ptr [0x7e15f4]。8 个 push 站点是 0x4af856、0x4b6313、0x4db76a、0x50469e、
      0x54b83c、0x69ef66、0x719d96、0x75c756。OleSaveToStream 第 2 实参契约是 IPersistStream。
  (c) 反向：以 0x818858 或 0x7f7c70 作 riid 的 16 个站点，同样正向扫到 ret 为止，无一命中该 call。
  (d) 010C 那侧靠方法数上限：16 个站点上 QI 结果只在 +0xc 出现（例 0x42cab5 的 ff 50 0c），
      三个站点 0x4d5892、0x73e7b7、0x742815 是 call [reg+0xc] 带 4 字节出参后接
      mov edi,<类自己的 CLSID> 与 repe cmpsd，三个 CLSID 互不相同。

主张二（撤回错误表述）：0x7e36c0 与 0x7e9b20 都在 .rdata、各 16 字节，是 IID 常量，不是 QI 体。
0x7e36c0 = {96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}，
0x7e9b20 = {5FF0CA70-8B12-11D1-B708-00A024DDAFD1}。

主张三（接受点完整）：它们的接受点（体内把 riid 与该 IID 做 repe cmpsd 的 QI 体）恰三处，
且宿主集合完整：
  0x429360 在 vtable 0x7e36d4 的 slot0，类 .?AVApplicationClass@@
  0x429270 在 vtable 0x7ea564 的 slot3（+0xc），类 .?AVTiberianSunClassFactory@@
  0x6cf430 在 vtable 0x7f4108 的 slot0，类 .?AVSwizzleManagerClass@@
完整性依据：三个入口被当作 bf 立即数或 68 立即数引用的次数全为 0，故除 vtable 槽外无第二条
引用路径。

主张四（定名）：0x7e36c0 = .?AUIApplication@@，0x7e9b20 = .?AUISwizzle@@。
依据是宿主类 RTTI 在 mdisp 0 处的非 IUnknown 接口名唯一。

## 你要做的事（只读，用 python3 + pefile + capstone，脚本全放 /tmp，不写项目目录）

1. 独立复算导入表里 OleSaveToStream 与 OleLoadFromStream 的 IAT 槽地址与所属 DLL。
2. 独立复算 0x7f7c80 与 0x820270 的 16 字节是否逐字节相同；0x7f7c70 与 0x818858 同问；
   并复算跨对是否不同。同时报出这四处的 GUID 文本形式。
3. 独立复算以 0x820270 为 riid 的 push 站点数（形态 68 70 02 82 00），并逐站点从 push 之后
   正向反汇编到 ret，报出是否命中 call dword ptr [0x7e15f4]。8 个都要给。
4. 独立复算以 0x818858 与 0x7f7c70 为 riid 的 push 站点数，并逐站点做同样的正向扫描，
   报出命中 call [0x7e15f4] 的站点数。
5. 独立复算 0x7e36d4 的 slot0 与 slot3(+0xc)、0x7ea564 的 slot3(+0xc) 的值，
   核对是否分别为 0x429360、0x429420、0x429270。并复算 0x429360 与 0x429270 两个函数体
   内是否都出现 0x7f7c90（IID_IUnknown）的比较。
6. 独立复算 0x7f4108 的 slot0 是否等于 0x6cf430，以及该类 RTTI 基类表三条的名字、
   mdisp 与 ncb（ncb 在 BC 结构 +4 处，不是 +16）。
7. 独立复算全 .rdata 里 u32 值等于 0x429360、0x429270、0x6cf430 的全部位置，
   逐个判定是否落在某个 vtable 槽上，报出宿主类名。这三个入口被 bf/68 立即数引用的次数是多少。
8. 对抗性检查：有没有任何一处字节证据能推翻上述四条主张？特别查
   (i) 是否存在把 0x818858 或 0x7f7c70 的 QI 结果喂给 call [0x7e15f4] 的站点；
   (ii) 是否存在以 0x7e36c0 或 0x7e9b20 为立即数的第二处 QI 体（即第四个接受点）。
   若有，逐处给地址与指令文本。

## 输出

报告写到 /tmp/r127_audit_hy4.md，纯文本 Markdown，禁止使用反引号字符。
逐条给 PASS 或 FAIL 与实测数字，最后单列一节「与主张不符之处」。
另请在报告末尾注明你的回合数与用时。不要写任何文件到项目目录。
