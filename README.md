<div align="center" markdown>

<img src="https://i.imgur.com/0uLnE9D.png"/>

# Create Users from CSV

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/convert-yolov5-to-supervisely-format)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/convert-yolov5-to-supervisely-format)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-yolov5-to-supervisely-format&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-yolov5-to-supervisely-format&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-yolov5-to-supervisely-format&counter=runs&label=runs&123)](https://supervise.ly)

</div>

## Overview

Transform [YOLO v5](https://github.com/ultralytics/yolov5) project folder or `.tar` archive to supervisely format project.


## Preparation

1. You can download [Coco128](https://www.kaggle.com/ultralytics/coco128/download) project or our [lemons](link) project with custom classes
or create your own project.
2. YOLO v5 project must contain `data_config.yaml` file in its root directory if you want to use custom classes, 
or it will use default coco class names:
```
# class names
names: ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
        'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
        'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
        'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 
        'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 
        'teddy bear', 'hair drier', 'toothbrush']
```
3. Here's the example of how your YOLO v5 project folder or archive should look like:
<img src="https://i.imgur.com/reiLqjv.png"/>

4. Drag and drop your project or archive to Team Files
<img src="https://i.imgur.com/W8geV2F.gif"/>

## How To Run 
**Step 1**: Add app to your team from Ecosystem if it is not there. Application will be added to `Current Team`->`PLugins & Apps` page.

**Step 2**: Go to `Current Team`->`Files` page, right-click on your `.tar` archive or YOLO v5 project and choose `Run App`->`Convert YOLO v5 to Supervisely format`.
<img src="https://i.imgur.com/weCzQAf.png"/> 

**Note**: You will be redirected to `Workspace`->`Tasks` page. You can go to your project by clicking on it's name from `Tasks` page. Project will be available in your current `Workspace`
<img src="https://i.imgur.com/5BneltN.png"/>

**Note**: Running procedure is simialr for almost all apps that are started from context menu. Example steps with screenshots are [here in how-to-run section](https://github.com/supervisely-ecosystem/merge-classes#how-to-run). 
