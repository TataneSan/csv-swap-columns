# csv-swap-columns

Swap two columns of a CSV file, or move one column to another's position.
Columns are selected by header name or 1-based index (negative indices
count from the end). The delimiter is sniffed automatically. Pure stdlib.

## Features

- Swap by header name or 1-based index (`-1` = last column)
- `--move` reinserts column A at column B's position
- Delimiter sniffing (`,;` TAB `|`) or explicit `-d`
- `--no-header` for headerless files, `--in-place` to rewrite the file
- Rows padded to the widest row before the operation
- CI gates `--require-columns N` / `--require-rows N` (exit 2 on failure)
- `--json` emits a small report on stderr
- Zero dependencies, Python >= 3.9

## Install

```bash
pip install .
# or
pip install git+https://github.com/TataneSan/csv-swap-columns.git
```

## Usage

```bash
# Swap 'email' and 'name' columns
csv-swap-columns email name users.csv

# Swap first and last columns from stdin
printf 'a,b,c\n1,2,3\n' | csv-swap-columns 1 -1 -

# Move column A to column C's position
printf 'a,b,c\n1,2,3\n' | csv-swap-columns --move a c -
# b,c,a
# 2,3,1

# Headerless file, indices only
csv-swap-columns 2 4 data.csv --no-header

# Rewrite the file in place, with a CI gate on shape
csv-swap-columns a c users.csv --in-place --require-columns 3
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | ok |
| 1 | I/O or CLI error |
| 2 | unknown column, out-of-range index, identical columns, or a `--require-*` gate failed |

## Tests

```bash
python -m unittest discover -s tests
```

## License

MIT
