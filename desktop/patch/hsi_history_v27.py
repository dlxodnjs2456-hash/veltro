import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old="const chartReq=lsHsi?window.desktop.getMarketKline({...ref,kType:currentK,limit:500}).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));"
new="const hsiUrl='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/hsi-kline-api?token=veltro-hsi-kline-20260831&symbol=HSIU26&kType='+encodeURIComponent(String(currentK))+'&limit=3000';const chartReq=lsHsi?fetch(hsiUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));"
if old not in renderer:
    raise RuntimeError('HSI v25 chart request anchor missing')
renderer=renderer.replace(old,new,1)
renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ['hsi-kline-api','limit=3000','symbol=HSIU26']:
    if needle not in check:
        raise RuntimeError('missing HSI history v27 patch: '+needle)
print('VELTRO v1.0.27 HSI 3000-bar LS history patch applied')
