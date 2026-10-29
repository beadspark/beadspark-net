# beadspark.net

アンティークビーズ中心の静的サイト。ビルド不要、そのままVercelに置けます。

## 構成

```
index.html          トップ
beads/index.html    コレクション一覧（全90点・産地で絞り込み）
beads/N130006.html  商品詳細 × 90
guide.html          お買い物について
law.html            特定商取引法に基づく表記（noindex）
drone.html          ドローン事業
contact.html        お問い合わせ
assets/site.css     全ページ共通のスタイル
images/full/        詳細用（幅1200px）383点
images/thumb/       一覧用（幅600px）383点
gen.py              全HTMLの生成スクリプト
data-beads.json     商品データ
sitemap.xml / robots.txt
```

## 個人情報の扱い（重要）

氏名・住所・電話番号は **law.html にのみ** 記載しています。以下の対策を入れています。

- `law.html` に `noindex, nofollow, noarchive, nosnippet` を指定（検索結果に出さない）
- `sitemap.xml` から law.html を除外
- `robots.txt` で `Disallow: /law.html`
- 電話番号を `tel:` リンクにしない（自動収集とワンタップ発信を防ぐ）
- 電話番号をspanで分割（単純な正規表現による抜き出しを外す）
- フッターと他ページには一切載せない

**HTMLを直接編集する際は、この情報を他のページに書き足さないでください。**
全96ページ共通のフッターに1行足すだけで、対策が無意味になります。

確認コマンド:

```bash
grep -rl '9440\|検崎\|昭代3-10-27' . --include=*.html
# → law.html のみが出れば正常
```

## 公開手順

```bash
cd beadspark-net
git init && git add . && git commit -m "beadspark.net 初版"
git remote add origin git@github.com:beadspark/beadspark-net.git
git push -u origin main
```

Vercel で Import → Framework Preset は **Other**、Build Command と Output Directory は空欄。
Settings → Domains に `beadspark.net` / `www.beadspark.net` を追加してDNSを設定。

## 公開前の確認

- `info@beadspark.net` が実際に受信できるか（全90点の注文ボタンがこの宛先）
- 郵便番号 814-0012（昭代）を日本郵便のデータで確認済み
- 価格の端数（28,009円など。ShopServeの税処理の名残）

## 画像フォルダについて

`images/full`（幅1200px・詳細用）と `images/thumb`（幅600px・一覧用）は自動生成です。
元の写真を手で分ける必要はありません。

新しい写真を追加するとき:

```bash
pip install pillow            # 初回のみ
python3 prepare-images.py ~/Desktop/新しい写真
```

撮ったままの写真を渡せば、2サイズに書き出して所定の場所に置きます。
元の写真は変更しません。ファイル名（拡張子を除く）がそのまま識別子になるので、
`data-beads.json` の `images[].file` にはその名前を書きます。

## 売り切れにする

`sold.txt` に商品番号を1行ずつ書いて `python3 gen.py` を実行します。

```
N130006
N130002   # 「#」から後ろはメモ。無視されます
```

反映されること:

- 一覧カードに SOLD バッジ、写真は彩度を落として表示
- 価格の代わりに「売り切れ」
- 詳細ページは注文ボタンが消え、「売り切れました」＋問い合わせ導線に
- 詳細ページに noindex を付与（検索結果に新規で出さない）
- トップの主役写真・おすすめ8点・年代/産地のカバー写真は販売中から自動で選び直し
- 一覧の「販売中のみ表示」チェックで隠せる

売り切れた商品もページ自体は残します。過去に何を扱ってきたかが見えるほうが、
アンティークを扱う店としては信用につながるためです。完全に消したい場合は
`data-beads.json` からその商品を削除してください。

## 商品を追加・変更する

`data-beads.json` を編集して `python3 gen.py` を流すと全ページが再生成されます。
HTMLは直接編集せず、`gen.py` のテンプレートを直してください。

## Claude Code への指示（そのまま貼れます）

```
beadspark-net リポジトリ。ビルドツールなしの静的サイトで、
gen.py が data-beads.json から全96ページを生成します。

守ること:
- HTMLを直接編集しない。gen.py のテンプレートを直して再生成する
- 氏名・住所・電話番号は law.html 以外に絶対に出さない。
  フッターや共通テンプレートへの追記は禁止。
  作業後に `grep -rl '9440' . --include=*.html` で law.html のみか確認すること
- 色とフォントは assets/site.css の :root 変数経由のみ。生のhexを増やさない
  (--ground/--patina/--gold/--cinnabar/--ivory 系、--f-lat/--f-jp/--f-ui)
- 年代の古い順に並べる構成がこのサイトの背骨。並び順の意味を壊さない
- prefers-reduced-motion 対応とキーボードフォーカス表示は維持

依頼:
1. 売り切れ商品を一覧の末尾にまとめて並べる（現在は年代順のまま混在）
2. 一覧に価格帯の絞り込みを追加（〜1万円 / 1〜3万円 / 3万円〜）
```

## 未実装

- 価格帯での絞り込み
- 商品説明の推敲（旧サイトの文面をそのまま流用）
