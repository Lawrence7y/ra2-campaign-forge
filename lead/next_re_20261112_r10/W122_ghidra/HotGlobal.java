// W122i: who references 0x00B0C110 most? count by enclosing function, decompile top 2.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class HotGlobal extends GhidraScript {
    public void run() throws Exception {
        long t = 0x00B0C110L;
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
        Map<Long,Integer> cnt = new HashMap<>();
        Map<Long,Long> firstRef = new HashMap<>();
        int total = 0;
        while (it.hasNext()) {
            Reference r = it.next();
            total++;
            Address from = r.getFromAddress();
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(from);
            if (cf == null) continue;
            long e = cf.getEntryPoint().getOffset();
            cnt.put(e, cnt.getOrDefault(e,0)+1);
            if (!firstRef.containsKey(e)) firstRef.put(e, from.getOffset());
        }
        println("### total refs to " + a + " = " + total + " across " + cnt.size() + " functions");
        List<Map.Entry<Long,Integer>> es = new ArrayList<>(cnt.entrySet());
        es.sort((x,y) -> y.getValue() - x.getValue());
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        int shown = 0;
        for (Map.Entry<Long,Integer> e : es) {
            Address fa = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(e.getKey().longValue());
            Function fn = currentProgram.getFunctionManager().getFunctionAt(fa);
            println(String.format("  fn %s refs=%d size=%d firstRef@%08x", fa, e.getValue(),
                    fn==null? -1 : fn.getBody().getNumAddresses(), firstRef.get(e.getKey())));
            if (shown < 2 && fn != null) {
                shown++;
                DecompileResults res = di.decompileFunction(fn, 60, monitor);
                if (res != null && res.decompileCompleted()) {
                    String[] lines = res.getDecompiledFunction().getC().split("\n");
                    int k = 0;
                    for (String ln : lines) {
                        println("D| " + ln);
                        if (++k > 110) { println("D| ..."); break; }
                    }
                }
            }
        }
    }
}