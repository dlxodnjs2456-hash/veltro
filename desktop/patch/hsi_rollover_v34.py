import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old="const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),chartReq]);"
new="const [qr,res]=await Promise.all([lsHsi?Promise.resolve(null):window.desktop.getMarketQuote(ref).catch(()=>null),chartReq]);"
if old not in renderer:
    raise RuntimeError('HSI quote fallback anchor missing')
renderer=renderer.replace(old,new,1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
if "lsHsi?Promise.resolve(null):window.desktop.getMarketQuote" not in check:
    raise RuntimeError('HSI stale quote guard missing')
if 'hsi-kline-api' not in check or 'hsi-realtime-api' not in check:
    raise RuntimeError('HSI LS chart/realtime routes missing')
print('VELTRO v1.0.34 HSI rollover stale-quote guard applied')
