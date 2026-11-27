(()=>{
const $=window.jQuery,g=window.game_data;
if(!$||!g)return alert('Nur im Spiel');
const err=t=>UI.ErrorMessage(t);
if(!/screen=report/.test(location.search))return err('Bitte einen Spähbericht öffnen');
const bd=$('#attack_spy_building_data').val();
if(!bd)return err('Keine Gebäude im Bericht');
let B={};
try{JSON.parse(bd).forEach(b=>B[b.id]=+b.level||0);}catch(e){return err('Bericht nicht lesbar');}
const xp=s=>document.evaluate(s,document,null,9,null).singleNodeValue;
const ta=xp("//td[contains(text(),'Ziel:')]/following-sibling::td//a[contains(@href,'info_village')]")||$('#attack_info_def a[href*="info_village"]')[0];
const vid=ta&&(ta.href.match(/[?&]id=(\d+)/)||[])[1];
if(!vid)return err('Zieldorf nicht gefunden');
const kz=xp("//td[contains(text(),'Kampfzeit')]/following-sibling::td");
const dt=((kz&&kz.textContent)||'').match(/\d\d\.\d\d\.\d\d\s+\d\d:\d\d/);
const K='spyN_'+g.world;
let C;try{C=JSON.parse(localStorage.getItem(K));}catch(e){}
const base=g.link_base_pure.replace(/&screen=$/,'');
const run=()=>{
const pr=l=>l>0?C.b*C.s*1.163118**(l-1):5*C.s;
const P={wood:pr(B.wood||0),stone:pr(B.stone||0),iron:pr(B.iron||0)};
if($('.bonus_icon_1').length)P.wood*=2;
if($('.bonus_icon_2').length)P.stone*=2;
if($('.bonus_icon_3').length)P.iron*=2;
if($('.bonus_icon_8').length)for(const k in P)P[k]*=1.3;
const sum=(Math.floor(P.wood)+Math.floor(P.stone)+Math.floor(P.iron)).toLocaleString('de-DE');
const hg=B.main||0,tm=dt?dt[0].replace(/\s+/,' '):new Date().toLocaleString('de-DE',{day:'2-digit',month:'2-digit',year:'2-digit',hour:'2-digit',minute:'2-digit'}).replace(',','');const L=(hg>=3||B.wall?'🔴':hg==2?'🟡':'🟢')+' HG '+hg+(B.wall?' · Wall '+B.wall:'')+' · '+sum+' Ress/h · Holz '+(B.wood||0)+' Lehm '+(B.stone||0)+' Eisen '+(B.iron||0)+' · Spy '+tm;
$.post(base+'&screen=api&ajaxaction=village_note_edit',{village_id:vid,note:L,h:g.csrf}).done(()=>UI.SuccessMessage('Notiz gespeichert: '+L)).fail(()=>err('Speichern fehlgeschlagen'));
};
if(C&&C.s)run();
else $.get('/interface.php?func=get_config').done(x=>{const q=$(x);C={s:+q.find('speed').first().text()||1,b:+q.find('base_production').first().text()||30};try{localStorage.setItem(K,JSON.stringify(C));}catch(e){}run();}).fail(()=>err('Weltdaten nicht erreichbar'));
})();
