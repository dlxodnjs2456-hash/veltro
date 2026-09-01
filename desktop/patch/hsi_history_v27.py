import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old="const chartReq=lsHsi?window.desktop.getMarketKline({...ref,kType:currentK,limit:500}).catch(()=>null):window.desktop.getMarketKline({...ref,kType:currentK,limit:3000}).catch(()=>null);"
new="const hsiUrl='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/hsi-kline-api?token=veltro-hsi-kline-20260831&symbol=HSIU26&kType='+encodeURIComponent(String(currentK))+'&limit=3000';const chartReq=lsHsi?fetch(hsiUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):window.desktop.getMarketKline({...ref,kType:currentK,limit:3000}).catch(()=>null);"
if old not in renderer:
    raise RuntimeError('HSI production-compatible chart request anchor missing')
renderer=renderer.replace(old,new,1)
renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ['hsi-kline-api','window.desktop.getMarketKline({...ref,kType:currentK,limit:3000})']:
    if needle not in check:
        raise RuntimeError('missing isolated HSI history patch: '+needle)
if 'databento-kline-test' in check:
    raise RuntimeError('obsolete test endpoint reintroduced')
print('VELTRO HSI history isolated; production Databento route preserved')
