import pathlib

root=pathlib.Path.cwd(); build=root/'desktop'/'build'
renderer_path=build/'src'/'renderer.js'; main_path=build/'src'/'main.js'; preload_path=build/'src'/'preload.js'
renderer=renderer_path.read_text(encoding='utf-8')
main=main_path.read_text(encoding='utf-8')
preload=preload_path.read_text(encoding='utf-8')

old="const hsiUrl='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/hsi-kline-api?token=veltro-hsi-kline-20260831&symbol=HSIU26&kType='+encodeURIComponent(String(currentK))+'&limit=3000';const chartReq=lsHsi?fetch(hsiUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));"
new="const chartReq=lsHsi?window.desktop.getHsiKline({symbol:String(currentCode||'HSIQ26'),kType:currentK,limit:3000}).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));"
if old not in renderer: raise RuntimeError('v27 HSI direct-fetch anchor missing')
renderer=renderer.replace(old,new,1)

handler_anchor="ipcMain.handle('app:quit',()=>app.quit());"
if handler_anchor not in main: raise RuntimeError('main ipc anchor missing')
if "ipcMain.handle('app:hsi-kline'" not in main:
    handler="""ipcMain.handle('app:hsi-kline',(_evt,args={})=>new Promise((resolve)=>{\n  const symbol=encodeURIComponent(String(args.symbol||'HSIQ26'));\n  const kType=encodeURIComponent(String(args.kType||1));\n  const limit=encodeURIComponent(String(Math.max(100,Math.min(3000,Number(args.limit)||3000))));\n  const path='/functions/v1/hsi-kline-api?token=veltro-hsi-kline-20260831&symbol='+symbol+'&kType='+kType+'&limit='+limit+'&ts='+Date.now();\n  const req=https.get({hostname:'mzjkvakigwtlibwlslhq.supabase.co',path,headers:{'Cache-Control':'no-cache','User-Agent':'VELTRO-HTS'}},(res)=>{\n    let body='';res.setEncoding('utf8');res.on('data',c=>{body+=c;if(body.length>6000000)req.destroy();});\n    res.on('end',()=>{try{resolve(JSON.parse(body))}catch{resolve({ok:false,error:'hsi_kline_invalid_json',status:res.statusCode})}});\n  });\n  req.setTimeout(20000,()=>{req.destroy();resolve({ok:false,error:'hsi_kline_timeout'})});\n  req.on('error',e=>resolve({ok:false,error:String(e?.message||e)}));\n}));"""
    main=main.replace(handler_anchor,handler_anchor+'\n'+handler,1)

quit_anchor="quit: () => ipcRenderer.invoke('app:quit'),"
if quit_anchor not in preload: raise RuntimeError('preload anchor missing')
if "getHsiKline:" not in preload:
    preload=preload.replace(quit_anchor,quit_anchor+"\n  getHsiKline: (args) => ipcRenderer.invoke('app:hsi-kline', args),",1)

prefs_anchor="let prefs=chartIndicatorPrefs();"
if prefs_anchor not in renderer: raise RuntimeError('chart prefs anchor missing')
renderer=renderer.replace(prefs_anchor,prefs_anchor+"\n  const chartCache=window.__veltroChartCache||(window.__veltroChartCache=new Map());",1)

req_old="const chartReq=lsHsi?window.desktop.getHsiKline({symbol:String(currentCode||'HSIQ26'),kType:currentK,limit:3000}).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));"
req_new="const chartCacheKey=(lsHsi?'ls:':'db:')+String(currentCode)+':'+String(currentK);const cachedChart=chartCache.get(chartCacheKey);const loadChart=()=>lsHsi?window.desktop.getHsiKline({symbol:String(currentCode||'HSIQ26'),kType:currentK,limit:3000}).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));const chartReq=(cachedChart&&Date.now()-cachedChart.at<60000)?Promise.resolve(cachedChart.data):loadChart().then(data=>{if(data?.ok)chartCache.set(chartCacheKey,{at:Date.now(),data});return data;});"
if req_old not in renderer: raise RuntimeError('chart request cache anchor missing')
renderer=renderer.replace(req_old,req_new,1)

reload_old="w.querySelector('#chartReload').onclick=()=>draw(true);"
if reload_old not in renderer: raise RuntimeError('chart reload anchor missing')
renderer=renderer.replace(reload_old,"w.querySelector('#chartReload').onclick=()=>{chartCache.clear();draw(true);};",1)

timer_old="barTimer=setInterval(()=>{if(!document.hidden)draw(false)},30000);"
if timer_old not in renderer: raise RuntimeError('bar timer anchor missing')
renderer=renderer.replace(timer_old,"barTimer=setInterval(()=>{if(!document.hidden)draw(false)},120000);",1)

renderer_path.write_text(renderer,encoding='utf-8'); main_path.write_text(main,encoding='utf-8'); preload_path.write_text(preload,encoding='utf-8')
for path,needle in [(renderer_path,'window.desktop.getHsiKline'),(main_path,"ipcMain.handle('app:hsi-kline'"),(preload_path,'getHsiKline:'),(renderer_path,'__veltroChartCache'),(renderer_path,'120000')]:
    if needle not in path.read_text(encoding='utf-8'): raise RuntimeError('missing v28/v29 performance patch: '+needle)
print('VELTRO HSI IPC + chart caching/redraw optimization applied')
