import nuke
import MotionBakery
from MotionBakery_settings import *

nuke.tprint('\n\t{} | version: {}\n'.format(MotionBakery.__title__, MotionBakery.__version__))

new_menu = nuke.menu('Nodes').addMenu('MotionBakery',
                                      icon='./icons/motion_bakery.png')

new_menu.addCommand('Bake a Match Move', 'MotionBakery.bake_it(mode="matchmove")',
                    matchmove_shortcut,
                    icon='./icons/matchmove.png')

new_menu.addCommand('Bake a Stabilize', 'MotionBakery.bake_it(mode="stabilize")',
                    stabilize_shortcut,
                    icon='./icons/stabilize.png')

new_menu.addCommand('Bake a Roto|RotoPaint', 'MotionBakery.bake_it(mode="roto")',
                    matchmove_kit_shortcut,
                    icon='./icons/roto.png')

new_menu.addCommand('Bake a CornerPin', 'MotionBakery.bake_it(mode="cpin")',
                    cornerpin_shortcut,
                    icon='./icons/cornerpin.png')
