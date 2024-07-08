import dataclasses
import os.path


@dataclasses.dataclass
class SAMProjectInfo:
    project_name: str
    root_dir: str
    build_dir: str


def get_sam_project_info(
    template_file_name: str = "template.yaml",
    start_dir: str = None,
):
    def walk(dir_name: str):
        dir_contents = os.listdir(dir_name)
        if template_file_name in dir_contents:
            return dir_name
        else:
            parent_dir_name = os.path.dirname(dir_name)
            if parent_dir_name == dir_name or parent_dir_name is None:
                raise ValueError(f"Cannot find {template_file_name}")
            return walk(os.path.dirname(dir_name))

    if start_dir is None:
        current_working_dir = os.getcwd()
        start_dir = current_working_dir

    root_dir = walk(start_dir)
    project_dir_name = os.path.basename(root_dir)
    build_dir = os.path.join(root_dir, ".aws-sam", "build")

    return SAMProjectInfo(
        project_name=project_dir_name,
        root_dir=root_dir,
        build_dir=build_dir,
    )
