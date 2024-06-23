__title__ = 'MotionBakery'
__author__ = 'Luciano Cequinel'
__contact__ = 'lucianocequinel@gmail.com'
__version__ = '1.0.0'
__release_date__ = 'June, 24 2024'
__license__ = 'MIT'


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

    create_layer = False
    if node_class == 'Transform':
        new_node = nuke.nodes.Transform()

        new_node['filter'].setValue(tracker_node['filter'].enumName(int(tracker_node['filter'].getValue())))
        new_node['motionblur'].setValue(tracker_node['motionblur'].getValue())
        new_node['shutter'].setValue(tracker_node['shutter'].getValue())
        new_node['shutteroffset'].setValue(
            tracker_node['shutteroffset'].enumName(int(tracker_node['shutteroffset'].getValue())))

    elif node_class == 'Roto':
        new_node = nuke.nodes.Roto()
        create_layer = True

    elif node_class == 'RotoPaint':
        new_node = nuke.nodes.RotoPaint()
        create_layer = True

    if create_layer:
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

    tab_group = nuke.Tab_Knob('tracker_knob', 'Tracker settings')
    new_node.addKnob(tab_group)

    ref_frame = nuke.Int_Knob('tr_reference_frame', 'reference frame')
    new_node.addKnob(ref_frame)
    new_node['tr_reference_frame'].setValue(reference_frame)
    new_node['label'].setValue('reference frame: {}'.format(str('[value tr_reference_frame]')))

    set_reference = nuke.PyScript_Knob('set_reference', 'set to current frame',
                                       'nuke.thisNode()["tr_reference_frame"].setValue(nuke.frame())')
    new_node.addKnob(set_reference)

    parent_command = 'nuke.zoom(2, [{}, {}])'.format(x, y)
    goto_parent = nuke.PyScript_Knob('goto_parent', 'go to parent Tracker', parent_command)
    new_node.addKnob(goto_parent)

    return new_node


def copy_animation_to_rotopaint_layer(source_node, target_node):
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
    rotate = transform.getRotationAnimCurve(0)
    scale_x = transform.getScaleAnimCurve(0)
    scale_y = transform.getScaleAnimCurve(1)
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
            rotate.addKey(key.x, key.y)

    if scale_x_anim:
        for key in scale_x_anim.keys():
            scale_x.addKey(key.x, key.y)

    if scale_y_anim:
        for key in scale_y_anim.keys():
            scale_y.addKey(key.x, key.y)

    if center_x_anim:
        for key in center_x_anim.keys():
            center_x.addKey(key.x, key.y)

    if center_y_anim:
        for key in center_y_anim.keys():
            center_y.addKey(key.x, key.y)


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

    if stabilize:
        custom_node['translate'].setExpression('curve - curve(tr_reference_frame)')
        custom_node['rotate'].setExpression('curve - curve(tr_reference_frame)')
        custom_node['scale'].setExpression('curve - curve(tr_reference_frame) + 1')

    else:
        custom_node['translate'].setExpression('curve(tr_reference_frame) - curve')
        custom_node['rotate'].setExpression('curve(tr_reference_frame) - curve')
        custom_node['scale'].setExpression('curve(tr_reference_frame) - curve + 1')


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
        color_knob = nuke.String_Knob('color_group', 'colour group', str(color))
        tracker.addKnob(color_knob)
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
        print('cpin mode')




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