<div align="center" markdown>

<img src="https://i.imgur.com/1YEjnZa.png"/>

# Convert YOLOv5 to Supervisely format

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
App transforms folder or `tar` archive with images and labels in [YOLOv5 format](https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data) to [Supervisely format](https://docs.supervise.ly/data-organization/00_ann_format_navi) and uploads data to Supervisely Platform.


## Preparation

Upload images and labels in YOLO v5 format to team files. It is possible to upload folders ([download example](https://drive.google.com/drive/folders/13frGSuhizrTsot_4ddoMK3llj7O0lKDQ?usp=sharing)) or tar archives ([download example](https://drive.google.com/file/d/1DgmtV7ac0Md9TeSzMJbZ8r77vXC9nk0T/view?usp=sharing)).

![](https://i.imgur.com/BRA0Bjt.png)

**Custom data_config.yaml**
```
names: [kiwi, lemon]            # class names
colors: [[255,1,1], [1,255,1]]  # class colors
nc: 2                           # number of classes
train: ../lemons/images/train   # path to train imgs
val: ../lemons/images/val       # path to val imgs
```

**Project Tree example for Folder and Archive**
<img src="https://i.imgur.com/z3VjMnY.png"/>

**Note**: YOLO v5 project must contain `data_config.yaml` file in its root directory if you want to use custom classes, 
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


## How To Run 

**Step 1**: Add app to your team from Ecosystem if it is not there. Application will be added to `Current Team`->`PLugins & Apps` page.

**Step 2**: Go to `Current Team`->`Files` page, right-click on your `.tar` archive or YOLO v5 project and choose `Run App`->`Convert YOLO v5 to Supervisely format`. You will be redirected to `Workspace`->`Tasks` page.
<img src="https://i.imgur.com/DaXd5Vw.png"/> 

**Note**: Running procedure is simialr for almost all apps that are started from context menu. Example steps with screenshots are [here in how-to-run section](https://github.com/supervisely-ecosystem/merge-classes#how-to-run). 

## How to use

Project will be available in your current `Workspace` with the same name as the folder or archive with your YOLO v5 project. 
Application creates 2 datasets `train` and `val`, and applies matching train and val tags to images. 
If there are no images in your val directory only `train` dataset will be created.

<img src="https://i.imgur.com/KFiRU6K.png"/>

You can also access your project by clicking on it's name from `Tasks` page
<img src="https://i.imgur.com/hM2kWVf.png"/>


