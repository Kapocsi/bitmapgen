from sys import stderr
from typing import Any, Optional
from PIL import Image
import numpy as np
from pathlib import Path
import re
import argparse


X_SIZE_ALIGN = 8


def eprint(*args, **kwargs):
    merged_kwargs: Any = {"file": stderr} | kwargs
    print(*args, **merged_kwargs)


def to_camel_case_identifier(s):
    # Remove invalid characters (keep only letters, numbers, and underscores)
    s = re.sub(r"[^a-zA-Z0-9_]", " ", s)

    # Split into words
    words = s.split()

    if not words:
        return "_var"  # Default in case the input is empty or non-alphanumeric

    # Ensure it does not start with a digit by prefixing with an underscore
    if words[0][0].isdigit():
        words[0] = "_" + words[0]

    # Convert to camelCase
    camel_case = words[0].lower() + "".join(w.capitalize() for w in words[1:])

    return camel_case


class BitMap:
    bitmap: Optional[np.ndarray] = None
    name = None
    width: Optional[int] = None
    height: Optional[int] = None

    def __init__(self, image_path) -> None:
        self.name = Path(image_path).with_suffix("").name

        with Image.open(image_path) as image:
            self.createBitMap(image)

    def createBitMap(self, image):
        image_arr = np.array(image)

        y, x, *_ = image_arr.shape
        if len(image_arr.shape) == 3:
            bool_arr = np.sum(image_arr, axis=2) > 128
        else:
            bool_arr = image_arr != 0

        if x % X_SIZE_ALIGN != 0:
            eprint(f"{self.name or '<no name>'} is not byte aligned: padding width")

        new_x = int(X_SIZE_ALIGN * np.ceil(x / X_SIZE_ALIGN))
        diff = new_x - x

        padded = np.pad(bool_arr, ((0, 0), (diff // 2, diff // 2 + diff % 2)))

        packed = np.packbits(padded)

        packed = np.reshape(packed, (len(packed) // 4, 4))
        w = 256 ** np.arange(0, 4)[::-1]
        packed = np.sum(packed * w, axis=1)

        self.width = new_x
        self.height = y
        self.bitmap = packed

    def c_repr(self) -> str:
        assert self.bitmap is not None

        ident = to_camel_case_identifier(self.name)

        return f"""
        {self.arr_repr()}
        const BitMap {ident} = {self.struct_repr()};
            """

    def h_repr(self) -> str:
        ident = to_camel_case_identifier(self.name)
        return f"const BitMap {ident};"

    def struct_repr(self, ending=";") -> str:
        ident = to_camel_case_identifier(self.name)
        return f"{{ _{ident},{self.width},{self.height} }}{ending}"

    def arr_repr(self) -> str:
        assert self.bitmap is not None

        ident = to_camel_case_identifier(self.name)

        return f"""
static const u32 _{ident}[{len(self.bitmap)}] =
        {{
{",".join(hex(x) for x in self.bitmap)}
        }};
        """


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-oc", "--c_output", default="bitmaps.c")
    parser.add_argument("-oh", "--h_output", default="bitmaps.h")
    parser.add_argument("input_files", nargs="+")

    args = parser.parse_args()

    c_output = open(args.c_output, "w+")
    h_output = open(args.h_output, "w+")

    input_files = args.input_files

    bitmaps = [BitMap(path) for path in input_files]
    print('#include "bitmaps.h"', file=c_output)
    print("\n".join(b.c_repr() for b in bitmaps), file=c_output)

    print(
        """
/**
 * @file bitmaps.h
 * @brief Declares external bitmap objects.
 */

#ifndef BITMAPS_H
#define BITMAPS_H

#include "bitmap.h"
#include "global.h"
#include "raster.h"
        """,
        file=h_output,
    )

    print("\n".join(b.h_repr() for b in bitmaps), file=h_output)

    print("#endif", file=h_output)


if __name__ == "__main__":
    main()
