# S03-K1 · UNKNOWNS（未解决项）

| # | 项 | 现状 | 下一步取法 |
|---|---|---|---|
| U1 | CCFileClass 继承状态字节 `+0x19/+0x25/+0x29` 精确语义 | 有读点(`431F10`/`431F30`)无独立写点定位，标 `[静态推断]` | dump `0x431F10..0x4326xx` 全族，逐字节回溯这三个字节的写者 |
| U2 | `MixFileClass+0x12` 缓冲归属字节的填充点 | 只有 free 路径读点(`5B3F14` 等)，Cache() 填充点未定位（与线索文档 §8 未闭环 2 一致） | 对 `+0x12`/`+0x24` 设写 watch（真机）或反查 `0x5B3E90` Cache 家族 |
| U3 | RSA/Blowfish 分组解密逐条链（密钥块 80B、56B Blowfish key） | 只落实入口常量（PKStraw`633050`/e=0x10001/blowfish.dll），未逐条 dump 到分组运算 | dump `0x633130 PKStraw::Get` + `0x631F60` 公钥 ctor + COM 绑定 `0x6BEDB0` |
| U4 | `crc_hash=zlib.crc32(name.upper())` 与真实 mix 产物吻合 | 仅引用线索文档，本卡未在磁盘产物上独立复算 | 对 `ra2youli\expandmd98.mix` 5 条目跑 CRC 对照（需产物，本卡未做） |
| U5 | 两类"GetSize"值口径 | 类中无 v[12] GetSize；给出对象大小 0x6C/0x28（new↔字段两处对账） | 若审计坚持要 v[12] 常量，需确认是否指别的类；本卡已按纪律停机说明 |
| U6 | RULE 选择 DialogBox 后"把 RULESMD.INI 插数组第 0 位"的精确代码点 | 已入账 §3，本卡 E07 只定位到对话框 IAT 与多次 Load，未逐条追插入位 | dump `0x52D000..0x52D400` 对话框回调与数组操作 |
