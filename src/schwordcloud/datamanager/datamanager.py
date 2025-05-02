import json
import random
import uuid
from datetime import datetime
from os import environ

import pandas as pd

from .annotation import (
    fetch_annotation,
    get_uuid_history,
    save_cloud_annotation,
    update_null_annotation,
)
from .sch import fetch_sch_database

pd.options.mode.copy_on_write = True

ANNOTATION_TS_FORMAT = "%d/%m/%Y %H:%M:%S"


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

        self.data_home = config["local_data_home"]["data_home"]
        self.annotation_data_home = config["local_data_home"]["annotation_data_home"]
        self.sch_data_home = config["local_data_home"]["sch_data_home"]
        self.search_results_data_home = config["local_data_home"]["search_results_data_home"]

        self.cloud_annotation_get_folder = config["cloud_data_home"]["cloud_annotation_get_folder"]
        self.cloud_annotation_post_folder = config["cloud_data_home"]["cloud_annotation_post_folder"]

        self.sch = fetch_sch_database(self.sch_data_home)
        self.annotation = fetch_annotation(self.cloud_annotation_get_folder, self.annotation_data_home)
        self.uuid_history = get_uuid_history(self.annotation)

        self._cached_search_results = []
        self._cached_annotation = []


    def get_items_to_search(self, category: int = 2, grace_period: int = 180, shuffle: bool = True) -> list:
        """
        Get the items to search from the SCH database.

        """
        df_sch = self.sch
        # Filter categories 1, 2, and 3
        if category in {1, 2, 3}:
            df_sch = df_sch[df_sch["Categoria do Produto"] == category]

        columns_to_keep = ["Número de Homologação", "Data da Homologação"]
        df_sch = df_sch[columns_to_keep]
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

        items_to_search = df_to_search["Número de Homologação"].to_list()
        if shuffle:
            random.shuffle(items_to_search)

        return items_to_search

    def format_annotation(self, search_result: dict) -> dict:
        """
        Format the search results into a dictionary.

        Parameters
        ----------
        search_result : dict
            The search results to format.

        Returns
        -------
        formatted_results : dict
            The formatted search results.
        """
        wordcloud = search_result["wordcloud"]
        query = wordcloud["searchedWord"]
        datahora = datetime.now().strftime(ANNOTATION_TS_FORMAT)
        computername = environ["COMPUTERNAME"]
        username = environ["USERNAME"]
        homologacao = f"{query[:5]}-{query[5:7]}-{query[7:]}"
        _id = self.uuid_history.get(homologacao, str(uuid.uuid4()))
        atributo = "WordCloud"
        situacao = -1 if wordcloud["cloudOfWords"] == "" else 1
        wordcloud = json.dumps(wordcloud)

        return {
            "ID": _id,
            "DataHora": datahora,
            "Computador": computername,
            "Usuário": username,
            "Homologação": homologacao,
            "Atributo": atributo,
            "Valor": wordcloud,
            "Situação": situacao,
        }
    
    def add_result(self, search_result: dict) -> None:
        """
        Append the new annotation to the list.

        Parameters
        ----------
        search_result : dict
            The search results to append.
        """

        if search_result['status_code'] in [429, 503]:
            # Handle rate limiting or service unavailable
            print("Rate limit exceeded or service unavailable.")
            return False
        
        self._cached_search_results.append(search_result)
        formatted_annotation = self.format_annotation(search_result)
        self._cached_annotation.append(formatted_annotation)
        return True
    
    def save_annotation(self) -> None:
        """
        Save the new annotation to the local file.

        """
        if not self._cached_annotation:
            print("No new annotations to save.")
            return

        annotation = pd.DataFrame(self._cached_annotation)
        
        try:
            # Save the new annotation to the cloud folder
            save_cloud_annotation(annotation, self.cloud_annotation_post_folder)
            # Save the new annotation to the local folder
            update_null_annotation(annotation, self.annotation_data_home)
            # Clear the cached annotation
            self._cached_annotation = []
            print("Annotation saved successfully.")
        except Exception as e:
            print(f"Error saving annotation: {e}")