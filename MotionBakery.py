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


def customize_node(node_class, reference_frame, tracker_node):
    x = tracker_node.xpos()
    y = tracker_node.ypos()
    w = tracker_node.screenWidth()
    h = tracker_node.screenHeight()
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

    set_reference = nuke.PyScript_Knob('set_reference', 'set to current frame',
                                       'nuke.thisNode()["tr_reference_frame"].setValue(nuke.frame())')
    new_node.addKnob(set_reference)

    parent_command = 'nuke.zoom(2, [{}, {}])'.format(x, y)
    goto_parent = nuke.PyScript_Knob('goto_parent', 'go to parent Tracker', parent_command)
    # goto_parent.setFlag(nuke.STARTLINE)
    new_node.addKnob(goto_parent)

    return new_node


def copyKnobValuesAtKeys(src, dst, chan):
    if src.isAnimated():
        dst.setAnimated(chan)
        for Idx in range(src.getNumKeys(chan)):
            t = src.getKeyTime(Idx, chan)
            dst.setValueAt(src.getValueAt(t, chan), t, chan)

    else:
        dst.setValue(src.getValue(chan), chan)


def copyAnimation(tracker, custom_node, stabilize=False):
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
    # custom_node['scale'].setExpression('curve - curve(tr_reference_frame) + 1')
def bakery(tracker, mode='matchmove', bake_roto=False):
    tracker_name = tracker.name()
    tracker_reference_frame = int(tracker['reference_frame'].value())

    x = tracker.xpos()
    y = tracker.ypos()
    w = tracker.screenWidth()
    h = tracker.screenHeight()
    m = int(x + w / 2)

    stabilize = True if mode == 'stabilize' else False
    proposedName = '{}_{}_'.format(tracker_name, 'stabilize' if stabilize else 'matchmove')

    color = generate_color()
    if 'color_group' in tracker.knobs():
        print('color from knob')
        color = int(tracker['color_group'].value())
    else:
        color_knob = nuke.String_Knob('color_group', 'colour group', str(color))
        tracker.addKnob(color_knob)
        tracker['tile_color'].setValue(color)

    custom_node = customize_node(node_class='Transform',
                                 reference_frame=int(tracker['reference_frame'].value()),
                                 tracker_node=tracker)

    custom_node.setName(proposedName, uncollide=True)
    custom_node['tile_color'].setValue(color)
    custom_node['label'].setValue('{} : {}'.format(str(tracker_reference_frame),
                                                   'stabilize' if stabilize else 'matchmove'))

    copyAnimation(tracker, custom_node, stabilize)

    if bake_roto:
        # create and setup new Roto node
        custom_node = customize_node(node_class=standard_roto_node,
                                     reference_frame=tracker_reference_frame,
                                     tracker_node=tracker)

        proposedName = 'Roto_from_{}_'.format(tracker_name)
        custom_node.setName(proposedName, uncollide=True)
        custom_node['tile_color'].setValue(color)
        custom_node['label'].setValue('{} : {}'.format(str(tracker_reference_frame),
                                                       'stabilize' if stabilize else 'matchmove'))

        copyAnimation(tracker, custom_node, stabilize=False)


def bake_it(mode='matchmove', bake_roto=False):
    node = nuke.selectedNodes()
    if len(node) == 1:
        tracker = nuke.selectedNode()
        if tracker.Class() == 'Tracker4':
            if mode == 'cpin':
                pass
            else:
                if bake_roto:
                    bakery(tracker, mode='matchmove', bake_roto=bake_roto)
                else:
                    bakery(tracker, mode=mode)
        else:
            print('Select a Tracker Node!')

    else:
        if len(node) > 1:
            print('Select only one node!')
        else:
            print('Select a Tracker node!')



# bake_it(mode='matchmove')
# bake_it(mode='stabilize')
# bake_it(mode='matchmove', bake_roto=True)