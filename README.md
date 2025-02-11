# BitMap Generator

## Install

This project uses [uv](https://github.com/astral-sh/uv), you can still install
deps and run this project without it, using the usual tooling.

### Using [UV](https://github.com/astral-sh/uv)

```sh
git clone https://github.com/Kapocsi/bitmapgen
cd bitmapgen
uv install .
```

### Using pip

```sh
git clone https://github.com/Kapocsi/bitmapgen
cd bitmapgen
pip install .
```

## Usage

To generate `bitmap.c` and `bitmap.h` file run

```sh
bitmapgen <input files>
```

full usage info can be found by running

```sh
bitmapgen --help
```
