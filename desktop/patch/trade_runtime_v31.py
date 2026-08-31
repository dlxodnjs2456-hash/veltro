import pathlib,re

root=pathlib.Path.cwd(); renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

# 1) Complete trade-window market mappings. Chart routing had HSI separately, but the trade screen did not.
old_map="const marketSymbolMap={\n  NQU26:{region:'US',code:'NQ'}, ESU26:{region:'US',code:'ES'}, CLV26:{region:'US',code:'CL'}, GCZ26:{region:'US',code:'GC'}, SIU26:{region:'US',code:'SI'},\n};"
new_map="const marketSymbolMap={\n  NQU26:{region:'US',code:'NQ'}, ESU26:{region:'US',code:'ES'}, CLV26:{region:'US',code:'CL'}, GCZ26:{region:'US',code:'GC'}, SIU26:{region:'US',code:'SI'},\n  '6JU26':{region:'US',code:'6J'}, HSIQ26:{region:'HK',code:'HSI'}, HSIU26:{region:'HK',code:'HSI'},\n};"
if old_map not in renderer: raise RuntimeError('marketSymbolMap anchor missing')
renderer=renderer.replace(old_map,new_map,1)

# 2) Never silently drop the newest quote request while another request is in flight.
old_busy="let selectedMarketBusy=false;"
new_busy="let selectedMarketBusy=false,selectedMarketPending=false;"
if old_busy not in renderer: raise RuntimeError('selectedMarketBusy anchor missing')
renderer=renderer.replace(old_busy,new_busy,1)

# 3) Shared quote application. This also lets held, non-selected symbols update their PnL.
init_anchor="async function initMarketData(){\n  try{const c=await window.desktop.getMarketDataConfig();state.market.configured=Boolean(c?.configured);state.market.provider=c?.provider||'iTick';}catch(_e){}\n}\n"
helper=r'''async function initMarketData(){
  try{const c=await window.desktop.getMarketDataConfig();state.market.configured=Boolean(c?.configured);state.market.provider=c?.provider||'iTick';}catch(_e){}
}
function applyMarketQuoteToState(sym,r,withTape=false){
  if(!r?.ok||!r.quote||!state.symbols[sym]||!state.prices[sym]) return false;
  const q=r.quote,s=state.symbols[sym],p=state.prices[sym],prevLast=Number(p.last),prevMarketTs=Number(p.marketTs||0);
  const last=Number(q.ld);if(!Number.isFinite(last)||last<=0)return false;
  p.last=roundToTick(last,s);
  const bestAsk=Number(r.depth?.a?.[0]?.p),bestBid=Number(r.depth?.b?.[0]?.p);
  p.ask=Number.isFinite(bestAsk)&&bestAsk>0?roundToTick(bestAsk,s):roundToTick(p.last+s.tickSize,s);
  p.bid=Number.isFinite(bestBid)&&bestBid>0?roundToTick(bestBid,s):roundToTick(p.last-s.tickSize,s);
  p.open=Number(q.o)||p.open||s.base;p.prev=Number(q.p)||p.prev||s.base;p.high=Number(q.h)||p.high||p.last;p.low=Number(q.l)||p.low||p.last;p.volume=Number(q.v)||p.volume||0;p.change=Number(q.ch)||0;p.changePct=Number(q.chp)||0;p.marketTs=Number(q.t)||Date.now();
  if(withTape){
    const prevVolume=Number(state.market.volumeBySymbol[sym]||0),totalVolume=Number(q.v)||0;let tradeQty=prevVolume>0&&totalVolume>=prevVolume?totalVolume-prevVolume:0;if(!Number.isFinite(tradeQty)||tradeQty<0)tradeQty=0;state.market.volumeBySymbol[sym]=totalVolume;
    const tapeTime=new Date(p.marketTs).toLocaleTimeString('ko-KR',{hour12:false}),lastTape=state.tape[state.tape.length-1];
    if(!lastTape||lastTape.marketTs!==p.marketTs||Number(lastTape.rawPrice)!==p.last){state.tape.push({time:tapeTime,price:fmt(p.last,dec(s)),qty:tradeQty||1,marketTs:p.marketTs,rawPrice:p.last,symbol:sym});if(state.tape.length>120)state.tape=state.tape.slice(-120);}
  }
  state.market.liveSymbols[sym]=true;state.market.connected=true;state.market.error='';state.market.lastUpdate=Date.now();
  return p.last!==prevLast||p.marketTs!==prevMarketTs;
}
'''
if init_anchor not in renderer: raise RuntimeError('initMarketData anchor missing')
renderer=renderer.replace(init_anchor,helper,1)

# 4) Replace selected quote loop: queued latest refresh + lightweight live DOM update instead of rebuilding all controls.
start=renderer.find("async function refreshSelectedMarket(forceRender=true){")
end=renderer.find("\nasync function refreshOpenOrderMarkets(){",start)
if start<0 or end<0: raise RuntimeError('refreshSelectedMarket block missing')
new_refresh=r'''async function refreshSelectedMarket(forceRender=true){
  if(!state.market.configured||!state.loggedIn||state.view!=='trade')return false;
  const ref=marketRef();if(!ref)return false;
  if(selectedMarketBusy){selectedMarketPending=true;return false;}
  selectedMarketBusy=true;const selectedAtStart=state.selected;
  try{
    const r=await window.desktop.getMarketQuote(ref);if(!r?.ok||!r.quote)throw new Error(r?.error||'market_request_failed');
    const changed=applyMarketQuoteToState(selectedAtStart,r,true);
    if(forceRender&&changed&&selectedAtStart===state.selected)updateTradeLiveDom();
    return true;
  }catch(e){state.market.connected=false;state.market.error=String(e?.message||e);updateTradeConnectionDom();return false;}
  finally{selectedMarketBusy=false;if(selectedMarketPending){selectedMarketPending=false;queueMicrotask(()=>refreshSelectedMarket(true).catch(()=>{}));}}
}
'''
renderer=renderer[:start]+new_refresh+renderer[end:]

# 5) Held symbols and open-limit symbols are refreshed too. Previously the response was discarded, leaving non-selected PnL stale.
start=renderer.find("async function refreshOpenOrderMarkets(){")
end=renderer.find("\nfunction pointValueKRW",start)
if start<0 or end<0: raise RuntimeError('refreshOpenOrderMarkets block missing')
new_other=r'''async function refreshOpenOrderMarkets(){
  if(!state.market.configured||!state.loggedIn)return;
  const orderSymbols=(state.orders||[]).filter(o=>String(o.status).toUpperCase()==='OPEN'&&String(o.order_type||o.type).toUpperCase()==='LIMIT').map(o=>o.symbol);
  const positionSymbols=(state.positions||[]).map(p=>p.symbol);
  const symbols=[...new Set([...orderSymbols,...positionSymbols].filter(x=>x&&x!==state.selected))].slice(0,8);
  await Promise.all(symbols.map(async sym=>{const ref=marketRef(sym);if(!ref)return;try{const r=await window.desktop.getMarketQuote(ref);applyMarketQuoteToState(sym,r,false);}catch(_e){}}));
  updateTradeLiveDom();
}
'''
renderer=renderer[:start]+new_other+renderer[end:]

# 6) Add stable live fields instead of destroying/rebinding the entire trade UI on every quote.
repls={
'<div class="eval-row block-tone-b"><span>평가담보금</span><strong>${numKrw(equity())}</strong></div>':'<div class="eval-row block-tone-b"><span>평가담보금</span><strong id="liveEquity">${numKrw(equity())}</strong></div>',
'<tr><td>${numKrw(equity())}</td><td>${pos ? fmt(pos.entry, dec(s)) : \'0\'}</td><td>${numKrw(pl)}</td><td>${numKrw(pl + state.realized)}</td><td>${liq ? fmt(liq, dec(s)) : \'0\'}</td></tr>':'<tr><td id="liveEquity2">${numKrw(equity())}</td><td id="liveEntry">${pos ? fmt(pos.entry, dec(s)) : \'0\'}</td><td id="liveSelectedPnl">${numKrw(pl)}</td><td id="liveTotalPnl">${numKrw(pl + state.realized)}</td><td id="liveLiq">${liq ? fmt(liq, dec(s)) : \'0\'}</td></tr>',
'<div class="ticker-row"><span>현/비/%</span><b>${fmt(p.last, dec(s))}</b><em class="red">${fmt(Number.isFinite(p.change)?p.change:(p.last-s.base), dec(s))}</em><em class="red">${Number.isFinite(p.changePct)?Number(p.changePct).toFixed(2):((p.last-s.base)/s.base*100).toFixed(2)}</em><span>시/고/저</span><b>${fmt(p.open||s.base, dec(s))}</b><em class="red">${fmt(p.high||Math.max(p.ask,s.base), dec(s))}</em><em class="blue">${fmt(p.low||Math.min(p.bid,s.base), dec(s))}</em></div>':'<div class="ticker-row"><span>현/비/%</span><b id="liveLast">${fmt(p.last, dec(s))}</b><em class="red" id="liveChange">${fmt(Number.isFinite(p.change)?p.change:(p.last-s.base), dec(s))}</em><em class="red" id="liveChangePct">${Number.isFinite(p.changePct)?Number(p.changePct).toFixed(2):((p.last-s.base)/s.base*100).toFixed(2)}</em><span>시/고/저</span><b id="liveOpen">${fmt(p.open||s.base, dec(s))}</b><em class="red" id="liveHigh">${fmt(p.high||Math.max(p.ask,s.base), dec(s))}</em><em class="blue" id="liveLow">${fmt(p.low||Math.min(p.bid,s.base), dec(s))}</em></div>'
}
for a,b in repls.items():
    if a not in renderer: raise RuntimeError('trade live field anchor missing: '+a[:50])
    renderer=renderer.replace(a,b,1)

# Add index markers to position current-price/PnL cells.
old_pos="<td>${fmt(cur, dec(sy))}</td><td class=\"${pp >= 0 ? 'profit-pos' : 'profit-neg'}\">${numKrw(pp)}</td>"
new_pos="<td><span data-live-pos-price=\"${i}\">${fmt(cur, dec(sy))}</span></td><td class=\"${pp >= 0 ? 'profit-pos' : 'profit-neg'}\"><span data-live-pos-pnl=\"${i}\">${numKrw(pp)}</span></td>"
if old_pos not in renderer: raise RuntimeError('positions live field anchor missing')
renderer=renderer.replace(old_pos,new_pos,1)

# Live DOM patcher goes just before renderTrade.
anchor="function renderTrade(w) {"
patcher=r'''function updateTradeConnectionDom(){const el=document.querySelector('.market-status');if(!el)return;el.classList.toggle('live',!!state.market.connected);el.classList.toggle('off',!state.market.connected);el.textContent=state.market.connected?'실시간':'시세 재연결';}
function updateTradeLiveDom(){
  if(state.view!=='trade')return;const s=state.symbols[state.selected],p=state.prices[state.selected];if(!s||!p)return;
  const pos=currentPosition(),pl=pos?pnlFor(state.selected,pos.side,pos.entry,p.last,pos.qty):0,liq=pos?liquidationPrice(pos):0;
  const set=(id,v)=>{const el=document.getElementById(id);if(el)el.textContent=v;};
  set('liveEquity',numKrw(equity()));set('liveEquity2',numKrw(equity()));set('liveEntry',pos?fmt(pos.entry,dec(s)):'0');set('liveSelectedPnl',numKrw(pl));set('liveTotalPnl',numKrw(pl+state.realized));set('liveLiq',liq?fmt(liq,dec(s)):'0');
  set('liveLast',fmt(p.last,dec(s)));set('liveChange',fmt(Number.isFinite(p.change)?p.change:(p.last-s.base),dec(s)));set('liveChangePct',Number.isFinite(p.changePct)?Number(p.changePct).toFixed(2):((p.last-s.base)/s.base*100).toFixed(2));set('liveOpen',fmt(p.open||s.base,dec(s)));set('liveHigh',fmt(p.high||Math.max(p.ask,s.base),dec(s)));set('liveLow',fmt(p.low||Math.min(p.bid,s.base),dec(s)));
  document.querySelectorAll('[data-live-pos-price]').forEach(el=>{const i=Number(el.dataset.livePosPrice),x=state.positions[i],sy=x&&state.symbols[x.symbol];if(x&&sy)el.textContent=fmt(state.prices[x.symbol].last,dec(sy));});
  document.querySelectorAll('[data-live-pos-pnl]').forEach(el=>{const i=Number(el.dataset.livePosPnl),x=state.positions[i];if(!x)return;const pp=pnlFor(x.symbol,x.side,x.entry,state.prices[x.symbol].last,x.qty);el.textContent=numKrw(pp);const td=el.closest('td');if(td){td.classList.toggle('profit-pos',pp>=0);td.classList.toggle('profit-neg',pp<0);}});
  const tape=document.querySelector('.tape-box');if(tape)tape.innerHTML=state.tape.filter(t=>!t.symbol||t.symbol===state.selected).slice(-10).reverse().map(t=>`<div class="tape-row-v28"><span>${t.time}</span><span class="px">${t.price}</span><span>${t.qty}</span></div>`).join('');
  updateTradeConnectionDom();
}

'''
if anchor not in renderer: raise RuntimeError('renderTrade anchor missing')
renderer=renderer.replace(anchor,patcher+anchor,1)

# 7) Protect trade action clicks from duplicate in-flight requests without changing any order semantics.
old_submit="function submitOrder(side, w) { if (state.orderType === 'MARKET') placeMarket(side, w); else placeLimit(side, w); }"
new_submit="let tradeSubmitBusy=false;async function submitOrder(side,w){if(tradeSubmitBusy)return;tradeSubmitBusy=true;const buy=document.getElementById('buy'),sell=document.getElementById('sell');if(buy)buy.disabled=true;if(sell)sell.disabled=true;try{if(state.orderType==='MARKET')await placeMarket(side,w);else await placeLimit(side,w);}finally{tradeSubmitBusy=false;const b=document.getElementById('buy'),s=document.getElementById('sell');if(b)b.disabled=false;if(s)s.disabled=false;setTimeout(()=>refreshSelectedMarket(true),0);}}"
if old_submit not in renderer: raise RuntimeError('submitOrder anchor missing')
renderer=renderer.replace(old_submit,new_submit,1)

old_close="async function closePosition(i, w) {\n  const p=state.positions[i]; if(!p)return;"
new_close="const closingPositionIds=new Set();\nasync function closePosition(i, w) {\n  const p=state.positions[i]; if(!p||closingPositionIds.has(String(p.id)))return;closingPositionIds.add(String(p.id));"
if old_close not in renderer: raise RuntimeError('closePosition anchor missing')
renderer=renderer.replace(old_close,new_close,1)
# Ensure lock is released on both failure and success paths.
old_fail="if(!result?.ok){showModal('청산 실패',result?.error||'포지션 청산에 실패했습니다.');return;}\n  if(state.sound.close)playBeep(); await hydrateSharedState(); renderTrade(w);"
new_fail="if(!result?.ok){closingPositionIds.delete(String(p.id));showModal('청산 실패',result?.error||'포지션 청산에 실패했습니다.');return;}\n  closingPositionIds.delete(String(p.id));if(state.sound.close)playBeep(); await hydrateSharedState(); renderTrade(w);setTimeout(()=>refreshSelectedMarket(true),0);"
if old_fail not in renderer: raise RuntimeError('closePosition completion anchor missing')
renderer=renderer.replace(old_fail,new_fail,1)

# 8) Make held/open-order symbol refresh more frequent and selected price loop more responsive, still serialized.
old_poll="openOrderTick=(openOrderTick+1)%4;\n    if(openOrderTick===0) await refreshOpenOrderMarkets().catch(()=>{});"
new_poll="openOrderTick=(openOrderTick+1)%2;\n    if(openOrderTick===0) await refreshOpenOrderMarkets().catch(()=>{});"
if old_poll not in renderer: raise RuntimeError('openOrderTick anchor missing')
renderer=renderer.replace(old_poll,new_poll,1)
old_delay="if(!appPollStopped) marketPollTimer=setTimeout(marketPollLoop,1200);"
new_delay="if(!appPollStopped) marketPollTimer=setTimeout(marketPollLoop,800);"
if old_delay not in renderer: raise RuntimeError('market poll delay anchor missing')
renderer=renderer.replace(old_delay,new_delay,1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ["HSIQ26:{region:'HK',code:'HSI'}","selectedMarketPending","applyMarketQuoteToState","updateTradeLiveDom","data-live-pos-pnl","tradeSubmitBusy","closingPositionIds","setTimeout(marketPollLoop,800)"]:
    if needle not in check: raise RuntimeError('missing v1.0.31 runtime patch: '+needle)
print('VELTRO v1.0.31 trading live-price, PnL, stale-state and click-flow stability patch applied')
