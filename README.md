# csv-swap-columns

![Python](https://img.shields.io/badge/python-%3E%3D3.9-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Échange deux colonnes d'un CSV, désignées par nom (via le header) ou par index 0-based. Utile pour réordonner un export avant import dans un outil qui impose un ordre de colonnes fixe.

Zéro dépendance, Python standard uniquement.

## Fonctionnalités

- Sélection par nom de colonne (défaut) ou par index avec `--index`
- Support des CSV sans header via `--no-header --index`
- Lignes de longueur variable : pad/truncate automatique, ou `--strict` pour les rejeter
- Séparateur configurable (`-d ';'`, tab...)
- Mode `--check` CI : exit 2 pour valider que le swap s'appliquerait (dry-run structurel)
- Rapport `--json` : index résolus, nombre de lignes, header après permutation

## Installation

```bash
pip install .
# ou directement depuis GitHub
pip install git+https://github.com/TataneSan/csv-swap-columns.git
```

## Usage

```text
csv-swap-columns --col1 X --col2 Y [--index] [--no-header] [-d D] [--strict] [--check] [--json] [-q] [INPUT]
```

| Option | Description |
|---|---|
| `--col1`, `--col2` | Colonnes à échanger (obligatoires, différentes) |
| `--index` | Interprète `col1`/`col2` comme des index 0-based |
| `--no-header` | CSV sans header (impose `--index`) |
| `-d, --delimiter` | Séparateur CSV (défaut `,`) |
| `--strict` | Erreur si une ligne n'a pas le même nombre de colonnes que le header |
| `--check` | CI : n'écrit rien, exit 2 si le swap s'appliquerait |
| `--json` | Rapport JSON au lieu du CSV permuté |
| `INPUT` | Fichier d'entrée ; `-` ou omis = stdin |

## Exemples

Par nom de colonne :

```bash
$ printf 'id,name,email\n1,alice,a@x.com\n' | csv-swap-columns --col1 name --col2 email -
id,email,name
1,a@x.com,alice
```

Par index :

```bash
$ printf 'a,b,c\n1,2,3\n' | csv-swap-columns --col1 0 --col2 2 --index -
c,b,a
3,2,1
```

CSV sans header :

```bash
$ printf '1,2,3\n4,5,6\n' | csv-swap-columns --no-header --index --col1 0 --col2 1 -
2,1,3
5,4,6
```

Mode CI :

```bash
$ printf 'a,b\n1,2\n' | csv-swap-columns --col1 a --col2 b --check -
colonnes 0 et 1 seraient permutees sur 2 ligne(s)
$ echo $?
2
```

Colonne introuvable → erreur explicite :

```bash
$ printf 'a,b\n' | csv-swap-columns --col1 z --col2 b -
erreur: colonne 'z' introuvable dans le header ['a', 'b']
$ echo $?
1
```

## Exit codes

| Code | Signification |
|---|---|
| 0 | Succès (swap effectué, ou `--check` OK) |
| 1 | Erreur I/O, CSV invalide, colonne introuvable |
| 2 | `--check` : un swap aurait effectivement lieu |

## Licence

MIT — voir [LICENSE](LICENSE).
