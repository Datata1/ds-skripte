# Die Stämme – Skripte

Kleine Helfer für Die Stämme:

| Skript | Wofür | Wo |
|---|---|---|
| **Raubzug-Rechner** | Teilt deine Truppen optimal auf die Raubzug-Stufen auf (Ress pro Lauf, Ress pro Stunde oder gleiche Laufzeit, optional mit max. Laufzeit) | Schnellleiste im Spiel |
| **Späh-Notiz** | Schreibt aus einem Spähbericht eine einzeilige Dorfnotiz: 🟢/🟡/🔴 Ampel, HG-Stufe, Wall, Ress/h, Minen, Spähzeitpunkt | Schnellleiste im Spiel (Premium nötig) |
| **Stamm-Statistik** | Wer im Stamm wie viel gefarmt und beim Raubzug gesammelt hat – als Tabelle und Graph für Discord | Python am PC |

---

## Schnellleiste einrichten (Raubzug-Rechner & Späh-Notiz)

1. Im Spiel oben auf **Einstellungen → Schnellleiste bearbeiten**.
2. **Link hinzufügen** klicken.
3. **Name** eintragen (z. B. `Raubzug`), bei **Ziel-URL** den Code von unten einfügen  
   (rechts oben im Codeblock ist ein Kopier-Knopf).
4. Speichern – der Link erscheint in deiner Schnellleiste.

### Raubzug-Rechner

Auf den Link klicken – er öffnet den Raubzug im Versammlungsplatz und zeigt darüber den Rechner.

- Einheiten an-/abhaken, optional eine Anzahl festlegen (leer = alle).
- Ziel wählen: **Ress pro Lauf**, **Ress pro Stunde** oder **Gleiche Laufzeit**, optional **max. Laufzeit**.
- Der Rechner trägt die Truppen für die nächste Stufe ein, der passende Start-Knopf blinkt grün.  
  **Abschicken musst du selbst** – nach jedem Klick wird automatisch die nächste Stufe eingetragen.
- Nochmal auf den Schnellleisten-Link klicken blendet ihn wieder aus.

```text
javascript:(()=>{const $=window.jQuery,g=window.game_data;if(!$||!g)return alert('Nur im Spiel');const q=location.search;if(!/[?&]mode=scavenge(&|$)/.test(q)||!/screen=place/.test(q)){location.href=g.link_base_pure+'place&mode=scavenge';return;}if(window.__rzO)window.__rzO.disconnect();if($('#rz').length){$('#rz').remove();$('.rzn').removeClass('rzn');return;}if(!$('.scavenge-option').length)return UI.ErrorMessage('Kein Raubzug');const U=[['spear',25,1],['sword',15,1],['axe',10,1],['archer',10,1],['light',80,4],['marcher',50,5],['heavy',50,6],['knight',100,10]].filter(u=>$(`input.unitsInput[name=${u[0]}]`).length);const I=window.image_base||(($('img[src*="/graphic/"]').attr('src')||'').match(/.*\/graphic\//)||['/graphic/'])[0];const LF=[0,.1,.25,.5,.75];const K='rzR_'+g.world;const RS={};let S={sel:{},mode:'max',lim:false,lt:'2:00',skip:{}};U.forEach(u=>S.sel[u[0]]=u[0]!='knight');try{const o=JSON.parse(localStorage.getItem(K));if(o)S=$.extend(true,S,o);}catch(e){}let ws=S.ws;const save=()=>{try{localStorage.setItem(K,JSON.stringify(S));}catch(e){}};const df=()=>ws?ws**-.55:1;const dur=L=>L>0?((L*L*100)**.45+1800)*df():0;const maxK=(T,f)=>{const x=T/df()-1800;return x>0?Math.sqrt(x**(1/.45)/100)/f:0;};const av=u=>+(($(`.units-entry-all[data-unit=${u}]`).first().text().match(/\d+/g)||[0]).join(''));const nf=n=>Math.round(n).toLocaleString('de-DE');const im=u=>`<img src="${I}unit/unit_${u}.png">`;const pd=t=>{t=$.trim(t||'').replace(',','.');const p=t.split(':');return p.length>1?(+p[0]||0)*3600+(+p[1]||0)*60+(+p[2]||0):Math.round((parseFloat(t)||0)*3600);};const fd=s=>{s=Math.round(s);const z=n=>(n<10?'0':'')+n;return Math.floor(s/3600)+':'+z(Math.floor(s % 3600 / 60))+':'+z(s % 60);};const opts=()=>$('.scavenge-option').get().map((e,i)=>{const o=$(e),fr=o.find('.free_send_button').length>0;return{id:i+1,o,fr,r:!fr&&o.find('.return-countdown').length>0,t:$.trim(o.find('.title').first().text())||'Stufe '+(i+1)};});const alloc=(C,F,T)=>{const n=F.length,f=F.map(o=>LF[o.id]),cap=f.map(x=>T?maxK(T,x):1/0),H=f.map(()=>0);if(!n||C<=0)return H;if(S.mode=='run'){let rem=C;return f.map((x,i)=>[x,i]).sort((a,b)=>b[0]-a[0]).reduce((h,[x,i])=>{h[i]=Math.min(rem,cap[i]);rem-=h[i];return h;},H);}if(S.mode=='eq'){let s=C/f.reduce((a,x)=>a+1/x,0);f.forEach((x,i)=>{s=Math.min(s,cap[i]*x);});return f.map(x=>s/x);}const st=C/3000,rt=(h,k)=>h>0?h*f[k]/dur(h*f[k]):0;let left=C;while(left>1e-9){let bi=-1,bg=-1,ba=0;for(let i=0;i<n;i++){const a=Math.min(st,left,cap[i]-H[i]);if(a<=1e-9)continue;const v=(rt(H[i]+a,i)-rt(H[i],i))/a;if(v>bg){bg=v;bi=i;ba=a;}}if(bi<0)break;H[bi]+=ba;left-=ba;}return H;};const plan=()=>{const O=opts(),X={};for(;;){const F=O.filter(o=>o.fr&&!S.skip[o.id]&&!X[o.id]),N={};let C=0;U.forEach(([u,c])=>{N[u]=S.sel[u]?Math.max(0,av(u)-(RS[u]||0)):0;C+=N[u]*c;});const T=S.lim?pd(S.lt):0,H=alloc(C,F,T),sH=H.reduce((a,x)=>a+x,0),R=F.map(o=>({o,u:{}}));let bg=0;H.forEach((h,i)=>{if(h>H[bg])bg=i;});U.forEach(([u])=>{let us=0;R.forEach((r,i)=>{r.u[u]=C?Math.floor(N[u]*H[i]/C):0;us+=r.u[u];});if(R.length&&sH>=C*.9999)R[bg].u[u]+=N[u]-us;});R.forEach(r=>{r.c=U.reduce((a,[u,c])=>a+r.u[u]*c,0);r.L=r.c*LF[r.o.id];r.d=dur(r.L);r.h=r.d?r.L/r.d*3600:0;r.p=U.reduce((a,[u,,p])=>a+r.u[u]*p,0);});const Q=R.filter(r=>r.c>0).sort((a,b)=>b.o.id-a.o.id),w=Q.filter(r=>r.p<10).sort((a,b)=>a.p-b.p);if(!w.length)return{O,R:Q,C,T};X[w[0].o.id]=1;}};let cur=0;const fill=r=>{U.forEach(([u])=>{const v=r?Math.min(r.u[u],av(u)):0;$(`input.unitsInput[name=${u}]`).val(v||'').trigger('input').trigger('keyup').trigger('change');});$('.rzn').removeClass('rzn');cur=r?r.o.id:0;if(r)r.o.o.find('.free_send_button').addClass('rzn');};const css='#rz{margin-bottom:10px}#rz h4{display:flex;gap:8px;align-items:center}#rz .tot{margin-left:auto}#rz .x{cursor:pointer}#rz table{width:100%}#rz td,#rz th{text-align:center}#rz td:first-child,#rz th:first-child{text-align:left}#rz [data-r]{width:50px;text-align:center}#rz .er{border:1px solid red;background:#fdd}#rz tr.cur td{background:#d6efc0}#rz tr.na td{color:#888}#rz .lt{width:40px;text-align:center}#rz .op{padding:6px 4px}#rz .op label{margin-right:12px}#rz .ft{padding:4px;text-align:right}#rz .st{width:16px;text-align:center}#rz .st img{width:14px;height:14px}#rz .st input{margin:0}#rz .sc td:nth-child(2),#rz .sc th:nth-child(2){text-align:left}.rzn{box-shadow:0 0 0 3px #43a047!important;animation:rzb 1s infinite alternate}@keyframes rzb{to{box-shadow:0 0 0 6px #43a04744}}';$('#rzs').remove();$('head').append(`<style id="rzs">${css}</style>`);const P=$(`<div id="rz" class="vis"><h4>Raubzug-Rechner<span class="tot"></span><a class="x">✕</a></h4><table class="vis"><tr><th>Einheit</th>${U.map(([u])=>`<th>${im(u)}</th>`).join('')}</tr><tr><td>Mitschicken</td>${U.map(([u])=>`<td><input type="checkbox" class="ck" data-u="${u}"${S.sel[u]?' checked':''}></td>`).join('')}</tr><tr><td>Verfügbar</td>${U.map(([u])=>`<td data-v="${u}"></td>`).join('')}</tr><tr><td>Anzahl</td>${U.map(([u])=>`<td><input inputmode="numeric" data-r="${u}" placeholder="alle"></td>`).join('')}</tr></table><div class="op"><b>Ziel:</b> <label><input type="radio" name="rzm" value="run">Ress pro Lauf</label><label><input type="radio" name="rzm" value="max">Ress pro Stunde</label><label><input type="radio" name="rzm" value="eq">Gleiche Laufzeit</label> | <label><input type="checkbox" class="lo"${S.lim?' checked':''}> max. Laufzeit <input class="lt" value="${S.lt}"> h</label></div><table class="vis sc"></table><div class="ft"><a class="btn rf">Nächste Stufe eintragen</a></div></div>`);$('#scavenge_screen').length?$('#scavenge_screen').before(P):$('#content_value').prepend(P);const go=f=>{const p=plan();if(f)fill(p.R[0]);U.forEach(([u])=>{P.find(`[data-v=${u}]`).text(nf(av(u))).css('opacity',S.sel[u]?1:.4);P.find(`[data-r=${u}]`).prop('disabled',!S.sel[u]);});P.find(`[value=${S.mode}]`).prop('checked',true);P.find('.lt').prop('disabled',!S.lim);P.find('[data-r]').each(function(){const u=$(this).data('r');if(this!=document.activeElement&&u in RS)$(this).val(Math.max(0,av(u)-RS[u])).removeClass('er');});P.find('.rf').toggleClass('rzn',!cur&&p.R.length>0);const sh=U.filter(([u])=>S.sel[u]),n=sh.length+3;let tot=0;P.find('.sc').html(`<tr><th class="st"></th><th>Stufe</th>${sh.map(([u])=>`<th>${im(u)}</th>`).join('')}<th>Dauer</th><th>${['wood','stone','iron'].map(x=>`<span class="icon header ${x}"></span>`).join('')}</th><th>pro Stunde</th></tr>`+p.O.map(o=>{const r=p.R.find(x=>x.o==o);if(r)tot+=r.h;const nm=`<td class="st">${o.fr?`<input type="checkbox" class="sk" id="rzo${o.id}" data-o="${o.id}"${S.skip[o.id]?'':' checked'}>`:`<img src="${I+(o.r?'command/return':'scavenging/lock')}.png">`}</td><td><label for="rzo${o.id}">${o.t}</label></td>`;return r?`<tr class="${o.id==cur?'cur':''}">${nm}${sh.map(([u])=>`<td>${r.u[u]?nf(r.u[u]):'–'}</td>`).join('')}<td>${fd(r.d)}</td><td>je ${nf(r.L/3)}</td><td>${nf(r.h)}</td></tr>`:`<tr class="na">${nm}<td colspan="${n}">${o.r?'läuft – zurück in '+$.trim(o.o.find('.return-countdown').first().text()):!o.fr?'gesperrt':S.skip[o.id]?'nicht verwenden':'zu wenig Truppen'}</td></tr>`;}).join('')+(p.R.length?'':`<tr class="na"><td colspan="${n+2}">${!p.O.some(o=>o.fr)?'Keine freie Stufe.':p.C?'Mind. 10 Einwohner pro Stufe nötig.':'Keine Truppen verfügbar.'}</td></tr>`));P.find('.tot').text(`Gesamt: ${nf(tot)} Ress/h`);};let tm;const ch=()=>{save();clearTimeout(tm);tm=setTimeout(()=>go(1),150);};P.on('click','.x',()=>{ob.disconnect();$('.rzn').removeClass('rzn');P.remove();}).on('change','.ck',function(){S.sel[$(this).data('u')]=this.checked;ch();}).on('input','[data-r]',function(){const u=$(this).data('r'),a=av(u),v=this.value=this.value.replace(/\D/g,''),o=+v>a;v?RS[u]=Math.max(0,a-v):delete RS[u];$(this).toggleClass('er',o);if(o&&!this.e)UI.ErrorMessage(`Nur ${nf(a)} verfügbar`);this.e=o;ch();}).on('change','[name=rzm]',function(){S.mode=this.value;ch();}).on('change','.lo',function(){S.lim=this.checked;ch();}).on('input','.lt',function(){S.lt=this.value;ch();}).on('change','.sk',function(){S.skip[$(this).data('o')]=!this.checked;ch();}).on('click','.rf',()=>go(1));const key=()=>opts().map(o=>o.fr?'f':o.r?'r':'l').join('')+U.map(([u])=>av(u));let lk=key(),ot;const ob=new MutationObserver(m=>{if(m.every(x=>$(x.target).closest('#rz').length))return;clearTimeout(ot);ot=setTimeout(()=>{const k=key();if(k!=lk){lk=k;cur=0;$('.rzn').removeClass('rzn');go(0);}},350);});ob.observe($('#content_value')[0]||document.body,{childList:true,subtree:true});window.__rzO=ob;if(!ws)$.get('/interface.php?func=get_config',x=>{ws=S.ws=+$(x).find('speed').first().text()||0;save();go(1);});go(1);})();
```

### Späh-Notiz

Einen Spähbericht öffnen und auf den Link klicken. Die Notiz des Zieldorfs wird überschrieben mit z. B.:

`🟡 HG 2 · 1.234 Ress/h · Holz 8 Lehm 7 Eisen 6 · Spy 26.11.26 14:03`

- 🟢 HG 1 · 🟡 HG 2 · 🔴 HG 3+ oder Wall vorhanden
- Ress/h berücksichtigt Weltgeschwindigkeit und Bonusdörfer.
- Dorfnotizen gibt es nur mit **Premium-Account**.

```text
javascript:(()=>{const $=window.jQuery,g=window.game_data;if(!$||!g)return alert('Nur im Spiel');const err=t=>UI.ErrorMessage(t);if(!/screen=report/.test(location.search))return err('Bitte einen Spähbericht öffnen');const bd=$('#attack_spy_building_data').val();if(!bd)return err('Keine Gebäude im Bericht');let B={};try{JSON.parse(bd).forEach(b=>B[b.id]=+b.level||0);}catch(e){return err('Bericht nicht lesbar');}const xp=s=>document.evaluate(s,document,null,9,null).singleNodeValue;const ta=xp("//td[contains(text(),'Ziel:')]/following-sibling::td//a[contains(@href,'info_village')]")||$('#attack_info_def a[href*="info_village"]')[0];const vid=ta&&(ta.href.match(/[?&]id=(\d+)/)||[])[1];if(!vid)return err('Zieldorf nicht gefunden');const kz=xp("//td[contains(text(),'Kampfzeit')]/following-sibling::td");const dt=((kz&&kz.textContent)||'').match(/\d\d\.\d\d\.\d\d\s+\d\d:\d\d/);const K='spyN_'+g.world;let C;try{C=JSON.parse(localStorage.getItem(K));}catch(e){}const base=g.link_base_pure.replace(/&screen=$/,'');const run=()=>{const pr=l=>l>0?C.b*C.s*1.163118**(l-1):5*C.s;const P={wood:pr(B.wood||0),stone:pr(B.stone||0),iron:pr(B.iron||0)};if($('.bonus_icon_1').length)P.wood*=2;if($('.bonus_icon_2').length)P.stone*=2;if($('.bonus_icon_3').length)P.iron*=2;if($('.bonus_icon_8').length)for(const k in P)P[k]*=1.3;const sum=(Math.floor(P.wood)+Math.floor(P.stone)+Math.floor(P.iron)).toLocaleString('de-DE');const hg=B.main||0,tm=dt?dt[0].replace(/\s+/,' '):new Date().toLocaleString('de-DE',{day:'2-digit',month:'2-digit',year:'2-digit',hour:'2-digit',minute:'2-digit'}).replace(',','');const L=(hg>=3||B.wall?'🔴':hg==2?'🟡':'🟢')+' HG '+hg+(B.wall?' · Wall '+B.wall:'')+' · '+sum+' Ress/h · Holz '+(B.wood||0)+' Lehm '+(B.stone||0)+' Eisen '+(B.iron||0)+' · Spy '+tm;$.post(base+'&screen=api&ajaxaction=village_note_edit',{village_id:vid,note:L,h:g.csrf}).done(()=>UI.SuccessMessage('Notiz gespeichert: '+L)).fail(()=>err('Speichern fehlgeschlagen'));};if(C&&C.s)run();else $.get('/interface.php?func=get_config').done(x=>{const q=$(x);C={s:+q.find('speed').first().text()||1,b:+q.find('base_production').first().text()||30};try{localStorage.setItem(K,JSON.stringify(C));}catch(e){}run();}).fail(()=>err('Weltdaten nicht erreichbar'));})();
```

> **Hinweis zu den Skript-Regeln:** Beide Skripte lesen nur die offene Seite, schicken nichts automatisch
> und machen eine Aktion pro Klick. Sie sind aber (noch) nicht offiziell in der Skript-Bibliothek
> freigegeben – Nutzung auf eigene Verantwortung.

Die lesbaren Quelltexte liegen in [`raubzug-rechner.js`](raubzug-rechner.js) und [`spaeh-notiz.js`](spaeh-notiz.js).

---

## Stamm-Statistik (Python)

Liest nur **öffentliche** Seiten ohne Login (Weltdaten und die Rangliste „An einem Tag“) und baut daraus
eine Übersicht pro Stammesmitglied:

- **Farm-Ress** – geplünderte Rohstoffe
- **Farmen** – Anzahl geplünderter Dörfer
- **Raubzug-Ress** – beim Raubzug gesammelte Rohstoffe

Dazu ein PNG-Graph (eine Farbe pro Spieler) zum Reinkopieren in Discord.

### Installation

Du brauchst [Python 3.9 oder neuer](https://www.python.org/downloads/). Dann einmalig:

```bash
pip install -r requirements.txt
```

(Ohne `matplotlib` läuft das Skript auch, dann nur ohne Graph.)

### Benutzen

```bash
python3 stamm-statistik.py --stamm GBB
```

Unter Windows heißt der Befehl meist `python` statt `python3`.

| Option | Bedeutung |
|---|---|
| `--stamm TAG` | Stammes-Kürzel (Pflicht), z. B. `GBB` oder `-B.O-` |
| `--welt de262` | Welt (Standard: `de262`) |
| `--rekorde` | bester Tag je Spieler mit Datum |
| `--gestern` | nur der gestrige Tag |
| `--tage 7` | Gesamt nur über die letzten 7 Tage |
| `--kein-graph` | kein PNG erzeugen |
| `--webhook URL` | Tabelle und Graph direkt in einen Discord-Kanal posten |

Der Text wird im Terminal ausgegeben (zum Kopieren nach Discord), der Graph landet als
`stamm-statistik-<welt>-<tag>.png` im selben Ordner.

### Wichtig: täglich laufen lassen

Die Rangliste zeigt pro Spieler nur seinen **besten Tag**. Das Skript merkt sich jeden Rekord in
`stamm-statistik-<welt>-<tag>.json`. Wer es **einmal am Tag** startet, sammelt so die Tageswerte
und bekommt echte Summen. Im Early Game stellt fast jeder täglich einen neuen Rekord auf.

Automatisch jeden Morgen (Linux/Mac, `crontab -e`):

```text
0 8 * * * cd /pfad/zum/ordner && python3 stamm-statistik.py --stamm GBB --webhook https://discord.com/api/webhooks/...
```

Unter Windows geht das gleiche mit der **Aufgabenplanung**.

**Discord-Webhook anlegen:** Kanal-Einstellungen → Integrationen → Webhooks → Neuer Webhook → URL kopieren.
Die URL ist wie ein Passwort – nicht öffentlich teilen.
