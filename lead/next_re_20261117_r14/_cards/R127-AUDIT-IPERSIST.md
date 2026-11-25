# R127 跨家族审计卡 · deepseek-v4.1-flash

你是 R127 的独立审计员，家族为 deepseek。主会话家族为 hy4。只做审计，不改任何文件。

## 背景（主会话本轮主张，待你逐条对抗）
镜像 ra2bench/gamemd.exe（sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，
4825360 B，PE32 i386，ImageBase 0x400000）。本轮主张两条：

主张一（GUID 定名）：0x7f7c80 与其 .data 孪生 0x820270 是 IPersistStream，
0x7f7c70 与其 .data 孪生 0x818858 是 IPersist。依据不是外部头文件，而是两条字节行为：
  (a) 有 8 处 QI 内联点以 0x820270 作 riid，其返回指针被立即当作第 2 实参传给
      ole32!OleSaveToStream（IAT 槽 0x7e15f4）；另有 35 处以 0x7f7c80（同一 GUID 的
      .rdata 拷贝）出现在 OleSaveToStream 调用前的 push 序列里。OleSaveToStream 的
      第 2 实参契约要求 IPersistStream，故 0x820270/0x7f7c80 = IPersistStream。
  (b) 以 0x818858/0x7f7c70 作 riid 的 QI 点，其返回指针上被调用的虚槽只有 +0xc 一处族
      （带一个 4 字节出参），从不触及 +0x10/+0x14/+0x18/+0x1c，故该接口方法数上限为 1，
      与 IPersist（仅 GetClassID）相符，与 IPersistStream（4 方法）不符。

主张二（两个 QI 体的归属）：
  (a) 0x7e36c0 的直属宿主是 TiberianSunClassFactory（vtable 0x7ea564 的 +0xc 槽）
      与 ApplicationClass（vtable 0x7e36d4 的 +0xc 槽），且两份 QI 体都同时显式比较
      0x7f7c90（IID_IUnknown），故 0x7e36c0 不是 IUnknown。
  (b) 0x7e9b20 的直属宿主是 SwizzleManagerClass（vtable 0x7f4108 的 slot0 即 0x6cf430），
      该 QI 体同时显式比较 0x7f7c90，且该类 RTTI 只有 ISwizzle 与 IUnknown 两个 mdisp 0
      接口，故 0x7e9b20 = ISwizzle。

## 你要做的事（只读，用 python3 + pefile + capstone，全部脚本放 /tmp，不要写进项目目录）
1. 独立复算 IAT 槽 0x7e15f4 的导入名，确认它是不是 OleSaveToStream。
2. 独立复算 0x7f7c80 与 0x820270 的 16 字节是否逐字节相同；0x7f7c70 与 0x818858 是否逐字节相同。
3. 独立复算 0x820270 的 push 站点数，以及与 OleSaveToStream 调用相邻的站点数。
4. 独立复算 0x818858/0x7f7c70 的 QI 站点上返回指针被调用的虚槽偏移集合。
5. 独立复算 0x7ea564 与 0x7e36d4 两个 vtable 的 +0xc 槽值是否等于 0x429270 与 0x429360，
   并复算这两个函数体内是否都出现 0x7f7c90 的比较。
6. 独立复算 0x7f4108 的 slot0 是否等于 0x6cf430，以及该类 RTTI 基类表内容。
7. 对抗性检查：有没有任何一处字节证据能推翻上述两条主张？特别是
   (i) 是否存在以 0x818858/0x7f7c70 为 riid 后调用 +0x10 或更高虚槽的站点；
   (ii) 是否存在把 0x818858 的结果传给 OleSaveToStream 的站点。
   若有，逐处给地址与指令文本。

## 输出
报告写到 /tmp/r127_audit_deepseek.md，纯文本 Markdown，禁止使用反引号字符，
逐条给 PASS/FAIL 与实测数字，最后单列一节「与主张不符之处」。不要写任何文件到项目目录。
