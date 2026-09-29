"""Original semantic SVG authoring for female Endministrator round-003.

No source-image tracing, bitmap payloads, randomness, or drawing-model call.
The short and full head/face/hair paths are separately authored. Shared helpers
only express material primitives and real repeated hardware constructions.
Run from repository root through tools.run_visual_e2e.run_bounded.
"""
from pathlib import Path
from io import BytesIO
import argparse
import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO))
from tools.render_svg import render_svg_text, validate_svg, backend_info
from PIL import Image, ImageDraw, ImageFont
import numpy as np


class Art:
    def __init__(self, profile, branch, revision):
        self.profile, self.branch, self.revision = profile, branch, revision
        self.defs, self.body = [], []

    def linear(self, name, xy, colors):
        x1,y1,x2,y2 = xy
        stops = ''.join(f'<stop offset="{p}" stop-color="{c}"/>' for p,c in colors)
        self.defs.append(f'<linearGradient id="{name}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{stops}</linearGradient>')
        return f'url(#{name})'

    def radial(self, name, cx, cy, rx, ry, colors):
        stops = ''.join(f'<stop offset="{p}" stop-color="{c}"/>' for p,c in colors)
        self.defs.append(f'<radialGradient id="{name}" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="1" gradientTransform="translate({cx} {cy}) scale({rx} {ry})">{stops}</radialGradient>')
        return f'url(#{name})'

    def path(self, name, d, fill, extra=''):
        self.body.append(f'<path id="{name}" d="{d}" fill="{fill}" {extra}/>')

    def ellipse(self, name, cx, cy, rx, ry, fill, extra=''):
        self.body.append(f'<ellipse id="{name}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" {extra}/>')

    def group(self, name, transform=''):
        self.body.append(f'<g id="{name}" transform="{transform}">')

    def end(self):
        self.body.append('</g>')

    def done(self):
        title = f'Female Endministrator {self.branch} {self.profile} {self.revision}'
        return '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280" viewBox="0 0 1280 1280"><title>'+title+'</title><desc>Original editable bot style vector; official illustration basis; transparent; user acceptance pending.</desc><defs>'+''.join(self.defs)+'</defs>'+''.join(self.body)+'</svg>\n'


def materials(a):
    short = a.profile == 'short'
    return {
        'hair-back': a.linear('hair-back-field',(50,180,970,1060), [(0,'#41444d' if short else '#343940'),(.52,'#242933'),(1,'#1e242d')]),
        'hair-crown': a.radial('hair-crown-field',390,330,800,860,[(0,'#51545d' if short else '#4b5356'),(.48,'#3f424b'),(1,'#292d37')]),
        'hair-front': a.linear('hair-front-field',(430,180,610,800),[(0,'#424a52'),(.35,'#62696a' if short else '#657172'),(.74,'#444d56'),(1,'#2c3540')]),
        'hair-left': a.radial('hair-left-field',370,400,460,760,[(0,'#606568' if short else '#667172'),(.4,'#50595f'),(.77,'#3b434c'),(1,'#2f3640')]),
        'hair-right': a.radial('hair-right-field',820,580,340,590,[(0,'#555d63' if short else '#59676a'),(.60,'#414950'),(1,'#262e39')]),
        'hair-tip': a.linear('hair-tip-field',(700,730,940,1130),[(0,'#272d38'),(.65,'#3e444e'),(1,'#4c5159')]),
        'face': a.radial('face-field',440,935 if short else 780,625,640 if short else 490,[(0,'#fffdfa'),(.54,'#fff4eb' if short else '#fff0e7'),(1,'#f2d4c9')]),
        'face-edge': a.linear('face-edge-field',(300,450,600,720),[(0,'#e3b7aa'),(.7,'#f3d2c4'),(1,'#f8e3d8')]),
        'eye': a.linear('eye-field',(0,590,0,956),[(0,'#34484e'),(.4,'#263840'),(1,'#1a2630')]),
        'metal': a.linear('metal-field',(140,240,400,700),[(0,'#cbd3d6'),(.38,'#f2f3ed'),(.57,'#a1adb3'),(1,'#77868e')]),
        'metal-side': '#424d59',
        'mask': a.linear('mask-field',(170,520,770,920),[(0,'#555d66'),(.48,'#3b444f'),(1,'#202a35')]),
        'mask-middle': a.linear('mask-middle-field',(400,600,540,850),[(0,'#77828a'),(.26,'#5c6873'),(1,'#323e4b')]),
        'mask-low': a.linear('mask-low-field',(470,725,640,960),[(0,'#303b48'),(.65,'#404c59'),(1,'#252f3e')]),
        'yellow': a.linear('yellow-field',(400,700,950,1150),[(0,'#f0e060'),(.6,'#d3c641'),(1,'#b5a932')]),
        'cloth': a.linear('cloth-field',(360,910,800,1310),[(0,'#d6dddf'),(.38,'#f0f0ec'),(1,'#b9c4cc')]),
        'cloth-shadow': a.linear('cloth-shadow-field',(330,960,750,1210),[(0,'#9aa8b4'),(.6,'#d9dfdf'),(1,'#bdc7ce')]),
        'hood': a.linear('hood-field',(400,950,700,1360),[(0,'#46535e'),(.4,'#29333f'),(1,'#1b2532')]),
        'lining': a.linear('lining-field',(150,1000,840,1280),[(0,'#e6e7e1'),(.5,'#aab8c2'),(1,'#e3e5e2')]),
    }


def clip_hardware(a, m, x, y, scale=1):
    a.group('female-multipart-hairclip',f'translate({x} {y}) scale({scale}) rotate(-12)')
    a.path('clip-long-side','M 4 0 L 22 2 L 51 184 L 37 194 L 28 184 Z',m['metal-side'])
    a.path('clip-long-plate','M 0 0 L 15 -3 L 43 179 L 33 190 L 25 181 Z',m['metal'])
    a.path('clip-long-narrow-rim','M 0 0 L 4 -1 L 30 180 L 33 190 L 25 181 Z','#ecf0ee')
    a.path('clip-long-brushed-center','M 7 7 L 13 6 L 38 178 L 34 182 L 31 176 Z','#74818a')
    a.path('clip-short-side','M 40 55 L 55 55 L 73 167 L 60 172 Z',m['metal-side'])
    a.path('clip-short-plate','M 36 50 L 49 49 L 66 161 L 56 167 Z',m['metal'])
    a.path('clip-short-dark-center','M 41 57 L 46 56 L 61 157 L 58 161 Z','#7e8b92')
    a.path('clip-transverse-thickness','M -33 109 L 72 91 L 78 111 L -29 128 Z','#38434d')
    a.path('clip-transverse-clasp','M -36 102 L 69 85 L 74 102 L -33 119 Z',m['metal'])
    a.path('clip-joining-collar','M 21 101 L 46 97 L 48 110 L 22 114 Z','#434d58')
    a.path('clip-secondary-tab','M 1 135 L 23 131 L 27 146 L 5 151 Z','#abb5bc')
    a.end()


def capsule(a, m, name, x, y, w, h):
    r=w/2
    d=f'M {x+r} {y} A {r} {r} 0 0 1 {x+w} {y+r} L {x+w} {y+h-r} A {r} {r} 0 0 1 {x} {y+h-r} L {x} {y+r} A {r} {r} 0 0 1 {x+r} {y} Z'
    a.path(name,d,m['eye'], 'stroke="#596970" stroke-width="1.7"')


def suppressor(a,m,full):
    # Hardware is in head coordinates. In full the eye/nose projection is authored
    # separately; only the device's homologous panels share normalized geometry.
    if full:
        a.group('originium-suppressor','translate(83 53) scale(.82 .85)')
    else:
        a.group('originium-suppressor')
    a.path('suppressor-under-body','M 147 654 L 343 610 L 448 636 L 576 650 L 800 601 L 872 669 L 831 811 L 687 862 L 546 931 L 398 845 L 224 801 Z',m['mask'])
    a.path('suppressor-center-crown','M 318 624 L 373 603 L 413 634 L 592 636 L 641 609 L 694 628 L 769 745 L 647 784 L 578 851 L 517 799 L 464 850 L 382 778 L 284 749 Z',m['mask-middle'])
    a.path('suppressor-center-left-plane','M 318 624 L 373 603 L 413 634 L 494 653 L 464 749 L 382 778 L 284 749 Z','#56626c')
    a.path('suppressor-center-crown-edge','M 318 624 L 373 603 L 413 634 L 592 636 L 641 609 L 654 614 L 598 648 L 406 646 L 371 615 L 322 634 Z','#a3afb5')
    a.path('suppressor-nose-base','M 224 792 L 382 778 L 464 850 L 517 799 L 578 851 L 647 784 L 831 811 L 683 858 L 546 931 L 401 846 Z',m['mask-low'])
    a.path('suppressor-nose-facet','M 517 799 L 546 831 L 546 931 L 482 895 Z','#4b5966')
    a.path('suppressor-nose-edge','M 517 799 L 524 805 L 553 838 L 549 920 L 546 931 L 541 831 Z','#75828b')
    a.path('suppressor-left-arm-thickness','M 147 654 L 282 435 L 306 430 L 347 464 L 231 769 L 193 794 L 156 771 Z','#202a35')
    a.path('suppressor-left-arm','M 133 645 L 270 425 L 294 421 L 334 455 L 218 756 L 180 781 L 144 758 Z',m['mask'])
    a.path('suppressor-left-rim','M 133 645 L 270 425 L 279 424 L 145 650 L 155 749 L 185 771 L 218 750 L 218 756 L 180 781 L 144 758 Z','#87979f')
    a.path('suppressor-left-yellow-tip','M 270 425 L 294 421 L 334 455 L 330 465 L 291 432 L 269 436 Z',m['yellow'])
    a.path('suppressor-right-arm','M 800 601 L 779 438 L 804 421 L 826 438 L 892 653 L 867 710 L 838 726 Z',m['mask'])
    a.path('suppressor-right-arm-rim','M 779 438 L 785 434 L 806 600 L 844 716 L 838 726 L 800 601 Z','#8c9aa3')
    a.path('suppressor-right-yellow-tip','M 779 438 L 804 421 L 826 438 L 830 448 L 804 433 L 781 448 Z',m['yellow'])
    a.path('suppressor-left-connector','M 180 781 L 205 768 L 224 778 L 215 794 L 189 797 Z',m['yellow'])
    a.path('suppressor-right-connector','M 838 726 L 863 711 L 876 724 L 866 743 L 844 743 Z',m['yellow'])
    a.end()


def short_art(branch, revision):
    a=Art('short',branch,revision);m=materials(a)
    a.group('projected-head','rotate(13 540 680)')
    a.path('bob-back-silhouette','M -161 542 C -142 234 52 64 353 45 C 605 3 866 95 1017 294 C 1158 478 1176 727 1117 885 C 1095 964 1120 1089 1212 1110 C 1147 1141 1095 1130 1050 1086 C 1126 1223 1102 1302 1209 1326 C 1086 1367 1002 1314 948 1259 C 827 1403 626 1453 432 1432 C 177 1405 -74 1251 -155 1010 C -217 824 -172 723 -161 542 Z',m['hair-back'])
    a.path('far-left-bob-return','M -108 594 C -208 928 -75 1120 77 1166 C -19 1151 -69 1191 -133 1121 C -79 1250 48 1268 160 1293 C -37 1299 -218 1184 -245 987 Z',m['hair-left'])
    a.path('far-right-bob-turn','M 885 436 C 1068 515 1087 747 1054 910 C 1020 1066 1100 1213 1185 1218 C 1116 1269 1038 1213 998 1163 C 1042 1305 982 1367 929 1380 C 960 1261 847 1193 852 1035 Z',m['hair-tip'])
    a.path('face-visible-domain','M 98 443 C 232 322 452 326 644 394 C 846 465 1006 647 999 865 C 997 1045 914 1251 711 1357 C 572 1428 329 1434 132 1317 C -23 1228 -98 1092 -76 908 C -69 728 11 537 98 443 Z',m['face'])
    if branch=='unmasked':
        capsule(a,m,'eye-left',214,676,101,280)
        capsule(a,m,'eye-right',646,676,101,280)
    a.ellipse('cheek-left',129,1029,74,39,'#f7cac3')
    a.ellipse('cheek-right',794,1029,70,39,'#f7cac3')
    if branch=='masked':suppressor(a,m,False)
    a.path('crown-primary','M -155 474 C -117 205 52 81 285 51 C 393 39 484 60 552 77 C 614 40 734 93 812 148 C 997 282 1083 468 1090 649 C 1034 544 939 484 827 413 C 727 318 668 221 545 200 C 333 183 199 320 73 477 C -23 566 -100 629 -174 634 Z',m['hair-crown'])
    a.path('left-sweeping-fringe','M 472 117 C 315 105 180 163 68 272 C -12 352 -31 480 -112 521 C -50 532 -9 508 31 480 C -48 628 -35 815 42 922 C -10 732 149 553 285 479 C 385 423 480 295 514 224 C 483 329 414 408 367 445 C 469 420 558 326 561 234 C 563 177 526 133 472 117 Z',m['hair-left'])
    a.path('fringe-center-wide','M 557 158 C 500 222 451 340 442 456 C 441 530 474 600 537 634 C 516 594 518 550 526 520 C 542 583 584 633 635 656 C 615 616 602 581 607 548 C 640 614 681 644 736 650 C 678 565 696 446 661 341 C 644 267 608 190 557 158 Z',m['hair-front'])
    a.path('fringe-right-join','M 571 154 C 723 170 849 263 913 394 C 959 496 949 589 999 684 C 933 651 885 593 861 535 C 884 612 888 698 845 761 C 853 665 768 589 740 501 C 711 407 674 286 571 154 Z',m['hair-right'])
    a.path('right-bob-front','M 907 352 C 1099 469 1134 681 1086 901 C 1061 1015 1037 1104 1100 1162 C 1016 1158 970 1099 955 1037 C 981 1188 919 1296 804 1298 C 891 1234 886 1172 877 1122 C 853 1209 785 1278 710 1271 C 819 1169 826 1080 841 970 C 868 838 897 703 884 592 C 878 488 866 427 907 352 Z',m['hair-right'])
    a.path('left-bob-front','M 63 393 C -30 609 -75 788 -26 957 C -6 1033 43 1083 92 1092 C 7 1097 -43 1062 -69 1017 C -17 1164 102 1204 163 1177 C 123 1235 -24 1244 -108 1132 C -173 1036 -196 889 -157 727 C -119 575 -49 456 63 393 Z',m['hair-left'])
    a.path('crown-small-tuft','M 382 57 C 440 12 508 26 561 68 C 526 7 474 -8 429 11 C 470 -13 510 -12 540 2 C 483 -44 407 -15 382 57 Z',m['hair-crown'])
    clip_hardware(a,m,96,277,1.28)
    a.end()
    return a.done()


def full_clothing(a,m):
    # Independently planned crop: shoulders are below the larger exposed jaw.
    a.path('hood-outer-silhouette','M 91 959 C 22 905 -52 928 -107 1000 C -130 1050 -21 1190 114 1236 L 122 1402 L 1126 1406 C 1154 1267 1117 1112 1046 1011 C 1004 951 921 922 865 941 L 717 1024 L 362 1044 Z',m['hood'])
    a.path('hood-left-inner-lining','M 84 972 C -8 937 -49 979 -60 1015 C -11 1101 113 1156 216 1137 L 328 1070 L 250 1022 Z',m['lining'])
    a.path('hood-right-inner-lining','M 744 1024 C 780 979 860 958 898 943 C 993 956 1056 1020 1084 1101 L 1005 1156 L 847 1123 Z',m['lining'])
    a.path('upper-chest-underlayer','M 326 969 C 421 956 611 981 747 1011 L 887 1398 L 214 1398 C 228 1232 271 1077 326 969 Z',m['cloth'])
    a.path('neck-dark-inner','M 381 898 C 451 923 613 923 679 886 L 682 1006 C 603 1076 443 1040 369 993 Z','#2b3540')
    a.path('standing-collar-back','M 342 936 C 430 994 615 1005 710 929 L 747 1004 C 648 1091 442 1077 331 1010 Z',m['cloth-shadow'])
    a.path('standing-collar-front','M 329 987 C 423 1041 613 1063 718 984 L 737 1045 C 627 1123 424 1098 320 1046 Z',m['cloth'])
    # Broad rib-form shifts, not texture strokes or repeated random noise.
    for i,(x,y) in enumerate(((355,1002),(387,1017),(420,1029),(456,1038),(496,1045),(538,1048),(581,1047),(624,1038),(663,1024),(697,1007))):
        a.path(f'collar-rib-{i}',f'M {x} {y} L {x+4} {y+2} L {x+1} {y+43} L {x-3} {y+42} Z','#b9c3c9')
    a.path('collar-orange-connector','M 473 1038 L 500 1043 L 493 1092 L 466 1087 Z','#cb784a')
    a.path('collar-orange-edge','M 498 1043 L 506 1044 L 499 1093 L 493 1092 Z','#8e6656')
    a.path('collar-zip-tab','M 442 1040 L 462 1045 L 450 1112 L 431 1106 Z','#697985')
    a.path('collar-zip-tab-open','M 446 1052 L 455 1054 L 447 1098 L 439 1095 Z','#c6cfd2')
    a.path('chest-right-fold','M 731 1080 C 728 1159 763 1251 819 1378 L 872 1398 L 801 1165 Z','#a6b5bf')
    a.path('chest-panel-seam','M 384 1160 L 434 1125 L 628 1157 L 637 1241 L 602 1219 L 457 1192 L 461 1291 L 438 1308 L 428 1179 Z','#c4cfd3')
    a.path('outer-collar-left-face','M 79 976 C 108 1066 204 1126 311 1120 L 337 1388 L 139 1405 C 180 1255 142 1154 79 976 Z',m['hood'])
    a.path('outer-collar-left-return','M 96 977 C 137 1055 207 1093 311 1120 L 264 1170 C 171 1128 125 1052 96 977 Z','#66757f')
    a.path('outer-collar-right-face','M 908 956 L 1011 1004 C 956 1083 913 1169 902 1253 L 962 1396 L 842 1400 C 811 1281 793 1170 748 1093 C 823 1064 866 1018 908 956 Z',m['hood'])
    a.path('outer-collar-right-fold','M 908 956 L 925 963 C 887 1029 832 1091 784 1116 L 748 1093 C 823 1064 866 1018 908 956 Z','#788792')
    a.path('yellow-shoulder-piece','M 968 1000 L 1024 1021 C 1004 1061 987 1108 981 1148 L 875 1134 L 821 1097 C 880 1073 930 1038 968 1000 Z',m['yellow'])
    a.path('yellow-shoulder-return','M 821 1097 L 875 1134 L 981 1148 L 978 1160 L 870 1147 L 818 1108 Z','#9e983b')
    a.path('yellow-silver-connector','M 912 1098 C 910 1081 923 1072 935 1078 L 947 1084 L 941 1096 L 930 1090 C 925 1087 921 1090 923 1097 L 932 1103 L 927 1115 Z',m['metal'])
    # Open elongated nested rings visibly connected to the collar front.
    a.group('layered-collar-ring-fastener','rotate(-11 638 1102)')
    a.path('ring-second-layer','M 598 1083 L 702 1083 C 728 1083 742 1101 742 1122 C 742 1142 727 1156 701 1156 L 595 1156 C 570 1156 556 1142 556 1121 C 556 1099 572 1083 598 1083 Z M 598 1098 C 581 1098 571 1108 571 1121 C 571 1134 580 1142 595 1142 L 701 1142 C 718 1142 727 1134 727 1122 C 727 1108 718 1098 702 1098 Z','#8798a3','fill-rule="evenodd"')
    a.path('ring-anchor','M 548 1066 C 528 1062 513 1077 513 1097 C 513 1122 530 1135 551 1131 L 567 1126 L 564 1113 L 548 1117 C 536 1119 528 1110 528 1097 C 528 1086 536 1079 548 1081 L 558 1083 L 563 1070 Z',m['metal'])
    a.path('ring-back-depth','M 582 1066 L 699 1066 C 728 1066 740 1083 740 1104 C 740 1126 724 1140 697 1140 L 580 1140 C 553 1140 541 1124 541 1105 C 541 1084 554 1066 582 1066 Z M 582 1085 C 567 1085 560 1092 560 1105 C 560 1115 567 1121 580 1121 L 697 1121 C 712 1121 721 1115 721 1104 C 721 1092 713 1085 699 1085 Z','#475661','fill-rule="evenodd"')
    a.path('ring-front-body','M 576 1058 L 693 1058 C 722 1058 734 1075 734 1096 C 734 1118 718 1132 691 1132 L 574 1132 C 547 1132 535 1116 535 1097 C 535 1076 548 1058 576 1058 Z M 576 1077 C 561 1077 554 1084 554 1097 C 554 1107 561 1113 574 1113 L 691 1113 C 706 1113 715 1107 715 1096 C 715 1084 707 1077 693 1077 Z',m['metal'],'fill-rule="evenodd"')
    a.path('ring-overlap-strap','M 565 1054 L 581 1054 L 581 1135 L 566 1135 C 550 1118 548 1074 565 1054 Z','#a4b2bb')
    a.path('ring-overlap-light','M 565 1054 L 570 1054 C 560 1078 560 1108 571 1135 L 566 1135 C 550 1118 548 1074 565 1054 Z','#edf0ed')
    a.end()


def full_art(branch,revision):
    a=Art('full',branch,revision);m=materials(a)
    a.group('projected-head-and-neck','rotate(13 560 630)')
    full_clothing(a,m)
    a.path('full-back-bob','M 26 483 C 30 263 178 110 391 93 C 606 56 820 142 938 303 C 1060 470 1064 672 1001 806 C 982 855 1003 917 1064 940 C 1011 961 970 946 941 916 C 968 1002 1017 1027 1050 1028 C 947 1072 860 1008 822 971 C 690 1072 435 1087 267 1003 C 133 936 30 812 18 671 Z',m['hair-back'])
    a.path('back-bob-right-separation','M 905 423 C 1015 537 1021 736 956 853 C 921 918 950 999 1008 1018 C 939 1037 878 983 864 917 C 870 985 823 1035 778 1030 C 848 949 789 820 820 714 Z',m['hair-tip'])
    a.path('full-visible-face','M 190 427 C 292 347 465 358 634 411 C 812 467 937 588 936 744 C 930 880 838 995 682 1032 C 531 1068 364 1017 237 933 C 136 866 93 753 110 633 C 123 541 144 472 190 427 Z',m['face'])
    if branch=='unmasked':
        capsule(a,m,'eye-left',270,629,83,225)
        capsule(a,m,'eye-right',629,629,83,225)
    a.ellipse('cheek-left',218,892,61,32,'#f3c3be')
    a.ellipse('cheek-right',773,892,59,32,'#f3c3be')
    if branch=='masked':suppressor(a,m,True)
    a.path('full-crown','M 27 483 C 28 275 156 127 354 96 C 454 75 528 88 575 117 C 638 88 738 128 813 190 C 963 306 1012 444 1015 591 C 950 502 885 458 800 409 C 705 327 648 244 548 223 C 381 203 257 293 161 412 C 107 476 70 513 25 532 Z',m['hair-crown'])
    a.path('full-left-crown-stream','M 528 121 C 384 99 266 148 169 233 C 83 309 68 396 8 442 C 60 439 103 411 130 384 C 56 522 75 656 129 748 C 98 620 215 493 320 429 C 410 373 482 280 522 205 C 501 291 452 360 413 396 C 491 375 550 292 560 231 C 569 174 550 137 528 121 Z',m['hair-left'])
    a.path('full-center-forelock','M 564 165 C 509 235 471 330 475 427 C 480 494 499 536 549 573 C 531 539 530 509 536 480 C 551 531 577 564 621 593 C 608 563 601 537 603 512 C 629 559 661 584 704 593 C 665 528 673 440 648 350 C 630 267 598 191 564 165 Z',m['hair-front'])
    a.path('full-forelock-middle-side','M 576 174 C 685 205 769 286 803 374 C 841 469 823 521 857 596 C 807 568 780 533 760 488 C 775 548 771 600 740 641 C 744 566 694 510 679 438 C 665 342 622 236 576 174 Z',m['hair-right'])
    a.path('full-right-temple-lock','M 776 270 C 926 348 976 483 943 632 C 929 701 956 759 986 785 C 935 781 901 742 890 699 C 898 785 867 861 817 886 C 855 811 833 742 829 681 C 815 546 846 422 776 270 Z',m['hair-front'])
    a.path('full-right-cheek-lock','M 919 433 C 1009 510 1035 656 987 787 C 965 848 941 906 974 952 C 915 940 893 896 895 851 C 874 943 824 996 754 990 C 811 950 825 903 822 860 C 803 924 766 957 719 956 C 794 887 791 818 815 725 C 850 620 864 511 849 457 Z',m['hair-right'])
    a.path('full-left-temple-lock','M 187 344 C 119 444 88 590 108 697 C 122 764 151 798 184 816 C 136 813 100 786 83 749 C 103 847 158 881 204 882 C 143 912 72 856 46 775 C 1 628 76 417 187 344 Z',m['hair-left'])
    a.path('full-left-outturned-tip','M 78 687 C 70 796 89 889 149 928 C 179 949 202 949 229 938 C 202 980 115 976 70 928 C 90 984 137 1003 175 1004 C 106 1024 20 960 13 859 Z',m['hair-tip'])
    a.path('full-crown-little-curl','M 434 104 C 466 63 514 62 557 91 C 534 55 499 49 474 53 C 502 39 532 42 554 52 C 515 10 451 42 434 104 Z',m['hair-crown'])
    clip_hardware(a,m,211,267,1.06)
    a.end()
    return a.done()


def board(records, output, revision):
    canvas=Image.new('RGB',(1580,1800),'#e9ecee'); d=ImageDraw.Draw(canvas)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',26);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    except OSError:font=small=ImageFont.load_default()
    for i,r in enumerate(records):
        x=30+(i%2)*790;y=30+(i//2)*900
        d.text((x,y),f"{r['branch']} / {r['profile']} / {revision}",fill='#27303a',font=font)
        img=Image.open(r['png']).convert('RGBA');view=img.resize((710,710),Image.Resampling.LANCZOS)
        panel=Image.new('RGBA',(710,710),'#20252c');panel.alpha_composite(view);canvas.paste(panel.convert('RGB'),(x,y+44))
        for j,size in enumerate((128,48,24)):
            mini=Image.open(Path(r['png']).with_name(f'preview-{size}.png')).convert('RGBA')
            bg=Image.new('RGBA',(size,size),'#f6f5f2');bg.alpha_composite(mini);canvas.paste(bg.convert('RGB'),(x+j*200,y+771))
            d.text((x+j*200,y+742),f'{size}px',fill='#34414b',font=small)
    canvas.save(output)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r001');args=parser.parse_args()
    records=[]
    for branch in ('unmasked','masked'):
        for profile in ('short','full'):
            folder=ROOT/branch/profile/'revisions'/args.revision
            if not (folder/'prompt.zh-CN.md').exists():raise SystemExit('Save actual prompt first: '+str(folder))
            if (folder/'icon.svg').exists():raise SystemExit('Revision exists; no overwrite: '+str(folder))
            text=short_art(branch,args.revision) if profile=='short' else full_art(branch,args.revision)
            validate_svg(text);(folder/'icon.svg').write_text(text,encoding='utf-8')
            shutil.copy2(__file__,folder/'sourcecode.py')
            for size in (1280,128,48,24):
                (folder/f'preview-{size}.png').write_bytes(render_svg_text(text,size))
            pixels=np.asarray(Image.open(folder/'preview-1280.png').convert('RGBA'))
            metadata={
                'round':'round-003','entity':'endministrator-female','profile':profile,'branch':branch,'revision':args.revision,
                'parent':None if args.revision=='r001' else 'r001',
                'reference_basis':'official illustration','user_decision':'both','user_acceptance':'unassessed',
                'svg_sha256':hashlib.sha256(text.encode()).hexdigest(),'structural_check':'passed',
                'renderer':backend_info(),'alpha':{'transparent_pixels':int((pixels[:,:,3]==0).sum()),'opaque_pixels':int((pixels[:,:,3]==255).sum()),'partial_pixels':int(((pixels[:,:,3]>0)&(pixels[:,:,3]<255)).sum()),'top_right':int(pixels[0,-1,3])},
                'eyes':{'kind':'exact capsule via circular arcs and straight sides','pair_equal':True,'dimensions':[101,280] if profile=='short' else [83,225]} if branch=='unmasked' else {'kind':'normally occluded by opaque suppressor','capsules_omitted':True},
                'visual_review':'pending actual image inspection','claim_limit':'No 99 percent or user acceptance claim.',
            }
            (folder/'revision.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            records.append({'branch':branch,'profile':profile,'png':str(folder/'preview-1280.png')})
    board(records,ROOT/f'overview-{args.revision}.png',args.revision)
    print(json.dumps({'revision':args.revision,'rendered':len(records),'overview':str(ROOT/f'overview-{args.revision}.png')}))

if __name__=='__main__':main()
