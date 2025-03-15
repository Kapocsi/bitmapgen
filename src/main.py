import argparse
import re
from typing import Optional
from pathlib import Path

from PIL import Image
import numpy as np

from util import eprint
from const import HEADER_HEAD, HEADER_TAIL


X_SIZE_ALIGN = 8


def to_camel_case_identifier(s):
    """
    Convert string to valid camel case identifier
    """
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
    """
    A class to represent a bitmap image and convert it into a packed binary format
    for use in C-style structures.

    Attributes:
        bitmap (Optional[np.ndarray]): The packed binary representation of the image.
        name (str): The name of the image file without extension.
        width (Optional[int]): The width of the processed bitmap.
        height (Optional[int]): The height of the processed bitmap.
    """

    bitmap: Optional[np.ndarray] = None
    path: str
    name = None
    width: Optional[int] = None
    height: Optional[int] = None

    def __init__(self, image_path: str) -> None:
        """
        Initializes a BitMap instance by processing an image file.

        Args:
            image_path (str): The path to the image file to be processed.
        """
        self.name = Path(image_path).with_suffix("").name
        self.path = image_path
        self.ident = to_camel_case_identifier(self.name)

        with Image.open(self.path) as image:
            self.create_bit_map(image)

    def create_bit_map(self, image: Image.Image) -> None:
        """
        Converts the given image into a packed bitmap representation.

        The image is processed into a binary format where each bit represents a pixel.
        If the image is not byte-aligned, padding is added to the width.

        Args:
            image (Image.Image): The image to be processed.
        """
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
        """
        Generates the C representation of the bitmap data.

        Returns:
            str: A string representing the bitmap in a C header format.
        """
        return f"""
        {self.arr_repr()}
        const BitMap {self.ident} = {self.struct_repr()};
            """

    def h_repr(self) -> str:
        """
        Generates the header file declaration for the bitmap.

        Returns:
            str: A string declaring the bitmap in a C header file.
        """
        return f"extern const BitMap {self.ident};"

    def struct_repr(self, ending=";") -> str:
        """
        Generates the struct representation of the bitmap.

        Args:
            ending (str, optional): The string to append at the end of the struct. Defaults to ";".

        Returns:
            str: A C-style struct representation of the bitmap.
        """
        return f"{{ _{self.ident},{self.width},{self.height} }}{ending}"

    def arr_repr(self) -> str:
        """
        Generates the packed array representation of the bitmap.

        Returns:
            str: A C-style static array representation of the bitmap data.
        """
        assert self.bitmap is not None

        return f"""
static const u32 _{self.ident}[{len(self.bitmap)}] =
        {{
{",".join(hex(x) for x in self.bitmap)}
        }};
        """


def main():
    """
    Converts images passed via a CLI to bitmaps.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-oc", "--c_output", default="bitmaps.c")
    parser.add_argument("-oh", "--h_output", default="bitmaps.h")
    parser.add_argument("input_files", nargs="+")

    args = parser.parse_args()

    input_files = args.input_files

    bitmaps = [BitMap(path) for path in input_files]

    h_contents = "\n".join(
        [
            HEADER_HEAD,
            "\n".join(b.h_repr() for b in bitmaps),
            HEADER_TAIL,
        ]
    )
    c_contents = "\n".join(
        [
            f'#include "{Path(args.h_output).name}"',
            "\n".join(b.c_repr() for b in bitmaps),
        ]
    )

    with open(args.c_output, "w+", encoding="ascii") as f:
        f.write(c_contents)

    with open(args.h_output, "w+", encoding="ascii") as f:
        f.write(h_contents)


if __name__ == "__main__":
    main()
