"""Build local release assets. No Git mutations, tagging, or publication."""
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path
from whisper_srt_aligner import __version__
from release_privacy import check_archive

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
DIST.mkdir(exist_ok=True)
subprocess.run([sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation',
                '--wheel-dir',str(DIST),str(ROOT)],check=True)
archive=DIST/f'whisper-srt-aligner-{__version__}-source.zip'
included=['README.md','LICENSE','CHANGELOG.md','pyproject.toml','.gitignore',
          'src','tests','scripts','docs','packaging','.github']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as output:
    for name in included:
        candidate=ROOT/name
        paths=[candidate] if candidate.is_file() else sorted(candidate.rglob('*'))
        for path in paths:
            if not path.is_file() or any(p=='__pycache__' or p.endswith('.egg-info') for p in path.parts):
                continue
            output.write(path,f'whisper-srt-aligner-{__version__}/{path.relative_to(ROOT).as_posix()}')
assets=[DIST/f'whisper_srt_aligner-{__version__}-py3-none-any.whl',archive]
windows=DIST/'windows'/f'WhisperSrtAligner-{__version__}-windows-x64.zip'
if windows.is_file():assets.append(windows)
checksums=[]
for path in assets:
    check_archive(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    checksums.append(f'{digest}  {path.name}')
(DIST/'SHA256SUMS.txt').write_text('\n'.join(checksums)+'\n',encoding='utf-8')
print('\n'.join(checksums))
