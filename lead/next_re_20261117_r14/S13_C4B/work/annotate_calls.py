import pathlib,json
raw=json.loads(pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_C4B\work\scan_raw.json").read_text(encoding="utf-8"))
cov={}
for ln in pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv").read_text(encoding="utf-8").splitlines()[1:]:
 a=ln.split(chr(9))
 if len(a)>4: cov[int(a[0],16)]=(a[1],a[2],a[4])
for d in raw["rows"]:
 e=int(d["entry"],16)
 sc=[]
 for t,op,tgt in d["calls"]:
  if op=="direct" and int(tgt) in cov:
   n,g,grade=cov[int(tgt)]
   sc.append((grade,t,int(tgt),n,g))
 pr=[x for x in sc if x[0]=="[\u5df2\u8bc1]"]
 d["all_proved_calls"]=pr
 d["all_graded_calls"]=sc
print(len([d for d in raw["rows"] if d["all_proved_calls"]]))
for d in sorted(raw["rows"],key=lambda x:(-len(x["all_proved_calls"]),-len(x["memabs"]),x["entry"]))[:20]:
 print(d["entry"],d["name"],"pr",len(d["all_proved_calls"]),"gl",len(d["memabs"]),"calls",len(d["calls"]),"directs",[hex(x[2]) for x in d["all_proved_calls"][:6]])
pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_C4B\work\scan_raw.json").write_text(json.dumps(raw,indent=2),encoding="utf-8")
