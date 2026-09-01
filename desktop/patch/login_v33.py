import pathlib, re

root = pathlib.Path.cwd()
renderer_path = root / 'desktop' / 'build' / 'src' / 'renderer.js'
styles_path = root / 'desktop' / 'build' / 'src' / 'styles.css'

renderer = renderer_path.read_text(encoding='utf-8')

# Keep the requested monochrome person / lock icons.
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

# Restore the login poster behavior used before the v1.0.32 startup-paint experiment.
renderer, n_img = re.subn(
    r'<img class="veltro-login-poster-img(?: ready)?" id="loginPosterImage"(?:\s+src="[^"]*")?\s+alt="VELTRO">',
    '<img class="veltro-login-poster-img" id="loginPosterImage" alt="VELTRO">',
    renderer,
    count=1,
)
if n_img != 1:
    raise RuntimeError(f'Could not restore original login poster element: {n_img}')

old_loader_pattern = re.compile(
    r"\(async\(\)=>\{const img=document\.getElementById\('loginPosterImage'\);if\(!img\)return;.*?\}\)\(\);",
    re.S,
)
original_loader = """(async()=>{const img=document.getElementById('loginPosterImage');if(!img)return;try{const cfg=await window.desktop?.remoteLoginPoster?.();const remote=cfg?.login_image_data;if(remote&&String(remote).startsWith('data:image/')){img.src=remote;img.classList.add('ready');return;}}catch{}try{const local=await window.desktop?.loginPosterUrl?.();if(local){img.src=local;img.classList.add('ready');}}catch{}})();"""
renderer, n_loader = old_loader_pattern.subn(original_loader, renderer, count=1)
if n_loader != 1:
    raise RuntimeError(f'Could not restore original login poster loader: {n_loader}')

renderer_path.write_text(renderer, encoding='utf-8')

styles = styles_path.read_text(encoding='utf-8')
styles += r'''

/* v1.0.33: restore pre-v1.0.32 login poster presentation; keep requested monochrome icons */
.exact-poster-art{background:#03101f!important}
.veltro-login-poster-img{opacity:0!important;visibility:hidden!important;background:#03101f!important;transition:none!important}
.veltro-login-poster-img.ready{opacity:1!important;visibility:visible!important}
.veltro-ref-card .user-icon::before,.veltro-ref-card .user-icon::after,.veltro-ref-card .lock-icon::before,.veltro-ref-card .lock-icon::after{content:none!important;display:none!important}
.veltro-ref-card .field-icon{font-family:"Segoe UI Symbol","Segoe UI Emoji",sans-serif!important;filter:grayscale(1) saturate(0) brightness(1.72)!important;color:#d7dde4!important}
'''
styles_path.write_text(styles, encoding='utf-8')

if 'src="../assets/login_left_current.jpg"' in renderer:
    raise RuntimeError('v1.0.32 forced poster source still present')
if "localStorage.getItem('veltro_login_poster')" in renderer:
    raise RuntimeError('v1.0.32 cached poster startup path still present')
if original_loader not in renderer:
    raise RuntimeError('Original remote-first poster loader missing')
if '&#128100;' not in renderer or '&#128274;' not in renderer:
    raise RuntimeError('Requested login icons missing')

print('VELTRO v1.0.33 login icons kept; original poster behavior restored')
