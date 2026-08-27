import base64, json, os, pathlib, re

root = pathlib.Path.cwd()
build = root / 'desktop' / 'build'
renderer_path = build / 'src' / 'renderer.js'
styles_path = build / 'src' / 'styles.css'
pkg_path = build / 'package.json'
asset_path = build / 'assets' / 'login_left_current.jpg'
version = os.environ.get('VELTRO_VERSION', '').strip()
if not re.fullmatch(r'\d+\.\d+\.\d+', version):
    raise RuntimeError(f'Invalid VELTRO_VERSION: {version!r}')

# Use the approved VELTRO poster asset already stored in the repository.
poster_b64 = ''
poster_b64 += (root / 'desktop' / 'branding' / 'login_left_v107_part0.b64').read_text(encoding='utf-8')
poster_b64 += (root / 'desktop' / 'branding' / 'login_left_v107_part1.b64').read_text(encoding='utf-8')
poster_b64 = re.sub(r'\s+', '', poster_b64)
poster = base64.b64decode(poster_b64)
if len(poster) < 50000:
    raise RuntimeError('login poster asset is unexpectedly small')
asset_path.parent.mkdir(parents=True, exist_ok=True)
asset_path.write_bytes(poster)

renderer = renderer_path.read_text(encoding='utf-8')
# Remove the broken asynchronous runtime poster loader. The poster is now a normal packaged asset.
renderer = re.sub(r"(?m)^\s*window\.desktop\?\.assetUrl\?\.\('login_left_v\d+\.jpg'\).*?\.catch\(\(\)=>\{\}\);\s*$", '', renderer)

left_pattern = re.compile(
    r'<div class="login-art veltro-login-art exact-poster-art" id="loginPoster">\s*'
    r'<div class="version" id="version">v [^<]+</div>\s*</div>',
    re.S
)
left_html = f'''<div class="login-art veltro-login-art exact-poster-art" id="loginPoster">
            <img class="veltro-login-poster-img" src="../assets/login_left_current.jpg" alt="VELTRO">
            <div class="version" id="version">v {version}</div>
          </div>'''
renderer2, n = left_pattern.subn(left_html, renderer, count=1)
if n != 1:
    raise RuntimeError('Could not replace the v1.0.12 login poster panel')
renderer = renderer2
renderer = re.sub(r'v 1\.0\.\d+', f'v {version}', renderer)
renderer_path.write_text(renderer, encoding='utf-8')

styles = styles_path.read_text(encoding='utf-8')
styles += r'''

/* Stable packaged login poster */
.exact-poster-art{
  position:relative !important;
  overflow:hidden !important;
  padding:0 !important;
  background:#03101f !important;
}
.exact-poster-art::before,.exact-poster-art::after{content:none !important;display:none !important}
.veltro-login-poster-img{
  position:absolute !important;
  inset:0 !important;
  width:100% !important;
  height:100% !important;
  display:block !important;
  object-fit:cover !important;
  object-position:center center !important;
  z-index:1 !important;
}
.exact-poster-art .version{
  z-index:5 !important;
  left:14px !important;
  bottom:10px !important;
  color:#fff !important;
  background:rgba(3,16,31,.72) !important;
  padding:3px 7px !important;
  border-radius:2px !important;
}
'''
styles_path.write_text(styles, encoding='utf-8')

pkg = json.loads(pkg_path.read_text(encoding='utf-8-sig'))
pkg['version'] = version
pkg.setdefault('build', {})['files'] = ['src/**/*', 'assets/**/*', 'package.json']
pkg_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding='utf-8')

final_renderer = renderer_path.read_text(encoding='utf-8')
final_styles = styles_path.read_text(encoding='utf-8')
if '../assets/login_left_current.jpg' not in final_renderer:
    raise RuntimeError('static login poster image is missing')
if "assetUrl?.('login_left_v" in final_renderer:
    raise RuntimeError('old async login poster loader is still present')
if 'object-fit:cover !important' not in final_styles:
    raise RuntimeError('stable poster CSS is missing')
if not asset_path.exists() or asset_path.stat().st_size != len(poster):
    raise RuntimeError('packaged poster asset verification failed')
print(f'VELTRO {version} stable login poster patch verified')
