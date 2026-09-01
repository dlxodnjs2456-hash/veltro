import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

anchor="function renderTrade(w) {"
replacement="function renderTrade(w) {\n  window.__veltroTradeWindow=w;\n  window.__veltroLadderCenter=Number(state.prices[state.selected]?.last||0);"
if anchor not in renderer:
    raise RuntimeError('renderTrade anchor missing')
renderer=renderer.replace(anchor,replacement,1)

live_anchor="function updateTradeLiveDom(){\n  if(state.view!=='trade')return;const s=state.symbols[state.selected],p=state.prices[state.selected];if(!s||!p)return;"
live_replacement="function updateTradeLiveDom(){\n  if(state.view!=='trade')return;const s=state.symbols[state.selected],p=state.prices[state.selected];if(!s||!p)return;\n  const ladderCenter=Number(window.__veltroLadderCenter||0),tick=Number(s.tickSize||0);\n  if(window.__veltroTradeWindow&&Number.isFinite(p.last)&&p.last>0&&tick>0&&(!ladderCenter||Math.abs(p.last-ladderCenter)>=tick*2)){\n    window.__veltroLadderCenter=Number(p.last);\n    renderTrade(window.__veltroTradeWindow);\n    return;\n  }"
if live_anchor not in renderer:
    raise RuntimeError('updateTradeLiveDom anchor missing')
renderer=renderer.replace(live_anchor,live_replacement,1)

renderer_path.write_text(renderer,encoding='utf-8')
final=renderer_path.read_text(encoding='utf-8')
if 'window.__veltroLadderCenter' not in final or 'Math.abs(p.last-ladderCenter)>=tick*2' not in final:
    raise RuntimeError('ladder recenter patch verification failed')
print('VELTRO ladder auto-recenter patch verified')
