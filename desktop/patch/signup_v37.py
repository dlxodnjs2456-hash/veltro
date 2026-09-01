import pathlib

# v1.0.38 correction:
# The verified HTS base already contains the original '회원가입하기' entry.
# Do not inject another signup button. Keep this patch file as a no-op so the
# existing release workflow remains stable without touching unrelated logic.
root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
if not renderer_path.exists():
    raise RuntimeError('renderer.js missing')
print('VELTRO signup patch: existing signup UI preserved; duplicate injection disabled')
