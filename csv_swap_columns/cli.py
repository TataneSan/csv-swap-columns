"""Swap two columns of a CSV file.

Reads a CSV file (or stdin), swaps two columns identified by name or
0-based index, and writes the result to stdout.

Exit codes:
    0  success (or --check passed: the two columns differ)
    1  I/O or CLI error (missing file, unknown column, invalid CSV)
    2  --check failed: the two columns are identical everywhere
"""

import argparse
import csv
import io
import json
import sys


def _open_input(path):
    """Return (text stream, should_close)."""
    if path in (None, "-"):
        return sys.stdin, False
    return open(path, "r", newline="", encoding="utf-8"), True


def _resolve_column(header, spec):
    """Resolve a column spec (name or 0-based index) to an index."""
    try:
        idx = int(spec)
    except (TypeError, ValueError):
        idx = None
    if idx is not None:
        if idx < 0 or idx >= len(header):
            raise ValueError(
                "column index %d out of range (0..%d)" % (idx, len(header) - 1)
            )
        return idx
    if spec not in header:
        raise ValueError("unknown column name: %r" % spec)
    return header.index(spec)


def swap_rows(rows, idx_a, idx_b):
    """Return new list of rows with columns idx_a and idx_b swapped."""
    out = []
    for row in rows:
        n = max(idx_a, idx_b) + 1
        padded = list(row) + [""] * (n - len(row))
        padded[idx_a], padded[idx_b] = padded[idx_b], padded[idx_a]
        out.append(padded)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="csv-swap-columns",
        description="Swap two columns of a CSV file, by name or 0-based index.",
    )
    parser.add_argument("file", nargs="?", default="-",
                        help="CSV file to read (default: stdin, use '-' for stdin)")
    parser.add_argument("--col-a", "-a", required=True,
                        help="first column (name or 0-based index)")
    parser.add_argument("--col-b", "-b", required=True,
                        help="second column (name or 0-based index)")
    parser.add_argument("--delimiter", "-d", default=",",
                        help="field delimiter (default: ',')")
    parser.add_argument("--no-header", action="store_true",
                        help="treat first row as data (columns referenced by index only)")
    parser.add_argument("--check", action="store_true",
                        help="do not print the CSV; exit 0 if the swap changes "
                             "something, 2 if the two columns are identical")
    parser.add_argument("--json", action="store_true",
                        help="print a JSON report to stderr")
    args = parser.parse_args(argv)

    try:
        stream, close = _open_input(args.file)
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    try:
        reader = csv.reader(stream, delimiter=args.delimiter)
        rows = [r for r in reader]
    except csv.Error as exc:
        if close:
            stream.close()
        print("error: invalid CSV: %s" % exc, file=sys.stderr)
        return 1
    if close:
        stream.close()

    if not rows:
        print("error: empty input", file=sys.stderr)
        return 1

    if args.no_header:
        header = [str(i) for i in range(max(len(r) for r in rows))]
        data_rows = rows
    else:
        header = rows[0]
        data_rows = rows[1:]

    try:
        idx_a = _resolve_column(header, args.col_a)
        idx_b = _resolve_column(header, args.col_b)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    if idx_a == idx_b:
        print("error: --col-a and --col-b refer to the same column", file=sys.stderr)
        return 1

    before = [list(r) for r in (rows if args.no_header else data_rows)]
    swapped_data = swap_rows(before, idx_a, idx_b)
    changed = before != swapped_data

    report = {
        "file": args.file,
        "col_a": {"spec": args.col_a, "index": idx_a, "name": header[idx_a]},
        "col_b": {"spec": args.col_b, "index": idx_b, "name": header[idx_b]},
        "rows": len(before),
        "changed": changed,
    }

    if args.check:
        if args.json:
            print(json.dumps(report, indent=2), file=sys.stderr)
        else:
            state = "differ" if changed else "identical"
            print("columns %d and %d %s over %d row(s)"
                  % (idx_a, idx_b, state, len(before)), file=sys.stderr)
        return 0 if changed else 2

    out_rows = swapped_data if args.no_header else [header] + swapped_data
    writer = csv.writer(sys.stdout, delimiter=args.delimiter,
                        lineterminator="\n")
    for row in out_rows:
        writer.writerow(row)

    if args.json:
        print(json.dumps(report, indent=2), file=sys.stderr)
    return 0
