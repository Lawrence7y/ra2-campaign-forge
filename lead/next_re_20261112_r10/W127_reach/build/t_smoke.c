/* toolchain smoke test: can we build a 32-bit PE DLL, and does an inline hook shape work? */
__declspec(dllexport) int f(void) { return 1; }
__declspec(dllexport) int g(int a) { return a + 1; }
