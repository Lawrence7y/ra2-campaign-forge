# UNKNOWNS

- 静态反汇编未做运行时对象类型采样；BufferIO 归属以 vptr 写入、vtable 槽、this 来源和布局/基类虚调用为证。
- 0x431A30/0x431BC0/0x431D90 无直接 call 目标引用，可能为间接调用或已废弃路径；站点仍属 BufferIO 对象布局，计入静态写/读点。函数名仅为描述性标签。
- 0x544BE0 等站点的对象来自虚调用返回值，未能证明为 BufferIO 族，按 fail-closed 排除。
- 0x431F50 是 BufferIO 槽8，但体内无 +0x29 站点；不贡献计数。
