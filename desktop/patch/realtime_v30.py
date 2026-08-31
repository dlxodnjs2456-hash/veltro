import pathlib,re

root=pathlib.Path.cwd(); renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old_decl="let currentCode=state.selected,currentK=1,chart=null,candleSeries=null,volumeSeries=null,overlaySeries=[],loading=false,quoteTimer=null,barTimer=null,lastBars=[];"
new_decl="let currentCode=state.selected,currentK=1,chart=null,candleSeries=null,volumeSeries=null,overlaySeries=[],loading=false,quoteTimer=null,barTimer=null,lastBars=[],realtimeWs=null,realtimeRetry=null,realtimeSeq=0;"
if old_decl not in renderer: raise RuntimeError('chart state declaration anchor missing')
renderer=renderer.replace(old_decl,new_decl,1)

helper_anchor="function localSymbol(){return state.symbols[currentCode]||state.symbols.NQU26;}"
helpers=r'''function isHsiCode(){return ['HSI','HSIQ26','HSIU26'].includes(String(currentCode||'').toUpperCase());}
  function closeRealtime(){realtimeSeq++;if(realtimeRetry){clearTimeout(realtimeRetry);realtimeRetry=null;}try{realtimeWs?.close()}catch{}realtimeWs=null;}
  function applyRealtimeTick(v,ts=Date.now(),qty=0){const sy=localSymbol();if(!Number.isFinite(v)||v<=0)return;lastEl.textContent=fmt(v,dec(sy));const bucket=({1:1,2:5,3:15,4:30,5:60}[currentK]||1)*60000,bt=Math.floor(Number(ts||Date.now())/bucket)*bucket;let b=lastBars.length?{...lastBars[lastBars.length-1]}:null;if(!b||Math.floor(b.t/bucket)*bucket!==bt){b={t:bt,o:v,h:v,l:v,c:v,v:Math.max(0,Number(qty)||0)};lastBars.push(b);}else{b.h=Math.max(Number(b.h)||v,v);b.l=Math.min(Number(b.l)||v,v);b.c=v;b.t=bt;b.v=Math.max(0,Number(b.v||0)+(Number(qty)||0));lastBars[lastBars.length-1]=b;}if(candleSeries)candleSeries.update({time:Math.floor(bt/1000),open:b.o,high:b.h,low:b.l,close:b.c});if(volumeSeries)volumeSeries.update({time:Math.floor(bt/1000),value:b.v,color:b.c>=b.o?'rgba(239,83,80,.45)':'rgba(33,150,243,.45)'});showLastBar(b);conn.textContent='LIVE · LS WS';conn.classList.add('live');window.dispatchEvent(new CustomEvent('veltro:market-tick',{detail:{symbol:String(currentCode),price:v,ts:bt,provider:'ls'}}));}
  function startRealtime(){closeRealtime();if(!isHsiCode()||document.hidden)return;const seq=++realtimeSeq,symbol=String(currentCode||'HSIQ26').toUpperCase();const url='wss://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/hsi-realtime-api?token=veltro-hsi-realtime-20260831&symbol='+encodeURIComponent(symbol);try{const ws=new WebSocket(url);realtimeWs=ws;conn.textContent='LS 실시간 연결 중...';conn.classList.remove('live');ws.onmessage=(ev)=>{if(seq!==realtimeSeq)return;try{const m=JSON.parse(String(ev.data||'{}'));if(m?.type==='tick'&&String(m?.source||'').toUpperCase()==='OVC')applyRealtimeTick(Number(m.price),Number(m.ts)||Date.now(),Number(m.qty)||0);else if(m?.type==='status'&&m?.state==='upstream_error')conn.textContent='LS 실시간 재연결 중...';}catch{}};ws.onopen=()=>{if(seq===realtimeSeq)conn.textContent='LS 실시간 구독 중...';};ws.onerror=()=>{if(seq===realtimeSeq)conn.textContent='LS 실시간 재연결 중...';};ws.onclose=()=>{if(seq!==realtimeSeq||!isHsiCode())return;realtimeWs=null;realtimeRetry=setTimeout(()=>{if(seq===realtimeSeq)startRealtime();},1200);};}catch{realtimeRetry=setTimeout(()=>startRealtime(),1500);}}
  function showChartNotice(){let m=document.getElementById('chartOpenSourceNotice');if(m){m.remove();return;}m=document.createElement('div');m.id='chartOpenSourceNotice';m.style.cssText='position:absolute;top:52px;right:12px;z-index:30;width:330px;background:#fff;border:1px solid #d7dde5;box-shadow:0 8px 28px rgba(0,0,0,.16);padding:14px;font:12px Arial,sans-serif;color:#4b5563';m.innerHTML='<div style="font-weight:700;color:#111827;margin-bottom:8px">오픈소스 고지</div><div>TradingView Lightweight Charts™<br>Copyright © 2025 TradingView, Inc.</div><a href="https://www.tradingview.com/" target="_blank" rel="noreferrer" style="display:inline-block;margin-top:9px;color:#2563eb">TradingView 웹사이트</a><button type="button" style="float:right;border:0;background:#eef2f7;padding:5px 8px;cursor:pointer">닫기</button>';m.querySelector('button').onclick=()=>m.remove();w.querySelector('.tv-chart-page').appendChild(m);}
'''
if helper_anchor not in renderer: raise RuntimeError('localSymbol anchor missing')
renderer=renderer.replace(helper_anchor,helper_anchor+'\n  '+helpers,1)

# Optimized chart revisions may change the polling interval. Replace the polling expression by shape, not by a fixed millisecond value.
renderer,n=re.subn(r"quoteTimer=setInterval\(\(\)=>\{if\(!document\.hidden\)refreshQuote\(\)\},\d+\);","quoteTimer=setInterval(()=>{if(!document.hidden&&!isHsiCode())refreshQuote()},1000);",renderer,count=1)
if n!=1: raise RuntimeError('quote timer shape missing')

old_change="w.querySelector('#proChartSymbol').onchange=e=>{currentCode=e.target.value;state.selected=currentCode;lastBars=[];draw(true);};"
new_change="w.querySelector('#proChartSymbol').onchange=e=>{closeRealtime();currentCode=e.target.value;state.selected=currentCode;lastBars=[];draw(true);startRealtime();};"
if old_change not in renderer: raise RuntimeError('symbol onchange anchor missing')
renderer=renderer.replace(old_change,new_change,1)

# Start the websocket immediately after the first chart draw, regardless of the poll timer's current interval.
initial_anchor="await draw(true);"
if initial_anchor not in renderer: raise RuntimeError('initial chart draw anchor missing')
renderer=renderer.replace(initial_anchor,initial_anchor+'startRealtime();',1)

old_unload="window.addEventListener('beforeunload',()=>{clearInterval(quoteTimer);clearInterval(barTimer);destroyChart();},{once:true});"
new_unload="window.addEventListener('beforeunload',()=>{closeRealtime();clearInterval(quoteTimer);clearInterval(barTimer);destroyChart();},{once:true});document.addEventListener('visibilitychange',()=>{if(document.hidden)closeRealtime();else if(isHsiCode())startRealtime();});"
if old_unload not in renderer: raise RuntimeError('beforeunload anchor missing')
renderer=renderer.replace(old_unload,new_unload,1)

# Remove the visible footer attribution only; keep the required attribution notice and link behind the chart info control.
renderer,n=re.subn(r'<span class="chart-attribution">.*?</span>','',renderer,count=1,flags=re.S)
if n!=1: raise RuntimeError('chart attribution footer anchor missing')
gear_anchor="w.querySelector('#indicatorBtn').onclick=()=>{panel.hidden=!panel.hidden;updateIndicatorPanel();};"
gear_new=gear_anchor+"const gear=w.querySelector('.tv-gear');if(gear){gear.style.cursor='pointer';gear.title='차트 정보 / 오픈소스 고지';gear.onclick=showChartNotice;}"
if gear_anchor not in renderer: raise RuntimeError('chart gear anchor missing')
renderer=renderer.replace(gear_anchor,gear_new,1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ['hsi-realtime-api','LIVE · LS WS','applyRealtimeTick','startRealtime','showChartNotice','오픈소스 고지']:
    if needle not in check: raise RuntimeError('missing realtime v30 patch: '+needle)
if 'class="chart-attribution"' in check: raise RuntimeError('visible chart attribution footer remains')
print('VELTRO v1.0.30 HSI OVC websocket realtime and attribution relocation applied')
