"""Share the linter's pinned official SDK archive with Direct Mode."""
from pathlib import Path
import shutil
archive='genvm-universal-v0.3.0-rc7.tar.xz'
source=Path.home()/'.cache/genvm-linter'/archive
target=Path.home()/'.cache/gltest-direct'/archive
if not source.exists():raise SystemExit('Run genvm-lint check contracts/band_pact.py first.')
target.parent.mkdir(parents=True,exist_ok=True)
if not target.exists():shutil.copyfile(source,target)
print('Pinned SDK archive ready.')
