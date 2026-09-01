import pathlib

root = pathlib.Path.cwd()
renderer_path = root / 'desktop' / 'build' / 'src' / 'renderer.js'
renderer = renderer_path.read_text(encoding='utf-8')

# v23 used to remap production HTS symbols to the obsolete public
# databento-kline-test endpoint. v22 now restores the normal authenticated
# getMarketKline path, so v23 must not replace it again.
required = "window.desktop.getMarketKline({...ref,kType:currentK,limit:3000})"
if required not in renderer:
    raise RuntimeError('production getMarketKline route missing before v23 verification')
if 'databento-kline-test' in renderer:
    raise RuntimeError('obsolete databento-kline-test route still present')
if 'quoteTimer=null' in renderer:
    raise RuntimeError('chart live quote timer unexpectedly disabled')

renderer_path.write_text(renderer, encoding='utf-8')
print('VELTRO Databento v23: production kline routing preserved without test-symbol remap')
