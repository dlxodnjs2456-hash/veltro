import pathlib,re

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

# NQ benchmark supplied by operator:
# entry 29225.00 -> current 29220.75, LONG 10 contracts = -1,164,075 KRW.
# 4.25 points * 10 contracts => 42.5 point-contracts, so KRW 27,390 per point,
# or KRW 6,847.5 per 0.25-point NQ tick.
old_patterns=[
    r"(NQU26[^\n\r]{0,240}?tickValue\s*:\s*)6290(?:\.0+)?",
    r"(tickValue\s*:\s*)6290(?:\.0+)?(?=[,}\s])",
]
count=0
for pat in old_patterns:
    renderer,n=re.subn(pat,r"\g<1>6847.5",renderer,count=1)
    count+=n
    if n:
        break
if count!=1:
    raise RuntimeError('NQ tickValue 6290 anchor missing or ambiguous; refusing broad PnL modification')

renderer_path.write_text(renderer,encoding='utf-8')
final=renderer_path.read_text(encoding='utf-8')
if 'tickValue:6847.5' not in final and 'tickValue: 6847.5' not in final:
    raise RuntimeError('NQ benchmark tick value was not applied')
if re.search(r"NQU26[^\n\r]{0,240}?tickValue\s*:\s*6290",final):
    raise RuntimeError('Old NQ tick value still present')
print('VELTRO NQ PnL benchmark applied: tick=0.25, tickValueKRW=6847.5, pointValueKRW=27390')
