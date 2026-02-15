# MotionBakery
### An update to the default Exporting Tracking data. 💃

<img width="75%" src=".\imgs\MotionBakery_menu_nodes.jpg" />

## Overview
MotionBakery is a Nuke script designed to streamline the process of creating useful nodes from a Tracker node.
It automates the creation of Transform, Roto or RotoPaint, and CornerPin2D nodes, copying the animated knobs from Tracker node.</p>
The result is exactly the same as if you create the nodes from Tracker.</p>
The intent here is to make it faster and easier to create nodes from tracked data, allowing artists to extract that data without having to open Tracker properties.

## Features
* **Node Creation:** Creates Transform (match move or stabilize), Roto/RotoPaint, and CornerPin2D nodes from selected Tracker nodes.
* **Color Grouping:** Applies a random color to the Tracker and the created nodes to make it easy to identify the parenting in the node graph.
* **Find Parent:** you can easily go to the parent Tracker.
* **Independent nodes:** each new node is independent, allowing you to set a reference frame for each one.

<img width="50%" src=".\imgs\Settings_tab.jpg" />

## Customization 
In `MotionBakery_settings.py` you can:
* **Set Shortcuts:** set a shortcut for each operation 🎹
* **Roto or RotoPaint**: you can choose to create either a Roto or RotoPaint node.
> ⚠️ <font color='darkred'><b>You must restart Nuke after changing the settings.</b></font>


## Installation
1. **Download the [repository](https://github.com/CequinaVFX/MotionBakery)** or from [Nukepedia](www.nukepedia.com)
2. Unzip and rename the folder to `MotionBakery`
3. Copy the folder to [.nuke standard folder](https://learn.foundry.com/nuke/12.2/content/user_guide/configuring_nuke/finding_nuke_home.html)
4. Add these line to init.py (`create a new one if it doesn't exist`):
```python
import nuke 
nuke.pluginAddPath('./MotionBakery')
```
## Author
Luciano Cequinel | [cequina.com](www.cequina.com)

