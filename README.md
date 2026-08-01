# csv-swap-columns

Swap two columns of a CSV file, selected by header name or 1-based index.
Pure Python standard library, zero dependencies.

## Features

- Columns by name or index
- Header-less files with `--no-header`
- Delimiter auto-detection with `--delimiter auto`
- `--check` CI mode: fails when the columns are already identical

## Installation

```bash
pip install .
# or
pip install git+https://github.com/TataneSan/csv-swap-columns.git
```

## Usage

```bash
csv-swap-columns data.csv name email        # by header name
csv-swap-columns data.csv 1 3               # by index
csv-swap-columns --no-header data.csv 1 2
cat data.csv | csv-swap-columns - a b
```

### Example

```bash
$ cat people.csv
name,age,city
alice,30,paris

$ csv-swap-columns people.csv name city
city,age,name
paris,30,alice
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success |
| 1 | I/O, CSV parsing or CLI error |
| 2 | unknown column, out-of-range index, or `--check` failure |

## License

MIT
