#!/usr/bin/env python3
"""撮ったままの写真を images/full と images/thumb に書き出す。

使い方:
    python3 prepare-images.py 新しい写真のフォルダ

元の写真は変更しません。同名ファイルがあれば上書きします。
"""
import os, sys
from PIL import Image, ImageOps

SIZES = [('full', 1200, 84), ('thumb', 600, 80)]
EXTS = ('.jpg', '.jpeg', '.png', '.heic', '.webp')

src = sys.argv[1] if len(sys.argv) > 1 else '.'
here = os.path.dirname(os.path.abspath(__file__))

n = 0
for root, _, files in os.walk(src):
    for f in sorted(files):
        if not f.lower().endswith(EXTS):
            continue
        stem = os.path.splitext(f)[0]
        try:
            im = ImageOps.exif_transpose(Image.open(os.path.join(root, f))).convert('RGB')
        except Exception as err:
            print(f'  スキップ {f}: {err}')
            continue
        w, h = im.size
        for kind, mx, q in SIZES:
            out = os.path.join(here, 'images', kind)
            os.makedirs(out, exist_ok=True)
            o = im.copy()
            if w > mx:
                o = o.resize((mx, round(h * mx / w)), Image.LANCZOS)
            o.save(os.path.join(out, stem + '.jpg'), 'JPEG',
                   quality=q, optimize=True, progressive=True)
        n += 1
        print(f'  {f}  {w}x{h}  →  full / thumb')

print(f'\n{n}点を書き出しました。')
print('このあと data-beads.json に商品を追加して、python3 gen.py を実行してください。')
