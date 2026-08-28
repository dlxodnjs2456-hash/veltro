import json, pathlib, re
root=pathlib.Path.cwd(); build=root/'desktop'/'build'
renderer_path=build/'src'/'renderer.js'; styles_path=build/'src'/'styles.css'; main_path=build/'src'/'main.js'; preload_path=build/'src'/'preload.js'; pkg_path=build/'package.json'

renderer=renderer_path.read_text(encoding='utf-8')
loader=r'''async function ensureLightweightCharts(){
  if(window.LightweightCharts?.createChart) return window.LightweightCharts;
  if(window.__veltroLwLoader) return window.__veltroLwLoader;
  window.__veltroLwLoader=(async()=>{
    const src=await window.desktop?.chartEngineUrl?.();
    if(!src) throw new Error('chart_assets_missing');
    await new Promise((resolve,reject)=>{
      if(window.LightweightCharts?.createChart) return resolve();
      const el=document.createElement('script');el.src=src;el.async=false;el.onload=resolve;el.onerror=()=>reject(new Error('chart_library_load_failed'));document.head.appendChild(el);
    });
    if(!window.LightweightCharts?.createChart) throw new Error('chart_library_load_failed');
    return window.LightweightCharts;
  })();
  return window.__veltroLwLoader;
}

const DEFAULT_INDICATORS='''
renderer,n=re.subn(r'async function ensureHighchartsStock\(\)\{.*?\n\}\n\nconst DEFAULT_INDICATORS=',loader,renderer,count=1,flags=re.S)
if n!=1: raise RuntimeError('chart loader replacement failed')

chart=r'''async function renderChartWindow(w){
  let currentCode=state.selected,currentK=1,chart=null,candleSeries=null,volumeSeries=null,overlaySeries=[],loading=false,quoteTimer=null,barTimer=null,lastBars=[];
  let prefs=chartIndicatorPrefs();
  const codeOptions=Object.entries(state.symbols).map(([code,sy])=>`<option value="${code}" ${code===currentCode?'selected':''}>${code} · ${sy.name}</option>`).join('');
  w.innerHTML=`<div class="tv-chart-page">
    <div class="tv-head"><div class="tv-head-left">
      <select id="proChartSymbol">${codeOptions}</select><button class="tv-tf-title" id="tfTitle">1분</button><span class="tv-candle-icon">♮</span>
      <button class="tv-tool">⊕ 비교</button><button class="tv-tool" id="indicatorBtn">ƒx 지표</button><button class="tv-tool tv-muted">↶</button><button class="tv-tool tv-muted">↷</button>
      <span class="tv-save">☁ 저장</span><span class="tv-gear">⚙</span><button class="tv-tool" id="fitChartBtn">⛶</button>
    </div><div class="tv-status"><span id="chartConnState">연결 확인 중...</span></div></div>
    <div class="tv-subhead"><strong id="tvSymbolTitle">${currentCode}</strong><span> · <b id="tvTfLabel">1</b> · <span id="tvExchange">CME</span></span><span class="tv-live-dot"></span>
      <div class="tv-ohlc" id="chartOhlc"><span>시 -</span><span>고 -</span><span>저 -</span><span>종 -</span></div><div class="tv-last" id="chartLastPrice">-</div></div>
    <div class="tv-timeframes"><button class="chart-tf active" data-k="1">1분</button><button class="chart-tf" data-k="2">5분</button><button class="chart-tf" data-k="3">15분</button><button class="chart-tf" data-k="4">30분</button><button class="chart-tf" data-k="5">1시간</button><button class="tv-tool" id="chartReload">새로고침</button></div>
    <div class="tv-indicator-panel" id="indicatorPanel" hidden><div class="pro-indicator-title"><div><strong>지표 설정</strong><small>차트 오버레이 설정</small></div><button id="indicatorClose">×</button></div>
      <div class="ind-section"><h4>메인 차트</h4>${indicatorRow('SMA','SMA 이동평균',['1','2','3'],prefs)}${indicatorRow('EMA','EMA 지수이동평균',['기간'],prefs)}${indicatorRow('BB','볼린저밴드',['기간','표준편차'],prefs)}</div>
      <div class="ind-section"><h4>보조 지표</h4>${indicatorRow('VOL','거래량',[],prefs)}</div><div class="pro-indicator-actions"><button class="secondary" id="indicatorReset">기본값</button><button id="indicatorApply">적용</button></div></div>
    <div class="tv-main"><div class="tv-left-tools"><span>＋</span><span>／</span><span>☰</span><span>⌁</span><span>T</span><span>⌁</span><span>◎</span><span>⌕</span><span>🧲</span><span>✎</span><span>🔒</span><span>◉</span><span>🗑</span></div><div class="tv-chart-wrap"><div id="klineChart" class="tv-chart-box"><div class="chart-loading">LS증권 분봉을 불러오는 중...</div></div></div></div>
    <div class="tv-footer"><span id="chartFootnote">LS Securities</span><span id="chartUpdated"></span></div></div>`;

  const box=w.querySelector('#klineChart'),panel=w.querySelector('#indicatorPanel'),lastEl=w.querySelector('#chartLastPrice'),ohlcEl=w.querySelector('#chartOhlc'),conn=w.querySelector('#chartConnState'),foot=w.querySelector('#chartFootnote');
  function localSymbol(){return state.symbols[currentCode]||state.symbols.NQU26;}
  function localRef(){const old=state.selected;state.selected=currentCode;const r=marketRef();state.selected=old;return r;}
  function updateIndicatorPanel(){panel.querySelectorAll('[data-ind]').forEach(x=>x.checked=!!prefs[x.dataset.ind]?.enabled);panel.querySelectorAll('[data-param]').forEach(x=>{const [n,i]=x.dataset.param.split(':');x.value=Number(prefs[n]?.params?.[Number(i)]??x.value);});}
  function readIndicatorPanel(){const next=JSON.parse(JSON.stringify(prefs));panel.querySelectorAll('[data-ind]').forEach(x=>{if(next[x.dataset.ind])next[x.dataset.ind].enabled=x.checked;});panel.querySelectorAll('[data-param]').forEach(x=>{const [n,i]=x.dataset.param.split(':');if(next[n])next[n].params[Number(i)]=Math.max(1,Number(x.value)||1);});return next;}
  function normalizeBars(raw){return (Array.isArray(raw)?raw:[]).map(b=>({t:Number(b.t??b.timestamp),o:Number(b.o??b.open),h:Number(b.h??b.high),l:Number(b.l??b.low),c:Number(b.c??b.close),v:Math.max(0,Number(b.v??b.volume??0))})).filter(b=>[b.t,b.o,b.h,b.l,b.c].every(Number.isFinite)&&b.t>0).map(b=>({...b,t:b.t<1e12?b.t*1000:b.t})).sort((a,b)=>a.t-b.t);}
  function showLastBar(bar){const sy=localSymbol();lastEl.textContent=fmt(bar.c,dec(sy));ohlcEl.innerHTML=`<span>시 ${fmt(bar.o,dec(sy))}</span><span>고 ${fmt(bar.h,dec(sy))}</span><span>저 ${fmt(bar.l,dec(sy))}</span><span>종 ${fmt(bar.c,dec(sy))}</span>`;w.querySelector('#chartUpdated').textContent=`마지막 ${new Date(bar.t).toLocaleTimeString('ko-KR',{hour12:false})}`;}
  function destroyChart(){try{box.__ro?.disconnect()}catch{}try{chart?.remove()}catch{}chart=null;candleSeries=null;volumeSeries=null;overlaySeries=[];}
  function sma(bars,p){const out=[];for(let i=p-1;i<bars.length;i++){let s=0;for(let j=i-p+1;j<=i;j++)s+=bars[j].c;out.push({time:Math.floor(bars[i].t/1000),value:s/p});}return out;}
  function ema(bars,p){const out=[];if(!bars.length)return out;const k=2/(p+1);let v=bars[0].c;for(let i=0;i<bars.length;i++){v=i?bars[i].c*k+v*(1-k):v;out.push({time:Math.floor(bars[i].t/1000),value:v});}return out;}
  function buildChart(bars){
    destroyChart();box.innerHTML='';const LC=window.LightweightCharts;
    chart=LC.createChart(box,{width:box.clientWidth,height:box.clientHeight,layout:{background:{type:'solid',color:'#fff'},textColor:'#4b5563',fontSize:12,fontFamily:'Arial, sans-serif'},grid:{vertLines:{color:'#eef1f5'},horzLines:{color:'#eef1f5'}},rightPriceScale:{borderColor:'#dfe3e8',scaleMargins:{top:.08,bottom:.24}},timeScale:{borderColor:'#dfe3e8',timeVisible:true,secondsVisible:false,rightOffset:3,barSpacing:9,minBarSpacing:3},crosshair:{mode:LC.CrosshairMode?.Normal??0},localization:{locale:'ko-KR'}});
    candleSeries=chart.addCandlestickSeries({upColor:'#ef5350',downColor:'#2196f3',borderUpColor:'#ef5350',borderDownColor:'#2196f3',wickUpColor:'#ef5350',wickDownColor:'#2196f3',priceLineVisible:true,lastValueVisible:true});
    candleSeries.setData(bars.map(b=>({time:Math.floor(b.t/1000),open:b.o,high:b.h,low:b.l,close:b.c})));
    if(prefs.VOL?.enabled){volumeSeries=chart.addHistogramSeries({priceFormat:{type:'volume'},priceScaleId:'vol'});chart.priceScale('vol').applyOptions({scaleMargins:{top:.78,bottom:0}});volumeSeries.setData(bars.map(b=>({time:Math.floor(b.t/1000),value:b.v,color:b.c>=b.o?'rgba(239,83,80,.45)':'rgba(33,150,243,.45)'})));}
    if(prefs.SMA?.enabled)for(const p of prefs.SMA.params||[]){const s=chart.addLineSeries({lineWidth:1,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});s.setData(sma(bars,Number(p)||20));overlaySeries.push(s);}if(prefs.EMA?.enabled){const s=chart.addLineSeries({lineWidth:1,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});s.setData(ema(bars,Number(prefs.EMA.params[0])||20));overlaySeries.push(s);}
    chart.timeScale().fitContent();const ro=new ResizeObserver(()=>{if(chart)chart.applyOptions({width:box.clientWidth,height:box.clientHeight});});ro.observe(box);box.__ro=ro;
  }
  async function draw(resetView=false){if(loading)return;loading=true;const ref=localRef(),sy=localSymbol();if(!ref){box.innerHTML='<div class="chart-loading">선택 종목의 시세 매핑이 없습니다.</div>';loading=false;return;}try{const [qr,res]=await Promise.all([window.desktop.getMarketQuote(ref).catch(()=>null),window.desktop.getMarketKline({...ref,kType:currentK,limit:300}).catch(()=>null)]);const bars=normalizeBars(res?.bars);lastBars=bars;if(qr?.ok&&Number.isFinite(Number(qr.quote?.ld)))lastEl.textContent=fmt(Number(qr.quote.ld),dec(sy));if(!bars.length){box.innerHTML='<div class="chart-loading"><b>LS증권 분봉 데이터가 없습니다.</b><br>종목코드 또는 분봉 응답을 확인 중입니다.</div>';destroyChart();foot.textContent=`${currentCode} · LS`;return;}buildChart(bars);showLastBar(bars[bars.length-1]);if(resetView)chart?.timeScale()?.fitContent();conn.textContent='LIVE · LS';conn.classList.add('live');foot.textContent=`${currentCode} · LS · ${bars.length}봉`;w.querySelector('#tvSymbolTitle').textContent=currentCode;w.querySelector('#tvTfLabel').textContent=({1:'1',2:'5',3:'15',4:'30',5:'60'}[currentK]||'1');w.querySelector('#tfTitle').textContent=({1:'1분',2:'5분',3:'15분',4:'30분',5:'1시간'}[currentK]||'1분');w.querySelector('#tvExchange').textContent=sy.exchange||'CME';}catch(e){box.innerHTML=`<div class="chart-loading">차트 조회 실패<br>${String(e?.message||e)}</div>`;destroyChart();conn.textContent='연결 오류';conn.classList.remove('live');}finally{loading=false;}}
  async function refreshQuote(){const ref=localRef(),sy=localSymbol();if(!ref)return;try{const qr=await window.desktop.getMarketQuote(ref),v=Number(qr?.quote?.ld);if(qr?.ok&&Number.isFinite(v)){lastEl.textContent=fmt(v,dec(sy));if(candleSeries&&lastBars.length){const b={...lastBars[lastBars.length-1]},bucket=({1:1,2:5,3:15,4:30,5:60}[currentK]||1)*60000,now=Number(qr.quote?.t)||Date.now(),bt=Math.floor(now/bucket)*bucket;if(bt===Math.floor(b.t/bucket)*bucket){b.h=Math.max(b.h,v);b.l=Math.min(b.l,v);b.c=v;b.t=bt;candleSeries.update({time:Math.floor(bt/1000),open:b.o,high:b.h,low:b.l,close:b.c});showLastBar(b);}}}}catch(_e){}}
  try{await initMarketData();await ensureLightweightCharts();}catch(_e){box.innerHTML='<div class="chart-loading">차트 엔진을 불러오지 못했습니다.</div>';return;}
  w.querySelector('#indicatorBtn').onclick=()=>{panel.hidden=!panel.hidden;updateIndicatorPanel();};w.querySelector('#indicatorClose').onclick=()=>panel.hidden=true;w.querySelector('#indicatorReset').onclick=()=>{prefs=JSON.parse(JSON.stringify(DEFAULT_INDICATORS));updateIndicatorPanel();};w.querySelector('#indicatorApply').onclick=()=>{prefs=readIndicatorPanel();saveChartIndicatorPrefs(prefs);panel.hidden=true;draw(false);};w.querySelector('#fitChartBtn').onclick=()=>chart?.timeScale()?.fitContent();w.querySelector('#chartReload').onclick=()=>draw(true);w.querySelectorAll('.chart-tf').forEach(btn=>btn.onclick=()=>{w.querySelectorAll('.chart-tf').forEach(x=>x.classList.remove('active'));btn.classList.add('active');currentK=Number(btn.dataset.k)||1;draw(true);});w.querySelector('#proChartSymbol').onchange=e=>{currentCode=e.target.value;state.selected=currentCode;lastBars=[];draw(true);};await draw(true);quoteTimer=setInterval(()=>{if(!document.hidden)refreshQuote()},2500);barTimer=setInterval(()=>{if(!document.hidden)draw(false)},30000);window.addEventListener('beforeunload',()=>{clearInterval(quoteTimer);clearInterval(barTimer);destroyChart();},{once:true});
}
'''
renderer,n=re.subn(r'async function renderChartWindow\(w\)\{.*?\n\}\n\nfunction showModal',chart+'\nfunction showModal',renderer,count=1,flags=re.S)
if n!=1: raise RuntimeError('chart window replacement failed')
renderer_path.write_text(renderer,encoding='utf-8')

styles=styles_path.read_text(encoding='utf-8')+r'''

/* LS trading-style chart v20 */
.tv-chart-page{height:100%;display:flex;flex-direction:column;background:#fff;color:#3d4652;font-family:Arial,'Noto Sans KR',sans-serif}.tv-head{height:48px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e6e9ed;padding:0 10px;background:#fff}.tv-head-left{display:flex;align-items:center;gap:6px}.tv-head select{height:34px;border:1px solid #e2e6ea;border-radius:3px;font-weight:700;padding:0 10px;background:#fff}.tv-tool,.tv-tf-title{height:30px;border:0;background:#fff;color:#3f4854;padding:0 8px;border-radius:4px;font-weight:600}.tv-tool:hover,.tv-tf-title:hover{background:#f2f4f7}.tv-muted{color:#a4abb4}.tv-save,.tv-gear,.tv-candle-icon{padding:0 6px;color:#606a76}.tv-status{font-size:12px}.tv-status .live,#chartConnState.live{color:#008f55;font-weight:700}.tv-subhead{height:42px;display:flex;align-items:center;gap:6px;padding:0 58px;border-bottom:1px solid #edf0f3;font-size:13px}.tv-live-dot{width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block}.tv-ohlc{display:flex;gap:10px;margin-left:6px;font-size:12px}.tv-last{margin-left:auto;font-size:22px;font-weight:800;color:#172033}.tv-timeframes{height:38px;display:flex;align-items:center;gap:4px;padding:0 58px;border-bottom:1px solid #edf0f3}.tv-timeframes .chart-tf{border:0;background:#fff;padding:6px 10px;border-radius:4px}.tv-timeframes .chart-tf.active{background:#eaf3ff;color:#1769aa;font-weight:800}.tv-timeframes #chartReload{margin-left:auto}.tv-main{flex:1;min-height:0;display:flex}.tv-left-tools{width:52px;border-right:1px solid #edf0f3;display:flex;flex-direction:column;align-items:center;gap:8px;padding:10px 0;font-size:18px;color:#5b6570}.tv-left-tools span{width:34px;height:34px;display:flex;align-items:center;justify-content:center;border-radius:4px}.tv-left-tools span:hover{background:#f2f4f7}.tv-chart-wrap{flex:1;min-width:0;min-height:0;position:relative}.tv-chart-box{position:absolute;inset:0;background:#fff}.chart-loading{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;color:#77818d;line-height:1.65}.tv-footer{height:28px;border-top:1px solid #edf0f3;display:flex;align-items:center;justify-content:space-between;padding:0 12px 0 58px;font-size:11px;color:#8a929c}.tv-indicator-panel{position:absolute;z-index:20;top:91px;left:200px;width:430px;background:#fff;border:1px solid #d9dee5;box-shadow:0 8px 30px rgba(0,0,0,.14);border-radius:6px;padding:12px}
'''
styles_path.write_text(styles,encoding='utf-8')

main=main_path.read_text(encoding='utf-8')
main=re.sub(r"(?m)^\s*ipcMain\.handle\('app:chart-assets-base'.*?$",'',main)
anchor="ipcMain.handle('app:login-poster-url',()=>pathToFileURL(path.join(process.resourcesPath,'login-left.jpg')).toString());"
if anchor not in main: raise RuntimeError('login poster handler anchor missing')
if "app:chart-engine-url" not in main:
    main=main.replace(anchor,anchor+"\nipcMain.handle('app:chart-engine-url',()=>pathToFileURL(path.join(process.resourcesPath,'lightweight-charts','lightweight-charts.standalone.production.js')).toString());",1)
main_path.write_text(main,encoding='utf-8')

preload=preload_path.read_text(encoding='utf-8')
preload=re.sub(r"(?m)^\s*chartAssetsBase:.*?$",'',preload)
anchor="remoteLoginPoster: () => ipcRenderer.invoke('app:remote-login-poster'),"
if anchor not in preload: raise RuntimeError('preload anchor missing')
if "chartEngineUrl:" not in preload: preload=preload.replace(anchor,anchor+"\n  chartEngineUrl: () => ipcRenderer.invoke('app:chart-engine-url'),",1)
preload_path.write_text(preload,encoding='utf-8')

pkg=json.loads(pkg_path.read_text(encoding='utf-8-sig'));pkg.setdefault('dependencies',{}).pop('highcharts',None);pkg['dependencies']['lightweight-charts']='4.2.3';extra=pkg.setdefault('build',{}).get('extraResources') or [];extra=[x for x in extra if not(isinstance(x,dict) and x.get('to') in {'highcharts','lightweight-charts'})];extra.append({'from':'node_modules/lightweight-charts/dist','to':'lightweight-charts'});pkg['build']['extraResources']=extra;pkg_path.write_text(json.dumps(pkg,ensure_ascii=False,indent=2),encoding='utf-8')

for needle,src in [('ensureLightweightCharts',renderer),('tv-chart-page',renderer),("app:chart-engine-url",main),('chartEngineUrl:',preload),('lightweight-charts',json.dumps(pkg))]:
    if needle not in src: raise RuntimeError('missing '+needle)
print('VELTRO trading-style LS chart patch applied')
