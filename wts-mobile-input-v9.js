(()=>{
  if(window.__VELTRO_MOBILE_INPUT_V9__) return;
  window.__VELTRO_MOBILE_INPUT_V9__=true;

  const isMobile=()=>window.innerWidth<=820 || /VELTRO-Android|Android|iPhone|iPad|iPod/i.test(navigator.userAgent||'');
  const numericIds=new Set(['oq','dep','ca','wa']);
  const decimalIds=new Set(['op']);

  function apply(el){
    if(!isMobile()||!el||el.tagName!=='INPUT') return;
    const id=String(el.id||'');
    if(numericIds.has(id)){
      // Android WebView/mobile browsers are more reliable with text+inputmode than type=number.
      if(el.type==='number') el.type='text';
      el.inputMode='numeric';
      el.setAttribute('inputmode','numeric');
      el.setAttribute('pattern','[0-9]*');
      el.setAttribute('autocomplete','off');
      el.setAttribute('autocorrect','off');
      el.setAttribute('spellcheck','false');
      return;
    }
    if(decimalIds.has(id)){
      if(el.type==='number') el.type='text';
      el.inputMode='decimal';
      el.setAttribute('inputmode','decimal');
      el.setAttribute('autocomplete','off');
      el.setAttribute('autocorrect','off');
      el.setAttribute('spellcheck','false');
    }
  }

  function scan(root=document){
    if(!isMobile()) return;
    root.querySelectorAll?.('input').forEach(apply);
  }

  document.addEventListener('focusin',e=>apply(e.target),true);
  const obs=new MutationObserver(ms=>{
    for(const m of ms){
      for(const n of m.addedNodes){
        if(n?.nodeType!==1) continue;
        if(n.tagName==='INPUT') apply(n);
        scan(n);
      }
    }
  });
  obs.observe(document.documentElement,{childList:true,subtree:true});
  window.addEventListener('resize',()=>scan());
  scan();
})();
