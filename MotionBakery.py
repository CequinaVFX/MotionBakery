__title__ = 'MotionBakery'
__author__ = 'Luciano Cequinel'
__website__ = 'https://www.cequina.com/'
__website_blog__ = 'https://www.cequina.com/post/motion-bakery'
__version__ = '1.3.4'
__release_date__ = 'February, 22 2026'

import re
import time
import random

import nuke
import _curvelib as cl
import nuke.rotopaint as rp

from MotionBakery_settings import COLOR_RANGE, STANDARD_ROTO_NODE, MARK_ALL_TRACKS


def generate_color():
    """
    Generates a random color in hexadecimal format.

    Returns:
        int: A random color value in hexadecimal integer format (e.g., 0xff0000ff).
    """

    red = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
    green = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
    blue = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
    return int('{:02x}{:02x}{:02x}ff'.format(int(red * 255), int(green * 255), int(blue * 255)), 16)


def get_tracker_names(node):
    """
    Extracts the names of the tracks from a Tracker node.

    Args:
        node (nuke.Node): The Tracker node to extract track names from.

    Returns:
        list: A list of track names, or an Empty list.
    """
    return re.findall(r'"([^"]+)"', node['tracks'].toScript())


def mark_all_trackers(node, mark_translate=True, mark_rotate=True, mark_scale=True) :
    """
    All credits to Isaac Spiegel, I stole this code from him! www.isaacspiegel.com
    I've made some adjustments to fit it into the Bakery.
    """
    if not node:
        return

    knob = node['tracks']
    num_columns = 31
    column_translate = 6
    column_rotate = 7
    column_scale = 8
    count = 0

    total_tracks = len(get_tracker_names(node))

    if total_tracks > 1:
        while count <= int(total_tracks) - 1 :
            knob.setValue(mark_translate, num_columns * count + column_translate)
            knob.setValue(mark_rotate, num_columns * count + column_rotate)
            knob.setValue(mark_scale, num_columns * count + column_scale)

            count += 1

            time.sleep(0.01)


def customize_node(node_class, reference_frame, tracker_node):
    """
    Creates and customizes the new node (Transform, Roto, RotoPaint, or CornerPin2D) based on a Tracker node.

    Args:
        node_class (str): The class of the node to create ('Transform', 'Roto', 'RotoPaint', or 'CornerPin').
        reference_frame (int): The reference frame for the new node.
        tracker_node (nuke.Node): The Tracker node to derive settings from.

    Returns:
        nuke.Node: The newly created and customized node.
    """

    x_position = tracker_node.xpos()
    y_position = tracker_node.ypos()

    dag_width = tracker_node.screenWidth()
    dag_center_point = int(x_position + dag_width / 2)

    transform_class = False
    roto_class = False

    if node_class == 'Transform':
        new_node = nuke.nodes.Transform()
        transform_class = True

    elif node_class == 'Roto':
        new_node = nuke.nodes.Roto()
        roto_class = True

    elif node_class == 'RotoPaint':
        new_node = nuke.nodes.RotoPaint()
        roto_class = True

    elif node_class == 'CornerPin':
        new_node = nuke.nodes.CornerPin2D()
        transform_class = True

    if transform_class:
        new_node['filter'].setValue(tracker_node['filter'].enumName(int(tracker_node['filter'].getValue())))
        new_node['motionblur'].setValue(tracker_node['motionblur'].getValue())
        new_node['shutter'].setValue(tracker_node['shutter'].getValue())
        new_node['shutteroffset'].setValue(
            tracker_node['shutteroffset'].enumName(int(tracker_node['shutteroffset'].getValue())))

    new_node.resetKnobsToDefault()
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

    cmd = """
tkn = nuke.toNode('{0}')
if tkn: nuke.zoom(2, [tkn.xpos(), tkn.ypos()])
else: nuke.message('{0} not found!')
""".format(tracker_node.name())

    # Add Go to parent button
    new_node.addKnob(nuke.PyScript_Knob('goto_parent',
                                        'find {}'.format(tracker_node.name()),
                                        cmd))

    if roto_class:
        new_node['motionblur'].setValue(tracker_node['motionblur'].getValue())
        new_node['motionblur_shutter'].setValue(tracker_node['shutter'].getValue())
        new_node['motionblur_shutter_offset_type'].setValue(
            tracker_node['shutteroffset'].enumName(int(tracker_node['shutteroffset'].getValue())))

        new_node['reference_frame'].setExpression('tr_reference_frame')

        # Create additional knobs for Roto/ RotoPaint nodes
        space001 = nuke.Text_Knob('space001', ' ', '')

        position_knob = nuke.XY_Knob('translate_curve', 'translate')
        position_knob.setFlag(nuke.STARTLINE)
        position_knob.setVisible(False)

        rotation_knob = nuke.Double_Knob('rotate_curve', 'rotate')
        rotation_knob.setFlag(nuke.STARTLINE)
        rotation_knob.setVisible(False)

        scale_knob = nuke.WH_Knob('scale_curve', 'scale')
        scale_knob.setFlag(nuke.STARTLINE)
        scale_knob.setVisible(False)

        center_knob = nuke.XY_Knob('center_curve', 'center')
        center_knob.setFlag(nuke.STARTLINE)
        center_knob.setVisible(False)

        new_node.addKnob(space001)

        new_node.addKnob(position_knob)
        new_node.addKnob(rotation_knob)
        new_node.addKnob(scale_knob)
        new_node.addKnob(center_knob)

    return new_node


def four_corners_of_a_convex_poly(tracker_node, ref_frame):
    """
    Determines the order of four selected tracks in a Tracker node
    to ensure they form a convex quadrilateral.
    This is mostly the original code from Foundry's Nuke Tracker4 node.
    I've removed the mandatory selection of desired tracks.
    It will now automatically use the first 4 tracks available (if at least 4 exist).
    Otherwise, it will return an empty list.

    Args:
        tracker_node (nuke.Node): The Tracker4 node.
        ref_frame (int): The reference frame to evaluate track positions.

    Returns:
        list: A list of the indices of the four tracks, ordered to form a convex quadrilateral.
              Returns an empty list if less than four tracks.
    """

    selected_tracks = tracker_node['selected_tracks']
    all_tracks = tracker_node['tracks']
    total_tracks = len(get_tracker_names(tracker_node))

    # Check if there are 4 tracks selected, Return if not.
    sa = selected_tracks.getText().split(',')
    if len(sa) == 4:
        i = [int(sa[0]), int(sa[1]), int(sa[2]), int(sa[3])]

    elif total_tracks >= 4:
        # It will get the first 4 tracks, if nothing is selected.
        i = [0, 1, 2, 3]

    else:
        # It's not possible to create a CornerPin with less than 4 tracks.
        # It will return an empty list, to lead to an error message.
        return []

    n_cols = 31
    x_col = 2
    y_col = 3

    x = [all_tracks.getValueAt(ref_frame, i[0] * n_cols + x_col),
         all_tracks.getValueAt(ref_frame, i[1] * n_cols + x_col),
         all_tracks.getValueAt(ref_frame, i[2] * n_cols + x_col),
         all_tracks.getValueAt(ref_frame, i[3] * n_cols + x_col)]

    y = [all_tracks.getValueAt(ref_frame, i[0] * n_cols + y_col),
         all_tracks.getValueAt(ref_frame, i[1] * n_cols + y_col),
         all_tracks.getValueAt(ref_frame, i[2] * n_cols + y_col),
         all_tracks.getValueAt(ref_frame, i[3] * n_cols + y_col)]

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
    """
    Creates a layer in a RotoPaint node linked to a Tracker node's animation.

    Args:
        tracker_node (nuke.Node): The Tracker node to copy animation from.
        roto_node (nuke.Node): The new Roto/RotoPaint node.
    """

    grid_x = int(nuke.toNode('preferences').knob('GridWidth').value())
    grid_y = int(nuke.toNode('preferences').knob('GridHeight').value())

    tracker_name = tracker_node.name()
    tracker_node.setSelected(False)

    roto_node['translate_curve'].copyAnimations(tracker_node['translate'].animations())
    roto_node['rotate_curve'].copyAnimations(tracker_node['rotate'].animations())
    roto_node['scale_curve'].copyAnimations(tracker_node['scale'].animations())
    roto_node['center_curve'].copyAnimations(tracker_node['center'].animations())

    roto_node['translate_curve'].setExpression('curve - curve(tr_reference_frame)')
    roto_node['rotate_curve'].setExpression('curve - curve(tr_reference_frame)')
    roto_node['scale_curve'].setExpression('curve - curve(tr_reference_frame) + 1')

    roto_node.setXYpos(tracker_node.xpos() - grid_x * 0,
                       tracker_node.ypos() + grid_y * 2)

    roto_node.setSelected(True)

    # Create linked layer in Roto Node
    curves_knob = roto_node["curves"]
    stab_layer = rp.Layer(curves_knob)
    stab_layer.name = tracker_name

    # Define variable for accessing the getTransform()
    transform_attr = stab_layer.getTransform()

    trans_curve_x = cl.AnimCurve()
    trans_curve_y = cl.AnimCurve()

    trans_curve_x.expressionString = "translate_curve.x"
    trans_curve_y.expressionString = "translate_curve.y"
    trans_curve_x.useExpression = True
    trans_curve_y.useExpression = True

    transform_attr.setTranslationAnimCurve(0, trans_curve_x)
    transform_attr.setTranslationAnimCurve(1, trans_curve_y)

    if tracker_node['rotate'].isAnimated():
        rot_curve = cl.AnimCurve()
        rot_curve.expressionString = "rotate_curve"
        rot_curve.useExpression = True

        transform_attr.setRotationAnimCurve(2, rot_curve)

    if tracker_node['scale'].isAnimated():
        scale_curve = cl.AnimCurve()
        scale_curve.expressionString = "scale_curve"
        scale_curve.useExpression = True

        transform_attr.setScaleAnimCurve(0, scale_curve)
        transform_attr.setScaleAnimCurve(1, scale_curve)

    center_curve_x = cl.AnimCurve()
    center_curve_y = cl.AnimCurve()
    center_curve_x.expressionString = "center_curve.x"
    center_curve_y.expressionString = "center_curve.y"
    center_curve_x.useExpression = True
    center_curve_y.useExpression = True

    transform_attr.setPivotPointAnimCurve(0, center_curve_x)
    transform_attr.setPivotPointAnimCurve(1, center_curve_y)

    curves_knob.rootLayer.append(stab_layer)


def copy_knob_values_at_keys(src, dst, chan):
    """
    Copies keyframe animation from one knob to another, channel by channel.

    Args:
        src (nuke.Knob): The source knob to copy animation from.
        dst (nuke.Knob): The destination knob to copy animation to.
        chan (int): The channel index to copy (0 for X, 1 for Y, etc.).
    """

    if src.isAnimated():
        dst.setAnimated(chan)

        for Idx in range(src.getNumKeys(chan)):
            t = src.getKeyTime(Idx, chan)
            dst.setValueAt(src.getValueAt(t, chan), t, chan)

    else:
        dst.setValue(src.getValue(chan), chan)


def copy_animation_to_transform(tracker_node, custom_node, stabilize=False):
    """
    Copies animation data from a Tracker node to a Transform node.

    Args:
        tracker_node (nuke.Node): The Tracker4 node.
        custom_node (nuke.Node) : The new Transform node.
        stabilize (bool, optional): Whether to invert the transform for stabilization. Defaults to False.
    """

    animated_knobs = []
    for knob in ('translate', 'rotate', 'scale', 'center'):
        if tracker_node[knob].isAnimated():
            animated_knobs.append(knob)
            if knob == 'rotate':
                copy_knob_values_at_keys(tracker_node[knob], custom_node[knob], 0)
            else:
                copy_knob_values_at_keys(tracker_node[knob], custom_node[knob], 0)
                copy_knob_values_at_keys(tracker_node[knob], custom_node[knob], 1)

    src_transform_knob = tracker_node['transform']
    src_transform_name = src_transform_knob.enumName(int(src_transform_knob.getValue()))

    src_transform_is_stabilize = (src_transform_name.find('stabilize') == 0)
    invert_due_to_dest_stabilize = (stabilize and not src_transform_is_stabilize)
    invert_due_to_src_stabilize = ((not stabilize) and src_transform_is_stabilize)
    need_to_invert = (invert_due_to_dest_stabilize or invert_due_to_src_stabilize)

    if need_to_invert:
        trans_knob = custom_node['translate']
        rotate_knob = custom_node['rotate']
        scale_knob = custom_node['scale']
        center_knob = custom_node['center']

        for chan in range(2):
            for Idx in range(center_knob.getNumKeys(chan)):
                t = center_knob.getKeyTime(Idx, chan)
                center_knob.setValueAt(center_knob.getValueAt(t, chan) + trans_knob.getValueAt(t, chan), t, chan)

            for Idx in range(scale_knob.getNumKeys(chan)):
                t = scale_knob.getKeyTime(Idx, chan)
                scale_knob.setValueAt(1 / scale_knob.getValueAt(t, chan), t, chan)

            for Idx in range(trans_knob.getNumKeys(chan)):
                t = trans_knob.getKeyTime(Idx, chan)
                trans_knob.setValueAt(-trans_knob.getValueAt(t, chan), t, chan)

        for Idx in range(rotate_knob.getNumKeys(0)):
            t = rotate_knob.getKeyTime(Idx, 0)
            rotate_knob.setValueAt(-rotate_knob.getValueAt(t, 0), t, 0)

    custom_node['translate'].setExpression('curve - curve(tr_reference_frame)')
    if 'rotate' in animated_knobs:
        custom_node['rotate'].setExpression('curve - curve(tr_reference_frame)')

    if 'scale' in animated_knobs:
        custom_node['scale'].setExpression('curve - curve(tr_reference_frame) + 1')


def check_color_group(tracker_node):
    """
    Checks if a 'color_group' knob exists on the Tracker node; creates it if it doesn't.
    Ensures that the node has a color associated with it for organizational purposes.

    Args:
        tracker_node (nuke.Node): The selected Tracker4 node.
    """

    color = generate_color()

    if tracker_node.knobs().get('color_group'):
        color = int(tracker_node['color_group'].value())

    else:
        tracker_node.addKnob(nuke.Tab_Knob('tracker_knob', 'Tracker Group'))
        tracker_node.addKnob(nuke.String_Knob('color_group', 'color group', str(color)))

        tracker_node['color_group'].setEnabled(False)
        tracker_node['tile_color'].setValue(color)

    return color


def bakery(tracker_node, mode='matchmove'):
    """
    Main function to process a Tracker node and create new nodes based on the specified mode.

    Args:
        tracker_node (nuke.Node): The selected Tracker node - Tracker4 only.
        mode (str, optional): The mode of operation.
            'matchmove' (default)   : Creates a Transform node for match moving.
            'stabilize'             : Creates a Transform node for stabilization.
            'roto'                  : Creates a Roto/ RotoPaint node with a tracked layer.
            'cpin'                  : Creates a MatchMove CornerPin2D node.
    """

    tracker_name = tracker_node.name()
    tracker_reference_frame = int(tracker_node['reference_frame'].value())

    stabilize_mode = mode == 'stabilize'

    color = check_color_group(tracker_node)

    if tracker_node['label'].value() == '':
        tracker_node['label'].setValue('Operation: [value transform]\n'
                                       'Reference frame: [value reference frame]')

    if mode in ('matchmove', 'stabilize'):
        if MARK_ALL_TRACKS:
            mark_all_trackers(tracker_node)

        proposed_name = '{}_{}_'.format(tracker_name, 'stabilize' if stabilize_mode else 'matchmove')
        custom_node = customize_node(node_class='Transform',
                                     reference_frame=tracker_reference_frame,
                                     tracker_node=tracker_node)

        custom_node.setName(proposed_name, uncollide=True)
        custom_node['tile_color'].setValue(color)

        copy_animation_to_transform(tracker_node, custom_node, stabilize_mode)
        custom_node.setSelected(False)

    elif mode == 'roto':
        if MARK_ALL_TRACKS:
            mark_all_trackers(tracker_node)

        proposed_name = '{}_{}_'.format(STANDARD_ROTO_NODE, tracker_name)

        custom_roto = customize_node(node_class=STANDARD_ROTO_NODE,
                                     reference_frame=tracker_reference_frame,
                                     tracker_node=tracker_node)

        custom_roto.setName(proposed_name, uncollide=True)
        custom_roto['tile_color'].setValue(color)

        copy_animation_to_rotopaint_layer(tracker_node, custom_roto)

        custom_roto.setSelected(False)

    else:  # mode == 'cpin'
        tracks_index = four_corners_of_a_convex_poly(tracker_node, tracker_reference_frame)

        if len(tracks_index) == 4:
            proposed_name = '{}_CPin_matchmove_'.format(tracker_name)

            custom_cpin = customize_node(node_class='CornerPin',
                                 reference_frame=tracker_reference_frame,
                                 tracker_node=tracker_node)

            custom_cpin.setName(proposed_name, uncollide=True)
            custom_cpin['tile_color'].setValue(color)

            to_knobs = ["to1", "to2", "to3", "to4"]
            from_knobs = ["from1", "from2", "from3", "from4"]

            for i in range(len(tracks_index)):
                k = tracker_node['tracks']

                track_x_index = tracks_index[i] * 31 + 2
                track_y_index = tracks_index[i] * 31 + 3

                p = custom_cpin[to_knobs[i]]
                p.setAnimated(0)
                p.setAnimated(1)

                for Idx in range(k.getNumKeys(track_x_index)):
                    t = k.getKeyTime(Idx, track_x_index)
                    p.setValueAt(k.getValueAt(t, track_x_index), t, 0)

                for Idx in range(k.getNumKeys(track_y_index)):
                    t = k.getKeyTime(Idx, track_y_index)
                    p.setValueAt(k.getValueAt(t, track_y_index), t, 1)

                p = custom_cpin[from_knobs[i]]
                p.setValue(k.getValueAt(tracker_reference_frame, track_x_index), 0)
                p.setValue(k.getValueAt(tracker_reference_frame, track_y_index), 1)

            custom_cpin['from1'].setExpression('to1(tr_reference_frame)')
            custom_cpin['from2'].setExpression('to2(tr_reference_frame)')
            custom_cpin['from3'].setExpression('to3(tr_reference_frame)')
            custom_cpin['from4'].setExpression('to4(tr_reference_frame)')

            custom_cpin.setSelected(False)

        else:
            nuke.critical('CornerPin2D export requires at least 4 tracks, either selected or not.')
            return


def bake_selection(mode='matchmove'):
    """
    Bakes animation from a selected Tracker4 node to new nodes based on the specified mode.
    This is the main entry point for the user interaction.

    Args:
        mode (str, optional): The mode of operation ('matchmove', 'stabilize', 'roto', or 'cpin').
            Defaults to 'matchmove'.
    """

    node = nuke.selectedNodes()

    if len(node) == 1:
        tracker = nuke.selectedNode()

        if tracker.Class() == 'Tracker4':

            if not get_tracker_names(tracker):
                nuke.message('No tracks on this Tracker!\nYou must track something before baking.')
                return

            tracker.setSelected(False)

            bakery(tracker, mode=mode)

            tracker.setSelected(True)

        else:
            nuke.message('Select a Tracker Node!\nOnly Tracker4 allowed!')

    else:
        if len(node) > 1:
            nuke.message('Select only one node!')
        else:
            nuke.message('Select a Tracker node!')


if __name__ == '__main__':
    bake_selection(mode='matchmove')
