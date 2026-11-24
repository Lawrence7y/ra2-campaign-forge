// W168 run3: virtual battle-load method, full init fn ordering, file-existence/MIX layer.
// @category W168
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class W168Run3 extends GhidraScript {
    Address va(long v){ return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    void dumpFn(long t, int cap) throws Exception {
        Address a=va(t);
        Function f=currentProgram.getFunctionManager().getFunctionAt(a);
        if (f==null){ println("=== no exact fn at "+a+" ==="); return; }
        println("=== FN "+a+" "+f.getName()+" size="+f.getBody().getNumAddresses()+" ===");
        DecompInterface di=new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r=di.decompileFunction(f,120,monitor);
        if(r==null||!r.decompileCompleted()){ println("  decompile FAILED"); return; }
        int k=0;
        for(String ln:r.getDecompiledFunction().getC().split("\n")){
            println("C| "+ln);
            if(++k>cap){ println("C| ...TRUNCATED"); break; }
        }
        println("=== END FN "+a+" ===");
    }
    public void run() throws Exception {
        println("========== VIRTUAL BATTLE LOAD METHOD (vtable 0x7E4A28+0x64) ==========");
        dumpFn(0x0046CCD0L, 280);
        println("========== FULL INIT FN 0x52BA60 (ordering) ==========");
        dumpFn(0x0052BA60L, 420);
        println("========== FILE-EXISTENCE / MIX LAYER ==========");
        dumpFn(0x00431E80L, 120);
        dumpFn(0x00431F10L, 160);
        println("========== RULE CHOOSER DIALOG PROC ==========");
        dumpFn(0x0052D430L, 160);
        println("========== DONE ==========");
    }
}
