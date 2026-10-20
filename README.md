# gitignore-audit

Audit `.gitignore` rules against the files in a Git repository. The tool reports patterns that match nothing, are duplicated, are overly broad, or cannot affect files that are already tracked by Git.

## Features

- Detect stale `.gitignore` patterns that match no repository file.
- Detect duplicate ignore patterns.
- Flag common catch-all patterns such as `*` and `**`.
- Detect patterns that would ignore files already tracked by Git.
- Provide human-readable and JSON output.
- Use Git's own ignore matching through `git check-ignore`.

## Requirements

- Python 3.10 or newer
- Git installed and available on `PATH`
- A Git repository to audit

## Install

```sh
git clone https://example.com/gitignore-audit.git
cd gitignore-audit
```

No third-party Python dependencies are required.

## Usage

Audit the current repository:

```sh
python cli.py .
```

Audit another repository:

```sh
python cli.py /path/to/repository
```

Use a custom ignore file:

```sh
python cli.py . --gitignore .gitignore.custom
```

Emit machine-readable JSON:

```sh
python cli.py . --json
```

## Exit codes

- `0`: no issues found
- `1`: one or more audit issues found
- `2`: runtime error, such as missing Git or an invalid repository

## How it works

`gitignore-audit` walks the repository, collects candidate file and directory paths, and asks Git which `.gitignore` pattern applies to each path. It then compares those results with the list of tracked files. Because Git performs the matching, the audit reflects Git's ignore semantics rather than a simplified approximation.

## License

MIT License

Copyright (c) 2026 gitignore-audit contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
