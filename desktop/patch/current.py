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
renderer=re.sub(r"(?m)^\s*window\.desktop\?\.remoteLoginPoster\?\.\(\).*?$",'',renderer)
renderer=re.sub(r"(?m)^\s*\(async\(\)=>\{const img=document\.getElementById\('loginPosterImage'\).*?$",'',renderer)
left_pattern=re.compile(r'<div class="login-art veltro-login-art exact-poster-art" id="loginPoster">\s*(?:<img[^>]+>\s*)?<div class="version" id="version">v [^<]+</div>\s*</div>',re.S)
left_html=f'''<div class="login-art veltro-login-art exact-poster-art" id="loginPoster">
            <img class="veltro-login-poster-img" id="loginPosterImage" alt="VELTRO">
            <div class="version" id="version">v {version}</div>
          </div>'''
renderer,n=left_pattern.subn(left_html,renderer,count=1)
if n!=1: raise RuntimeError('Could not replace login poster panel')
renderer=re.sub(r'v 1\.0\.\d+',f'v {version}',renderer)
version_line="window.desktop?.version().then(v => document.getElementById('version').textContent = `v ${v}`);"
poster_loader="""(async()=>{const img=document.getElementById('loginPosterImage');if(!img)return;try{const cfg=await window.desktop?.remoteLoginPoster?.();const remote=cfg?.login_image_data;if(remote&&String(remote).startsWith('data:image/')){img.src=remote;img.classList.add('ready');return;}}catch{}try{const local=await window.desktop?.loginPosterUrl?.();if(local){img.src=local;img.classList.add('ready');}}catch{}})();"""
if version_line not in renderer: raise RuntimeError('Could not find version binding')
renderer=renderer.replace(version_line,version_line+'\n  '+poster_loader,1)

# Replace CDN-only Highcharts loader with packaged local Highcharts assets.
chart_loader=r'''async function ensureHighchartsStock(){
  if(window.Highcharts?.stockChart) return window.Highcharts;
  if(window.__veltroHighchartsLoader) return window.__veltroHighchartsLoader;
  window.__veltroHighchartsLoader=(async()=>{
    const base=await window.desktop?.chartAssetsBase?.();
    if(!base) throw new Error('chart_assets_missing');
    const addCss=(rel)=>new Promise((resolve)=>{
      const href=base+rel;
      if([...document.querySelectorAll('link[rel="stylesheet"]')].some(x=>x.href===href)) return resolve();
      const l=document.createElement('link');l.rel='stylesheet';l.href=href;l.onload=()=>resolve();l.onerror=()=>resolve();document.head.appendChild(l);
    });
    const addScript=(rel)=>new Promise((resolve,reject)=>{
      const src=base+rel;
      if([...document.scripts].some(x=>x.src===src)) return resolve();
      const el=document.createElement('script');el.src=src;el.async=false;el.onload=resolve;el.onerror=()=>reject(new Error('chart_library_load_failed:'+rel));document.head.appendChild(el);
    });
    await Promise.all([
      addCss('css/stocktools/gui.css'),
      addCss('css/annotations/popup.css')
    ]);
    for(const rel of [
      'highstock.js',
      'indicators/indicators-all.js',
      'modules/annotations-advanced.js',
      'modules/price-indicator.js',
      'modules/full-screen.js',
      'modules/stock-tools.js'
    ]) await addScript(rel);
    if(!window.Highcharts?.stockChart) throw new Error('chart_library_load_failed');
    return window.Highcharts;
  })();
  return window.__veltroHighchartsLoader;
}

const DEFAULT_INDICATORS='''
renderer,n=re.subn(r'async function ensureHighchartsStock\(\)\{.*?\n\}\n\nconst DEFAULT_INDICATORS=',chart_loader,renderer,count=1,flags=re.S)
if n!=1: raise RuntimeError('Could not replace Highcharts loader')
renderer=renderer.replace("conn.textContent='LIVE · iTick';", "conn.textContent='LIVE · '+String(res?.provider||qr?.provider||state.market.provider||'LS').toUpperCase();")
renderer=renderer.replace("foot.textContent=`${currentCode} · ${res?.source==='live_samples'?'실시간 누적':'iTick K-line'} · ${bars.length}봉`;", "foot.textContent=`${currentCode} · ${String(res?.provider||state.market.provider||'LS').toUpperCase()} · ${bars.length}봉`;" )
renderer_path.write_text(renderer,encoding='utf-8')

styles=styles_path.read_text(encoding='utf-8')+r'''

/* Stable packaged login poster v6: remote-first, no fallback flash */
.exact-poster-art{position:relative!important;overflow:hidden!important;padding:0!important;background:#03101f!important;display:block!important}
.exact-poster-art::before,.exact-poster-art::after{content:none!important;display:none!important}
.veltro-login-poster-img{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;display:block!important;object-fit:cover!important;object-position:center center!important;z-index:1!important;opacity:0!important;visibility:hidden!important;background:#03101f!important}
.veltro-login-poster-img.ready{opacity:1!important;visibility:visible!important}
.exact-poster-art .version{position:absolute!important;z-index:5!important;left:14px!important;bottom:10px!important;color:#fff!important;background:rgba(3,16,31,.72)!important;padding:3px 7px!important;border-radius:2px!important}
'''
styles_path.write_text(styles,encoding='utf-8')

main=main_path.read_text(encoding='utf-8')
if "const { pathToFileURL } = require('url');" not in main:
    anchor="const path = require('path');"
    if anchor not in main: raise RuntimeError('path require anchor missing in main.js')
    main=main.replace(anchor,anchor+"\nconst { pathToFileURL } = require('url');",1)
if "const https = require('https');" not in main:
    anchor="const path = require('path');"
    main=main.replace(anchor,anchor+"\nconst https = require('https');",1)
main=re.sub(r"(?m)^\s*ipcMain\.handle\('app:login-poster-url'.*?$",'',main)
main=re.sub(r"(?m)^\s*ipcMain\.handle\('app:chart-assets-base'.*?$",'',main)
main=re.sub(r"(?ms)^\s*ipcMain\.handle\('app:remote-login-poster'.*?^\s*\}\);\s*$",'',main)
handler_anchor="ipcMain.handle('app:quit',()=>app.quit());"
if handler_anchor not in main: raise RuntimeError('app:quit handler missing in main.js')
handlers="""ipcMain.handle('app:login-poster-url',()=>pathToFileURL(path.join(process.resourcesPath,'login-left.jpg')).toString());
ipcMain.handle('app:chart-assets-base',()=>pathToFileURL(path.join(process.resourcesPath,'highcharts')+path.sep).toString());
ipcMain.handle('app:remote-login-poster',()=>new Promise((resolve)=>{
  const req=https.get('https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/hts-config?ts='+Date.now(),{headers:{'Cache-Control':'no-cache','User-Agent':'VELTRO-HTS'}},(res)=>{
    let body='';
    res.setEncoding('utf8');
    res.on('data',chunk=>{body+=chunk;if(body.length>3500000)req.destroy();});
    res.on('end',()=>{try{resolve(res.statusCode===200?JSON.parse(body):null)}catch{resolve(null)}});
  });
  req.setTimeout(8000,()=>{req.destroy();resolve(null)});
  req.on('error',()=>resolve(null));
}));"""
main=main.replace(handler_anchor,handler_anchor+'\n'+handlers,1)
main_path.write_text(main,encoding='utf-8')

preload=preload_path.read_text(encoding='utf-8')
preload=re.sub(r"(?m)^\s*loginPosterUrl:.*?$",'',preload)
preload=re.sub(r"(?m)^\s*remoteLoginPoster:.*?$",'',preload)
preload=re.sub(r"(?m)^\s*chartAssetsBase:.*?$",'',preload)
quit_anchor="quit: () => ipcRenderer.invoke('app:quit'),"
if quit_anchor not in preload: raise RuntimeError('quit bridge missing in preload.js')
preload=preload.replace(quit_anchor,quit_anchor+"\n  loginPosterUrl: () => ipcRenderer.invoke('app:login-poster-url'),\n  remoteLoginPoster: () => ipcRenderer.invoke('app:remote-login-poster'),\n  chartAssetsBase: () => ipcRenderer.invoke('app:chart-assets-base'),",1)
preload_path.write_text(preload,encoding='utf-8')

pkg=json.loads(pkg_path.read_text(encoding='utf-8-sig')); pkg['version']=version
pkg.setdefault('dependencies',{})['highcharts']='12.4.0'
pkg.setdefault('build',{})['files']=['src/**/*','assets/**/*','package.json']
extra=pkg['build'].get('extraResources') or []
extra=[x for x in extra if not(isinstance(x,dict) and x.get('to') in {'login-left.jpg','highcharts'})]
extra.append({'from':'resources/login-left.jpg','to':'login-left.jpg'})
extra.append({'from':'node_modules/highcharts','to':'highcharts'})
pkg['build']['extraResources']=extra
pkg_path.write_text(json.dumps(pkg,ensure_ascii=False,indent=2),encoding='utf-8')

if 'id="loginPosterImage"' not in renderer: raise RuntimeError('loginPosterImage missing')
if "remoteLoginPoster?.()" not in renderer: raise RuntimeError('remoteLoginPoster renderer binding missing')
if 'img.classList.add(\'ready\')' not in renderer: raise RuntimeError('poster ready-state binding missing')
if "chartAssetsBase?.()" not in renderer: raise RuntimeError('local chart asset loader missing')
if "app:chart-assets-base" not in main: raise RuntimeError('chart asset IPC missing')
if "chartAssetsBase:" not in preload: raise RuntimeError('chart asset preload bridge missing')
if {'from':'node_modules/highcharts','to':'highcharts'} not in pkg['build']['extraResources']: raise RuntimeError('Highcharts extraResource missing')
print(f'VELTRO {version} local Highcharts + remote-first poster patch verified: {actual_sha256}')
