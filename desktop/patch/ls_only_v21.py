import pathlib

root = pathlib.Path.cwd()
renderer_path = root / 'desktop' / 'build' / 'src' / 'renderer.js'
renderer = renderer_path.read_text(encoding='utf-8')

old = "const bars=normalizeBars(res?.bars);lastBars=bars;"
new = "const source=String(res?.source||'').toLowerCase();const lsOnly=!!res?.ok&&res?.provider==='ls'&&source!=='live_samples'&&source!=='sampled'&&source!=='fallback'&&source!=='none';const bars=lsOnly?normalizeBars(res?.bars):[];lastBars=bars;"
if old not in renderer:
    raise RuntimeError('LS-only chart source anchor missing')
renderer = renderer.replace(old, new, 1)

renderer = renderer.replace("window.desktop.getMarketKline({...ref,kType:currentK,limit:300})", "window.desktop.getMarketKline({...ref,kType:currentK,limit:500})", 1)
renderer = renderer.replace("<b>LS증권 분봉 데이터가 없습니다.</b><br>종목코드 또는 분봉 응답을 확인 중입니다.", "<b>LS증권 원본 과거봉을 불러오지 못했습니다.</b><br>샘플·누적·대체 시세는 표시하지 않습니다.", 1)
renderer = renderer.replace("foot.textContent=`${currentCode} · LS`;", "foot.textContent=`${currentCode} · LS 원본 · 과거봉 없음`;", 1)
renderer = renderer.replace("foot.textContent=`${currentCode} · LS · ${bars.length}봉`;", "foot.textContent=`${currentCode} · LS 원본 · ${bars.length}봉`;", 1)
renderer = renderer.replace("conn.textContent='LIVE · LS';", "conn.textContent='LIVE · LS';", 1)

# The quote-driven update remains enabled because it is also LS data. No local/sample candle is created.
renderer_path.write_text(renderer, encoding='utf-8')

check = renderer_path.read_text(encoding='utf-8')
for needle in ["limit:500", "source!=='live_samples'", "LS증권 원본 과거봉", "LS 원본"]:
    if needle not in check:
        raise RuntimeError('missing LS-only chart patch: ' + needle)
print('VELTRO LS-only chart v21 patch applied')
