#!/usr/bin/env python3
"""Embed the generated sprite sheets into science-kombat.html as base64 data URIs.

Replaces the block between the SPRITE_DATA markers so sheets can be
regenerated and re-embedded at any time:
    python3 design/generate_sprites.py && python3 design/embed_sprites.py
"""
import base64, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, '..', 'science-kombat.html')
SHEETS = os.path.join(HERE, 'sheets')

IDS = ['einstein', 'tesla', 'curie', 'newton', 'darwin', 'hawking',
       'ada', 'franklin', 'johnson', 'galileo', 'turing', 'archimedes']

def main():
    entries = []
    total = 0
    for cid in IDS:
        path = os.path.join(SHEETS, cid + '.png')
        data = base64.b64encode(open(path, 'rb').read()).decode()
        total += len(data)
        entries.append(f"{cid}:'data:image/png;base64,{data}'")
    block = ('/*__SPRITE_DATA_START__*/\n'
             'const SPRITE_SHEETS={' + ',\n'.join(entries) + '};\n'
             '/*__SPRITE_DATA_END__*/')
    html = open(HTML, encoding='utf-8').read()
    pat = re.compile(r'/\*__SPRITE_DATA_START__\*/.*?/\*__SPRITE_DATA_END__\*/', re.S)
    if not pat.search(html):
        sys.exit('SPRITE_DATA markers not found in science-kombat.html')
    open(HTML, 'w', encoding='utf-8').write(pat.sub(lambda _: block, html))
    print(f'embedded {len(IDS)} sheets, {total//1024} KiB base64')

if __name__ == '__main__':
    main()
