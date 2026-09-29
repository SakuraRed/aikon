"""One evidence-led local revision of the independent v1 drawing."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from generate_v1 import SVG, render_svg_file, validate_svg

CHANGES = {
    '#404966': '#303953',
    'M0-106 C30-106 50-83 50-53 L50 54 C50 83 30 105 0 105 C-30 105-51 83-51 54 L-51-53 C-51-83-30-106 0-106Z': 'M0-107.7 C31-107.7 51.7-84 51.7-54 L51.7 54 C51.7 84.6 31 106.7 0 106.7 C-31.7 106.7-52.7 84.7-52.7 54 L-52.7-54 C-52.7-84.7-31-107.7 0-107.7Z',
    'M0-102 C29-102 49-80 49-51 L49 51 C49 80 29 102 0 102 C-30 102-50 80-50 51 L-50-51 C-50-80-30-102 0-102Z': 'M0-103.7 C30-103.7 50.7-81 50.7-51 L50.7 51 C50.7 81 30 103.7 0 103.7 C-30.7 103.7-51.7 81-51.7 51 L-51.7-51 C-51.7-81-30-103.7 0-103.7Z',
    'fill="#324884" d="M667 509 C663 642 715 798 780 879 L804 916 C761 816 711 692 680 620Z"': 'fill="#3a508d" d="M667 509 C664 572 669 605 680 637 C704 713 744 817 788 888 L804 916 C765 837 722 739 698 675 C676 613 667 562 667 509Z"',
}

def main():
    revised = SVG
    for old, new in CHANGES.items():
        assert revised.count(old) == 1, old
        revised = revised.replace(old, new)
    target = HERE / 'v2'
    target.mkdir(exist_ok=True)
    (target / 'short.svg').write_text(revised, encoding='utf-8')
    (target / 'prompt.txt').write_bytes((HERE / 'prompt-v2.txt').read_bytes())
    (target / 'revision-source.py').write_bytes(Path(__file__).read_bytes())
    validate_svg(revised)
    reports = {}
    for size in [1280, 128, 48, 24]:
        reports[str(size)] = render_svg_file(target / 'short.svg', target / f'preview-{size}.png', size)
        shutil.copyfile(target / f'preview-{size}.png', HERE / f'preview-{size}.png')
    shutil.copyfile(target / 'short.svg', HERE / 'short.svg')
    reports['changes'] = ['eye inner fill expanded; exterior fixed; rim contrast reduced', 'one center-fringe cast shadow narrowed and softened; all other shapes fixed']
    reports['status'] = 'structurally_checked; visual_review_pending; user_acceptance_pending'
    (target / 'render-report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps({'created': str(target), 'svg_sha256': hashlib.sha256(revised.encode()).hexdigest()}))

if __name__ == '__main__':
    main()
