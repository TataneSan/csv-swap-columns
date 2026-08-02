# csv-swap-columns

Swap or move CSV columns by name or index (supports negative indices).

## Features

- Fast, dependency-free Python CLI
- Reads from stdin or file
- Machine-readable JSON output (`--json`)
- CI gates: exit code 2 when constraints fail (`--require-*`)
- Unicode-aware

## Install

```bash
pip install .
```

or directly from the repo:

```bash
pip install git+https://github.com/TataneSan/csv-swap-columns.git
```

## Usage

```
csv-swap-columns [file] A B [--move] [--no-header] [--in-place] [--require-columns N] [--require-rows N] [--json]
```

## Examples

```bash
csv-swap-columns data.csv name age --move
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | success |
| 1    | I/O or CLI error |
| 2    | gate condition not met (CI) |

## License

MIT
