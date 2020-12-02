import os
import yaml
import tarfile

import supervisely_lib as sly

my_app = sly.AppService()

TEAM_ID = os.environ["context.teamId"]
WORKSPACE_ID = os.environ["context.workspaceId"]
INPUT_DIR = os.environ.get("modal.state.slyFolder")
INPUT_FILE = os.environ.get("modal.state.slyFile")

DATA_CONFIG_NAME = "data_config.yaml"

coco_classes = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
        "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
        "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
        "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
        "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
        "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
        "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard",
        "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
        "teddy bear", "hair drier", "toothbrush"]


def generate_colors(count):
    colors = []

    for _ in range(count):
        new_color = sly.color.generate_rgb(colors)
        colors.append(new_color)
    return colors


def get_coco_names(config_yaml, app_logger):
    if "names" in config_yaml:
        return config_yaml["names"]
    app_logger.warn("['names'] field is empty in data_config.yaml. Class names will be taken from default coco class names")
    return coco_classes


def get_coco_classes_colors(config_yaml, default_count):
    if "colors" in config_yaml:
        yaml_class_colors = config_yaml["colors"]
        return yaml_class_colors
    return generate_colors(default_count)


def read_config_yaml(config_yaml_path, app_logger):
    result = {"names": None, "colors": None, "datasets": []}

    if not os.path.isfile(config_yaml_path):
        raise Exception("{} not found in {}".format(DATA_CONFIG_NAME, config_yaml_path))

    with open(config_yaml_path, "r") as config_yaml_info:
        config_yaml = yaml.safe_load(config_yaml_info)
        result["names"] = get_coco_names(config_yaml)
        result["colors"] = get_coco_classes_colors(config_yaml, len(result["names"]))

        conf_dirname = os.path.dirname(config_yaml_path)
        for t in ["train", "val"]:
          if t in config_yaml:
            cur_dataset_path = os.path.normpath(os.path.join(conf_dirname, config_yaml[t]))
            if os.path.isdir(cur_dataset_path):
                result["datasets"].append((t, cur_dataset_path))
            else:
                app_logger.warn("No such Directory: {}. Directory is missing in your project folder or have wrong path in data_config.yaml. Directory will be skipped".format(cur_dataset_path))

        if len(result["datasets"]) == 0:
            raise Exception("No datasets given, check your project Directory or Archive")

        if len(result["datasets"]) == 2 and config_yaml["train"] == config_yaml["val"]:
            app_logger.warn("'train' and 'val' paths for images are equal in data_config.yaml. Images will be uploaded to 'train' dataset")
    return result


def upload_project_meta(api, project_id, config_yaml_info):
    classes = []

    for class_id, class_name in enumerate(config_yaml_info["names"]):
        yaml_class_color = config_yaml_info["colors"][class_id]
        obj_class = sly.ObjClass(name=class_name, geometry_type=sly.Rectangle, color=yaml_class_color)
        classes.append(obj_class)

    tags_arr = [
        sly.TagMeta(name="train", value_type=sly.TagValueType.NONE),

        sly.TagMeta(name="val", value_type=sly.TagValueType.NONE)
    ]

    project_meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection(items=classes), tag_metas=sly.TagMetaCollection(items=tags_arr))

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
    line_parts = line.split()

    if len(line_parts) != 5:
        raise Exception("Invalid annotation format")
    else:
        class_id, x_center, y_center, ann_width, ann_height = line_parts
        class_name = config_yaml_info["names"][int(class_id)]
        return sly.Label(convert_geometry(x_center, y_center, ann_width, ann_height, img_width, img_height), project_meta.get_obj_class(class_name))


def process_coco_dir(input_dir, project, project_meta, api, config_yaml_info, app_logger):
    for dataset_type, dataset_path in config_yaml_info["datasets"]:
        tag_meta = project_meta.get_tag_meta(dataset_type)
        dataset_name = os.path.basename(dataset_path)

        images_list = sorted(sly.fs.list_files(dataset_path))
        if len(images_list) > 0:
            dataset = api.dataset.create(project.id, dataset_name, change_name_if_conflict=True)

            progress = sly.Progress("Processing {} dataset".format(dataset_name), len(images_list), sly.logger)
            for batch in sly._utils.batched(images_list):
                cur_img_names = []
                cur_img_paths = []
                cur_anns = []

                for image_file_name in batch:
                    image_name = os.path.basename(image_file_name)
                    cur_img_names.append(image_name)
                    cur_img_paths.append(image_file_name)
                    ann_file_name = os.path.join(input_dir, "labels", dataset_name, "{}.txt".format(os.path.splitext(image_name)[0]))
                    curr_img = sly.image.read(image_file_name)
                    height, width = curr_img.shape[:2]

                    labels_arr = []
                    if os.path.isfile(ann_file_name):
                        with open(ann_file_name, "r") as f:
                            for idx, line in enumerate(f):
                                try:
                                    label = parse_line(line, width, height, project_meta, config_yaml_info)
                                    labels_arr.append(label)
                                except Exception as e:
                                    app_logger.warn(e, {"filename": ann_file_name, "line": line, "line_num": idx})

                    tags_arr = sly.TagCollection(items=[sly.Tag(tag_meta)])
                    ann = sly.Annotation(img_size=(height, width), labels=labels_arr, img_tags=tags_arr)
                    cur_anns.append(ann)

                img_infos = api.image.upload_paths(dataset.id, cur_img_names, cur_img_paths)
                img_ids = [x.id for x in img_infos]

                api.annotation.upload_anns(img_ids, cur_anns)
                progress.iters_done_report(len(batch))
        else:
            app_logger.warn("Dataset: {} is empty".format(dataset_name))


@my_app.callback("yolov5_sly_converter")
@sly.timeit
def yolov5_sly_converter(api: sly.Api, task_id, context, state, app_logger):
    storage_dir = my_app.data_dir

    if INPUT_DIR:
        cur_files_path = INPUT_DIR
        extract_dir = storage_dir
        archive_path = storage_dir + (cur_files_path.rstrip("/") + ".tar")
    else:
        cur_files_path = INPUT_FILE
        extract_dir = os.path.join(storage_dir, sly.fs.get_file_name(cur_files_path))
        archive_path = os.path.join(storage_dir, sly.fs.get_file_name_with_ext(cur_files_path))

    api.file.download(TEAM_ID, cur_files_path, archive_path)

    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path) as archive:
             archive.extractall(extract_dir)
    else:
        raise Exception("No such file".format(INPUT_FILE))

    input_dir = extract_dir

    if INPUT_DIR:
       cur_files_path = cur_files_path.rstrip("/")
       input_dir = os.path.join(input_dir, cur_files_path.lstrip("/"))

    project_name = sly.fs.get_file_name(cur_files_path)

    config_yaml_info = read_config_yaml(os.path.join(input_dir, DATA_CONFIG_NAME), app_logger)
    project = api.project.create(WORKSPACE_ID, project_name, change_name_if_conflict=True)
    project_meta = upload_project_meta(api, project.id, config_yaml_info)

    process_coco_dir(input_dir, project, project_meta, api, config_yaml_info, app_logger)

    api.task.set_output_project(task_id, project.id, project.name)

    my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "context.teamId": TEAM_ID,
        "context.workspaceId": WORKSPACE_ID,
        "modal.state.slyFolder": INPUT_DIR,
        "modal.state.slyFile": INPUT_FILE,
        "CONFIG_DIR": os.environ.get("CONFIG_DIR", None)
    })

    my_app.run(initial_events=[{"command": "yolov5_sly_converter"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
