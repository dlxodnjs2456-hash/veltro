import pathlib

root = pathlib.Path.cwd()
renderer_path = root / 'desktop' / 'build' / 'src' / 'renderer.js'
renderer = renderer_path.read_text(encoding='utf-8')

old = "const dbMap={NQ:'NQ.n.0',ES:'ES.n.0',CL:'CL.n.0',GC:'GC.n.0',SI:'SI.n.0','6J':'6J.n.0'};const dbSymbol=dbMap[currentCode]||'NQ.n.0';const dbUrl='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/databento-kline-test?test_token=veltro-databento-chart-check-20260831&symbol='+encodeURIComponent(dbSymbol);const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null)]);"
new = "const dbMap={NQ:'NQ.n.0',NQU26:'NQ.n.0',ES:'ES.n.0',ESU26:'ES.n.0',CL:'CL.n.0',CLV26:'CL.n.0',GC:'GC.n.0',GCZ26:'GC.n.0',SI:'SI.n.0',SIU26:'SI.n.0','6J':'6J.n.0','6JU26':'6J.n.0'};const dbSymbol=dbMap[currentCode]||null;const dbUrl=dbSymbol?'https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/databento-kline-test?test_token=veltro-databento-chart-check-20260831&symbol='+encodeURIComponent(dbSymbol)+'&kType='+encodeURIComponent(String(currentK))+'&limit=3000':null;const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),dbUrl?fetch(dbUrl,{cache:'no-store'}).then(r=>r.json()).catch(()=>null):Promise.resolve({ok:false,error:'databento_symbol_not_supported'})]);"
if old not in renderer:
    raise RuntimeError('v22 Databento call anchor missing')
renderer = renderer.replace(old, new, 1)

renderer = renderer.replace("renderer = renderer.replace(\"quoteTimer=setInterval(()=>{if(!document.hidden)refreshQuote()},2500);\", \"quoteTimer=null;\", 1)", "renderer = renderer", 0)
renderer_path.write_text(renderer, encoding='utf-8')

check = renderer_path.read_text(encoding='utf-8')
for needle in ["NQU26:'NQ.n.0'", "ESU26:'ES.n.0'", "CLV26:'CL.n.0'", "GCZ26:'GC.n.0'", "SIU26:'SI.n.0'", "'6JU26':'6J.n.0'", "&kType=", "&limit=3000"]:
    if needle not in check:
        raise RuntimeError('missing Databento v23 patch: ' + needle)
print('VELTRO Databento multi-symbol/timeframe chart v23 patch applied')
