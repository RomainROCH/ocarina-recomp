#!/usr/bin/env python3
"""Compile the production vk_texture.c BC3 copy guard in isolation (no game/Vulkan)."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent.parent
source = (root / "runtime/vk_texture.c").read_text(encoding="utf-8")
match = re.search(r"\bint bc_cut\s*=\s*e->f\.astc_bc\s*&&.*?;", source, re.S)
if not match:
    raise SystemExit("Missing production BC3 copy guard in vk_texture.c")
predicate = match.group(0)

c = r'''
#include <stdint.h>
#include <stdio.h>
typedef struct { int xoffset, yoffset; } Region;
typedef struct { struct { int astc_bc; } f; } Texture;
static int skip(uint32_t mw, uint32_t mh, uint32_t w, uint32_t h,
                int ox, int oy, int bc3) {
    Texture e_val = { .f.astc_bc = bc3 };
    Texture *e = &e_val;
    Region r_val = { .xoffset = ox, .yoffset = oy };
    Region *r = &r_val;
    __GUARD__
    return bc_cut;
}
typedef struct { int mw,mh,w,h,ox,oy,bw,bh,bc3,want_skip; } Case;
int main(void) {
    static const Case cases[] = {
        { 8, 8, 4, 4, 0, 0, 4, 4, 1, 0 },  // aligned ASTC4x4 and BC3
        {10,10, 5,10, 5, 0, 5, 5, 1, 1 },  // ASTC5x5 start valid; BC3 x=5 invalid
        {10,10,10, 5, 0, 5, 5, 5, 1, 1 },  // ASTC5x5 start valid; BC3 y=5 invalid
        {10,10, 5, 5, 5, 5, 5, 5, 1, 1 },  // ASTC5x5 start valid; BC3 x/y invalid
        {12,12, 6,12, 6, 0, 6, 6, 1, 1 },  // ASTC6x6 start valid; BC3 x=6 invalid
        { 5, 5, 5, 5, 0, 0, 5, 5, 1, 0 },  // image edge may end in BC3 block
        { 9, 9, 5, 5, 4, 4, 4, 4, 1, 0 },  // edge and aligned BC3 block start
        {10,10, 5,10, 0, 0, 5, 5, 1, 1 },  // interior BC3 partial width
        {10,10, 5,10, 5, 0, 5, 5, 0, 0 },  // no BC3 conversion: unchanged
        {16,16, 8, 8, 8, 8, 8, 8, 1, 0 }   // ASTC8x8/BC3 aligned
    };
    for (unsigned i=0; i<sizeof(cases)/sizeof(cases[0]); ++i) {
        const Case t = cases[i];
        if (t.ox % t.bw || t.oy % t.bh) {
            fprintf(stderr, "Invalid test: ASTC block offsets in case %u\n", i); return 2;
        }
        int got = skip((uint32_t)t.mw,(uint32_t)t.mh,(uint32_t)t.w,(uint32_t)t.h,
                       t.ox,t.oy,t.bc3);
        if (!!got != t.want_skip) {
            fprintf(stderr, "Case %u: skip=%d, expected=%d\n", i, got, t.want_skip);
            return 1;
        }
    }
    puts("10 production-guard cases passed (ASTC/BC3 offsets + edge extents)");
    return 0;
}
'''.replace("__GUARD__", predicate)
cc = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CC", "cc")
with tempfile.TemporaryDirectory() as td:
    src = Path(td) / "bc3_copy.c"
    exe = Path(td) / ("bc3_copy.exe" if os.name == "nt" else "bc3_copy")
    src.write_text(c, encoding="utf-8")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O1", str(src), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
