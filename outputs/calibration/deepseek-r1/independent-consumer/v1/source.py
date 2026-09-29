"""Independent visual reconstruction. No input bitmap is read by this generator.
Run with the repository verification Python, bounded externally to 45 seconds.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tools.render_svg import render_svg_file, validate_svg

OUT = Path(__file__).resolve().parent

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280" viewBox="0 0 1280 1280" color-interpolation="sRGB">
<title>DeepSeek, independent short calibration v1</title>
<desc>Manual semantic vector reconstruction from the visually inspected Cetus-derived r1 reference. Transparent background. No bitmap or automatic trace.</desc>
<defs>
 <linearGradient id="hair-field" gradientUnits="userSpaceOnUse" x1="510" y1="310" x2="510" y2="1160"><stop stop-color="#405395"/><stop offset="0.43" stop-color="#4863ab"/><stop offset="1" stop-color="#739dd6"/></linearGradient>
 <linearGradient id="bang-field" gradientUnits="userSpaceOnUse" x1="486" y1="313" x2="474" y2="861"><stop stop-color="#43599e"/><stop offset="0.53" stop-color="#4966ae"/><stop offset="1" stop-color="#7799d4"/></linearGradient>
 <linearGradient id="left-field" gradientUnits="userSpaceOnUse" x1="175" y1="270" x2="157" y2="789"><stop stop-color="#405397"/><stop offset="0.45" stop-color="#4865af"/><stop offset="1" stop-color="#719ed6"/></linearGradient>
 <linearGradient id="rear-field" gradientUnits="userSpaceOnUse" x1="1030" y1="692" x2="920" y2="1280"><stop stop-color="#1c234f"/><stop offset="1" stop-color="#374e92"/></linearGradient>
 <linearGradient id="fin-field" gradientUnits="userSpaceOnUse" x1="1009" y1="790" x2="1196" y2="1117"><stop stop-color="#293367"/><stop offset="1" stop-color="#34457f"/></linearGradient>
 <linearGradient id="pale-fin-field" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#bab9d4"/><stop offset="1" stop-color="#e0dfea"/></linearGradient>
 <radialGradient id="face-field" gradientUnits="userSpaceOnUse" cx="426" cy="872" r="602" gradientTransform="matrix(1 0 0 0.91 0 78)"><stop stop-color="#fffefa"/><stop offset="0.55" stop-color="#fff2e8"/><stop offset="1" stop-color="#f7e7e5"/></radialGradient>
 <linearGradient id="frill-field" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fffefd"/><stop offset="1" stop-color="#f7f2fa"/></linearGradient>
 <linearGradient id="bow-field" gradientUnits="userSpaceOnUse" x1="979" y1="729" x2="1135" y2="911"><stop stop-color="#729fdc"/><stop offset="1" stop-color="#6091d3"/></linearGradient>
 <linearGradient id="eye-field" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#232943"/><stop offset="0.6" stop-color="#20263e"/><stop offset="1" stop-color="#1f263e"/></linearGradient>
 <linearGradient id="eye-rim" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#404966"/><stop offset="0.45" stop-color="#252c48"/><stop offset="1" stop-color="#101a31"/></linearGradient>
 <clipPath id="canvas"><path d="M0 0H1280V1280H0Z"/></clipPath>
</defs>
<g id="portrait" clip-path="url(#canvas)">
 <g id="rear-hair" data-material="hair-back">
  <path id="rear-hair-mass" fill="url(#rear-field)" d="M951 541 C1045 606 1082 708 1106 827 C1138 996 1095 1083 1147 1234 C1098 1262 1048 1278 1000 1288 L743 1288 C797 1198 814 1081 854 947Z"/>
  <path id="rear-tip-turn" fill="#455da3" d="M942 1037 C961 1125 997 1194 974 1263 C1005 1237 1018 1188 1029 1130 C1036 1197 1064 1245 1088 1276 L948 1291 C978 1237 984 1174 975 1153 C979 1217 954 1267 940 1289 L868 1289Z"/>
 </g>
 <g id="whale-side-fin" data-material="whale-fin">
  <path id="fin-pale-underside" fill="url(#pale-fin-field)" d="M987 942 C1013 1004 1056 1045 1110 1075 C1161 1105 1219 1138 1257 1107 L1244 1132 C1207 1155 1163 1142 1133 1132 C1107 1148 1068 1120 1045 1096 C1039 1108 1014 1091 1005 1074 C987 1046 981 1006 987 942Z"/>
  <path id="fin-underside-fold" fill="#b7b7d0" d="M987 958 C1007 1005 1037 1030 1055 1044 L1045 1096 C1023 1105 1003 1077 994 1050Z"/>
  <path id="fin-upper" fill="url(#fin-field)" d="M1005 794 C1051 804 1086 817 1112 856 C1154 929 1187 1045 1256 1106 L1246 1126 C1194 1131 1129 1101 1087 1077 C1039 1048 1006 1016 989 979 L988 867Z"/>
  <path id="fin-root-shadow" fill="#19234d" d="M997 807 L1065 846 C1054 878 1023 910 987 927Z"/>
 </g>
 <g id="headdress" data-material="white-cloth">
  <path id="headdress-fold-base" fill="#d0cee2" d="M-3 291 L8 230 C34 213 47 215 58 228 C64 182 165 143 188 178 L198 190 C219 133 280 126 327 132 C365 134 390 143 391 166 L422 164 C448 144 478 140 511 158 L581 202 C613 159 692 191 733 226 C751 242 758 258 751 271 L763 279 C798 265 830 291 858 316 C889 344 913 380 899 404 L911 424 C951 417 982 463 998 507 C1010 539 1007 563 990 575 L992 594 C1028 602 1043 650 1040 684 C1041 713 1031 735 1016 742 L970 758 C935 583 852 439 724 353 C507 207 279 199 -3 291Z"/>
  <path id="frill-left" fill="url(#frill-field)" d="M60 215 C76 184 151 151 182 172 C194 179 192 185 190 195 C186 213 182 225 174 238 L95 258Z"/>
  <path id="frill-crown" fill="url(#frill-field)" d="M209 171 C235 135 282 129 314 132 C355 132 388 143 391 165 C387 189 378 210 369 227 L233 230 C222 209 215 189 209 171Z"/>
  <path id="frill-curl-under" fill="url(#frill-field)" d="M422 164 C445 145 463 145 481 150 L511 260 L436 237 C428 211 425 188 422 164Z"/>
  <path id="frill-upper-right" fill="url(#frill-field)" d="M601 190 C635 171 699 199 734 229 C752 245 757 258 750 272 C738 292 718 313 701 328 L603 282 C600 250 597 219 601 190Z"/>
  <path id="frill-mid-right" fill="url(#frill-field)" d="M774 277 C811 266 849 304 873 330 C897 357 911 383 900 402 C884 419 861 433 843 444 L758 364 C760 329 765 297 774 277Z"/>
  <path id="frill-lower-right" fill="url(#frill-field)" d="M915 424 C949 420 980 461 995 500 C1007 532 1011 556 991 574 C973 582 952 588 928 590 L881 500 C891 472 902 442 915 424Z"/>
  <path id="frill-side" fill="url(#frill-field)" d="M993 595 C1025 604 1041 648 1040 681 L1036 712 L961 702 L948 653 C965 628 980 607 993 595Z"/>
 </g>
 <g id="face" data-material="skin">
  <path id="face-main" fill="url(#face-field)" d="M-42 562 C84 462 254 384 429 424 C634 458 800 651 839 879 C852 1029 814 1186 739 1286 L285 1285 C173 1283 84 1235 34 1146 C-15 1061 -29 956 -27 838Z"/>
  <path id="fringe-cast-shadow-left" fill="#f1cbc0" d="M232 571 C273 535 309 497 338 462 L322 531Z"/>
  <path id="fringe-cast-shadow-right" fill="#f2cdc2" d="M656 588 C671 630 691 689 708 738 L644 645Z"/>
 </g>
 <g id="bow" data-material="blue-ribbon">
  <path id="bow-bottom-shadow" fill="#426bc0" d="M971 771 C980 720 1007 746 1030 780 L1059 811 C1085 776 1129 771 1138 794 C1150 822 1135 884 1112 917 C1095 941 1061 900 1047 856 C1028 884 1009 890 980 887Z"/>
  <path id="bow-left-loop" fill="url(#bow-field)" d="M971 754 C984 719 1008 726 1027 754 C1040 771 1056 808 1050 831 C1046 857 1027 872 985 870Z"/>
  <path id="bow-right-loop" fill="url(#bow-field)" d="M1057 814 C1074 791 1121 769 1135 790 C1154 819 1129 889 1110 911 C1094 925 1067 888 1055 862 C1047 840 1047 828 1057 814Z"/>
  <path id="bow-fold-left" fill="#5078c3" d="M1047 829 C1030 808 1021 824 1031 833 L1044 838Z"/>
  <path id="bow-knot" fill="#6494d6" d="M1047 812 C1055 808 1063 816 1064 829 C1064 843 1055 853 1045 849 L1042 838Z"/>
  <path id="bow-fold-right" fill="#4d76bf" d="M1064 835 C1073 826 1084 837 1081 844 C1076 855 1065 846 1061 844Z"/>
 </g>
 <g id="front-hair" data-material="blue-hair">
  <path id="hair-continuous-base" fill="url(#hair-field)" d="M-28 304 C136 232 291 205 454 239 C690 248 880 381 954 660 C989 796 1008 970 978 1112 C958 1207 904 1257 838 1257 C882 1225 916 1169 927 1108 C888 1158 805 1193 739 1168 C783 1145 805 1116 812 1087 C824 1015 819 951 800 906 L651 585 C631 718 590 782 552 811 L560 854 C453 830 393 748 382 673 C377 711 380 743 387 761 C304 708 313 568 333 475 C260 566 152 644 26 681 C9 735 6 800 35 846 C9 837 -10 829 -24 818Z"/>
  <path id="crown-left-plane" fill="#394d8c" d="M-21 299 C111 246 244 217 358 226 C174 238 74 306 -20 416Z"/>
  <path id="left-flow" fill="url(#left-field)" d="M-25 422 C116 272 274 222 390 244 C402 327 368 407 333 475 C269 560 151 643 26 681 C4 746 9 807 35 846 L-28 823Z"/>
  <path id="left-strand-shadow" fill="#374e92" d="M26 681 C63 592 121 515 174 458 C130 526 99 600 89 658Z"/>
  <path id="left-tip-shadow" fill="#304681" d="M232 571 C284 530 322 473 353 405 C336 450 334 471 332 478 C302 514 268 546 232 571Z"/>
  <path id="center-bang" fill="url(#bang-field)" d="M490 274 C566 269 630 338 657 410 C686 496 665 635 622 719 C600 763 574 794 552 811 C550 785 554 751 560 723 C548 779 550 826 560 854 C457 832 394 750 382 674 C379 650 379 623 382 597 C376 666 378 722 387 761 C307 711 311 568 333 475 C348 386 413 297 490 274Z"/>
  <path id="side-bang-shadow" fill="#324884" d="M667 509 C663 642 715 798 780 879 L804 916 C761 816 711 692 680 620Z"/>
  <path id="side-tip-shadow" fill="#3c5393" d="M774 673 C771 769 805 864 814 940 L797 1019 C846 958 869 868 871 805 C875 925 840 1043 812 1087 C822 1013 820 951 801 910 C777 834 778 748 774 673Z"/>
  <path id="top-curl" fill="#425aa1" d="M208 87 C274 4 420 -3 514 43 C583 77 609 137 578 203 C561 239 533 261 501 277 L480 280 C506 219 471 145 419 105 C358 53 275 53 208 87Z"/>
 </g>
 <g id="eyes" data-material="dark-eye">
  <g id="eye-left" transform="translate(214 777) rotate(14)">
   <path id="eye-left-rim" fill="url(#eye-rim)" d="M0-109 C32-109 53-85 53-54 L53 54 C53 86 32 108 0 108 C-33 108-54 86-54 54 L-54-54 C-54-86-32-109 0-109Z"/>
   <path id="eye-left-core" fill="url(#eye-field)" d="M0-106 C30-106 50-83 50-53 L50 54 C50 83 30 105 0 105 C-30 105-51 83-51 54 L-51-53 C-51-83-30-106 0-106Z"/>
  </g>
  <g id="eye-right" transform="translate(644 928) rotate(14)">
   <path id="eye-right-rim" fill="url(#eye-rim)" d="M0-105 C31-105 52-82 52-51 L52 51 C52 82 31 105 0 105 C-32 105-53 82-53 51 L-53-51 C-53-82-31-105 0-105Z"/>
   <path id="eye-right-core" fill="url(#eye-field)" d="M0-102 C29-102 49-80 49-51 L49 51 C49 80 29 102 0 102 C-30 102-50 80-50 51 L-50-51 C-50-80-30-102 0-102Z"/>
  </g>
 </g>
 <g id="cheeks" data-material="blush">
  <ellipse id="cheek-left" cx="57" cy="904" rx="78" ry="48" transform="rotate(23 57 904)" fill="#ffd6d2"/>
  <ellipse id="cheek-right" cx="697" cy="1098" rx="69" ry="43" transform="rotate(23 697 1098)" fill="#fdd5d2"/>
 </g>
</g>
</svg>
'''

def main():
    target = OUT / 'v1'
    target.mkdir(exist_ok=True)
    (target / 'short.svg').write_text(SVG, encoding='utf-8')
    (target / 'source.py').write_bytes(Path(__file__).read_bytes())
    (target / 'prompt.txt').write_bytes((OUT / 'prompt-v1.txt').read_bytes())
    parsed = validate_svg(SVG)
    reports = {}
    for size in [1280, 128, 48, 24]:
        reports[str(size)] = render_svg_file(target / 'short.svg', target / f'preview-{size}.png', size)
    reports['construction'] = {'paths': sum(e.tag.endswith('}path') for e in parsed.iter()), 'raster_inputs_read_by_generator': False, 'geometry_source': 'independent manual visual estimates', 'status': 'structurally_checked; visual_review_pending; user_acceptance_pending'}
    (target / 'render-report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps({'created': str(target), 'svg_sha256': hashlib.sha256(SVG.encode()).hexdigest()}))

if __name__ == '__main__':
    main()
