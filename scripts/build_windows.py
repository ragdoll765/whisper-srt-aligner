"""Build a local, unsigned Windows GUI bundle. Never publishes a release."""
import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from whisper_srt_aligner import __version__
from release_privacy import clean_bundle, check_archive

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--work-dir',type=Path,required=True)
args=parser.parse_args()
if sys.platform!='win32':raise SystemExit('Build the Windows bundle on Windows')
output=ROOT/'dist/windows'
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean',
    '--workpath',str(args.work_dir),'--distpath',str(output),
    str(ROOT/'packaging/WhisperSrtAligner.spec')],check=True)
folder=output/'WhisperSrtAligner'
shutil.copyfile(ROOT/'docs/wiki/Windows-GUI.md',folder/'START-HERE.md')
(folder/'THIRD-PARTY-NOTICES.txt').write_text(
    'Whisper SRT Aligner is MIT licensed. Runtime dependencies and their licenses\n'
    'are included under _internal/*.dist-info and _internal/licenses.\n'
    'Python: https://www.python.org/psf/license/\n'
    'PyInstaller bootloader: GPL with distribution exception; https://pyinstaller.org/en/stable/license.html\n'
    'FFmpeg and speech models are NOT bundled. Install FFmpeg separately and consult\n'
    'its license. A selected model downloads from Hugging Face on first use.\n',encoding='utf-8')
clean_bundle(folder)
archive=Path(shutil.make_archive(str(output/f'WhisperSrtAligner-{__version__}-windows-x64'),'zip',output,'WhisperSrtAligner'))
check_archive(archive)
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.sha256').write_text(f'{digest}  {archive.name}\n',encoding='utf-8')
print(f'Built {archive} ({archive.stat().st_size/1024/1024:.1f} MiB)\nSHA256 {digest}')
