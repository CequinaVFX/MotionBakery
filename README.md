# MotionBakery

## Overview

MotionBakery is a Nuke script designed to streamline the process of creating nodes from Tracker4 data.
It automates the creation of Transform, Roto, RotoPaint, and CornerPin2D nodes, copying their animation to the Tracker4 node. This simplifies workflows for tasks such as matchmoving, stabilization, and rotoscoping.

## Features

* **Node Creation:** Automatically creates Transform, Roto, RotoPaint, and CornerPin2D nodes from selected Tracker4 nodes.
* **Copy Tracking data:** Copies the animation data from the Tracker4 node to the newly created nodes.
* **Customization:** Allows customization of created nodes, including setting reference frames and copying Tracker4 settings.
* **Color Grouping**: Applies a random color to the created nodes and adds a non-editable color_group knob on the tracker node.

## Installation
1. **Download the [repository](https://github.com/CequinaVFX/MotionBakery)**
2. Unzip and rename the folder to `MotionBakery`
3. Copy the folder to [.nuke standard folder](https://learn.foundry.com/nuke/12.2/content/user_guide/configuring_nuke/finding_nuke_home.html)
4. Add these line to init.py (`create a new one if it doesn't exist`):
   ```python
   import nuke 
   nuke.pluginAddPath('./MotionBakery')
   ```
## Requirements

* Nuke 11.0 or higher.
* A Tracker4 node in your Nuke composition.

## How to Use

1.  **Select a Tracker node.**
2.  **Choose the mode:** Select "MotionBakery" from the Nuke menu. The script will execute in matchmove mode.
3.  The script will create the appropriate node(s) and connect them to the Tracker4 node.

##  Tracker Node Label

The script automatically sets the label of the Tracker4 node to display the operation and reference frame.

## Author

Luciano Cequinel

## License

MIT License
