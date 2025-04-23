from pathlib import Path

import pandas as pd

from .annotation import fetch_annotation
from .sch import fetch_sch_database

pd.options.mode.copy_on_write = True


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

        self.cloud_annotation_get_folder = Path(
            config["cloud"]["cloud_annotation_get_folder"]
        ).expanduser()
        self.cloud_annotation_post_folder = Path(
            config["cloud"]["cloud_annotation_post_folder"]
        ).expanduser()
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

        # check if the local null annotation file exists
        if annotation_config := config.get("annotation"):
            if null_annotation_file := annotation_config.get("null_annotation_file"):
                null_annotation_file = Path(null_annotation_file).expanduser()
            else:
                if not null_annotation_file.exists():
                    raise FileNotFoundError(
                        f"Null annotation file not found: {null_annotation_file}"
                    )
                if not null_annotation_file.is_file():
                    raise NotADirectoryError(
                        f"Null annotation file is not a file: {null_annotation_file}"
                    )
        else:
            null_annotation_file = None
        self.null_annotation_file = null_annotation_file

        self.sch = fetch_sch_database(self.sch_data_home)

        cloud_annotation_file = self.cloud_annotation_get_folder / "Annotation.xlsx"
        self.annotation = fetch_annotation(
            cloud_annotation_file, self.null_annotation_file, self.annotation_data_home
        )

        self.uuid_history = {
            key: value
            for key, value in self.annotation[["Homologação", "ID"]].to_dict("split")[
                "data"
            ]
        }

        self.new_annotation = []

    def get_items_to_search(self, category: int = 2, grace_period: int = 180) -> list:
        """
        Get the items to search from the SCH database.

        """
        df_sch = self.sch
        # Filter categories 1, 2, and 3
        if category in [1, 2, 3]:
            df_sch = df_sch[df_sch["Categoria do Produto"] == category]

        columns_to_keep = ["Número de Homologação", "Data da Homologação"]
        df_sch = df_sch[df_sch["Categoria do Produto"] == category][columns_to_keep]
        df_sch = df_sch.drop_duplicates(subset="Número de Homologação")

        df_annotation = self.annotation
        columns_to_merge = ["Homologação", "DataHora", "ID"]
        df_annotation = df_annotation[columns_to_merge]
        df_annotation.columns = ["Número de Homologação", "Data da Busca", "ID"]
        df_annotation["Número de Homologação"] = df_annotation[
            "Número de Homologação"
        ].apply(lambda numero_homologacao: numero_homologacao.replace("-", ""))

        df_to_search = df_sch.merge(df_annotation, how="left")
        df_to_search = df_to_search[df_to_search["ID"].isna()]
        df_to_search["Dias da Homologação"] = df_to_search["Data da Homologação"].apply(
            lambda data_homologacao: (pd.Timestamp.now() - data_homologacao).days
        )

        if grace_period > 0:
            # Filter the homologations that are older than the grace period
            df_to_search = df_to_search[
                df_to_search["Dias da Homologação"] > grace_period
            ]

        return df_to_search['Número de Homologação'].to_list()
