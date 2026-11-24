# W101 PROGRESS

- 2026-11-14 18:20 | W101 启动 | 已整份读完 R09_COMMON.md。只读约束知悉：不改 ra2youli\、不写 MIX、不启动游戏、不注入。
- 2026-11-14 18:2x | step0 探针 | 复核 gamemd.exe sha256=73201CC0…67476 与底座一致；W97 art 文件 sha256=E1F03783…BA31 一致。复核 crc32("ARTMD.INI")=0xAF902833、crc32("RULESMD.INI")=0x1F674573（未填充 zlib）。17 个 MIX 头全部 dump：大部分 flags=3（加密索引）。
- 2026-11-14 18:3x | 读 mixlib.py 全文 + fs_mix_load_chain_deep.md 全文 | mixlib 格式地面真值（fmt/flags/count + RSA key block + blowfish）；deep doc 装载链/INI 通道/0x5B4430 Find 已 [实证]。
- 2026-11-14 18:4x | step2 exe 扫描 | .text raw sha256 == deep doc 基线（同一镜像）。**全镜像无 0xAF902833/0x1F674573 及一切变体的立即数**。"ARTMD.INI" 字面量 @0x826254，push 于 0x52D034 与 0x679EF6；"RULESMD.INI" @0x826260，push 于 0x52CE24/0x52CF39；"RULEMD*.INI" 通配 @0x52CD98。
- 2026-11-14 18:5x | step3 普查 v1 | 17 个 MIX 加密索引全部解密成功；两个 bug（3 元组解包、data_start 多 8 字节）→ 修复重跑。
- 2026-11-14 19:0x | step4/5 反汇编 | INI 块函数 0x52CD70 全流程；MixFileClass::Find=0x5B4430（strupr→0x4A1DE0 哈希→平坦索引二分，无嵌套下钻）；ctor=0x5B3C20（CCFileClass::Open 打开 → 混合感知 ⇒ 嵌套 MIX 经显式名挂载可达）。
- 2026-11-14 19:0x | step6 哈希破译 | 0x4A1DE0 = zlib CRC 表 + 4 字节块 + **count-pad 终结**（尾块 buf[L]=L 再重复 buf[0]）。TABLE==zlib True。
- 2026-11-14 19:0x | step7 ★核心突破★ | engine_hash("ARTMD.INI")=0x5B47D8D5、("RULESMD.INI")=0x8218F9F4、("LOCALMD.MIX")=0xFBE0D09D、("LOCAL.MIX")=0xA8548FD9、("ART.INI")=0xF91B2C8B —— **五个零售未知 id 全中**。名字从未被改，此前是哈希算法用错。
- 2026-11-14 19:1x | step8 | 挂载点实证：0x5303CD push "LOCALMD.MIX" → ctor(0x5B3C20, key=0x886980)；LOCAL.MIX 同构。散装无 art/rules 类 INI；RA2MD.INI=[Intro] 选项文件；ra2forge_install.json 证实 ra2forge 未触碰大 INI。
- 2026-11-14 19:1x | step3 普查 v2（后台） | 严格 TD 判据 + countpad 命名方案 + utf-8 stdout，补全 ra2.mix/ra2md.mix 嵌套树 → 待收。
