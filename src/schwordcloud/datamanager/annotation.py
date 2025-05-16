"""
Annotation data management module for SCHWordCloud.

This module provides functions to fetch, save, and update annotation data used by the word cloud
generation system. It handles both regular annotations and null annotations (for searches with no results).

Functions:
    fetch_annotation: Retrieves annotation data from cloud storage to local storage.
    save_cloud_annotation: Saves annotation data to cloud storage.
    update_null_annotation: Updates the null annotation file with new null annotation data.

Constants:
    ANOTATION_FILE_TS_FORMAT: Time format string used for annotation file timestamps.
"""

import logging
from datetime import datetime
from os.path import exists, join
from shutil import copyfile

import pandas as pd

logger = logging.getLogger(__name__)

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
    annotation -> pd.DataFrame
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
    cloud_null_annotation_file = join(cloud_annotation_folder, "AnnotationNull.xlsx")

    local_annotation_file = join(local_annotation_folder, "Annotation.xlsx")
    local_null_annotation_file = join(local_annotation_folder, "AnnotationNull.xlsx")

    if not exists(cloud_annotation_file):
        logger.error(f"Annotation file not found: {cloud_annotation_file}")
        raise FileNotFoundError(
            f"Annotation file not found: {cloud_null_annotation_file}"
        )

    copyfile(cloud_annotation_file, local_annotation_file)
    if not exists(local_annotation_file):
        logger.error(f"Error fetching annotation file: {cloud_annotation_file}")
        raise OSError(f"Error fetching annotation file: {cloud_annotation_file}")

    annotation = pd.read_excel(local_annotation_file)

    if exists(cloud_null_annotation_file):
        copyfile(cloud_null_annotation_file, local_null_annotation_file)
        if not exists(local_null_annotation_file):
            logger.error(
                f"Error fetching null annotation file: {cloud_null_annotation_file}"
            )
            raise OSError(
                f"Error fetching null annotation file: {cloud_null_annotation_file}"
            )

    if exists(local_null_annotation_file):
        null_annotation = pd.read_excel(local_null_annotation_file)
        annotation = pd.concat([annotation, null_annotation], ignore_index=True)

    annotation = annotation[annotation["Atributo"] == "WordCloud"].reset_index(
        drop=True
    )

    return annotation


def save_cloud_annotation(annotation: pd.DataFrame, cloud_annotation_post_folder: str):
    """Save annotations with status 1 to a timestamped Excel file in the specified cloud annotation post folder.

    This function handles the process of saving annotation to a timestamped Excel file by:
    - Creating a timestamped filename in the format specified by ANOTATION_FILE_TS_FORMAT
    - Skiping saving if no annotations with status 1 are present
    - Logging a success message upon successful file save

    Parameters
    ----------
    annotation : pd.DataFrame
        The DataFrame containing annotations to be saved, filtered to only include entries with 'Situação' == 1.
    cloud_annotation_post_folder : str
        The directory path where the timestamped annotation file will be saved.

    Raises
    ------
    OSError
        If there is an error writing the annotation file to disk.

    """
    logger.info("Saving annotation file...")
    annotation = annotation[annotation["Situação"] == 1]
    if annotation.empty:
        logger.info("Nothing to save in annotation file.")
    else:
        annotation_ts = datetime.now().strftime(ANOTATION_FILE_TS_FORMAT)
        annotation_file = f"Annotation_{annotation_ts}.xlsx"
        annotation_file = join(cloud_annotation_post_folder, annotation_file)
        try:
            annotation.to_excel(annotation_file, index=False)
            logger.info(f"Annotation file saved successfully: {annotation_file}")
        except Exception as e:
            logger.error(f"Error saving annotation file: {annotation_file}")
            raise OSError(f"Error saving annotation file: {annotation_file}") from e


def update_null_annotation(annotation: pd.DataFrame, annotation_data_home: str) -> None:
    """Update the null annotation file with new null annotations.

    This function handles the process of updating a null annotation Excel file by:
    - Filtering annotations with 'Situação' == -1 as null annotations
    - Appending new null annotations to an existing file
    - Removing duplicate entries based on the 'ID' column

    Parameters
    ----------
    annotation : pd.DataFrame
        The annotation DataFrame containing null annotations to be added.
    annotation_data_home : str
        The directory path where the null annotation file is stored.

    Returns
    -------
    bool
        True if the null annotation file was successfully updated, False if no updates were made.

    Raises
    ------
    OSError
        If there is an error writing to the null annotation file.
    """
    logger.info("Updating null annotation file...")
    null_annotation = annotation[annotation["Situação"] == -1]

    if null_annotation.empty:
        logger.info("Nothing to update in null annotation file.")
        return False
    else:   
        logger.debug(f"Null annotation: {null_annotation}")

    null_annotation_file = join(annotation_data_home, "AnnotationNull.xlsx")
    if exists(null_annotation_file):
        null_annotation_history = pd.read_excel(null_annotation_file)
        null_annotation = pd.concat(
            [null_annotation_history, null_annotation], ignore_index=True
        )
        null_annotation = null_annotation.drop_duplicates(subset=["ID"])

    try:
        null_annotation.to_excel(null_annotation_file, index=False)
        logger.info(
            f"Null annotation file updated successfully: {null_annotation_file}."
        )
        return True
    except Exception as e:
        logger.error(f"Error updating null annotation file: {null_annotation_file}")
        raise OSError(
            f"Error updating null annotation file: {null_annotation_file}"
        ) from e


def get_uuid_history(annotation: pd.DataFrame) -> dict:
    """Get the UUID history from the annotation file.

    Extracts a dictionary mapping homologation status to ID from the annotation DataFrame.

    Parameters
    ----------
    annotation : pd.DataFrame
        The annotation DataFrame containing 'Homologação' and 'ID' columns.

    Returns
    -------
    dict
        A dictionary where keys are homologation values and values are corresponding IDs.
    """
    annotation_uuid = annotation[["Homologação", "ID"]].to_dict("split")["data"]

    return dict(annotation_uuid)
