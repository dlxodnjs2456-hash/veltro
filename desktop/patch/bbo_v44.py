import pathlib,re

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old="""  p.ask=Number.isFinite(bestAsk)&&bestAsk>0?roundToTick(bestAsk,s):roundToTick(p.last+s.tickSize,s);\n  p.bid=Number.isFinite(bestBid)&&bestBid>0?roundToTick(bestBid,s):roundToTick(p.last-s.tickSize,s);"""
new="""  const prevAsk=Number(p.ask),prevBid=Number(p.bid);\n  p.ask=Number.isFinite(bestAsk)&&bestAsk>0?roundToTick(bestAsk,s):(Number.isFinite(prevAsk)&&prevAsk>0?roundToTick(prevAsk,s):p.last);\n  p.bid=Number.isFinite(bestBid)&&bestBid>0?roundToTick(bestBid,s):(Number.isFinite(prevBid)&&prevBid>0?roundToTick(prevBid,s):p.last);"""
if old not in renderer:
    raise RuntimeError('v44 synthetic BBO fallback anchor missing')
renderer=renderer.replace(old,new,1)

anchor="function renderTrade(w) {"
replacement="function renderTrade(w) {\n  window.__veltroTradeWindow=w;\n  window.__veltroLadderCenter=Number(state.prices[state.selected]?.last||0);"
if anchor not in renderer:
    raise RuntimeError('renderTrade anchor missing for ladder recenter')
renderer=renderer.replace(anchor,replacement,1)

live_anchor="function updateTradeLiveDom(){\n  if(state.view!=='trade')return;const s=state.symbols[state.selected],p=state.prices[state.selected];if(!s||!p)return;"
live_replacement="function updateTradeLiveDom(){\n  if(state.view!=='trade')return;const s=state.symbols[state.selected],p=state.prices[state.selected];if(!s||!p)return;\n  const ladderCenter=Number(window.__veltroLadderCenter||0),tick=Number(s.tickSize||0);\n  if(window.__veltroTradeWindow&&Number.isFinite(p.last)&&p.last>0&&tick>0&&(!ladderCenter||Math.abs(p.last-ladderCenter)>=tick*2)){\n    window.__veltroLadderCenter=Number(p.last);\n    renderTrade(window.__veltroTradeWindow);\n    return;\n  }"
if live_anchor not in renderer:
    raise RuntimeError('updateTradeLiveDom anchor missing for ladder recenter')
renderer=renderer.replace(live_anchor,live_replacement,1)

# Contract PnL benchmarks supplied from the reference HTS.
# Only tickValue is changed. Market prices, order behavior, margin, position data,
# and every non-PnL trading semantic remain untouched.
benchmarks={
    'NQU26':(6290,6847.5),
    'CLV26':(13840,13695),
    'GCZ26':(13840,13695),
    'SIU26':(34600,34237.5),
    '6JU26':(8650,8559.4),
}
for symbol,(old_value,new_value) in benchmarks.items():
    pattern=rf"({re.escape(symbol)}[^\n\r]{{0,300}}?tickValue\s*:\s*){re.escape(str(old_value))}(?:\.0+)?(?=[,}}\s])"
    renderer,count=re.subn(pattern,rf"\g<1>{new_value}",renderer,count=1)
    if count!=1:
        # Safe fallback only when the old tick value is unique enough for the known build base.
        pattern=rf"(tickValue\s*:\s*){re.escape(str(old_value))}(?:\.0+)?(?=[,}}\s])"
        renderer,count=re.subn(pattern,rf"\g<1>{new_value}",renderer,count=1)
    if count!=1:
        raise RuntimeError(f'{symbol} tickValue {old_value} anchor missing; refusing broad PnL modification')

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
if 'p.last+s.tickSize' in check or 'p.last-s.tickSize' in check:
    raise RuntimeError('synthetic last +/- tick BBO fallback still present')
for needle in [
    'const prevAsk=Number(p.ask),prevBid=Number(p.bid);',
    '?roundToTick(bestAsk,s):',
    '?roundToTick(bestBid,s):',
    'window.__veltroLadderCenter',
    'Math.abs(p.last-ladderCenter)>=tick*2'
]:
    if needle not in check:
        raise RuntimeError('missing BBO/ladder guard: '+needle)
for expected in ['6847.5','13695','34237.5','8559.4']:
    if not re.search(rf"tickValue\s*:\s*{re.escape(expected)}(?=[,}}\s])",check):
        raise RuntimeError('contract PnL benchmark missing: '+expected)

checks=[
    ((29220.75-29225.00)/.25*6847.5*10,-1164075,'NQ'),
    ((87.88-87.92)/.01*13695*5,-273900,'CL'),
    ((4429.6-4429.8)/.1*13695*5,-136950,'GC'),
    ((65.610-65.65)/.005*34237.5*5,-1369500,'SI'),
    ((6255.5-6256)/.5*8559.4*5,-42797,'6J'),
]
for got,expected,name in checks:
    if round(got)!=expected:
        raise RuntimeError(f'{name} benchmark regression mismatch: {got} != {expected}')
print('VELTRO real BBO + supplied contract PnL benchmarks applied; received prices are not modified')
# v1.0.47 release trigger; no other runtime behavior changed.
