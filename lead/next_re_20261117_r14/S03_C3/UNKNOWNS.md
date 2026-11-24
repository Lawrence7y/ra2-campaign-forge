# S03-C3 · UNKNOWNS

1. **006C9890 归属分歧**：台账 `GOAL_THREE_TARGETS_20261018.md:20586` 把 `0x006C9890` 列在 `File_Stream_Crypto` 表（col=10/67），与盘上 subsystem=S03/name=FileStraw::slot1 不同。按 ⑱ 只报不改名；是否改归 D-37 类歧义由 Lead 裁，本卡不动 subsystem 与 name。
2. **③ 的语义命名边界**：本卡 ③ 严格按字节机械可述（读/写/返回/调用约定/错误路径）落笔；vt+4 / vt+0x34 / vt+0x1C / vt+0x28 / vt+0x40 等槽的**业务名**（如 GetName/Close/Seek/Error）未从 YRpp 地址绑定独立证实，故 ③ 只写「虚调用 + 参数 + 效果」，不据名推断——符合 §8.5 主条（docs/台账不得作名字第二通道）。
3. **00552490 / 00631CC0 / 0065D150 的 caller 全为 `[未证]` 或 NULLFN**：④ 的 direct-call 站点字节成立即满足 D-40；caller 自身未证不影响本行四环，不作「已证 caller 强度」主张。
4. **00431E80 的两条共享 RTTI 链**：`.?AVBufferIOFileClass@@`（本卡采用）；未发现与盘上名冲突的第二张表，若后续有 YRpp 地址绑定给不同名，按 ⑱ 另报。
5. **补③前 S03 四环基线为 0/194**：随机基线只对「①②④」基率有意义；③ 是本次新落笔的环，无法从盘上历史数据估基率，故按「补前 E[7]=0」如实记。
