(()=>{
  if(window.__VELTRO_WTS_HOTFIX_V2__) return;
  window.__VELTRO_WTS_HOTFIX_V2__=true;
  const FEED='https://mzjkvakigwtlibwlslhq.supabase.co/functions/v1/market-data-api';
  const isHsi=i=>String(i?.code||'').toUpperCase()==='HSI';
  let quoteSeq=0;

  const style=document.createElement('style');
  style.textContent=`
  #signupBtn{background:#fff!important;color:#1687d9!important;border:1px solid #b8d8ee!important;margin-top:8px!important}
  .drawer{overflow-y:auto!important;overflow-x:hidden!important;-webkit-overflow-scrolling:touch!important;overscroll-behavior:contain!important;padding-bottom:calc(40px + env(safe-area-inset-bottom))!important}
  .m-bottom{grid-template-columns:repeat(4,1fr)!important;height:58px!important}
  .m-bottom button{font-size:11px!important;padding:0 3px!important}
  .m-bottom .mbuy{background:#d84d48!important}.m-bottom .msell{background:#2d66c9!important}
  .m-tabs button.active{background:#1970a6!important;color:#fff!important;font-weight:900!important;border-bottom:3px solid #38bdf8!important}
  `;
  document.head.appendChild(style);

  const loginCard=document.querySelector('.login-card');
  if(loginCard && !document.getElementById('signupBtn')){
    const b=document.createElement('button');
    b.id='signupBtn'; b.type='button'; b.textContent='회원가입';
    b.onclick=()=>{location.href='/signup.html'};
    const msg=document.getElementById('loginMsg');
    loginCard.insertBefore(b,msg||null);
  }

  function syncTabs(){
    document.querySelectorAll('#mTabs [data-tab]').forEach(x=>x.classList.toggle('active',page==='trade'&&x.dataset.tab===tab));
  }
  function syncBottom(){
    const nav=document.querySelector('.m-bottom'); if(!nav) return;
    if(nav.dataset.v2==='1') return;
    nav.dataset.v2='1';
    nav.innerHTML=`<button class="mbuy" data-mtype="MARKET" data-mside="BUY">시장가 매수</button><button class="msell" data-mtype="MARKET" data-mside="SELL">시장가 매도</button><button class="mbuy" data-mtype="LIMIT" data-mside="BUY">지정가 매수</button><button class="msell" data-mtype="LIMIT" data-mside="SELL">지정가 매도</button>`;
  }
  async function mobileSideOrder(type,side){
    try{
      if(isHsi(cur)){toast('현재 점검중인 종목입니다.');return;}
      const q=Math.max(1,Number(prompt('주문 수량','1')||0)); if(!q)return;
      let price=lp();
      if(type==='LIMIT') price=Number(prompt('지정가',String(lp()))||0);
      if(!Number.isFinite(price)||price<=0) throw Error('현재가를 확인할 수 없습니다.');
      await api(TRADING,{action:'submit_order',symbol:cur.symbol,side,order_type:type,qty:q,price});
      await loadTrading();renderAll();toast(`${side==='BUY'?'매수':'매도'} 주문 처리 완료`);
    }catch(e){toast('주문 실패: '+e.message)}
  }

  const originalRender=window.renderAll||renderAll;
  renderAll=function(){
    originalRender();
    syncTabs();syncBottom();
  };
  window.renderAll=renderAll;

  const originalLoadQuote=window.loadQuote||loadQuote;
  loadQuote=async function(){
    if(isHsi(cur)){quote=null;return;}
    const seq=++quoteSeq, code=cur.code;
    try{
      const r=await api(FEED,{action:'quote',code});
      if(seq===quoteSeq && cur.code===code) quote=r.quote||r.data||r;
    }catch(e){
      if(seq===quoteSeq && cur.code===code) await originalLoadQuote();
    }
  };
  window.loadQuote=loadQuote;

  const originalDrawChart=window.drawChart||drawChart;
  drawChart=async function(){
    if(page!=='trade'||tab!=='chart'||!document.querySelector('#chartBox'))return;
    if(isHsi(cur)){document.querySelector('#chartBox').innerHTML='<div style="height:100%;display:grid;place-items:center;color:#667085">현재 점검중인 종목입니다.</div>';return;}
    try{
      const r=await api(FEED,{action:'kline',code:cur.code,kType:tf,limit:500});
      const bs=(r.bars||[]).map(b=>({t:Number(b.t??b.timestamp),o:Number(b.o??b.open),h:Number(b.h??b.high),l:Number(b.l??b.low),c:Number(b.c??b.close),v:Math.max(0,Number(b.v??b.volume??0))})).filter(b=>[b.t,b.o,b.h,b.l,b.c].every(Number.isFinite)).map(b=>({...b,t:b.t<1e12?b.t*1000:b.t})).sort((a,b)=>a.t-b.t);
      if(!bs.length) throw Error('chart_empty');
      if(chart){try{chart.destroy()}catch{}chart=null}
      const up='#d84d48',down='#2d66c9',ohlc=bs.map(b=>[b.t,b.o,b.h,b.l,b.c]),vol=bs.map(b=>({x:b.t,y:b.v,color:b.c>=b.o?'rgba(216,77,72,.48)':'rgba(45,102,201,.48)'}));
      chart=Highcharts.stockChart('chartBox',{chart:{animation:false,panning:{enabled:true,type:'x'},zooming:{type:'x'}},rangeSelector:{inputEnabled:false,selected:4},navigator:{enabled:true},scrollbar:{enabled:true},xAxis:{ordinal:false},yAxis:[{height:'72%'},{top:'75%',height:'25%',offset:0,title:{text:'VOL'}}],series:[{type:'candlestick',id:'price',name:cur.symbol,data:ohlc,dataGrouping:{enabled:false},upColor:up,upLineColor:up,color:down,lineColor:down,lastPrice:{enabled:true,color:'#1687d9'}},{type:'column',name:'Volume',data:vol,yAxis:1,dataGrouping:{enabled:false}},{type:'sma',linkedTo:'price',params:{period:20},name:'SMA20'}]});
      const t=document.querySelector('#tf');if(t){t.value=String(tf);t.onchange=()=>{tf=Number(t.value);drawChart()}}
      const cr=document.querySelector('#chartReload');if(cr)cr.onclick=drawChart;
      const cs=document.querySelector('#chartState');if(cs)cs.textContent='시장 시세 · '+bs.length+'봉';
    }catch(e){try{await originalDrawChart()}catch{const box=document.querySelector('#chartBox');if(box)box.innerHTML='<div style="padding:40px;color:#c33">차트 조회 실패</div>'}}
  };
  window.drawChart=drawChart;

  document.addEventListener('click',e=>{
    const tabBtn=e.target.closest?.('#mTabs [data-tab]');
    if(tabBtn){e.preventDefault();e.stopImmediatePropagation();page='trade';tab=tabBtn.dataset.tab;renderAll();closeDrawer();return;}
    const symBtn=e.target.closest?.('[data-symbol]');
    if(symBtn){
      const n=INS.find(i=>i.symbol===symBtn.dataset.symbol);if(!n)return;
      e.preventDefault();e.stopImmediatePropagation();
      if(isHsi(n)){toast('현재 점검중인 종목입니다.');closeDrawer();return;}
      cur=n;page='trade';quote=null;quoteSeq++;renderAll();closeDrawer();
      const selected=n.symbol;
      loadQuote().then(()=>{if(cur.symbol===selected)refreshLiveTrade()}).catch(()=>{});
      return;
    }
    const ob=e.target.closest?.('.m-bottom [data-mtype][data-mside]');
    if(ob){e.preventDefault();e.stopImmediatePropagation();mobileSideOrder(ob.dataset.mtype,ob.dataset.mside);return;}
  },true);

  syncTabs();syncBottom();
})();