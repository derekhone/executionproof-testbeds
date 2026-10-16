#!/usr/bin/env python3
"""Inspect newly introduced Git blobs only; never execute submitted files."""
import argparse
import pathlib
import re
import subprocess
import sys

FORBIDDEN_SUFFIXES = (
    '.pyc', '.pyo', '.pyd', '.cubin', '.ptx', '.fatbin', '.o', '.obj',
    '.so', '.dll', '.exe', '.a', '.lib', '-wal', '-shm',
)
FORBIDDEN_NAMES = {'elementwise_add', 'vector_runner', '.abacus.donotdelete'}


def git(*args):
    return subprocess.check_output(['git', *args])


def verify_commit(value):
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value):
        raise ValueError('Expected a full hexadecimal commit ID')
    git('cat-file', '-e', value + '^{commit}')
    return value


def blocked_path(path):
    p = pathlib.PurePosixPath(path.lower())
    return ('__pycache__' in p.parts or p.name in FORBIDDEN_NAMES
            or p.name.endswith(FORBIDDEN_SUFFIXES))


def blob_prefix(oid):
    # Stream only the signature rather than materializing a potentially large binary.
    proc = subprocess.Popen(['git', 'cat-file', 'blob', oid], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)
    try:
        prefix = proc.stdout.read(4)
    finally:
        proc.stdout.close()
        proc.wait()
    return prefix


def inspect(base, head):
    verify_commit(base)
    verify_commit(head)
    # --no-renames intentionally treats a rename/copy destination as an addition.
    raw = git('diff', '--name-only', '--diff-filter=A', '--no-renames', '-z', base, head, '--')
    paths = [p.decode('utf-8', 'surrogateescape') for p in raw.split(b'\0') if p]
    failures = []
    for path in paths:
        if blocked_path(path):
            failures.append((path, 'generated output or local-state filename'))
            continue
        entry = git('--literal-pathspecs', 'ls-tree', '-z', head, '--', path).split(b'\0')[0]
        metadata, actual = entry.split(b'\t', 1)
        mode, kind, oid = metadata.split()
        if actual.decode('utf-8', 'surrogateescape') != path:
            raise ValueError('Unexpected tree lookup result')
        if kind != b'blob' or mode == b'120000':
            failures.append((path, 'new symlink/submodule needs owner review'))
            continue
        if blob_prefix(oid.decode('ascii')) == b'\x7fELF':
            failures.append((path, 'ELF compiled output'))
    return paths, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', required=True)
    args = parser.parse_args()
    try:
        paths, failures = inspect(args.base, args.head)
    except (ValueError, subprocess.SubprocessError, OSError) as exc:
        print(f'Publication hygiene could not complete: {type(exc).__name__}', file=sys.stderr)
        return 2  # Missing history or inspection errors never silently pass.
    for path, reason in failures:
        # repr escapes newline/control characters; never print blob contents.
        print(f'BLOCKED {path!r}: {reason}')
    print(f'Inspected {len(paths)} added destinations; blocked {len(failures)}.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
