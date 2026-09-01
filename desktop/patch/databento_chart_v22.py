import pathlib

root = pathlib.Path.cwd()
renderer_path = root / 'desktop' / 'build' / 'src' / 'renderer.js'
renderer = renderer_path.read_text(encoding='utf-8')

# Restore the original authenticated market-data kline path. The old v22 test URL
# was a temporary validation endpoint with a fixed 2026-08-29 end time and must
# never be used by the production HTS chart.
old_call = "const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),window.desktop.getMarketKline({...ref,kType:currentK,limit:500}).catch(()=>null)]);"
new_call = "const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),window.desktop.getMarketKline({...ref,kType:currentK,limit:3000}).catch(()=>null)]);"
if old_call not in renderer:
    raise RuntimeError('Databento chart call anchor missing')
renderer = renderer.replace(old_call, new_call, 1)

old_filter = "const source=String(res?.source||'').toLowerCase();const lsOnly=!!res?.ok&&res?.provider==='ls'&&source!=='live_samples'&&source!=='sampled'&&source!=='fallback'&&source!=='none';const bars=lsOnly?normalizeBars(res?.bars):[];lastBars=bars;"
new_filter = "const databentoOnly=!!res?.ok&&String(res?.provider||'').toLowerCase()==='databento'&&Array.isArray(res?.bars);const bars=databentoOnly?normalizeBars(res?.bars):[];lastBars=bars;"
if old_filter not in renderer:
    raise RuntimeError('LS-only filter anchor missing')
renderer = renderer.replace(old_filter, new_filter, 1)

renderer = renderer.replace('LS증권 분봉을 불러오는 중...', 'Databento 과거봉을 불러오는 중...', 1)
renderer = renderer.replace("<b>LS증권 원본 과거봉을 불러오지 못했습니다.</b><br>샘플·누적·대체 시세는 표시하지 않습니다.", "<b>Databento 과거봉을 불러오지 못했습니다.</b><br>GLBX.MDP3 · OHLCV-1m 응답을 확인 중입니다.", 1)
renderer = renderer.replace("foot.textContent=`${currentCode} · LS 원본 · 과거봉 없음`;", "foot.textContent=`${currentCode} · Databento · 과거봉 없음`;", 1)
renderer = renderer.replace("conn.textContent='LIVE · LS';", "conn.textContent='HISTORICAL · DATABENTO';", 1)
renderer = renderer.replace("foot.textContent=`${currentCode} · LS 원본 · ${bars.length}봉`;", "foot.textContent=`${currentCode} · Databento · ${bars.length}봉`;", 1)

# IMPORTANT: preserve the chart's existing quoteTimer. Production live updates must
# not be disabled here.
renderer_path.write_text(renderer, encoding='utf-8')

check = renderer_path.read_text(encoding='utf-8')
for needle in ['window.desktop.getMarketKline({...ref,kType:currentK,limit:3000})', "provider||'').toLowerCase()==='databento'", 'HISTORICAL · DATABENTO']:
    if needle not in check:
        raise RuntimeError('missing production Databento chart patch: ' + needle)
if 'databento-kline-test' in check:
    raise RuntimeError('obsolete databento-kline-test still present')
if 'quoteTimer=null' in check:
    raise RuntimeError('chart quote timer was disabled')
print('VELTRO production Databento chart path restored; live quote timer preserved')
