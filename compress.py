import sys

import brotli


def main():
    """Compress a specified input file using Brotli compression."""
    if len(sys.argv) != 2:
        print("Error: Incorrect number of arguments. Expected 1.")
        print("Usage: python compress.py <path to file to compress>")
        print("Example: python compress.py zones.json")
        exit(1)

    with open(sys.argv[1], "rb") as r, \
            open("{}.br".format(sys.argv[1]), "wb") as w:
        w.write(brotli.compress(r.read()))


if __name__ == "__main__":
    main()
