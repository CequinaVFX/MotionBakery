import os
import nuke

import MotionBakery
from MotionBakery_settings import *

nuke.tprint('\n\t >> {} | version: {}\n'.format(MotionBakery.__title__, MotionBakery.__version__))

_dir = os.path.dirname(__file__)
icon_path = os.path.join(_dir, 'icons')

mb_menu = nuke.menu('Nodes').addMenu('MotionBakery',
                                      icon='{}/{}.png'.format(icon_path, 'motion_bakery'))

mb_menu.addCommand('Bake a Match Move', 'MotionBakery.bake_selection(mode="matchmove")',
                    MATCHMOVE_SHORTCUT,
                    icon='{}/{}.png'.format(icon_path, 'matchmove'))

mb_menu.addCommand('Bake a Stabilize', 'MotionBakery.bake_selection(mode="stabilize")',
                    STABILIZE_SHORTCUT,
                    icon='{}/{}.png'.format(icon_path, 'stabilize'))

mb_menu.addCommand('Bake a Roto|RotoPaint', 'MotionBakery.bake_selection(mode="roto")',
                    ROTO_SHORTCUT,
                    icon='{}/{}.png'.format(icon_path, 'roto'))

mb_menu.addCommand('Bake a CornerPin', 'MotionBakery.bake_selection(mode="cpin")',
                    CORNERPIN_SHORTCUT,
                    icon='{}/{}.png'.format(icon_path, 'cornerpin'))
