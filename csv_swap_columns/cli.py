#!/usr/bin/env python3
"""Swap or move columns of a CSV file.

Columns are selected by header name or 1-based index (negative indices count
from the end). Default action swaps two columns; --move reinserts column A
at column B's position.

Exit codes:
  0 - ok
  1 - I/O or CLI error
  2 - check failed (unknown column, identical columns, gate unsatisfied)
"""
import argparse
import csv
import json
import sys


def sniff(text):
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def resolve(col, header, no_header, width):
    """Resolve a column selector to a 0-based index. 1-based for numbers."""
    try:
        idx = int(col)
    except ValueError:
        if no_header:
            raise ValueError(
                "with --no-header, columns must be 1-based indices")
        if col not in header:
            raise KeyError(col)
        return header.index(col)
    if idx == 0:
        raise ValueError("column indices are 1-based")
    return idx - 1 if idx > 0 else width + idx


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="csv-swap-columns",
        description="Swap two columns of a CSV file (or --move one).")
    p.add_argument("col_a", help="first column (header name or 1-based index)")
    p.add_argument("col_b", help="second column (header name or 1-based index)")
    p.add_argument("csvfile", nargs="?", default="-",
                   help="CSV file (default: stdin, '-' for stdin)")
    p.add_argument("-d", "--delimiter", default=None,
                   help="field delimiter (default: sniffed, fallback ',')")
    p.add_argument("--move", action="store_true",
                   help="move column A to column B's position instead of swapping")
    p.add_argument("--no-header", action="store_true",
                   help="treat first row as data")
    p.add_argument("--in-place", action="store_true",
                   help="rewrite csvfile in place (requires a real file)")
    p.add_argument("--require-columns", type=int, metavar="N",
                   help="exit 2 if the CSV has fewer than N columns")
    p.add_argument("--require-rows", type=int, metavar="N",
                   help="exit 2 if the CSV has fewer than N data rows")
    p.add_argument("--json", action="store_true",
                   help="emit a JSON report to stderr")
    args = p.parse_args(argv)

    try:
        if args.csvfile == "-":
            text = sys.stdin.read()
        else:
            with open(args.csvfile, "r", encoding="utf-8", newline="") as fh:
                text = fh.read()
    except OSError as exc:
        print("error: cannot read %s: %s" % (args.csvfile, exc), file=sys.stderr)
        return 1

    if args.in_place and args.csvfile == "-":
        print("error: --in-place requires a file argument", file=sys.stderr)
        return 1

    delimiter = args.delimiter or sniff(text)
    rows = list(csv.reader(text.splitlines(keepends=True), delimiter=delimiter))

    if not rows:
        print("error: empty CSV", file=sys.stderr)
        return 1

    header = [] if args.no_header else rows[0]
    width = max(len(r) for r in rows)

    if args.require_columns is not None and width < args.require_columns:
        print("error: CSV has %d columns, required >= %d" % (width, args.require_columns),
              file=sys.stderr)
        return 2
    data_rows = len(rows) if args.no_header else max(0, len(rows) - 1)
    if args.require_rows is not None and data_rows < args.require_rows:
        print("error: CSV has %d data rows, required >= %d" % (data_rows, args.require_rows),
              file=sys.stderr)
        return 2

    try:
        ia = resolve(args.col_a, header, args.no_header, width)
        ib = resolve(args.col_b, header, args.no_header, width)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    except KeyError as exc:
        print("error: unknown column %s (header: %s)" % (exc, header),
              file=sys.stderr)
        return 2

    for label, idx in (("col_a", ia), ("col_b", ib)):
        if not (0 <= idx < width):
            print("error: %s index %d out of range (width=%d)" % (label, idx + 1, width),
                  file=sys.stderr)
            return 2
    if ia == ib:
        print("error: both columns resolve to index %d" % (ia + 1), file=sys.stderr)
        return 2

    out_rows = []
    for row in rows:
        row = row + [""] * (width - len(row))
        if args.move:
            val = row.pop(ia)
            row.insert(ib, val)
        else:
            row[ia], row[ib] = row[ib], row[ia]
        out_rows.append(row)

    buf = []
    class _Sink:
        def write(self, s):
            buf.append(s)
    writer = csv.writer(_Sink(), delimiter=delimiter, lineterminator="\n")
    for row in out_rows:
        writer.writerow(row)
    output = "".join(buf)

    if args.in_place:
        try:
            with open(args.csvfile, "w", encoding="utf-8", newline="") as fh:
                fh.write(output)
        except OSError as exc:
            print("error: cannot write %s: %s" % (args.csvfile, exc), file=sys.stderr)
            return 1
    else:
        sys.stdout.write(output)

    if args.json:
        json.dump({
            "operation": "move" if args.move else "swap",
            "columns": [ia + 1, ib + 1],
            "width": width,
            "rows": len(rows),
        }, sys.stderr)
        sys.stderr.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
