from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old = "async function startTimers(){timers.forEach(clearInterval);timers=[setInterval(async()=>{if(!token||document.hidden)return;try{await loadQuote();if(page==='trade')refreshLiveTrade()}catch(e){console.warn('quote poll',e)}},2000),setInterval(async()=>{if(!token||document.hidden)return;try{await Promise.all([loadTrading(),loadDash()]);pollOpenOrderQuotes();if(page!=='trade'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))renderAll()}catch(e){console.warn('account poll',e)}},5000),setInterval(()=>{if(page==='trade'&&tab==='chart'&&!document.hidden)drawChart()},30000)]}"

new = r'''let pollStop=false,quoteTimer=null,accountTimer=null,chartTimer=null;
function stopPollers(){
  pollStop=true;
  if(quoteTimer)clearTimeout(quoteTimer);
  if(accountTimer)clearTimeout(accountTimer);
  if(chartTimer)clearTimeout(chartTimer);
  quoteTimer=accountTimer=chartTimer=null;
}
async function quoteLoop(){
  if(pollStop||!token)return;
  if(!document.hidden){
    try{
      await loadQuote();
      if(page==='trade')refreshLiveTrade();
    }catch(e){console.warn('quote loop',e)}
  }
  if(!pollStop&&token)quoteTimer=setTimeout(quoteLoop,1500);
}
async function accountLoop(){
  if(pollStop||!token)return;
  if(!document.hidden){
    try{
      await Promise.all([loadTrading(),loadDash()]);
      await pollOpenOrderQuotes();
      if(page!=='trade'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))renderAll();
    }catch(e){console.warn('account loop',e)}
  }
  if(!pollStop&&token)accountTimer=setTimeout(accountLoop,5000);
}
async function chartLoop(){
  if(pollStop||!token)return;
  if(page==='trade'&&tab==='chart'&&!document.hidden){
    try{await drawChart()}catch(e){console.warn('chart loop',e)}
  }
  if(!pollStop&&token)chartTimer=setTimeout(chartLoop,30000);
}
function startTimers(){
  stopPollers();
  pollStop=false;
  quoteLoop();
  accountLoop();
  chartLoop();
}'''

if old not in s:
    raise SystemExit('old startTimers block not found')
s = s.replace(old, new, 1)

old_logout = "function logout(){timers.forEach(clearInterval);timers=[];clearPersistedSession();$('#app').classList.add('hidden');$('#login').classList.remove('hidden');$('#pw').value=''}"
new_logout = "function logout(){stopPollers();timers.forEach(clearInterval);timers=[];clearPersistedSession();$('#app').classList.add('hidden');$('#login').classList.remove('hidden');$('#pw').value=''}"
if old_logout in s:
    s = s.replace(old_logout, new_logout, 1)
else:
    raise SystemExit('logout block not found')

assert "setTimeout(quoteLoop,1500)" in s
assert "setTimeout(accountLoop,5000)" in s
assert "function stopPollers()" in s
assert "function startTimers()" in s
p.write_text(s, encoding='utf-8')
