#!/usr/bin/env python3
"""
Swap or move two columns in a CSV file.

Columns are specified by 0-based index, negative index relative to end,
or by header name (when the file has a header row).

Exit codes:
  0  success
  1  I/O or CLI error
  2  gate condition not met (require-columns / require-rows)
"""
import argparse
import csv
import sys
import json
import os


def sniff_dialect(sample):
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel


def resolve_col(idx_or_name, header, ncols, no_header):
    if no_header:
        if idx_or_name.lstrip("-").isdigit():
            idx = int(idx_or_name)
            if idx < 0:
                idx += ncols
            if not (0 <= idx < ncols):
                raise KeyError(f"index {idx_or_name} out of range")
            return idx
        raise KeyError(f"column '{idx_or_name}' not numeric in no-header mode")
    else:
        if idx_or_name.lstrip("-").isdigit():
            idx = int(idx_or_name)
            if idx < 0:
                idx += ncols
            if not (0 <= idx < ncols):
                raise KeyError(f"index {idx_or_name} out of range")
            return idx
        if idx_or_name in header:
            return header.index(idx_or_name)
        raise KeyError(f"column '{idx_or_name}' not found in header")


def swap_list(lst, a, b, move=False):
    lst = list(lst)
    if move:
        val = lst.pop(a)
        lst.insert(b, val)
    else:
        lst[a], lst[b] = lst[b], lst[a]
    return lst


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Swap or move two CSV columns by name or index."
    )
    parser.add_argument("file", help="CSV input file")
    parser.add_argument("col_a", help="First column (index or name)")
    parser.add_argument("col_b", help="Second column (index or name)")
    parser.add_argument("--move", action="store_true",
                        help="Move col_a to position of col_b (instead of swapping)")
    parser.add_argument("--no-header", action="store_true",
                        help="CSV has no header row")
    parser.add_argument("--in-place", action="store_true",
                        help="Rewrite the input file")
    parser.add_argument("--require-columns", type=int, default=None, metavar="N",
                        help="Exit 2 if column count < N")
    parser.add_argument("--require-rows", type=int, default=None, metavar="N",
                        help="Exit 2 if row count < N")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON report")
    args = parser.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8", errors="replace", newline="") as f:
            sample = f.read(8192)
            f.seek(0)
            dialect = sniff_dialect(sample)
            reader = csv.reader(f, dialect)
            rows = list(reader)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except csv.Error as e:
        print(f"error: csv parse: {e}", file=sys.stderr)
        return 1

    if not rows:
        print("error: empty CSV", file=sys.stderr)
        return 1

    header = rows[0] if not args.no_header else None
    data = rows[1:] if not args.no_header else rows
    ncols = len(header) if header else len(rows[0])

    try:
        ia = resolve_col(args.col_a, header, ncols, args.no_header)
        ib = resolve_col(args.col_b, header, ncols, args.no_header)
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # Gates
    if args.require_columns is not None and ncols < args.require_columns:
        msg = f"columns {ncols} < require-columns {args.require_columns}"
        if args.json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg, file=sys.stderr)
        return 2
    if args.require_rows is not None and len(data) < args.require_rows:
        msg = f"rows {len(data)} < require-rows {args.require_rows}"
        if args.json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg, file=sys.stderr)
        return 2

    # Apply swap/move to every row
    out_rows = [swap_list(r, ia, ib, move=args.move) for r in rows]

    out = sys.stdout
    if args.in_place:
        out = open(args.file, "w", encoding="utf-8", newline="")
    writer = csv.writer(out, dialect)
    writer.writerows(out_rows)
    if args.in_place:
        out.close()

    if args.json:
        print(json.dumps({
            "file": args.file,
            "column_a": args.col_a,
            "column_b": args.col_b,
            "operation": "move" if args.move else "swap",
            "rows": len(data),
            "columns": ncols,
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
