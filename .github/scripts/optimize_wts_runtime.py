from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
s=s.replace(",chart=null,tf=1,timers=[];",",chart=null,tf=1;")
s=s.replace("function logout(){stopPollers();timers.forEach(clearInterval);timers=[];clearPersistedSession();$('#app').classList.add('hidden');$('#login').classList.remove('hidden');$('#pw').value=''}","function logout(){stopPollers();clearPersistedSession();$('#app').classList.add('hidden');$('#login').classList.remove('hidden');$('#pw').value=''}")
old="""async function quoteLoop(){
  if(pollStop||!token)return;
  if(!document.hidden){
    try{
      await loadQuote();
      if(page==='trade')refreshLiveTrade();
    }catch(e){console.warn('quote loop',e)}
  }
  if(!pollStop&&token)quoteTimer=setTimeout(quoteLoop,1500);
}"""
new="""async function quoteLoop(){
  if(pollStop||!token)return;
  if(!document.hidden){
    try{
      const beforeLast=lp(),beforeTs=Number(quote?.t||0);
      await loadQuote();
      const changed=lp()!==beforeLast||Number(quote?.t||0)!==beforeTs;
      if(page==='trade'&&changed)refreshLiveTrade();
    }catch(e){console.warn('quote loop',e)}
  }
  if(!pollStop&&token)quoteTimer=setTimeout(quoteLoop,1200);
}"""
if old not in s: raise SystemExit('quote loop block not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
