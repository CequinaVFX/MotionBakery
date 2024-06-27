__title__ = 'MotionBakery'
__author__ = 'Luciano Cequinel'
__contact__ = 'lucianocequinel@gmail.com'
__version__ = '1.0.0'
__release_date__ = 'June, 24 2024'
__license__ = 'MIT'

import math

import nuke
import random
import nukescripts
import nuke.rotopaint as rp
from MotionBakery_settings import standard_roto_node


def generate_color():
    red = random.random()
    green = random.random()
    blue = random.random()
    return int('{:02x}{:02x}{:02x}ff'.format(int(red * 255), int(green * 255), int(blue * 255)), 16)


def getTrackerNames(node) :
    n = node["tracks"].toScript()
    rows = n.split("\n")[34 :]

    trackers = []

    for i in rows :
        try:
            trkName = i.split("}")[1].split("{")[0][2 :-2]
            if trkName != "" :
                trackers.append(trkName)
        except:
            continue

    return trackers


def customize_node(node_class, reference_frame, tracker_node):
    x = tracker_node.xpos()
    y = tracker_node.ypos()
    w = tracker_node.screenWidth()
    m = int(x + w / 2)

    tranform_class = False
    roto_class = False

    if node_class == 'Transform':
        new_node = nuke.nodes.Transform()
        tranform_class = True

    elif node_class == 'Roto':
        new_node = nuke.nodes.Roto()
        roto_class = True

    elif node_class == 'RotoPaint':
        new_node = nuke.nodes.RotoPaint()
        new_node.resetKnobsToDefault()
        roto_class = True

    elif node_class == 'CornerPin':
        new_node = nuke.nodes.CornerPin2D()
        new_node.resetKnobsToDefault()
        tranform_class = True

    if tranform_class:
        new_node['filter'].setValue(tracker_node['filter'].enumName(int(tracker_node['filter'].getValue())))
        new_node['motionblur'].setValue(tracker_node['motionblur'].getValue())
        new_node['shutter'].setValue(tracker_node['shutter'].getValue())
        new_node['shutteroffset'].setValue(
            tracker_node['shutteroffset'].enumName(int(tracker_node['shutteroffset'].getValue())))

    if roto_class:
        new_node['motionblur'].setValue(tracker_node['motionblur'].getValue())
        new_node['motionblur_shutter'].setValue(tracker_node['shutter'].getValue())
        new_node['motionblur_shutter_offset_type'].setValue(
            tracker_node['shutteroffset'].enumName(int(tracker_node['shutteroffset'].getValue())))

        curve = new_node['curves']
        root = curve.rootLayer
        newLayer = rp.Layer(curve)
        newLayer.name = tracker_node.name()
        root.append(newLayer)
        curve.changed()
        layer = curve.toElement(tracker_node.name())

    new_node.setXYpos(int(m + w), int(y + w / 2))
    nuke.autoplace(new_node)

    new_node.addKnob(nuke.Tab_Knob('tracker_knob', 'Tracker settings'))

    new_node.addKnob(nuke.Int_Knob('tr_reference_frame', 'reference frame'))
    new_node['tr_reference_frame'].setValue(reference_frame)
    new_node['label'].setValue('reference frame: {}'.format(str('[value tr_reference_frame]')))

    set_reference = nuke.PyScript_Knob('set_reference', 'set to current frame',
                                       'nuke.thisNode()["tr_reference_frame"].setValue(nuke.frame())')
    new_node.addKnob(set_reference)

    cmd = ("nuke.zoom(2, [{0}, {1}]) "
           "if nuke.toNode('{2}') "
           "else nuke.message('{2} not found!')").format(x, y,
                                                         tracker_node.name())

    goto_parent = nuke.PyScript_Knob('goto_parent', 'go to parent Tracker', cmd)
    new_node.addKnob(goto_parent)

    return new_node


def fourCornersOfAConvexPoly(tracker_node, ref_frame):
    k = tracker_node['selected_tracks']
    tracks = tracker_node['tracks']
    sa = k.getText().split(',')

    if len(sa) != 4:
        idx = []
        return idx

    i = [int(sa[0]), int(sa[1]), int(sa[2]), int(sa[3])]

    nCols = 31
    xCol = 2
    yCol = 3

    x = [tracks.getValueAt(ref_frame, i[0] * nCols + xCol),
         tracks.getValueAt(ref_frame, i[1] * nCols + xCol),
         tracks.getValueAt(ref_frame, i[2] * nCols + xCol),
         tracks.getValueAt(ref_frame, i[3] * nCols + xCol)]

    y = [tracks.getValueAt(ref_frame, i[0] * nCols + yCol),
         tracks.getValueAt(ref_frame, i[1] * nCols + yCol),
         tracks.getValueAt(ref_frame, i[2] * nCols + yCol),
         tracks.getValueAt(ref_frame, i[3] * nCols + yCol)]

    import math
    mx = sum(x) / 4
    my = sum(y) / 4

    x = [x[0] - mx, x[1] - mx, x[2] - mx, x[3] - mx]
    y = [y[0] - my, y[1] - my, y[2] - my, y[3] - my]

    a = [math.pi + math.atan2(y[0], x[0]), math.pi + math.atan2(y[1], x[1]),
         math.pi + math.atan2(y[2], x[2]), math.pi + math.atan2(y[3], x[3])]

    idx = sorted(range(len(i)), key=a.__getitem__)
    idx = [i[idx[0]], i[idx[1]], i[idx[2]], i[idx[3]]]

    return idx


def copy_animation_to_rotopaint_layer(source_node, target_node):
    center_x_anim = source_node['center'].animation(0)
    center_y_anim = source_node['center'].animation(1)
    translate_x_anim = source_node['translate'].animation(0)
    translate_y_anim = source_node['translate'].animation(1)
    rotate_anim = source_node['rotate'].animation(0)
    scale_x_anim = source_node['scale'].animation(0)
    scale_y_anim = source_node['scale'].animation(1)

    new_layer = target_node['curves'].rootLayer[0]

    transform = new_layer.getTransform()
    translate_x_curve = transform.getTranslationAnimCurve(0)
    translate_y_curve = transform.getTranslationAnimCurve(1)
    rotate_curve = transform.getRotationAnimCurve(2)
    scale_x_curve = transform.getScaleAnimCurve(0)
    scale_y_curve = transform.getScaleAnimCurve(1)
    center_x_curve = transform.getPivotPointAnimCurve(0)
    center_y_curve = transform.getPivotPointAnimCurve(1)

    for key in translate_x_anim.keys():
        cx = center_x_anim.evaluate(key.x) if center_x_anim else 0
        cy = center_y_anim.evaluate(key.x) if center_y_anim else 0
        tx = translate_x_anim.evaluate(key.x) if translate_x_anim else 0
        ty = translate_y_anim.evaluate(key.x) if translate_y_anim else 0
        rot = rotate_anim.evaluate(key.x) if rotate_anim else 0
        sx = scale_x_anim.evaluate(key.x) if scale_x_anim else 1
        sy = scale_y_anim.evaluate(key.x) if scale_y_anim else 1

        translate_x_curve.addKey(key.x, tx)
        translate_y_curve.addKey(key.x, ty)
        rotate_curve.addKey(key.x, rot)
        scale_x_curve.addKey(key.x, sx)
        scale_y_curve.addKey(key.x, sy)
        center_x_curve.addKey(key.x, cx)
        center_y_curve.addKey(key.x, cy)


def copy_animation_to_rotopaint_layer_bkp(source_node, target_node):
    translate_x_anim = source_node['translate'].animation(0)
    translate_y_anim = source_node['translate'].animation(1)
    rotate_anim = source_node['rotate'].animation(0)
    scale_x_anim = source_node['scale'].animation(0)
    scale_y_anim = source_node['scale'].animation(1)
    center_x_anim = source_node['center'].animation(0)
    center_y_anim = source_node['center'].animation(1)

    layer = target_node['curves'].rootLayer[0]

    transform = layer.getTransform()
    translate_x = transform.getTranslationAnimCurve(0)
    translate_y = transform.getTranslationAnimCurve(1)
    rotate = transform.getRotationAnimCurve(2)
    scale_x = transform.getScaleAnimCurve(0)
    # scale_y = transform.getScaleAnimCurve(1)
    center_x = transform.getPivotPointAnimCurve(0)
    center_y = transform.getPivotPointAnimCurve(1)

    if translate_x_anim:
        for key in translate_x_anim.keys():
            translate_x.addKey(key.x, key.y)

    if translate_y_anim:
        for key in translate_y_anim.keys():
            translate_y.addKey(key.x, key.y)

    if rotate_anim:
        for key in rotate_anim.keys():
            print(key.x, key.y)
            rotate.addKey(key.x, key.y)

    if scale_x_anim:
        for key in scale_x_anim.keys():
            scale_x.addKey(key.x, key.y)

    # if scale_y_anim:
    #     for key in scale_y_anim.keys():
    #         scale_y.addKey(key.x, key.y)

    if center_x_anim:
        for key in center_x_anim.keys():
            center_x.addKey(key.x, key.y)

    if center_y_anim:
        for key in center_y_anim.keys():
            center_y.addKey(key.x, key.y)


def copy_animation_to_roto_layer_matrix(source_node, target_node):
    # Get the animation curves from the center, translate, rotate, and scale knobs
    center_x_anim = source_node['center'].animation(0)
    center_y_anim = source_node['center'].animation(1)
    translate_x_anim = source_node['translate'].animation(0)
    translate_y_anim = source_node['translate'].animation(1)
    rotate_anim = source_node['rotate'].animation(0)
    scale_x_anim = source_node['scale'].animation(0)
    scale_y_anim = source_node['scale'].animation(1)

    layer = target_node['curves'].rootLayer[0]
    # Ensure the target node is a Roto node
    # if not isinstance(target_node, nuke.nodes.Roto):
    #     nuke.message("Target node is not a Roto node.")
    #     return
    #
    # # Create a new layer in the Roto node
    # roto = target_node['curves']
    # new_layer = roto.createLayer(layer_name)

    # Apply the animation curves to the layer's transform matrix
    transform = layer.getTransform()
    matrix_curve = transform.getExtraMatrixAnimCurve()

    # Clear any existing animation on the layer's transform matrix
    matrix_curve.clear()

    # Copy the animation keyframes
    for key in translate_x_anim.keys():
        time = key.x
        cx = center_x_anim.evaluate(time) if center_x_anim else 0
        cy = center_y_anim.evaluate(time) if center_y_anim else 0
        tx = translate_x_anim.evaluate(time) if translate_x_anim else 0
        ty = translate_y_anim.evaluate(time) if translate_y_anim else 0
        rot = rotate_anim.evaluate(time) if rotate_anim else 0
        sx = scale_x_anim.evaluate(time) if scale_x_anim else 1
        sy = scale_y_anim.evaluate(time) if scale_y_anim else 1

        # Compute the transformation matrix
        radians = math.radians(rot)
        cos_r = math.cos(radians)
        sin_r = math.sin(radians)

        # Create the transformation matrix
        matrix = nuke.math.Matrix4()
        matrix.makeIdentity()
        matrix.translate(cx, cy, 0)
        matrix.scale(sx, sy, 1)
        matrix.rotateZ(radians)
        matrix.translate(tx, ty, 0)
        matrix.translate(-cx, -cy, 0)

        # Add the keyframe to the matrix curve
        matrix_curve.addKey(time, matrix)


def copyKnobValuesAtKeys(src, dst, chan):
    if src.isAnimated():
        dst.setAnimated(chan)
        for Idx in range(src.getNumKeys(chan)):
            t = src.getKeyTime(Idx, chan)
            dst.setValueAt(src.getValueAt(t, chan), t, chan)

    else:
        dst.setValue(src.getValue(chan), chan)


def copy_animation_to_transform(tracker, custom_node, stabilize=False):
    # if isinstance(tracker['scale'].value(), float):
    #     print('single value')
    # else:
    #     print('separated values')

    for knob in ('translate', 'rotate', 'scale', 'center'):
        if knob == 'rotate':
            copyKnobValuesAtKeys(tracker[knob], custom_node[knob], 0)
        else:
            copyKnobValuesAtKeys(tracker[knob], custom_node[knob], 0)
            copyKnobValuesAtKeys(tracker[knob], custom_node[knob], 1)

    srcTransformKnob = tracker['transform']
    srcTransformName = srcTransformKnob.enumName(int(srcTransformKnob.getValue()))

    srcTransformIsStabilize = (srcTransformName.find('stabilize') == 0)
    invertDueToDestStabilize = (stabilize and not srcTransformIsStabilize)
    invertDueToSrcStabilize = ((not stabilize) and srcTransformIsStabilize)
    needToInvert = (invertDueToDestStabilize or invertDueToSrcStabilize)

    if needToInvert:
        transKnob = custom_node['translate']
        rotateKnob = custom_node['rotate']
        scaleKnob = custom_node['scale']
        centerKnob = custom_node['center']
        for chan in range(2):
            for Idx in range(centerKnob.getNumKeys(chan)):
                t = centerKnob.getKeyTime(Idx, chan)
                centerKnob.setValueAt(centerKnob.getValueAt(t, chan) + transKnob.getValueAt(t, chan), t, chan)
            for Idx in range(scaleKnob.getNumKeys(chan)):
                t = scaleKnob.getKeyTime(Idx, chan)
                scaleKnob.setValueAt(1 / scaleKnob.getValueAt(t, chan), t, chan)
            for Idx in range(transKnob.getNumKeys(chan)):
                t = transKnob.getKeyTime(Idx, chan)
                transKnob.setValueAt(-transKnob.getValueAt(t, chan), t, chan)
        for Idx in range(rotateKnob.getNumKeys(0)):
            t = rotateKnob.getKeyTime(Idx, 0)
            rotateKnob.setValueAt(-rotateKnob.getValueAt(t, 0), t, 0)

    custom_node['translate'].setExpression('curve - curve(tr_reference_frame)')
    custom_node['rotate'].setExpression('curve - curve(tr_reference_frame)')
    custom_node['scale'].setExpression('curve - curve(tr_reference_frame) + 1')


def bakery(tracker, mode='matchmove'):
    if not getTrackerNames(tracker):
        print('No trackers on this Tracker!')
        return

    tracker_name = tracker.name()
    tracker_reference_frame = int(tracker['reference_frame'].value())

    stabilize = True if mode == 'stabilize' else False

    color = generate_color()
    if 'color_group' in tracker.knobs():
        color = int(tracker['color_group'].value())
    else:
        tracker.addKnob(nuke.Tab_Knob('tracker_knob', 'Tracker Group'))
        tracker.addKnob(nuke.String_Knob('color_group', 'colour group', str(color)))

        tracker['color_group'].setEnabled(False)
        tracker['tile_color'].setValue(color)

    if mode == 'matchmove' or mode == 'stabilize':
        proposedName = '{}_{}_'.format(tracker_name, 'stabilize' if stabilize else 'matchmove')

        custom_node = customize_node(node_class='Transform',
                                     reference_frame=int(tracker['reference_frame'].value()),
                                     tracker_node=tracker)

        custom_node.setName(proposedName, uncollide=True)
        custom_node['tile_color'].setValue(color)

        copy_animation_to_transform(tracker, custom_node, stabilize)

    elif mode == 'roto':
        proposedName = '{}_from_{}_'.format(standard_roto_node, tracker_name)

        custom_roto = customize_node(node_class=standard_roto_node,
                                     reference_frame=tracker_reference_frame,
                                     tracker_node=tracker)

        custom_roto.setName(proposedName, uncollide=True)
        custom_roto['tile_color'].setValue(color)

        copy_animation_to_rotopaint_layer(tracker, custom_roto)

    else:
        idx = fourCornersOfAConvexPoly(tracker, tracker_reference_frame)

        if len(idx) != 4:
            nuke.critical('CornerPin2D export needs exactly 4 tracks selected.')

        else:
            proposedName = 'MM_CPin_from_{}_'.format(tracker_name)

            # pin = nuke.nodes.CornerPin2D()
            pin = customize_node(node_class='CornerPin',
                                 reference_frame=tracker_reference_frame,
                                 tracker_node=tracker)

            pin.setName(proposedName, uncollide=True)
            pin['tile_color'].setValue(color)

            toKnobs = ["to1", "to2", "to3", "to4"]
            fromKnobs = ["from1", "from2", "from3", "from4"]

            for i in range(len(idx)):
                k = tracker['tracks']

                xIdx = idx[i] * 31 + 2
                yIdx = idx[i] * 31 + 3

                p = pin[toKnobs[i]]
                p.setAnimated(0)
                p.setAnimated(1)

                for Idx in range(k.getNumKeys(xIdx)):
                    t = k.getKeyTime(Idx, xIdx)
                    p.setValueAt(k.getValueAt(t, xIdx), t, 0)

                for Idx in range(k.getNumKeys(yIdx)):
                    t = k.getKeyTime(Idx, yIdx)
                    p.setValueAt(k.getValueAt(t, yIdx), t, 1)

                p = pin[fromKnobs[i]]
                p.setValue(k.getValueAt(tracker_reference_frame, xIdx), 0)
                p.setValue(k.getValueAt(tracker_reference_frame, yIdx), 1)

            pin['from1'].setExpression('to1(tr_reference_frame)')
            pin['from2'].setExpression('to2(tr_reference_frame)')
            pin['from3'].setExpression('to3(tr_reference_frame)')
            pin['from4'].setExpression('to4(tr_reference_frame)')


def bake_it(mode='matchmove'):
    node = nuke.selectedNodes()
    if len(node) == 1:
        tracker = nuke.selectedNode()
        if tracker.Class() == 'Tracker4':
            bakery(tracker, mode=mode)
        else:
            print('Select a Tracker Node!')

    else:
        if len(node) > 1:
            print('Select only one node!')
        else:
            print('Select a Tracker node!')


# bake_it(mode='matchmove', bake_roto=True)