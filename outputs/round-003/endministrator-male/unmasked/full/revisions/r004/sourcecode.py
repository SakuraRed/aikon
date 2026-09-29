"""Original semantic SVG authoring for the male Endministrator, round 003.

Run from the repository root with the pinned optional renderer. Geometry below
is authored from observed forms, not copied from any old candidate or traced.
Each profile has its own points and topology. No source raster is read here.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools.render_svg import render_svg_text, validate_svg, backend_info
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
S = 'http://www.w3.org/2000/svg'
ET.register_namespace('',S)

def element(parent, tag, **attrs):
    return ET.SubElement(parent,'{'+S+'}'+tag,{k.replace('_','-'):str(v) for k,v in attrs.items()})

def path(parent, id, d, fill, **attrs):
    return element(parent,'path',id=id,d=d,fill=fill,**attrs)

def linear(defs,id,coords,stops):
    x1,y1,x2,y2=coords
    g=element(defs,'linearGradient',id=id,gradientUnits='userSpaceOnUse',x1=x1,y1=y1,x2=x2,y2=y2)
    for o,c in stops:
        element(g,'stop',offset=o,stop_color=c)

def radial(defs,id,cx,cy,r,stops,transform=None):
    attrs={'id':id,'gradientUnits':'userSpaceOnUse','cx':cx,'cy':cy,'r':r}
    if transform: attrs['gradientTransform']=transform
    g=element(defs,'radialGradient',**attrs)
    for o,c in stops: element(g,'stop',offset=o,stop_color=c)

def paint(id): return 'url(#'+id+')'

def capsule(parent,id,x,y,w,h):
    r=w/2
    d=f'M{x+r},{y} A{r},{r} 0 0 1 {x+w},{y+r} L{x+w},{y+h-r} A{r},{r} 0 0 1 {x},{y+h-r} L{x},{y+r} A{r},{r} 0 0 1 {x+r},{y} Z'
    path(parent,id,d,paint('eye-material'))
    # The eye's material field, not a separate white dot or iris, provides gloss.
    return d

def defs(root,profile,revision):
    d=element(root,'defs')
    radial(d,'face-material',350,750 if profile=='short' else 620,720,[(0,'#fffdf8'),(.49,'#fff3e9'),(1,'#f5dace')])
    radial(d,'crown-material',385,230 if profile=='short' else 180,760,[(0,'#595b5b'),(.39,'#41454a'),(.8,'#2a2e35'),(1,'#20252c')])
    radial(d,'sweep-material',430,310 if profile=='short' else 245,650,[(0,'#565b60'),(.48,'#3e454c'),(1,'#242a31')])
    radial(d,'mid-sweep-material',420,315 if profile=='short' else 240,620,[(0,'#494f54'),(.55,'#353c44'),(1,'#262c33')])
    radial(d,'fall-material',735 if profile=='short' else 640,475 if profile=='short' else 345,700,[(0,'#52585c'),(.6,'#383f46'),(1,'#242b33')])
    linear(d,'back-material',(0,300,900,1080),[(0,'#31383f'),(.58,'#222830'),(1,'#1b222a')])
    linear(d,'side-material',(610,350,1060,1050),[(0,'#363e46'),(.6,'#252d35'),(1,'#39424a')])
    linear(d,'eye-material',(0,profile=='short' and 700 or 520,70,profile=='short' and 945 or 745),[(0,'#263d46'),(.1,'#20343e'),(.5,'#15232e'),(.88,'#172731'),(1,'#20333d')])
    linear(d,'mask-central',(120,600,830,940),[(0,'#3f4851'),(.38,'#323b46'),(1,'#252d37')])
    linear(d,'mask-crown',(180,630,550,900),[(0,'#707984'),(.15,'#545f6b'),(.67,'#394552'),(1,'#313b46')])
    linear(d,'mask-left',(100,480,230,860),[(0,'#58616a'),(.6,'#353e48'),(1,'#252e39')])
    linear(d,'mask-right',(700,430,840,850),[(0,'#414c57'),(.58,'#555f68'),(1,'#2a333e')])
    linear(d,'mask-nose',(410,770,455,1010),[(0,'#65727d'),(.52,'#425261'),(1,'#303d4a')])
    linear(d,'metal',(180,930,720,1150),[(0,'#88959e'),(.24,'#e4e9e9'),(.5,'#8d9ca6'),(.76,'#cad4d8'),(1,'#6b7b87')])
    linear(d,'pale-collar',(290,900,790,1300),[(0,'#eceded'),(.34,'#c9ced1'),(.7,'#a9b1b8'),(1,'#dfe1e0')])
    linear(d,'coat',(0,850,850,1420),[(0,'#49515d'),(.48,'#262f3c'),(1,'#18232f')])
    linear(d,'coat-wing',(630,900,1090,1170),[(0,'#556577'),(.44,'#303e4d'),(1,'#162432')])
    linear(d,'yellow-plate-material',(820,1050,980,1350),[(0,'#eee989'),(.34,'#e3df60'),(.73,'#d1c84b'),(1,'#afaa41')])
    linear(d,'inner-neck',(310,890,690,1080),[(0,'#222b32'),(.4,'#333b40'),(1,'#151f28')])
    return d

def short_back(g):
    path(g,'hair-back','M-200 564 C-168 337 -63 219 165 160 C106 123 75 96 57 62 C171 74 251 122 301 151 C298 85 276 25 245 -18 C347 17 397 86 439 138 C504 66 511 15 502 -42 C579 12 612 62 616 128 C718 88 805 114 870 190 C920 248 948 291 1012 317 C976 332 946 325 923 319 C946 387 1006 433 1069 459 C1023 471 1001 461 983 452 C1013 521 1046 546 1100 559 C1072 584 1032 582 1009 574 C1037 650 1048 684 1109 714 C1061 727 1036 714 1019 704 C1040 775 1043 819 1088 845 C1041 852 1017 838 997 820 C1010 898 1001 951 1039 988 C1004 985 974 961 955 938 C939 1003 925 1047 948 1091 C896 1076 869 1036 850 1002 C845 1058 822 1105 814 1126 C769 1095 749 1053 727 1002 L66 1113 C-127 1015 -232 818 -200 564 Z',paint('back-material'))
    path(g,'hair-crown','M-166 574 C-117 347 -33 216 188 174 C159 155 143 133 133 116 C238 133 317 188 353 201 C352 147 327 90 291 64 C385 86 433 152 447 188 C485 130 516 106 542 72 C544 112 540 134 532 162 C692 82 832 171 881 282 C922 375 967 390 1010 407 C933 433 911 408 886 390 C946 511 972 630 961 797 C918 930 806 1031 634 1062 L20 1002 C-137 873 -200 726 -166 574 Z',paint('crown-material'))
    path(g,'hair-short-nape-left','M-106 695 C-10 811 8 942 48 1023 C75 1067 89 1082 126 1091 C80 1103 36 1086 19 1064 C16 1114 -3 1142 -18 1158 C-42 1111 -78 1033 -103 953 Z',paint('side-material'))

def short_face(g):
    path(g,'face','M83 461 C226 322 528 321 727 448 C894 554 973 773 965 969 C960 1160 871 1356 692 1424 C469 1508 148 1406 -18 1243 C-124 1135 -156 956 -115 792 C-77 626 -7 525 83 461 Z',paint('face-material'))
    path(g,'ear-near','M879 779 C972 741 1012 792 999 858 C986 922 951 963 908 957 C908 880 899 825 879 779 Z','#f5d8c9')
    element(g,'ellipse',id='cheek-left',cx=67,cy=1035,rx=82,ry=43,fill='#f7cecb')
    element(g,'ellipse',id='cheek-right',cx=737,cy=1056,rx=82,ry=43,fill='#f7cecb')

def short_front(g,revision):
    # The narrow shadow belongs only to the receiving forehead under this sweep.
    path(g,'fringe-contact-shadow','M-74 626 C203 644 453 484 553 278 C601 423 612 599 526 704 C622 673 670 594 678 549 C701 727 742 810 838 866 L890 867 C830 705 834 470 759 286 C641 199 540 187 387 275 C120 336 -28 472 -74 626 Z','#e8c2b6')
    path(g,'fringe-outer-sweep','M576 184 C437 104 239 166 77 271 C-8 325 -103 354 -163 339 C-97 418 4 426 69 417 C-8 469 -84 498 -153 483 C-97 546 -12 552 43 535 C7 579 -45 612 -95 610 C-15 656 53 645 110 616 C51 685 -5 714 -55 713 C96 761 298 664 413 563 C530 464 617 310 576 184 Z',paint('sweep-material'))
    path(g,'fringe-upper-wave','M583 179 C459 143 318 202 224 277 C147 334 78 363 25 364 C125 400 249 350 324 300 C414 244 494 216 550 227 C481 328 333 416 169 435 C365 447 527 350 583 179 Z',paint('mid-sweep-material'))
    path(g,'fringe-low-wave','M569 228 C543 392 381 539 183 599 C128 616 92 622 53 623 C128 673 277 634 387 557 C497 481 570 364 569 228 Z',paint('mid-sweep-material'))
    path(g,'fringe-long-right','M580 180 C693 149 799 255 824 395 C843 500 825 577 824 638 C821 735 841 815 893 872 C807 844 733 753 713 643 C705 599 700 560 695 519 C689 640 653 720 585 759 C643 632 625 516 594 412 C570 329 535 243 580 180 Z',paint('fall-material'))
    path(g,'temple-right','M792 337 C897 401 931 537 931 655 C930 755 934 836 965 892 C934 875 915 851 901 827 C905 890 895 956 919 994 C863 967 831 922 821 866 C796 785 811 704 818 620 C828 503 809 418 792 337 Z',paint('side-material'))
    path(g,'temple-left','M-62 551 C-16 563 9 590 7 640 C-3 718 -27 801 -5 867 C-33 850 -57 821 -66 790 C-70 851 -66 895 -39 927 C-102 908 -128 859 -129 788 C-129 686 -92 608 -62 551 Z',paint('side-material'))

def full_garment(g,revision):
    path(g,'coat-base','M47 946 C102 878 177 854 260 891 C310 922 340 931 422 947 C583 986 693 918 762 883 C858 836 1000 864 1086 934 L1021 1043 C1080 1111 1144 1267 1167 1480 L-171 1480 C-114 1258 -93 1092 47 946 Z',paint('coat'))
    path(g,'hood-far-inner','M65 876 C169 849 209 855 283 902 L414 960 L391 1033 L219 1055 L128 979 Z',paint('pale-collar'))
    path(g,'hood-far-wing','M-27 934 L158 929 L282 1050 L241 1156 L114 1021 L-54 1008 L78 976 Z',paint('coat-wing'))
    path(g,'hood-near-lining','M671 926 C800 834 968 858 1059 923 L1008 1019 L806 1102 L630 1005 Z',paint('pale-collar'))
    path(g,'hood-near-outer','M734 1010 C861 938 970 904 1060 923 L1028 1005 L943 1052 L806 1077 L856 1120 L689 1177 L628 1094 Z',paint('coat-wing'))
    path(g,'neck-inner','M285 840 C381 877 553 906 663 859 L700 996 C599 1074 386 1080 272 987 Z',paint('inner-neck'))
    path(g,'chest-inner','M309 1021 C441 1001 604 1046 749 1018 L841 1460 L150 1460 L189 1102 Z',paint('pale-collar'))
    path(g,'collar-far-upright','M225 873 C273 905 347 934 423 946 L439 1039 C353 1036 270 1022 215 986 L187 883 Z',paint('pale-collar'))
    path(g,'collar-near-upright','M431 946 C527 956 618 933 719 874 L761 962 C680 1028 549 1054 434 1043 Z',paint('pale-collar'))
    path(g,'collar-top-roll','M212 888 C294 950 512 1016 731 895 L744 910 C563 1043 301 981 219 908 Z','#d9ddde')
    path(g,'collar-inner-shadow','M240 873 C337 920 432 940 517 932 C602 922 674 899 708 879 L712 899 C658 937 573 959 518 963 C399 971 303 938 243 911 Z','#7b878e')
    path(g,'zipper-shadow','M429 959 L450 964 L466 1067 L445 1070 Z','#434f58')
    path(g,'zipper-metal','M434 965 L443 967 L458 1061 L450 1062 Z',paint('metal'))
    path(g,'zipper-pull','M444 1004 L459 1003 L467 1043 L452 1046 Z M449 1011 L454 1010 L459 1034 L455 1035 Z',paint('metal'),fill_rule='evenodd')
    path(g,'ring-attachment-strap','M311 1019 L395 1042 L388 1074 L303 1052 Z','#293642')
    path(g,'fastener-upper','M288 1015 C277 1011 267 1018 270 1032 L275 1061 C278 1074 287 1082 301 1088 L385 1126 C405 1135 424 1129 430 1116 C437 1101 428 1087 414 1081 L308 1024 C301 1020 295 1017 288 1015 Z M293 1034 L411 1096 C419 1100 421 1106 417 1110 C413 1116 404 1115 395 1111 L307 1073 C295 1068 291 1062 289 1054 L285 1037 C285 1032 289 1032 293 1034 Z',paint('metal'),fill_rule='evenodd')
    path(g,'fastener-lower-long','M309 1069 C302 1061 289 1060 281 1069 C275 1076 274 1088 282 1098 L378 1214 C387 1226 404 1228 416 1218 C428 1207 430 1195 420 1181 Z M299 1084 L407 1193 C411 1198 410 1203 405 1206 C401 1209 396 1206 392 1202 L293 1090 C289 1085 293 1080 299 1084 Z',paint('metal'),fill_rule='evenodd')
    path(g,'chest-fabric-turn','M466 1114 L729 1054 L822 1440 L681 1451 C587 1349 526 1234 466 1114 Z','#c4cbd0')
    path(g,'coat-left-front','M170 1050 L291 1081 L183 1300 L164 1470 L-37 1480 C17 1299 90 1119 170 1050 Z','#2b3846')
    path(g,'yellow-plate-edge','M737 1059 L885 1052 L1037 1189 Q1048 1200 1035 1214 L986 1264 Q975 1276 961 1268 L873 1197 L748 1341 Q738 1354 724 1343 L683 1308 Q674 1300 682 1285 Z',paint('metal'))
    path(g,'yellow-plate','M745 1073 L881 1066 L1026 1198 L974 1253 L873 1174 L735 1331 L694 1299 Z',paint('yellow-plate-material'))
    path(g,'yellow-turn','M745 1073 L881 1066 L946 1128 L852 1109 L727 1196 Z','#bfc45a')
    path(g,'yellow-attachment','M968 1188 Q975 1182 982 1188 L996 1201 Q1002 1207 997 1214 L984 1227 Q978 1234 971 1227 L957 1214 Q950 1207 957 1200 Z','#374553')
    for k,x,y in [('upper',733,1249),('lower',714,1280)]:
        path(g,'plate-pin-'+k,f'M{x} {y} c-5 -5 -11 -4 -15 1 c-5 7 -3 13 3 17 l9 4 l5 -8 l-8 -3 c-3 -2 -1 -5 1 -4 l5 2 Z',paint('metal'))

def full_back(g,revision):
    path(g,'hair-back','M-105 498 C-97 310 -32 183 153 141 C110 118 78 86 55 52 C144 52 231 113 255 132 C265 86 237 30 201 -11 C293 7 334 63 369 100 C429 60 451 14 440 -31 C507 9 532 68 533 109 C638 59 751 133 797 207 C826 250 851 268 892 273 C868 295 844 290 830 285 C852 337 891 363 932 376 C911 394 883 390 865 385 C900 440 920 467 960 476 C937 501 910 499 890 489 C912 548 945 574 979 584 C957 601 932 598 914 588 C936 647 946 675 981 702 C949 709 925 698 913 687 C926 756 923 793 949 823 C910 820 885 798 872 778 C865 832 856 870 869 903 C829 889 808 857 794 832 C784 885 773 911 756 936 C727 909 708 873 700 846 L143 943 C-4 888 -112 704 -105 498 Z',paint('back-material'))
    path(g,'hair-crown','M-84 491 C-60 312 31 199 182 164 C146 136 123 114 116 97 C205 105 264 153 296 177 C302 128 289 82 266 60 C330 80 369 118 384 150 C423 125 451 97 469 75 C470 117 467 138 461 151 C577 80 725 150 777 240 C815 307 841 325 875 338 C832 351 811 343 793 333 C847 432 875 556 852 668 C822 798 699 899 530 923 L115 890 C-43 797 -117 650 -84 491 Z',paint('crown-material'))
    path(g,'nape-short-far','M41 700 C93 740 104 801 119 854 C130 897 155 922 181 934 C145 940 123 923 109 905 C112 945 103 967 96 986 C67 959 32 916 16 870 Z',paint('side-material'))
    path(g,'nape-short-near','M764 703 C814 732 837 786 833 832 C829 868 835 900 851 924 C819 914 801 896 790 874 C790 915 785 938 800 960 C757 944 738 916 730 882 L729 757 Z',paint('side-material'))

def full_face(g):
    path(g,'face','M80 362 C212 253 435 254 619 332 C787 403 867 555 858 724 C850 865 772 980 621 1010 C411 1053 171 982 45 870 C-42 793 -68 663 -31 547 C-6 471 30 405 80 362 Z',paint('face-material'))
    path(g,'ear-near','M782 585 C861 561 897 607 884 659 C873 708 843 743 811 739 C812 669 799 621 782 585 Z','#f1d5c7')
    element(g,'ellipse',id='cheek-left',cx=79,cy=824,rx=66,ry=35,fill='#f5cdca')
    element(g,'ellipse',id='cheek-right',cx=663,cy=849,rx=66,ry=35,fill='#f5cdca')

def full_front(g,revision):
    path(g,'fringe-contact-shadow','M-23 520 C171 544 411 379 481 233 C520 337 534 487 484 568 C561 541 591 493 604 450 C631 593 670 679 752 731 L805 730 C769 564 742 377 676 252 C585 183 504 170 390 224 C206 273 33 387 -23 520 Z','#e5c4b8')
    path(g,'fringe-outer-sweep','M508 158 C398 106 253 143 136 219 C47 277 -15 297 -78 288 C-33 349 42 356 101 344 C41 388 -21 410 -70 402 C-19 450 40 454 85 441 C48 485 11 510 -36 509 C36 548 99 533 146 508 C104 565 40 602 -1 600 C119 637 288 565 401 472 C502 389 556 243 508 158 Z',paint('sweep-material'))
    path(g,'fringe-upper-flow','M509 161 C395 144 300 180 214 240 C164 276 110 299 69 301 C152 326 238 290 301 250 C374 205 439 191 479 200 C432 279 338 343 227 371 C350 361 479 274 509 161 Z',paint('mid-sweep-material'))
    path(g,'fringe-middle-flow','M499 207 C466 330 327 421 155 451 C133 455 109 458 87 456 C166 492 270 459 351 411 C430 365 489 290 499 207 Z',paint('mid-sweep-material'))
    path(g,'fringe-low-flow','M498 262 C453 412 313 527 153 565 C109 576 82 581 47 580 C134 611 249 561 329 507 C427 441 484 350 498 262 Z',paint('mid-sweep-material'))
    path(g,'fringe-long-right','M507 157 C603 117 704 208 732 320 C757 422 730 488 731 534 C733 613 751 683 793 731 C713 707 650 629 630 540 C621 500 619 471 614 436 C607 535 574 603 520 638 C566 532 551 438 528 356 C503 276 476 211 507 157 Z',paint('fall-material'))
    path(g,'temple-right','M705 278 C798 338 832 442 834 544 C833 630 831 696 863 742 C835 731 818 713 805 690 C808 750 799 802 817 835 C765 815 739 778 730 729 C710 661 717 593 727 526 C741 424 720 343 705 278 Z',paint('side-material'))
    path(g,'temple-left','M-16 470 C19 489 30 523 24 568 C13 628 -3 685 9 739 C-17 721 -34 700 -39 679 C-45 725 -43 761 -22 787 C-68 774 -93 730 -88 672 C-81 590 -38 513 -16 470 Z',paint('side-material'))

def mask(g,profile):
    # The two masks are separate projected paths, never scaled from one profile.
    if profile=='short':
        base='M80 714 L251 661 L327 687 L523 687 L600 661 L790 716 L821 846 L629 947 L438 1005 L228 943 L53 835 Z'
        front='M251 661 L327 687 L523 687 L600 661 L690 780 L637 865 L528 922 L438 862 L355 922 L238 863 L185 780 Z'
        nose='M438 862 L528 922 L497 980 L438 1005 L380 987 L355 922 Z'
        left='M72 446 Q73 433 87 431 L160 418 L238 786 L188 870 L123 893 L39 822 Z'
        right='M720 426 Q730 418 742 424 L813 449 L866 815 L785 891 L715 869 L652 787 Z'
        pale_l='M81 446 L91 443 L64 794 L133 872 L123 879 L51 817 Z'
        pale_r='M798 448 L808 453 L853 813 L780 877 L771 872 L839 808 Z'
        top_rim='M263 668 L329 694 L523 694 L590 668 L598 675 L526 705 L326 705 L258 676 Z'
        connectors=[('left','M184 849 L201 844 L216 863 L209 881 L190 889 L175 875 L182 864 L189 870 L197 865 Z'),('right','M748 861 L762 850 L781 859 L788 874 L775 887 L757 883 L754 872 L769 877 L776 871 L766 868 Z')]
    else:
        base='M69 538 L224 491 L286 514 L447 514 L514 490 L692 542 L716 660 L552 744 L391 791 L215 740 L46 648 Z'
        front='M224 491 L286 514 L447 514 L514 490 L599 597 L554 670 L466 722 L391 670 L321 722 L218 670 L161 597 Z'
        nose='M391 670 L466 722 L441 770 L391 791 L342 775 L321 722 Z'
        left='M65 317 Q67 306 78 303 L141 291 L218 606 L171 680 L118 699 L32 640 Z'
        right='M624 297 Q633 288 644 293 L707 319 L758 633 L685 699 L623 681 L567 607 Z'
        pale_l='M73 317 L82 314 L55 617 L124 679 L116 685 L43 634 Z'
        pale_r='M695 319 L704 323 L746 631 L681 685 L674 680 L734 625 Z'
        top_rim='M233 498 L287 521 L447 521 L507 498 L514 505 L450 531 L284 531 L228 505 Z'
        connectors=[('left','M170 660 L184 656 L197 672 L191 688 L175 694 L162 682 L168 672 L175 677 L181 673 Z'),('right','M650 674 L662 664 L678 672 L684 685 L673 696 L658 692 L655 683 L668 687 L674 682 L665 679 Z')]
    path(g,'suppressor-shadow',base,'#c3aaa4',transform='translate(0 10)')
    path(g,'suppressor-base',base,paint('mask-central'))
    path(g,'suppressor-central-plane',front,paint('mask-crown'))
    path(g,'suppressor-nose-drop',nose,paint('mask-nose'))
    path(g,'suppressor-left-side',left,paint('mask-left'))
    path(g,'suppressor-right-side',right,paint('mask-right'))
    path(g,'suppressor-left-edge',pale_l,'#aab4bc')
    path(g,'suppressor-right-edge',pale_r,'#aab4bc')
    path(g,'suppressor-top-rim',top_rim,'#b7c2c7')
    for name,d in connectors: path(g,'suppressor-yellow-'+name,d,'#e1dc60')

def revise_visible_defects(root,branch,profile):
    """r002: bounded edits after real r001 inspection; r001 remains on disk."""
    ids={e.get('id'):e for e in root.iter() if e.get('id')}
    g=ids['entity']
    if profile=='short':
        ids['hair-back'].set('d','M-200 564 C-168 337 -63 219 165 160 C119 137 104 117 82 95 C168 99 242 131 294 157 C302 113 281 83 261 56 C337 74 389 119 427 156 C478 117 489 96 490 64 C533 91 551 114 554 143 C709 95 815 151 870 231 C907 285 949 310 1001 323 C967 341 941 336 923 329 C956 411 992 459 1042 484 C1005 495 980 482 963 469 C996 547 1020 568 1067 581 C1026 602 994 591 975 580 C1001 673 1012 722 1060 757 C1017 763 994 746 974 725 C998 820 985 875 1020 915 C981 906 956 877 944 851 C935 939 921 991 936 1028 C900 1014 876 979 858 949 C847 1014 823 1057 809 1082 C773 1050 752 1009 727 969 L66 1113 C-127 1015 -232 818 -200 564 Z')
        ids['hair-crown'].set('d','M-166 574 C-117 347 -33 216 188 174 C231 155 279 156 327 167 C369 143 418 149 450 175 C506 130 566 124 622 136 C741 142 833 211 881 299 C922 375 953 400 991 419 C945 435 911 408 886 390 C946 511 972 630 961 797 C918 930 806 1031 634 1062 L20 1002 C-137 873 -200 726 -166 574 Z')
        ids['fringe-long-right'].set('d','M580 180 C693 149 799 255 824 395 C843 500 825 577 824 638 C821 735 841 815 893 872 C807 844 733 753 713 643 C705 599 700 560 695 519 C704 590 696 636 681 676 C682 584 647 484 613 387 C580 301 538 242 580 180 Z')
    else:
        ids['hair-back'].set('d','M-105 498 C-97 310 -32 183 153 141 C119 123 97 101 85 78 C158 88 221 118 255 137 C266 110 259 84 247 62 C301 75 341 111 369 139 C414 114 430 90 433 71 C466 89 482 110 486 128 C629 80 741 138 797 232 C824 277 852 293 888 303 C860 318 838 310 825 303 C854 363 882 403 921 424 C892 438 868 428 852 419 C879 481 898 510 934 526 C903 541 878 534 861 522 C888 602 900 644 937 670 C906 681 880 665 864 646 C886 727 878 766 903 800 C873 795 849 777 836 754 C829 818 817 854 828 885 C797 873 779 849 764 823 C752 874 740 907 729 925 C699 904 681 870 672 843 L143 943 C-4 888 -112 704 -105 498 Z')
        ids['hair-crown'].set('d','M-84 491 C-60 312 31 199 182 164 C230 147 269 157 296 177 C332 148 359 147 391 166 C441 125 507 121 554 136 C655 126 739 184 777 263 C811 313 833 332 862 346 C832 351 811 343 793 333 C847 432 875 556 852 668 C822 798 699 899 530 923 L115 890 C-43 797 -117 650 -84 491 Z')
        ids['face'].set('d','M80 362 C212 253 435 254 619 332 C787 403 867 555 858 724 C850 831 772 916 621 941 C411 982 171 928 45 824 C-42 747 -68 663 -31 547 C-6 471 30 405 80 362 Z')
        ids['fringe-outer-sweep'].set('d','M508 158 C398 106 253 143 136 219 C47 277 -15 297 -78 288 C-33 349 42 356 101 344 C41 388 -21 410 -70 402 C-19 450 40 454 85 441 C48 485 11 510 -36 509 C36 548 99 533 146 508 C100 539 46 561 3 556 C129 594 297 529 401 445 C502 362 556 243 508 158 Z')
        ids['fringe-low-flow'].set('d','M498 262 C453 390 313 492 153 535 C109 546 82 551 47 550 C134 581 249 539 329 485 C427 419 484 350 498 262 Z')
        ids['fringe-long-right'].set('d','M507 157 C603 117 704 208 732 320 C757 422 730 488 731 534 C733 613 751 683 793 731 C713 707 650 629 630 540 C621 500 619 471 614 436 C622 503 605 536 594 566 C604 490 570 399 540 327 C509 246 478 204 507 157 Z')
        # Front inner neck now has a visible arc below the deliberately raised chin.
        ids['neck-inner'].set('d','M265 844 C381 881 553 910 673 845 L703 1002 C589 1059 380 1049 258 985 Z')
        for name in ('fastener-upper','fastener-lower-long'):
            ids[name].set('stroke','#56636b');ids[name].set('stroke-width','3')
        if branch=='unmasked':
            for name,x in [('eye-left',158),('eye-right',523)]:
                eye=ids[name];y=585;w=84;h=228;r=42
                eye.set('d',f'M{x+r},{y} A{r},{r} 0 0 1 {x+w},{y+r} L{x+w},{y+h-r} A{r},{r} 0 0 1 {x},{y+h-r} L{x},{y+r} A{r},{r} 0 0 1 {x+r},{y} Z')
            ids['eye-material'].set('y1','585');ids['eye-material'].set('y2','813')
    # Remove the overly broad peach crescent; replace it with a narrow real cast
    # support cloned from the actual hair outline and clipped to the face.
    old=ids['fringe-contact-shadow'];old.set('fill','none')
    d=ids['face'].get('d')
    clip=element(root.find('{'+S+'}defs'),'clipPath',id='forehead-shadow-receiver',clipPathUnits='userSpaceOnUse')
    path(clip,'forehead-shadow-receiver-shape',d,'#ffffff')
    shadows=ET.Element('{'+S+'}g',{'id':'hair-contact-shadows','clip-path':'url(#forehead-shadow-receiver)'})
    for id in ('fringe-outer-sweep','fringe-long-right'):
        cast=copy.deepcopy(ids[id]);cast.set('id',id+'-cast');cast.set('fill','#ead0c4' if branch=='unmasked' else '#27313a');cast.set('transform','translate(0 10)');shadows.append(cast)
    g.insert(list(g).index(old),shadows)
    # Analytic broad gloss retains smooth fields and adds no painted fragments.
    color_sets={
        'crown-material':['#626668','#42494f','#293039','#202731'],
        'sweep-material':['#646a70','#424c55','#252e38'],
        'mid-sweep-material':['#555e65','#37444e','#252f38'],
        'fall-material':['#59636b','#394750','#252f3a'],
    }
    for id,colors in color_sets.items():
        for stop,color in zip(ids[id],colors):stop.set('stop-color',color)

def revise_mask_and_collar(root,branch,profile):
    ids={e.get('id'):e for e in root.iter() if e.get('id')}
    g=ids['entity']
    if profile=='full':
        for id in ('collar-far-upright','collar-near-upright','collar-top-roll','collar-inner-shadow','zipper-shadow','zipper-metal','zipper-pull','ring-attachment-strap','fastener-upper','fastener-lower-long'):
            ids[id].set('transform','translate(0 45)')
    if branch!='masked':return
    if profile=='short':
        base='M80 714 L251 661 L327 687 L523 687 L600 661 L790 716 L821 846 L629 947 L426 1056 L228 943 L53 835 Z'
        nose='M438 824 L528 922 L497 986 L426 1056 L367 989 L355 922 Z'
        leftnose='M438 824 L426 1056 L367 989 L355 922 Z'
        ridge='M265 723 C327 728 378 773 414 815 L438 847 L473 809 L550 747 L559 758 L482 821 L438 869 L405 827 C367 785 322 743 262 738 Z'
        seam='M438 865 L439 978 L426 1056 L414 1044 L427 975 L427 860 Z'
        right='M625 459 Q630 446 644 451 L710 477 L757 812 L670 888 L609 864 L589 801 Z'
        rightedge='M700 476 L710 480 L746 809 L667 875 L657 870 L732 803 Z'
        connect='M634 859 L649 850 L666 860 L672 876 L658 887 L641 881 L639 870 L653 877 L660 872 L651 866 Z'
    else:
        base='M69 538 L224 491 L286 514 L447 514 L514 490 L692 542 L716 660 L552 744 L381 834 L215 740 L46 648 Z'
        nose='M391 635 L466 722 L440 776 L381 834 L332 779 L321 722 Z'
        leftnose='M391 635 L381 834 L332 779 L321 722 Z'
        ridge='M236 547 C287 552 335 592 366 628 L391 656 L420 624 L486 571 L493 581 L428 635 L391 676 L358 639 C326 604 284 566 233 560 Z'
        seam='M391 671 L392 769 L381 834 L371 824 L382 766 L382 666 Z'
        right='M540 332 Q546 322 557 326 L614 350 L656 638 L582 702 L529 684 L511 628 Z'
        rightedge='M605 350 L614 354 L646 635 L579 691 L571 686 L634 630 Z'
        connect='M552 678 L564 670 L579 679 L584 692 L572 702 L558 697 L556 688 L568 694 L574 689 L566 684 Z'
    ids['suppressor-base'].set('d',base);ids['suppressor-shadow'].set('d',base)
    ids['suppressor-nose-drop'].set('d',nose)
    ids['suppressor-right-side'].set('d',right)
    ids['suppressor-right-edge'].set('d',rightedge)
    ids['suppressor-yellow-right'].set('d',connect)
    d=root.find('{'+S+'}defs')
    linear(d,'mask-fold-material',(250,650 if profile=='short' else 500,570,970 if profile=='short' else 800),[(0,'#52616e'),(.42,'#88979e'),(.63,'#a8b3b7'),(1,'#52626f')])
    # The fold highlight follows the physical central facet and terminates at
    # its seam; it is not a hair highlight or arbitrary separate bright island.
    i=list(g).index(ids['suppressor-nose-drop'])+1
    for id,shape,fill in [('suppressor-nose-side-plane',leftnose,'#354553'),('suppressor-central-fold',ridge,paint('mask-fold-material')),('suppressor-nose-ridge',seam,'#71818d')]:
        node=ET.Element('{'+S+'}path',{'id':id,'d':shape,'fill':fill});g.insert(i,node);i+=1

def revise_mask_edge_clip(root,branch,profile):
    if branch!='masked':return
    ids={e.get('id'):e for e in root.iter() if e.get('id')}
    g=ids['entity'];d=root.find('{'+S+'}defs')
    clip=element(d,'clipPath',id='suppressor-central-silhouette',clipPathUnits='userSpaceOnUse')
    path(clip,'suppressor-central-silhouette-boundary',ids['suppressor-base'].get('d'),'#ffffff')
    common=ET.Element('{'+S+'}g',{'id':'suppressor-central-common-coverage','clip-path':'url(#suppressor-central-silhouette)'})
    at=list(g).index(ids['suppressor-base'])
    ids['suppressor-base'].set('d','M-100 -100 H1400 V1400 H-100 Z')
    if profile=='short':
        ids['suppressor-central-plane'].set('d','M151 500 L700 500 L690 780 L637 865 L528 922 L438 862 L355 922 L238 863 L185 780 Z')
        ids['suppressor-top-rim'].set('d','M239 645 L326 671 L523 671 L612 645 L606 676 L525 700 L327 700 L248 676 Z')
    else:
        ids['suppressor-central-plane'].set('d','M130 355 L614 355 L599 597 L554 670 L466 722 L391 670 L321 722 L218 670 L161 597 Z')
        ids['suppressor-top-rim'].set('d','M214 475 L286 498 L447 498 L526 475 L520 506 L449 527 L285 527 L222 506 Z')
    for id in ('suppressor-base','suppressor-central-plane','suppressor-nose-drop','suppressor-nose-side-plane','suppressor-central-fold','suppressor-nose-ridge','suppressor-top-rim'):
        g.remove(ids[id]);common.append(ids[id])
    g.insert(at,common)

def artwork(branch,profile,revision):
    root=ET.Element('{'+S+'}svg',{'width':'1280','height':'1280','viewBox':'0 0 1280 1280','role':'img','aria-labelledby':'title description'})
    element(root,'title',id='title').text=f'Endministrator male / {branch} / {profile}'
    element(root,'desc',id='description').text='Official-illustration-based male short swept hair. Original editable vector candidate, transparent background. Natural gradients without texture. User acceptance unassessed.'
    defs(root,profile,revision)
    g=element(root,'g',id='entity',transform='rotate(15 480 740)' if profile=='short' else 'rotate(15 450 570)')
    if profile=='short':
        short_back(g);short_face(g)
        if branch=='masked':mask(g,profile)
        else:
            capsule(g,'eye-left',145,712,100,268)
            capsule(g,'eye-right',575,712,100,268)
        short_front(g,revision)
    else:
        full_garment(g,revision);full_back(g,revision);full_face(g)
        if branch=='masked':mask(g,profile)
        else:
            capsule(g,'eye-left',158,538,84,228)
            capsule(g,'eye-right',523,538,84,228)
        full_front(g,revision)
    if revision in ('r002','r003','r004'):revise_visible_defects(root,branch,profile)
    if revision in ('r003','r004'):revise_mask_and_collar(root,branch,profile)
    if revision=='r004':revise_mask_edge_clip(root,branch,profile)
    return ET.tostring(root,encoding='unicode')+'\n'

def compose_overview(revision):
    board=Image.new('RGB',(1400,1580),'#e7e9ec')
    draw=ImageDraw.Draw(board)
    try: font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',28)
    except OSError:font=ImageFont.load_default()
    for col,branch in enumerate(('unmasked','masked')):
        for row,profile in enumerate(('short','full')):
            x=30+col*695;y=48+row*790
            im=Image.open(OUT/branch/profile/'revisions'/revision/'preview-1280.png').convert('RGBA')
            bg=Image.new('RGBA',im.size,'#f6f5f3' if row==0 else '#171d28')
            bg.alpha_composite(im)
            board.paste(bg.convert('RGB').resize((640,640),Image.Resampling.LANCZOS),(x,y))
            draw.text((x,y-35),f'MALE / {branch.upper()} / {profile.upper()} / {revision}',font=font,fill='#252c38')
            for j,size in enumerate((128,48,24)):
                sm=Image.open(OUT/branch/profile/'revisions'/revision/f'preview-{size}.png').convert('RGBA')
                sb=Image.new('RGBA',(size,size),'#ffffff');sb.alpha_composite(sm)
                board.paste(sb.convert('RGB'),(x+j*180,y+660))
    board.save(OUT/f'overview-{revision}.png')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--revision',default='r001');ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    revision=args.revision
    reports=[]
    for branch in ('masked','unmasked'):
        for profile in ('short','full'):
            target=OUT/branch/profile/'revisions'/revision
            if args.resume and (target/'generation.json').exists():
                reports.append(json.loads((target/'generation.json').read_text(encoding='utf-8')))
                continue
            if not (target/'actual-prompt.md').is_file():raise RuntimeError('Save actual prompt before drawing: '+str(target))
            svg=artwork(branch,profile,revision)
            validate_svg(svg)
            file=target/f'{profile}.svg'
            if file.exists():raise RuntimeError('Revision is immutable: '+str(file))
            file.write_text(svg,encoding='utf-8')
            shutil.copy2(__file__,target/'sourcecode.py')
            for size in (1280,128,48,24): (target/f'preview-{size}.png').write_bytes(render_svg_text(svg,size))
            im=Image.open(target/'preview-1280.png').convert('RGBA')
            for name,color in [('light','#faf9f6'),('dark','#111722')]:
                bg=Image.new('RGBA',im.size,color);bg.alpha_composite(im);bg.convert('RGB').save(target/f'preview-{name}.png')
            xml=ET.fromstring(svg)
            report={'branch':branch,'profile':profile,'revision':revision,'svg_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'sourcecode_sha256':hashlib.sha256((target/'sourcecode.py').read_bytes()).hexdigest(),'prompt_sha256':hashlib.sha256((target/'actual-prompt.md').read_bytes()).hexdigest(),'path_count':len(xml.findall('.//{'+S+'}path')),'renderer':backend_info(),'structural_validation':'passed static supported SVG subset','reference_basis':'official illustration','visual_review':'pending actual host image inspection','user_acceptance':'unassessed','capsule_visibility':'user-selected mask occlusion exception' if branch=='masked' else 'two unoccluded actual capsule paths intended','profile_difference':'independently authored head and garment geometry, not a transformed short group' if profile=='full' else 'tight head-only crop'}
            (target/'generation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            reports.append(report)
    compose_overview(revision)
    print(json.dumps(reports,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
