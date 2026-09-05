import re, os, html
S = os.path.dirname(os.path.abspath(__file__))
svg = open(S + '/master.svg').read()
inner = re.sub(r'^<svg[^>]*>', '', svg, count=1).rsplit('</svg>', 1)[0]
KEYS = ("hd", "hn", "ft", "ch")
SECTIONS = [
  ("hd", "头", "420 118 160 190", {
     "O": ("原版", "现在的胶囊头，一条竖槽。"),
     "A": ("面罩", "一条横向的深色面罩缝，两侧传感器圆盘，顶缝，下颌缝。"),
     "B": ("单镜头", "正中一枚圆形镜头，下方一道细缝，两侧传感器圆盘。"),
     "C": ("分体头盔", "头顶盖和下颌板分开，面罩缝就在两者的接缝处。"),
     "D": ("无面", "什么都不画：光滑的胶囊，只有背光侧的少量排线和脖子。"),
     "E": ("无面一缝", "无面，只留一道从头顶到下巴的细缝。")}),
  ("hn", "手", "95 118 250 235", {
     "O": ("原版", "现在的手套手，手指没有关节。"),
     "A": ("关节手", "手指分三节逐节变细，指节处有小圆关节，拇指同样。"),
     "B": ("左右交替", "Touch 那只手和举起的右手保留外壳，另外两只掀开成杆件加销钉的骨架手，按达芬奇左右交替。"),
     "C": ("手套", "最接近原版：手指逐渐变细、指根一道缝，不画关节圆。")}),
  ("ft", "脚", "150 796 490 134", {
     "O": ("原版", "现在的方块脚和尖头脚。"),
     "A": ("靴", "侧视的靴子：脚踝球关节、鞋头盖、底板，张开的腿脚底贴着圆。"),
     "B": ("分趾", "两片趾板加脚踝护套。"),
     "C": ("圆头鞋", "最简：圆头鞋身，脚踝只有一道环缝。")}),
  ("ch", "开胸机构", "390 280 220 220", {
     "O": ("原版", "现在的椎片加乱涂肋条，右侧平行直排线。"),
     "A": ("肋骨与肩缸", "结构：居中脊椎只露左半边，四道肋箍，肩关节液压缸（原版胸口那根斜缸的位置），两根液压干线沿脊椎向下。"),
     "B": ("齿轮泵", "动力：齿轮泵（圆壳里两枚啮合齿轮，驱动轴从壳体后面伸进来），肩关节液压缸，泵的出口接沿脊椎向下的两根干线，最下一道肋箍。"),
     "C": ("桁架", "框架：之字形桁架加节点销，两根液压干线沿脊椎向下。")}),
]
css_vars = ''.join('.%s-%s{display:var(--%s%s,none)}' % (k, v, k, v) for k in KEYS for v in "OABCDE")

cards = []
for key, title, vb, opts in SECTIONS:
    x, y, cw, ch = map(float, vb.split())
    row = []
    for v in opts:
        name, note = opts[v]
        btns = "" if v == "O" else "".join('<button type="button" class="score" data-k="%s" data-v="%s" data-s="%d" aria-pressed="false">%d</button>' % (key, v, s, s) for s in range(1, 6))
        rate = '<div class="rate"><div class="rate__btns" role="group" aria-label="%s %s 打分">%s</div><input class="rate__memo" type="text" data-k="%s" data-v="%s" placeholder="备注（可选）" maxlength="120"></div>' % (title, name, btns, key, v) if v != "O" else '<div class="rate rate--ref">参考，不打分</div>'
        row.append('''<article class="card%s">
  <header class="card__head"><span class="card__num">%s</span><h3 class="card__title">%s</h3></header>
  <p class="card__note">%s</p>
  <div class="fig"><svg viewBox="%s" style="--%s%s:inline" aria-label="%s %s"><use href="#fig" width="1000" height="1000"/></svg></div>
  %s
</article>''' % (" card--ref" if v == "O" else "", "原" if v == "O" else v, html.escape(name), html.escape(note), vb, key, v, html.escape(title), html.escape(name), rate))
    sel = "".join('<label class="pick"><input type="radio" name="pick-%s" value="%s"%s> %s</label>' % (key, v, ' checked' if v == "A" else '', "原版" if v == "O" else v + " " + opts[v][0]) for v in opts)
    cards.append('''<section class="sec" id="sec-%s">
  <h2 class="sec__title">%s</h2>
  <div class="row row--%s">%s</div>
</section>''' % (key, html.escape(title), key, "\n".join(row)))
    globals().setdefault("pickers", []).append('<div class="picker"><span class="picker__label">%s</span>%s</div>' % (html.escape(title), sel))

page = '''<title>维特鲁威人局部方案</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap">
<style>
:root{
  --ground:#f4f3f0; --paper:#ffffff; --ink:#1f1c18; --muted:#6c665d; --rule:#e2ded6;
  --sang:#8a6a4f; --sang-ink:#6e523b; --hot:#a8552b; --chip:#ece8e1; --ok:#3f7a4f; --plate:#ffffff;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#1b1917; --paper:#242120; --ink:#ebe6de; --muted:#a39c92; --rule:#3a3632;
    --sang:#b08a6a; --sang-ink:#c9a382; --hot:#d4794f; --chip:#2f2b28; --ok:#7fbc8f; --plate:#fbfaf7;
  }
}
:root[data-theme="dark"]{
  --ground:#1b1917; --paper:#242120; --ink:#ebe6de; --muted:#a39c92; --rule:#3a3632;
  --sang:#b08a6a; --sang-ink:#c9a382; --hot:#d4794f; --chip:#2f2b28; --ok:#7fbc8f; --plate:#fbfaf7;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:Lato,"PingFang SC","Hiragino Sans GB","Noto Sans SC",Helvetica,sans-serif;font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1240px;margin:0 auto;padding:28px 22px 80px}
.head{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px 32px;padding-bottom:18px;border-bottom:1px solid var(--rule);margin-bottom:8px}
h1{margin:0;font-family:Newsreader,Georgia,"Songti SC",serif;font-weight:500;font-size:34px;line-height:1.15;letter-spacing:-.01em;text-wrap:balance}
.head p{margin:6px 0 0;color:var(--muted);max-width:60ch}
.summary{display:flex;flex-direction:column;align-items:flex-end;gap:8px;min-width:280px}
.chips{display:flex;flex-wrap:wrap;gap:6px;justify-content:flex-end}
.chip{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;background:var(--chip);font-size:13px;font-variant-numeric:tabular-nums}
.chip b{font-weight:700}
.chip--empty{color:var(--muted)}
.status{display:flex;align-items:center;gap:12px;font-size:13px;color:var(--muted)}
.status .dot{width:7px;height:7px;border-radius:50%;background:var(--muted);display:inline-block;margin-right:6px;vertical-align:1px}
.status.is-saved .dot{background:var(--ok)}
.status.is-saving .dot{background:var(--hot)}
.copy{font:inherit;font-size:13px;color:var(--ink);background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:5px 11px;cursor:pointer}
.copy:hover{border-color:var(--sang)}
.copy:focus-visible,.score:focus-visible,.rate__memo:focus-visible,.pick input:focus-visible{outline:2px solid var(--hot);outline-offset:2px}
.sec{padding-top:26px}
.sec__title{margin:0 0 12px;font-family:Newsreader,Georgia,"Songti SC",serif;font-weight:500;font-size:26px}
.row{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.row--ft{grid-template-columns:repeat(2,minmax(0,1fr))}
.row--hd{grid-template-columns:repeat(3,minmax(0,1fr))}
@media (max-width:1000px){.row,.row--hd{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:600px){.row,.row--ft{grid-template-columns:1fr}.summary{align-items:flex-start}.chips{justify-content:flex-start}}
.card{background:var(--paper);border:1px solid var(--rule);border-radius:8px;padding:14px 16px;display:flex;flex-direction:column;gap:8px}
.card--ref{border-style:dashed}
.card__head{display:flex;align-items:baseline;gap:10px}
.card__num{font-family:Newsreader,Georgia,serif;font-size:24px;font-weight:600;color:var(--sang-ink);line-height:1}
.card__title{margin:0;font-size:17px;font-weight:700;line-height:1.3}
.card__note{margin:-2px 0 0;color:var(--muted);font-size:13.5px;min-height:3.9em}
.fig{background:var(--plate);border-radius:6px;padding:6px}
.fig svg{display:block;width:100%;height:auto;color:#8a6a4f}
.rate{display:flex;align-items:center;gap:10px;flex-wrap:wrap;border-top:1px solid var(--rule);padding-top:10px;margin-top:2px}
.rate--ref{color:var(--muted);font-size:13px}
.rate__btns{display:flex;gap:5px}
.score{font:inherit;font-weight:700;font-size:14px;width:34px;height:32px;border-radius:6px;border:1px solid var(--rule);background:transparent;color:var(--ink);cursor:pointer;font-variant-numeric:tabular-nums;transition:background .12s,color .12s,border-color .12s}
.score:hover{border-color:var(--sang)}
.score[aria-pressed="true"]{background:var(--sang);border-color:var(--sang);color:#fff}
.rate__memo{flex:1 1 120px;min-width:0;font:inherit;font-size:13px;padding:6px 9px;border:1px solid var(--rule);border-radius:6px;background:transparent;color:var(--ink)}
.rate__memo::placeholder{color:var(--muted)}
.combo{margin-top:34px;padding-top:26px;border-top:1px solid var(--rule)}
.combo__body{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:22px;align-items:start}
@media (max-width:820px){.combo__body{grid-template-columns:1fr}}
.pickers{display:flex;flex-direction:column;gap:14px;padding-top:6px}
.picker{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center}
.picker__label{font-weight:700;min-width:5.5em}
.pick{display:inline-flex;align-items:center;gap:5px;font-size:14px;cursor:pointer}
.combo p{color:var(--muted);margin:6px 0 0;font-size:14px}
.foot{margin-top:28px;color:var(--muted);font-size:13px}
.vm-geom{opacity:.55}.l-deep{opacity:.6}.l-shade{opacity:.7}
.l-halo{fill:none;stroke:#fff;stroke-width:2.6;stroke-linejoin:round}
.part{display:none}
__CSSVARS__
@media (prefers-reduced-motion:reduce){.score{transition:none}}
</style>
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><symbol id="fig" viewBox="0 0 1000 1000">__INNER__</symbol></svg>
<div class="wrap">
  <header class="head">
    <div>
      <h1>维特鲁威人局部方案</h1>
      <p>原图不动，只换头、手、脚和开胸机构。每个部位三个方案，按 1 到 5 打分，分数自动保存；页面最下面可以任意组合预览整图。</p>
    </div>
    <div class="summary">
      <div class="chips" id="chips"></div>
      <div class="status" id="status"><span><span class="dot"></span><span id="statusText">未打分</span></span><button type="button" class="copy" id="copy">复制打分</button></div>
    </div>
  </header>
__CARDS__
  <section class="combo" id="combo">
    <h2 class="sec__title">组合预览</h2>
    <div class="combo__body">
      <div class="fig"><svg viewBox="0 0 1000 1000" id="comboFig" style="--hdA:inline;--hnA:inline;--ftA:inline;--chA:inline" aria-label="组合预览"><use href="#fig" width="1000" height="1000"/></svg></div>
      <div class="pickers">
        __PICKERS__
        <p>组合选择也会一起保存。排线已按上一轮的 2 + 6 处理（减淡加留白），四肢的排线这一轮还没动。</p>
      </div>
    </div>
  </section>
  <p class="foot">局部放大图比主页尺寸大很多，粗细和密度请以组合预览为准。</p>
</div>
<script>
(function(){
  var KEYS = ['hd','hn','ft','ch'], NAMES = {hd:'头', hn:'手', ft:'脚', ch:'机构'}, KEY = 'vitruvian-parts-v1';
  var VARS = {hd:['A','B','C','D','E'], hn:['A','B','C'], ft:['A','B','C'], ch:['A','B','C']};
  var state = {scores:{}, memos:{}, combo:{hd:'A', hn:'A', ft:'A', ch:'A'}};
  var db = null, saveTimer = null, dirty = false;
  var chips = document.getElementById('chips'), statusEl = document.getElementById('status'), statusText = document.getElementById('statusText'), comboFig = document.getElementById('comboFig');

  function render(){
    var frag = '', any = false;
    KEYS.forEach(function(k){
      VARS[k].forEach(function(v){
        var s = state.scores[k + v];
        if (s){ any = true; frag += '<span class="chip">' + NAMES[k] + v + ' <b>' + s + '</b></span>'; }
        else frag += '<span class="chip chip--empty">' + NAMES[k] + v + ' –</span>';
      });
    });
    chips.innerHTML = frag;
    document.querySelectorAll('.score').forEach(function(b){
      b.setAttribute('aria-pressed', String(state.scores[b.dataset.k + b.dataset.v] == b.dataset.s));
    });
    document.querySelectorAll('.rate__memo').forEach(function(m){
      var v = state.memos[m.dataset.k + m.dataset.v] || '';
      if (m.value !== v && document.activeElement !== m) m.value = v;
    });
    KEYS.forEach(function(k){
      var r = document.querySelector('input[name="pick-' + k + '"][value="' + state.combo[k] + '"]');
      if (r) r.checked = true;
      ['O'].concat(VARS[k]).forEach(function(v){ comboFig.style.setProperty('--' + k + v, state.combo[k] === v ? 'inline' : 'none'); });
    });
    if (!any && !dirty) statusText.textContent = '未打分';
  }
  function summaryText(){
    var parts = [];
    KEYS.forEach(function(k){
      VARS[k].forEach(function(v){
        var s = state.scores[k + v] ? state.scores[k + v] : '–';
        var m = state.memos[k + v] ? '（' + state.memos[k + v] + '）' : '';
        parts.push(NAMES[k] + v + ':' + s + m);
      });
    });
    parts.push('组合:' + KEYS.map(function(k){ return NAMES[k] + state.combo[k]; }).join('+'));
    return parts.join('，');
  }
  function setStatus(cls, text){ statusEl.className = 'status ' + cls; statusText.textContent = text; }
  function persistLocal(){ try { localStorage.setItem(KEY, JSON.stringify(state)); } catch(e){} }
  function scheduleSave(){
    dirty = true; persistLocal(); setStatus('is-saving', '保存中…');
    clearTimeout(saveTimer); saveTimer = setTimeout(save, 400);
  }
  function save(){
    if (!db){ setStatus('is-saved', '已保存在本机'); return; }
    db.doc('parts/main').set({scores: state.scores, memos: state.memos, combo: state.combo, updatedAt: new Date().toISOString()})
      .then(function(){ dirty = false; setStatus('is-saved', '已保存'); })
      .catch(function(){ setStatus('is-saving', '保存失败，稍后重试'); saveTimer = setTimeout(save, 3000); });
  }

  try { var cached = JSON.parse(localStorage.getItem(KEY) || 'null'); if (cached && cached.scores){ state = cached; state.combo = state.combo || {hd:'A', hn:'A', ft:'A', ch:'A'}; } } catch(e){}
  render();

  document.addEventListener('click', function(e){
    var b = e.target.closest('.score'); if (!b) return;
    var id = b.dataset.k + b.dataset.v, s = +b.dataset.s;
    if (state.scores[id] === s) delete state.scores[id]; else state.scores[id] = s;
    render(); scheduleSave();
  });
  document.addEventListener('input', function(e){
    var m = e.target.closest('.rate__memo'); if (!m) return;
    var id = m.dataset.k + m.dataset.v, t = m.value.trim();
    if (t) state.memos[id] = t; else delete state.memos[id];
    scheduleSave();
  });
  document.addEventListener('change', function(e){
    var r = e.target.closest('input[type="radio"]'); if (!r) return;
    var k = r.name.replace('pick-', ''); state.combo[k] = r.value;
    render(); scheduleSave();
  });
  document.getElementById('copy').addEventListener('click', function(){
    var t = summaryText();
    var done = function(){ setStatus(statusEl.className.indexOf('is-saved') > -1 ? 'is-saved' : '', '已复制'); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, function(){ window.prompt('复制打分', t); });
    else window.prompt('复制打分', t);
  });

  if (window.claude && window.claude.use){
    window.claude.use('db').then(function(ns){
      db = ns; if (!db) return;
      return db.doc('parts/main').get().then(function(snap){
        if (snap && snap.exists && !dirty){
          var d = snap.data() || {};
          state = {scores: d.scores || {}, memos: d.memos || {}, combo: d.combo || {hd:'A', hn:'A', ft:'A', ch:'A'}};
          persistLocal(); render();
          if (Object.keys(state.scores).length) setStatus('is-saved', '已保存');
        } else if (dirty) { save(); }
      });
    }).catch(function(){});
  }
})();
</script>
'''
page = page.replace('__CSSVARS__', css_vars).replace('__INNER__', inner).replace('__CARDS__', "\n".join(cards)).replace('__PICKERS__', "\n        ".join(pickers))
open(S + '/vitruvian-parts.html', 'w').write(page)
print("bytes", len(page))
