from pathlib import Path
import json, os, subprocess, shutil
root=Path(__file__).resolve().parent
repos=root/'repos'
if repos.exists(): raise SystemExit('Refusing existing repos directory; inspect it before restoring.')
repos.mkdir()
env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1')
for name, spec in json.loads((root/'manifests/repos.json').read_text()).items():
    dest=repos/name
    subprocess.run(['git','clone',spec['url'],str(dest)],env=env,check=True)
    subprocess.run(['git','-C',str(dest),'checkout',spec['commit']],env=env,check=True)
    patch=root/'manifests'/f'{name}-tracked.patch'
    if patch.exists() and patch.stat().st_size:
        subprocess.run(['git','-C',str(dest),'apply',str(patch)],check=True)
    overlay=root/'overlays'/name
    if overlay.exists(): shutil.copytree(overlay,dest,dirs_exist_ok=True)
subprocess.run(['git','-C',str(repos/'openpi'),'submodule','update','--init','--recursive'],env=env,check=True)
print('Sources restored. Environments, LFS assets, content packs and model cache still need restoration.')
