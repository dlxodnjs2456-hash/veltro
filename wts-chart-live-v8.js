(()=>{
  if(window.__VELTRO_CHART_LIVE_V8__)return;
  window.__VELTRO_CHART_LIVE_V8__=true;

  // Bound only heavy aggregated history requests. The backend still builds every
  // candle from genuine Databento 1-minute OHLCV; no price scaling/synthesis.
  if(typeof api==='function'){
    const baseChartApi=api;
    api=async function(url,body,auth=true,retry=true){
      if(String(body?.action||'')==='kline'){
        const k=Number(body?.kType||1);
        if(k===3 && Number(body?.limit||0)>1000) body={...body,limit:1000};
        if(k===5 && Number(body?.limit||0)>500) body={...body,limit:500};
      }
      return baseChartApi(url,body,auth,retry);
    };
    window.api=api;
  }

  // wts-chart-v3 records genuine Databento Live quotes into the active OHLC
  // candle every 1.5s and creates a new candle on bucket rollover. Do not let
  // the slower full-history resync replace that forming candle.
  if(typeof chartLoop==='function'){
    chartLoop=async function(){
      if(pollStop||!token)return;
      if(!pollStop&&token)chartTimer=setTimeout(chartLoop,120000);
    };
    window.chartLoop=chartLoop;
  }
})();
