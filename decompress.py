import sys

import brotli


def main():
    """Decompress a specified, Brotli-compressed input file."""
    if len(sys.argv) != 2:
        print("Error: Incorrect number of arguments. Expected 1.")
        print("Usage: python decompress.py <path to file to decompress>")
        print("Example: python decompress.py zones.json.br")
        exit(1)

    with open(sys.argv[1], "rb") as r, open(sys.argv[1][:-3], "wb") as w:
        w.write(brotli.decompress(r.read()))


if __name__ == "__main__":
    main()
