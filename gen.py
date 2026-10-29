#!/usr/bin/env python3
"""beads.json から beadspark.net の静的サイトを生成する。"""
import json, os, re, html, shutil
from urllib.parse import quote

ROOT = 'site'
DATA = json.load(open('work/beads.json'))
ITEMS = DATA['items']

# ── 年代の帯 ────────────────────────────────────────────
BANDS = [
    ('ancient',      '古代',            '〜5世紀',      0,    500),
    ('medieval',     '中世・ルネサンス', '6〜16世紀',    501,  1600),
    ('modern',       '近代',            '17〜19世紀',   1601, 1900),
    ('contemporary', '近現代',          '20世紀以降',   1901, 9999),
]

def band_of(y):
    for b in BANDS:
        if b[3] <= y <= b[4]: return b
    return BANDS[-1]

def era_label(y):
    if y <= 1: return '1世紀頃'
    if y < 1000: return f'{y}年頃'
    return f'{y}年代'

def split_name(name):
    """【】で囲まれた部分を主題、その手前を来歴として分ける。"""
    m = re.search(r'【(.+?)】', name)
    if not m:
        return name, ''
    title = m.group(1).strip()
    lead = name[:m.start()].strip()
    return title, lead

def yen(n): return f'{n:,}'
def e(s):   return html.escape(str(s), quote=True)

for it in ITEMS:
    it['year'] = int(it['era']) if str(it['era']).isdigit() else 0
    it['band'] = band_of(it['year'])
    it['short'], it['lead'] = split_name(it['name'])
    for im in it['images']:
        im['stem'] = os.path.splitext(im['file'])[0]

SOLD = set()
if os.path.exists('sold.txt'):
    for ln in open('sold.txt', encoding='utf-8'):
        ln = ln.split('#')[0].strip()
        if ln: SOLD.add(ln)
for it in ITEMS:
    if it['id'] in SOLD: it['status'] = 'sold'

ITEMS.sort(key=lambda i: (i['year'], i['id']))
BY_ID = {i['id']: i for i in ITEMS}
CATS = sorted({i['category'] for i in ITEMS})

# ── 共通パーツ ──────────────────────────────────────────
def page(title, desc, body, rel='', extra_head='', body_class=''):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#131e1a">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;1,300&family=Shippori+Mincho:wght@400;600;800&family=Zen+Kaku+Gothic+New:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rel}assets/site.css">
{extra_head}
</head>
<body class="{body_class}">
<a class="skip" href="#main">本文へ移動</a>
<header class="hd">
  <a class="hd__brand" href="{rel}index.html">beadspark</a>
  <nav class="hd__nav">
    <a href="{rel}beads/index.html">コレクション</a>
    <a href="{rel}guide.html">お買い物について</a>
    <a href="{rel}drone.html">ドローン事業</a>
    <a href="{rel}contact.html">お問い合わせ</a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="ft">
  <div class="ft__mark">beadspark</div>
  <nav class="ft__nav">
    <a href="{rel}beads/index.html">コレクション</a>
    <a href="{rel}guide.html">お買い物について</a>
    <a href="{rel}law.html">特定商取引法に基づく表記</a>
    <a href="{rel}drone.html">ドローン事業</a>
    <a href="{rel}contact.html">お問い合わせ</a>
  </nav>
  <p class="ft__note">アンティークビーズには、作られた土地と時代があります。<br>&copy; 2026 beadspark ／ 福岡市早良区</p>
</footer>
</body>
</html>
"""

def card(it, rel):
    im = it['images'][0]
    sold = it['status'] == 'sold'
    price = ('<span class="card__price card__price--sold">売り切れ</span>' if sold
             else f'<span class="card__price">&yen;{yen(it["price"])}<small>税込</small></span>')
    badge = '<span class="soldbadge">SOLD</span>' if sold else ''
    return f"""<a class="card{' is-sold' if sold else ''}" href="{rel}beads/{it['id']}.html" data-cat="{e(it['category'])}" data-band="{it['band'][0]}" data-year="{it['year']}" data-sold="{'1' if sold else '0'}">
  <span class="card__fig">{badge}<img src="{rel}images/thumb/{e(im['stem'])}.jpg" alt="{e(it['short'])}" loading="lazy" width="600" height="400"></span>
  <span class="card__yr">{e(era_label(it['year']))}</span>
  <span class="card__ttl">{e(it['short'])}</span>
  <span class="card__lead">{e(it['lead'])}</span>
  {price}
</a>"""

# ══ トップページ ════════════════════════════════════════
counts = {b[0]: sum(1 for i in ITEMS if i['band'][0] == b[0]) for b in BANDS}
oldest, newest = ITEMS[0], ITEMS[-1]

def rep(bid):
    """その年代帯でいちばん高価なもの＝代表として写真を使う。"""
    g = [i for i in AVAIL if i['band'][0] == bid] or [i for i in ITEMS if i['band'][0] == bid]
    return max(g, key=lambda i: i['price']) if g else None

AVAIL = [i for i in ITEMS if i['status'] != 'sold'] or ITEMS
hero_item = max(AVAIL, key=lambda i: i['price'])
picks = [i for i in sorted(AVAIL, key=lambda i: -i['price'])[:9] if i is not hero_item][:8]
strip = sorted(ITEMS, key=lambda i: i['year'])
strip = [strip[round(k * (len(strip) - 1) / 13)] for k in range(14)]

scale = ''
for b in BANDS:
    r = rep(b[0])
    scale += f"""<a class="band-card" href="beads/index.html#{b[0]}">
  <span class="band-card__fig"><img src="images/thumb/{e(r['images'][0]['stem'])}.jpg" alt="{e(b[1])}の一例" loading="lazy" width="600" height="400"></span>
  <span class="band-card__n">{counts[b[0]]}<small>点</small></span>
  <span class="band-card__nm">{b[1]}</span>
  <span class="band-card__rg">{b[2]}</span>
</a>"""

cat_cards = ''
for ci, c in enumerate(CATS):
    g = [i for i in ITEMS if i['category'] == c]
    r = max([i for i in g if i['status'] != 'sold'] or g, key=lambda i: i['price'])
    cat_cards += f"""<a class="cat" href="beads/index.html#cat-{ci}">
  <img src="images/thumb/{e(r['images'][0]['stem'])}.jpg" alt="" loading="lazy" width="600" height="400">
  <span class="cat__nm">{e(c)}<b>{len(g)}</b></span>
</a>"""

tiles = ''.join(
    f'<a class="tile" href="beads/{i["id"]}.html" title="{e(i["short"])}">'
    f'<img src="images/thumb/{e(i["images"][0]["stem"])}.jpg" alt="{e(i["short"])}" loading="lazy" width="600" height="400">'
    f'<span>{e(era_label(i["year"]))}</span></a>' for i in strip)

home = f"""
<section class="hero hero--img">
  <div class="hero__txt">
    <p class="eyebrow">アンティークビーズ ／ とんぼ玉</p>
    <h1>紀元1世紀から現代に<br><i>時を超えて</i></h1>
    <p class="hero__lead">地中海のローマンガラス、ヴェネチアのシェブロン、チベットのDzi beads。産地と時代のはっきりしたビーズだけを選び、一連のネックレスに仕立てました。同じものは二つとありません。</p>
    <a class="btn" href="beads/index.html">コレクション全{len(ITEMS)}点を見る</a>
  </div>
  <a class="hero__fig" href="beads/{hero_item['id']}.html">
    <img src="images/full/{e(hero_item['images'][0]['stem'])}.jpg" alt="{e(hero_item['short'])}" width="1200" height="800">
    <span class="hero__cap"><b>{e(era_label(hero_item['year']))}</b>{e(hero_item['short'])}</span>
  </a>
</section>

<section class="strip" aria-label="年代順の一覧">
  <div class="strip__inner">{tiles}</div>
  <p class="strip__note">←　古い順にならべています　→</p>
</section>

<section class="sec">
  <div class="sec__head"><h2>年代からさがす</h2><a class="more" href="beads/index.html">全{len(ITEMS)}点</a></div>
  <div class="bands4">{scale}</div>
</section>

<section class="sec">
  <div class="sec__head"><h2>いま並んでいるもの</h2><a class="more" href="beads/index.html">すべて見る</a></div>
  <div class="grid">{''.join(card(i,'') for i in picks)}</div>
</section>

<section class="sec sec--quote">
  <blockquote>
    <p>いちばん古いのは<b>{e(era_label(oldest['year']))}</b>のもの。<br>いちばん新しいのは{e(era_label(newest['year']))}。<br>その間に、ガラスの作り方が何度も変わりました。</p>
  </blockquote>
</section>

<section class="sec">
  <div class="sec__head"><h2>産地からさがす</h2></div>
  <div class="cats">{cat_cards}</div>
</section>

<section class="sec--drone">
  <a class="drone" href="drone.html">
    <img src="images/full/Ac101-sannpu.jpg" alt="農業用ドローンによる散布作業" loading="lazy" width="1400" height="789">
    <span class="drone__txt">
      <span class="eyebrow">もうひとつの仕事</span>
      <span class="drone__h">農業ドローン散布。<br>点検事業は株式会社KENZAKI DRへ。</span>
      <span class="drone__more">ドローン事業と法人化のお知らせ →</span>
    </span>
  </a>
</section>
"""
os.makedirs(ROOT, exist_ok=True)
open(f'{ROOT}/index.html', 'w').write(page(
    'beadspark｜アンティークビーズ・とんぼ玉のネックレス',
    '紀元1世紀のローマンガラスから現代まで。産地と時代のはっきりしたアンティークビーズを一連のネックレスに仕立てて販売しています。福岡市早良区。',
    home))

# ══ 一覧ページ ══════════════════════════════════════════
groups = ''
for b in BANDS:
    g = [i for i in ITEMS if i['band'][0] == b[0]]
    if not g: continue
    groups += f"""<section class="band" id="{b[0]}">
  <div class="band__rail"><h2>{b[1]}</h2><p>{b[2]}</p><p class="band__n">{len(g)}点</p></div>
  <div class="grid">{''.join(card(i,'../') for i in g)}</div>
</section>"""

chips = '<button class="chip is-on" data-f="all">すべて</button>' + \
    ''.join(f'<button class="chip" data-f="{e(c)}">{e(c)}</button>' for c in CATS)

listing = f"""
<section class="lead">
  <p class="eyebrow">コレクション</p>
  <h1>全{len(ITEMS)}点</h1>
  <p class="lead__p">作られた年代の古い順に並べています。産地で絞り込むこともできます。<br>
  すべて一点ものです。ご注文をいただいたあとに在庫を確認し、2営業日以内にお返事いたします。</p>
  <div class="chips" role="group" aria-label="産地で絞り込む">{chips}</div>
  <label class="only"><input type="checkbox" id="onlyav"> 販売中のみ表示</label>
  <p class="hit" aria-live="polite"></p>
</section>
{groups}
<script>
(function(){{
  var chips=document.querySelectorAll('.chip'),
      cards=document.querySelectorAll('.card'),
      bands=document.querySelectorAll('.band'),
      hit=document.querySelector('.hit');
  var av=document.getElementById('onlyav');
  function apply(f){{
    var n=0;
    cards.forEach(function(c){{
      var on = (f==='all' || c.dataset.cat===f);
      if(av.checked && c.dataset.sold==='1') on=false;
      c.hidden = !on; if(on) n++;
    }});
    bands.forEach(function(b){{
      b.hidden = !b.querySelector('.card:not([hidden])');
    }});
    hit.textContent = (f==='all' && !av.checked) ? '' : n+'点を表示中';
  }}
  av.addEventListener('change',function(){{
    var on=document.querySelector('.chip.is-on');
    apply(on?on.dataset.f:'all');
  }});
  chips.forEach(function(ch){{
    ch.addEventListener('click',function(){{
      chips.forEach(function(x){{x.classList.remove('is-on')}});
      ch.classList.add('is-on'); apply(ch.dataset.f);
    }});
  }});
}})();
</script>
"""
os.makedirs(f'{ROOT}/beads', exist_ok=True)
open(f'{ROOT}/beads/index.html', 'w').write(page(
    f'コレクション 全{len(ITEMS)}点｜beadspark',
    f'アンティークビーズのネックレス全{len(ITEMS)}点。ヴェネチア、ローマンガラス、Dzi beadsなど、産地と年代別に一覧できます。',
    listing, rel='../'))

# ══ 商品詳細 ════════════════════════════════════════════
MAIL = 'info@beadspark.net'
for idx, it in enumerate(ITEMS):
    prev_, next_ = ITEMS[idx-1] if idx else None, ITEMS[idx+1] if idx+1 < len(ITEMS) else None
    imgs = it['images']
    thumbs = ''.join(
        f'<button class="th{" is-on" if k==0 else ""}" data-src="../images/full/{e(im["stem"])}.jpg" aria-label="画像{k+1}枚目">'
        f'<img src="../images/thumb/{e(im["stem"])}.jpg" alt="" loading="lazy" width="600" height="400"></button>'
        for k, im in enumerate(imgs)) if len(imgs) > 1 else ''

    spec = it['spec']
    rows = [('商品番号', it['id']), ('製作年代', era_label(it['year'])), ('産地・系統', it['category'])]
    if 'width' in spec:  rows.append(('全長', f"約{spec['width']}mm"))
    if 'height' in spec: rows.append(('玉のサイズ', f"約{spec['height']}×{spec['depth']}mm"))
    if 'weight' in spec: rows.append(('重量', f"約{spec['weight']}{it['weight_unit'] or 'g'}"))

    subj = f"[在庫確認・ご注文] {it['id']} {it['short']}"
    body_ = ("下記の商品について、在庫の確認とご注文をお願いします。\r\n\r\n"
             f"商品番号：{it['id']}\r\n商品名：{it['short']}\r\n"
             f"価格：{yen(it['price'])}円（税込）\r\n\r\n"
             "--------\r\nお名前：\r\nご住所：\r\nお電話番号：\r\nご質問など：\r\n--------\r\n\r\n"
             "※一点もののため、在庫を確認のうえ2営業日以内にお返事いたします。\r\n"
             "※お支払いは銀行振込のみです。在庫がある場合、あわせて振込先と送料をご案内いたします。")
    mailto = f"mailto:{MAIL}?subject={quote(subj)}&amp;body={quote(body_)}"

    if it['status'] == 'sold':
        buybox = ('<p class="item__price item__price--sold">売り切れました</p>'
                  '<p class="item__pay">この一点は販売済みです。すべて一点もののため、'
                  '同じものをご用意することはできません。<br>'
                  '似た年代・産地のものをお探しでしたら、'
                  f'<a href="../contact.html">お問い合わせ</a>ください。</p>'
                  '<a class="btn btn--ghost" href="index.html">ほかの一点を見る</a>')
    else:
        buybox = (f'<p class="item__price">&yen;{yen(it["price"])}<small>税込</small></p>'
                  f'<a class="btn" href="{mailto}">在庫を確認して注文する</a>'
                  '<div class="item__pay">'
                  '<p><b>すべて一点ものです。</b>行き違いですでに売り切れている場合があります。'
                  'ご注文をいただいたあとに在庫を確認し、2営業日以内にお返事いたします。</p>'
                  '<p>在庫がある場合は、あわせて振込先と送料をご案内します。'
                  'お支払いは<b>銀行振込のみ</b>、ご入金の確認後に発送いたします。'
                  'この時点ではまだご注文は確定しませんので、ご安心ください。</p>'
                  '<p>ボタンを押すとメールが開きます。商品番号が入っていますので、'
                  'お名前とご住所を書き添えて送信してください。</p>'
                  '</div>')

    detail = f"""
<nav class="crumb"><a href="../index.html">ホーム</a> ／ <a href="index.html">コレクション</a> ／ <span>{e(it['id'])}</span></nav>

<article class="item">
  <div class="item__media">
    <div class="stage"><img id="stage" src="../images/full/{e(imgs[0]['stem'])}.jpg" alt="{e(it['short'])}" width="1200" height="800"></div>
    <div class="ths">{thumbs}</div>
  </div>

  <div class="item__body">
    <p class="item__lead">{e(it['lead'])}</p>
    <h1>{e(it['short'])}</h1>
    <p class="item__yr"><span>{e(era_label(it['year']))}</span>{e(it['category'])}{'<b class="yr-sold">SOLD</b>' if it['status']=='sold' else ''}</p>

    {buybox}

    <div class="desc"><p>{'<br>'.join(x for x in e(it['description']).replace('。','。\n').split('\n') if x.strip())}</p></div>

    <table class="spec">
      <tbody>{''.join(f'<tr><th>{e(a)}</th><td>{e(b)}</td></tr>' for a, b in rows)}</tbody>
    </table>
    <p class="onlyone">一点ものです。同じものはありません。</p>
  </div>
</article>

<nav class="pager">
  {f'<a class="pager__a" href="{prev_["id"]}.html"><span>前の年代</span>{e(prev_["short"])}</a>' if prev_ else '<span></span>'}
  {f'<a class="pager__a pager__a--r" href="{next_["id"]}.html"><span>次の年代</span>{e(next_["short"])}</a>' if next_ else '<span></span>'}
</nav>

<script>
(function(){{
  var st=document.getElementById('stage');
  document.querySelectorAll('.th').forEach(function(b){{
    b.addEventListener('click',function(){{
      st.src=b.dataset.src;
      document.querySelectorAll('.th').forEach(function(x){{x.classList.remove('is-on')}});
      b.classList.add('is-on');
    }});
  }});
}})();
</script>
"""
    open(f'{ROOT}/beads/{it["id"]}.html', 'w').write(page(
        f"{it['short']}｜{era_label(it['year'])}｜beadspark",
        (it['description'][:110] + '…'),
        detail, rel='../',
        extra_head=('<meta name="robots" content="noindex,follow">' if it['status'] == 'sold' else '')))

# ══ 固定ページ ══════════════════════════════════════════
guide = """
<section class="lead">
  <p class="eyebrow">お買い物について</p>
  <h1>ご注文から<br>お届けまで</h1>
</section>
<section class="prose">
  <h2>ご注文の流れ</h2>
  <ol>
    <li>商品ページの「在庫を確認して注文する」からメールをお送りください。商品番号が入った状態でメールが開きます。お名前とご住所を書き添えてください。</li>
    <li><b>在庫を確認し、2営業日以内にお返事します。</b>在庫がある場合は、振込先と送料を含めた合計金額をあわせてご案内します。この時点でご注文が確定します。</li>
    <li>ご入金を確認しだい、3営業日以内に発送いたします。</li>
  </ol>
  <p>メールをお送りいただいた時点では、まだご注文は確定しません。在庫の有無をお知らせしたうえで、あらためてご判断いただけます。</p>

  <h2>在庫について</h2>
  <p>すべて一点ものです。同じ商品は二つとなく、一度売れると再入荷はありません。</p>
  <p>実店舗やイベントでの販売、他のお客様とのご注文の行き違いにより、<b>サイトに掲載されていても、すでに売り切れている場合があります。</b>そのため、ご注文をいただいてから在庫を確認する形をとらせていただいています。</p>
  <p>売り切れの場合は、その旨をお知らせしたうえでキャンセルとさせていただきます。代金をお預かりする前ですので、お客様のご負担は発生しません。もし似た年代・産地のものをお探しでしたら、あわせてご紹介いたします。</p>

  <h2>お支払い</h2>
  <p>銀行振込のみとなります。振込手数料はお客様のご負担でお願いいたします。カード決済および代金引換には対応しておりません。</p>

  <h2>配送</h2>
  <p>ご入金確認後、3営業日以内に発送します。配送方法と送料はご注文時にご案内します。海外への発送はご相談ください。</p>

  <h2>一点ものについて</h2>
  <p>すべて一点ものです。同じ商品を再度ご用意することはできません。<br>アンティークビーズには、製作当時の気泡、擦れ、欠け、色むらがあります。これらは古い玉が経てきた時間の一部であり、不良ではありません。気になる箇所は、ご注文前にお問い合わせいただければ追加の写真をお送りします。</p>

  <h2>返品・交換</h2>
  <p>商品の破損・汚損、またはご注文と異なる商品が届いた場合は、到着後7日以内にご連絡ください。送料当方負担で交換または返金いたします。<br>お客様のご都合による返品は、一点ものという性質上お受けしておりません。</p>

  <h2>お手入れ</h2>
  <p>古いガラスや天然素材を使っています。入浴時や就寝時は外し、汗や香水が付いた際は乾いた柔らかい布で拭き取ってください。</p>
</section>
"""
open(f'{ROOT}/guide.html', 'w').write(page(
    'お買い物について｜beadspark', 'ご注文の流れ、お支払い（銀行振込のみ）、配送、返品についてご案内します。', guide))

law = """
<section class="lead">
  <p class="eyebrow">Legal</p>
  <h1>特定商取引法に<br>基づく表記</h1>
</section>
<section class="prose">
  <table class="spec spec--wide"><tbody>
    <tr><th>販売業者</th><td>beadspark</td></tr>
    <tr><th>運営責任者</th><td>検崎 雄二</td></tr>
    <tr><th>所在地</th><td>〒814-0012<br>福岡県福岡市早良区昭代3-10-27</td></tr>
    <tr><th>電話番号</th><td><a href="tel:09074419440">090-7441-9440</a><br><small>受付時間：平日 10:00〜17:00<br>点検・散布の作業中は出られないことがあります。メールでもご連絡いただけます。</small></td></tr>
    <tr><th>メールアドレス</th><td>info@beadspark.net</td></tr>
    <tr><th>販売価格</th><td>各商品ページに表示された金額（消費税込）</td></tr>
    <tr><th>商品代金以外の必要料金</th><td>送料、振込手数料</td></tr>
    <tr><th>お支払い方法</th><td>銀行振込のみ</td></tr>
    <tr><th>お支払い期限</th><td>ご案内から7日以内</td></tr>
    <tr><th>引渡し時期</th><td>ご注文後に在庫を確認し、2営業日以内に可否をご連絡します。<br>ご入金確認後、3営業日以内に発送します。</td></tr>
    <tr><th>在庫と注文の確定</th><td>すべて一点ものです。掲載中の商品でも、行き違いにより売り切れている場合があります。<br>ご注文メールの受信時点では契約は成立せず、当方から在庫の確認と代金のご案内をお送りした時点で成立するものとします。<br>売り切れの場合はキャンセルとさせていただきます。代金をお預かりする前のため、お客様のご負担は発生しません。</td></tr>
    <tr><th>返品・交換</th><td>商品の破損・汚損、または誤配送の場合は、到着後7日以内にご連絡ください。送料当方負担で交換または返金いたします。<br>お客様のご都合による返品は、一点ものという商品の性質上お受けしておりません。</td></tr>
  </tbody></table>
</section>
"""
LAW_HEAD = '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">'
open(f'{ROOT}/law.html', 'w').write(page(
    '特定商取引法に基づく表記｜beadspark', 'beadsparkの特定商取引法に基づく表記です。', law, extra_head=LAW_HEAD))

drone = """
<section class="lead">
  <p class="eyebrow">ドローン事業</p>
  <h1>太陽光発電設備の<br>赤外線点検と、<br>農業ドローン散布。</h1>
  <p class="lead__p">beadsparkは福岡市早良区を拠点に、農業用ドローンによる農薬散布を行っています。赤外線ドローン点検と解析ソフトウェア「IR Works AI」などの新しいご依頼は、株式会社KENZAKI DRで承ります。</p>
</section>
<section class="prose">
  <h2>ドローン点検事業の法人化について</h2>
  <p>ドローン点検を中心とする事業を法人化し、<b>株式会社KENZAKI DR</b>（2026年11月設立予定・現在設立準備中）に移すことになりました。</p>
  <ul>
    <li>赤外線ドローン点検・空撮・ドローン講習・IRシリーズの新規のご依頼は、株式会社KENZAKI DR（<a href="https://kenzaki-dr.jp/">kenzaki-dr.jp</a>／info@kenzaki-dr.jp）で承ります。</li>
    <li>現在beadsparkとご契約いただいている業務は、契約の名義・内容・請求書の発行元・お振込先を変えずに、beadsparkのまま最後までお引き受けします。お手続きは必要ありません。</li>
    <li>農薬散布の請負とアンティークビーズの販売は、これまでどおりbeadsparkで承ります。</li>
    <li>担当はこれまでと同じ検崎です。お電話とメールの連絡先も、そのままお使いいただけます。</li>
  </ul>

  <figure class="shot"><img src="images/full/tenken_mv2.jpg" alt="点検に使用するドローン" loading="lazy" width="1400" height="787"></figure>

  <h2>太陽光発電設備のドローン点検</h2>
  <p>赤外線カメラを搭載したドローンでアレイ全面を撮影し、ホットスポット、クラスタ故障、ストリング異常を検出します。電気的診断と組み合わせた原因の切り分けにも対応します。低圧からメガソーラーまで、O&amp;M事業者様からの外注もお受けしています。<br><small>新規のご依頼は株式会社KENZAKI DRで承ります。</small></p>

  <figure class="shot"><img src="images/full/Ac101-sannpu.jpg" alt="農業用ドローンによる散布作業" loading="lazy" width="1400" height="789"></figure>

  <h2>農業用ドローンによる散布</h2>
  <p>水稲を中心に、防除・追肥の散布作業を請け負います。圃場の状況に応じて散布計画を立て、繁忙期も機体とバッテリーの運用体制を整えて対応しています。</p>

  <h2>IR Works AI</h2>
  <p>ドローンで撮影した赤外線画像から異常発熱箇所を抽出し、点検報告書の作成までを支援するソフトウェアです。点検現場の実作業をそのまま設計に落とし込んでいます。株式会社KENZAKI DRが開発・提供します。</p>

  <p class="prose__cta"><a class="btn" href="https://kenzaki-dr.jp/">点検のご依頼（株式会社KENZAKI DR）</a></p>
  <p class="prose__cta"><a class="btn" href="contact.html">散布について問い合わせる</a></p>
</section>
"""
open(f'{ROOT}/drone.html', 'w').write(page(
    'ドローン事業｜太陽光発電設備の赤外線点検・農業散布｜beadspark',
    '福岡市早良区。農業用ドローンによる散布作業の請負。赤外線ドローン点検とIR Works AIの新規のご依頼は株式会社KENZAKI DRで承ります。', drone))

contact = f"""
<section class="lead">
  <p class="eyebrow">お問い合わせ</p>
  <h1>メールで<br>承っています。</h1>
  <p class="lead__p">ビーズのご注文・ご質問、ドローン点検や散布のご相談は、こちらまでお送りください。2営業日以内にお返事します。</p>
</section>
<section class="prose">
  <p class="prose__cta"><a class="btn" href="mailto:{MAIL}">{MAIL}</a></p>
  <p class="legalnote">お問い合わせはメールにて承っております。<br>散布の繁忙期はお返事にお時間をいただく場合があります。</p>

  <h2>ビーズについてお問い合わせの場合</h2>
  <p>気になる商品の<b>商品番号</b>をお書き添えください。追加の写真が必要な場合は、見たい箇所（留め具、玉の裏側など）をお知らせいただければお送りします。</p>
  <p>すべて一点ものです。掲載中でも売り切れている場合がありますので、在庫の確認だけのお問い合わせもお気軽にどうぞ。</p>

  <h2>ドローン事業についてお問い合わせの場合</h2>
  <p>散布のご依頼は、<b>圃場の面積と作物</b>をお書きください。</p>
  <p>赤外線ドローン点検・空撮・ドローン講習・IRシリーズの新しいご依頼は、株式会社KENZAKI DR（<a href="https://kenzaki-dr.jp/">kenzaki-dr.jp</a>／info@kenzaki-dr.jp）で承ります。設備の<b>所在地・規模（kW）・ご希望の時期</b>をお知らせください。現在ご契約中の業務は、これまでどおりこちらのアドレスで承ります。</p>

  <p class="legalnote">散布の繁忙期はお返事にお時間をいただく場合があります。</p>
</section>
"""
open(f'{ROOT}/contact.html', 'w').write(page(
    'お問い合わせ｜beadspark', 'アンティークビーズのご注文、ドローン点検・散布のご相談はメールにて承ります。', contact))

print('生成完了:', len([f for _, _, fs in os.walk(ROOT) for f in fs if f.endswith('.html')]), 'ページ')
