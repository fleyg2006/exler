"""Reproduce lexical markers from extracted author product sections (stdlib only)."""
import json
import re
from pathlib import Path

root = Path('product_analysis')
rows = json.loads((root / 'placements.json').read_text())
sections = {}
for row in rows:
    sections[(row['post_id'], row['section'])] = row['section_text']
posts = {}
for (post_id, section), text in sections.items():
    posts.setdefault(post_id, []).append(text)
patterns = {
    'personal_experience': r'пользуюсь|у меня|себе купил|себе заказал',
    'convenience': r'удобн',
    'compactness': r'компактн',
    'low_price': r'недорог|дешев',
    'praise': r'отличн',
    'ordered': r'заказал',
    'review': r'обзор',
}
result = {
    'unit': 'edition containing at least one regex match in extracted product sections',
    'limitations': 'Lexical markers, not semantic labels; sections without extracted product links omitted. Reader comments and repeated footer excluded.',
    'editions': len(posts),
    'sections': len(sections),
    'markers': {
        name: {'pattern': pattern, 'edition_ids': sorted(
            post_id for post_id, texts in posts.items()
            if re.search(pattern, ' '.join(texts), re.I)
        )} for name, pattern in patterns.items()
    },
}
(root / 'style_markers.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
