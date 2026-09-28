"""One-subject, hand-authored SVG calibration. No tracing or raster embedding."""
from pathlib import Path
from math import cos, sin, radians
import json
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def node(parent, tag, **attrs):
    return ET.SubElement(parent, f"{{{NS}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()})


PATHS = {
    "bob-back": "M -86 246 C -63 164 3 117 99 126 C 136 108 168 110 195 124 C 271 108 326 152 344 216 C 361 276 353 360 367 438 C 375 486 387 535 356 578 C 335 603 300 620 270 614 C 293 571 290 529 272 487 C 229 555 118 582 17 552 C -79 521 -127 436 -119 350 C -114 304 -101 266 -86 246 Z",
    "face-domain": "M -95 320 C -40 313 5 281 67 220 C 107 260 165 282 213 278 C 252 288 284 316 303 346 C 302 391 287 426 264 448 C 246 468 216 485 189 501 C 175 513 167 526 161 542 C 57 559 -43 523 -105 468 C -153 422 -159 385 -141 355 C -127 335 -111 326 -95 320 Z",
    "crown-swept": "M -86 279 C -87 200 -36 153 42 136 C 89 118 151 133 194 123 C 229 115 269 120 289 141 C 238 134 182 175 151 213 C 114 260 78 301 27 330 C -2 347 -25 359 -54 365 C -41 343 -38 323 -36 305 C -61 323 -84 333 -109 333 C -99 315 -89 297 -86 279 Z",
    "left-cheek-sweep": "M 285 142 C 235 137 190 161 148 197 C 100 237 61 299 45 356 C 30 405 30 443 47 478 C 0 452 -20 400 -10 348 C 0 289 35 230 95 182 C 157 132 230 117 285 142 Z",
    "short-right-fringe": "M 284 143 C 330 161 347 204 345 249 C 342 284 325 307 300 322 C 309 298 311 280 307 261 C 291 276 276 282 254 282 C 267 271 273 260 276 245 C 255 266 234 274 209 274 C 228 257 238 240 241 220 C 222 240 199 254 177 258 C 193 232 199 212 199 203 C 230 180 258 157 284 143 Z",
    "central-swept-forelock": "M 282 145 C 247 153 209 176 180 207 C 148 240 131 278 137 307 C 140 322 150 333 163 338 C 152 318 157 288 172 264 C 171 299 188 326 218 340 C 207 315 213 286 236 263 C 266 235 286 190 282 145 Z",
    "right-bob-turn": "M 335 230 C 359 302 342 371 345 429 C 347 479 370 529 349 572 C 335 602 303 618 270 614 C 307 586 315 544 305 510 C 296 477 282 452 281 423 C 281 389 295 355 318 328 C 341 300 344 272 335 230 Z",
    "right-cheek-lock": "M 332 288 C 327 341 294 362 290 420 C 287 463 308 488 321 505 C 289 497 269 466 266 430 C 263 384 282 344 310 314 C 320 302 327 294 332 288 Z",
    "main-bundle-dark-root": "M 23 181 C 25 138 37 108 62 86 C 84 67 115 64 132 79 C 110 74 96 87 95 110 C 91 142 69 166 54 187 Z",
    "main-bundle-rear-hook": "M 20 176 C -25 188 -81 151 -90 113 C -98 80 -82 40 -48 17 C -65 41 -72 60 -68 80 C -63 98 -48 110 -32 115 C -38 81 -21 48 2 40 C 22 31 36 37 40 46 C 15 42 9 60 12 78 C 13 99 31 117 42 135 Z",
    "main-bundle-front-hook": "M -6 137 C -26 106 -17 75 3 54 C 19 39 43 38 64 46 C 78 50 87 58 90 72 C 83 65 70 67 61 75 C 45 91 45 112 48 130 C 71 132 87 125 96 108 C 100 130 91 149 71 162 C 57 172 44 185 25 187 Z",
    "main-bundle-hanging-turn": "M -47 130 C -42 150 -29 158 -9 161 C 16 162 30 147 38 133 C 35 160 48 178 71 178 C 90 179 103 170 110 158 C 113 182 102 203 83 215 C 66 227 45 227 29 218 C 28 239 49 250 64 247 C 50 269 19 278 -5 270 C -26 265 -32 256 -32 243 C -45 254 -63 250 -72 236 C -84 216 -77 198 -60 186 C -84 187 -100 173 -99 151 C -98 143 -95 137 -91 130 C -81 145 -60 147 -47 130 Z",
    "main-bundle-fold": "M -45 131 C -34 154 -14 175 6 178 C -3 198 -2 235 18 260 C -10 243 -21 211 -19 193 C -39 204 -57 221 -64 239 C -68 216 -58 192 -43 178 C -61 181 -79 176 -89 162 C -70 166 -55 151 -45 131 Z",
    "main-bundle-lip": "M 5 54 C 28 38 55 39 75 54 C 64 54 53 59 46 67 C 30 60 15 61 1 73 C -4 92 -2 111 7 126 C -13 112 -17 77 5 54 Z",
    "main-bundle-rear-rim": "M -48 17 C -66 42 -72 61 -67 82 C -62 101 -47 111 -32 115 C -44 124 -59 119 -70 108 C -91 89 -83 49 -48 17 Z",
    "main-bundle-underturn": "M 39 153 C 45 174 64 190 83 189 C 94 187 102 179 110 158 C 113 182 102 203 83 215 C 58 226 34 212 28 197 C 25 182 31 166 39 153 Z",
    "secondary-coral": "M 338 319 C 361 324 375 340 375 359 C 389 350 392 335 385 323 C 410 339 414 365 399 385 C 421 380 434 363 429 344 C 454 370 440 407 412 423 C 394 438 372 439 356 428 C 355 445 340 453 324 450 C 331 438 332 422 327 407 C 311 393 313 368 324 353 Z",
    "secondary-root": "M 324 314 C 340 317 356 331 365 350 C 372 368 374 391 360 404 C 350 414 336 407 327 392 C 315 372 311 340 324 314 Z",
    "secondary-fold": "M 375 359 C 387 383 383 410 367 427 C 388 426 405 412 412 398 C 398 405 383 396 375 359 Z",
}


def create(profile):
    full = profile == "full"
    angle = 17 if full else 15
    pal = {
        "hair": "url(#hair-tone)" if full else "#57575f",
        "hair_dark": "#343640" if full else "#454750",
        "hair_front": "url(#sweep-tone)" if full else "#626069",
        "skin": "url(#skin-tone)" if full else "#fff1df",
        "coral": "url(#coral-tone)" if full else "#ee929e",
        "coral_dark": "#ce626f" if full else "#dc7b8b",
        "coral_light": "#ffb1bd" if full else "#f8a6b1",
        "halo": "url(#halo-tone)" if full else "#69cac1",
        "halo_dark": "#378f96" if full else "#4aa5a6",
    }
    svg = ET.Element(f"{{{NS}}}svg", {"width":"512", "height":"512", "viewBox":"0 0 512 512", "role":"img", "aria-labelledby":"icon-title"})
    node(svg, "title", id="icon-title").text = f"img1 direct SVG calibration {profile} candidate"
    defs = node(svg, "defs")
    if full:
        for gid, x1,y1,x2,y2, stops in [
            ("hair-tone", 0,120,140,580, [("0%","#69656d"),("48%","#53525d"),("100%","#383d47")]),
            ("sweep-tone",100,135,50,470,[("0%","#79717a"),("55%","#615d66"),("100%","#42454f")]),
            ("skin-tone",0,290,300,565,[("0%","#fff1e7"),("65%","#fff0e7"),("100%","#f3d8d1")]),
            ("coral-tone",-15,35,20,273,[("0%","#ffa9b6"),("45%","#f08a99"),("100%","#db7082")]),
            ("halo-tone",0,-45,0,45,[("0%","#8be4d2"),("45%","#57c0b6"),("100%","#3b9f9f")]),
        ]:
            gr=node(defs,"linearGradient",id=gid,x1=x1,y1=y1,x2=x2,y2=y2,gradientUnits="userSpaceOnUse")
            for offset,color in stops: node(gr,"stop",offset=offset,stop_color=color)
    clip = node(defs,"clipPath",id="face-clip")
    node(clip,"path",d=PATHS["face-domain"])
    head=node(svg,"g",id="head",transform=f"rotate({angle} 140 350)")
    # Halo coordinates are constructed in head-local space; final screen angle stays 43 deg.
    a=radians(angle)
    halo_dx,halo_dy=329-140,135-350
    hx=140+halo_dx*cos(a)+halo_dy*sin(a)
    hy=350-halo_dx*sin(a)+halo_dy*cos(a)
    halo=node(head,"g",id="halo",transform=f"translate({hx:.4f} {hy:.4f}) rotate({43-angle})")
    node(halo,"path",id="halo-left-point",d="M -110 -15 L -151 -10 L -112 10 Z",fill=pal["halo_dark"])
    node(halo,"path",id="halo-upper-point",d="M -41 -39 L -29 -91 L -6 -42 Z",fill=pal["halo"])
    node(halo,"path",id="halo-upper-facet",d="M -29 -91 L -23 -44 L -6 -42 Z",fill="#c2f3df" if full else "#a6e7d7")
    node(halo,"path",id="halo-right-point",d="M 107 -14 L 163 7 L 108 13 Z",fill=pal["halo"])
    node(halo,"path",id="halo-right-facet",d="M 116 -3 L 163 7 L 108 13 Z",fill=pal["halo_dark"])
    node(halo,"path",id="halo-ring",d="M 116 0 A 116 44 0 1 1 -116 0 A 116 44 0 1 1 116 0 Z M 108 0 A 108 35.5 0 1 0 -108 0 A 108 35.5 0 1 0 108 0 Z",fill=pal["halo"],fill_rule="evenodd")
    if full:
        node(halo,"path",id="halo-edge-light",d="M -111 -2 C -111 -25 -62 -41 0 -41 C 63 -41 111 -23 112 -2",fill="none",stroke="#b8efdd",stroke_width="1.8",stroke_linecap="round")

    def path(parent,key,fill,**kw): return node(parent,"path",id=key,d=PATHS[key],fill=fill,**kw)
    path(head,"secondary-coral",pal["coral"])
    path(head,"secondary-fold",pal["coral_dark"])
    path(head,"bob-back",pal["hair_dark"])
    path(head,"secondary-root",pal["hair_dark"])
    if full:
        node(head,"path",id="secondary-root-turn",d="M 329 326 C 336 349 342 370 357 389 C 348 385 335 379 330 367 C 324 353 324 338 329 326 Z",fill="#51525d")
    path(head,"face-domain",pal["skin"])
    # Cheeks are clipped to the skin geometry and composited BELOW every foreground hair mass.
    # The clip prevents escaping the face; normal occlusion removes the portions hidden by hair.
    cheeks=node(head,"g",id="cheeks",fill="#edb2b4" if full else "#efbab9",opacity="0.48" if full else "0.42",clip_path="url(#face-clip)")
    node(cheeks,"ellipse",cx=74,cy=405,rx=21,ry=11)
    node(cheeks,"ellipse",cx=248,cy=406,rx=21,ry=11)
    # Skin shadow belongs to the hair/skin junction and is clipped to this subject's face domain.
    shade=node(head,"g",id="hair-cast-shadow",clip_path="url(#face-clip)")
    node(shade,"path",d="M -28 325 C 65 275 114 206 156 191 C 214 216 272 254 309 295 L 320 365 C 269 324 237 310 187 300 C 142 289 111 270 85 250 C 54 290 13 331 -28 352 Z",fill="#e9c9c0" if full else "#f1d5c4",opacity="0.65" if full else "0.45")
    path(head,"crown-swept",pal["hair"])
    path(head,"right-bob-turn",pal["hair"])
    path(head,"short-right-fringe",pal["hair"])
    path(head,"central-swept-forelock",pal["hair_front"])
    path(head,"left-cheek-sweep",pal["hair_front"])
    path(head,"right-cheek-lock",pal["hair_dark"])
    if full:
        node(head,"path",id="crown-soft-plane",d="M -62 233 C -29 174 32 150 97 147 C 126 140 152 133 180 133 C 121 151 54 187 10 232 C -17 256 -40 276 -70 287 C -61 270 -58 253 -62 233 Z",fill="#8b8088",opacity="0.24")
        node(head,"path",id="sweep-wide-plane",d="M 262 143 C 211 155 164 184 127 222 C 82 270 53 324 44 374 C 41 332 65 270 103 225 C 149 171 214 139 262 143 Z",fill="#aaa0a5",opacity="0.18")
        node(head,"path",id="fringe-volume-plane",d="M 285 151 C 308 165 325 187 331 207 C 309 198 286 198 271 209 C 269 189 275 169 285 151 Z",fill="#92838b",opacity="0.28")
        node(head,"path",id="bob-outer-plane",d="M 341 350 C 336 403 343 468 353 507 C 358 540 341 573 317 589 C 335 553 326 514 320 487 C 312 448 319 393 341 350 Z",fill="#85818b",opacity="0.16")
    else:
        node(head,"path",id="sweep-wide-plane",d="M 262 143 C 211 155 164 184 127 222 C 82 270 53 324 44 374 C 41 332 65 270 103 225 C 149 171 214 139 262 143 Z",fill="#74717a",opacity="0.35")
    # The large coral structure remains off-centre and joins the head through a visible dark root.
    tuft=node(head,"g",id="main-coral-bundle",transform="translate(-20 64) scale(.82)")
    path(tuft,"main-bundle-dark-root",pal["hair_dark"])
    path(tuft,"main-bundle-rear-hook",pal["coral"])
    path(tuft,"main-bundle-rear-rim",pal["coral_light"])
    path(tuft,"main-bundle-front-hook",pal["coral"])
    path(tuft,"main-bundle-hanging-turn",pal["coral"])
    path(tuft,"main-bundle-fold",pal["coral_dark"],opacity="0.58" if full else "0.42")
    path(tuft,"main-bundle-lip",pal["coral_light"])
    path(tuft,"main-bundle-underturn",pal["coral_dark"],opacity="0.62" if full else "0.40")
    if full:
        node(tuft,"path",id="hanging-bundle-light",d="M -17 191 C -15 226 -2 253 18 267 C -9 262 -22 241 -25 213 Z",fill="#ffafba",opacity="0.35")
    eyes=node(head,"g",id="eyes",fill="#24252b" if full else "#000000")
    ew,eh=(35,96.25) if full else (92/3,92)
    for label,cx in [("left",84),("right",248)]:
        node(eyes,"rect",id=f"eye-{label}",x=cx-ew/2,y=340-eh/2,width=ew,height=eh,rx=ew/2)
    ET.indent(svg,space="  ")
    filename=OUT/f"{profile}.svg"
    ET.ElementTree(svg).write(filename,encoding="utf-8",xml_declaration=True)
    eye_midpoint=[140+26*cos(a)+10*sin(a),350+26*sin(a)-10*cos(a)]
    def document_scene(el):
        return {"type":el.tag.rsplit("}",1)[-1],"attributes":dict(el.attrib),"children":[document_scene(child) for child in el]}
    return {"profile":profile,"head_rotation_degrees":angle,"screen_halo_degrees":43,"halo_screen_center":[329,135],"eye_width":ew,"eye_height":eh,"eye_ratio":eh/ew,"eye_axis_canvas_fraction":eh/512,"eye_pair_screen_midpoint":eye_midpoint,"eye_pair_midpoint_canvas_fraction":[v/512 for v in eye_midpoint],"palette":pal,"svg":filename.name,"render_status":"awaiting root render","acceptance":"unaccepted","document":document_scene(svg)}


if __name__ == "__main__":
    for p in ("prompt-short.used.zh-CN.md","prompt-full.used.zh-CN.md","drawing-brief.md"):
        if not (OUT/p).is_file(): raise RuntimeError(f"Drawing input must already exist: {p}")
    profiles=[create("short"),create("full")]
    (OUT/"scene.json").write_text(json.dumps({"revision":"direct-svg-r002","base_revision":"revisions/r001","subject":"img_1, identity unverified","canvas":[512,512],"source_paths":PATHS,"profiles":profiles},ensure_ascii=False,indent=2),encoding="utf-8")
    report={}
    for profile in profiles:
        root=ET.parse(OUT/profile["svg"]).getroot()
        tags=[e.tag.rsplit("}",1)[-1] for e in root.iter()]
        rects=[e for e in root.iter() if e.tag.endswith("}rect")]
        forbidden=set(tags)&{"image","script","foreignObject","text","filter"}
        assert not forbidden, forbidden
        assert len(rects)==2 and all(e.attrib["id"].startswith("eye-") for e in rects)
        assert all("href" not in k for e in root.iter() for k in e.attrib)
        report[profile["profile"]]={"xml_parsed":True,"raster_embedding":False,"external_references":False,"visible_text":False,"background_element":False,"eye_count":len(rects),"eye_ratio":profile["eye_ratio"],"eye_axis_canvas_fraction":profile["eye_axis_canvas_fraction"],"eye_pair_midpoint_canvas_fraction":profile["eye_pair_midpoint_canvas_fraction"],"path_count":tags.count("path"),"gradient_count":tags.count("linearGradient"),"visual_acceptance":"NOT EVALUATED BY STRUCTURE CHECK"}
    (OUT/"structure-check.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
