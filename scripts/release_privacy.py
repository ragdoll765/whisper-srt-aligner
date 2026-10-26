"""Remove build provenance and reject private files in release archives."""
import argparse
import io
import re
import zipfile
from pathlib import Path


def private_metadata(name):
    parts = Path(name).parts
    return name.endswith('direct_url.json') or (
        any(part.endswith('.dist-info') for part in parts)
        and ('__pycache__' in parts or name.endswith(('.pyc', '.pyo')))
    )


def clean_bundle(folder):
    for path in folder.rglob('*'):
        if path.is_file() and private_metadata(str(path)):
            path.unlink()


def check_archive(path):
    # Check this workstation's home in both JSON and native Windows spelling.
    home = str(Path.home()).replace('\\', '/').rstrip('/').lower().encode()
    failures = []

    def inspect(data, name):
        normalized = data.replace(b'\\\\', b'/').replace(b'\\', b'/').lower()
        if home in normalized or home.decode().encode('utf-16le') in data.lower():
            failures.append(f'{name}: local home path')
        if re.search(rb'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----', data):
            failures.append(f'{name}: private key')

    def visit(archive, prefix=''):
        for item in archive.infolist():
            if item.is_dir():
                continue
            name = prefix + item.filename
            parts = item.filename.replace('\\', '/').split('/')
            if private_metadata(item.filename) or any(
                part in ('.codex', '.ssh', '.env', 'id_rsa', 'id_ed25519')
                or part.startswith('.env.') for part in parts
            ):
                failures.append(f'{name}: private file')
            data = archive.read(item)
            inspect(data, name)
            if item.filename.endswith(('.zip', '.whl')):
                with zipfile.ZipFile(io.BytesIO(data)) as nested:
                    visit(nested, name + '!')

    with zipfile.ZipFile(path) as archive:
        visit(archive)
    if failures:
        raise ValueError('\n'.join(failures))


def sanitize_archive(source, destination):
    """Copy an existing release, omitting provenance without changing its code."""
    if source.resolve() == destination.resolve():
        raise ValueError('Source and destination must differ')
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(destination, 'w') as clean:
        for item in original.infolist():
            if not private_metadata(item.filename):
                clean.writestr(item, original.read(item))
    try:
        check_archive(destination)
    except Exception:
        destination.unlink()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--sanitize-to', type=Path)
    args = parser.parse_args()
    if args.sanitize_to:
        sanitize_archive(args.archive, args.sanitize_to)
    else:
        check_archive(args.archive)
    print('Release privacy check passed')
