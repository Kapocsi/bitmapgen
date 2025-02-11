from main import BitMap
from pathlib import Path

pngs = Path("./out/").glob("*.png")
maps = {}


for p in pngs:
    index = int(p.with_suffix("").name)
    if index > 255:
        continue
    b = BitMap(p)

    maps[index] = b


cfile = open("depixel.c", "w+")


print(
    """
#include "../bitmap.h"
#include "../global.h"

#define EMPTY_BITMAP {(const u32 *)(0l), 0, 0}
""",
    file=cfile,
)


for k, m in maps.items():
    print(m.arr_repr(), file=cfile)


print("BitMap depixel[] = {", file=cfile)

for i in range(128):
    if i in maps:
        print(maps[i].struct_repr(ending=","), file=cfile)
    else:
        print("EMPTY_BITMAP,", file=cfile)

print("};", file=cfile)
