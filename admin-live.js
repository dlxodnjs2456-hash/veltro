(()=>{
  let alarmTimer=null, audioCtx=null, acknowledgedKey='';
  const requestKey=(d)=>{
    const deps=(d?.deposits||[]).filter(x=>['pending','confirm_requested'].includes(x.status)).map(x=>`D${x.id}:${x.status}`).sort();
    const wds=(d?.withdrawals||[]).filter(x=>x.status==='pending').map(x=>`W${x.id}`).sort();
    return [...deps,...wds].join('|');
  };
  const counts=(d)=>({
    dep:(d?.deposits||[]).filter(x=>['pending','confirm_requested'].includes(x.status)).length,
    wd:(d?.withdrawals||[]).filter(x=>x.status==='pending').length
  });
  function ensureAudio(){try{if(!audioCtx)audioCtx=new (window.AudioContext||window.webkitAudioContext)();if(audioCtx.state==='suspended')audioCtx.resume();}catch{}}
  function beep(){try{ensureAudio();if(!audioCtx)return;const now=audioCtx.currentTime;[0,.22,.44].forEach((off,i)=>{const o=audioCtx.createOscillator(),g=audioCtx.createGain();o.type='square';o.frequency.value=i%2?880:660;g.gain.setValueAtTime(.0001,now+off);g.gain.exponentialRampToValueAtTime(.13,now+off+.01);g.gain.exponentialRampToValueAtTime(.0001,now+off+.15);o.connect(g).connect(audioCtx.destination);o.start(now+off);o.stop(now+off+.17);});}catch{}}
  function stopAlarm(){if(alarmTimer){clearInterval(alarmTimer);alarmTimer=null;}}
  function startAlarm(){if(alarmTimer)return;beep();alarmTimer=setInterval(beep,2800);}
  function banner(){let el=document.getElementById('requestAlarmBanner');if(el)return el;el=document.createElement('div');el.id='requestAlarmBanner';el.style.cssText='position:fixed;top:48px;right:18px;z-index:9999;background:#fff4f2;border:1px solid #e14f43;box-shadow:0 4px 16px rgba(0,0,0,.18);padding:11px 13px;min-width:320px;font:12px Arial,Malgun Gothic,sans-serif;display:none';el.innerHTML='<b style="color:#c8352e">처리 대기 요청이 있습니다.</b><div id="requestAlarmText" style="margin-top:5px;color:#444"></div><button id="requestAlarmAck" style="margin-top:8px;height:28px;border:0;background:#e14f43;color:#fff;padding:0 12px;cursor:pointer">알림 확인</button>';document.body.appendChild(el);el.querySelector('#requestAlarmAck').onclick=()=>{acknowledgedKey=requestKey(window.data);stopAlarm();el.style.display='none';};return el;}
  function updateBadges(d){const c=counts(d);[['deposits',c.dep],['withdrawals',c.wd]].forEach(([p,n])=>{const b=document.querySelector(`.nav[data-page="${p}"]`);if(!b)return;let s=b.querySelector('.live-badge');if(!s){s=document.createElement('span');s.className='live-badge';s.style.cssText='float:right;background:#e14f43;color:#fff;min-width:18px;height:18px;line-height:18px;text-align:center;border-radius:9px;font-size:10px;margin-top:10px';b.appendChild(s);}s.textContent=n;s.style.display=n?'inline-block':'none';});}
  function handleAlarm(d){const key=requestKey(d),c=counts(d),el=banner();updateBadges(d);if(key&&key!==acknowledgedKey){el.style.display='block';el.querySelector('#requestAlarmText').textContent=`충전 ${c.dep}건 / 출금 ${c.wd}건 처리 대기`;startAlarm();}else if(!key){stopAlarm();el.style.display='none';acknowledgedKey='';}}
  async function refreshLive(){try{if(!window.token)return;const next=await window.post(window.ADMIN,{action:'dashboard'},true);window.data=next;handleAlarm(next);const active=document.activeElement;const editing=active&&['INPUT','TEXTAREA','SELECT'].includes(active.tagName);const modalOpen=document.querySelector('.modal-mask');if(!editing&&!modalOpen&&['deposits','withdrawals','money','performance'].includes(window.page))window.render();}catch(e){console.warn('admin live refresh failed',e);}}
  document.addEventListener('pointerdown',ensureAudio,{once:true,capture:true});
  const boot=setInterval(()=>{if(window.token){clearInterval(boot);refreshLive();setInterval(refreshLive,5000);}},500);
})();
