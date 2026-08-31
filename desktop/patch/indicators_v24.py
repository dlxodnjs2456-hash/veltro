import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

anchor="let prefs=chartIndicatorPrefs();"
insert="""let prefs=chartIndicatorPrefs();
  const extraIndicatorDefaults={WMA:{enabled:false,params:[20]},BB:{enabled:false,params:[20,2]},VWAP:{enabled:false,params:[]},PSAR:{enabled:false,params:[0.02,0.2]},ICHIMOKU:{enabled:false,params:[9,26,52]},RSI:{enabled:false,params:[14]},MACD:{enabled:false,params:[12,26,9]},STOCH:{enabled:false,params:[14,3]},ATR:{enabled:false,params:[14]},CCI:{enabled:false,params:[20]},WILLR:{enabled:false,params:[14]},ROC:{enabled:false,params:[12]},MOM:{enabled:false,params:[10]},OBV:{enabled:false,params:[]}};
  for(const [k,v] of Object.entries(extraIndicatorDefaults)) if(!prefs[k]) prefs[k]=JSON.parse(JSON.stringify(v));"""
if anchor not in renderer: raise RuntimeError('indicator prefs anchor missing')
renderer=renderer.replace(anchor,insert,1)

old_panel="""<div class=\"ind-section\"><h4>메인 차트</h4>${indicatorRow('SMA','SMA 이동평균',['1','2','3'],prefs)}${indicatorRow('EMA','EMA 지수이동평균',['기간'],prefs)}${indicatorRow('BB','볼린저밴드',['기간','표준편차'],prefs)}</div>
      <div class=\"ind-section\"><h4>보조 지표</h4>${indicatorRow('VOL','거래량',[],prefs)}</div>"""
new_panel="""<div class=\"ind-section\"><h4>메인 차트</h4>${indicatorRow('SMA','SMA 이동평균',['1','2','3'],prefs)}${indicatorRow('EMA','EMA 지수이동평균',['기간'],prefs)}${indicatorRow('WMA','WMA 가중이동평균',['기간'],prefs)}${indicatorRow('BB','볼린저밴드',['기간','표준편차'],prefs)}${indicatorRow('VWAP','VWAP',[],prefs)}${indicatorRow('PSAR','Parabolic SAR',['가속','최대'],prefs)}${indicatorRow('ICHIMOKU','일목균형표',['전환','기준','선행B'],prefs)}</div>
      <div class=\"ind-section\"><h4>보조 지표</h4>${indicatorRow('VOL','거래량',[],prefs)}${indicatorRow('RSI','RSI',['기간'],prefs)}${indicatorRow('MACD','MACD',['단기','장기','시그널'],prefs)}${indicatorRow('STOCH','Stochastic',['K','D'],prefs)}${indicatorRow('ATR','ATR',['기간'],prefs)}${indicatorRow('CCI','CCI',['기간'],prefs)}${indicatorRow('WILLR','Williams %R',['기간'],prefs)}${indicatorRow('ROC','ROC',['기간'],prefs)}${indicatorRow('MOM','Momentum',['기간'],prefs)}${indicatorRow('OBV','OBV',[],prefs)}</div>"""
if old_panel not in renderer: raise RuntimeError('indicator panel anchor missing')
renderer=renderer.replace(old_panel,new_panel,1)

ema_anchor="""function ema(bars,p){const out=[];if(!bars.length)return out;const k=2/(p+1);let v=bars[0].c;for(let i=0;i<bars.length;i++){v=i?bars[i].c*k+v*(1-k):v;out.push({time:Math.floor(bars[i].t/1000),value:v});}return out;}"""
helpers=r'''function wma(bars,p){const out=[],den=p*(p+1)/2;for(let i=p-1;i<bars.length;i++){let s=0;for(let j=0;j<p;j++)s+=bars[i-p+1+j].c*(j+1);out.push({time:Math.floor(bars[i].t/1000),value:s/den});}return out;}
  function bbands(bars,p,mul){const up=[],mid=[],lo=[];for(let i=p-1;i<bars.length;i++){const a=bars.slice(i-p+1,i+1).map(x=>x.c),avg=a.reduce((s,x)=>s+x,0)/p,sd=Math.sqrt(a.reduce((s,x)=>s+(x-avg)*(x-avg),0)/p),time=Math.floor(bars[i].t/1000);mid.push({time,value:avg});up.push({time,value:avg+sd*mul});lo.push({time,value:avg-sd*mul});}return {up,mid,lo};}
  function vwap(bars){let pv=0,v=0;return bars.map(b=>{const vol=Math.max(0,b.v||0),tp=(b.h+b.l+b.c)/3;pv+=tp*vol;v+=vol;return {time:Math.floor(b.t/1000),value:v?pv/v:tp};});}
  function rsi(bars,p){const out=[];if(bars.length<=p)return out;let gain=0,loss=0;for(let i=1;i<=p;i++){const d=bars[i].c-bars[i-1].c;if(d>=0)gain+=d;else loss-=d;}gain/=p;loss/=p;for(let i=p;i<bars.length;i++){if(i>p){const d=bars[i].c-bars[i-1].c;gain=(gain*(p-1)+Math.max(d,0))/p;loss=(loss*(p-1)+Math.max(-d,0))/p;}const rs=loss===0?100:gain/loss;out.push({time:Math.floor(bars[i].t/1000),value:loss===0?100:100-(100/(1+rs))});}return out;}
  function atr(bars,p){const tr=[];for(let i=0;i<bars.length;i++){const prev=i?bars[i-1].c:bars[i].c;tr.push(Math.max(bars[i].h-bars[i].l,Math.abs(bars[i].h-prev),Math.abs(bars[i].l-prev)));}const out=[];let a=0;for(let i=0;i<tr.length;i++){if(i<p){a+=tr[i];if(i===p-1){a/=p;out.push({time:Math.floor(bars[i].t/1000),value:a});}}else{a=(a*(p-1)+tr[i])/p;out.push({time:Math.floor(bars[i].t/1000),value:a});}}return out;}
  function roc(bars,p){const out=[];for(let i=p;i<bars.length;i++)out.push({time:Math.floor(bars[i].t/1000),value:(bars[i].c/bars[i-p].c-1)*100});return out;}
  function momentum(bars,p){const out=[];for(let i=p;i<bars.length;i++)out.push({time:Math.floor(bars[i].t/1000),value:bars[i].c-bars[i-p].c});return out;}
  function obv(bars){let v=0;const out=[];for(let i=0;i<bars.length;i++){if(i){if(bars[i].c>bars[i-1].c)v+=bars[i].v||0;else if(bars[i].c<bars[i-1].c)v-=bars[i].v||0;}out.push({time:Math.floor(bars[i].t/1000),value:v});}return out;}
  function cci(bars,p){const out=[];for(let i=p-1;i<bars.length;i++){const a=bars.slice(i-p+1,i+1).map(x=>(x.h+x.l+x.c)/3),avg=a.reduce((s,x)=>s+x,0)/p,md=a.reduce((s,x)=>s+Math.abs(x-avg),0)/p,tp=a[a.length-1];out.push({time:Math.floor(bars[i].t/1000),value:md?((tp-avg)/(0.015*md)):0});}return out;}
  function willr(bars,p){const out=[];for(let i=p-1;i<bars.length;i++){const a=bars.slice(i-p+1,i+1),hh=Math.max(...a.map(x=>x.h)),ll=Math.min(...a.map(x=>x.l));out.push({time:Math.floor(bars[i].t/1000),value:hh===ll?0:-100*(hh-bars[i].c)/(hh-ll)});}return out;}
  function stochastic(bars,p,dn){const k=[];for(let i=p-1;i<bars.length;i++){const a=bars.slice(i-p+1,i+1),hh=Math.max(...a.map(x=>x.h)),ll=Math.min(...a.map(x=>x.l)),val=hh===ll?50:100*(bars[i].c-ll)/(hh-ll);k.push({time:Math.floor(bars[i].t/1000),value:val});}const d=[];for(let i=dn-1;i<k.length;i++)d.push({time:k[i].time,value:k.slice(i-dn+1,i+1).reduce((s,x)=>s+x.value,0)/dn});return {k,d};}
  function macd(bars,fast,slow,signal){const ef=ema(bars,fast),es=ema(bars,slow),sm=new Map(es.map(x=>[x.time,x.value])),m=ef.filter(x=>sm.has(x.time)).map(x=>({time:x.time,value:x.value-sm.get(x.time)}));const fake=m.map(x=>({t:x.time*1000,c:x.value})),sig=ema(fake,signal),sigm=new Map(sig.map(x=>[x.time,x.value])),hist=m.filter(x=>sigm.has(x.time)).map(x=>({time:x.time,value:x.value-sigm.get(x.time)}));return {macd:m,signal:sig,hist};}
  function psar(bars,step,maxaf){if(bars.length<2)return[];let bull=true,af=step,ep=bars[0].h,sar=bars[0].l;const out=[];for(let i=1;i<bars.length;i++){sar=sar+af*(ep-sar);if(bull){sar=Math.min(sar,bars[i-1].l,i>1?bars[i-2].l:bars[i-1].l);if(bars[i].l<sar){bull=false;sar=ep;ep=bars[i].l;af=step}else if(bars[i].h>ep){ep=bars[i].h;af=Math.min(maxaf,af+step)}}else{sar=Math.max(sar,bars[i-1].h,i>1?bars[i-2].h:bars[i-1].h);if(bars[i].h>sar){bull=true;sar=ep;ep=bars[i].h;af=step}else if(bars[i].l<ep){ep=bars[i].l;af=Math.min(maxaf,af+step)}}out.push({time:Math.floor(bars[i].t/1000),value:sar});}return out;}
  function ichimoku(bars,a,b,c){const conv=[],base=[],leadA=[],leadB=[];const mid=(i,p)=>{const s=bars.slice(i-p+1,i+1);return (Math.max(...s.map(x=>x.h))+Math.min(...s.map(x=>x.l)))/2};for(let i=0;i<bars.length;i++){const time=Math.floor(bars[i].t/1000);if(i>=a-1)conv.push({time,value:mid(i,a)});if(i>=b-1){const bv=mid(i,b);base.push({time,value:bv});if(i>=a-1)leadA.push({time,value:(mid(i,a)+bv)/2});}if(i>=c-1)leadB.push({time,value:mid(i,c)});}return {conv,base,leadA,leadB};}
  function addLine(data,opts={}){if(!data?.length)return null;const s=chart.addLineSeries({lineWidth:1,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false,...opts});s.setData(data);overlaySeries.push(s);return s;}
  function addOsc(data,id){const s=addLine(data,{priceScaleId:id});if(s)chart.priceScale(id).applyOptions({scaleMargins:{top:.78,bottom:.03},borderVisible:false});return s;}'''
if ema_anchor not in renderer: raise RuntimeError('ema helper anchor missing')
renderer=renderer.replace(ema_anchor,ema_anchor+'\n  '+helpers,1)

old_build="""if(prefs.SMA?.enabled)for(const p of prefs.SMA.params||[]){const s=chart.addLineSeries({lineWidth:1,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});s.setData(sma(bars,Number(p)||20));overlaySeries.push(s);}if(prefs.EMA?.enabled){const s=chart.addLineSeries({lineWidth:1,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});s.setData(ema(bars,Number(prefs.EMA.params[0])||20));overlaySeries.push(s);}"""
new_build=r'''if(prefs.SMA?.enabled)for(const p of prefs.SMA.params||[])addLine(sma(bars,Number(p)||20));
    if(prefs.EMA?.enabled)addLine(ema(bars,Number(prefs.EMA.params[0])||20));
    if(prefs.WMA?.enabled)addLine(wma(bars,Number(prefs.WMA.params[0])||20));
    if(prefs.BB?.enabled){const b=bbands(bars,Number(prefs.BB.params[0])||20,Number(prefs.BB.params[1])||2);addLine(b.up);addLine(b.mid);addLine(b.lo);}
    if(prefs.VWAP?.enabled)addLine(vwap(bars));
    if(prefs.PSAR?.enabled)addLine(psar(bars,Number(prefs.PSAR.params[0])||0.02,Number(prefs.PSAR.params[1])||0.2),{lineStyle:2});
    if(prefs.ICHIMOKU?.enabled){const x=ichimoku(bars,Number(prefs.ICHIMOKU.params[0])||9,Number(prefs.ICHIMOKU.params[1])||26,Number(prefs.ICHIMOKU.params[2])||52);addLine(x.conv);addLine(x.base);addLine(x.leadA);addLine(x.leadB);}
    if(prefs.RSI?.enabled)addOsc(rsi(bars,Number(prefs.RSI.params[0])||14),'rsi');
    if(prefs.MACD?.enabled){const x=macd(bars,Number(prefs.MACD.params[0])||12,Number(prefs.MACD.params[1])||26,Number(prefs.MACD.params[2])||9);addOsc(x.macd,'macd');addOsc(x.signal,'macd');}
    if(prefs.STOCH?.enabled){const x=stochastic(bars,Number(prefs.STOCH.params[0])||14,Number(prefs.STOCH.params[1])||3);addOsc(x.k,'stoch');addOsc(x.d,'stoch');}
    if(prefs.ATR?.enabled)addOsc(atr(bars,Number(prefs.ATR.params[0])||14),'atr');
    if(prefs.CCI?.enabled)addOsc(cci(bars,Number(prefs.CCI.params[0])||20),'cci');
    if(prefs.WILLR?.enabled)addOsc(willr(bars,Number(prefs.WILLR.params[0])||14),'willr');
    if(prefs.ROC?.enabled)addOsc(roc(bars,Number(prefs.ROC.params[0])||12),'roc');
    if(prefs.MOM?.enabled)addOsc(momentum(bars,Number(prefs.MOM.params[0])||10),'mom');
    if(prefs.OBV?.enabled)addOsc(obv(bars),'obv');'''
if old_build not in renderer: raise RuntimeError('indicator render anchor missing')
renderer=renderer.replace(old_build,new_build,1)

layout_old="layout:{background:{type:'solid',color:'#fff'},textColor:'#4b5563',fontSize:12,fontFamily:'Arial, sans-serif'}"
layout_new="layout:{background:{type:'solid',color:'#fff'},textColor:'#4b5563',fontSize:12,fontFamily:'Arial, sans-serif',attributionLogo:false}"
if layout_old not in renderer: raise RuntimeError('chart layout anchor missing')
renderer=renderer.replace(layout_old,layout_new,1)

footer_old='<div class="tv-footer"><span id="chartFootnote">LS Securities</span><span id="chartUpdated"></span></div>'
footer_new='<div class="tv-footer"><span id="chartFootnote">LS Securities</span><span class="chart-attribution">Lightweight Charts™ by <a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">TradingView</a></span><span id="chartUpdated"></span></div>'
if footer_old not in renderer: raise RuntimeError('footer anchor missing')
renderer=renderer.replace(footer_old,footer_new,1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ['attributionLogo:false',"indicatorRow('RSI'","indicatorRow('MACD'",'bbands(bars','Lightweight Charts™ by']:
    if needle not in check: raise RuntimeError('v24 indicator patch missing '+needle)
print('VELTRO v24 indicators + attribution patch applied')
