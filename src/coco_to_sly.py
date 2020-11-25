import os
import yaml
import tarfile

import supervisely_lib as sly

my_app = sly.AppService()

TEAM_ID = os.environ["context.teamId"]
WORKSPACE_ID = os.environ['context.workspaceId']
INPUT_DIR = os.environ.get("modal.state.slyFolder")
INPUT_FILE = os.environ.get("modal.state.slyFile")

DATA_CONFIG_NAME = 'data_config.yaml'

coco_classes = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus',
                6: 'train', 7: 'truck',
                8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign',
                12: 'parking meter',
                13: 'bench',
                14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow',
                20: 'elephant',
                21: 'bear',
                22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag',
                27: 'tie',
                28: 'suitcase',
                29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite',
                34: 'baseball bat',
                35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket',
                39: 'bottle',
                40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl',
                46: 'banana',
                47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot',
                52: 'hot dog',
                53: 'pizza', 54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch',
                58: 'potted plant',
                59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse',
                65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave', 69: 'oven',
                70: 'toaster',
                71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock', 75: 'vase',
                76: 'scissors',
                77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'}

def generate_colors(count):
    colors = []

    for _ in range(count):
        new_color = sly.color.generate_rgb(colors)
        colors.append(new_color)

    return colors


def get_coco_classes_dict(config_yaml):
    if 'names' in config_yaml:
        yaml_class_names = config_yaml['names']
        return {k: v for k, v in enumerate(yaml_class_names)}

    return coco_classes


def get_coco_classes_colors(config_yaml, default_count):
    if 'colors' in config_yaml:
        yaml_class_colors = config_yaml['colors']
        return yaml_class_colors

    return generate_colors(default_count)


def read_config_yaml(config_yaml_path):
    result = {"names":coco_classes, "colors":None}

    if os.path.isfile(config_yaml_path):
        with open(config_yaml_path, 'r') as config_yaml_info:
            config_yaml = yaml.safe_load(config_yaml_info)
            result["names"] = get_coco_classes_dict(config_yaml)
            result["colors"] = get_coco_classes_colors(config_yaml, len(result["names"]))
    else:
        result["colors"] = generate_colors(len(result["names"]))

    return result


def upload_project_meta(api, project_id, config_yaml_info):
    classes = []

    for class_id, class_name in config_yaml_info["names"].items():
        yaml_class_color = config_yaml_info['colors'][class_id]
        obj_class = sly.ObjClass(name=class_name, geometry_type=sly.Rectangle, color=yaml_class_color)
        classes.append(obj_class)

    project_meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection(items=classes))
    api.project.update_meta(project_id, project_meta.to_json())

    return project_meta


def convert_geometry(x_center, y_center, ann_width, ann_height, img_width, img_height):
    x_center = float(x_center)
    y_center = float(y_center)
    ann_width = float(ann_width)
    ann_height = float(ann_height)

    px_x_center = x_center * img_width
    px_y_center = y_center * img_height

    px_ann_width = ann_width * img_width
    px_ann_height = ann_height * img_height

    left = px_x_center - (px_ann_width / 2)
    right = px_x_center + (px_ann_width / 2)

    top = px_y_center - (px_ann_height / 2)
    bottom = px_y_center + (px_ann_height / 2)

    return sly.Rectangle(top, left, bottom, right)


def parse_line(line, img_width, img_height, project_meta, config_yaml_info):
    class_id, x_center, y_center, ann_width, ann_height = line.split()
    class_name = config_yaml_info["names"].get(int(class_id))

    return sly.Label(convert_geometry(x_center, y_center, ann_width, ann_height, img_width, img_height),
                     project_meta.get_obj_class(class_name))


def process_coco_dir(input_dir, project, project_meta, api, config_yaml_info):
    datasets_dir = os.path.join(input_dir, 'images')

    for dataset_name in sly.fs.get_subdirs(datasets_dir):
        images_list = sorted(sly.fs.list_files(os.path.join(datasets_dir, dataset_name)))

        if len(images_list) > 0:
            dataset = api.dataset.create(project.id, dataset_name)

            progress = sly.Progress(f'Processing {dataset_name} dataset', len(images_list), sly.logger)

            for batch in sly._utils.batched(images_list):
                cur_img_names_batch = []
                cur_img_paths_batch = []
                cur_anns_batch = []

                for image_file_name in batch:
                    image_name = os.path.basename(image_file_name)

                    cur_img_names_batch.append(image_name)
                    cur_img_paths_batch.append(image_file_name)
                    ann_file_name = os.path.join(input_dir, 'labels', dataset_name,
                                                 f"{os.path.splitext(image_name)[0]}.txt")

                    curr_img = sly.image.read(image_file_name)
                    height, width = curr_img.shape[:2]

                    labels_arr = []

                    if os.path.isfile(ann_file_name):
                        with open(ann_file_name, 'r') as f:
                            for line in f:
                                label = parse_line(line, width, height, project_meta, config_yaml_info)
                                labels_arr.append(label)

                    ann = sly.Annotation(img_size=(height, width), labels=labels_arr)
                    cur_anns_batch.append(ann)

                img_infos = api.image.upload_paths(dataset.id, cur_img_names_batch, cur_img_paths_batch)
                img_ids = [x.id for x in img_infos]

                api.annotation.upload_anns(img_ids, cur_anns_batch)

                progress.iters_done_report(len(batch))

        else:
            app_logger.warn(f"Dataset \"{dataset_name}\" is empty")

@my_app.callback("coco_sly_converter")
@sly.timeit
def coco_sly_converter(api: sly.Api, task_id, context, state, app_logger):
    # download dataset files from server files
    storage_dir = my_app.data_dir
    extract_dir = os.path.join(storage_dir, "images_to_convert")

    if INPUT_DIR:
        cur_files_path = INPUT_DIR
    else:
        cur_files_path = INPUT_FILE

    api.file.download(TEAM_ID, cur_files_path, os.path.join(storage_dir, "images_to_convert.tar")) #download data
    with tarfile.open(os.path.join(storage_dir, "images_to_convert.tar")) as archive:
        archive.extractall(extract_dir)

    input_dir = extract_dir

    if INPUT_DIR:
      cur_files_path = cur_files_path.rstrip('/')
      input_dir = os.path.join(input_dir, cur_files_path.lstrip("/"))

    project_name = sly.fs.get_file_name(cur_files_path)

    config_yaml_info = read_config_yaml(os.path.join(input_dir, DATA_CONFIG_NAME))
    project = api.project.create(WORKSPACE_ID, project_name, change_name_if_conflict=True)
    project_meta = upload_project_meta(api, project.id, config_yaml_info)

    process_coco_dir(input_dir, project, project_meta, api, config_yaml_info)

    api.task.set_output_project(task_id, project.id, project.name)


    my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "context.teamId": TEAM_ID,
        "context.workspaceId": WORKSPACE_ID,
        "modal.state.slyFolder": INPUT_DIR,
        "modal.state.slyFile": INPUT_FILE,
        "CONFIG_DIR": os.environ.get("CONFIG_DIR", "ENV not found")
    })

    # Run application service
    my_app.run(initial_events=[{"command": "coco_sly_converter"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)