"""Full r001, source-A maid clothing with r1 head identity; hard limit 45s."""
from pathlib import Path
import os,threading,sys,json,hashlib,copy,shutil
t=threading.Timer(45,lambda:os._exit(124));t.daemon=True;t.start()
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from render_svg import render_svg_text,validate_svg,backend_info
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def tag(n):return '{'+NS+'}'+n
basepath=REPO/'outputs/calibration/deepseek-r1/independent-consumer-round3/r004/short.svg'
base=basepath.read_text(encoding='utf-8');tree=ET.fromstring(base)
defs=tree.find(tag('defs'));head=tree.find(tag('g'));head.set('id','full-r1-head');head.attrib.pop('clip-path')
defs.remove(next(e for e in defs if e.get('id')=='canvas-crop'))
stage=ET.Element(tag('g'),{'id':'full-composition','transform':'translate(0 0) scale(0.76)'})
tree.remove(head);tree.append(stage)
tree.find(tag('title')).text='DeepSeek full — selected blue-white maid attire'
tree.find(tag('desc')).text='Transparent SVG. R1 head identity plus user-selected candidate A white pleated chest panel, dark navy bow and shoulder straps. Unseen jaw, neck pose and lower hair are creative adaptation, not official r1 costume evidence. Unaccepted candidate.'
def grad(name,xy,stops):
    e=ET.SubElement(defs,tag('linearGradient'),dict(id=name,gradientUnits='userSpaceOnUse',x1=str(xy[0]),y1=str(xy[1]),x2=str(xy[2]),y2=str(xy[3])))
    for z,c in stops:ET.SubElement(e,tag('stop'),{'offset':str(z),'stop-color':c})
def path(group,name,d,fill):return ET.SubElement(group,tag('path'),{'id':name,'d':d,'fill':fill})
grad('full-neck-field',(360,1355,410,1475),[(0,'#edcbc2'),(.55,'#f5dcd1'),(1,'#faeadd')])
grad('full-dress-field',(100,1400,900,1720),[(0,'#283152'),(.45,'#353f69'),(1,'#202845')])
grad('full-cloth-field',(300,1370,490,1730),[(0,'#fbf6f4'),(.4,'#fefbfa'),(1,'#e1dfeb')])
grad('full-cloth-fold',(260,1370,540,1700),[(0,'#c9c9dc'),(.5,'#ece7ee'),(1,'#b4bbd2')])
grad('full-bow-field',(320,1395,540,1495),[(0,'#334163'),(.45,'#25334f'),(1,'#1d2945')])
grad('full-strap-field',(250,1380,630,1760),[(0,'#202944'),(.5,'#35415f'),(1,'#1b2540')])

# Continuing lower hair has its own complete parent; source side-fin rim and
# hook/bow/headband remain unchanged above the crop boundary.
back=ET.SubElement(stage,tag('g'),{'id':'full-back-hair-adaptation'})
path(back,'full-back-hair-parent','M 744 1123 C 919 1117 1098 1191 1178 1290 C 1229 1393 1219 1536 1268 1656 C 1157 1669 1068 1587 1036 1519 C 1060 1634 1000 1720 917 1753 L 624 1753 C 739 1600 775 1446 733 1300 Z','url(#measured-rear-hair)')
path(back,'full-back-hair-flow','M 889 1179 C 999 1288 1002 1459 1128 1629 C 1022 1594 964 1521 952 1413 C 960 1591 838 1691 748 1711 C 851 1570 886 1435 856 1280 Z','url(#measured-rear-lower-flow)')
path(back,'full-back-hair-fold','M 952 1413 C 960 1544 900 1635 819 1695 C 878 1602 893 1516 879 1433 Z','url(#measured-rear-lower-cut)')

body=ET.SubElement(stage,tag('g'),{'id':'full-selected-maid-attire','transform':'rotate(18 430 1490)'})
path(body,'maid-dress-shoulders','M 265 1369 C 123 1378 15 1459 -72 1633 L -72 1800 H 1040 C 1000 1569 817 1425 609 1380 C 506 1357 364 1351 265 1369 Z','url(#full-dress-field)')
path(body,'neck-adaptation','M 331 1303 C 329 1362 341 1406 354 1454 L 563 1454 C 550 1394 541 1344 550 1297 Z','url(#full-neck-field)')

# Broad A-source chest panel, with its left and right dark shoulder straps.
path(body,'maid-white-chest-panel','M 283 1393 C 329 1407 363 1426 426 1438 C 492 1447 554 1422 604 1398 C 638 1497 667 1660 638 1794 L 252 1794 C 249 1668 255 1513 283 1393 Z','url(#full-cloth-field)')
path(body,'maid-left-strap','M 253 1373 C 270 1380 288 1388 306 1393 C 283 1533 281 1667 292 1793 L 229 1793 C 222 1648 231 1495 253 1373 Z','url(#full-strap-field)')
path(body,'maid-right-strap','M 579 1398 C 596 1388 614 1380 636 1377 C 673 1531 691 1680 680 1793 L 620 1793 C 634 1655 607 1491 579 1398 Z','url(#full-strap-field)')
path(body,'maid-left-pleat-shadow','M 285 1401 C 309 1411 325 1422 343 1437 L 328 1465 L 345 1491 L 320 1514 L 334 1546 L 311 1570 L 329 1600 L 303 1625 L 316 1657 L 292 1680 C 287 1576 285 1484 285 1401 Z','url(#full-cloth-fold)')
path(body,'maid-left-pleats','M 290 1400 C 311 1407 329 1417 346 1434 L 319 1458 L 344 1482 L 313 1507 L 332 1537 L 308 1562 L 325 1590 L 301 1617 L 311 1648 L 291 1673 C 282 1560 279 1474 290 1400 Z','#fbf8f9')
path(body,'maid-right-pleat-shadow','M 582 1408 C 560 1426 549 1431 531 1438 L 540 1472 L 524 1500 L 544 1524 L 531 1555 L 552 1582 L 540 1612 L 568 1637 L 563 1676 L 603 1700 C 606 1588 600 1496 582 1408 Z','url(#full-cloth-fold)')
path(body,'maid-right-pleats','M 578 1402 C 559 1418 545 1425 528 1430 L 540 1464 L 523 1490 L 544 1518 L 533 1548 L 552 1574 L 542 1605 L 568 1630 L 563 1662 L 599 1691 C 600 1574 596 1484 578 1402 Z','#faf7f9')
path(body,'maid-center-placket','M 410 1470 C 415 1570 416 1681 411 1794 L 461 1794 C 468 1671 463 1568 452 1467 Z','#eeebf0')

# A's short white neck ruff is grounded in fabric; no necklace/jewel added.
path(body,'maid-collar-shadow','M 324 1370 C 384 1408 498 1415 562 1375 L 579 1421 C 499 1463 400 1459 315 1415 Z','url(#full-cloth-fold)')
path(body,'maid-collar-left','M 319 1364 L 338 1372 L 351 1369 L 365 1381 L 381 1379 L 395 1390 L 421 1390 L 429 1431 C 386 1430 349 1418 315 1402 Z','#fcf9fa')
path(body,'maid-collar-right','M 441 1392 L 465 1392 L 479 1384 L 494 1387 L 510 1378 L 525 1382 L 543 1369 L 561 1372 L 575 1405 C 533 1428 488 1440 444 1434 Z','url(#full-cloth-field)')
path(body,'maid-bow-left-tail','M 407 1436 C 392 1475 370 1510 347 1526 L 382 1533 L 397 1554 C 428 1512 439 1476 437 1440 Z','url(#full-bow-field)')
path(body,'maid-bow-right-tail','M 443 1438 C 465 1475 486 1508 514 1523 L 485 1536 L 472 1553 C 443 1515 428 1478 425 1444 Z','#273652')
path(body,'maid-bow-left','M 427 1431 C 397 1402 356 1387 335 1394 C 320 1403 326 1444 335 1465 C 351 1484 394 1460 427 1449 Z','url(#full-bow-field)')
path(body,'maid-bow-right','M 442 1432 C 472 1404 518 1395 538 1407 C 546 1425 535 1458 525 1472 C 504 1481 471 1460 441 1450 Z','url(#full-bow-field)')
path(body,'maid-bow-left-fold','M 337 1401 C 369 1400 400 1416 421 1434 C 393 1420 367 1411 337 1410 Z','#3e4c6e')
path(body,'maid-bow-right-fold','M 447 1438 C 479 1422 506 1414 532 1415 C 506 1424 477 1438 449 1447 Z','#354565')
path(body,'maid-bow-knot','M 421 1424 C 432 1420 441 1423 449 1431 L 447 1453 C 439 1461 429 1459 421 1453 Z','#293750')

stage.append(head)
# Complete the unseen lower jaw; source-visible face/hair/eyes stay as observed.
for name in ['face-parent','face-continuous-illumination']:
    e=next(q for q in head if q.get('id')==name);d=e.get('d');assert 'L -20 1289 Z' in d
    e.set('d',d.replace('L -20 1289 Z','C 653 1370 538 1422 396 1399 C 219 1390 70 1321 -20 1238 Z'))
# Original back-hair paths end at the source canvas. Their hidden lower crop
# edges are completed in full with smooth continuation instead of a flat ledge.
rear=next(e for e in head if e.get('id')=='rear-hair');d=rear.get('d')
d=d.replace('L730.000 1300.000','C1236.000 1435.000 1239.000 1570.000 1268.000 1656.000 C1157.000 1669.000 1068.000 1587.000 1036.000 1519.000 L730.000 1300.000')
rear.set('d',d)
for name in ['rear-lower-flow','rear-lower-cut']:
    e=next(q for q in head if q.get('id')==name);head.remove(e)

dest=ROOT/'full-revisions/r001';dest.mkdir(parents=True,exist_ok=True)
svg=ET.tostring(tree,encoding='unicode');validate_svg(svg);(dest/'full.svg').write_text(svg,encoding='utf-8')
for size in [1280,128,48,24]:(dest/f'full-{size}.png').write_bytes(render_svg_text(svg,size))
shutil.copy2(ROOT/'full-draw.py',dest/'sourcecode.py');shutil.copy2(ROOT/'full.prompt.zh-CN.md',dest/'actualprompt.md')
board=Image.new('RGB',(960,410));dr=ImageDraw.Draw(board)
for i,bg in enumerate(['#f6f4ee','#0f0f0f','#bcbcc5']):
    dr.rectangle((i*320,0,i*320+319,409),fill=bg)
    for yy,s in [(32,128),(220,48),(320,24)]:
        im=Image.open(dest/f'full-{s}.png').convert('RGBA');board.paste(im,(i*320+36,yy),im);dr.text((i*320+180,yy+4),f'{s}px',fill='#888888')
board.save(dest/'inspection-board.png')
report={'revision':'r001','svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'head_base_sha256':hashlib.sha256(base.encode()).hexdigest(),'outfit_source':'candidate-a-maid.jpg, user-selected alternative attire, not official r1 evidence','new_inferences':['unseen jaw','neck pose','lower back hair continuation','selected clothing adapted to tilted upper-body projection'],'short_unchanged':True,'user_acceptance':'unassessed','backend':backend_info()}
(dest/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report));t.cancel()
