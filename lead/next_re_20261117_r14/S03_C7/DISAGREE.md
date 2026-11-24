# S03-C7 DISAGREE（与上游卡/审计的分歧与确认记录）

## D1 · 00432050：确认审计判定（C6 delta「缓冲读」语义反向）
- **上游**：S03_C6/coverage_delta.tsv 把 `00432050`（CDFileClass::vslot12）写成「缓冲**读**(buffer,count)… 非缓冲态委托 WriteFile」——自相矛盾（读却委托写）。M43 MERGE_LOG line15 据此整行拒绝、维持 `[静态推断]`。
- **C6 审计**（`S03_C6/_audit/VERDICT.md` line20/25）：判「语义方向反了：它是缓冲**写**，不是缓冲**读**」，列三条证据（Raw.slot12=WriteFile；`+0x228 call 0x65CDD0` 即该 Write；`+0x125 memmove` dst=内部缓冲）。
- **本卡独立复核结论**：**同意审计**。三条独立字节证据全部指向 WRITE、无一条指向 read：
  1. 非缓冲支路 `+0x228 call 0x65CDD0` → 体内 `+0x052 call [0x7E11A0]`=KERNEL32!WriteFile；
  2. 缓冲拷贝 `+0x125 call 0x7CA090`(memmove) 的 dst=`[esi+0x30]+[esi+0x38]`=内部缓冲、src=调用者缓冲（数据流入缓冲）；
  3. 模式闸 `+0x04F cmp eax,1` 对读模式报错误码 `0xD`(13)，`+0x109` 置脏标 `[esi+0x27]=1`。
- **处置**：按任务「核通 ⇔ 给出正确语义与 ③b 证据」，本卡给出 ③b④ 级正确语义（见 `EVIDENCE/REPROCESS_00432050.md`）。但 00432050 在 C6 排除集内、非本卡 8 行作业面 ⇒ 不新增第 9 行、不进本卡 delta；盘上保持 `[静态推断]` 待后续 M 卡改写。**此处不是与审计分歧，而是确认审计、并补齐其未落笔的正确语义。**

## D2 · ② 归属（⑯）与 name 栏占位名的关系（无分歧，口径声明）
- 004325C0（CDFileClass::vslot13）② 有 CDFileClass/BIO 两表同 slot ⇒ 按 §8.1 ⑯ + M1 归基类级 **BufferIOFileClass**；0065D1F0 三表同 slot14 ⇒ 归最基 **RawFileClass**；00631D30 五表同 slot1 ⇒ 归 **Pipe**。三行 name 栏仍保留盘上占位名（`CDFileClass::vslot13` / `CDFileClass::slot14` / `FilePipe::slot1`），与 C4/C5/C6 既有口径一致（name 属 DoD D-38 待裁，不在本卡改）；② 栏类名全部声明为 RTTI 字节实测，判据2（②栏类名与 name 类一致）逐行核过：行名类前缀与持有表集合交集非空，无自相矛盾。

## D3 · 基线口径（无分歧，口径声明）
- 本卡报 ③b 基率 strict 19.78% / loose 35.16%（池 91，seed 20261119，2000 次）。不采用「②∧④ 入选率」当基线（§8.7 判据4：那是 A 集合入选谓词本身）；不把 `K=8×p` 当校验（判据3：恒等式）。两档操作化在 `work/baselines.py` 固定，可复跑。

## D4 · 与 SURVEY_RING24 池差（无分歧）
- SURVEY-RING24 报 S03 A=31、n(静态推断)=109；本卡池 91 是「当前盘上 coverage 静态推断 ∩ 有 CFG extent」，109→91 差 18 为 M39/M40/M43/M44 逐轮并入后 grade 升级退出 `[静态推断]` 池所致。A=31 为 ②∩④ 结构集合，与池实时缩水无关；两数不同源、不冲突。
