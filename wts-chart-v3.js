(()=>{
  if(window.__VELTRO_WTS_CHART_V3__)return;
  window.__VELTRO_WTS_CHART_V3__=true;
  const FEED='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/market-data-api';
  let liveTimer=null,resizeObs=null,candleSeries=null,volumeSeries=null,lastBars=[];
  const tfLabel={1:'1분',2:'5분',3:'15분',4:'30분',5:'1시간'};
  const tfMinutes={1:1,2:5,3:15,4:30,5:60};
  const style=document.createElement('style');
  style.textContent=`
  .wts-tv{height:100%;min-height:0;min-width:0;display:flex;flex-direction:column;background:#fff;border:1px solid #e1e6ec;color:#3d4652;overflow:hidden}
  .wts-tv-head{min-height:44px;display:flex;align-items:center;gap:6px;padding:5px 10px;border-bottom:1px solid #e6e9ed;min-width:0;flex-wrap:wrap}
  .wts-tv-head strong{font-size:13px;color:#111827;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:65%}.wts-tv-head span{font-size:12px;color:#6b7280}.wts-tv-head .live{margin-left:auto;color:#0c9b6a;font-weight:800;white-space:nowrap}.wts-tv-head .stale{color:#c57a00}
  .wts-tv-tfs{min-height:40px;display:flex;align-items:center;gap:4px;padding:4px 9px;border-bottom:1px solid #e6e9ed;overflow-x:auto;overflow-y:hidden;min-width:0;scrollbar-width:thin}
  .wts-tv-tfs button{height:28px;flex:0 0 auto;border:0;background:#fff;padding:0 10px;border-radius:4px;color:#4b5563;font-weight:700;cursor:pointer}.wts-tv-tfs button.active{background:#eaf4ff;color:#1677c8}.wts-tv-tfs .reload{margin-left:auto;border:1px solid #d5dbe3}
  .wts-tv-ohlc{min-height:30px;display:flex;align-items:center;gap:12px;padding:4px 10px;border-bottom:1px solid #f0f2f5;font-size:11px;color:#667085;overflow-x:auto;overflow-y:hidden;white-space:nowrap;min-width:0}.wts-tv-ohlc b{font-size:14px;color:#111827;margin-right:4px}.wts-tv-box{position:relative;flex:1 1 auto;min-height:260px;min-width:0;width:100%;overflow:hidden}.wts-tv-state{min-height:25px;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:0 9px;border-top:1px solid #eef1f5;font-size:10px;color:#8a94a3;min-width:0}.wts-tv-state span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .wts-tv-loading{position:absolute;inset:0;display:grid;place-items:center;text-align:center;color:#667085;background:#fff;z-index:2;padding:24px}.wts-tv-loading b{color:#1f2937}
  .chart-wrap,.card.chart-wrap,#main,.work,.trade,.center{min-width:0!important;max-width:100%!important}.chart-wrap{overflow:hidden!important}.trade{grid-template-rows:auto auto minmax(300px,1fr) minmax(140px,220px)!important}
  @media(max-width:1280px) and (min-width:821px){.grid{grid-template-columns:180px minmax(0,1fr) 240px!important}.grid.no-order{grid-template-columns:180px minmax(0,1fr)!important}.work{padding:7px!important}.right{padding:7px 7px 7px 0!important}.side .sub{padding-left:18px!important}.tabs button{min-width:70px!important}.market-head{min-width:0!important}.market-head>div:first-child{min-width:0!important;overflow:hidden}.market-head b,.market-head small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.last{font-size:21px!important;white-space:nowrap}.wts-tv-head strong{max-width:52%}}
  @media(max-width:1024px) and (min-width:821px){.grid{grid-template-columns:160px minmax(0,1fr) 205px!important}.grid.no-order{grid-template-columns:160px minmax(0,1fr)!important}.tabs{overflow-x:auto!important}.tabs button{min-width:62px!important;font-size:12px!important}.wts-tv-head .live{width:100%;margin-left:0}.wts-tv-head strong{max-width:72%}.wts-tv-ohlc{gap:7px}.order{padding:9px!important}}
  @media(max-width:820px){.wts-tv{height:calc(100dvh - 150px);min-height:430px;border:0}.wts-tv-head{min-height:42px;padding:5px 7px}.wts-tv-head strong{max-width:70%}.wts-tv-head .live{font-size:10px}.wts-tv-tfs{min-height:38px;padding:3px 5px}.wts-tv-tfs button{padding:0 8px;font-size:11px}.wts-tv-tfs .reload{margin-left:0}.wts-tv-ohlc{gap:8px;padding:4px 7px}.wts-tv-box{min-height:300px}.m-main,.m-main .chart-wrap{min-width:0!important;width:100%!important;max-width:100vw!important;overflow:hidden!important}.m-main .chart-wrap{height:calc(100dvh - 150px)!important;min-height:430px!important}.m-main{overflow-x:hidden!important}.market-head{min-width:0!important}.market-head>div:first-child{min-width:0!important;overflow:hidden}.market-head b,.market-head small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.last{font-size:20px!important;white-space:nowrap}}
  `;
  document.head.appendChild(style);

  async function ensureLC(){
    if(window.LightweightCharts?.createChart)return window.LightweightCharts;
    if(window.__wtsLcPromise)return window.__wtsLcPromise;
    window.__wtsLcPromise=new Promise((resolve,reject)=>{
      const s=document.createElement('script');
      s.src='https://unpkg.com/lightweight-charts@4.2.3/dist/lightweight-charts.standalone.production.js';
      s.onload=()=>window.LightweightCharts?.createChart?resolve(window.LightweightCharts):reject(new Error('chart_engine_load_failed'));
      s.onerror=()=>reject(new Error('chart_engine_load_failed'));
      document.head.appendChild(s);
    });
    return window.__wtsLcPromise;
  }
  function normalize(raw){return (Array.isArray(raw)?raw:[]).map(b=>({t:Number(b.t??b.timestamp),o:Number(b.o??b.open),h:Number(b.h??b.high),l:Number(b.l??b.low),c:Number(b.c??b.close),v:Math.max(0,Number(b.v??b.volume??0))})).filter(b=>[b.t,b.o,b.h,b.l,b.c].every(Number.isFinite)&&b.t>0).map(b=>({...b,t:b.t<1e12?b.t*1000:b.t})).sort((a,b)=>a.t-b.t)}
  function digits(){const x=Number(cur?.tick||0.01);const s=String(x);return s.includes('.')?s.split('.')[1].length:0}
  function fmt(v){return Number(v).toLocaleString('en-US',{minimumFractionDigits:digits(),maximumFractionDigits:digits()})}
  function cleanup(){if(liveTimer){clearInterval(liveTimer);liveTimer=null}try{resizeObs?.disconnect()}catch{}resizeObs=null;try{chart?.remove?.()}catch{}chart=null;candleSeries=null;volumeSeries=null;lastBars=[]}
  function setConn(text,stale=false){const el=document.querySelector('#wtsTvConn');if(!el)return;el.textContent=text;el.classList.toggle('stale',!!stale)}
  function shell(){
    const wrap=document.querySelector('.chart-wrap');if(!wrap)return null;
    wrap.innerHTML=`<div class="wts-tv"><div class="wts-tv-head"><strong id="wtsTvSymbol">${cur.symbol} · ${cur.name}</strong><span id="wtsTvExchange">${cur.exchange}</span><span class="live" id="wtsTvConn">연결 확인 중...</span></div><div class="wts-tv-tfs">${[1,2,3,4,5].map(k=>`<button data-tv-tf="${k}" class="${Number(tf)===k?'active':''}">${tfLabel[k]}</button>`).join('')}<button class="reload" id="wtsTvReload">새로고침</button></div><div class="wts-tv-ohlc" id="wtsTvOhlc"><b id="wtsTvLast">-</b><span>시 -</span><span>고 -</span><span>저 -</span><span>종 -</span></div><div class="wts-tv-box" id="chartBox"><div class="wts-tv-loading">과거봉을 불러오는 중입니다.</div></div><div class="wts-tv-state"><span id="wtsTvState">과거봉 Databento · 현재가 Databento Live 우선</span><span id="wtsTvUpdated"></span></div></div>`;
    wrap.querySelectorAll('[data-tv-tf]').forEach(b=>b.onclick=()=>{tf=Number(b.dataset.tvTf)||1;drawChart()});
    wrap.querySelector('#wtsTvReload').onclick=()=>drawChart();
    return wrap.querySelector('#chartBox');
  }
  function showBar(b){const root=document.querySelector('.wts-tv');if(!root||!b)return;root.querySelector('#wtsTvOhlc').innerHTML=`<b id="wtsTvLast">${fmt(b.c)}</b><span>시 ${fmt(b.o)}</span><span>고 ${fmt(b.h)}</span><span>저 ${fmt(b.l)}</span><span>종 ${fmt(b.c)}</span>`;root.querySelector('#wtsTvUpdated').textContent='마지막 '+new Date(b.t).toLocaleTimeString('ko-KR',{hour12:false})}
  async function liveUpdate(code){try{const r=await api(FEED,{action:'quote',code});if(cur.code!==code||page!=='trade'||tab!=='chart')return;const q=r?.quote||r?.data||r,v=Number(q?.ld),qt=Number(q?.t||Date.now());if(!Number.isFinite(v)||!candleSeries)return;const age=Date.now()-qt;setConn(age>5000?'Databento 폴백':'Databento Live',age>5000);const mins=tfMinutes[Number(tf)]||1,bt=Math.floor(qt/(mins*60000))*(mins*60000);let b=lastBars[lastBars.length-1];if(!b)return;if(bt>Math.floor(b.t/(mins*60000))*(mins*60000)){b={t:bt,o:v,h:v,l:v,c:v,v:0};lastBars.push(b)}else{b={...b,t:bt,h:Math.max(b.h,v),l:Math.min(b.l,v),c:v};lastBars[lastBars.length-1]=b}candleSeries.update({time:Math.floor(b.t/1000),open:b.o,high:b.h,low:b.l,close:b.c});showBar(b)}catch(_e){setConn('연결 지연',true)}}

  drawChart=async function(){
    if(page!=='trade'||tab!=='chart')return;
    cleanup();
    const box=shell();if(!box)return;
    if(String(cur?.code||'').toUpperCase()==='HSI'){box.innerHTML='<div class="wts-tv-loading"><b>현재 점검중인 종목입니다.</b></div>';return}
    const code=cur.code,symbol=cur.symbol;
    try{
      const LC=await ensureLC();
      const r=await api(FEED,{action:'kline',code,kType:Number(tf)||1,limit:3000});
      if(cur.code!==code||page!=='trade'||tab!=='chart')return;
      const bars=normalize(r?.bars);if(!bars.length)throw new Error('과거봉 데이터가 없습니다.');lastBars=bars;
      box.innerHTML='';
      chart=LC.createChart(box,{width:Math.max(1,box.clientWidth),height:Math.max(260,box.clientHeight),layout:{background:{type:'solid',color:'#fff'},textColor:'#4b5563',fontSize:12,fontFamily:'Arial, sans-serif'},grid:{vertLines:{color:'#eef1f5'},horzLines:{color:'#eef1f5'}},rightPriceScale:{borderColor:'#dfe3e8',scaleMargins:{top:.08,bottom:.24}},timeScale:{borderColor:'#dfe3e8',timeVisible:true,secondsVisible:false,rightOffset:3,barSpacing:9,minBarSpacing:3},crosshair:{mode:LC.CrosshairMode?.Normal??0},localization:{locale:'ko-KR'}});
      candleSeries=chart.addCandlestickSeries({upColor:'#ef5350',downColor:'#2196f3',borderUpColor:'#ef5350',borderDownColor:'#2196f3',wickUpColor:'#ef5350',wickDownColor:'#2196f3',priceLineVisible:true,lastValueVisible:true});
      candleSeries.setData(bars.map(b=>({time:Math.floor(b.t/1000),open:b.o,high:b.h,low:b.l,close:b.c})));
      volumeSeries=chart.addHistogramSeries({priceFormat:{type:'volume'},priceScaleId:'vol'});chart.priceScale('vol').applyOptions({scaleMargins:{top:.78,bottom:0}});volumeSeries.setData(bars.map(b=>({time:Math.floor(b.t/1000),value:b.v,color:b.c>=b.o?'rgba(239,83,80,.45)':'rgba(33,150,243,.45)'})));
      chart.timeScale().fitContent();showBar(bars[bars.length-1]);
      const root=document.querySelector('.wts-tv');if(root){setConn('Databento 연결');root.querySelector('#wtsTvState').textContent=`${symbol} · 과거봉 Databento · 현재가 Databento Live 우선 · ${bars.length}봉`;}
      resizeObs=new ResizeObserver(()=>{if(chart){const w=Math.max(1,box.clientWidth),h=Math.max(260,box.clientHeight);chart.applyOptions({width:w,height:h})}});resizeObs.observe(box);
      liveTimer=setInterval(()=>{if(!document.hidden)liveUpdate(code)},1500);
    }catch(e){box.innerHTML=`<div class="wts-tv-loading"><div><b>과거봉을 불러오지 못했습니다.</b><br>${String(e?.message||e)}</div></div>`;setConn('연결 오류',true);}
  };
  window.drawChart=drawChart;
})();