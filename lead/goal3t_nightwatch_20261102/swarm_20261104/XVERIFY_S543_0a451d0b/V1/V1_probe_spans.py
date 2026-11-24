import numpy as np
from PIL import Image

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_20261023r\measure_w2_end_x.png"
im = Image.open(p).convert("RGB")
arr = np.array(im)

# Look at y=230..245, across all x
row_mask = (arr[235:244, :, 0] > 120) & (arr[235:244, :, 0] > 2 * arr[235:244, :, 1]) & (arr[235:244, :, 0] > 2 * arr[235:244, :, 2])
# Find column ranges where row_mask is True
col_has_red = np.any(row_mask, axis=0)
indices = np.where(col_has_red)[0]

# Split into contiguous spans
spans = []
cur_span = []
for idx in indices:
    if not cur_span or idx == cur_span[-1] + 1:
        cur_span.append(idx)
    else:
        spans.append((cur_span[0], cur_span[-1]))
        cur_span = [idx]
if cur_span:
    spans.append((cur_span[0], cur_span[-1]))

print("Red text spans in y=235..244:")
for s, e in spans:
    print(f"  x={s}..{e} (width={e-s+1})")
    for y in range(235, 244):
        line = "".join("#" if row_mask[y-235, x] else " " for x in range(s, e+1))
        print(f"    {line}")
