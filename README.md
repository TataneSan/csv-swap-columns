# csv-swap-columns

Swap or reorder the columns of a CSV file **by name or 1-based index**.
Header-aware, delimiter auto-detection, in-place rewriting, and a `--check`
CI mode to assert a file already has the columns in the expected order.

## Features

- `--swap A B` — exchange two columns (names or indexes)
- `--order C1,C2,...` — full reorder; unlisted columns keep their relative
  order at the end (`--strict` to require every column to be listed)
- Auto-detects input delimiter (`,` `;` tab `|`), quoting-aware
- `--no-header` mode for raw data (indexes only)
- `--in-place` atomic rewrite, or stream to stdout for pipes
- `--check` CI gate (exit 2 when the order doesn't match)
- `--json` summary on stderr

## Install

```bash
pip install .
# or from GitHub:
pip install git+https://github.com/TataneSan/csv-swap-columns.git
```

Requires Python 3.9+. No dependencies.

## Usage

Given `people.csv`:

```csv
name,age,city
alice,30,paris
bob,25,lyon
```

```bash
# Swap two columns by name
csv-swap-columns --swap name city people.csv
# city,age,name
# paris,30,alice
# lyon,25,bob

# Swap by index (1-based)
csv-swap-columns --swap 1 3 people.csv

# Reorder: city first, then name, the rest untouched
csv-swap-columns --order city,name people.csv

# Require every column to be listed
csv-swap-columns --order city,age,name --strict people.csv

# Rewrite the file in place
csv-swap-columns --swap age city -i people.csv

# Change output delimiter
csv-swap-columns --order city,name -D ';' people.csv

# Pipe through
cat people.csv | csv-swap-columns --swap name age > reordered.csv

# Headerless data
printf 'a,b,c\n1,2,3\n' | csv-swap-columns --no-header --swap 1 2

# CI: assert column order
csv-swap-columns --order name,age,city --check people.csv
echo $?   # 0 = order OK, 2 = mismatch
```

## Exit codes

| Code | Meaning                                   |
|------|-------------------------------------------|
| 0    | success (or `--check` passed)             |
| 1    | CLI / I/O error                           |
| 2    | `--check` failed: order doesn't match     |

## License

MIT — see [LICENSE](LICENSE).
