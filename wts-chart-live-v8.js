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

  // Mobile numeric-input compatibility for both mobile WTS and Android MTS.
  const mobileInputMode=()=>window.innerWidth<=820 || /VELTRO-Android|Android|iPhone|iPad|iPod/i.test(navigator.userAgent||'');
  const integerIds=new Set(['oq','dep','ca','wa']);
  const decimalIds=new Set(['op']);
  let mobileEditing=false, editReleaseTimer=null;

  function isEditable(el){return !!el && ['INPUT','TEXTAREA','SELECT'].includes(el.tagName);}

  function patchMobileInput(el){
    if(!mobileInputMode()||!el||el.tagName!=='INPUT')return;
    const id=String(el.id||'');
    if(integerIds.has(id)){
      if(el.type==='number')el.type='text';
      el.inputMode='numeric';
      el.setAttribute('inputmode','numeric');
      el.setAttribute('pattern','[0-9]*');
      el.setAttribute('autocomplete','off');
      el.setAttribute('autocorrect','off');
      el.setAttribute('spellcheck','false');
    }else if(decimalIds.has(id)){
      if(el.type==='number')el.type='text';
      el.inputMode='decimal';
      el.setAttribute('inputmode','decimal');
      el.setAttribute('autocomplete','off');
      el.setAttribute('autocorrect','off');
      el.setAttribute('spellcheck','false');
    }
  }

  function scanMobileInputs(root=document){
    if(!mobileInputMode())return;
    root.querySelectorAll?.('input').forEach(patchMobileInput);
  }

  // Android/iOS soft keyboards resize the visual viewport. The base app has a
  // window.resize -> renderAll() handler; re-rendering while an input is focused
  // destroys that DOM node and immediately closes the keyboard. Guard renderAll
  // during mobile text entry, including a short blur grace period for WebView.
  if(typeof renderAll==='function'){
    const renderAllBeforeMobileGuard=renderAll;
    renderAll=function(){
      if(mobileInputMode() && (mobileEditing || isEditable(document.activeElement))) return;
      return renderAllBeforeMobileGuard();
    };
    window.renderAll=renderAll;
  }

  document.addEventListener('focusin',e=>{
    if(!mobileInputMode()||!isEditable(e.target))return;
    if(editReleaseTimer){clearTimeout(editReleaseTimer);editReleaseTimer=null;}
    mobileEditing=true;
    patchMobileInput(e.target);
  },true);

  document.addEventListener('focusout',()=>{
    if(!mobileInputMode())return;
    if(editReleaseTimer)clearTimeout(editReleaseTimer);
    editReleaseTimer=setTimeout(()=>{mobileEditing=false;editReleaseTimer=null;},350);
  },true);

  const inputObserver=new MutationObserver(mutations=>{
    for(const m of mutations){for(const n of m.addedNodes){if(n?.nodeType!==1)continue;if(n.tagName==='INPUT')patchMobileInput(n);scanMobileInputs(n);}}
  });
  inputObserver.observe(document.documentElement,{childList:true,subtree:true});
  window.addEventListener('resize',()=>scanMobileInputs());
  if(window.visualViewport) window.visualViewport.addEventListener('resize',()=>scanMobileInputs());
  scanMobileInputs();
})();
