#!/usr/bin/env python3
"""Swap two columns of a CSV file (header included).

Selects columns by header name or 0-based index and exchanges their
positions, rewriting the whole file to stdout.

Exit codes:
  0 - ok
  1 - I/O or CLI error
  2 - check failed (unknown column, identical columns)
"""
import argparse
import csv
import json
import sys


def resolve(col, header, no_header):
    if col.isdigit():
        return int(col)
    if no_header:
        raise ValueError("with --no-header, columns must be indices")
    if col not in header:
        raise KeyError(col)
    return header.index(col)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="csv-swap-columns",
        description="Swap two columns of a CSV file.")
    p.add_argument("col_a", help="first column (header name or index)")
    p.add_argument("col_b", help="second column (header name or index)")
    p.add_argument("csvfile", nargs="?", default="-",
                   help="CSV file (default: stdin, '-' for stdin)")
    p.add_argument("-d", "--delimiter", default=",", help="field delimiter (default: ,)")
    p.add_argument("--no-header", action="store_true", help="treat first row as data")
    p.add_argument("--json", action="store_true",
                   help="emit a JSON report after the CSV (to stderr)")
    args = p.parse_args(argv)

    try:
        if args.csvfile == "-":
            rows = list(csv.reader(sys.stdin, delimiter=args.delimiter))
        else:
            with open(args.csvfile, "r", encoding="utf-8", newline="") as fh:
                rows = list(csv.reader(fh, delimiter=args.delimiter))
    except OSError as exc:
        print("error: cannot read %s: %s" % (args.csvfile, exc), file=sys.stderr)
        return 1

    if not rows:
        print("error: empty CSV", file=sys.stderr)
        return 1

    header = [] if args.no_header else rows[0]
    try:
        ia = resolve(args.col_a, header, args.no_header)
        ib = resolve(args.col_b, header, args.no_header)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    except KeyError as exc:
        print("error: unknown column %s (header: %s)" % (exc, header), file=sys.stderr)
        return 2

    width = max(len(r) for r in rows) if rows else 0
    if ia >= width or ib >= width:
        print("error: column index out of range (width=%d)" % width, file=sys.stderr)
        return 2
    if ia == ib:
        print("error: both columns resolve to index %d" % ia, file=sys.stderr)
        return 2

    writer = csv.writer(sys.stdout, delimiter=args.delimiter, lineterminator="\n")
    for row in rows:
        row = row + [""] * (width - len(row))
        row[ia], row[ib] = row[ib], row[ia]
        writer.writerow(row)

    if args.json:
        json.dump({"swapped": [ia, ib], "width": width, "rows": len(rows)},
                  sys.stderr)
        sys.stderr.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
