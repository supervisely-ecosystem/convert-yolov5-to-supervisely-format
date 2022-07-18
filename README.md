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
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/convert-yolov5-to-supervisely-format)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/convert-yolov5-to-supervisely-format)](https://supervise.ly)

</div>

## Overview
App transforms folder or `tar` archive with images and labels in [YOLOv5 format](https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data) to [Supervisely format](https://docs.supervise.ly/data-organization/00_ann_format_navi) and uploads data to Supervisely Platform.


## Preparation

Upload images and labels in YOLO v5 format to team files. It is possible to upload folders ([download example](https://drive.google.com/drive/folders/1CqG0bmDRoGF33r5gLWnmEHgkp9u196DZ?usp=sharing)) or tar archives ([download example](https://drive.google.com/drive/folders/1YmbEBqgOVrL9IiBVRpKJ-_7ZnV31Wc7r?usp=sharing)).

![](https://i.imgur.com/BRA0Bjt.png)

Example of `data_config.yaml`:

```yaml
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

```yaml
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

## How to use

Result project will be saved to your current `Workspace` with the same name as the YOLO v5 folder or archive has. 
Application creates 2 datasets: `train` and `val`, and additionally assigns `train` and `val` tags to the images. 
If there are no images in `val` then only `train` dataset is created.

<img src="https://i.imgur.com/KFiRU6K.png"/>

You can also access your project by clicking on it's name from `Tasks` page.

<img src="https://i.imgur.com/hM2kWVf.png"/>


