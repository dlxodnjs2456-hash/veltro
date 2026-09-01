import pathlib

root = pathlib.Path.cwd()
renderer_path = root / 'desktop' / 'build' / 'src' / 'renderer.js'
renderer = renderer_path.read_text(encoding='utf-8')

required = "window.desktop.getMarketKline({...ref,kType:currentK,limit:3000})"
if required not in renderer:
    raise RuntimeError('production getMarketKline route missing before v23 verification')
if 'databento-kline-test' in renderer:
    raise RuntimeError('obsolete databento-kline-test route still present')
if 'quoteTimer=setInterval' not in renderer:
    raise RuntimeError('chart live quote timer missing')

renderer_path.write_text(renderer, encoding='utf-8')
print('VELTRO Databento v23: production kline routing and live timer preserved')
