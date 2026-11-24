# ⚠️ 本文件已消费 —— 不要再次追加

**本文件的 `## 2.28` 段已于 R41 追加进 `R14_COMMON.md`**
（R14_COMMON 316,689 → 322,283 B，CR 1,081 未变，备份 `R14_COMMON.before_s228_125304.md`）。

若未来某轮再次把本文件当草稿追加，会造成 **`§2.28` 重复**（R36 已发生过一次同类事故：
`str.replace` 静默失配导致 `§2.22` 被追加两遍）。

**幂等自检（下轮可直接跑）：**

```powershell
$rc = [IO.File]::ReadAllText('D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md')
([regex]::Matches($rc, '(?m)^## 2\.28')).Count    # 必须恰为 1
```

---

（以下为原草稿正文，仅作历史留存，**不要执行**。）
