(()=>{
  if(window.__VELTRO_WTS_RESPONSIVE_V4__)return;window.__VELTRO_WTS_RESPONSIVE_V4__=true;
  const s=document.createElement('style');
  s.textContent=`
  html,body,#app,.desktop,.grid,.work,#main,.trade,.card,.chart-wrap,.wts-tv,.wts-tv-box{min-width:0!important;max-width:100%!important}
  body{overflow-x:hidden!important}.work,.chart-wrap,.wts-tv{overflow:hidden!important}
  .wts-tv{height:100%!important;min-height:0!important}.wts-tv-box{width:100%!important;min-height:260px!important}
  .wts-tv-head{height:auto!important;min-height:44px!important;flex-wrap:wrap!important;white-space:normal!important;overflow:hidden!important}.wts-tv-head strong{min-width:0!important;max-width:65%!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important}.wts-tv-head .live{white-space:nowrap!important}
  .wts-tv-ohlc,.wts-tv-tfs{max-width:100%!important;overflow-x:auto!important;overflow-y:hidden!important}
  .trade{grid-template-rows:auto auto minmax(300px,1fr) minmax(140px,220px)!important}
  @media(max-width:1280px) and (min-width:821px){.grid{grid-template-columns:180px minmax(0,1fr) 240px!important}.grid.no-order{grid-template-columns:180px minmax(0,1fr)!important}.work{padding:7px!important}.right{padding:7px 7px 7px 0!important}.tabs{overflow-x:auto!important}.tabs button{min-width:68px!important}.last{font-size:21px!important}}
  @media(max-width:1024px) and (min-width:821px){.grid{grid-template-columns:155px minmax(0,1fr) 200px!important}.grid.no-order{grid-template-columns:155px minmax(0,1fr)!important}.tabs button{min-width:60px!important;font-size:11px!important}.wts-tv-head .live{width:100%!important;margin-left:0!important}.wts-tv-head strong{max-width:75%!important}.order{padding:8px!important}}
  @media(max-width:820px){.mobile,.m-main,.m-main .chart-wrap{width:100%!important;max-width:100vw!important;min-width:0!important;overflow-x:hidden!important}.m-main .chart-wrap,.wts-tv{height:calc(100dvh - 150px)!important;min-height:430px!important}.wts-tv-box{min-height:300px!important}.wts-tv-head strong{max-width:72%!important}.wts-tv-tfs .reload{margin-left:0!important}.market-head{min-width:0!important}.market-head>div:first-child{min-width:0!important;overflow:hidden!important}.market-head b,.market-head small{display:block!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important}.last{font-size:20px!important;white-space:nowrap!important}}
  `;document.head.appendChild(s);
  const forceResize=()=>{try{window.dispatchEvent(new Event('resize'))}catch{}};
  window.addEventListener('orientationchange',()=>setTimeout(forceResize,150));
  window.addEventListener('resize',()=>setTimeout(()=>{const b=document.querySelector('.wts-tv-box');if(b&&window.chart?.applyOptions)window.chart.applyOptions({width:Math.max(1,b.clientWidth),height:Math.max(260,b.clientHeight)})},30));
})();