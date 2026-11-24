import json
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\p3_D2_chains.ndjson"
rows=[json.loads(l) for l in open(p,encoding="utf-8")]
for i,o in enumerate(rows,1):
    s=o.get("step")
    t=o.get("t_local","")[11:19]
    if s=="screen":
        vis=",".join(o.get("visible_control_texts",[]))
        c=o.get("counters") or {}
        print("%4d %s %-30s frame=%-8s mode=%-3s vis=%s"%(i,t,o.get("label"),c.get("frame"),c.get("mode"),vis[:150]))
    elif s in ("click","key","real_mouse_click","click_hwnd","I1_A1_loaded","poll_hit","poll_timeout","Q3_save_file","FATAL","instance_closed","Q3_process_exit","screenshot"):
        extra=""
        if s=="click": extra="%s -> %s"%(o.get("control_text"),o.get("result"))
        elif s=="key": extra="%s vk=%s"%(o.get("label"),o.get("vk"))
        elif s=="real_mouse_click": extra="%s (%s,%s)"%(o.get("label"),o.get("x"),o.get("y"))
        elif s=="poll_hit": extra="%s hits=%s t=%s"%(o.get("label"),o.get("hits"),o.get("elapsed_s"))
        elif s=="poll_timeout": extra="%s n=%s"%(o.get("label"),o.get("n_samples"))
        elif s=="FATAL": extra=o.get("error")
        elif s=="screenshot": extra=o.get("label")
        print("%4d %s >> %-20s %s"%(i,t,s,extra))
