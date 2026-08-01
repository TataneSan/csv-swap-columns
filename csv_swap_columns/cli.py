"""Swap two columns of a CSV file.

Columns can be given by header name or 1-based index. With --check the
tool exits 2 (without printing) when the two columns are already equal,
which is handy in CI to assert an expected layout.

Exit codes:
  0 - success
  1 - I/O, CSV parsing or CLI error
  2 - unknown column, or --check failure
"""

import argparse
import csv
import io
import sys


def resolve(spec, header):
    if spec.isdigit():
        idx = int(spec) - 1
        if 0 <= idx < len(header):
            return idx
        raise KeyError(spec)
    if header and spec in header:
        return header.index(spec)
    raise KeyError(spec)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="csv-swap-columns",
        description="Swap two columns of a CSV file.",
    )
    parser.add_argument("file", help="CSV file, or - for stdin")
    parser.add_argument("col_a", help="First column (name or 1-based index)")
    parser.add_argument("col_b", help="Second column (name or 1-based index)")
    parser.add_argument("--no-header", action="store_true",
                        help="Header-less CSV; columns must be indices")
    parser.add_argument("--delimiter", default=",",
                        help="Field delimiter or 'auto' (default: ,)")
    parser.add_argument("--check", action="store_true",
                        help="Exit 2 when the two columns are already equal (CI assertion)")
    args = parser.parse_args(argv)

    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, "r", encoding="utf-8", newline="") as fh:
                text = fh.read()
    except OSError as exc:
        print(f"csv-swap-columns: {exc}", file=sys.stderr)
        return 1

    if args.delimiter == "auto":
        try:
            args.delimiter = csv.Sniffer().sniff(text[:4096]).delimiter
        except csv.Error:
            args.delimiter = ","

    try:
        records = list(csv.reader(io.StringIO(text), delimiter=args.delimiter))
    except csv.Error as exc:
        print(f"csv-swap-columns: CSV parse error: {exc}", file=sys.stderr)
        return 1
    if not records:
        print("csv-swap-columns: empty input", file=sys.stderr)
        return 1

    header = [] if args.no_header else records[0]
    try:
        ia = resolve(args.col_a, header)
        ib = resolve(args.col_b, header)
    except KeyError as exc:
        print(f"csv-swap-columns: unknown column: {exc.args[0]!r}", file=sys.stderr)
        return 2

    width = max(len(r) for r in records)
    if ia >= width or ib >= width:
        print("csv-swap-columns: column index out of range", file=sys.stderr)
        return 2

    if args.check:
        same = all(
            (list(r) + [""] * width)[ia] == (list(r) + [""] * width)[ib] for r in records
        )
        if same:
            print("csv-swap-columns: columns already identical", file=sys.stderr)
            return 2
        return 0

    out = io.StringIO()
    w = csv.writer(out, delimiter=args.delimiter, lineterminator="\n")
    for row in records:
        padded = list(row) + [""] * (width - len(row))
        padded[ia], padded[ib] = padded[ib], padded[ia]
        w.writerow(padded[: len(row)] if len(row) == width else padded)
    sys.stdout.write(out.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main())
