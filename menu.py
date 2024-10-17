import nuke
import MotionBakery
from MotionBakery_settings import *

nuke.tprint('\n\t >> {} | version: {}\n'.format(MotionBakery.__title__, MotionBakery.__version__))

new_menu = nuke.menu('Nodes').addMenu('MotionBakery',
                                      icon='./icons/motion_bakery.png')

new_menu.addCommand('Bake a Match Move', 'MotionBakery.bake_selection(mode="matchmove")',
                    MATCHMOVE_SHORTCUT,
                    icon='./icons/matchmove.png')

new_menu.addCommand('Bake a Stabilize', 'MotionBakery.bake_selection(mode="stabilize")',
                    STABILIZE_SHORTCUT,
                    icon='./icons/stabilize.png')

new_menu.addCommand('Bake a Roto|RotoPaint', 'MotionBakery.bake_selection(mode="roto")',
                    ROTO_SHORTCUT,
                    icon='./icons/roto.png')

new_menu.addCommand('Bake a CornerPin', 'MotionBakery.bake_selection(mode="cpin")',
                    CORNERPIN_SHORTCUT,
                    icon='./icons/cornerpin.png')
