import pathlib,re

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old="""  p.ask=Number.isFinite(bestAsk)&&bestAsk>0?roundToTick(bestAsk,s):roundToTick(p.last+s.tickSize,s);\n  p.bid=Number.isFinite(bestBid)&&bestBid>0?roundToTick(bestBid,s):roundToTick(p.last-s.tickSize,s);"""
new="""  const prevAsk=Number(p.ask),prevBid=Number(p.bid);\n  p.ask=Number.isFinite(bestAsk)&&bestAsk>0?roundToTick(bestAsk,s):(Number.isFinite(prevAsk)&&prevAsk>0?roundToTick(prevAsk,s):p.last);\n  p.bid=Number.isFinite(bestBid)&&bestBid>0?roundToTick(bestBid,s):(Number.isFinite(prevBid)&&prevBid>0?roundToTick(prevBid,s):p.last);"""
if old not in renderer:
    raise RuntimeError('v44 synthetic BBO fallback anchor missing')
renderer=renderer.replace(old,new,1)

# Keep the original trade renderer intact, but remember its window and the price
# around which the ladder was rendered. If live price moves two ticks away,
# re-run the existing renderTrade function so its own original ladder builder
# recenters around the latest received market price. No market price is altered.
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

# NQ PnL benchmark from supplied reference:
# LONG 10 @ 29225.00, current 29220.75 => -1,164,075 KRW.
# This equals 6,847.5 KRW per 0.25-point tick, or 27,390 KRW per point/contract.
renderer,nq_count=re.subn(r"(NQU26[^\n\r]{0,260}?tickValue\s*:\s*)6290(?:\.0+)?",r"\g<1>6847.5",renderer,count=1)
if nq_count!=1:
    renderer,nq_count=re.subn(r"(tickValue\s*:\s*)6290(?:\.0+)?(?=[,}\s])",r"\g<1>6847.5",renderer,count=1)
if nq_count!=1:
    raise RuntimeError('NQ tickValue 6290 anchor missing; refusing broad PnL modification')

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
if not re.search(r"tickValue\s*:\s*6847\.5",check):
    raise RuntimeError('NQ PnL benchmark tick value missing')
pnl=(29220.75-29225.00)/0.25*6847.5*10
if round(pnl)!=-1164075:
    raise RuntimeError(f'NQ benchmark regression mismatch: {pnl}')
print('VELTRO real BBO + ladder recenter + NQ PnL benchmark applied; received prices are not modified')
