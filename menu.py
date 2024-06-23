import nuke
import MotionBakery
from MotionBakery_settings import *

nuke.tprint('\n\t{} | version: {}\n'.format(MotionBakery.__title__, MotionBakery.__version__))

new_menu = nuke.menu('Nodes').addMenu('MotionBakery', icon=motion_baker_icon)

new_menu.addCommand('Bake a Match Move', 'MotionBakery.bake_it(mode="matchmove")',
                    matchmove_shortcut, icon=matchmove_icon)

new_menu.addCommand('Bake a Stabilize', 'MotionBakery.bake_it(mode="stabilize")',
                    stabilize_shortcut, icon=stabilize_icon)

new_menu.addCommand('Bake a Roto|RotoPaint', 'MotionBakery.bake_it(mode="roto")',
                    matchmove_kit_shortcut, icon=matchmove_kit_icon)

new_menu.addCommand('Bake a CornerPin', 'MotionBakery.bake_it(mode="cpin")',
                    cornerpin_shortcut, icon=cornerpin_icon)
