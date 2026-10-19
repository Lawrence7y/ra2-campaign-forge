# W3-CS2 派工单 · **APP1 后的台账读数重钉：33 处 `2,538` 引用与 8 条 stale_readings 处置**（Qoder CN · 新会话 · 台账写域）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **两个已验收事实**：
> 1. **APP1 已把 10 章正文追加进原版侧 ATLAS**：`238,788 B / 2a917e45f890` → **`1,212,472 B / 1dce588aa505` @18:17:38**；**`atlas_unique_va 2,582 → 7,110`（净 +4,528，守恒 True）**（`qc/W3_20261002/app1_append/verify_app1.py` 34/34）。
> 2. **APP1 的 `stale_readings.json` 列了 8 条过期读数（3 条仍有效）**；而任务 C 复核时**台账里引用 `2,538` 已达 33 处**（6〔改〕/ 8〔注〕/ 19〔成〕，C1 已落 6〔改〕）。
> ⇒ **本卡 = 把 APP1 的分母巨变传播进台账**，让"引用 2,538 的处数"不再指向一个已不存在的分母。

## 🔴 铁律（先读）
1. **官方工具是唯一权威**：`tools/atlas_va_crosscheck.py` 指向**自己的输出目录**重跑；**每个新读数记命令 + 参数 + ATLAS mtime/sha + 作用域标签**（`E-W3-04`）。
2. **先复算、后分类、再落地**：
   - **复算**：用**任务 C 相同的作用域**（`_LEAD_TASK_C_caliber_consistency.md` / `CALIBER_CONSISTENCY_AUDIT.md` 里登记的档位）在 post-APP1 ATLAS 上重跑 ⇒ 得 `new_readings`；**并留 pre-APP1 复算**（用 `app1_append/snapshots/` 的快照跑一遍）证明"只是分母变了，我的档位没漂"。
   - **分类**：33 处逐处判 `STALE（数字已变，需更新）/ STILL_VALID（作用域无关，如行内哈希）/ SCOPE_SHIFTED（分母变了但结论方向不变，需加注）`。
   - **落地**：台账文件**追加式**（原句保留 + `【W3-CS2】` 注记：新值 + 复算命令 + 时刻）；**`verify_ledger.py` 改前改后两次必须 EXIT=0**（红灯即回滚）。
3. **`stale_readings.json` 8 条逐条处置**：3 条仍有效的**给"仍有效"的证据**；5 条过期的**给新值 + 指向本卡复算记录**。
4. **禁止**：① 不许把 7,110 写进任何 `comparable=false` 的口径行 ② 不许删旧数字（追加式）③ 不许改 `COVERAGE_LEDGER.md` 之外的他人件 ④ **不碰 ATLAS**（写者是 ZCode 的 APP1 会话）。
5. **写域**：`out/re_work/qc/W3_20261001/coverage_ledger/**`（台账两件 + 追加式注记）+ `out/re_work/qc/W3_20261002/cs2_readings/`
6. **空扫描报 `INSTRUMENT_FAILED`**。

## 交付
`CS2_REPORT.md`（§A 十节骨架；`[0]` 直答：pre/post 两套读数表、33 处分类计数、8 条处置清单）· `new_readings.json`（含命令/参数/mtime/sha/作用域）· `citation_triage.json`（33 处逐处）· `stale_readings_disposition.json`（8 条）· `runs/`（`verify_ledger` 改前改后两次原文）· `verify_cs2.py`（**EXIT=0 + `verdict tally` 行**）

## 回报 `[0]`
① pre/post 读数对照（带作用域）② 33 处分类计数 ③ 8 条处置 ④ verify_ledger 两次 EXIT ⑤ 反向验证（抽 1 处"仍成立"核其证据）⑥ `verdict tally` 原文

## 底线
> **宁可交"33 处里 12 处 STALE 已注新值、14 处仍有效给了证据、7 处我不确定分类"，也不要交"全部更新为 7,110"—— 分母变更不是橡皮图章。**
