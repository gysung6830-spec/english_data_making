# -*- coding: utf-8 -*-
"""고1 2026 9월 필생보에서 어법칩(강사용) 섹션만 추출."""
import re, os
src=open('make_pilsaengbo_v2.py').read()
src=re.sub(r'\nfor teacher,suf in .*', '\n', src, flags=re.S)
ns={'__file__':os.path.abspath('make_pilsaengbo_v2.py'),'__name__':'m'}
exec(compile(src, 'make_pilsaengbo_v2.py','exec'), ns)
P=ns['P']; CSS=ns['CSS']; render_grammar=ns['render_grammar']; SC=ns['SC']
from weasyprint import HTML
import fitz
body="".join(render_grammar(p, True) for p in P)
doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'
out=SC+"/고1_2026_9월_어법칩_강사용.pdf"
HTML(string=doc).write_pdf(out)
d=fitz.open(out); print("어법칩 강사용:", d.page_count,"p"); d.close()
print("OUT:", out)
