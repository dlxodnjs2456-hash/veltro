import pathlib

root = pathlib.Path.cwd()
renderer_path = root / 'desktop' / 'build' / 'src' / 'renderer.js'
renderer = renderer_path.read_text(encoding='utf-8')

old_call = "const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),window.desktop.getMarketKline({...ref,kType:currentK,limit:500}).catch(()=>null)]);"
new_call = "const dbMap={NQ:'NQ.n.0',ES:'ES.n.0',CL:'CL.n.0',GC:'GC.n.0',SI:'SI.n.0','6J':'6J.n.0'};const dbSymbol=dbMap[currentCode]||'NQ.n.0';const dbUrl='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/databento-kline-test?test_token=veltro-databento-chart-check-20260831&symbol='+encodeURIComponent(dbSymbol);const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null)]);"
if old_call not in renderer:
    raise RuntimeError('Databento chart call anchor missing')
renderer = renderer.replace(old_call, new_call, 1)

old_filter = "const source=String(res?.source||'').toLowerCase();const lsOnly=!!res?.ok&&res?.provider==='ls'&&source!=='live_samples'&&source!=='sampled'&&source!=='fallback'&&source!=='none';const bars=lsOnly?normalizeBars(res?.bars):[];lastBars=bars;"
new_filter = "const databentoOnly=!!res?.ok&&res?.provider==='databento'&&Array.isArray(res?.bars);const bars=databentoOnly?normalizeBars(res?.bars):[];lastBars=bars;"
if old_filter not in renderer:
    raise RuntimeError('LS-only filter anchor missing')
renderer = renderer.replace(old_filter, new_filter, 1)

renderer = renderer.replace('LS증권 분봉을 불러오는 중...', 'Databento NQ 과거봉을 불러오는 중...', 1)
renderer = renderer.replace("<b>LS증권 원본 과거봉을 불러오지 못했습니다.</b><br>샘플·누적·대체 시세는 표시하지 않습니다.", "<b>Databento 과거봉을 불러오지 못했습니다.</b><br>GLBX.MDP3 · OHLCV-1m 응답을 확인 중입니다.", 1)
renderer = renderer.replace("foot.textContent=`${currentCode} · LS 원본 · 과거봉 없음`;", "foot.textContent=`${currentCode} · Databento · 과거봉 없음`;", 1)
renderer = renderer.replace("conn.textContent='LIVE · LS';", "conn.textContent='HISTORICAL · DATABENTO';", 1)
renderer = renderer.replace("foot.textContent=`${currentCode} · LS 원본 · ${bars.length}봉`;", "foot.textContent=`${currentCode} · Databento · ${bars.length}봉`;", 1)
renderer = renderer.replace("quoteTimer=setInterval(()=>{if(!document.hidden)refreshQuote()},2500);", "quoteTimer=null;", 1)

renderer_path.write_text(renderer, encoding='utf-8')

check = renderer_path.read_text(encoding='utf-8')
for needle in ['databento-kline-test', "provider==='databento'", 'HISTORICAL · DATABENTO', 'Databento · ${bars.length}봉']:
    if needle not in check:
        raise RuntimeError('missing Databento chart patch: ' + needle)
print('VELTRO Databento historical chart v22 patch applied')
