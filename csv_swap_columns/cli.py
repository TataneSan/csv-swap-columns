"""Swap or reorder columns of a CSV file by name or index.

Two operation modes (mutually exclusive):

  --swap A B        exchange two columns (names or 1-based indexes)
  --order C1,C2...  place the listed columns first, in that order; columns
                    not listed keep their original relative order at the end
                    (use --strict to require every column to be listed)

Other options:

  -d, --delimiter   input delimiter (default: auto-detect among , ; tab |)
  -D, --out-delimiter  delimiter for the output (default: same as input)
  --no-header       treat the first row as data; columns are referenced by
                    1-based index only
  --check           CI mode: verify the file is already in the requested
                    order without writing anything (exit 2 otherwise)
  -i, --in-place    rewrite the input file instead of printing to stdout
  -j, --json        emit a JSON summary on stderr

Exit codes:
  0  success (or --check passed)
  1  CLI / I/O error
  2  --check failed: columns are not in the requested order
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple

CANDIDATE_DELIMITERS = [",", ";", "\t", "|"]


class CliError(Exception):
    """Fatal CLI error; caught by main() and reported with exit code 1."""


def sniff_delimiter(sample: str) -> str:
    """Pick the candidate delimiter that splits the most lines consistently."""
    lines = [l for l in sample.splitlines() if l.strip()][:20]
    if not lines:
        return ","
    best = ","
    best_score = -1.0
    for delim in CANDIDATE_DELIMITERS:
        counts = []
        for line in lines:
            # count occurrences outside quotes
            in_q = False
            count = 0
            i = 0
            while i < len(line):
                ch = line[i]
                if ch == '"':
                    if in_q and i + 1 < len(line) and line[i + 1] == '"':
                        i += 2
                        continue
                    in_q = not in_q
                elif ch == delim and not in_q:
                    count += 1
                i += 1
            counts.append(count)
        if min(counts) == 0:
            score = 0.0
        else:
            score = min(counts) * (1 if len(set(counts)) == 1 else 0.5)
        if score > best_score:
            best_score = score
            best = delim
    return best


def read_csv(path: Optional[str], delimiter: str) -> Tuple[List[List[str]], Optional[str]]:
    """Return (rows, error_stream). Reads stdin when path is None."""
    if path is None:
        text = sys.stdin.read()
    else:
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as fh:
                text = fh.read()
        except OSError as exc:
            raise CliError(f"error: cannot read {path}: {exc}")
    if not text.strip():
        return [], None
    delim = delimiter or sniff_delimiter(text[:8192])
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = [row for row in reader]
    return rows, delim


def resolve_column(
    ref: str, header: List[str], headers_available: bool
) -> int:
    """Resolve a column reference (name or 1-based index) to a 0-based index."""
    if ref.isdigit():
        idx = int(ref) - 1
        if 0 <= idx < len(header):
            return idx
        raise CliError(
            f"error: column index {ref} out of range (1..{len(header)})"
        )
    if headers_available:
        matches = [i for i, h in enumerate(header) if h == ref]
        if not matches:
            # case-insensitive fallback suggestion
            low = [h.lower() for h in header]
            if ref.lower() in low:
                i = low.index(ref.lower())
                raise CliError(
                    f"error: column '{ref}' not found; did you mean '{header[i]}'?"
                )
            raise CliError(
                f"error: column '{ref}' not found in header {header}"
            )
        if len(matches) > 1:
            raise CliError(f"error: duplicate column name '{ref}' in header")
        return matches[0]
    raise CliError(
        f"error: column names need a header row (use 1-based indexes with --no-header)"
    )


def parse_order_args(values: List[str]) -> List[str]:
    """Accept both comma-separated and space-separated column lists."""
    refs: List[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                refs.append(part)
    return refs


def compute_new_order(
    n_cols: int,
    header: List[str],
    headers_available: bool,
    swap: Optional[List[str]],
    order: Optional[List[str]],
    strict: bool,
) -> List[int]:
    if swap:
        if len(swap) != 2:
            raise CliError("error: --swap expects exactly two columns")
        a = resolve_column(swap[0], header, headers_available)
        b = resolve_column(swap[1], header, headers_available)
        new_order = list(range(n_cols))
        new_order[a], new_order[b] = new_order[b], new_order[a]
        return new_order
    assert order is not None
    indexes = [resolve_column(r, header, headers_available) for r in order]
    if len(set(indexes)) != len(indexes):
        raise CliError("error: --order lists a column more than once")
    remaining = [i for i in range(n_cols) if i not in indexes]
    if strict and remaining:
        missing = [
            header[i] if headers_available else str(i + 1) for i in remaining
        ]
        raise CliError(
            f"error: --strict requires every column to appear in --order; missing: {missing}"
        )
    return indexes + remaining


def reorder_rows(rows: List[List[str]], new_order: List[int]) -> List[List[str]]:
    out: List[List[str]] = []
    for row in rows:
        new_row = []
        for idx in new_order:
            new_row.append(row[idx] if idx < len(row) else "")
        out.append(new_row)
    return out


def emit_csv(rows: List[List[str]], delimiter: str, out) -> None:
    writer = csv.writer(out, delimiter=delimiter, lineterminator="\n")
    writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="csv-swap-columns",
        description="Swap or reorder CSV columns by name or 1-based index.",
    )
    p.add_argument("file", nargs="?", help="input CSV (default: stdin)")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--swap",
        nargs=2,
        metavar=("A", "B"),
        help="swap two columns (names or 1-based indexes)",
    )
    mode.add_argument(
        "--order",
        nargs="+",
        metavar="COL",
        help="full column order (comma or space separated); unlisted columns keep their relative order at the end",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="with --order: fail unless every column is listed",
    )
    p.add_argument("-d", "--delimiter", help="input delimiter (default: auto-detect)")
    p.add_argument("-D", "--out-delimiter", help="output delimiter (default: same as input)")
    p.add_argument(
        "--no-header",
        action="store_true",
        help="treat the first row as data; reference columns by 1-based index",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="CI mode: verify the requested order without writing (exit 2 on mismatch)",
    )
    p.add_argument(
        "-i", "--in-place",
        action="store_true",
        help="rewrite the input file in place",
    )
    p.add_argument("-j", "--json", action="store_true", help="JSON summary on stderr")
    p.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.in_place and not args.file:
        parser.error("--in-place requires an input file")
    if args.in_place and args.check:
        parser.error("--in-place and --check are mutually exclusive")

    try:
        rows, delim = read_csv(args.file, args.delimiter)
    except CliError as exc:
        print(exc, file=sys.stderr)
        return 1
    if not rows:
        print("error: empty input", file=sys.stderr)
        return 1

    headers_available = not args.no_header
    header = rows[0] if headers_available else [str(i + 1) for i in range(max(len(r) for r in rows))]
    n_cols = max(len(r) for r in rows)

    order_refs = parse_order_args(args.order) if args.order else None
    try:
        new_order = compute_new_order(
            n_cols, header, headers_available, args.swap, order_refs, args.strict
        )
    except CliError as exc:
        print(exc, file=sys.stderr)
        return 1

    # Normalized to full-length rows for output
    padded = [r + [""] * (n_cols - len(r)) for r in rows]
    result = reorder_rows(padded, new_order)

    out_delim = args.out_delimiter or delim or ","

    summary: Dict[str, Any] = {
        "file": args.file or "<stdin>",
        "columns": n_cols,
        "new_order": [
            header[i] if headers_available else i + 1 for i in new_order
        ],
        "delimiter_in": delim,
        "delimiter_out": out_delim,
    }

    if args.check:
        identity = new_order == list(range(n_cols))
        summary["check"] = "pass" if identity else "fail"
        if args.json:
            json.dump(summary, sys.stderr, indent=2)
            sys.stderr.write("\n")
        if identity:
            fmt = ", ".join(summary["new_order"])
            print(f"columns already in requested order ({fmt})")
            return 0
        print("columns are NOT in the requested order", file=sys.stderr)
        return 2

    if args.in_place:
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(os.path.abspath(args.file)), suffix=".csv"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
                emit_csv(result, out_delim, fh)
            os.replace(tmp, args.file)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        summary["written"] = args.file
        print(f"rewrote {args.file} ({len(result)} rows)")
    else:
        emit_csv(result, out_delim, sys.stdout)

    if args.json:
        json.dump(summary, sys.stderr, indent=2)
        sys.stderr.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
