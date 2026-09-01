import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old_call="const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),window.desktop.getMarketKline({...ref,kType:currentK,limit:3000}).catch(()=>null)]);"
new_call="const lsHsi=['HSI','HSIQ26','HSIU26'].includes(String(currentCode).toUpperCase());const chartReq=lsHsi?window.desktop.getMarketKline({...ref,kType:currentK,limit:500}).catch(()=>null):window.desktop.getMarketKline({...ref,kType:currentK,limit:3000}).catch(()=>null);const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),chartReq]);"
if old_call not in renderer:
    raise RuntimeError('production Databento chart call anchor missing')
renderer=renderer.replace(old_call,new_call,1)

old_filter="const databentoOnly=!!res?.ok&&String(res?.provider||'').toLowerCase()==='databento'&&Array.isArray(res?.bars);const bars=databentoOnly?normalizeBars(res?.bars):[];lastBars=bars;"
new_filter="const source=String(res?.source||'').toLowerCase();const databentoOnly=!lsHsi&&!!res?.ok&&String(res?.provider||'').toLowerCase()==='databento'&&Array.isArray(res?.bars);const lsHsiOnly=lsHsi&&!!res?.ok&&String(res?.provider||'').toLowerCase()==='ls'&&Array.isArray(res?.bars)&&source!=='live_samples'&&source!=='sampled'&&source!=='fallback'&&source!=='none';const bars=(databentoOnly||lsHsiOnly)?normalizeBars(res?.bars):[];lastBars=bars;"
if old_filter not in renderer:
    raise RuntimeError('production Databento filter anchor missing')
renderer=renderer.replace(old_filter,new_filter,1)

renderer=renderer.replace("conn.textContent='HISTORICAL · DATABENTO';", "conn.textContent=lsHsi?'LIVE · LS':'HISTORICAL · DATABENTO';", 1)
renderer=renderer.replace("foot.textContent=`${currentCode} · Databento · ${bars.length}봉`;", "foot.textContent=lsHsi?`${currentCode} · LS · ${bars.length}봉`:`${currentCode} · Databento · ${bars.length}봉`;", 1)
renderer=renderer.replace("foot.textContent=`${currentCode} · Databento · 과거봉 없음`;", "foot.textContent=lsHsi?`${currentCode} · LS · 과거봉 없음`:`${currentCode} · Databento · 과거봉 없음`;", 1)
renderer=renderer.replace("<b>Databento 과거봉을 불러오지 못했습니다.</b><br>GLBX.MDP3 · OHLCV-1m 응답을 확인 중입니다.", "<b>과거봉을 불러오지 못했습니다.</b><br>선택 종목의 시세 공급원 응답을 확인 중입니다.", 1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ["['HSI','HSIQ26','HSIU26']", 'window.desktop.getMarketKline({...ref,kType:currentK,limit:3000})', 'lsHsiOnly']:
    if needle not in check:
        raise RuntimeError('missing HSI production compatibility patch: '+needle)
if 'databento-kline-test' in check:
    raise RuntimeError('obsolete test endpoint reintroduced by HSI patch')
print('VELTRO HSI routing compatible with production Databento chart')
