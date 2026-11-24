// W122n: xrefs to 0x00A8ED50 (claimed Bullet vector) + decompile top 2 referencers.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class BulletX extends GhidraScript {
    public void run() throws Exception {
        long t = 0x00A8ED50L;
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
        Map<Long,Integer> cnt = new HashMap<>();
        int total=0;
        while (it.hasNext()) {
            Reference r = it.next(); total++;
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            if (cf==null) continue;
            long e=cf.getEntryPoint().getOffset();
            cnt.put(e, cnt.getOrDefault(e,0)+1);
        }
        println("### refs to " + a + " = " + total + " across " + cnt.size());
        List<Map.Entry<Long,Integer>> es=new ArrayList<>(cnt.entrySet());
        es.sort((x,y)->y.getValue()-x.getValue());
        DecompInterface di=new DecompInterface(); di.openProgram(currentProgram);
        int shown=0;
        for (Map.Entry<Long,Integer> e: es) {
            Address fa=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(e.getKey().longValue());
            Function fn=currentProgram.getFunctionManager().getFunctionAt(fa);
            println(String.format("  fn %s refs=%d size=%d", fa, e.getValue(), fn==null?-1:fn.getBody().getNumAddresses()));
            if (shown<2 && fn!=null) {
                shown++;
                DecompileResults res=di.decompileFunction(fn,45,monitor);
                if (res!=null && res.decompileCompleted()) {
                    int k=0;
                    for (String ln: res.getDecompiledFunction().getC().split("\n")) {
                        println("C| "+ln);
                        if (++k>50) { println("C| ..."); break; }
                    }
                }
            }
        }
    }
}