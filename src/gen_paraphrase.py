#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""패러프레이징 50문항 생성기 — '다음 중 바르게 바꿔 말한 것은?' 객관식.

5대 변환(동의어·구체→추상·품사전환·반대구조·비유→직설)별로 문항을 만들고,
오답마다 함정 유형(그대로 복사/뜻 반대·왜곡/과장/무관)을 표시한다.
출력: samples/패러프레이징_50.html
"""
import html
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "samples" / "패러프레이징_50.html"
CIRCLED = "①②③④⑤"

# 각 문항: (변환유형, 발문source, 정답idx1based, [ (choice, trap) ... ] )
#   trap: ok / copy(그대로 복사) / rev(뜻 반대) / dist(뜻 왜곡) / over(과장) / off(무관)
Q = [
 # ── 동의어 치환 (10) ──
 ("동의어","The new policy enhances public safety.",2,[
   ("makes safety completely impossible","rev"),("improves public safety","ok"),
   ("reduces the need for safety","dist"),("guarantees zero accidents forever","over"),("ignores public opinion","off")]),
 ("동의어","Regular exercise strengthens the heart.",1,[
   ("makes the heart stronger","ok"),("weakens the body over time","rev"),
   ("has no effect on health","rev"),("cures every disease instantly","over"),("requires expensive equipment","off")]),
 ("동의어","The report highlights several key problems.",3,[
   ("hides the main problems","rev"),("solves all the problems at once","over"),
   ("emphasizes several important issues","ok"),("lists only minor details","dist"),("was written by students","off")]),
 ("동의어","Technology has transformed modern communication.",2,[
   ("left communication unchanged","rev"),("dramatically changed how we communicate","ok"),
   ("made all communication impossible","over"),("slowed down every conversation","dist"),("is too costly for most people","off")]),
 ("동의어","The teacher clarified the difficult concept.",1,[
   ("made the concept easier to understand","ok"),("made the concept more confusing","rev"),
   ("skipped the concept entirely","off"),("proved the concept was wrong","dist"),("assigned extra homework","off")]),
 ("동의어","Scientists gathered abundant evidence.",3,[
   ("found no evidence at all","rev"),("destroyed the collected data","dist"),
   ("collected plenty of evidence","ok"),("ignored the available data","dist"),("published a novel","off")]),
 ("동의어","The plan aims to minimize waste.",2,[
   ("aims to increase waste","rev"),("seeks to reduce waste as much as possible","ok"),
   ("has nothing to do with waste","off"),("eliminates every kind of waste forever","over"),("raises production costs","off")]),
 ("동의어","Her argument was remarkably persuasive.",1,[
   ("was strikingly convincing","ok"),("was completely unconvincing","rev"),
   ("was far too short","off"),("persuaded absolutely everyone","over"),("was written in a hurry","off")]),
 ("동의어","The company expanded its operations rapidly.",2,[
   ("shut down all its operations","rev"),("grew its business quickly","ok"),
   ("kept everything exactly the same","rev"),("moved abroad permanently","off"),("lost most of its customers","dist")]),
 ("동의어","The medicine alleviates chronic pain.",3,[
   ("worsens long-term pain","rev"),("causes new kinds of pain","dist"),
   ("eases ongoing pain","ok"),("removes all pain permanently","over"),("is sold only online","off")]),
 # ── 구체 → 추상(상위어) (10) ──
 ("구체→추상","Apples, carrots, and spinach are part of a healthy diet.",2,[
   ("Only apples are truly healthy","over"),("Fruits and vegetables support good health","ok"),
   ("Vegetables are harmful to health","rev"),("Spinach tastes better than carrots","off"),("Diets should avoid all plants","rev")]),
 ("구체→추상","Cars, buses, and trains move people across cities.",1,[
   ("Various forms of transport carry people through cities","ok"),("Only trains can move people","over"),
   ("Cities have no need for transport","rev"),("Buses are slower than cars","off"),("Traffic always causes accidents","dist")]),
 ("구체→추상","Doctors, nurses, and pharmacists care for patients.",3,[
   ("Only doctors can treat patients","over"),("Patients rarely need any care","rev"),
   ("Healthcare workers look after patients","ok"),("Nurses earn less than doctors","off"),("Hospitals are always crowded","off")]),
 ("구체→추상","Painters, poets, and composers express emotion through their work.",2,[
   ("Only painters express real emotion","over"),("Artists convey feeling through what they create","ok"),
   ("Art has nothing to do with emotion","rev"),("Poets write faster than composers","off"),("Emotion ruins good art","dist")]),
 ("구체→추상","Lions, wolves, and eagles hunt other animals.",1,[
   ("Predators feed on other animals","ok"),("Only lions are true hunters","over"),
   ("These animals never hunt","rev"),("Eagles are bigger than wolves","off"),("Hunting is easy for all animals","dist")]),
 ("구체→추상","Facebook, e-mail, and text messages let friends stay in touch.",3,[
   ("Only e-mail keeps friends connected","over"),("Friends can no longer communicate","rev"),
   ("Digital tools help friends keep in contact","ok"),("Texting is cheaper than e-mail","off"),("Social media ends friendships","dist")]),
 ("구체→추상","Rice, wheat, and corn feed much of the world.",2,[
   ("Only rice can feed people","over"),("Grains provide food for many people","ok"),
   ("These crops are inedible","rev"),("Corn grows faster than wheat","off"),("Farming harms the planet","off")]),
 ("구체→추상","Guitars, drums, and violins fill the hall with sound.",1,[
   ("Musical instruments produce the sound in the hall","ok"),("Only drums make real music","over"),
   ("The hall stayed completely silent","rev"),("Violins cost more than guitars","off"),("Loud music damages hearing","dist")]),
 ("구체→추상","Solar, wind, and hydro power reduce carbon emissions.",3,[
   ("Only solar power is truly clean","over"),("These sources raise emissions","rev"),
   ("Renewable energy lowers carbon emissions","ok"),("Wind farms are ugly to look at","off"),("Power plants never pollute","dist")]),
 ("구체→추상","Chess, Go, and bridge sharpen strategic thinking.",2,[
   ("Only chess builds intelligence","over"),("Strategy games improve strategic thinking","ok"),
   ("These games dull the mind","rev"),("Go is older than chess","off"),("Games waste valuable time","dist")]),
 # ── 품사 전환 (8) ──
 ("품사전환","People who decide quickly often succeed.",2,[
   ("Slow people always fail","over"),("Quick decision-making often leads to success","ok"),
   ("Deciding has nothing to do with success","rev"),("Success requires no choices","dist"),("Fast people are careless","off")]),
 ("품사전환","When leaders communicate clearly, teams perform better.",1,[
   ("Clear communication improves team performance","ok"),("Silence helps teams the most","rev"),
   ("Communication harms teamwork","rev"),("Leaders should never speak","over"),("Teams dislike their leaders","off")]),
 ("품사전환","Because the child was curious, she explored everything.",3,[
   ("Her boredom kept her still","rev"),("Curiosity is a sign of danger","dist"),
   ("Her curiosity drove her exploration","ok"),("She avoided anything new","rev"),("Children rarely ask questions","off")]),
 ("품사전환","The team collaborated, and the project improved.",2,[
   ("Working alone improved the project","rev"),("Their collaboration led to a better project","ok"),
   ("Collaboration ruined the project","rev"),("The project needed no teamwork","dist"),("The team disliked the work","off")]),
 ("품사전환","Since prices rose sharply, people spent less.",1,[
   ("The sharp rise in prices reduced spending","ok"),("Cheaper prices lowered spending","rev"),
   ("Prices had no effect on spending","rev"),("People spent everything they had","over"),("Shops closed down entirely","off")]),
 ("품사전환","He practiced daily, so his skills advanced.",3,[
   ("Skipping practice sharpened his skills","rev"),("Practice made his skills worse","rev"),
   ("Daily practice led to the advancement of his skills","ok"),("Skills need no practice","dist"),("He disliked his hobby","off")]),
 ("품사전환","The city planned carefully and avoided chaos.",2,[
   ("Careless planning prevented chaos","rev"),("Careful planning helped the city avoid chaos","ok"),
   ("Planning caused the chaos","rev"),("The city ignored all planning","dist"),("Chaos is good for cities","off")]),
 ("품사전환","Because she persevered, she reached her goal.",1,[
   ("Her perseverance brought her to her goal","ok"),("Giving up got her the goal","rev"),
   ("Her goal required no effort","dist"),("She quit before finishing","rev"),("Goals are always easy","over")]),
 # ── 반대구조(부정↔긍정) (10) ──
 ("반대구조","This tool does not limit creativity; it frees it.",2,[
   ("The tool restricts creativity","rev"),("The tool sets creativity free","ok"),
   ("The tool has no effect on creativity","dist"),("Creativity needs no tools at all","over"),("The tool is hard to use","off")]),
 ("반대구조","The rule does not silence students; it invites debate.",1,[
   ("The rule encourages students to debate","ok"),("The rule keeps students quiet","rev"),
   ("The rule bans all discussion","rev"),("Debate is a waste of class time","dist"),("Students dislike the rule","off")]),
 ("반대구조","Failure is not the end but a step toward growth.",3,[
   ("Failure stops all progress","rev"),("Failure should be avoided at any cost","over"),
   ("Failure can lead to growth","ok"),("Growth never involves setbacks","rev"),("Success requires no effort","off")]),
 ("반대구조","The policy does not shrink freedom; it protects it.",2,[
   ("The policy takes away freedom","rev"),("The policy safeguards freedom","ok"),
   ("Freedom and policy are unrelated","dist"),("The policy removes all rules","over"),("The policy is unpopular","off")]),
 ("반대구조","Stress is not always harmful; in small doses it helps.",1,[
   ("A little stress can be beneficial","ok"),("Stress is always damaging","rev"),
   ("Stress never affects people","rev"),("All stress should be removed","over"),("Stress is caused by work","off")]),
 ("반대구조","The change did not weaken the team; it united it.",3,[
   ("The change broke the team apart","rev"),("The team ignored the change","dist"),
   ("The change brought the team together","ok"),("Teams never change","rev"),("The change was expensive","off")]),
 ("반대구조","Silence is not empty; it carries meaning.",2,[
   ("Silence means nothing at all","rev"),("Silence can be meaningful","ok"),
   ("Silence is always uncomfortable","dist"),("People should never be silent","over"),("Noise is better than silence","off")]),
 ("반대구조","The app does not replace teachers; it supports them.",1,[
   ("The app helps teachers rather than replacing them","ok"),("Teachers are now unnecessary","rev"),
   ("The app fully substitutes for teachers","rev"),("Teaching needs no technology","dist"),("Teachers reject the app","off")]),
 ("반대구조","Rules do not kill fun; they make fair play possible.",3,[
   ("Rules destroy all enjoyment","rev"),("Games are better without any rules","over"),
   ("Rules enable fair and enjoyable play","ok"),("Fairness ruins the fun","dist"),("Players hate every rule","off")]),
 ("반대구조","Aging is not only loss; it also brings wisdom.",2,[
   ("Aging brings nothing but decline","rev"),("Aging can also bring wisdom","ok"),
   ("Wisdom has no link to age","dist"),("Only the young are wise","rev"),("People fear growing old","off")]),
 # ── 비유 → 직설 (12) ──
 ("비유→직설","Reading is a window to other worlds.",2,[
   ("Windows help us read more easily","copy"),("Reading lets us experience unfamiliar worlds","ok"),
   ("Books should have more pictures","off"),("Other worlds are dangerous","dist"),("Reading narrows the mind","rev")]),
 ("비유→직설","Time is a thief that steals our chances.",1,[
   ("As time passes, opportunities are lost","ok"),("Thieves are afraid of time","copy"),
   ("Time makes us richer","rev"),("We have unlimited chances","over"),("Clocks are expensive","off")]),
 ("비유→직설","Her words were a bridge between the two sides.",3,[
   ("Bridges are made of strong words","copy"),("The two sides refused to talk","rev"),
   ("Her words connected the two sides","ok"),("She built an actual bridge","off"),("Words always cause conflict","dist")]),
 ("비유→직설","Knowledge is a light in the darkness.",2,[
   ("Darkness is brighter than light","rev"),("Knowledge helps us understand the unknown","ok"),
   ("Lamps are a form of knowledge","copy"),("Learning keeps us in the dark","rev"),("Electricity is essential","off")]),
 ("비유→직설","Fear is a chain that holds us back.",1,[
   ("Fear prevents us from moving forward","ok"),("Chains are stronger than fear","copy"),
   ("Fear pushes us to act boldly","rev"),("We should welcome all fear","over"),("Metal chains are heavy","off")]),
 ("비유→직설","The internet is a double-edged sword.",3,[
   ("Swords are sold on the internet","copy"),("The internet is entirely harmful","over"),
   ("The internet has both benefits and dangers","ok"),("The internet has no downsides","rev"),("Blades must be handled carefully","off")]),
 ("비유→직설","His anger was a storm that passed quickly.",2,[
   ("Storms make people angry","copy"),("His anger was intense but brief","ok"),
   ("He was never angry at all","rev"),("His anger lasted for years","rev"),("Weather affects our mood","off")]),
 ("비유→직설","Opportunity is a door that opens only once.",1,[
   ("A chance may come only for a limited time","ok"),("Doors should stay open forever","rev"),
   ("Carpenters build many doors","copy"),("Opportunities are endless","over"),("Old doors are hard to open","off")]),
 ("비유→직설","Success is a ladder climbed step by step.",3,[
   ("Ladders are needed for success","copy"),("Success comes all at once","rev"),
   ("Success is reached gradually, one stage at a time","ok"),("Climbing is dangerous work","off"),("Only tall people succeed","dist")]),
 ("비유→직설","Words can be seeds that grow into ideas.",2,[
   ("Farmers plant words in fields","copy"),("What we say can develop into ideas","ok"),
   ("Ideas destroy language","rev"),("Seeds never grow","rev"),("Gardening is a useful hobby","off")]),
 ("비유→직설","The city never sleeps.",1,[
   ("The city stays active at all hours","ok"),("The city closes early every night","rev"),
   ("Cities need plenty of rest","copy"),("No one lives in the city","dist"),("Sleep is important for health","off")]),
 ("비유→직설","Patience is the key that unlocks progress.",3,[
   ("Keys are needed to make progress","copy"),("Progress happens without any effort","rev"),
   ("Being patient makes progress possible","ok"),("Locks slow everyone down","off"),("Impatience speeds up success","rev")]),
]

TRAP = {"ok":("정답","b-ok"),"copy":("그대로 복사","b-copy"),"rev":("뜻 반대","b-dist"),
        "dist":("뜻 왜곡","b-dist"),"over":("과장","b-over"),"off":("무관","b-off")}
def esc(s): return html.escape(s, quote=False)

def build():
    probs, ans = [], []
    for i,(typ,src,a,chs) in enumerate(Q,1):
        lis="".join(f'<li><span class="num">{CIRCLED[j]}</span>{esc(c)}</li>' for j,(c,_) in enumerate(chs))
        probs.append(f'''<div class="q"><div><span class="qn">Q{i}</span><span class="tp">{typ}</span>
          <span class="ask">다음 중 밑줄 문장을 바르게 바꿔 말한 것은?</span></div>
          <div class="src">"{esc(src)}"</div><ul class="ch">{lis}</ul></div>''')
        rows=""
        for j,(c,t) in enumerate(chs):
            nm,cls=TRAP[t]; ok=' class="ok"' if t=="ok" else ""
            rows+=f'<tr{ok}><td class="oc">{CIRCLED[j]}</td><td>{esc(c)} <span class="badge {cls}">{nm}</span></td></tr>'
        ans.append(f'<div class="ak"><span class="qn">Q{i}</span> 정답 <span class="cor">{CIRCLED[a-1]}</span> <span class="badge b-ok">{typ}</span><table>{rows}</table></div>')
    doc=TPL.replace("{{PROB}}","\n".join(probs)).replace("{{ANS}}","\n".join(ans)).replace("{{N}}",str(len(Q)))
    OUT.write_text(doc,encoding="utf-8"); print(f"패러프레이징 {len(Q)}문항 → {OUT}")

TPL='''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>패러프레이징 50문항</title><style>
@page{ size:A4; margin:11mm 12mm; } *{ box-sizing:border-box; }
body{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; margin:0; }
.wrap{ max-width:820px; margin:0 auto; }
:root{ --deep:#1f7a5c; --deep-d:#12543d; --amber:#ffe9a8; --trap:#cd5049; --muted:#6b7280; --line:#e6e8ea; }
.cover{ text-align:center; padding:12px 0 8px; border-bottom:3px solid var(--deep-d); margin-bottom:12px; }
.cover .t{ font-size:19px; font-weight:800; color:var(--deep-d); } .cover .s{ font-size:10px; color:var(--muted); }
.q{ border:1px solid var(--line); border-radius:7px; padding:10px 13px; margin-bottom:9px; break-inside:avoid; }
.q .qn{ background:var(--deep-d); color:#fff; font-weight:800; font-size:10.5px; padding:1px 8px; border-radius:5px; margin-right:6px; }
.q .tp{ font-size:8.5px; font-weight:800; color:#fff; background:var(--deep); border-radius:8px; padding:1px 7px; margin-right:6px; }
.q .ask{ font-size:9.8px; font-weight:700; }
.src{ background:#eaf5f0; border:1px solid #cfe6dd; border-radius:6px; padding:7px 10px; margin:6px 0; font-size:10.3px; }
.ch{ list-style:none; margin:0; padding:0; } .ch li{ font-size:9.7px; padding:2px 0 2px 3px; } .ch .num{ font-weight:800; margin-right:4px; }
.answers{ break-before:page; } .answers h2{ font-size:14px; color:var(--deep-d); border-bottom:2px solid var(--deep); padding-bottom:5px; }
.ak{ font-size:9.4px; margin-bottom:7px; break-inside:avoid; } .ak .qn{ background:var(--deep-d); color:#fff; font-weight:800; font-size:9.5px; padding:1px 6px; border-radius:4px; margin-right:5px; }
.ak .cor{ color:var(--deep); font-weight:800; } .ak table{ width:100%; border-collapse:collapse; margin-top:3px; }
.ak td{ padding:2px 6px; border-bottom:1px solid var(--line); font-size:9px; } .ak .oc{ font-weight:800; width:18px; } .ak tr.ok{ background:#eaf5f0; }
.badge{ display:inline-block; font-size:7.8px; font-weight:800; border-radius:8px; padding:0 6px; color:#fff; }
.b-ok{ background:var(--deep); } .b-copy{ background:#c2410c; } .b-dist{ background:var(--trap); } .b-over{ background:#b8860b; } .b-off{ background:var(--muted); }
</style></head><body><div class="wrap">
<div class="cover"><div class="t">패러프레이징 훈련 — {{N}}문항</div>
<div class="s">정답=뜻 유지·단어 교체 / 오답=그대로 복사·뜻 왜곡·과장·무관. 5대 변환 유형별.</div></div>
{{PROB}}
<div class="answers"><h2>정답 &amp; 해설 — 오답 함정 유형까지</h2>{{ANS}}</div>
</div></body></html>'''

if __name__=="__main__": build()
