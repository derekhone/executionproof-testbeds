"""Synthetic fixtures only. No research code, shipped binaries or endpoints run."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('hygiene', Path(__file__).with_name('publication_hygiene.py'))
hygiene = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hygiene)


class GuardTests(unittest.TestCase):
    def test_filename_classes(self):
        blocked = ['a/__pycache__/x', 'x.pyc', 'x.pyo', 'x.pyd', 'x.sqlite3-wal',
                   'x.sqlite-shm', 'x.db-wal', 'raw-wal', 'x.cubin', 'x.ptx', 'x.fatbin',
                   'x.o', 'x.obj', 'x.so', 'x.dll', 'x.exe', 'x.a', 'x.lib',
                   'kernels/elementwise_add', 'kernels/vector_runner', '.abacus.donotdelete',
                   'nested/X.PYC']
        for name in blocked:
            with self.subTest(name=name):
                self.assertTrue(hygiene.blocked_path(name))
        for name in ['README.md', 'kernel.cu', 'results/failure.json', 'x.sqlite3',
                     'MANIFEST.sha256', 'no-extension', 'file with space.md']:
            with self.subTest(name=name):
                self.assertFalse(hygiene.blocked_path(name))

    def test_git_diff_behavior_and_signature(self):
        old = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                def git(*args):
                    return subprocess.check_output(['git', *args], stderr=subprocess.DEVNULL).decode().strip()
                git('init', '-q')
                git('config', 'user.name', 'Synthetic Guard Test')
                git('config', 'user.email', 'guard-test@example.invalid')
                Path('historical.pyc').write_bytes(b'preserved-fixture')
                Path('old.md').write_text('document')
                git('add', '.')
                git('commit', '-qm', 'synthetic baseline')
                base = git('rev-parse', 'HEAD')
                paths, failures = hygiene.inspect(base, base)
                self.assertEqual((paths, failures), ([], []))
                # Existing generated artifact changes are deliberately grandfathered.
                Path('historical.pyc').write_bytes(b'modified-fixture')
                git('add', '.')
                git('commit', '-qm', 'existing fixture change')
                self.assertEqual(hygiene.inspect(base, git('rev-parse', 'HEAD'))[1], [])
                Path('innocent-name').write_bytes(b'\x7fELF' + b'\x00' * 12)
                Path('bad\nname.pyc').write_bytes(b'fixture')
                Path('copy.cubin').write_text('document')
                Path('odd [name].md').write_text('safe')
                Path('link.md').symlink_to('old.md')
                git('mv', 'old.md', 'renamed.ptx')
                git('add', '.')
                git('commit', '-qm', 'new synthetic artifacts')
                head = git('rev-parse', 'HEAD')
                paths, failures = hygiene.inspect(base, head)
                rejected = {p for p, _ in failures}
                self.assertEqual(rejected, {'innocent-name', 'bad\nname.pyc', 'copy.cubin', 'link.md', 'renamed.ptx'})
                self.assertIn('odd [name].md', paths)
                with self.assertRaises(ValueError):
                    hygiene.inspect('--help', head)
                with self.assertRaises(subprocess.CalledProcessError):
                    hygiene.inspect('0' * 40, head)
            finally:
                os.chdir(old)


if __name__ == '__main__':
    unittest.main()
