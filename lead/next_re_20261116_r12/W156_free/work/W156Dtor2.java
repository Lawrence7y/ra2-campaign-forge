// W156: what is FUN_00445880 called twice in the BuildingClass destructor?
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
public class W156Dtor2 extends GhidraScript {
    DecompInterface di;
    void d(long addr) throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(addr);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        println("=== " + a + " size=" + (f==null?-1:f.getBody().getNumAddresses()) + " ===");
        if (f==null) return;
        DecompileResults r = di.decompileFunction(f,90,monitor);
        if(r==null||!r.decompileCompleted()){println("FAILED");return;}
        println(r.getDecompiledFunction().getC());
    }
    public void run() throws Exception {
        di=new DecompInterface(); di.openProgram(currentProgram);
        d(0x00445880L);
        println("W156Dtor2 DONE");
    }
}
