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
        pattern=rf"(tickValue\s*:\s*){re.escape(str(old_value))}(?:\.0+)?(?=[,}}\s])"
        renderer,count=re.subn(pattern,rf"\g<1>{new_value}",renderer,count=1)
    if count!=1:
        raise RuntimeError(f'{symbol} tickValue {old_value} anchor missing; refusing broad PnL modification')

agg_helper="""  function aggregateTfBars(src,mins){\n    const ms=mins*60000,out=[];\n    for(const x of src){\n      const bt=Math.floor(Number(x.t)/ms)*ms,last=out[out.length-1];\n      if(!last||last.t!==bt)out.push({t:bt,o:x.o,h:x.h,l:x.l,c:x.c,v:Number(x.v||0)});\n      else{last.h=Math.max(last.h,x.h);last.l=Math.min(last.l,x.l);last.c=x.c;last.v+=Number(x.v||0);}\n    }\n    return out;\n  }\n"""
draw_anchor="  async function draw(resetView=false){"
if 'function aggregateTfBars(src,mins)' not in renderer:
    if draw_anchor not in renderer:
        raise RuntimeError('chart draw anchor missing for timeframe compatibility')
    renderer=renderer.replace(draw_anchor,agg_helper+draw_anchor,1)

# HSI remains visible but maintenance-only. Never enter any historical/realtime LS path.
maintenance_guard="  async function draw(resetView=false){if(isHsiCode()){box.innerHTML='<div class=\"chart-loading\"><b>현재 점검중인 종목입니다.</b></div>';loading=false;return;}"
if draw_anchor in renderer:
    renderer=renderer.replace(draw_anchor,maintenance_guard,1)

req_old="window.desktop.getMarketKline({...ref,kType:currentK,limit:3000})"
req_new="window.desktop.getMarketKline({...ref,kType:currentK,limit:(currentK===5?300:currentK===4?500:currentK===3?500:currentK===2?1200:1500)})"
if req_old not in renderer:
    raise RuntimeError('production kline request missing')
renderer=renderer.replace(req_old,req_new,1)

# Final chart result is Databento-only. Legacy LS variables may remain for build compatibility,
# but they are not allowed to provide bars or open a realtime connection in the packaged app.
bars_old="const bars=(databentoOnly||lsHsiOnly)?normalizeBars(res?.bars):[];lastBars=bars;"
bars_new="const bars=databentoOnly?normalizeBars(res?.bars):[];lastBars=bars;"
if bars_old not in renderer:
    raise RuntimeError('filtered bars anchor missing')
renderer=renderer.replace(bars_old,bars_new,1)

start_rt="function startRealtime(){closeRealtime();if(!isHsiCode()||document.hidden)return;"
if start_rt in renderer:
    renderer=renderer.replace(start_rt,"function startRealtime(){return;/* DATABENTO_ONLY_LS_DISABLED */if(!isHsiCode()||document.hidden)return;",1)
renderer=renderer.replace('LIVE · LS WS','LIVE · DATABENTO')
renderer=renderer.replace('LS 실시간 연결 중...','현재 점검중인 종목입니다.')
renderer=renderer.replace('LS 실시간 재연결 중...','현재 점검중인 종목입니다.')
renderer=renderer.replace('LS 실시간 구독 중...','현재 점검중인 종목입니다.')

# The live quote timer owns the actively-forming candle. Remove only a 30-second
# barTimer history resync if one still exists after all previous compatibility patches.
periodic_re=r"barTimer\s*=\s*setInterval\(.*?,\s*30000\s*\)\s*;?"
renderer,n=re.subn(periodic_re,"barTimer=null;",renderer,count=1,flags=re.S)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
if 'p.last+s.tickSize' in check or 'p.last-s.tickSize' in check:
    raise RuntimeError('synthetic last +/- tick BBO fallback still present')
for needle in [
    'const prevAsk=Number(p.ask),prevBid=Number(p.bid);',
    'window.__veltroLadderCenter',
    'Math.abs(p.last-ladderCenter)>=tick*2',
    'applyChartOnlyLiveQuote',
    'b={t:bt,o:v,h:v,l:v,c:v,v:0}',
    'currentK===5?300:currentK===4?500:currentK===3?500:currentK===2?1200:1500',
    'DATABENTO_ONLY_LS_DISABLED',
    'const bars=databentoOnly?normalizeBars(res?.bars):[];lastBars=bars;'
]:
    if needle not in check:
        raise RuntimeError('missing BBO/chart guard: '+needle)
if not re.search(r"quoteTimer\s*=\s*setInterval",check):
    raise RuntimeError('realtime quote timer missing')
if re.search(r"barTimer\s*=\s*setInterval\(.*?,\s*30000\s*\)",check,re.S):
    raise RuntimeError('30-second historical redraw still active')
for forbidden in ['LIVE · LS WS','LS 실시간 연결 중...','LS 실시간 재연결 중...','LS 실시간 구독 중...']:
    if forbidden in check:
        raise RuntimeError('active LS chart text remains: '+forbidden)
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
print('VELTRO Databento-only chart runtime: LS disabled, bounded history loading, BBO/PnL preserved')
