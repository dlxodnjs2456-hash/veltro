import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old_call="const dbMap={NQ:'NQ.n.0',NQU26:'NQ.n.0',ES:'ES.n.0',ESU26:'ES.n.0',CL:'CL.n.0',CLV26:'CL.n.0',GC:'GC.n.0',GCZ26:'GC.n.0',SI:'SI.n.0',SIU26:'SI.n.0','6J':'6J.n.0','6JU26':'6J.n.0'};const dbSymbol=dbMap[currentCode]||null;const dbUrl=dbSymbol?'https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/databento-kline-test?test_token=veltro-databento-chart-check-20260831&symbol='+encodeURIComponent(dbSymbol)+'&kType='+encodeURIComponent(String(currentK))+'&limit=3000':null;const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'databento_symbol_not_supported'})]);"
new_call="const dbMap={NQ:'NQ.n.0',NQU26:'NQ.n.0',ES:'ES.n.0',ESU26:'ES.n.0',CL:'CL.n.0',CLV26:'CL.n.0',GC:'GC.n.0',GCZ26:'GC.n.0',SI:'SI.n.0',SIU26:'SI.n.0','6J':'6J.n.0','6JU26':'6J.n.0'};const lsHsi=['HSI','HSIQ26','HSIU26'].includes(String(currentCode).toUpperCase());const dbSymbol=dbMap[currentCode]||null;const dbUrl=dbSymbol?'https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/databento-kline-test?test_token=veltro-databento-chart-check-20260831&symbol='+encodeURIComponent(dbSymbol)+'&kType='+encodeURIComponent(String(currentK))+'&limit=3000':null;const chartReq=lsHsi?window.desktop.getMarketKline({...ref,kType:currentK,limit:500}).catch(()=>null):(dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'chart_symbol_not_supported'}));const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),chartReq]);"
if old_call not in renderer:
    raise RuntimeError('Databento v23 call anchor missing')
renderer=renderer.replace(old_call,new_call,1)

old_filter="const databentoOnly=!!res?.ok&&res?.provider==='databento'&&Array.isArray(res?.bars);const bars=databentoOnly?normalizeBars(res?.bars):[];lastBars=bars;"
new_filter="const source=String(res?.source||'').toLowerCase();const databentoOnly=!!res?.ok&&res?.provider==='databento'&&Array.isArray(res?.bars);const lsHsiOnly=lsHsi&&!!res?.ok&&res?.provider==='ls'&&Array.isArray(res?.bars)&&source!=='live_samples'&&source!=='sampled'&&source!=='fallback'&&source!=='none';const bars=(databentoOnly||lsHsiOnly)?normalizeBars(res?.bars):[];lastBars=bars;"
if old_filter not in renderer:
    raise RuntimeError('Databento v22 filter anchor missing')
renderer=renderer.replace(old_filter,new_filter,1)

renderer=renderer.replace("conn.textContent='HISTORICAL · DATABENTO';", "conn.textContent=lsHsi?'LIVE · LS':'HISTORICAL · DATABENTO';", 1)
renderer=renderer.replace("foot.textContent=`${currentCode} · Databento · ${bars.length}봉`;", "foot.textContent=lsHsi?`${currentCode} · LS · ${bars.length}봉`:`${currentCode} · Databento · ${bars.length}봉`;", 1)
renderer=renderer.replace("foot.textContent=`${currentCode} · Databento · 과거봉 없음`;", "foot.textContent=lsHsi?`${currentCode} · LS · 과거봉 없음`:`${currentCode} · Databento · 과거봉 없음`;", 1)
renderer=renderer.replace("<b>Databento 과거봉을 불러오지 못했습니다.</b><br>GLBX.MDP3 · OHLCV-1m 응답을 확인 중입니다.", "<b>과거봉을 불러오지 못했습니다.</b><br>선택 종목의 시세 공급원 응답을 확인 중입니다.", 1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ["['HSI','HSIQ26','HSIU26']", "lsHsiOnly", "LIVE · LS", "currentCode} · LS"]:
    if needle not in check:
        raise RuntimeError('missing HSI LS v25 patch: '+needle)
print('VELTRO v1.0.25 HSI LS chart routing patch applied')
