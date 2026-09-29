"""Portable standard-library SVG paint field exporter; no image/runtime fitting."""
from xml.sax.saxutils import escape


def rgb(values):
    if len(values) != 3 or not all(0 <= v <= 255 for v in values):
        raise ValueError('bounded three-channel sRGB required')
    return 'rgb(' + ','.join(f'{v/255*100:.7f}%' for v in values) + ')'


def paint(field, identifier):
    """Return (defs, base fill, overlay attrs) for one semantic surface.

    Overlay attrs must paint the same path, inside a shared surface clip whose
    opacity/coverage is sampled ONCE. Do not stack antialiased path edges.
    """
    if field['kind'] == 'layered':
        definition, fill, nested = paint(field['base'], identifier + '-base')
        if nested or len(field['glazes']) > 2:
            raise ValueError('only one base and at most two simple glazes')
        attrs = []
        for i, glaze in enumerate(field['glazes']):
            # Vary coverage in a white alpha mask, then composite a constant
            # opaque pigment. This avoids low-alpha premultiplied RGB stop
            # quantization changing the pigment's hue during interpolation.
            import copy
            coverage = copy.deepcopy(glaze)
            for stop in coverage['stops']:
                stop['rgb'] = [255.,255.,255.]
            defs, alpha_fill, nested = paint(coverage, identifier + f'-glaze-{i}')
            if nested:
                raise ValueError('nested layer is not permitted')
            definition += defs
            mask_id = identifier + f'-glaze-mask-{i}'
            definition += f'<mask id="{mask_id}" maskUnits="userSpaceOnUse" x="-1" y="-1" width="1282" height="1282" mask-type="alpha"><rect x="-1" y="-1" width="1282" height="1282" fill="{alpha_fill}"/></mask>'
            attrs.append({'fill': rgb(glaze['stops'][0]['rgb']), 'mask':f'url(#{mask_id})'})
        return definition, fill, attrs
    if field['kind'] == 'solid':
        return '', rgb(field['rgb']), []
    stops = field['stops']
    if not 2 <= len(stops) <= 5:
        raise ValueError('two to five stops required')
    tags = ''.join(f'<stop offset="{s["offset"]:.7f}" stop-color="{rgb(s["rgb"])}" stop-opacity="{s.get("opacity",1):.7f}"/>' for s in stops)
    common = f'id="{escape(identifier)}" gradientUnits="userSpaceOnUse" color-interpolation="sRGB"'
    if field['kind'] == 'linear':
        a,b = field['from'],field['to']
        definition = f'<linearGradient {common} x1="{a[0]:.7f}" y1="{a[1]:.7f}" x2="{b[0]:.7f}" y2="{b[1]:.7f}">{tags}</linearGradient>'
    elif field['kind'] == 'radial':
        cx,cy = field['center']; rx,ry = field['radii']
        if min(rx,ry) <= 0:
            raise ValueError('positive radii required')
        definition = f'<radialGradient {common} cx="0" cy="0" r="1" gradientTransform="translate({cx:.7f} {cy:.7f}) scale({rx:.7f} {ry:.7f})">{tags}</radialGradient>'
    else:
        raise ValueError('unsupported field')
    return definition, f'url(#{identifier})', []


def surface(region, field, identifier):
    """Return (defs, path/group), preserving a single surface edge coverage."""
    definition, fill, overlays = paint(field, identifier)
    d = escape(region['d']); rule = region.get('fill_rule','evenodd')
    if not overlays:
        return definition, f'<path id="{region["id"]}" d="{d}" fill-rule="{rule}" fill="{fill}"/>'
    clip = identifier + '-surface-clip'
    definition += f'<clipPath id="{clip}"><path d="{d}" clip-rule="{rule}"/></clipPath>'
    # The rectangle is local material support, not a canvas/background shape:
    # shared clip makes the emitted geometry exactly the semantic path.
    layers = [f'<rect x="-1" y="-1" width="1282" height="1282" fill="{fill}"/>']
    layers += [f'<rect x="-1" y="-1" width="1282" height="1282" fill="{a["fill"]}" mask="{a["mask"]}"/>' for a in overlays]
    return definition, f'<g id="{region["id"]}" clip-path="url(#{clip})">' + ''.join(layers) + '</g>'
