## 1. 文件指纹
coverage.tsv  bytes=4016071  sha256=325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2
gamemd.exe    bytes=4825360  sha256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476
atlas         bytes=427038

## 2. coverage.tsv 形状
header(逗号分隔提示): entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict
数据行 = 18498 ; 列数分布 = {8: 18498}
atlas 条目 = 12916

## 3. grade 分布（全表）
  [未证]          10969   59.30%
  [静态推断]         5875   31.76%
  [已证]           1654    8.94%

## 4. atlas 内/外
atlas 内行 = 12916 ; atlas 外行 = 5582
atlas 内 [已证] = 1648 ; atlas 外 [已证] = 6
atlas 内【全部】[已证]口径（不限 grade 列位置）:
  atlas 内 且 grade=[已证] = 1648

## 5. TOTAL strict（atlas内 ∧ [已证] ∧ 第4列不含字面 "[未证]"）
TOTAL strict = 1331  (分母 atlas_n=12916, 10.31%)
对照：不做 ne() 归一时 atlas 内行 = 12916（差异即小写 entry 漏配数）

## 6. ④ 已成文（grade=[已证] ∧ 第4列含字符 ④）
④ 已成文 = 319 / 1654 = 19.29%
[已证] 且第4列含 [未证] = 317
（check: 1654 - 317 = 1337 ）

## 7. 逐子系统（strict_panel.py 口径）
S     atlas  namedS14 namedStr  proved provedSt   four  thrN thrP  n%(R14) n%(str)  p%  p%(str)  nominal strict
S01       53        11        9       6         6      1    48   27    20.75   16.98 11.32   11.32   False False
S02      330        41       34      35         5      2   297  165    12.42   10.30 10.61    1.52   False False
S03      194       125       12      39        37      5   175   97    64.43    6.19 20.10   19.07   False False
S04      316       104       88      91        91      1   285  158    32.91   27.85 28.80   28.80   False False
S05      643       520      157     171       139     15   579  322    80.87   24.42 26.59   21.62   False False
S06      847       388      123     138       123     11   763  424    45.81   14.52 16.29   14.52   False False
S07      804       587       64      75        52     10   724  402    73.01    7.96  9.33    6.47   False False
S08       22        20        1       9         9      6    20   11    90.91    4.55 40.91   40.91   False False
S09     1051       681       82     115        98     58   946  526    64.80    7.80 10.94    9.32   False False
S10      526       513       82     130       116     18   474  263    97.53   15.59 24.71   22.05   False False
S11      368       358       29      35        34     17   332  184    97.28    7.88  9.51    9.24   False False
S12      279       204       54      65        50     11   252  140    73.12   19.35 23.30   17.92   False False
S13      240       216      108     106       105      0   216  120    90.00   45.00 44.17   43.75   False False
S14      489       330      135     116       103     11   441  245    67.48   27.61 23.72   21.06   False False
S15      158       144      102     116        63      5   143   79    91.14   64.56 73.42   39.87   True  False
S16       90        81       54      48        22      2    81   45    90.00   60.00 53.33   24.44   True  False
S17      102        94       58      59        58      4    92   51    92.16   56.86 57.84   56.86   True  True 
S18      659       497       57      66        56     48   594  330    75.42    8.65 10.02    8.50   False False
S19      355        40       20      27        18      7   320  178    11.27    5.63  7.61    5.07   False False
S20      410       399       42      62        50     21   369  205    97.32   10.24 15.12   12.20   False False
S21      129        91       27      30        30     11   117   65    70.54   20.93 23.26   23.26   False False
S22     4851      1759       34     109        66     54  4366 2426    36.26    0.70  2.25    1.36   False False

TOTAL atlas_n=12916 named_S14=7203 named_strict=1372 proved=1648 proved_strict=1331 four=318
名义达标 3/22 : S15,S16,S17
严格达标 1/22 : S17

## 8. evidence_path 字面形态（Lead 只数形态，不判可解析性）
  OTHER                  852
  TRACE_ONLY_literal     802
  （权威口径见 EVID_RESOLVE/resolve.py —— 上述字面粗分不能替代它）
