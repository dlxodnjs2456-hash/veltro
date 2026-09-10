(()=>{
  if(window.__VELTRO_ORDER_CONFIRM_V9__)return;
  window.__VELTRO_ORDER_CONFIRM_V9__=true;
  let mobileOrderBusy=false;

  async function safeMobileOrder(type){
    if(mobileOrderBusy)return;
    const rawQty=prompt('주문 수량을 입력하세요.','1');
    if(rawQty===null)return;
    const qty=Number(rawQty);
    if(!Number.isFinite(qty)||qty<=0){toast('주문 수량을 확인해주세요.');return}

    const rawSide=prompt('주문 방향을 입력하세요.\n매수 = BUY 또는 매수\n매도 = SELL 또는 매도\n취소하려면 취소 버튼을 누르세요.','매수');
    if(rawSide===null)return;
    const sideText=String(rawSide).trim().toUpperCase();
    const side=(sideText==='BUY'||sideText==='매수')?'BUY':(sideText==='SELL'||sideText==='매도')?'SELL':null;
    if(!side){toast('주문 방향을 확인해주세요.');return}

    let price=lp();
    if(type==='LIMIT'){
      const rawPrice=prompt('지정가를 입력하세요.',String(lp()));
      if(rawPrice===null)return;
      price=Number(rawPrice);
    }
    if(!Number.isFinite(Number(price))||Number(price)<=0){toast('주문 가격을 확인해주세요.');return}

    const sideKo=side==='BUY'?'매수':'매도';
    const orderKo=type==='LIMIT'?'지정가':'시장가';
    const ok=confirm(`${cur.symbol}\n${sideKo} ${qty}계약 · ${orderKo}\n\n체결을 진행하시겠습니까?\n취소를 누르면 주문은 전송되지 않습니다.`);
    if(!ok)return;

    mobileOrderBusy=true;
    try{
      const r=await api(TRADING,{action:'submit_order',symbol:cur.symbol,side,order_type:type,qty,price:Number(price)});
      await loadTrading();
      renderAll();
      toast(r?.filled===false?'지정가 주문이 접수되었습니다.':'주문이 체결되었습니다.');
    }catch(e){
      toast(e?.message==='action_in_progress'?'주문 처리 중입니다.':'주문 실패: '+(e?.message||'request_failed'));
    }finally{
      mobileOrderBusy=false;
    }
  }

  window.mobileOrder=safeMobileOrder;
})();
