(()=>{
  if(window.__VELTRO_RUNTIME_V6__)return;
  window.__VELTRO_RUNTIME_V6__=true;
  const FEED='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/market-data-api';
  const quoteCache=new Map(),quoteInflight=new Map(),actionInflight=new Map(),pxBySymbol=new Map(),quoteMetaByCode=new Map();
  let renewInflight=null,posTimer=null,posBusy=false,resizeTimer=null,connTimer=null;
  const validPx=v=>{v=Number(v);return Number.isFinite(v)&&v>0?v:null};
  const instrument=s=>INS.find(x=>x.symbol===s)||null;
  const isHsi=i=>String(i?.code||'').toUpperCase()==='HSI';
  const hsiContract=INS.find(x=>String(x?.code||'').toUpperCase()==='HSI');if(hsiContract){hsiContract.symbol='HSIU26';hsiContract.month='202609'}

  function ensureConn(){let el=document.querySelector('#veltroConnState');if(el)return el;el=document.createElement('div');el.id='veltroConnState';el.style.cssText='position:fixed;right:10px;top:58px;z-index:80;padding:5px 8px;border-radius:6px;font:700 10px Arial,"Malgun Gothic",sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.12);display:none;pointer-events:none';document.body.appendChild(el);return el}
  function paintConn(){const el=ensureConn();if(!token){el.style.display='none';return}const metas=[...quoteMetaByCode.values()],newest=metas.length?Math.max(...metas.map(x=>Number(x.at)||0)):0,age=newest?Date.now()-newest:Infinity;if(!navigator.onLine){el.textContent='네트워크 연결 없음';el.style.background='#fff1f0';el.style.color='#b42318';el.style.display='block';return}if(age>15000){el.textContent='시세 연결 지연 · 마지막 값 유지';el.style.background='#fff7e6';el.style.color='#b54708';el.style.display='block';return}el.style.display='none'}

  const baseApi=api;
  api=async function(url,body,auth=true,retry=true){
    const act=String(body?.action||'');
    if(url===FEED&&act==='quote'){
      const code=String(body?.code||'').toUpperCase(),now=Date.now(),hit=quoteCache.get(code);
      if(hit&&now-hit.at<700)return hit.value;
      if(quoteInflight.has(code))return quoteInflight.get(code);
      const p=baseApi(url,body,auth,retry).then(v=>{const q=v?.quote||v?.data||v,px=validPx(q?.ld??q?.last??q?.price);if(px!=null){quoteCache.set(code,{at:Date.now(),value:v});quoteMetaByCode.set(code,{at:Date.now(),marketAt:Number(q?.t)||Date.now()});paintConn()}return v}).catch(e=>{const stale=quoteCache.get(code);paintConn();if(stale?.value)return stale.value;throw e}).finally(()=>quoteInflight.delete(code));
      quoteInflight.set(code,p);return p;
    }
    if(url===TRADING&&['submit_order','close_position','cancel_order','set_overnight'].includes(act)){
      const key=act+'|'+String(body?.position_id??body?.order_id??body?.symbol??'')+'|'+String(body?.side??'')+'|'+String(body?.order_type??'')+'|'+String(body?.qty??'')+'|'+String(body?.price??'');
      if(actionInflight.has(key))return actionInflight.get(key);
      const p=baseApi(url,body,auth,retry).finally(()=>actionInflight.delete(key));actionInflight.set(key,p);return p;
    }
    return baseApi(url,body,auth,retry);
  };
  window.api=api;

  if(typeof renewSession==='function'){
    const baseRenew=renewSession;
    renewSession=async function(){if(renewInflight)return renewInflight;renewInflight=Promise.resolve().then(()=>baseRenew()).finally(()=>{renewInflight=null});return renewInflight};
    window.renewSession=renewSession;
  }

  function currentPx(symbol){if(symbol===cur?.symbol){const v=validPx(quote?.ld??quote?.last??quote?.price);if(v!=null){pxBySymbol.set(symbol,v);return v}}return validPx(pxBySymbol.get(symbol))}
  async function fetchSymbol(symbol){const i=instrument(symbol);if(!i||isHsi(i))return null;try{const r=await api(FEED,{action:'quote',code:i.code}),q=r?.quote||r?.data||r,v=validPx(q?.ld??q?.last??q?.price);if(v!=null)pxBySymbol.set(symbol,v);return v}catch{return currentPx(symbol)}}

  pnl=function(p){const i=instrument(p.symbol)||cur,px=currentPx(p.symbol);if(px==null)return null;const entry=Number(p.avg_entry),qty=Number(p.qty),tick=Number(i?.tick||1),tickValue=Number(i?.tickValue||0);if(!Number.isFinite(entry)||!Number.isFinite(qty)||!tick)return null;const ticks=(String(p.side).toUpperCase()==='BUY'?px-entry:entry-px)/tick;return Math.round(ticks*tickValue*qty)};window.pnl=pnl;

  positions=function(){const rows=(trading.positions||[]).map(p=>{const i=instrument(p.symbol)||cur,v=pnl(p),px=currentPx(p.symbol),id=String(p.id);return `<tr data-pos-id="${id}"><td>${String(p.side).toUpperCase()==='BUY'?'매수':'매도'}</td><td>${p.symbol}</td><td>${p.qty}</td><td>${pf(p.avg_entry,i)}</td><td><span data-pos-price>${px==null?'-':pf(px,i)}</span></td><td class="${v==null?'':v>=0?'red':'blue'}" data-pos-pnl-cell><span data-pos-pnl>${v==null?'-':fmt(v)}</span></td><td><button class="mini danger" data-close="${p.id}">청산</button></td></tr>`}).join('');return `<table class="table"><thead><tr><th>구분</th><th>종목</th><th>수량</th><th>평단가</th><th>현재가</th><th>평가손익</th><th>기능</th></tr></thead><tbody>${rows||'<tr><td colspan="7" style="height:80px;color:#98a2b3">보유 포지션이 없습니다.</td></tr>'}</tbody></table>`};window.positions=positions;

  function patchPositionDom(){const ps=trading.positions||[],map=new Map(ps.map(p=>[String(p.id),p])),rows=[...document.querySelectorAll('tr[data-pos-id]')],expected=ps.length,uniqueRendered=new Set(rows.map(r=>r.dataset.posId)).size;if(uniqueRendered!==expected){document.querySelectorAll('.bottom').forEach(el=>el.innerHTML=positions());if(isMobile()&&page==='trade'&&tab==='positions'){const card=document.querySelector('#mMain .card');if(card)card.innerHTML=positions()}bind();return}rows.forEach(row=>{const p=map.get(String(row.dataset.posId));if(!p)return;const i=instrument(p.symbol)||cur,px=currentPx(p.symbol),v=pnl(p),pe=row.querySelector('[data-pos-price]'),ve=row.querySelector('[data-pos-pnl]'),cell=row.querySelector('[data-pos-pnl-cell]');if(pe)pe.textContent=px==null?'-':pf(px,i);if(ve)ve.textContent=v==null?'-':fmt(v);if(cell){cell.classList.toggle('red',v!=null&&v>=0);cell.classList.toggle('blue',v!=null&&v<0)}})}

  async function refreshPositionQuotes(){if(posBusy||!token)return;posBusy=true;try{const syms=[...new Set((trading.positions||[]).map(p=>p.symbol).filter(Boolean))];await Promise.all(syms.map(s=>s===cur?.symbol?Promise.resolve(currentPx(s)):fetchSymbol(s)));if(page==='trade')patchPositionDom()}finally{posBusy=false}}

  const baseLoadQuote=loadQuote;
  loadQuote=async function(){try{await baseLoadQuote()}catch(e){if(currentPx(cur?.symbol)==null)throw e}const v=validPx(quote?.ld??quote?.last??quote?.price);if(v!=null&&cur?.symbol)pxBySymbol.set(cur.symbol,v);paintConn();return quote};window.loadQuote=loadQuote;

  closePos=async function(id){if(!confirm('현재가 기준으로 해당 포지션을 청산할까요?'))return;try{const p=(trading.positions||[]).find(x=>String(x.id)===String(id));if(!p)throw Error('position_not_found');let price=currentPx(p.symbol);if(price==null)price=await fetchSymbol(p.symbol);if(price==null)throw Error('current_price_unavailable');await api(TRADING,{action:'close_position',position_id:id,price});await loadTrading();await refreshPositionQuotes();renderAll();toast('청산되었습니다.')}catch(e){toast(e.message==='action_in_progress'?'처리 중입니다.':'청산 실패: '+e.message)}};window.closePos=closePos;

  chartLoop=async function(){if(pollStop||!token)return;if(page==='trade'&&tab==='chart'&&!document.hidden){try{await drawChart()}catch(e){console.warn('chart resync',e)}}if(!pollStop&&token)chartTimer=setTimeout(chartLoop,120000)};window.chartLoop=chartLoop;

  const baseRenderAll=renderAll;
  renderAll=function(){if(window.__veltroResizeEvent){clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>baseRenderAll(),90);return}return baseRenderAll()};window.renderAll=renderAll;
  window.addEventListener('resize',()=>{window.__veltroResizeEvent=true;setTimeout(()=>{window.__veltroResizeEvent=false},0)},true);

  window.addEventListener('change',e=>{const el=e.target;if(el?.id!=='os')return;const i=instrument(el.value);if(!isHsi(i))return;el.value=cur?.symbol&&!isHsi(cur)?cur.symbol:(INS.find(x=>!isHsi(x))?.symbol||'NQU26');e.preventDefault();e.stopImmediatePropagation();toast('현재 점검중인 종목입니다.')},true);
  window.addEventListener('pointerdown',e=>{const b=e.target?.closest?.('[data-symbol]');if(!b)return;const i=instrument(b.dataset.symbol);if(!i||isHsi(i))return;api(FEED,{action:'quote',code:i.code}).catch(()=>{})},true);

  function startPositionTimer(){if(posTimer)clearInterval(posTimer);refreshPositionQuotes();posTimer=setInterval(()=>{if(!document.hidden)refreshPositionQuotes()},1800);if(connTimer)clearInterval(connTimer);connTimer=setInterval(paintConn,2500)}
  const baseStartTimers=startTimers;startTimers=function(){baseStartTimers();startPositionTimer()};window.startTimers=startTimers;
  const baseStopPollers=stopPollers;stopPollers=function(){if(posTimer){clearInterval(posTimer);posTimer=null}if(connTimer){clearInterval(connTimer);connTimer=null}baseStopPollers();paintConn()};window.stopPollers=stopPollers;

  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&token){loadQuote().then(()=>{refreshLiveTrade();refreshPositionQuotes();paintConn()}).catch(()=>paintConn())}});
  window.addEventListener('online',()=>{if(token){loadQuote().then(()=>{refreshLiveTrade();refreshPositionQuotes();paintConn()}).catch(()=>paintConn())}});
  window.addEventListener('offline',paintConn);
  if(token)startPositionTimer();
})();