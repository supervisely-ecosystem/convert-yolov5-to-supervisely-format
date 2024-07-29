import os
import tarfile
import zipfile
from os.path import basename, dirname, normpath
from pathlib import Path

import supervisely as sly
import yaml
from dotenv import load_dotenv

from workflow import Workflow

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

# region constants
STORAGE_DIR = os.path.join(os.getcwd(), "storage")
DATA_CONFIG_NAME = "data_config.yaml"
ARCHIVE_EXTENSIONS = [".zip", ".tar", ".gz", ".tar.gz", ".tgz", ".xz"]
# region envvars
team_id = sly.env.team_id()
workspace_id = sly.env.workspace_id()
input_dir = sly.env.folder(raise_not_found=False)
task_id = sly.env.task_id(raise_not_found=False)
# If path to the import dir from env variable does not end with slash, add it, otherwise the error will occur.
if input_dir is not None and not input_dir.endswith("/"):
    sly.logger.info(
        "The path to the import dir from env variable does not end with slash. Adding it."
    )
    input_dir += "/"
input_file = sly.env.file(raise_not_found=False)
# endregion
sly.logger.info(
    f"Team: {team_id}, Workspace: {workspace_id}, "
    f"Input directory: {input_dir}, Input file: {input_file}"
)
if not task_id:
    sly.logger.info("Task id is not found. Looks like app working in development mode.")
sly.fs.mkdir(STORAGE_DIR, remove_content_if_exists=True)

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


def get_coco_names(config_yaml):
    if "names" not in config_yaml:
        sly.logger.warn(
            "['names'] key is empty in {}. Class names will be taken from default coco classes names".format(
                DATA_CONFIG_NAME
            )
        )
    return config_yaml.get("names", coco_classes)


def get_coco_classes_colors(config_yaml, default_count):
    return config_yaml.get("colors", generate_colors(default_count))


def read_config_yaml(config_yaml_path):
    result = {"names": None, "colors": None, "datasets": []}

    if not os.path.isfile(config_yaml_path):
        raise Exception("File {!r} not found".format(config_yaml_path))

    with open(config_yaml_path, "r") as config_yaml_info:
        config_yaml = yaml.safe_load(config_yaml_info)
        result["names"] = get_coco_names(config_yaml)
        result["colors"] = get_coco_classes_colors(config_yaml, len(result["names"]))

        if "nc" not in config_yaml:
            sly.logger.warn(
                "Number of classes is not defined in {}. Actual number of classes is {}.".format(
                    DATA_CONFIG_NAME, len(result["names"])
                )
            )
        elif config_yaml.get("nc", []) != len(result["names"]):
            sly.logger.warn(
                "Defined number of classes {} doesn't match with actual number of classes {}. Config name: {}.".format(
                    config_yaml.get("nc", int), len(result["names"]), DATA_CONFIG_NAME
                )
            )

        if len(config_yaml.get("colors", [])) == 0:
            sly.logger.warn(
                "Colors not found in {}. Colors will be generated for classes automatically.".format(
                    DATA_CONFIG_NAME
                )
            )
            result["colors"] = generate_colors(len(result["names"]))
        elif result["names"] == coco_classes or len(result["names"]) != len(
            config_yaml.get("colors")
        ):
            sly.logger.warn(
                "len(config_yaml['colors']) !=  len(config_yaml['names']). New colors "
                "will be generated for classes automatically."
            )
            result["colors"] = generate_colors(len(result["names"]))

        conf_dirname = os.path.dirname(config_yaml_path)
        sly.logger.info(
            f"Will try to find dataset paths in {DATA_CONFIG_NAME} in {conf_dirname} directory."
        )
        for t in ["train", "val", "test"]:
            sly.logger.info(f"Checking {t} dataset path in {DATA_CONFIG_NAME}...")
            if t not in config_yaml and t != "test":
                raise Exception("{!r} path is not defined in {!r}".format(t, DATA_CONFIG_NAME))

            if t in config_yaml:
                sly.logger.info(f"Found {t} dataset path in {DATA_CONFIG_NAME}...")
                if config_yaml[t].startswith(".."):
                    cur_dataset_path = os.path.normpath(
                        os.path.join(conf_dirname, "/".join(config_yaml[t].split("/")[2:]))
                    )
                else:
                    cur_dataset_path = os.path.normpath(os.path.join(conf_dirname, config_yaml[t]))
                sly.logger.info(f"Path to {t} dataset: {cur_dataset_path}.")

                if len(result["datasets"]) == 1 and config_yaml["train"] == config_yaml["val"]:
                    sly.logger.warn(
                        "'train' and 'val' paths for images are the same in {}. Images will be uploaded "
                        "to 'train' dataset".format(DATA_CONFIG_NAME)
                    )
                    continue

                if os.path.isdir(cur_dataset_path):
                    sly.logger.info(
                        f"Dataset path {cur_dataset_path} exists and was added to the list."
                    )
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

    sly.logger.info(f"Config file {DATA_CONFIG_NAME} has been successfully read.")
    sly.logger.info(f"Was found {len(result['datasets'])} datasets in {DATA_CONFIG_NAME}.")

    return result


def upload_project_meta(api, project_id, config_yaml_info):
    classes = []
    for class_id, class_name in enumerate(config_yaml_info["names"]):
        yaml_class_color = config_yaml_info["colors"][class_id]
        obj_class = sly.ObjClass(
            name=class_name, geometry_type=sly.Rectangle, color=yaml_class_color
        )
        classes.append(obj_class)

    tags_arr = []
    for dataset_type, _ in config_yaml_info["datasets"]:
        tags_arr.append(sly.TagMeta(name=dataset_type, value_type=sly.TagValueType.NONE))
        sly.logger.info(f"Added tag {dataset_type} to project meta.")

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


def process_coco_dir(input_dir, project, project_meta, api, config_yaml_info):
    for dataset_type, dataset_path in config_yaml_info["datasets"]:
        tag_meta = project_meta.get_tag_meta(dataset_type)
        dataset_name = basename(dataset_path)

        images_list = sorted(
            sly.fs.list_files(
                dataset_path,
                valid_extensions=sly.image.SUPPORTED_IMG_EXTS,
                ignore_valid_extensions_case=True,
            )
        )
        if len(images_list) == 0:
            sly.logger.warning(f"Dataset: {dataset_name} is empty. It will be skipped.")
            continue

        dataset = api.dataset.create(project.id, dataset_name, change_name_if_conflict=True)
        progress = sly.Progress(f"Processing {dataset_name} dataset", len(images_list))
        bad_images = []
        for batch in sly._utils.batched(images_list):
            cur_img_names = []
            cur_img_paths = []
            cur_anns = []

            for image_file_name in batch:
                try:
                    sly.image.validate_format(image_file_name)
                except:
                    bad_images.append(image_file_name)
                    continue
                image_name = basename(image_file_name)
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
                                sly.logger.warn(
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

            try:
                img_infos = api.image.upload_paths(dataset.id, cur_img_names, cur_img_paths)
                img_ids = [x.id for x in img_infos]
                api.annotation.upload_anns(img_ids, cur_anns)
            except Exception as e:
                sly.logger.warn(msg=e)

            progress.iters_done_report(len(batch))
        if len(bad_images) > 0:
            sly.logger.warn(
                f"{dataset_name}: skipped {len(bad_images)} images with unsupported format: {bad_images}"
            )

    sly.logger.info(f"Project {project.name} has been successfully uploaded.")


def upload_images_only(api: sly.Api, team_id, input_dir):
    # global team_id, workspace_id, PROJECT_ID, input_dir, input_file

    def _filter_image_file_extention(file_name):
        ext = sly.fs.get_file_ext(file_name).lower()
        return ext in sly.image.SUPPORTED_IMG_EXTS and ext != ".nrrd"

    def _filter_unsupported_files(file_name):
        ext = sly.fs.get_file_ext(file_name).lower()
        return ext not in [".yaml", ".txt"] + sly.image.SUPPORTED_IMG_EXTS or ext == ".nrrd"

    bad_files = sly.fs.list_files_recursively(input_dir, filter_fn=_filter_unsupported_files)
    images_list = sly.fs.list_files_recursively(input_dir, filter_fn=_filter_image_file_extention)

    if len(bad_files) > 0:
        file_names = [sly.fs.get_file_name_with_ext(file_path) for file_path in bad_files]
        sly.logger.warn(f"Skipped {len(bad_files)} files with unsupported format: {file_names}")
    if len(images_list) == 0:
        raise Exception("Not found images in the input directory")
    if len(images_list) == 1:
        common_parent_dir = os.path.dirname(images_list[0])
    else:
        common_parent_dir = os.path.commonpath(images_list)
    project_name = basename(common_parent_dir.strip("/"))

    project = api.project.create(workspace_id, project_name, change_name_if_conflict=True)
    dataset = api.dataset.create(project.id, "train", change_name_if_conflict=True)

    bad_images = []
    progress = sly.Progress("Processing only images", len(images_list))
    for batch in sly.batched(images_list):
        img_names = []
        img_paths = []
        for img in batch:
            try:
                sly.image.validate_format(img)
            except:
                bad_images.append(img)
                continue
            img_names.append(basename(img))
            img_paths.append(img)
        try:
            api.image.upload_paths(dataset.id, img_names, img_paths)
        except Exception as e:
            sly.logger.warn(msg=e)
        progress.iters_done_report(len(batch))
    if len(bad_images) > 0:
        sly.logger.warn(f"Skipped {len(bad_images)} images with unsupported format: {bad_images}")
    try:
        api.task.set_output_project(task_id, project.id, project.name)
    except Exception as e:
        sly.logger.info(
            f"There was an error while setting output project: {e}"
            f"Mostly like the app in development mode and has no task_id."
        )
    sly.logger.info(f"Images from have been uploaded to project '{project.name}'")
    # -------------------------------------- Add Workflow Output ------------------------------------- #
    workflow.add_output(project.id)
    # ----------------------------------------------- - ---------------------------------------------- #


def find_markers(input_dir):
    paths = sly.fs.list_files_recursively(input_dir, valid_extensions=".yaml")
    markers = [basename(path) for path in paths]
    if len(markers) == 0:
        sly.logger.warn("No config files found in directory. Keep by default: data_config.yaml")
        markers = [DATA_CONFIG_NAME]
    if len(markers) == 1:
        sly.logger.info(f"Found config file: {paths}")
    elif len(markers) > 1:
        sly.logger.info(f"Found {len(markers)} config files in directory: {paths}")
    return list(set(markers))


def yolov5_sly_converter(api: sly.Api):
    global team_id, workspace_id, PROJECT_ID, input_dir, input_file, DATA_CONFIG_NAME
    sly.logger.info(f"Input paths: input_dir - {input_dir}. input_file - {input_file}.")

    # check if file was uploaded in folder mode and change mode to file (and opposite)
    sly.logger.info("Checking input path...")
    if input_dir:
        listdir = api.file.listdir(team_id, input_dir)
        if len(listdir) == 1 and sly.fs.get_file_ext(listdir[0]) in ARCHIVE_EXTENSIONS:
            sly.logger.info("Folder mode is selected, but archive file is uploaded.")
            sly.logger.info("Switching to file mode.")
            input_dir, input_file = None, os.path.join(input_dir, listdir[0])
    elif input_file:
        sly.logger.info("File mode is selected, but uploaded file is not an archive.")
        ext = sly.fs.get_file_ext(input_file)
        if ext not in ARCHIVE_EXTENSIONS:
            if ext.lower() not in [".yaml", ".txt"] + sly.image.SUPPORTED_IMG_EXTS:
                raise Exception(
                    "Unsupported files format. "
                    "Project must be an archive file or as directory with IMAGES, TXT labels and YAML config file."
                )
            parent_dir = dirname(normpath(input_file))
            listdir = [basename(normpath(path)) for path in api.file.listdir(team_id, parent_dir)]
            if ext == ".yaml":
                if "images" in listdir and "labels" in listdir:
                    input_dir, input_file = parent_dir, None
            if basename(parent_dir) in ["train", "val"]:
                parent_dir = os.path.dirname(parent_dir)
            if basename(parent_dir) in ["images", "labels"]:
                parent_dir = os.path.dirname(parent_dir)
            if not parent_dir.endswith("/"):
                parent_dir += "/"
            input_dir, input_file = parent_dir, None

    if input_dir:
        # If the app is launched from directory (not archive file).

        sly.logger.info(f"The app is launched from directory: {input_dir}")

        cur_files_path = input_dir
        extract_dir = os.path.join(STORAGE_DIR, str(Path(cur_files_path).parent).lstrip("/"))
        input_dir = os.path.join(extract_dir, Path(cur_files_path).name)
        archive_path = os.path.join(STORAGE_DIR, cur_files_path.strip("/") + ".tar")
        project_name = Path(cur_files_path).name

        sly.logger.info(
            f"Start downloading directory from {cur_files_path} to local path: {input_dir}"
        )

        if sly.fs.dir_exists(input_dir):
            sly.fs.clean_dir(input_dir)
        size = api.file.get_directory_size(team_id, cur_files_path)
        progress = sly.Progress("Downloading directory", total_cnt=size, is_size=True)
        api.file.download_directory(team_id, cur_files_path, input_dir, progress.iters_done_report)

        sly.logger.info(f"Successfully downloaded directory to {input_dir}.")

    else:
        # If the app is launched from archive file.
        sly.logger.info(f"The app is launched from archive file: {input_file}")

        cur_files_path = input_file
        extract_dir = os.path.join(STORAGE_DIR, sly.fs.get_file_name(cur_files_path))
        if sly.fs.get_file_ext(extract_dir) in ARCHIVE_EXTENSIONS:
            extract_dir = os.path.splitext(extract_dir)[0]
        archive_path = os.path.join(STORAGE_DIR, sly.fs.get_file_name_with_ext(cur_files_path))
        input_dir = extract_dir
        project_name = sly.fs.get_file_name(input_file)

        sly.logger.info(
            f"Start downloading archive from {cur_files_path} to local path: {archive_path}"
        )

        if sly.fs.dir_exists(input_dir):
            sly.fs.clean_dir(input_dir)

        if sly.fs.file_exists(archive_path):
            sly.fs.silent_remove(archive_path)

        size = api.file.get_info_by_path(team_id, cur_files_path).sizeb
        progress = sly.Progress("Downloading archive", total_cnt=size, is_size=True)
        api.file.download(
            team_id, cur_files_path, archive_path, progress_cb=progress.iters_done_report
        )

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
            raise Exception("No such file: {}".format(input_file))

        extracted_paths = sly.fs.list_dir_recursively(
            extract_dir, include_subdirs=True, use_global_paths=True
        )
        for path in extracted_paths:
            if sly.fs.get_file_name_with_ext(path).startswith("._"):
                sly.fs.silent_remove(path)

    sly.fs.remove_junk_from_dir(input_dir)
    project_count = 0
    markers = find_markers(input_dir)

    for yolo_dir in sly.fs.dirs_with_marker(input_dir, markers, ignore_case=True):
        try:
            config_yaml_path = os.path.join(yolo_dir, DATA_CONFIG_NAME)
            for marker in markers:
                config_yaml_path = os.path.join(yolo_dir, marker)
                if sly.fs.file_exists(config_yaml_path):
                    sly.logger.info(f"Found config file: {config_yaml_path}")
                    break
            project_name = basename(os.path.normpath(yolo_dir))
            config_yaml_info = read_config_yaml(config_yaml_path)
            project = api.project.create(workspace_id, project_name, change_name_if_conflict=True)
            project_meta = upload_project_meta(api, project.id, config_yaml_info)
            process_coco_dir(yolo_dir, project, project_meta, api, config_yaml_info)
            try:
                api.task.set_output_project(task_id, project.id, project.name)
            except Exception as e:
                sly.logger.info(
                    f"There was an error while setting output project: {e}"
                    f"Mostly like the app in development mode and has no task_id."
                )

            project_count += 1
            # -------------------------------------- Add Workflow Output ------------------------------------- #
            workflow.add_output(project.id)
            # ----------------------------------------------- - ---------------------------------------------- #
        except Exception as e:
            sly.logger.warning(f"There was a problem while processing {yolo_dir}: {e}")

    if project_count > 0:
        sly.logger.info(f"{project_count} projects have been successfully uploaded.")
    else:
        try:
            sly.logger.warn("No projects found. Trying to upload images only.")
            upload_images_only(api, team_id, input_dir)
        except Exception as e:
            raise Exception(
                "No projects have been uploaded. Please check logs and ensure that "
                f"the input data meets the requirements specified in the README: {e}"
            )


if __name__ == "__main__":
    api = sly.Api.from_env()
    workflow = Workflow(api)
    yolov5_sly_converter(api)
