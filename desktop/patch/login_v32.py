import pathlib, re

root = pathlib.Path.cwd()
renderer_path = root / 'desktop' / 'build' / 'src' / 'renderer.js'
styles_path = root / 'desktop' / 'build' / 'src' / 'styles.css'

renderer = renderer_path.read_text(encoding='utf-8')

# Keep the packaged image visible from the very first login paint.
renderer, n_img = re.subn(
    r'<img class="veltro-login-poster-img" id="loginPosterImage"(?:\s+src="[^"]*")?\s+alt="VELTRO">',
    '<img class="veltro-login-poster-img ready" id="loginPosterImage" src="../assets/login_left_current.jpg" alt="VELTRO">',
    renderer,
    count=1,
)
if n_img != 1:
    raise RuntimeError(f'Could not set immediate packaged login poster: {n_img}')

# Restore the requested login field icons only.
renderer, n_user = re.subn(
    r'<span class="field-icon user-icon"[^>]*>.*?</span>',
    '<span class="field-icon user-icon" aria-hidden="true">&#128100;</span>',
    renderer,
    count=1,
    flags=re.S,
)
renderer, n_lock = re.subn(
    r'<span class="field-icon lock-icon"[^>]*>.*?</span>',
    '<span class="field-icon lock-icon" aria-hidden="true">&#128274;</span>',
    renderer,
    count=1,
    flags=re.S,
)
if n_user != 1 or n_lock != 1:
    raise RuntimeError(f'Could not restore login icons: user={n_user} lock={n_lock}')

renderer_path.write_text(renderer, encoding='utf-8')

styles = styles_path.read_text(encoding='utf-8')
styles += r'''

/* v1.0.32 login-only startup paint fix */
.veltro-login-poster-img{opacity:1!important;visibility:visible!important}
'''
styles_path.write_text(styles, encoding='utf-8')

# Focused validation: no account/trade/data logic is touched by this patch.
if 'src="../assets/login_left_current.jpg"' not in renderer:
    raise RuntimeError('Packaged login poster source missing')
if '&#128100;' not in renderer or '&#128274;' not in renderer:
    raise RuntimeError('Requested login icons missing')
if 'opacity:1!important;visibility:visible!important' not in styles:
    raise RuntimeError('Immediate poster visibility override missing')

print('VELTRO v1.0.32 login-only patch verified')
