"""Deterministic hand-authored male Endministrator SVG pair; stdlib only."""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parent

def build(profile):
    full = profile == "full"
    layers=[]
    def p(identifier,d,fill,extra=""):
        layers.append(f'<path id="{identifier}" d="{d}" fill="{fill}" {extra}/>')
    defs='''<defs>
<linearGradient id="rear-paint" x1=".3" y1="0" x2=".65" y2="1"><stop stop-color="#343b3e"/><stop offset=".65" stop-color="#2b333b"/><stop offset="1" stop-color="#1d2630"/></linearGradient>
<linearGradient id="crown-paint" x1=".2" y1="0" x2=".7" y2="1"><stop stop-color="#586063"/><stop offset=".4" stop-color="#3f484c"/><stop offset=".75" stop-color="#4b5861"/><stop offset="1" stop-color="#65727c"/></linearGradient>
<linearGradient id="swept-paint" x1=".2" y1=".05" x2=".86" y2=".96"><stop stop-color="#4f595c"/><stop offset=".4" stop-color="#374249"/><stop offset=".78" stop-color="#52616c"/><stop offset="1" stop-color="#758089"/></linearGradient>
<linearGradient id="central-paint" x1=".4" y1="0" x2=".56" y2="1"><stop stop-color="#596367"/><stop offset=".45" stop-color="#3d494f"/><stop offset=".77" stop-color="#4e5d67"/><stop offset="1" stop-color="#7c8991"/></linearGradient>
<linearGradient id="side-paint" x1=".15" y1="0" x2=".74" y2="1"><stop stop-color="#3d484d"/><stop offset=".5" stop-color="#35414a"/><stop offset="1" stop-color="#5e707e"/></linearGradient>
<radialGradient id="skin-paint" cx=".42" cy=".39" r=".74"><stop stop-color="#fffcf4"/><stop offset=".55" stop-color="#fff2e5"/><stop offset="1" stop-color="#f2d9cd"/></radialGradient>
<radialGradient id="eye-paint" cx=".39" cy=".22" r=".87"><stop stop-color="#333d50"/><stop offset=".49" stop-color="#232d3f"/><stop offset="1" stop-color="#131c2d"/></radialGradient>
<linearGradient id="eye-edge" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#4d596d"/><stop offset=".35" stop-color="#182336"/><stop offset="1" stop-color="#0f192a"/></linearGradient>
<linearGradient id="visor-paint" x1=".18" y1="0" x2=".69" y2="1"><stop stop-color="#65717a"/><stop offset=".4" stop-color="#3b4852"/><stop offset="1" stop-color="#1d2b37"/></linearGradient>
<linearGradient id="collar-paint" x1=".22" y1="0" x2=".8" y2="1"><stop stop-color="#f6fafb"/><stop offset=".62" stop-color="#d6e0e7"/><stop offset="1" stop-color="#a4b3c1"/></linearGradient>
<radialGradient id="broad-gloss" cx=".49" cy=".38" r=".64"><stop stop-color="#b5c0c2" stop-opacity=".22"/><stop offset=".43" stop-color="#8c9ba4" stop-opacity=".11"/><stop offset="1" stop-color="#7a8c98" stop-opacity="0"/></radialGradient>
<linearGradient id="cheek-paint" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffd7d0"/><stop offset="1" stop-color="#f6c7c3"/></linearGradient>
</defs>'''
    if full:
        p("neck-underlayer","M350 810 L647 827 L758 1011 L252 1039Z","#2a3540")
        p("collar-left-fold","M201 846 L346 867 L446 971 L350 1040 L153 946Z","url(#collar-paint)")
        p("collar-right-fold","M652 829 L826 852 L768 994 L514 1019 L540 936Z","url(#collar-paint)")
        p("collar-yellow-insert","M244 933 L338 967 L321 1028 L211 977Z","#e6d45e")
        p("collar-dark-interior","M342 858 Q502 918 650 862 L594 944 Q462 985 402 937Z","#3a4652")
        p("collar-fastening","M488 969 L541 966 L544 1001 L491 1008Z","#8594a2")
    p("short-hair-rear","M117 303 C139 176 284 96 438 105 C603 81 758 146 807 261 C827 334 828 467 874 522 L834 517 L854 594 L809 568 L805 651 L777 617 L739 773 C673 842 306 844 192 760 L147 651 L118 674 L131 588 L78 625 L102 540 L55 563 L95 472 C69 417 80 357 117 303Z","url(#rear-paint)")
    p("face","M216 326 C318 276 558 288 680 354 C785 411 818 515 809 661 C801 791 717 879 615 914 C495 956 340 923 231 864 C139 813 111 747 120 623 C129 494 152 386 216 326Z M119 608.8 H122.2 V612 H119Z","url(#skin-paint)")
    p("ear-right","M786 586 C842 564 858 626 833 662 C819 681 804 684 790 674Z","#efcbbb")
    p("eye-left","M255 561 C255 537 274 518 297 518 C320 518 339 537 339 561 L339 651 C339 678 320 698 297 698 C274 698 255 678 255 651Z","url(#eye-paint)",'stroke="url(#eye-edge)" stroke-width="2"')
    p("eye-right","M604 561 C604 537 623 518 646 518 C669 518 688 537 688 561 L688 651 C688 678 669 698 646 698 C623 698 604 678 604 651Z","url(#eye-paint)",'stroke="url(#eye-edge)" stroke-width="2"')
    layers.append('<ellipse id="cheek-left" cx="210" cy="719" rx="63" ry="35" fill="url(#cheek-paint)"/>')
    layers.append('<ellipse id="cheek-right" cx="726" cy="714" rx="57" ry="33" fill="url(#cheek-paint)"/>')
    p("crown-silhouette","M100 418 C104 330 86 317 48 302 C104 289 110 264 146 238 L88 221 C149 209 162 189 186 159 L142 152 C204 120 257 112 311 105 C279 84 237 86 203 91 C254 52 318 63 357 76 C392 35 446 13 488 38 C458 41 438 62 424 89 C497 61 573 80 618 103 L595 58 C670 81 698 110 720 145 C795 162 817 195 847 228 L806 224 C838 261 855 296 868 335 L829 313 C850 355 850 404 833 461 C745 355 628 338 553 340 C382 310 269 343 191 440Z","url(#crown-paint)")
    p("swept-left-main","M480 126 C415 125 382 170 351 209 C303 270 229 296 187 336 C143 379 129 432 143 481 C86 440 93 367 123 324 C155 277 206 264 227 228 C266 171 361 94 480 126Z","url(#swept-paint)")
    p("swept-front-left","M488 134 C468 198 442 243 397 282 C348 324 276 344 244 389 C224 416 214 444 214 466 C184 421 204 365 244 332 C287 295 331 274 362 228 C404 168 438 145 488 134Z","url(#central-paint)")
    p("center-fringe-main","M508 131 C546 185 554 242 538 298 C521 359 479 409 472 474 C428 439 415 390 435 338 C460 269 486 228 483 174Z","url(#central-paint)")
    p("right-fringe-main","M538 132 C652 145 734 210 752 301 C768 376 739 437 733 495 C710 478 693 449 683 420 C695 461 686 493 665 513 C653 461 607 426 598 381 C593 328 634 296 605 238 C589 197 566 162 538 132Z","url(#swept-paint)")
    p("left-temple","M155 346 C131 420 139 479 159 525 C173 558 172 601 184 632 C154 620 135 598 129 574 L120 616 C88 547 96 486 101 453 C107 404 122 374 155 346Z","url(#side-paint)")
    p("right-temple","M736 261 C824 320 841 414 819 484 C800 544 817 576 810 616 C785 595 773 573 772 544 C756 585 744 598 724 609 C739 555 732 521 751 474 C778 404 772 335 736 261Z","url(#side-paint)")
    if full:
        p("fringe-left-upper-layer","M476 137 C424 204 359 232 310 269 C282 290 263 315 259 337 C235 316 245 282 265 262 C317 211 390 181 423 151Z","url(#central-paint)")
        p("fringe-left-lower-layer","M414 239 C378 303 331 332 304 375 C290 398 292 423 291 444 C266 420 259 391 275 362 C302 312 359 287 414 239Z","url(#swept-paint)")
        p("center-fine-lock","M489 186 C479 253 478 297 450 330 C424 361 416 385 419 409 C390 385 389 355 409 326 C442 278 465 232 489 186Z","url(#side-paint)")
        p("right-fringe-inner-layer","M604 204 C674 237 697 295 676 353 C662 392 645 409 651 440 C620 416 610 387 618 357 C633 306 642 276 624 243Z","url(#central-paint)")
        p("upper-left-swept-lock","M408 87 C328 74 265 118 224 160 C185 199 161 227 112 245 C159 251 202 237 237 206 C300 149 338 111 408 87Z","url(#central-paint)")
        p("crown-rise-lock","M387 133 C410 81 436 49 477 37 C453 32 429 37 406 52 C373 73 361 99 351 121Z","url(#swept-paint)")
        p("right-top-lock","M600 127 C650 150 677 180 697 215 C711 241 731 256 758 267 C741 269 726 267 709 263 C682 233 668 204 645 180Z","url(#central-paint)")
        p("lower-left-lock","M136 542 C127 589 146 641 175 668 L173 713 C153 691 137 672 130 654 L120 689 C108 636 102 592 136 542Z","url(#side-paint)")
        p("lower-right-lock","M805 516 C805 565 834 590 846 603 L816 602 C829 623 836 651 834 673 L803 645 L795 684 C783 650 776 621 788 591Z","url(#side-paint)")
        p("left-broad-gloss","M480 126 C415 125 382 170 351 209 C303 270 229 296 187 336 C143 379 129 432 143 481 C86 440 93 367 123 324 C155 277 206 264 227 228 C266 171 361 94 480 126Z","url(#broad-gloss)")
        p("center-broad-gloss","M508 131 C546 185 554 242 538 298 C521 359 479 409 472 474 C428 439 415 390 435 338 C460 269 486 228 483 174Z","url(#broad-gloss)")
    p("raised-visor-connected","M278 260 L374 226 L451 256 L532 235 L627 273 L613 296 L531 262 L452 284 L374 254 L291 286Z","url(#visor-paint)")
    p("visor-connected-rim","M278 260 L374 226 L451 256 L532 235 L627 273 L624 279 L532 242 L451 263 L374 233 L281 267Z","#e2ce63")
    transform='translate(31 10) rotate(14 500 520)' if full else 'translate(-87 -125) scale(1.2) rotate(14 500 520)'
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">\n<title>Male Endministrator '+profile+' gloss study</title>\n'+defs+'\n<g id="subject" transform="'+transform+'">\n'+'\n'.join(layers)+'\n</g>\n</svg>\n'

def main():
    for profile in ("short","full"):
        (ROOT / f"{profile}.svg").write_bytes(build(profile).encode("utf-8"))
    design={"schema":"aikon.direct-svg-study.v2","subject":"endministrator-male","round":"002",
        "identity":["asymmetric charcoal short hair","upturned crown locks","yellow-edged angular black forehead visor"],
        "source":"Official male Endministrator standing illustration; docs/research/input-fixtures.md",
        "adaptation":"Original eye-covering visor raised and compressed into forehead accessory to show both bot eyes; no claim of literal placement.",
        "short":{"composition":"1.2x close crop, cropped crown, no collar","hair":"four broad frontal locks and two short temples","surface":"continuous low-frequency color fields and dark blue eye gloss"},
        "full":{"composition":"full raised crown silhouette, visible ear and shallow collar","hair":"four additional front layers, extra crown locks and short temple tips, distinct from female shoulder-length bob","surface":"two broad radial highlights cover exact owning locks, preserving smooth flow"},
        "user_acceptance":"pending","image_generation_model_used":False,"geometry_reused_from_rejected_round_001":False,
        "source_rebuild":"python build.py","surface_policy":"Opaque bases; transparent canvas; no bitmap/filter/noise/dithering/white eye glint.",
        "revision_eye_clearance":"Only inner tip/curve of right-fringe-main retreats from unchanged right capsule; eyes and whole-head transform unchanged. See eye-clearance-report.json.",
        "revision_seam_repair":"Existing face underpaint gets a tiny opaque overlap subpath beneath left temple; true viewport-bottom collar exterior AA is preserved, as shown by expanded-canvas diagnostic.",
        "files":{p:hashlib.sha256((ROOT/f"{p}.svg").read_bytes()).hexdigest() for p in ("short","full")}}
    (ROOT/"design.json").write_text(json.dumps(design,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
