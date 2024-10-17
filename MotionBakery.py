__title__ = 'MotionBakery'
__author__ = 'Luciano Cequinel'
__contact__ = 'lucianocequinel@gmail.com'
__version__ = '1.1.0'
__release_date__ = 'October, 18 2024'
__license__ = 'MIT'

import math
import random

import nuke
import nukescripts
import nuke.rotopaint as rp
import _curvelib as cl
# import nuke.rotopaint._curvelib as cl


from MotionBakery_settings import STANDARD_ROTO_NODE, COLOR_RANGE


def generate_color():
    red = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
    green = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
    blue = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
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
    x_position = tracker_node.xpos()
    y_position = tracker_node.ypos()
    dag_width = tracker_node.screenWidth()
    dag_center_point = int(x_position + dag_width / 2)

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

        # curve = new_node['curves']
        # root = curve.rootLayer
        # newLayer = rp.Layer(curve)
        # newLayer.name = tracker_node.name()
        # root.append(newLayer)
        # curve.changed()
        # layer = curve.toElement(tracker_node.name())

    new_node.setXYpos(int(dag_center_point + dag_width), int(y_position + dag_width / 2))
    nuke.autoplace(new_node)

    # Add Tab group
    new_node.addKnob(nuke.Tab_Knob('tracker_knob', 'Tracker settings'))

    # Add Reference Frame knob
    new_node.addKnob(nuke.Int_Knob('tr_reference_frame', 'reference frame'))
    new_node['tr_reference_frame'].setValue(reference_frame)
    new_node['label'].setValue('reference frame: {}'.format(str('[value tr_reference_frame]')))

    # Add Set Reference Frame button
    new_node.addKnob(nuke.PyScript_Knob('set_reference',
                                        'set to current frame',
                                        'nuke.thisNode()["tr_reference_frame"].setValue(nuke.frame())'))

    # Add Parent Name label
    parent_label = nuke.Text_Knob('parent', ' ', tracker_node.name())
    parent_label.setFlag(nuke.STARTLINE)
    new_node.addKnob(parent_label)

    cmd = ("nuke.zoom(2, [{0}, {1}]) "
           "if nuke.toNode('{2}') "
           "else nuke.message('{2} not found!')").format(x_position, y_position,
                                                         tracker_node.name())

    # Add Go to parent button
    new_node.addKnob(nuke.PyScript_Knob('goto_parent',
                                        'go to parent Tracker',
                                        cmd))

    return new_node


def fourCornersOfAConvexPoly(tracker_node, ref_frame):
    selected_tracks = tracker_node['selected_tracks']
    all_tracks = tracker_node['tracks']
    sa = selected_tracks.getText().split(',')

    if len(sa) != 4:
        idx = []
        return idx

    i = [int(sa[0]), int(sa[1]), int(sa[2]), int(sa[3])]

    nCols = 31
    xCol = 2
    yCol = 3

    x = [all_tracks.getValueAt(ref_frame, i[0] * nCols + xCol),
         all_tracks.getValueAt(ref_frame, i[1] * nCols + xCol),
         all_tracks.getValueAt(ref_frame, i[2] * nCols + xCol),
         all_tracks.getValueAt(ref_frame, i[3] * nCols + xCol)]

    y = [all_tracks.getValueAt(ref_frame, i[0] * nCols + yCol),
         all_tracks.getValueAt(ref_frame, i[1] * nCols + yCol),
         all_tracks.getValueAt(ref_frame, i[2] * nCols + yCol),
         all_tracks.getValueAt(ref_frame, i[3] * nCols + yCol)]

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


def copy_animation_to_rotopaint_layer(tracker_node, roto_node):
    # Create a new Layer inside of the RotoPaint
    # curve = roto_node['curves']
    # root = curve.rootLayer
    # newLayer = rp.Layer(curve)
    # newLayer.name = tracker_node.name()
    # root.append(newLayer)
    # curve.changed()
    # layer = curve.toElement(tracker_node.name())

    # if isinstance(tracker_node['scale'].value(), list):
    #     print("The knob is an array class.")
    # else:
    #     print("The knob is NOT ARRAY CLASS.")

    # Create linked layer in Roto Node
    curves_knob = roto_node["curves"]
    tracked_layer = rp.Layer(curves_knob)
    tracked_layer.name = tracker_node.name()
    root = curves_knob.rootLayer
    root.append(tracked_layer)

    center_x_anim = tracker_node['center'].animation(0)
    center_y_anim = tracker_node['center'].animation(1)
    translate_x_anim = tracker_node['translate'].animation(0)
    translate_y_anim = tracker_node['translate'].animation(1)
    rotate_anim = tracker_node['rotate'].animation(0)
    scale_x_anim = tracker_node['scale'].animation(0)
    # scale_y_anim = tracker_node['scale'].animation(1)

    tracked_layer = roto_node['curves'].rootLayer[0]

    transform = tracked_layer.getTransform()

    translate_x_curve = transform.getTranslationAnimCurve(0)
    translate_y_curve = transform.getTranslationAnimCurve(1)

    rotate_curve = transform.getRotationAnimCurve(2)

    scale_x_curve = transform.getScaleAnimCurve(0)
    # scale_y_curve = transform.getScaleAnimCurve(1)

    center_x_curve = transform.getPivotPointAnimCurve(0)
    center_y_curve = transform.getPivotPointAnimCurve(1)

    for key in translate_x_anim.keys():
        tx = translate_x_anim.evaluate(key.x) if translate_x_anim else 0
        ty = translate_y_anim.evaluate(key.x) if translate_y_anim else 0

        rot = rotate_anim.evaluate(key.x) if rotate_anim else 0

        sx = scale_x_anim.evaluate(key.x) if scale_x_anim else 1
        # sy = scale_y_anim.evaluate(key.x) if scale_y_anim else 1

        cx = center_x_anim.evaluate(key.x) if center_x_anim else 0
        cy = center_y_anim.evaluate(key.x) if center_y_anim else 0

        translate_x_curve.addKey(key.x, tx)
        translate_y_curve.addKey(key.x, ty)

        rotate_curve.addKey(key.x, rot)

        scale_x_curve.addKey(key.x, sx)
        # scale_y_curve.addKey(key.x, sy)

        center_x_curve.addKey(key.x, cx)
        center_y_curve.addKey(key.x, cy)

        trans_curve_x = cl.AnimCurve()
        print(trans_curve_x)
        trans_curve_y = cl.AnimCurve()
        print(trans_curve_y)

        """        
        # Set expression
        trans_curve_x = cl.AnimCurve()
        trans_curve_y = cl.AnimCurve()

        # ('curve - curve(tr_reference_frame)')
        trans_curve_x.expressionString = "curve - curve(tr_reference_frame)"
        trans_curve_y.expressionString = "curve - curve(tr_reference_frame)"
        trans_curve_x.useExpression = True
        trans_curve_y.useExpression = True

        rot_curve = cl.AnimCurve()
        rot_curve.expressionString = "curve - curve(tr_reference_frame)"
        rot_curve.useExpression = True

        scale_curve = cl.AnimCurve()
        scale_curve.expressionString = "curve - curve(tr_reference_frame)"
        scale_curve.useExpression = True

        center_curve_x = cl.AnimCurve()
        center_curve_y = cl.AnimCurve()
        center_curve_x.expressionString = "curve - curve(tr_reference_frame)"
        center_curve_y.expressionString = "curve - curve(tr_reference_frame)"
        center_curve_x.useExpression = True
        center_curve_y.useExpression = True

        # Define variable for accessing the getTransform()
        transform_attr = tracked_layer.getTransform()
        # Set the Animation Curve for the Translation attribute to the value of the previously defined curve, for both x and y
        transform_attr.setTranslationAnimCurve(0, trans_curve_x)
        transform_attr.setTranslationAnimCurve(1, trans_curve_y)

        # Index value of setRotationAnimCurve is 2 even though there is only 1 parameter...
        # http://www.mail-archive.com/nuke-python@support.thefoundry.co.uk/msg02295.html
        transform_attr.setRotationAnimCurve(2, rot_curve)

        transform_attr.setScaleAnimCurve(0, scale_curve)
        # transform_attr.setScaleAnimCurve(1, scale_curve)

        transform_attr.setPivotPointAnimCurve(0, center_curve_x)
        transform_attr.setPivotPointAnimCurve(1, center_curve_y)
        """

    curves_knob.rootLayer.append(tracked_layer)


def copy_animation_to_rotopaint_layer_BKP(tracker_node, roto_node):
    center_x_anim = tracker_node['center'].animation(0)
    center_y_anim = tracker_node['center'].animation(1)
    translate_x_anim = tracker_node['translate'].animation(0)
    translate_y_anim = tracker_node['translate'].animation(1)
    rotate_anim = tracker_node['rotate'].animation(0)
    scale_x_anim = tracker_node['scale'].animation(0)
    scale_y_anim = tracker_node['scale'].animation(1)

    stab_layer = roto_node['curves'].rootLayer[0]

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


def copy_animation_to_roto_layer_matrix(tracker_node, roto_node):
    # Get the animation curves from the center, translate, rotate, and scale knobs
    center_x_anim = tracker_node['center'].animation(0)
    center_y_anim = tracker_node['center'].animation(1)
    translate_x_anim = tracker_node['translate'].animation(0)
    translate_y_anim = tracker_node['translate'].animation(1)
    rotate_anim = tracker_node['rotate'].animation(0)
    scale_x_anim = tracker_node['scale'].animation(0)
    scale_y_anim = tracker_node['scale'].animation(1)

    layer = roto_node['curves'].rootLayer[0]
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


def copy_animation_to_transform(tracker_node, custom_node, stabilize=False):
    # if isinstance(tracker['scale'].value(), float):
    #     print('single value')
    # else:
    #     print('separated values')

    for knob in ('translate', 'rotate', 'scale', 'center'):
        if knob == 'rotate':
            copyKnobValuesAtKeys(tracker_node[knob], custom_node[knob], 0)
        else:
            copyKnobValuesAtKeys(tracker_node[knob], custom_node[knob], 0)
            copyKnobValuesAtKeys(tracker_node[knob], custom_node[knob], 1)

    srcTransformKnob = tracker_node['transform']
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

    tracker_name = tracker.name()
    tracker_reference_frame = int(tracker['reference_frame'].value())

    stabilize = True if mode == 'stabilize' else False

    color = generate_color()

    if tracker.knobs().get('color_group'):
        color = int(tracker['color_group'].value())

    else:
        tracker.addKnob(nuke.Tab_Knob('tracker_knob', 'Tracker Group'))
        tracker.addKnob(nuke.String_Knob('color_group', 'color group', str(color)))

        tracker['color_group'].setEnabled(False)
        tracker['tile_color'].setValue(color)

    if tracker['label'].value() == '':
        tracker['label'].setValue('Operation: [value transform]\n'
                                  'Reference frame: [value reference frame]')

    proposed_name = '{}_{}_'.format(tracker_name, 'stabilize' if stabilize else 'matchmove')
    if any([mode == 'matchmove', mode == 'stabilize']):
        custom_node = customize_node(node_class='Transform',
                                     reference_frame=int(tracker['reference_frame'].value()),
                                     tracker_node=tracker)

        custom_node.setName(proposed_name, uncollide=True)
        custom_node['tile_color'].setValue(color)

        copy_animation_to_transform(tracker, custom_node, stabilize)

    elif mode == 'roto':
        proposed_name = '{}_from_{}_'.format(STANDARD_ROTO_NODE, tracker_name)

        custom_roto = customize_node(node_class=STANDARD_ROTO_NODE,
                                     reference_frame=tracker_reference_frame,
                                     tracker_node=tracker)

        custom_roto.setName(proposed_name, uncollide=True)
        custom_roto['tile_color'].setValue(color)

        copy_animation_to_rotopaint_layer(tracker, custom_roto)

    else:
        tracks_index = fourCornersOfAConvexPoly(tracker, tracker_reference_frame)

        if len(tracks_index) != 4:
            nuke.critical('CornerPin2D export needs exactly 4 tracks selected.')
            return
        else:
            proposed_name = '{}_CPin_matchmove'.format(tracker_name)

            pin = customize_node(node_class='CornerPin',
                                 reference_frame=tracker_reference_frame,
                                 tracker_node=tracker)

            pin.setName(proposed_name, uncollide=True)
            pin['tile_color'].setValue(color)

            toKnobs = ["to1", "to2", "to3", "to4"]
            fromKnobs = ["from1", "from2", "from3", "from4"]

            for i in range(len(tracks_index)):
                k = tracker['tracks']

                track_x_index = tracks_index[i] * 31 + 2
                track_y_index = tracks_index[i] * 31 + 3

                p = pin[toKnobs[i]]
                p.setAnimated(0)
                p.setAnimated(1)

                for Idx in range(k.getNumKeys(track_x_index)):
                    t = k.getKeyTime(Idx, track_x_index)
                    p.setValueAt(k.getValueAt(t, track_x_index), t, 0)

                for Idx in range(k.getNumKeys(track_y_index)):
                    t = k.getKeyTime(Idx, track_y_index)
                    p.setValueAt(k.getValueAt(t, track_y_index), t, 1)

                p = pin[fromKnobs[i]]
                p.setValue(k.getValueAt(tracker_reference_frame, track_x_index), 0)
                p.setValue(k.getValueAt(tracker_reference_frame, track_y_index), 1)

            pin['from1'].setExpression('to1(tr_reference_frame)')
            pin['from2'].setExpression('to2(tr_reference_frame)')
            pin['from3'].setExpression('to3(tr_reference_frame)')
            pin['from4'].setExpression('to4(tr_reference_frame)')


def bake_selection(mode='matchmove'):
    node = nuke.selectedNodes()

    if len(node) == 1:
        tracker = nuke.selectedNode()
        if tracker.Class() == 'Tracker4':
            if not getTrackerNames(tracker):
                nuke.message('No trackers on this Tracker!')
                return

            tracker.setSelected(False)
            bakery(tracker, mode=mode)
        else:
            nuke.message('Select a Tracker Node!\nOnly Tracker4 allowed!')

    else:
        if len(node) > 1:
            nuke.message('Select only one node!')
        else:
            nuke.message('Select a Tracker node!')


if __name__ == '__main__':
    bake_selection(mode='matchmove')