"""Deterministic hand-authored female Endministrator SVG pair; stdlib only."""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parent

def path(identifier, d, fill, extra=""):
    return f'<path id="{identifier}" d="{d}" fill="{fill}" {extra}/>'

def build(profile):
    full = profile == "full"
    pieces = []
    def p(identifier, d, fill, extra=""):
        pieces.append(path(identifier, d, fill, extra))
    defs = '''<defs>
<linearGradient id="back-paint" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#242b31"/><stop offset=".62" stop-color="#30383e"/><stop offset="1" stop-color="#1d232b"/></linearGradient>
<linearGradient id="hair-paint" x1=".24" y1="0" x2=".62" y2="1"><stop stop-color="#424c50"/><stop offset=".42" stop-color="#333c42"/><stop offset=".75" stop-color="#3f4b54"/><stop offset="1" stop-color="#66717a"/></linearGradient>
<linearGradient id="left-paint" x1=".35" y1=".06" x2=".68" y2="1"><stop stop-color="#566065"/><stop offset=".38" stop-color="#394248"/><stop offset=".72" stop-color="#354048"/><stop offset="1" stop-color="#56656e"/></linearGradient>
<linearGradient id="right-paint" x1=".14" y1=".08" x2=".83" y2=".96"><stop stop-color="#394247"/><stop offset=".5" stop-color="#343e45"/><stop offset=".86" stop-color="#53616c"/><stop offset="1" stop-color="#65727b"/></linearGradient>
<linearGradient id="fringe-paint" x1=".45" y1="0" x2=".44" y2="1"><stop stop-color="#4d585d"/><stop offset=".34" stop-color="#3a444a"/><stop offset=".69" stop-color="#46545e"/><stop offset="1" stop-color="#63717b"/></linearGradient>
<radialGradient id="face-paint" cx=".44" cy=".46" r=".68"><stop stop-color="#fffcf5"/><stop offset=".58" stop-color="#fff3e8"/><stop offset="1" stop-color="#f6ddd2"/></radialGradient>
<radialGradient id="eye-paint" cx=".38" cy=".2" r=".88"><stop stop-color="#333c50"/><stop offset=".48" stop-color="#242c3d"/><stop offset="1" stop-color="#151c2b"/></radialGradient>
<linearGradient id="eye-edge" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#4c5669"/><stop offset=".32" stop-color="#1c2436"/><stop offset="1" stop-color="#101727"/></linearGradient>
<linearGradient id="silver-paint" x1="0" y1="0" x2="1" y2=".7"><stop stop-color="#e8eeed"/><stop offset=".35" stop-color="#cbd5d5"/><stop offset=".72" stop-color="#849399"/><stop offset="1" stop-color="#c9d4d6"/></linearGradient>
<linearGradient id="visor-paint" x1=".12" y1="0" x2=".65" y2="1"><stop stop-color="#52606a"/><stop offset=".52" stop-color="#303b44"/><stop offset="1" stop-color="#202b33"/></linearGradient>
<linearGradient id="collar-paint" x1=".2" y1="0" x2=".8" y2="1"><stop stop-color="#f7fbfc"/><stop offset=".54" stop-color="#d9e1e7"/><stop offset="1" stop-color="#9facb9"/></linearGradient>
<radialGradient id="strand-gloss" cx=".47" cy=".43" r=".58"><stop stop-color="#9ba5ad" stop-opacity=".23"/><stop offset=".42" stop-color="#8997a2" stop-opacity=".12"/><stop offset="1" stop-color="#74818b" stop-opacity="0"/></radialGradient>
<linearGradient id="cheek-paint" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffd5d1"/><stop offset="1" stop-color="#fbc8c6"/></linearGradient>
<linearGradient id="contact-paint" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#e8c3b6"/><stop offset="1" stop-color="#fff3e8"/></linearGradient>
</defs>'''
    if full:
        p("collar-underlay", "M275 862 Q470 815 639 877 L763 1015 L251 1054 L183 931Z", "#27313b")
        p("collar-left", "M222 842 L415 907 L441 989 L271 1060 L156 912Z", "url(#collar-paint)")
        p("collar-right", "M628 853 L798 871 L752 1033 L517 1025 L549 935Z", "url(#collar-paint)")
        p("collar-yellow-tab", "M698 924 L757 932 L739 1000 L684 986Z", "#eed85e")
        p("collar-inner-shadow", "M350 879 Q492 929 637 883 L586 965 Q474 998 402 942Z", "#3a4550")
    p("bob-back", "M107 349 C90 204 200 92 345 87 C514 52 733 100 820 243 C900 374 913 533 918 671 C924 827 917 910 971 947 C909 959 882 938 859 902 C870 963 837 1000 792 1012 C811 967 793 936 777 916 C727 990 626 1001 579 965 L249 961 C150 974 76 920 90 823 C43 870 14 861 0 835 C57 800 54 714 68 618Z", "url(#back-paint)")
    p("face", "M200 319 C295 257 505 276 672 339 C813 392 857 501 847 653 C838 804 741 913 598 943 C439 976 228 918 158 802 C84 681 112 439 200 319Z", "url(#face-paint)")
    p("eye-left", "M254 562 C254 536 274 517 297 517 C320 517 339 536 339 562 L339 654 C339 681 320 701 296 701 C272 701 254 681 254 654Z", "url(#eye-paint)", 'stroke="url(#eye-edge)" stroke-width="2.1"')
    p("eye-right", "M613 562 C613 536 633 517 656 517 C679 517 698 536 698 562 L698 654 C698 681 679 701 655 701 C631 701 613 681 613 654Z", "url(#eye-paint)", 'stroke="url(#eye-edge)" stroke-width="2.1"')
    pieces.append('<ellipse id="cheek-left" cx="212" cy="724" rx="67" ry="37" fill="url(#cheek-paint)"/>')
    pieces.append('<ellipse id="cheek-right" cx="724" cy="724" rx="64" ry="36" fill="url(#cheek-paint)"/>')
    p("crown", "M73 442 C64 265 136 146 266 105 C417 36 631 66 758 174 C815 220 855 309 865 429 C780 357 728 346 634 346 C424 302 252 337 154 427 L73 478Z", "url(#hair-paint)")
    p("fringe-left", "M435 96 C382 145 374 222 344 282 C313 348 233 408 183 472 C143 524 134 584 148 638 C87 592 73 529 99 449 C124 359 194 327 225 265 C264 183 305 105 435 96Z", "url(#left-paint)")
    p("fringe-center-left", "M472 99 C450 166 491 210 480 276 C469 339 431 410 380 468 C355 497 349 522 353 546 C300 500 315 427 351 368 C386 307 425 224 422 174Z", "url(#fringe-paint)")
    p("fringe-center-right", "M512 104 C602 120 678 202 674 288 C672 377 624 435 558 471 C536 485 520 503 514 528 C477 483 490 418 522 367 C557 311 572 265 554 214 C544 170 526 139 512 104Z", "url(#hair-paint)")
    p("fringe-right", "M568 128 C706 138 807 227 836 350 C863 461 815 520 808 599 C768 572 747 518 748 465 C740 505 718 525 694 541 C708 481 683 445 678 401 C670 340 717 284 671 221 C650 188 609 149 568 128Z", "url(#right-paint)")
    p("side-left-main", "M137 369 C111 478 93 574 111 663 C127 747 128 823 192 877 C113 866 75 803 66 739 C31 792 18 813 -13 821 C54 710 27 648 45 552 C55 473 92 406 137 369Z", "url(#left-paint)")
    p("side-right-main", "M800 283 C894 380 930 553 899 710 C878 821 833 865 844 926 C792 900 771 840 790 773 C752 844 713 871 667 873 C753 800 727 715 763 647 C811 555 833 414 800 283Z", "url(#right-paint)")
    if full:
        p("left-forward-sweep", "M441 111 C388 181 352 234 309 278 C263 326 213 348 184 392 C209 322 244 281 276 235 C322 169 371 116 441 111Z", "url(#fringe-paint)")
        p("left-inner-sweep", "M432 150 C412 229 387 287 343 332 C313 365 282 392 268 427 C246 379 274 338 305 306 C353 257 391 204 432 150Z", "url(#left-paint)")
        p("center-front-lock", "M503 122 C530 183 536 250 509 309 C489 353 466 378 460 414 C428 384 435 340 451 305 C479 244 482 188 478 155Z", "url(#fringe-paint)")
        p("right-forward-lock", "M619 159 C701 199 747 261 743 324 C739 383 713 415 724 462 C684 436 665 403 670 362 C676 312 695 283 674 239 C660 209 638 180 619 159Z", "url(#left-paint)")
        p("left-bob-front-lock", "M95 471 C80 592 115 673 98 757 C90 800 102 853 140 892 C80 869 53 817 64 757 C82 658 39 567 95 471Z", "url(#fringe-paint)")
        p("right-bob-front-lock", "M859 429 C884 539 876 642 837 707 C816 746 810 790 823 828 C777 797 777 750 796 705 C832 625 859 534 859 429Z", "url(#fringe-paint)")
        p("left-underlock", "M80 657 C64 750 98 884 168 932 C104 921 68 889 51 850 C43 900 14 917 -14 912 C48 846 14 776 80 657Z", "url(#hair-paint)")
        p("right-underlock", "M874 682 C894 787 842 925 890 969 C817 951 792 899 815 836 C777 904 773 965 795 1000 C723 956 737 885 787 811Z", "url(#hair-paint)")
        p("crown-swept-lock", "M401 94 C328 115 271 157 240 202 C297 164 350 165 403 139 C431 125 453 113 474 106 C451 91 426 89 401 94Z", "url(#left-paint)")
        p("left-flow-gloss", "M435 96 C382 145 374 222 344 282 C313 348 233 408 183 472 C143 524 134 584 148 638 C87 592 73 529 99 449 C124 359 194 327 225 265 C264 183 305 105 435 96Z", "url(#strand-gloss)")
        p("right-flow-gloss", "M800 283 C894 380 930 553 899 710 C878 821 833 865 844 926 C792 900 771 840 790 773 C752 844 713 871 667 873 C753 800 727 715 763 647 C811 555 833 414 800 283Z", "url(#strand-gloss)")
    p("raised-visor-connected", "M294 265 L387 236 L472 267 L540 245 L619 278 L609 302 L539 273 L472 293 L386 264 L307 289Z", "url(#visor-paint)")
    p("visor-connected-rim", "M294 265 L387 236 L472 267 L540 245 L619 278 L617 283 L540 251 L472 273 L387 242 L296 271Z", "#dfcc64")
    p("clip-cross-long", "M145 278 L151 272 L224 344 L217 351Z", "url(#silver-paint)")
    p("clip-cross-short", "M145 335 L214 282 L219 291 L151 344Z", "url(#silver-paint)")
    transform = 'translate(22 -11) rotate(14 500 520)' if full else 'translate(-105 -150) scale(1.21) rotate(14 500 520)'
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">\n'
            '<title>Female Endministrator, '+profile+' gloss study</title>\n'+defs+'\n<g id="subject" transform="'+transform+'">\n'+'\n'.join(pieces)+'\n</g>\n</svg>\n')

def main():
    for profile in ("short", "full"):
        raw = build(profile).encode("utf-8")
        (ROOT / f"{profile}.svg").write_bytes(raw)
    design = {
        "schema": "aikon.direct-svg-study.v2", "subject": "endministrator-female", "round": "002",
        "source": "Official female Endministrator standing illustration; recorded in docs/research/input-fixtures.md",
        "identity": ["charcoal shoulder-length bob", "left silver crossed clips", "angular black visor with yellow trim"],
        "adaptation": "Visor raised and reduced to a thin forehead accessory so both Grok-bot eyes remain fully visible. This is a style adaptation, not literal original visor placement.",
        "short": {"composition": "1.21x tight crop, no collar", "hair": "five major fringe masses and two broad side locks", "gloss": "continuous material gradients and dark capsule eye fields"},
        "full": {"composition": "complete crown and more side contours, shallow collar at bottom", "hair": "six separate added broad locks: forward and inner left sweeps, central short lock, right forward lock, left/right front bob; plus crown and lower bob locks", "gloss": "continuous gradients plus two broad analytic highlights covering whole owning locks, avoiding detached ribbons"},
        "surface_policy": "Opaque material bases; no raster image, filters, random noise, dithering, or white eye glints.",
        "user_acceptance": "pending", "generator": "build.py, Python standard library", "image_generation_model_used": False,
        "geometry_reused_from_rejected_round_001": False,
        "files": {p: hashlib.sha256((ROOT / f"{p}.svg").read_bytes()).hexdigest() for p in ("short", "full")}
    }
    (ROOT / "design.json").write_text(json.dumps(design, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

if __name__ == "__main__":
    main()
