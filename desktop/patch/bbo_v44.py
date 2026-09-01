import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old="""  p.ask=Number.isFinite(bestAsk)&&bestAsk>0?roundToTick(bestAsk,s):roundToTick(p.last+s.tickSize,s);\n  p.bid=Number.isFinite(bestBid)&&bestBid>0?roundToTick(bestBid,s):roundToTick(p.last-s.tickSize,s);"""
new="""  const prevAsk=Number(p.ask),prevBid=Number(p.bid);\n  p.ask=Number.isFinite(bestAsk)&&bestAsk>0?roundToTick(bestAsk,s):(Number.isFinite(prevAsk)&&prevAsk>0?roundToTick(prevAsk,s):p.last);\n  p.bid=Number.isFinite(bestBid)&&bestBid>0?roundToTick(bestBid,s):(Number.isFinite(prevBid)&&prevBid>0?roundToTick(prevBid,s):p.last);"""
if old not in renderer:
    raise RuntimeError('v44 synthetic BBO fallback anchor missing')
renderer=renderer.replace(old,new,1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
if 'p.last+s.tickSize' in check or 'p.last-s.tickSize' in check:
    raise RuntimeError('synthetic last +/- tick BBO fallback still present')
for needle in ['const prevAsk=Number(p.ask),prevBid=Number(p.bid);','?roundToTick(bestAsk,s):','?roundToTick(bestBid,s):']:
    if needle not in check:
        raise RuntimeError('missing v44 real BBO guard: '+needle)
print('VELTRO v1.0.44 real BBO guard applied; synthetic last +/- tick fallback removed')
