// W164: gates inside UpdatePathfinding + Drive Process wrapper
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class W164_Gates extends GhidraScript {
    void dec(long t,String label,int max)throws Exception{
        Address a=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        Function f=currentProgram.getFunctionManager().getFunctionContaining(a);
        println("=== "+label+" entry="+(f==null?"?":f.getEntryPoint())+" size="+(f==null?-1:f.getBody().getNumAddresses())+" ===");
        if(f==null)return;
        DecompInterface di=new DecompInterface();di.openProgram(currentProgram);
        DecompileResults r=di.decompileFunction(f,90,monitor);
        if(r!=null&&r.decompileCompleted()){
            int k=0;for(String ln:r.getDecompiledFunction().getC().split("\n")){println("C| "+ln);if(++k>max){println("C| ...");break;}}
        }
    }
    public void run()throws Exception{
        dec(0x004D3920L,"UpdatePathfinding 0x4D3920",110);
        dec(0x004B0500L,"Drive Process wrapper off4+40 @0x4B0500",90);
    }
}
