// W122t: crash site 0x00724737 - containing function + stack return-address callees
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.util.*;

public class CrashSite extends GhidraScript {
    void dumpFn(Function f, int cap) throws Exception {
        if (f==null) return;
        println("--- FN " + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses() + " ---");
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 60, monitor);
        if (r==null || !r.decompileCompleted()) { println("  (decompile failed)"); return; }
        int k=0;
        for (String ln : r.getDecompiledFunction().getC().split("\n")) {
            println("C| " + ln);
            if (++k>cap) { println("C| ..."); break; }
        }
    }
    public void run() throws Exception {
        Address crash = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x00724737L);
        Function f = currentProgram.getFunctionManager().getFunctionContaining(crash);
        println("### crash 0x00724737 in " + (f==null?"<no fn>":f.getEntryPoint()+" size="+f.getBody().getNumAddresses()));
        dumpFn(f, 90);
        // stack return addresses from except.txt
        long[] rets = { 0x004F446AL, 0x006D16C7L, 0x004684F7L, 0x004685DDL, 0x004FC1CBL };
        for (long ra : rets) {
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(ra);
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(a);
            println("### ret 0x" + Long.toHexString(ra) + " in " + (cf==null?"<none>":cf.getEntryPoint()+" size="+cf.getBody().getNumAddresses()));
        }
    }
}