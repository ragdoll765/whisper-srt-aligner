import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from release_privacy import check_archive, sanitize_archive


class ReleasePrivacyTests(unittest.TestCase):
    def test_sanitize_removes_provenance_and_preserves_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / 'original.zip'
            clean = Path(folder) / 'clean.zip'
            runtime = {
                'app.exe': b'unchanged runtime',
                '_internal/base_library.zip': self.nested('module.pyc', b'bytecode'),
                '_internal/pkg.dist-info/licenses/LICENSE': b'license',
            }
            with zipfile.ZipFile(original, 'w') as archive:
                for name, data in runtime.items():
                    archive.writestr(name, data)
                archive.writestr('_internal/pkg.dist-info/direct_url.json',
                                 str(Path.home()))
                archive.writestr('_internal/pkg.dist-info/licenses/__pycache__/a.pyc',
                                 str(Path.home()))
            sanitize_archive(original, clean)
            with zipfile.ZipFile(clean) as archive:
                self.assertEqual(set(archive.namelist()), set(runtime))
                for name, data in runtime.items():
                    self.assertEqual(archive.read(name), data)

    @staticmethod
    def nested(name, data):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr(name, data)
        return stream.getvalue()

    def test_rejects_private_files_paths_and_nested_archives(self):
        cases = [
            ('.codex/config.json', b'{}'),
            ('.env.production', b'example'),
            ('metadata.json', str(Path.home()).replace('\\', '\\\\').encode()),
            ('nested.zip', self.nested('data', str(Path.home()).encode())),
            ('key', b'-----BEGIN ' + b'PRIVATE KEY-----'),
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.zip'
            for name, data in cases:
                with self.subTest(name=name):
                    with zipfile.ZipFile(path, 'w') as archive:
                        archive.writestr(name, data)
                    with self.assertRaises(ValueError):
                        check_archive(path)

    def test_failed_sanitization_does_not_leave_publishable_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / 'original.zip'
            clean = Path(folder) / 'clean.zip'
            with zipfile.ZipFile(original, 'w') as archive:
                archive.writestr('unexpected.txt', str(Path.home()))
            with self.assertRaises(ValueError):
                sanitize_archive(original, clean)
            self.assertFalse(clean.exists())
            self.assertTrue(original.exists())
