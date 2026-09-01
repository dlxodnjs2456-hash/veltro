(()=>{
  if(window.__VELTRO_POSITION_QUOTES_V5__)return;
  window.__VELTRO_POSITION_QUOTES_V5__=true;
  const FEED='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/wts-market-feed';
  const pxBySymbol=new Map();
  let posTimer=null,posBusy=false;

  function instrument(symbol){return INS.find(x=>x.symbol===symbol)||null}
  function validPx(v){v=Number(v);return Number.isFinite(v)&&v>0?v:null}
  function currentPx(symbol){
    if(symbol===cur?.symbol){const v=validPx(quote?.ld??quote?.last??quote?.price);if(v!=null){pxBySymbol.set(symbol,v);return v}}
    return validPx(pxBySymbol.get(symbol));
  }
  async function fetchSymbol(symbol){
    const i=instrument(symbol);if(!i||String(i.code).toUpperCase()==='HSI')return null;
    try{const r=await api(FEED,{action:'quote',code:i.code});const q=r?.quote||r?.data||r;const v=validPx(q?.ld??q?.last??q?.price);if(v!=null)pxBySymbol.set(symbol,v);return v}catch{return null}
  }
  async function refreshPositionQuotes(){
    if(posBusy||!token)return;posBusy=true;
    try{
      const syms=[...new Set((trading.positions||[]).map(p=>p.symbol).filter(Boolean))];
      await Promise.all(syms.map(s=>s===cur?.symbol?Promise.resolve(currentPx(s)):fetchSymbol(s)));
      if(page==='trade'){
        document.querySelectorAll('.bottom').forEach(el=>el.innerHTML=positions());
        if(isMobile()&&tab==='positions'&&document.querySelector('#mMain'))document.querySelector('#mMain').innerHTML=mobile();
        bind();
      }
    }finally{posBusy=false}
  }

  pnl=function(p){
    const i=instrument(p.symbol)||cur;const px=currentPx(p.symbol);if(px==null)return null;
    const entry=Number(p.avg_entry),qty=Number(p.qty);if(!Number.isFinite(entry)||!Number.isFinite(qty))return null;
    const ticks=(String(p.side).toUpperCase()==='BUY'?px-entry:entry-px)/Number(i.tick||1);
    return Math.round(ticks*Number(i.tickValue||0)*qty);
  };
  window.pnl=pnl;

  positions=function(){
    const r=(trading.positions||[]).map(p=>{const i=instrument(p.symbol)||cur,v=pnl(p),px=currentPx(p.symbol);return `<tr><td>${String(p.side).toUpperCase()==='BUY'?'매수':'매도'}</td><td>${p.symbol}</td><td>${p.qty}</td><td>${pf(p.avg_entry,i)}</td><td>${px==null?'-':pf(px,i)}</td><td class="${v==null?'':v>=0?'red':'blue'}">${v==null?'-':fmt(v)}</td><td><button class="mini danger" data-close="${p.id}">청산</button></td></tr>`}).join('');return `<table class="table"><thead><tr><th>구분</th><th>종목</th><th>수량</th><th>평단가</th><th>현재가</th><th>평가손익</th><th>기능</th></tr></thead><tbody>${r||'<tr><td colspan="7" style="height:80px;color:#98a2b3">보유 포지션이 없습니다.</td></tr>'}</tbody></table>`;
  };
  window.positions=positions;

  const oldLoadQuote=loadQuote;
  loadQuote=async function(){await oldLoadQuote();const v=validPx(quote?.ld??quote?.last??quote?.price);if(v!=null&&cur?.symbol)pxBySymbol.set(cur.symbol,v)};
  window.loadQuote=loadQuote;

  closePos=async function(id){
    if(!confirm('현재가 기준으로 해당 포지션을 청산할까요?'))return;
    try{
      const p=(trading.positions||[]).find(x=>String(x.id)===String(id));if(!p)throw Error('position_not_found');
      let price=currentPx(p.symbol);if(price==null)price=await fetchSymbol(p.symbol);if(price==null)throw Error('current_price_unavailable');
      await api(TRADING,{action:'close_position',position_id:id,price});await loadTrading();await refreshPositionQuotes();renderAll();toast('청산되었습니다.');
    }catch(e){toast('청산 실패: '+e.message)}
  };
  window.closePos=closePos;

  function start(){if(posTimer)clearInterval(posTimer);refreshPositionQuotes();posTimer=setInterval(()=>{if(!document.hidden)refreshPositionQuotes()},1500)}
  const oldStartTimers=startTimers;
  startTimers=function(){oldStartTimers();start()};window.startTimers=startTimers;
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&token)refreshPositionQuotes()});
  if(token)start();
})();