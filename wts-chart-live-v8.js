(()=>{
  if(window.__VELTRO_CHART_LIVE_V8__)return;
  window.__VELTRO_CHART_LIVE_V8__=true;

  // wts-chart-v3 already records genuine Databento Live quotes into the
  // active OHLC candle every 1.5s and creates a new candle on bucket rollover.
  // Do not let the slower full-history resync replace that forming candle.
  if(typeof chartLoop==='function'){
    chartLoop=async function(){
      if(pollStop||!token)return;
      // Historical data is loaded when the chart opens, timeframe/symbol changes,
      // or the user presses refresh. While open, liveUpdate owns the forming bars.
      if(!pollStop&&token)chartTimer=setTimeout(chartLoop,120000);
    };
    window.chartLoop=chartLoop;
  }
})();
