#!/usr/bin/env python3
"""Original curve-authored DeepSeek/r1 study. Standard library; no image tracing."""
from pathlib import Path
from math import sin, cos, radians
import hashlib
import json
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent


def path(name, d, fill, extra=""):
    return f'<path id="{name}" d="{d}" fill="{fill}" {extra}/>'


def linear(name, colors, coords="160 150 620 920"):
    x1, y1, x2, y2 = coords.split()
    stops = ''.join(f'<stop offset="{i/(len(colors)-1):.3f}" stop-color="{color}"/>' for i, color in enumerate(colors))
    return f'<linearGradient id="{name}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{stops}</linearGradient>'


def radial(name, colors, cx=".42", cy=".34", r=".8", fy=None):
    stops = ''.join(f'<stop offset="{i/(len(colors)-1):.3f}" stop-color="{color}"/>' for i, color in enumerate(colors))
    return f'<radialGradient id="{name}" cx="{cx}" cy="{cy}" r="{r}" fy="{fy or cy}">{stops}</radialGradient>'


def petal(theta1, theta2, i, full):
    # A single broad fabric fold. Neighboring folds overlap the unbroken band.
    center = (512, 570)
    def point(angle, rx, ry):
        loft = ([.94, 1.01, 1.06, .98, 1.04, 1.02, .97, 1.03, .98, .95, .92] if full else [.95, 1.04, 1.0, 1.07, .98, 1.02, .94])[i]
        rx = 398 + (rx-398)*loft
        ry = 398 + (ry-398)*loft
        return (center[0] + cos(radians(angle))*rx, center[1] + sin(radians(angle))*ry)
    a = point(theta1, 398, 398)
    b = point(theta1 + 1.2, 469, 481)
    c = point(theta1 + 3.5, 510, 535)
    d = point(theta2 - 3.5, 510, 535)
    e = point(theta2-1.2, 469, 481)
    f = point(theta2, 398, 398)
    def p(v): return f'{v[0]:.2f} {v[1]:.2f}'
    outline = f'M{p(a)} Q{p(point(theta1,449,448))} {p(b)} C{p(c)} {p(d)} {p(e)} Q{p(point(theta2,449,448))} {p(f)} Q{p(point((theta1+theta2)/2,385,385))} {p(a)}Z'
    return path(f'headband-frill-{i:02}', outline, 'url(#fabric)')


def band_backing(full):
    first, last = (204, 343.15) if full else (215, 335.4)
    def p(angle, radius):
        return f'{512+cos(radians(angle))*radius:.2f} {570+sin(radians(angle))*radius:.2f}'
    return f'M{p(first,476)} A476 476 0 0 1 {p(last,476)} L{p(last,392)} A392 392 0 0 0 {p(first,392)}Z'


FACE = 'M165 447 C183 310 330 290 494 304 C677 291 819 387 849 535 C874 667 853 811 786 891 C718 972 618 1005 492 1003 C349 1001 217 959 167 863 C116 765 124 574 165 447Z'
HAIR = 'M105 535 C63 379 92 242 225 177 C336 111 477 121 563 140 C759 139 883 277 915 435 C953 600 920 807 807 917 C856 817 851 728 805 641 C796 553 764 465 718 409 C685 460 648 478 600 480 C555 464 492 449 457 434 C366 463 255 536 182 555 C180 643 174 704 198 752 C112 716 93 627 105 535Z'


def generate(profile):
    full = profile == 'full'
    defs = [
        radial('skin', ['#fffdf7', '#fff4e8', '#f8dfd6'], '.47', '.33', '.88'),
        linear('hair-field', ['#35457f', '#4664a9', '#7296d7'] if full else ['#475a9f', '#5778b8', '#779bd5']),
        linear('front-lock', ['#405496', '#4c6eb7', '#83a6df'] if full else ['#4b65aa', '#6288c7', '#7fa2da'], '420 190 520 740'),
        linear('side-lock', ['#3b508f', '#5276b9', '#8badde'] if full else ['#506cb0', '#6990c9'], '790 250 860 925'),
        linear('left-lock', ['#3c528f', '#5277b7', '#82a9dc'] if full else ['#4b67a9', '#789fd5'], '240 260 150 830'),
        linear('crown-light', ['#4b6dad', '#6288c9', '#5375b8'], '220 210 480 520'),
        linear('hair-return', ['#2e3d70', '#34467f', '#4f6eae'], '660 220 790 1010'),
        linear('hair-seam', ['#35457e', '#3d579b'], '380 230 620 770'),
        linear('fabric', ['#ffffff', '#fbf8fd', '#dddced'], '380 60 600 550'),
        linear('fabric-reverse', ['#cfcee5', '#bfc1dc'], '260 80 940 700'),
        linear('bow', ['#91bdec', '#6499d4', '#4b76b7'], '825 528 991 786'),
        linear('bow-turn', ['#5a89c5', '#416baa'], '864 548 917 794'),
        radial('eye', ['#303a59', '#222a46', '#1e233c'], '.38', '.26', '.86'),
        linear('eye-edge', ['#55617c', '#252d48', '#151b30'], '280 550 680 810'),
        radial('blush', ['#f9c5c3', '#fbd3cd'], '.43', '.4', '.82'),
        linear('collar', ['#fffefd', '#d9e1ee'], '420 861 480 1060'),
    ]
    defs.append(f'<clipPath id="face-clip"><path d="{FACE}"/></clipPath>')
    defs.append(f'<clipPath id="hair-clip"><path d="{HAIR}"/></clipPath>')
    pieces=[]
    if full:
        pieces.append(path('back-hair', 'M219 349 C162 396 104 563 129 773 C140 865 98 937 41 965 C108 978 183 934 221 882 C212 963 257 1008 301 1028 C318 967 359 927 412 928 L735 1059 C831 1073 860 1014 862 925 C911 942 987 922 1034 876 C941 874 938 806 931 719 C920 540 855 319 711 256Z', 'url(#hair-return)'))
        pieces.append(path('rear-flow-right', 'M813 504 C915 616 871 823 968 887 C919 915 869 883 848 821 C891 941 835 1008 801 1022 C814 895 738 844 744 733Z', 'url(#side-lock)'))
        pieces.append(path('rear-flow-left', 'M185 474 C117 663 179 808 92 925 C170 904 214 828 214 742 C192 849 219 937 269 968 C246 881 296 827 273 724Z', 'url(#left-lock)'))
        pieces.append(path('blouse', 'M354 865 C291 885 222 947 204 1057 L771 1057 C758 952 707 894 644 872Z', '#334879'))
        pieces.append(path('collar-left', 'M351 873 C385 938 435 962 495 965 L431 1041 L277 949Z', 'url(#collar)'))
        pieces.append(path('collar-right', 'M638 880 C607 940 556 969 495 965 L575 1044 L715 947Z', 'url(#collar)'))
        pieces.append(path('neck-bow-left', 'M493 1002 C460 969 420 972 409 990 C407 1005 430 1034 482 1037Z', 'url(#bow)'))
        pieces.append(path('neck-bow-right', 'M500 1001 C535 965 578 970 585 989 C585 1010 551 1039 508 1037Z', 'url(#bow)'))
        pieces.append(path('neck-bow-knot', 'M483 997 Q497 988 512 999 L512 1028 Q496 1040 482 1028Z', 'url(#bow-turn)'))
    else:
        pieces.append(path('back-hair', 'M151 353 C51 553 95 826 172 943 C221 1003 333 1034 471 1047 L753 1047 C842 1006 925 874 928 694 C941 497 851 295 698 224Z', 'url(#hair-return)'))
    pieces.append(path('headband-underfold', band_backing(full), 'url(#fabric-reverse)'))
    angle = 204 if full else 215
    widths = [11, 12, 13, 14, 16, 15, 13, 13, 12, 11, 9.15] if full else [17, 18, 20, 21, 17, 16, 11.4]
    for i, width in enumerate(widths):
        pieces.append(petal(angle, angle+width, i, full))
        angle += width
    pieces.append(path('face', FACE, 'url(#skin)'))
    # Cheeks and eyes are in face coordinates, with geometry clipping outside.
    pieces.append('<g clip-path="url(#face-clip)">')
    pieces.append('<ellipse id="cheek-left" cx="229" cy="786" rx="59" ry="36" fill="url(#blush)" transform="rotate(3 229 786)"/>')
    pieces.append('<ellipse id="cheek-right" cx="744" cy="794" rx="57" ry="35" fill="url(#blush)" transform="rotate(3 744 794)"/>')
    pieces.append('<ellipse id="eye-left" cx="299" cy="681" rx="47" ry="85" fill="url(#eye)" stroke="url(#eye-edge)" stroke-width="2.1"/>')
    pieces.append('<ellipse id="eye-right" cx="678" cy="704" rx="45" ry="83" fill="url(#eye)" stroke="url(#eye-edge)" stroke-width="2.1"/>')
    pieces.append('</g>')
    pieces.append(path('hair-cap', HAIR, 'url(#hair-field)'))
    # Large locks share a crown and differ in attachment/taper, never bright chips.
    pieces.append(path('left-swept-fringe', 'M411 151 C277 153 160 241 126 377 C100 476 129 549 114 599 C234 545 347 480 408 367 C355 469 346 526 365 573 C356 399 475 281 509 171Z', 'url(#left-lock)'))
    if full:
        pieces.append(path('inner-swept-lock', 'M467 166 C380 213 311 307 293 389 C275 461 280 507 296 547 C299 472 328 424 351 400 C329 464 331 505 345 538 C348 458 383 395 414 339 C450 276 477 213 467 166Z', 'url(#front-lock)'))
    pieces.append(path('central-fringe', 'M498 150 C441 206 399 318 392 424 C383 523 411 593 445 621 C433 570 444 518 458 487 C448 582 480 639 548 663 C530 624 536 600 548 574 C627 523 654 445 637 351 C620 246 566 160 498 150Z', 'url(#front-lock)'))
    pieces.append(path('right-fringe', 'M568 165 C693 181 783 273 798 405 C811 497 785 566 800 632 C752 606 728 564 715 491 C717 536 698 566 674 582 C699 491 679 404 639 320 C610 248 577 193 568 165Z', 'url(#hair-field)'))
    pieces.append(path('right-face-lock', 'M783 350 C889 442 921 622 880 771 C860 850 821 907 745 934 C786 893 785 852 790 830 C760 880 725 900 676 903 C778 811 812 711 790 603 C774 514 756 440 783 350Z', 'url(#side-lock)'))
    pieces.append(path('left-face-lock', 'M161 385 C108 455 126 598 145 681 C158 749 144 799 177 843 C132 824 100 784 96 734 C101 802 117 845 152 878 C82 851 68 769 76 702 C82 615 41 492 104 402Z', 'url(#left-lock)'))
    if full:
        pieces.append(path('central-overlap', 'M464 275 C422 379 428 493 445 549 C449 516 454 484 465 454 C475 383 481 329 464 275Z', 'url(#hair-seam)'))
        pieces.append(path('right-temple-return', 'M702 381 C742 463 748 552 777 609 C753 585 736 562 724 534 C713 480 707 430 702 381Z', 'url(#hair-seam)'))
        pieces.append(path('side-flow-front', 'M857 549 C873 661 846 795 789 860 C829 784 831 708 821 650 C828 739 805 795 776 833 C839 692 802 624 815 550Z', 'url(#side-lock)'))
        pieces.append(path('left-flow-return', 'M113 523 C120 614 125 696 113 737 C123 795 137 819 152 837 C104 795 98 752 102 704 C116 632 98 584 113 523Z', 'url(#hair-seam)'))
    pieces.append(path('ahoge', 'M484 187 C559 152 586 95 559 45 C529 -5 450 -10 398 8 C357 23 319 50 298 74 C362 24 438 38 469 70 C512 109 487 149 455 181Z', 'url(#hair-field)'))
    if full:
        pieces.append(path('ahoge-turn', 'M484 187 C526 146 538 102 514 64 C534 82 542 108 530 133 C518 157 502 174 484 187Z', 'url(#crown-light)'))
    # Bow placement follows the far-side hair, retaining asymmetric r1 identity.
    pieces.append(path('side-bow-left', 'M892 589 C851 518 801 534 807 578 C810 626 843 659 890 653Z', 'url(#bow)'))
    pieces.append(path('side-bow-right', 'M901 592 C940 535 976 533 981 559 C988 587 967 648 930 674 C909 658 900 628 901 592Z', 'url(#bow)'))
    pieces.append(path('side-bow-left-fold', 'M822 622 C843 638 866 628 890 608 L890 653 C861 659 838 645 822 622Z', 'url(#bow-turn)'))
    pieces.append(path('side-bow-right-fold', 'M909 612 C917 637 934 650 952 651 L930 674 C916 662 908 643 904 625Z', 'url(#bow-turn)'))
    pieces.append(path('side-bow-knot', 'M883 587 Q897 580 910 592 L915 617 Q906 634 889 625Z', 'url(#bow)'))
    transform = 'translate(0 22) scale(.97) rotate(14 512 555)' if full else 'translate(-118 -139) scale(1.19) rotate(14 512 555)'
    # Full remains an extreme portrait; short crops more headwear and bottom hair.
    return '<?xml version="1.0" encoding="utf-8"?>\n' + f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024" role="img" aria-label="DeepSeek r1 inspired {profile} avatar"><title>DeepSeek · {profile} · r1 character reference</title><desc>Original code-authored vector; subject defined by user r1 reference. Transparent canvas. Candidate pending user review.</desc><defs>' + ''.join(defs) + f'</defs><g id="portrait" transform="{transform}">' + ''.join(pieces) + '</g></svg>\n'


def main():
    designs = {}
    for profile in ('short', 'full'):
        svg = generate(profile)
        ET.fromstring(svg)
        (HERE / (profile + '.svg')).write_text(svg, encoding='utf-8', newline='\n')
        designs[profile] = {
            'svg_sha256': hashlib.sha256(svg.encode()).hexdigest(),
            'main_front_hair_groups': 6 if profile == 'full' else 5,
            'additional_rear_hair_groups': 2 if profile == 'full' else 0,
            'secondary_hair_paths': 5 if profile == 'full' else 0,
            'frill_segments': 11 if profile == 'full' else 7,
            'crop': 'head and minimal collar' if profile == 'full' else 'close face, no collar',
            'scale': .97 if profile == 'full' else 1.19,
            'eye_finish': 'opaque dark navy radial field with very narrow edge gradient; no separate highlight',
            'paint': 'smooth analytic gradients; no stochastic texture or raster data',
            'status': 'candidate_not_user_accepted',
        }
    record = {
        'schema': 'aikon.direct-svg-study.v2',
        'round': '002', 'subject': 'DeepSeek',
        'reference': {'file': 'ref/user-mode/r1.png', 'role': ['subject','style'], 'basis': 'user-explicit; not an official brand character assertion'},
        'full_composition_reference': 'user attachment exec-048782ad-08b7-4c96-acab-3f8e94538c4b.png',
        'method': 'manually authored cubic curves and analytic gradient definitions, deterministic standard-library generator; no raster tracing or image model',
        'profiles': designs,
        'explicit_latest_overrides': [
            'allow natural low-frequency linear and radial gradients',
            'allow weak dark-eye field and narrow eye edge light; still no white eye spots',
            'full differs by composition, headwear, rear hair, secondary locks, and collar',
            'old global luma budget and zero-highlight policy do not govern this study',
        ],
        'limitations': ['User aesthetic review pending.', 'Reference similarity is visually assessed, not established by path count.', 'No cross-model or cross-harness identity guarantee.'],
    }
    (HERE/'design.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
