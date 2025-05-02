"""
Annotation data management module for SchWordCloud.

This module provides functions to fetch, save, and update annotation data used by the word cloud
generation system. It handles both regular annotations and null annotations (for searches with no results).

Functions:
    fetch_annotation: Retrieves annotation data from cloud storage to local storage.
    save_cloud_annotation: Saves annotation data to cloud storage.
    update_null_annotation: Updates the null annotation file with new null annotation data.

Constants:
    ANOTATION_FILE_TS_FORMAT: Time format string used for annotation file timestamps.
"""

from datetime import datetime
from os.path import exists, join
from pathlib import Path
from shutil import copyfile

import pandas as pd

# time format for annotation file
ANOTATION_FILE_TS_FORMAT = "%Y.%m.%d_T%H.%M.%S"


def fetch_annotation(
    cloud_annotation_folder: str, local_annotation_folder: str
) -> pd.DataFrame:
    """Fetch annotation data from cloud storage and combine with null annotations.

    Retrieves annotation files from a cloud folder, copies them to a local folder,
    and returns a DataFrame filtered for WordCloud attributes.

    Parameters
    ----------
    cloud_annotation_folder : str
        Path to the cloud folder containing annotation files.
    local_annotation_folder : str
        Path to the local folder where annotation files will be copied.

    Returns
    -------
    frame -> pd.DataFrame
        A DataFrame containing annotation data filtered for WordCloud attributes,
        combining both main annotation and null annotation files.

    Raises
    ------
    FileNotFoundError
        If the cloud annotation file cannot be found.
    OSError
        If there are issues copying or accessing annotation files.

    """
    cloud_annotation_file = join(cloud_annotation_folder, "Annotation.xlsx")
    cloud_null_annotation_file = join(cloud_annotation_folder, "NullAnnotation.xlsx")

    local_annotation_file = join(local_annotation_folder, "Annotation.xlsx")
    local_null_annotation_file = join(local_annotation_folder, "NullAnnotation.xlsx")

    if not exists(cloud_annotation_file):
        raise FileNotFoundError(
            f"Annotation file not found: {cloud_null_annotation_file}"
        )

    copyfile(cloud_annotation_file, local_annotation_file)
    if not exists(local_annotation_file):
        raise OSError(f"Error fetching annotation file: {cloud_annotation_file}")
    else:
        frame = pd.read_excel(local_annotation_file)

    if exists(cloud_null_annotation_file):
        copyfile(cloud_null_annotation_file, local_null_annotation_file)
        if not exists(local_null_annotation_file):
            raise OSError(
                f"Error fetching null annotation file: {cloud_null_annotation_file}"
            )

    if exists(local_null_annotation_file):
        null_annotation = pd.read_excel(local_null_annotation_file)
        frame = pd.concat([frame, null_annotation], ignore_index=True)

    frame = frame[frame["Atributo"] == "WordCloud"].reset_index(drop=True)

    return frame


def save_cloud_annotation(annotation: pd.DataFrame, cloud_annotation_post_folder: str):
    """Save the annotation file to the specified path.

    Parameters
    ----------
    annotation : DataFrame
        The annotation data to be saved.

    annotation_folder : str
        The path of the folder where the annotation file will be stored.

    Returns
    -------

    """

    annotation = annotation[annotation["Situação"] == 1]
    if annotation.empty:
        print("Nothing to save in annotation file.")
    else:
        annotation_ts = datetime.now().strftime(ANOTATION_FILE_TS_FORMAT)
        annotation_file = f"Annotation_{annotation_ts}.xlsx"
        annotation_file = join(cloud_annotation_post_folder, annotation_file)
        try:
            annotation.to_excel(annotation_file, index=False)
            print(f"Annotation file saved successfully: {annotation_file}")
        except Exception as e:
            raise OSError(f"Error saving annotation file: {annotation_file}") from e


def update_null_annotation(annotation: pd.DataFrame, annotation_data_home: str) -> None:
    """Update the null annotation file with the new null annotation data.

    Parameters
    ----------
    annotation : DataFrame
        The annotation data to be saved.

    null_annotation_file : str or Path
        The path of the null annotation file.

    ignore_not_found : bool, default=False
            If True, the function will not raise an error if the null annotation file is not found.

    """

    df_null_annotation = annotation[annotation["Situação"] == -1]

    if df_null_annotation.empty:
        print("Nothing to update in null annotation file.")
        return

    null_annotation_file = join(annotation_data_home, "AnnotationNull.xlsx")
    if exists(null_annotation_file):
        df_null_annotation_history = pd.read_excel(null_annotation_file)
        df_null_annotation = pd.concat(
            [df_null_annotation_history, df_null_annotation], ignore_index=True
        )
        df_null_annotation = df_null_annotation.drop_duplicates(subset=["ID"])

    try:
        df_null_annotation.to_excel(null_annotation_file, index=False)
        print(f"Null annotation file updated successfully: {null_annotation_file}.")
        return null_annotation_file
    except Exception as e:
        raise OSError(
            f"Error updating null annotation file: {null_annotation_file}"
        ) from e
    

def get_uuid_history(annotation: pd.DataFrame) -> dict:
    """Get the UUID history from the annotation file.
    Parameters
    ----------
    annotation : DataFrame
    The annotation data to be saved.
    Returns
    -------
    uuid_history : dict
    A dictionary containing the UUID history.
    """

    annotation_uuid = annotation[["Homologação", "ID"]].to_dict("split")["data"]
    uuid_history = {key: value for key, value in annotation_uuid}
    return uuid_history
