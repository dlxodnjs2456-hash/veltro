import pathlib

root=pathlib.Path.cwd(); renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

anchor="let prefs=chartIndicatorPrefs();"
insert="let prefs=chartIndicatorPrefs();\n  const chartCache=window.__veltroChartCache||(window.__veltroChartCache=new Map());"
if anchor not in renderer: raise RuntimeError('chart prefs anchor missing')
renderer=renderer.replace(anchor,insert,1)

old="const chartReq=lsHsi?window.desktop.getHsiKline({symbol:String(currentCode||'HSIQ26'),kType:currentK,limit:3000}).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));"
new="const chartCacheKey=(lsHsi?'ls:':'db:')+String(currentCode)+':'+String(currentK);const cachedChart=chartCache.get(chartCacheKey);const loadChart=()=>lsHsi?window.desktop.getHsiKline({symbol:String(currentCode||'HSIQ26'),kType:currentK,limit:3000}).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));const chartReq=(cachedChart&&Date.now()-cachedChart.at<60000)?Promise.resolve(cachedChart.data):loadChart().then(data=>{if(data?.ok)chartCache.set(chartCacheKey,{at:Date.now(),data});return data;});"
if old not in renderer: raise RuntimeError('v28 chart request anchor missing')
renderer=renderer.replace(old,new,1)

old_reload="w.querySelector('#chartReload').onclick=()=>draw(true);"
new_reload="w.querySelector('#chartReload').onclick=()=>{chartCache.clear();draw(true);};"
if old_reload not in renderer: raise RuntimeError('chart reload anchor missing')
renderer=renderer.replace(old_reload,new_reload,1)

old_timer="barTimer=setInterval(()=>{if(!document.hidden)draw(false)},30000);"
new_timer="barTimer=setInterval(()=>{if(!document.hidden)draw(false)},120000);"
if old_timer not in renderer: raise RuntimeError('bar timer anchor missing')
renderer=renderer.replace(old_timer,new_timer,1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ['__veltroChartCache','chartCacheKey','Date.now()-cachedChart.at<60000','120000','chartCache.clear()']:
    if needle not in check: raise RuntimeError('missing perf v29 patch: '+needle)
print('VELTRO v1.0.29 chart request caching and redraw throttling applied')
