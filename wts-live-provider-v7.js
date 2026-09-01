(()=>{
  if(window.__VELTRO_LIVE_PROVIDER_V7__)return;
  window.__VELTRO_LIVE_PROVIDER_V7__=true;
  const FEED='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/wts-market-feed';
  let provider='';
  const baseApi=window.api;
  if(typeof baseApi==='function'){
    window.api=async function(url,body,auth=true,retry=true){
      const r=await baseApi(url,body,auth,retry);
      if(url===FEED&&String(body?.action||'')==='quote'){
        provider=String(r?.provider||r?.quote?.provider||'');
        window.__VELTRO_QUOTE_PROVIDER__=provider;
        paint();
      }
      return r;
    };
    try{api=window.api}catch{}
  }
  function paint(){
    const state=document.querySelector('#wtsTvState'),conn=document.querySelector('#wtsTvConn');
    if(provider==='databento_live'){
      if(state)state.textContent=`${cur?.symbol||''} · 과거봉 Databento · 현재가 Databento Live`;
      if(conn){conn.textContent='연결됨 · Databento Live';conn.classList.remove('stale')}
    }else if(provider==='databento_historical_fallback'){
      if(state)state.textContent=`${cur?.symbol||''} · 과거봉 Databento · 현재가 Databento 최신 1분봉(폴백)`;
      if(conn){conn.textContent='Live 대기 · Databento 폴백';conn.classList.add('stale')}
    }
  }
  new MutationObserver(paint).observe(document.documentElement,{childList:true,subtree:true});
  setInterval(paint,1000);
})();
