#!/usr/bin/env python3
"""Swap two columns of a CSV file.

Reads a CSV from FILE or stdin, swaps the two columns given by name or
1-based index (headers included), and writes the result to stdout.

Exit codes:
  0  success
  1  I/O, CLI or CSV parsing error
  2  --check mode: swapping the columns back does not restore the input
     (self-verify, mainly for CI plumbing tests)
"""
import argparse
import csv
import json
import sys


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Swap two columns of a CSV file.")
    p.add_argument("file", nargs="?", default="-",
                   help="CSV file to read (default: stdin, use '-' for stdin)")
    p.add_argument("--columns", required=True,
                   help="Two columns to swap, comma-separated (names or 1-based indexes), e.g. a,c or 1,3")
    p.add_argument("--delimiter", default=",", help="CSV delimiter (default: ,)")
    p.add_argument("--check", action="store_true",
                   help="Self-verify: swap twice and compare to the original (exit 2 on mismatch)")
    p.add_argument("--json", action="store_true", help="Emit a JSON report instead of the CSV")
    return p.parse_args(argv)


def resolve(token, header):
    token = token.strip()
    if token.isdigit():
        idx = int(token) - 1
        if 0 <= idx < len(header):
            return idx
        raise ValueError(f"column index out of range: {token}")
    if token in header:
        return header.index(token)
    raise ValueError(f"unknown column: {token}")


def swap_rows(rows, i, j):
    for r in rows:
        r[i], r[j] = r[j], r[i]


def main(argv=None):
    args = parse_args(argv)
    try:
        fh = sys.stdin if args.file == "-" else open(args.file, newline="", encoding="utf-8")
    except OSError as e:
        print(f"error: cannot open {args.file}: {e}", file=sys.stderr)
        return 1

    tokens = args.columns.split(",")
    if len(tokens) != 2:
        print("error: --columns expects exactly two columns", file=sys.stderr)
        return 1

    with fh:
        try:
            reader = csv.reader(fh, delimiter=args.delimiter)
            header = next(reader, None)
            if header is None:
                print("error: empty CSV", file=sys.stderr)
                return 1
            rows = [header] + list(reader)
        except csv.Error as e:
            print(f"error: CSV parse error: {e}", file=sys.stderr)
            return 1

    try:
        i = resolve(tokens[0], header)
        j = resolve(tokens[1], header)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if i == j:
        print("error: cannot swap a column with itself", file=sys.stderr)
        return 1

    width = len(header)
    for r in rows:
        r.extend([""] * (width - len(r)))

    original = [list(r) for r in rows]
    name_i, name_j = header[i], header[j]
    swap_rows(rows, i, j)

    ok = True
    if args.check:
        twice = [list(r) for r in rows]
        swap_rows(twice, i, j)
        ok = twice == original

    report = {
        "file": args.file,
        "swapped": [name_i, name_j],
        "positions": [i + 1, j + 1],
        "rows": len(rows) - 1,
        "self_check_ok": ok,
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        w = csv.writer(sys.stdout, delimiter=args.delimiter, lineterminator="\n")
        w.writerows(rows)

    if args.check and not ok:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
