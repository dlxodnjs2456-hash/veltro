import base64, hashlib, json, os, pathlib, re

root=pathlib.Path.cwd(); build=root/'desktop'/'build'
renderer_path=build/'src'/'renderer.js'; styles_path=build/'src'/'styles.css'
main_path=build/'src'/'main.js'; preload_path=build/'src'/'preload.js'; pkg_path=build/'package.json'
asset_path=build/'assets'/'login_left_current.jpg'; resource_path=build/'resources'/'login-left.jpg'
version=os.environ.get('VELTRO_VERSION','').strip()
if not re.fullmatch(r'\d+\.\d+\.\d+',version): raise RuntimeError(f'Invalid VELTRO_VERSION: {version!r}')

poster_b64=re.sub(r'\s+','',(root/'desktop'/'patch'/'login_left_safe.b64').read_text(encoding='utf-8'))
poster=base64.b64decode(poster_b64,validate=True)
expected_sha256='b37d4a5df16d9b1cfca3f8cf1b75402f863b379fa26ab5b48cf24112d3fc1980'
actual_sha256=hashlib.sha256(poster).hexdigest()
if len(poster)!=9965 or not poster.startswith(b'\xff\xd8\xff') or actual_sha256!=expected_sha256:
    raise RuntimeError(f'login poster asset verification failed: bytes={len(poster)} sha256={actual_sha256}')
asset_path.parent.mkdir(parents=True,exist_ok=True); resource_path.parent.mkdir(parents=True,exist_ok=True)
asset_path.write_bytes(poster); resource_path.write_bytes(poster)

renderer=renderer_path.read_text(encoding='utf-8')
renderer=re.sub(r"(?m)^\s*window\.desktop\?\.assetUrl\?\.\('login_left_v\d+\.jpg'\).*?\.catch\(\(\)=>\{\}\);\s*$",'',renderer)
renderer=re.sub(r"(?m)^\s*window\.desktop\?\.loginPosterUrl\?\.\(\).*?\.catch\(\(\)=>\{\}\);\s*$",'',renderer)
renderer=re.sub(r"(?m)^\s*fetch\('https://mzjkvakigwtlibwlslhq\.supabase\.co/functions/v1/hts-config'.*?$",'',renderer)
left_pattern=re.compile(r'<div class="login-art veltro-login-art exact-poster-art" id="loginPoster">\s*(?:<img[^>]+>\s*)?<div class="version" id="version">v [^<]+</div>\s*</div>',re.S)
left_html=f'''<div class="login-art veltro-login-art exact-poster-art" id="loginPoster">
            <img class="veltro-login-poster-img" id="loginPosterImage" src="../assets/login_left_current.jpg" alt="VELTRO">
            <div class="version" id="version">v {version}</div>
          </div>'''
renderer,n=left_pattern.subn(left_html,renderer,count=1)
if n!=1: raise RuntimeError('Could not replace login poster panel')
renderer=re.sub(r'v 1\.0\.\d+',f'v {version}',renderer)
version_line="window.desktop?.version().then(v => document.getElementById('version').textContent = `v ${v}`);"
poster_line="window.desktop?.loginPosterUrl?.().then(u => { const img=document.getElementById('loginPosterImage'); if(img&&u) img.src=u; }).catch(()=>{});"
remote_line="fetch('https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/hts-config',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(cfg=>{const img=document.getElementById('loginPosterImage');if(img&&cfg?.login_image_data&&String(cfg.login_image_data).startsWith('data:image/'))img.src=cfg.login_image_data;}).catch(()=>{});"
if version_line not in renderer: raise RuntimeError('Could not find version binding')
renderer=renderer.replace(version_line,version_line+'\n  '+poster_line+'\n  '+remote_line,1)
renderer_path.write_text(renderer,encoding='utf-8')

styles=styles_path.read_text(encoding='utf-8')+r'''

/* Stable packaged login poster v4: admin remote image + local fallback */
.exact-poster-art{position:relative!important;overflow:hidden!important;padding:0!important;background:#03101f!important;display:block!important}
.exact-poster-art::before,.exact-poster-art::after{content:none!important;display:none!important}
.veltro-login-poster-img{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;display:block!important;object-fit:contain!important;object-position:center center!important;z-index:1!important;opacity:1!important;visibility:visible!important;background:#03101f!important}
.exact-poster-art .version{position:absolute!important;z-index:5!important;left:14px!important;bottom:10px!important;color:#fff!important;background:rgba(3,16,31,.72)!important;padding:3px 7px!important;border-radius:2px!important}
'''
styles_path.write_text(styles,encoding='utf-8')

main=main_path.read_text(encoding='utf-8')
if "const { pathToFileURL } = require('url');" not in main:
    anchor="const path = require('path');"
    if anchor not in main: raise RuntimeError('path require anchor missing in main.js')
    main=main.replace(anchor,anchor+"\nconst { pathToFileURL } = require('url');",1)
main=re.sub(r"(?m)^\s*ipcMain\.handle\('app:login-poster-url'.*?$",'',main)
handler_anchor="ipcMain.handle('app:quit',()=>app.quit());"
if handler_anchor not in main: raise RuntimeError('app:quit handler missing in main.js')
main=main.replace(handler_anchor,handler_anchor+"\nipcMain.handle('app:login-poster-url',()=>pathToFileURL(path.join(process.resourcesPath,'login-left.jpg')).toString());",1)
main_path.write_text(main,encoding='utf-8')

preload=preload_path.read_text(encoding='utf-8')
preload=re.sub(r"(?m)^\s*loginPosterUrl:.*?$",'',preload)
quit_anchor="quit: () => ipcRenderer.invoke('app:quit'),"
if quit_anchor not in preload: raise RuntimeError('quit bridge missing in preload.js')
preload=preload.replace(quit_anchor,quit_anchor+"\n  loginPosterUrl: () => ipcRenderer.invoke('app:login-poster-url'),",1)
preload_path.write_text(preload,encoding='utf-8')

pkg=json.loads(pkg_path.read_text(encoding='utf-8-sig')); pkg['version']=version
pkg.setdefault('build',{})['files']=['src/**/*','assets/**/*','package.json']
extra=pkg['build'].get('extraResources') or []
extra=[x for x in extra if not(isinstance(x,dict) and x.get('to')=='login-left.jpg')]
extra.append({'from':'resources/login-left.jpg','to':'login-left.jpg'}); pkg['build']['extraResources']=extra
pkg_path.write_text(json.dumps(pkg,ensure_ascii=False,indent=2),encoding='utf-8')

if 'id="loginPosterImage"' not in renderer: raise RuntimeError('loginPosterImage missing')
if "loginPosterUrl?.()" not in renderer: raise RuntimeError('loginPosterUrl renderer binding missing')
if "functions/v1/hts-config" not in renderer: raise RuntimeError('admin-managed HTS config fetch missing')
if "app:login-poster-url" not in main or "process.resourcesPath" not in main: raise RuntimeError('login poster main-process URL handler missing')
if "loginPosterUrl:" not in preload: raise RuntimeError('loginPosterUrl preload bridge missing')
if {'from':'resources/login-left.jpg','to':'login-left.jpg'} not in pkg['build']['extraResources']: raise RuntimeError('extraResources poster packaging missing')
if asset_path.read_bytes()!=poster or resource_path.read_bytes()!=poster: raise RuntimeError('poster asset write verification failed')
print(f'VELTRO {version} admin-managed login poster patch verified: {actual_sha256}')