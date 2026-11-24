import hashlib

A = r"D:\Project\ra2-campaign-forge\lead\s604_script_hunt_20261109\_sh_gen512655_out.txt"
B = r"D:\Project\ra2-campaign-forge\lead\s604_script_hunt_20261109\_sph_gen512655_rerun_out.txt"
with open(A, "rb") as f:
    a = f.read()
with open(B, "rb") as f:
    b = f.read()
print(f"prior_out bytes={len(a)} sha256={hashlib.sha256(a).hexdigest()}")
print(f"rerun_out bytes={len(b)} sha256={hashlib.sha256(b).hexdigest()}")
print(f"bytes_equal={a==b}")
an = a.replace(b"\r\n", b"\n")
bn = b.replace(b"\r\n", b"\n")
print(f"lf_normalized_equal={an==bn}")
