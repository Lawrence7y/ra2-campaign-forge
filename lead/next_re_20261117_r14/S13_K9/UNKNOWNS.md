# S13-K9 UNKNOWNS

1. **[未证] 3 漏扫行（0048AD60/0054E8E0/0048AD70）为何无 exact 调用**：它们的 vtable 未被任何 `C7 05 [global],vt` 写成活 vptr（或调用点以 this 指针非全局单例形式派发）。③ 不成立，但「为什么」需追这些对象是否栈上/成员内嵌实例——本卡不改分母、不扩任务面，留给后续卡。
2. **[未证] 运行时是否真正走到这 18 个 exact 站点**：本卡是静态字节裁定（双通道），未做真机。D1 活 vtable（构造器写 DynamicVectorClass）与 D2 析构 vtable（VectorClass）的切换时点由构造器/析构器代码静态推定；真机命中未测（D-36 仍禁）。
3. **[未证] 0040F7C0 的 slot4 伙伴 0x40F870**：F2 vtable(0x7E1E84) slot4=0x40F870，a-S13-K6 未把它列入 11 行（正确，它是「退34」之一）。本卡不碰它。
4. **[未证] 命名冲突全库扫描**：按纪律⑱应对 14 个 entry 地址查 docs/re + re_atlas/kb + 台账 + COVERAGE。本卡 name 用「类<slot 语义>」保守名（SetCapacity/FindItemIndex），未发现冲突但完整全库 grep 未逐文件跑——非本卡单目标（裁定 exact 存在）所需。
5. **[静态推断] slot2=SetCapacity 的具体语义**：体内字节（lea eax,[ebp*4]; call operator new; 复制指针数组; ret8）强支持，但未找到 YRpp 源码行级对照；按「字节合同」报，命名置信度高但未升 [已证] 的源码级。