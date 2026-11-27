# 卡 r161_e2_audit · R161 只读复核（跨家族审计员）

角色：audit（只读复核）。模型：work/cn:deepseek-v4.1-flash。预算 8 分钟，上限 35 轮。
禁止修改任何文件（包括 /tmp 之外的生产文件）；只读、只报。

## 被审对象
新文件 /home/t628/projects/ra2-campaign-forge/_r161/gate_runner.py（门禁串联 runner）。
它要解决的事实前提是：主门禁 lead/next_re_20261117_r14/check_disc.py 全文不读 FACT_INDEX.tsv，
事实层守门 _r160/facts_floors.py 只能手动跑，仓库里没有把两者串起来的 runner。

## 请逐条判：下列 8 条命题哪些成立、哪些不成立（每条给一行判定 + 证据行号或命令）
1. check_disc.py 里大小写敏感的字符串 FACT 出现 0 次（与 facts_floors.py 的存在理由相关）。
2. gate_runner.py 的 G3a 真的比对三处 GATE_VER（脚本常量 / DISC_RECHECK 第 20 行 col6 / DISC_UNVERIFIABLE 第 20 行 col4），
   三处取值必须完全相同才 PASS；请核对它取的是不是这两行、这两列。
3. G3b 用现盘 sha256(DISC_UNVERIFIABLE.tsv) 去比 check_disc.py 的 FREEZE_SHA256 常量，而不是比某个手抄值。
4. G3e 重算 C16_FLOORS_SHA256 时的规范化方式（逐 id 排序、冒号、逗号）与 check_disc.py 里生成该常量的方式是否一致；
   若不一致，这个断言会恒 FAIL 或恒 PASS —— 请明确指出属于哪种。
5. G3f 重算 facts MASTER_SHA256 时，是否与 _r160/facts_floors.py 里 D9 段拼接的字段**顺序与内容**完全一致；
   若不一致请指出差在哪一个字段。
6. 自测 S1：把台账里一个汉字换成另一个汉字（总字节不变）后 facts_floors 报 D0 —— 这条能否证明「等长改写被抓住」？
   有没有可能它其实是被别的断言抓住的？
7. 自测 S3：沙箱基线必须 exit 0 才有意义。请判断当前沙箱构造（仓库根逐项符号链接 + lead/ 逐项链接 + tier 目录五个实体副本）
   是否仍有可能因为路径缺失产生假 FAIL；若你发现还有遗漏的路径，请点名。
8. 边界声明是否诚实：文件里写「同改数据与常量仍能过」。这句话对 G3a..G3f 六条断言是否也成立？请逐条判。

## 交付格式
- 8 条各一行，格式：编号 + 成立/不成立 + 依据（文件:行号 或 命令输出摘要）。
- 最后单列一节「你建议但本卡未要求的加强项」，最多 3 条，不要展开实现。
- 不要复述文件内容，不要写客套话。
