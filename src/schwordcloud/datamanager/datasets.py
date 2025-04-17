from .sch import fetch_sch_database
from .annotation import fetch_annotation
from os.path import join
from pathlib import Path


class DataManager:
    """
    A class to manage the download and extraction of schematic datasets.

    Attributes
    ----------
    remote_sch_dataset : dict
        A dictionary containing the URL and filename of the remote dataset.
    local_sch_dataset : str
        The path to the local dataset directory.
    """

    def __init__(self, config: dict):
        # local datasets
        self.data_home = Path(config["datasets"]["data_home"]).expanduser()
        self.sch_data_home = Path(config["datasets"]["sch_data_home"]).expanduser()
        self.annotation_data_home = Path(
            config["datasets"]["annotation_data_home"]
        ).expanduser()
        self.search_results_data_home = Path(
            config["datasets"]["search_results_data_home"]
        ).expanduser()
        if not all(
            path.exists()
            for path in [
                self.data_home,
                self.sch_data_home,
                self.annotation_data_home,
                self.search_results_data_home,
            ]
        ):
            raise ValueError("One or more dataset folders do not exist.")
        if not all(
            path.is_dir()
            for path in [
                self.data_home,
                self.sch_data_home,
                self.annotation_data_home,
                self.search_results_data_home,
            ]
        ):
            raise ValueError("One or more dataset folders are not directories.")
        
        self.cloud_annotation_get_folder = Path(config["cloud"]["cloud_annotation_get_folder"]).expanduser()
        self.cloud_annotation_post_folder = Path(config["cloud"]["cloud_annotation_post_folder"]).expanduser()
        if not all(
            path.exists()
            for path in [
                self.cloud_annotation_get_folder,
                self.cloud_annotation_post_folder,
            ]
        ):
            raise ValueError("One or more cloud dataset folders do not exist.")
        if not all(
            path.is_dir()
            for path in [
                self.cloud_annotation_get_folder,
                self.cloud_annotation_post_folder,
            ]
        ):
            raise ValueError("One or more cloud dataset folders are not directories.")


        self.sch = fetch_sch_database(self.sch_data_home)

        cloud_annotation_file = self.cloud_annotation_get_folder / "Annotation.xlsx"
        self.annotation = fetch_annotation(cloud_annotation_file, self.annotation_data_home)
