s_path = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\RULING_R15_20261119\work\strict_panel.py"
d_path = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M66\_strict_panel_run.py"
s = open(s_path, encoding="utf-8").read()
old = 'OUT  = os.path.join(ROOT, "RULING_R15_20261119", "work")'
new = 'OUT  = os.path.join(ROOT, "MERGE_M66", "_strict_out")'
assert old in s, "OUT line not found"
s = s.replace(old, new)
open(d_path, "w", encoding="utf-8", newline="").write(s)
print("wrote", d_path)
