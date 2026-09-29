"""Independent raw-reference reconstruction. No prior artwork imported.
Run with existing .local/ci-venv/Scripts/python.exe draw.py; hard stop 45s.
"""
from pathlib import Path
import sys, os, threading, json, hashlib, time
threading.Timer(45, lambda: os._exit(124)).start()
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text, backend_info
from PIL import Image, ImageDraw
from io import BytesIO
import numpy as np

defs=[]; shapes=[]
def linear(name,coords,stops):
    defs.append(f'<linearGradient id="{name}" gradientUnits="userSpaceOnUse" x1="{coords[0]}" y1="{coords[1]}" x2="{coords[2]}" y2="{coords[3]}">'+''.join(f'<stop offset="{s}" stop-color="{c}"/>' for s,c in stops)+'</linearGradient>')
def radial(name,cx,cy,rx,ry,stops):
    defs.append(f'<radialGradient id="{name}" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="1" gradientTransform="translate({cx} {cy}) scale({rx} {ry})">'+''.join(f'<stop offset="{s}" stop-color="{c}"/>' for s,c in stops)+'</radialGradient>')
def path(name,d,fill,stroke=None,width=1):
    shapes.append(f'<path id="{name}" d="{d}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{width}"' if stroke else '')+'/>')
linear('rear-blue',(930,650,1230,1300),[(0,'#18204b'),(.58,'#303f79'),(1,'#354c8b')])
linear('front-blue',(350,280,240,845),[(0,'#41599f'),(.5,'#4968b0'),(1,'#7098d4')])
linear('crown-blue',(400,245,750,740),[(0,'#3f508f'),(1,'#415ba5')])
linear('center-blue',(440,310,470,850),[(0,'#475a9d'),(.45,'#4866b0'),(1,'#7b99d6')])
linear('side-blue',(790,520,820,1270),[(0,'#41579e'),(.50,'#4b67af'),(1,'#79a7dd')])
linear('side-inner-blue',(732,620,846,1030),[(0,'#4863a9'),(1,'#6c94d0')])
linear('white-cloth',(440,145,1060,1100),[(0,'#fffdfd'),(.58,'#f9f5fa'),(1,'#babbd4')])
linear('cloth-fold',(500,300,1030,1060),[(0,'#d4d1e6'),(1,'#b5b6d0')])
linear('bow-blue',(960,730,1120,940),[(0,'#6693d2'),(1,'#6194d8')])
linear('bow-edge',(1000,780,1110,940),[(0,'#4777c1'),(1,'#456ac0')])
radial('face-field',405,885,740,500,[(0,'#fffffe'),(.2,'#fffdf9'),(.6,'#fff0e5'),(1,'#f7e6e6')])
linear('eye-field',(174,696,697,1040),[(0,'#20253f'),(.55,'#1e243b'),(1,'#20263f')])
linear('eye-rim',(200,670,652,1030),[(0,'#1a203a'),(.55,'#101731'),(1,'#0d152f')])
defs.append('<clipPath id="canvas-crop"><path d="M 290 0 H 990 C 1167 0 1280 113 1280 290 V 990 C 1280 1167 1167 1280 990 1280 H 290 C 113 1280 0 1167 0 990 V 290 C 0 113 113 0 290 0 Z"/></clipPath>')

# Complete opaque parent shapes precede their child materials.
path('rear-hair','M 718 456 C 877 402 1016 558 1080 728 C 1100 792 1100 847 1132 899 C 1174 979 1190 1050 1258 1103 C 1252 1136 1188 1153 1110 1124 C 1132 1201 1158 1249 1190 1300 L 730 1300 Z','url(#rear-blue)')
path('rear-frill-support','M 923 898 C 970 969 992 1010 1055 1042 C 1120 1116 1199 1141 1247 1123 C 1224 1149 1172 1150 1134 1133 C 1109 1148 1059 1116 1042 1093 C 1027 1114 984 1065 980 1000 Z','url(#cloth-fold)')
path('rear-frill-light','M 985 991 C 1004 1012 1026 1031 1055 1042 C 1050 1062 1046 1083 1042 1093 C 1028 1113 984 1068 980 1000 Z','url(#white-cloth)')
path('rear-frill-center','M 1055 1042 C 1088 1076 1113 1097 1140 1109 C 1139 1120 1134 1130 1134 1133 C 1103 1148 1058 1114 1042 1093 Z','url(#white-cloth)')
path('rear-frill-end','M 1140 1109 C 1182 1124 1219 1133 1247 1123 C 1225 1149 1173 1151 1134 1133 Z','url(#white-cloth)')
path('rear-lower-flow','M 917 989 C 952 1089 981 1191 952 1287 L 973 1287 C 1003 1249 1027 1193 1028 1130 C 1037 1199 1067 1247 1091 1287 L 857 1287 Z','#435ca4')
path('rear-lower-cut','M 975 1158 C 985 1211 982 1239 973 1262 C 993 1247 1018 1198 1028 1130 L 1049 1287 L 946 1287 Z','#324884')

# Continuous underlying headband and seven broad fabric lobes.
path('headband-fold-parent','M -25 251 C 13 220 47 204 58 227 C 83 170 170 146 192 185 L 199 188 C 225 138 337 114 381 151 L 391 166 L 421 164 C 453 128 520 153 545 181 L 577 187 L 591 198 C 623 153 719 204 747 237 C 759 253 752 267 752 270 L 763 279 C 810 259 877 313 900 369 C 908 389 899 402 898 404 L 906 423 C 954 421 1005 492 1005 545 C 1006 568 997 574 991 579 L 988 593 C 1039 606 1051 696 1030 733 C 1017 749 985 742 966 732 L -20 499 Z','url(#cloth-fold)')
path('frill-left','M 58 227 C 77 183 153 151 181 171 C 190 175 194 180 192 185 C 188 204 181 224 173 240 L 95 267 C 80 254 65 235 62 215 Z','url(#white-cloth)')
path('frill-center','M 210 171 C 240 125 322 122 369 141 C 382 147 391 157 391 166 C 388 186 379 210 370 229 L 234 234 C 223 211 214 191 210 171 Z','url(#white-cloth)')
path('frill-center-right','M 421 164 C 447 139 483 145 513 155 L 504 260 L 436 238 C 428 211 423 186 421 164 Z','url(#white-cloth)')
path('frill-upper-right','M 603 189 C 639 170 705 205 734 230 C 756 248 758 262 748 277 C 732 297 714 314 699 326 L 604 283 C 598 246 597 210 603 189 Z','url(#white-cloth)')
path('frill-mid-right','M 773 276 C 814 266 865 312 889 349 C 904 373 908 388 898 404 C 880 419 861 433 840 444 L 753 385 C 757 334 765 295 773 276 Z','url(#white-cloth)')
path('frill-side','M 914 425 C 952 423 987 466 1000 511 C 1008 539 1007 559 997 570 C 978 581 951 587 926 590 L 874 512 C 886 477 899 446 914 425 Z','url(#white-cloth)')
path('frill-side-bottom','M 996 598 C 1027 612 1047 662 1038 704 L 1037 710 C 1011 708 990 706 963 701 L 948 648 Z','url(#white-cloth)')

# Exposed face is authored from observed projection, not an ellipse.
path('face-parent','M -20 611 C 117 581 240 479 343 435 C 478 417 627 507 683 655 C 734 739 805 842 821 913 C 828 1018 814 1126 782 1205 C 766 1241 744 1268 727 1289 L -20 1289 Z','url(#face-field)')
path('fringe-shadow-left','M 211 584 C 255 555 304 510 335 472 L 330 526 C 287 544 247 565 211 584 Z','#f1cbbf')
path('fringe-shadow-right','M 654 580 C 682 642 703 711 726 762 L 635 630 Z','#f2c9bd')

# Main covering: a dark crown supports broad, overlapping curls.
path('hair-crown-parent','M -20 300 C 140 234 268 209 425 233 C 609 250 763 321 864 463 C 944 576 973 720 984 839 C 1013 1029 990 1173 915 1253 C 889 1276 863 1283 835 1284 L 736 1288 C 773 1250 798 1208 810 1175 C 856 1174 900 1141 926 1108 C 898 1140 849 1175 795 1177 C 773 1178 754 1175 739 1168 C 777 1145 801 1116 811 1088 C 829 1027 823 967 808 916 C 758 850 708 759 682 686 L 654 592 C 635 682 600 770 552 812 C 552 830 556 843 561 855 C 490 841 438 799 404 736 C 388 703 381 666 381 606 C 380 680 377 724 387 761 C 329 722 315 651 320 574 C 321 538 325 504 333 474 C 246 573 142 646 28 680 C 10 735 7 803 35 845 C 7 837 -10 827 -20 814 Z','url(#crown-blue)')
path('left-sweep','M -20 413 C 81 292 156 254 231 237 C 320 225 411 242 492 274 C 430 290 391 343 354 403 C 333 447 322 499 279 543 C 208 614 125 652 28 680 C 9 736 8 803 35 845 C 8 838 -9 827 -20 814 Z','url(#front-blue)')
path('left-sweep-fold','M 26 681 C 48 616 100 540 174 458 C 124 528 101 590 90 658 Z','#415b9f')
path('left-sweep-deep-fold','M 232 572 C 287 521 326 467 354 403 C 341 443 337 459 333 475 C 302 514 270 546 232 572 Z','#314783')
path('center-fringe','M 491 276 C 556 269 617 310 658 373 C 714 456 734 526 743 579 C 713 539 687 512 668 507 C 670 624 631 741 552 812 C 552 828 556 844 560 854 C 486 839 430 790 402 731 C 387 699 380 659 381 606 C 378 681 377 724 387 761 C 337 729 314 654 321 569 C 324 500 337 445 354 403 C 403 339 452 298 491 276 Z','url(#center-blue)')
path('center-curl-fold','M 560 721 C 551 756 548 789 552 812 C 554 803 559 793 562 787 C 555 765 557 743 560 721 Z','#4967af')
path('right-inner-fringe','M 668 508 C 711 495 754 552 786 641 C 812 726 817 830 807 917 C 751 847 708 757 686 675 C 674 632 668 575 668 508 Z','url(#side-inner-blue)')
path('right-inner-fold','M 774 668 C 792 747 795 837 807 917 C 789 895 782 882 773 869 C 789 816 782 729 774 668 Z','#3d5297')
path('right-main-lock','M 650 343 C 772 392 861 461 915 568 C 976 690 991 865 992 978 C 995 1103 968 1198 918 1247 C 894 1267 866 1276 838 1278 C 890 1235 915 1168 927 1108 C 882 1167 799 1190 739 1168 C 783 1141 805 1113 813 1083 C 838 1001 878 915 871 806 C 870 900 839 978 796 1019 C 818 933 806 847 793 767 C 783 699 774 638 746 580 C 725 493 694 407 650 343 Z','url(#side-blue)')
path('right-lock-fold','M 871 806 C 877 917 842 1001 813 1083 C 824 1053 823 1023 822 994 C 852 927 870 872 871 806 Z','#3e559c')

# Crescent / whale-like identity crest, connected to its root.
path('identity-crescent','M 208 87 C 271 11 379 2 464 30 C 535 53 581 94 589 144 C 600 203 553 252 501 278 L 478 278 C 496 238 490 192 461 147 C 428 96 370 63 310 62 C 273 62 238 72 208 87 Z','#445ba3', '#4965b0', 1)

# Two-part side accessory with its knot and overlapped folds.
path('bow-left-shadow','M 968 760 C 980 730 996 725 1013 739 C 1042 762 1060 807 1049 845 C 1042 870 1017 885 989 887 Z','url(#bow-edge)')
path('bow-left','M 969 753 C 982 727 995 724 1011 738 C 1039 761 1054 800 1048 829 C 1043 858 1022 872 990 869 Z','url(#bow-blue)')
path('bow-right-shadow','M 1052 813 C 1073 785 1127 766 1139 800 C 1151 830 1128 898 1110 921 C 1094 940 1064 901 1050 870 C 1040 851 1044 826 1052 813 Z','url(#bow-edge)')
path('bow-right','M 1058 814 C 1076 788 1127 767 1137 796 C 1149 823 1129 884 1114 906 C 1102 924 1075 897 1060 866 C 1050 844 1051 827 1058 814 Z','url(#bow-blue)')
path('bow-knot','M 1047 810 C 1058 807 1068 819 1066 835 C 1064 850 1055 858 1042 854 C 1046 840 1049 824 1047 810 Z','#6490d0')
path('bow-left-crease','M 1046 836 C 1029 835 1023 827 1029 821 C 1035 814 1044 823 1046 836 Z','#4d7bc7')
path('bow-right-crease','M 1063 835 C 1071 827 1081 834 1082 841 C 1082 852 1070 850 1063 844 Z','#4b79c7')

# Measured projected capsules; rims remain integrated, no pupil/catchlight.
path('eye-left-rim','M 226 670 C 257 670 280 693 279 727 C 278 756 264 817 247 854 C 237 879 217 887 194 882 C 164 878 146 856 148 826 C 150 795 167 737 179 708 C 190 682 207 670 226 670 Z','#fffaf2')
path('eye-left','M 226 672 C 256 672 278 695 277 727 C 276 756 262 816 245 853 C 235 877 217 884 195 880 C 166 876 148 855 150 826 C 152 795 169 738 181 709 C 191 684 208 672 226 672 Z','url(#eye-field)','url(#eye-rim)',2.4)
path('eye-right-rim','M 652 823 C 681 823 704 849 705 880 C 706 910 690 970 676 1003 C 666 1028 646 1035 623 1030 C 594 1025 579 1004 580 977 C 581 948 597 891 608 861 C 617 837 633 823 652 823 Z','#fffaf4')
path('eye-right','M 652 825 C 680 825 701 849 703 880 C 704 910 688 969 674 1002 C 664 1026 646 1033 624 1028 C 596 1023 581 1003 582 977 C 583 948 599 892 610 862 C 619 839 634 825 652 825 Z','url(#eye-field)','url(#eye-rim)',2.4)
shapes.append('<ellipse id="cheek-left" cx="60" cy="904" rx="76" ry="47" transform="rotate(24 60 904)" fill="#ffd5d3"/>')
shapes.append('<ellipse id="cheek-right" cx="697" cy="1098" rx="69" ry="43" transform="rotate(23 697 1098)" fill="#ffd4d2"/>')

svg='<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280" viewBox="0 0 1280 1280"><title>DeepSeek short raw-reference reconstruction</title><desc>Editable semantic vector reconstruction; transparent background; unaccepted calibration draft.</desc><defs>'+''.join(defs)+'</defs><g id="portrait" clip-path="url(#canvas-crop)">'+''.join(shapes)+'</g></svg>'
(ROOT/'short.svg').write_text(svg,encoding='utf-8')
reports={}
for size in [1280,128,48,24]:
    png=render_svg_text(svg,size)
    (ROOT/f'preview-{size}.png').write_bytes(png)
    reports[str(size)]={'png_sha256':hashlib.sha256(png).hexdigest(),'bytes':len(png)}
# Inspection board contains actual-size outputs, with presentation backgrounds outside SVG.
board=Image.new('RGB',(960,410),'#e7e7eb'); d=ImageDraw.Draw(board)
for j,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    x=j*320
    d.rectangle((x,0,x+319,409),fill=bg)
    for y,s in [(32,128),(220,48),(320,24)]:
        im=Image.open(ROOT/f'preview-{s}.png').convert('RGBA')
        board.paste(im,(x+36,y),im)
        d.text((x+181,y+4),f'{s} px',fill='#999999')
board.save(ROOT/'inspection-board.png')
ref=Image.open(REPO/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGBA')
out=Image.open(ROOT/'preview-1280.png').convert('RGBA')
pair=Image.new('RGB',(1280,640),'#0f0f0f')
for idx,im in enumerate([ref,out]):
    im=im.resize((640,640),Image.Resampling.LANCZOS); pair.paste(im,(idx*640,0),im)
pair.save(ROOT/'reference-comparison.png')
a=np.asarray(out); fg=a[:,:,3]>0
reports.update({'backend':backend_info(),'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'shape_count':len(shapes),'opaque_pixels':int((a[:,:,3]==255).sum()),'transparent_pixels':int((a[:,:,3]==0).sum()),'upper_right_alpha':int(a[50,1200,3]),'user_acceptance':'unassessed','visual_review':'pending'})
(ROOT/'render-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print(json.dumps(reports))
os._exit(0)
