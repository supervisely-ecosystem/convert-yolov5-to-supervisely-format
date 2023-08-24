import os
import yaml
import tarfile
import zipfile

from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm

import supervisely as sly


if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

my_app = sly.AppService()

TEAM_ID = sly.env.team_id()
TASK_ID = sly.env.task_id()
WORKSPACE_ID = sly.env.workspace_id()
INPUT_DIR = os.environ.get("modal.state.slyFolder")
# If path to the import dir from env variable does not end with slash, add it, otherwise the error will occur.
if INPUT_DIR is not None and not INPUT_DIR.endswith("/"):
    sly.logger.warning(
        "The path to the import dir from env variable does not end with slash. Adding it."
    )
    INPUT_DIR += "/"
INPUT_FILE = os.environ.get("modal.state.slyFile")

DATA_CONFIG_NAME = "data_config.yaml"

coco_classes = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


def generate_colors(count):
    colors = []
    for _ in range(count):
        new_color = sly.color.generate_rgb(colors)
        colors.append(new_color)
    return colors


def get_coco_names(config_yaml, app_logger):
    if "names" not in config_yaml:
        app_logger.warn(
            "['names'] key is empty in {}. Class names will be taken from default coco classes names".format(
                DATA_CONFIG_NAME
            )
        )
    return config_yaml.get("names", coco_classes)


def get_coco_classes_colors(config_yaml, default_count):
    return config_yaml.get("colors", generate_colors(default_count))


def read_config_yaml(config_yaml_path, app_logger):
    result = {"names": None, "colors": None, "datasets": []}

    if not os.path.isfile(config_yaml_path):
        raise Exception("File {!r} not found".format(config_yaml_path))

    with open(config_yaml_path, "r") as config_yaml_info:
        config_yaml = yaml.safe_load(config_yaml_info)
        result["names"] = get_coco_names(config_yaml, app_logger)
        result["colors"] = get_coco_classes_colors(config_yaml, len(result["names"]))

        if "nc" not in config_yaml:
            app_logger.warn(
                "Number of classes is not defined in {}. Actual number of classes is {}.".format(
                    DATA_CONFIG_NAME, len(result["names"])
                )
            )
        elif config_yaml.get("nc", []) != len(result["names"]):
            app_logger.warn(
                "Defined number of classes {} doesn't match with actual number of classes {}. Config name: {}.".format(
                    config_yaml.get("nc", int), len(result["names"]), DATA_CONFIG_NAME
                )
            )

        if len(config_yaml.get("colors", [])) == 0:
            app_logger.warn(
                "Colors not found in {}. Colors will be generated for classes automatically.".format(
                    DATA_CONFIG_NAME
                )
            )
            result["colors"] = generate_colors(len(result["names"]))
        elif result["names"] == coco_classes or len(result["names"]) != len(
            config_yaml.get("colors")
        ):
            app_logger.warn(
                "len(config_yaml['colors']) !=  len(config_yaml['names']). New colors "
                "will be generated for classes automatically."
            )
            result["colors"] = generate_colors(len(result["names"]))

        conf_dirname = os.path.dirname(config_yaml_path)
        for t in ["train", "val"]:
            if t not in config_yaml:
                raise Exception("{!r} path is not defined in {!r}".format(t, DATA_CONFIG_NAME))

            if t in config_yaml:
                if config_yaml[t].startswith(".."):
                    cur_dataset_path = os.path.normpath(
                        os.path.join(conf_dirname, "/".join(config_yaml[t].split("/")[2:]))
                    )
                else:
                    cur_dataset_path = os.path.normpath(os.path.join(conf_dirname, config_yaml[t]))

                if len(result["datasets"]) == 1 and config_yaml["train"] == config_yaml["val"]:
                    app_logger.warn(
                        "'train' and 'val' paths for images are the same in {}. Images will be uploaded "
                        "to 'train' dataset".format(DATA_CONFIG_NAME)
                    )
                    continue

                if os.path.isdir(cur_dataset_path):
                    result["datasets"].append((t, cur_dataset_path))

                elif len(result["datasets"]) == 0:
                    raise Exception(
                        "No 'train' or 'val' directories found. Please check the project directory or config file."
                    )

                elif len(result["datasets"]) == 1:
                    os.makedirs(cur_dataset_path)
                    sly.logger.info(
                        f"The directory {cur_dataset_path} wasn't found. It was created."
                    )

    return result


def upload_project_meta(api, project_id, config_yaml_info):
    classes = []
    for class_id, class_name in enumerate(config_yaml_info["names"]):
        yaml_class_color = config_yaml_info["colors"][class_id]
        obj_class = sly.ObjClass(
            name=class_name, geometry_type=sly.Rectangle, color=yaml_class_color
        )
        classes.append(obj_class)

    tags_arr = [
        sly.TagMeta(name="train", value_type=sly.TagValueType.NONE),
        sly.TagMeta(name="val", value_type=sly.TagValueType.NONE),
    ]
    project_meta = sly.ProjectMeta(
        obj_classes=sly.ObjClassCollection(items=classes),
        tag_metas=sly.TagMetaCollection(items=tags_arr),
    )
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
        return sly.Label(
            convert_geometry(x_center, y_center, ann_width, ann_height, img_width, img_height),
            project_meta.get_obj_class(class_name),
        )


def process_coco_dir(input_dir, project, project_meta, api, config_yaml_info, app_logger):
    for dataset_type, dataset_path in config_yaml_info["datasets"]:
        tag_meta = project_meta.get_tag_meta(dataset_type)
        dataset_name = os.path.basename(dataset_path)

        images_list = sorted(
            sly.fs.list_files(dataset_path, valid_extensions=sly.image.SUPPORTED_IMG_EXTS)
        )
        if len(images_list) == 0:
            sly.logger.warning(f"Dataset: {dataset_name} is empty. It will be skipped.")
            continue

        dataset = api.dataset.create(project.id, dataset_name, change_name_if_conflict=True)
        progress = sly.Progress(
            "Processing {} dataset".format(dataset_name), len(images_list), sly.logger
        )
        for batch in sly._utils.batched(images_list):
            cur_img_names = []
            cur_img_paths = []
            cur_anns = []

            for image_file_name in batch:
                image_name = os.path.basename(image_file_name)
                cur_img_names.append(image_name)
                cur_img_paths.append(image_file_name)
                ann_file_name = os.path.join(
                    input_dir,
                    "labels",
                    dataset_name,
                    "{}.txt".format(os.path.splitext(image_name)[0]),
                )
                curr_img = sly.image.read(image_file_name)
                height, width = curr_img.shape[:2]

                labels_arr = []
                if os.path.isfile(ann_file_name):
                    with open(ann_file_name, "r") as f:
                        for idx, line in enumerate(f):
                            try:
                                label = parse_line(
                                    line, width, height, project_meta, config_yaml_info
                                )
                                labels_arr.append(label)
                            except Exception as e:
                                app_logger.warn(
                                    e,
                                    {
                                        "filename": ann_file_name,
                                        "line": line,
                                        "line_num": idx,
                                    },
                                )

                tags_arr = sly.TagCollection(items=[sly.Tag(tag_meta)])
                ann = sly.Annotation(img_size=(height, width), labels=labels_arr, img_tags=tags_arr)
                cur_anns.append(ann)

            img_infos = api.image.upload_paths(dataset.id, cur_img_names, cur_img_paths)
            img_ids = [x.id for x in img_infos]

            api.annotation.upload_anns(img_ids, cur_anns)
            progress.iters_done_report(len(batch))

    sly.logger.info(f"Project {project.name} has been successfully uploaded.")


def upload_images_only(api: sly.Api, task_id, team_id, input_dir):
    global TEAM_ID, WORKSPACE_ID, PROJECT_ID, INPUT_DIR, INPUT_FILE
    files = api.file.list(team_id, input_dir)
    images_list = [f for f in files if sly.fs.get_file_ext(f.name) in sly.image.SUPPORTED_IMG_EXTS]
    if len(images_list) == 0:
        return
    common_parent_dir = os.path.commonpath([img.path for img in images_list])
    project_name = os.path.basename(common_parent_dir.strip("/"))

    project = api.project.create(WORKSPACE_ID, project_name, change_name_if_conflict=True)
    dataset = api.dataset.create(project.id, "ds0", change_name_if_conflict=True)
    pbar = tqdm(total=len(images_list), desc="Uploading only images")
    for batch in sly.batched(images_list):
        img_names = [img.name for img in batch]
        img_links = [img.full_storage_url for img in batch]
        api.image.upload_links(dataset.id, img_names, img_links)
        pbar.update(len(batch))

    api.task.set_output_project(task_id, project.id, project.name)
    sly.logger.info(f"Images from have been uploaded to project {project.name}")


@my_app.callback("yolov5_sly_converter")
@sly.timeit
def yolov5_sly_converter(api: sly.Api, task_id, context, state, app_logger):
    global TEAM_ID, WORKSPACE_ID, PROJECT_ID, INPUT_DIR, INPUT_FILE
    sly.logger.info(f"Launching converter. INPUT_DIR: {INPUT_DIR}. INPUT_FILE: {INPUT_FILE}.")

    storage_dir = my_app.data_dir

    # check if file was uploaded in folder mode and change mode to file (and opposite)
    if INPUT_DIR:
        listdir = api.file.listdir(TEAM_ID, INPUT_DIR)
        if len(listdir) == 1 and (tarfile.is_tarfile(listdir[0]) or zipfile.is_zipfile(listdir[0])):
            sly.logger.info("Folder mode is selected, but archive file is uploaded.")
            sly.logger.info("Switching to file mode.")
            INPUT_DIR, INPUT_FILE = None, os.path.join(INPUT_DIR, listdir[0])
    elif INPUT_FILE:
        if not (tarfile.is_tarfile(INPUT_FILE) or zipfile.is_zipfile(INPUT_FILE)):
            sly.logger.info("File mode is selected, but uploaded file is not an archive.")
            parent_dir, _ = os.path.split(INPUT_FILE)
            if os.path.basename(parent_dir) in ["images", "labels"]:
                parent_dir = os.path.dirname(parent_dir)
            elif os.path.basename(parent_dir) in ["train", "val"]:
                parent_dir = os.path.dirname(os.path.dirname(parent_dir))
            if not parent_dir.endswith("/"):
                parent_dir += "/"
            sly.logger.info(f"parent_dir: {parent_dir}")
            listdir = api.file.listdir(TEAM_ID, parent_dir, recursive=True)
            config_files_list = [file for file in listdir if sly.fs.get_file_ext(file) == ".yaml"]
            file_names = [os.path.basename(file) for file in listdir]
            if DATA_CONFIG_NAME in file_names:
                sly.logger.info("Switching to folder mode.")
                INPUT_DIR, INPUT_FILE = parent_dir, None
            elif len(config_files_list) == 1:
                DATA_CONFIG_NAME = os.path.basename(config_files_list[0])
                sly.logger.info(f"Switching to folder mode. DATA_CONFIG_NAME: {DATA_CONFIG_NAME}")
                INPUT_DIR, INPUT_FILE = os.path.dirname(DATA_CONFIG_NAME), None
            elif len(config_files_list) > 1:
                sly.logger.info(f"Found {len(config_files_list)} config files in directory.")
                parent_dir = os.path.commonpath(config_files_list)
                sly.logger.info(f"Swithing to folder mode. Common_parent_dir: {parent_dir}")
                INPUT_DIR, INPUT_FILE = parent_dir, None
            else:
                sly.logger.warn("data_config.yaml file not found in directory. Trying to parce images only.")
                try:
                    upload_images_only(api, task_id, TEAM_ID, parent_dir)
                    my_app.stop()
                except Exception as e:
                    error_msg = (
                        "File mode is selected, but uploaded file is not an archive. \n"
                        "Config data_config.yaml file not found in directory. \n"
                        "Prepare your data according to the app requirements (README) and try again. \n"
                        "Uploading only images failed. Reason: \n"
                        f"{e}"
                    )
                    raise Exception(error_msg)

    if INPUT_DIR:
        # If the app is launched from directory (not archive file).

        sly.logger.info("The app is launched from directory (not archive file).")

        cur_files_path = INPUT_DIR
        extract_dir = os.path.join(storage_dir, str(Path(cur_files_path).parent).lstrip("/"))
        input_dir = os.path.join(extract_dir, Path(cur_files_path).name)
        archive_path = os.path.join(storage_dir, cur_files_path.strip("/") + ".tar")
        project_name = Path(cur_files_path).name

        sly.logger.info(
            f"Trying to download directory from {cur_files_path} to local path: {input_dir}"
        )

        api.file.download_directory(TEAM_ID, cur_files_path, input_dir)

        sly.logger.info(f"Successfully downloaded directory to {input_dir}.")

    else:
        # If the app is launched from archive file.

        sly.logger.info("The app is launched from archive file.")

        cur_files_path = INPUT_FILE
        extract_dir = os.path.join(storage_dir, sly.fs.get_file_name(cur_files_path))
        archive_path = os.path.join(storage_dir, sly.fs.get_file_name_with_ext(cur_files_path))
        input_dir = extract_dir
        project_name = sly.fs.get_file_name(INPUT_FILE)

        sly.logger.info(
            f"Trying to download archive from {cur_files_path} to local path: {archive_path}"
        )

        api.file.download(TEAM_ID, cur_files_path, archive_path)

        sly.logger.info(
            f"Successfully downloaded archive to {archive_path}, will extract it to {extract_dir}."
        )

        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as archive:
                archive.extractall(extract_dir)

            sly.logger.info(f"Successfully extracted archive to {extract_dir}.")
        elif zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            sly.logger.info(f"Successfully extracted archive to {extract_dir}.")
        else:
            sly.logger.warn("Archive cannot be unpacked {}".format(archive_path))
            raise Exception("No such file: {}".format(INPUT_FILE))

    # if not os.path.exists(os.path.join(input_dir, DATA_CONFIG_NAME)):
    #     sly.logger.info(
    #         f"Yaml config file not found in {input_dir}. Searching for it in subfolders."
    #     )
    #     all_files = glob.glob(os.path.join(input_dir, "**"), recursive=True)
    #     yaml_path = None
    #     for file in all_files:
    #         if os.path.basename(file) == DATA_CONFIG_NAME:
    #             yaml_path = file
    #             break
    #     if yaml_path is None:
    #         raise FileNotFoundError(
    #             "Yaml config file not found. Please check your input project directory."
    #         )
    #     else:
    #         sly.logger.info(f"Yaml config file found: {yaml_path}")
    #         input_dir = os.path.dirname(yaml_path)
    #         sly.logger.info(f"Input dir path changed to {input_dir}")

    # sly.logger.info(f"List of files in input directory: {os.listdir(input_dir)}")

    project_count = 0

    for yolo_dir in sly.fs.dirs_with_marker(input_dir, DATA_CONFIG_NAME, ignore_case=True):
        try:
            config_yaml_info = read_config_yaml(
                os.path.join(yolo_dir, DATA_CONFIG_NAME), app_logger
            )
            project = api.project.create(WORKSPACE_ID, project_name, change_name_if_conflict=True)
            project_meta = upload_project_meta(api, project.id, config_yaml_info)
            process_coco_dir(input_dir, project, project_meta, api, config_yaml_info, app_logger)
            api.task.set_output_project(task_id, project.id, project.name)

            project_count += 1
        except Exception as e:
            sly.logger.warning(f"There was a problem while processing {yolo_dir}: {e}")

    if project_count:
        sly.logger.info(f"{project_count} projects have been successfully uploaded.")
    else:
        raise Exception(
            "No projects have been uploaded. Please check logs and ensure that "
            "the input data meets the requirements specified in the README."
        )

    my_app.stop()


def main():
    sly.logger.info(
        "Script arguments",
        extra={
            "context.teamId": TEAM_ID,
            "context.workspaceId": WORKSPACE_ID,
            "modal.state.slyFolder": INPUT_DIR,
            "modal.state.slyFile": INPUT_FILE,
            "CONFIG_DIR": os.environ.get("CONFIG_DIR", None),
        },
    )

    my_app.run(initial_events=[{"command": "yolov5_sly_converter"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
