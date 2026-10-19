# 测量记录 Schema 与使用说明

> 本文件是 `tools/validate_measurement.py` 的配套使用说明，对应规范件  
> `out/re_work/work_chain/IMPL001/perf/control/spec/measurement_contract.md` v1。

---

## 1. 记录形态概览

`tools/validate_measurement.py` 只做**元数据层面的最小验收**：判断一份真实负载记录 JSON 是否具备可复现测量所需的字段与形态。  
**本验证器不证明输入数据是真机实测，不证明哈希对应的镜像真的被测量，不证明单位计数来自实际运行。**

---

## 2. 最小合法记录示例（合成示例，非真机数据）

下面是一份**完全合成**的最小合法记录，用于演示字段形态。其中的硬件描述、场景名、哈希值与单位数均为虚构，**不代表任何真实测量**。

```json
{
  "schema_version": 1,
  "target_exe": "gamemd.exe",
  "exe_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "config_sha256": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
  "map_sha256": "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",
  "hardware": "SYNTHETIC-BENCH-001",
  "scenario": "synthetic_baseline_3runs",
  "runs": [
    {
      "actual_units": 100,
      "count_source": {
        "kind": "runtime",
        "evidence": "Memory probe at ObjectClass::Array size, tick 3000"
      },
      "tick_ms": [15.2, 16.1, 15.8, 16.4, 15.9]
    },
    {
      "actual_units": 200,
      "count_source": {
        "kind": "runtime",
        "evidence": "Memory probe at ObjectClass::Array size, tick 6000"
      },
      "tick_ms": [18.4, 19.1, 18.7, 19.5, 18.9]
    },
    {
      "actual_units": 300,
      "count_source": {
        "kind": "runtime",
        "evidence": "Memory probe at ObjectClass::Array size, tick 9000"
      },
      "tick_ms": [23.1, 24.0, 23.5, 24.8, 23.9]
    }
  ]
}
```

**说明**：上例中 `hardware`、`scenario`、`evidence` 均为合成占位文本；哈希值使用公开空串/标准测试向量，不代表任何真实游戏二进制或配置文件。

---

## 3. 顶层字段约束

| 字段 | 类型 | 约束 | 失败字段路径 |
|---|---|---|---|
| `schema_version` | 整数 | 必须等于 `1`；布尔值不算整数（`true` 非法） | `schema_version` |
| `target_exe` | 字符串 | 只能是 `game.exe` 或 `gamemd.exe`（大小写敏感，不做归一） | `target_exe` |
| `exe_sha256` | 字符串 | 恰好 64 位十六进制字符（`[0-9a-fA-F]{64}`） | `exe_sha256` |
| `config_sha256` | 字符串 | 同上 | `config_sha256` |
| `map_sha256` | 字符串 | 同上 | `map_sha256` |
| `hardware` | 字符串 | 去空白后非空 | `hardware` |
| `scenario` | 字符串 | 去空白后非空 | `scenario` |
| `runs` | 数组 | 至少 3 组 | `runs` |

---

## 4. 每组 `runs[i]` 字段约束

| 字段 | 类型 | 约束 | 失败字段路径 |
|---|---|---|---|
| `actual_units` | 整数 | 正整数（≥1）；布尔值非法 | `runs[i].actual_units` |
| `count_source.kind` | 字符串 | 必须等于 `runtime` | `runs[i].count_source.kind` |
| `count_source.evidence` | 字符串 | 去空白后非空（可定位说明） | `runs[i].count_source.evidence` |
| `tick_ms` | 数组 | 非空；每个元素为有限、严格大于 0 的数值（整数或浮点，布尔值非法） | `runs[i].tick_ms`、`runs[i].tick_ms[j]` |
| `declared_units` | 可选，整数 | 若存在必须为正整数（布尔值非法）；仅作地图名义负载信息 | `runs[i].declared_units` |

**关键规则**：
- `declared_units`（地图名义负载）**不得**用于生成、推导或替代 `actual_units`；不得把名义值写入实际计数。
- 缺失字段与类型错误同样按上表字段路径报错；`count_source` 缺失时报 `runs[i].count_source`。
- `NaN`、`Infinity`、`-Infinity` 必须被拒绝，路径为 `runs[i].tick_ms[j]`。
- 未列出的额外字段一律忽略，不报错。

---

## 5. CLI 与退出码

```bash
python tools/validate_measurement.py <input.json> [--json]
```

| 退出码 | 含义 |
|---|---|
| `0` | 输入数据有效，校验通过 |
| `1` | 输入数据无效（校验失败） |
| `2` | 用法错误或文件不可读 / JSON 语法错误 |

- 无参或参数过多 → 退出 2 并打印用法。
- 默认输出人类可读文本；`--json` 输出机器可读 JSON（单个对象，stdout）。
- 校验失败时必须给出**字段路径**，一条一行，且可被 `--json` 模式以数组形式取到。

**有效输入的人类可读输出至少包含**：

```
[OK] schema_version=1 target_exe=<...> runs=<n>
run[<i>]: actual_units=<n> samples=<n> median=<x> p95=<y> p99=<z> declared_units=<n|absent>
...
NOTE: 元数据校验通过不代表输入数据真实；declared_units 仅为地图名义负载，不生成实际单位数；各 run 保持独立，不合并曲线、不宣称收益。
```

**无效输入的人类可读输出至少包含**：

```
[FAIL] <n> 个字段错误
 - <field_path>: <原因>
```

---

## 6. 统计算法（强制，供独立复算）

- 对每个 run 的 `tick_ms` 升序排序后按原数组元素计算，**不插值**。
- `samples` = 数组长度。
- **中位数**：`n` 为奇数取第 `(n+1)/2` 个（1 基）；`n` 为偶数取中间两个元素的算术平均。
- **nearest-rank 百分位**：`index = ceil(p/100 * n)`，1 基，并裁剪到 `[1, n]`。因此 `p95` 取 `ceil(0.95*n)`，`p99` 取 `ceil(0.99*n)`。`n=3` 时 p95 与 p99 都等于最大值，这是该方法的正常结果，不许改用线性插值。
- 输出数值保留原始精度（不得舍入到少于 6 位小数）；`--json` 中为 JSON number。
- 只统计，不做跨 run 聚合平均值或收益对比。

---

## 7. 限制声明

1. **验证器只验证记录形态**，不证明数据真伪、不宣称性能收益。
2. 本工具**不执行**输入文件中的任何命令，**不修改**输入文件，**不联网**，**不访问**游戏目录。
3. `declared_units` 仅为地图名义负载，不能替代 `actual_units`。
4. 不同 `runs` 的负载保持分组呈现，**不合并**成一条曲线，**不自动**宣称性能收益。

---

## 8. 与 H1 重测 / 后续真实采样卡的关系

- 本工具及其产出（集成件 `tools/validate_measurement.py` 与本文档）构成**离线基线元数据验证器**。
- 通过本工具校验的记录，仅表示其 JSON 形态符合 `measurement_contract.md` v1 的可复现测量字段要求；**不等同于 M0 高负载测量完成**。
- 下一步为**真实场景采样卡**（需由专门任务卡明确边界），届时需补充：
  - 运行时取证与游戏实例启动说明；
  - 真实采样环境、哈希与 `actual_units` 的来源证明；
  - 与本基线工具的结果对照与差异分析。
- 本包的未闭合项见 `out/re_work/work_chain/IMPL001/perf/integration/worker/REPORT.md`。

---

## 9. 运行示例

```bash
# 人类可读输出
python tools/validate_measurement.py out/re_work/work_chain/IMPL001/perf/fixtures/valid/valid_baseline.json

# 机器可读 JSON 输出
python tools/validate_measurement.py out/re_work/work_chain/IMPL001/perf/fixtures/valid/valid_baseline.json --json
```

> 注意：上述示例中的 `valid_baseline.json` 本身属于已验收原型夹具集，仅供格式参考；其中硬件描述仍为夹具内文本，不代表本工具生成的任何真机声明。
