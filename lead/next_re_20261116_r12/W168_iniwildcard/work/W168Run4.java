// W168 run4: resolve loose-vs-MIX file lookup layer for Q3.
// @category W168
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class W168Run4 extends GhidraScript {
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
    void xrefsTo(long t, String label) throws Exception {
        Address a=va(t);
        println("### XREFSTO "+label+" @ "+a+" ###");
        ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(a);
        int n=0;
        while(it.hasNext()){
            Reference r=it.next(); Address from=r.getFromAddress();
            Function cf=currentProgram.getFunctionManager().getFunctionContaining(from);
            println("  ref@"+from+" in="+(cf==null?"?":cf.getEntryPoint())+" type="+r.getReferenceType());
            if(++n>30){ println("  ..."); break; }
        }
        println("  total(shown)="+n);
    }
    public void run() throws Exception {
        println("========== LOOSE v MIX FILE LAYER ==========");
        dumpFn(0x0065CBF0L, 220);   // exists primitive called by FUN_00431F10
        dumpFn(0x0065CAC0L, 180);   // set-filename primitive called by FUN_00431E80
        println("========== XREFS ==========");
        xrefsTo(0x0065CBF0L,"FUN_0065CBF0 exists primitive");
        println("========== DONE ==========");
    }
}
