#!/usr/bin/env python3
# S16-N2 false-positive baseline: one consistent number
# 9 candidates; YRpp direct address bindings = 0; docs/re name-bearing record = 1 (0065E660, attribution conflict)
# Criterion "docs/re name-bearing record": random 3 draws expected false hits = 3 * 1/9 = 0.33
TOTAL = 9
DOCS_NAME_RECORDS = 1
DRAWS = 3
baseline = DRAWS * DOCS_NAME_RECORDS / TOTAL
print(f"false_positive_baseline={baseline:.2f}")
assert round(baseline, 2) == 0.33
