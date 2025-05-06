import json
import logging
import random
import uuid
from datetime import datetime
from os import environ
from os.path import exists, join

import pandas as pd

logger = logging.getLogger(__name__)

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
        self.search_results_data_home = config["local_data_home"][
            "search_results_data_home"
        ]

        self.cloud_annotation_get_folder = config["cloud_data_home"][
            "cloud_annotation_get_folder"
        ]
        self.cloud_annotation_post_folder = config["cloud_data_home"][
            "cloud_annotation_post_folder"
        ]

        self.sch = fetch_sch_database(self.sch_data_home)
        self.annotation = fetch_annotation(
            self.cloud_annotation_get_folder, self.annotation_data_home
        )
        self.uuid_history = get_uuid_history(self.annotation)
        self.items_to_search = self.get_items_to_search()

        self._cached_search_results = []
        self._cached_annotation = []

    def get_items_to_search(
        self, category: int = 2, grace_period: int = 180, shuffle: bool = True
    ) -> list:
        """Retrieve a list of homologation numbers to search based on specified criteria.

        This method filters the SCH database to find homologation numbers that have not been
        previously annotated, applying optional category and age filtering.

        Parameters
        ----------
        category : int, optional
            Product category to filter (1, 2, or 3). Defaults to 2.
        grace_period : int, optional
            Minimum number of days since homologation to include items. Defaults to 180.
        shuffle : bool, optional
            Whether to randomize the order of items to search. Defaults to True.

        Returns
        -------
        list
            A list of homologation numbers to be searched, optionally shuffled.
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
        """Format the search results into a dictionary for annotation.

        Converts a search result dictionary into a structured annotation format,
        including metadata such as timestamp, computer name, username, and
        wordcloud information. Generates a unique ID and determines the
        annotation's status based on the wordcloud content.

        Parameters
        ----------
        search_result : dict
            The search results to format, containing wordcloud information.

        Returns
        -------
        dict
            A formatted annotation dictionary with keys including ID, DataHora,
            Computador, Usuário, Homologação, Atributo, Valor, and Situação.
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
        """Append a new search result and its corresponding annotation to the cached lists.

        Processes an incoming search result, handling potential rate limiting scenarios.
        If the search result is successful, it is added to the search results cache
        and a formatted annotation is created and stored in the annotation cache.

        Parameters
        ----------
        search_result : dict
            A dictionary containing search result data, including status code and wordcloud information.

        Returns
        -------
        bool
            True if the result was successfully added, False if rate limit was exceeded
            or service was unavailable.
        """

        if search_result["status_code"] in [429, 503]:
            # Handle rate limiting or service unavailable
            print("Rate limit exceeded or service unavailable.")
            return False

        self._cached_search_results.append(search_result)
        formatted_annotation = self.format_annotation(search_result)
        self._cached_annotation.append(formatted_annotation)
        return True

    def save_annotation(self) -> None:
        """Save the new annotations to the local and cloud storage.

        This method performs the following actions:
        1. Checks if there are any cached annotations to save
        2. Converts cached annotations to a pandas DataFrame
        3. Saves annotations to the cloud folder
        4. Updates null annotations in the local folder
        5. Clears the cached annotations after successful save

        Prints a success message if annotations are saved, or an error message if an exception occurs.
        """

        if not self._cached_annotation:
            logger.info("No new annotations to save.")
            return

        annotation = pd.DataFrame(self._cached_annotation)

        try:
            # Save the new annotation to the cloud folder
            save_cloud_annotation(annotation, self.cloud_annotation_post_folder)
            # Update the new null annotation to the local folder
            update_null_annotation(annotation, self.annotation_data_home)
            # Clear the cached annotation
            self._cached_annotation = []
        except Exception as e:
            print(f"Error saving annotation: {e}")

    def save_search_results(self) -> None:
        """Save the cached search results to a local Parquet file.

        This method performs the following actions:
        1. Checks if there are any cached search results to save
        2. Reads existing search history from a Parquet file or creates a new DataFrame
        3. Converts raw contents of cached search results to JSON
        4. Appends new search results to the existing search history
        5. Saves the updated search history to the Parquet file
        6. Clears the cached search results after successful save

        Prints a message if no search results are available or if an error occurs during saving.
        """
        logger.info("Saving search results...")
        if not self._cached_search_results:
            logger.info("  No new search results to save.")
            return

        search_history_parquet = join(
            self.search_results_data_home, "search_history.parquet"
        )
        if exists(search_history_parquet):
            df_search_history = pd.read_parquet(search_history_parquet)
        else:
            df_search_history = pd.DataFrame()

        try:
            raw_contents = [
                json.dumps(result["raw_contents"])
                for result in self._cached_search_results
            ]
            df_search_history = pd.concat(
                [
                    df_search_history,
                    pd.DataFrame(raw_contents, columns=["raw_contents"]),
                ]
            )
            df_search_history.to_parquet(search_history_parquet, index=False)
            # Clear the cached search results
            self._cached_search_results = []
        except Exception as e:
            logger.error(f"Error saving search results: {search_history_parquet}")
            raise OSError("Error saving search results") from e
