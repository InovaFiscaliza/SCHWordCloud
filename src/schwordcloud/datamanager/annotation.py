from datetime import datetime
from os.path import exists, join
from shutil import copyfile

import pandas as pd

# time format for annotation file
ANOTATION_FILE_TS_FORMAT = "%Y.%m.%d_T%H.%M.%S"


def fetch_annotation(
    cloud_annotation_folder: str, local_annotation_folder: str
) -> pd.DataFrame:
    """Fetch the annotation file from the specified path.

    Parameters
    ----------
    cloud_annotation_file : str or Path
        The path to the annotation file in the cloud.

    null_annotation_file : str or Path, default=None
        The path to the null annotation file. If None, the function will not use a null annotation file.
        If provided, the function will use this file to fill in values previously searched  with no results in the annotation file.

    local_annotation_folder : str or Path, default=None
        The path of the local folder where the annotation file will be stored.
        If None, the function will open the annotation file directly from the cloud path.

    Returns
    -------
    frame : DataFrame of shape (n, 9)

       columns
    =  =================
    0  ID
    1  DataHora
    2  Computador
    3  Usuário
    4  Homologação
    5  Atributo
    6  Valor
    7  Situação
    8  Scarab Post Order
    =  =================
    """
    cloud_annotation_file = join(cloud_annotation_folder, "Annotation.xlsx")
    cloud_null_annotation_file = join(cloud_annotation_folder, "NullAnnotation.xlsx")
    
    local_annotation_file = join(local_annotation_folder, "Annotation.xlsx")
    local_null_annotation_file = join(local_annotation_folder, "NullAnnotation.xlsx")

    if not exists(cloud_annotation_file): 
        raise FileNotFoundError(f"Annotation file not found: {cloud_null_annotation_file}")

    copyfile(cloud_annotation_file, local_annotation_file)
    if not exists(local_annotation_file):
        raise OSError(f"Error fetching annotation file: {cloud_annotation_file}")
    else:
            frame = pd.read_excel(local_annotation_file)

    if exists(cloud_null_annotation_file):
        copyfile(cloud_null_annotation_file, local_null_annotation_file)
        if not exists(local_null_annotation_file):
            raise OSError(f"Error fetching null annotation file: {cloud_null_annotation_file}")
        
    if exists(local_null_annotation_file):
        null_annotation = pd.read_excel(local_null_annotation_file)
        frame = pd.concat([frame, null_annotation], ignore_index=True) 

    frame = frame[frame["Atributo"] == "WordCloud"].reset_index(drop=True)

    return frame


def save_cloud_annotation(
    annotation: pd.DataFrame, cloud_annotation_post_folder: str
):
    """Save the annotation file to the specified path.

    Parameters
    ----------
    annotation : DataFrame
        The annotation data to be saved.

    annotation_folder : str or Path
        The path of the folder where the annotation file will be stored.

    Returns
    -------
    local_annotation_file : Path
        The path of the saved annotation file.
    """
    # annotation_folder = Path(cloud_annotation_post_folder).expanduser()
    # if not annotation_folder.exists():
    #     raise FileNotFoundError(f"Annotation folder not found: {annotation_folder}")
    # if not annotation_folder.is_dir():
    #     raise NotADirectoryError(
    #         f"Annotation folder is not a directory: {annotation_folder}"
    #     )

    # annotation = annotation[annotation["Situação"] == 1]
    # annotation_ts = datetime.now().strftime(ANOTATION_FILE_TS_FORMAT)
    # annotation_file = f"Annotation_{annotation_ts}.xlsx"
    # annotation_file = annotation_folder / annotation_file
    # annotation.to_excel(annotation_file, index=False)

    return


def update_null_annotation(
    annotation: pd.DataFrame, null_annotation_file: str
) -> None:
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

    # null_annotation_file = Path(null_annotation_file).expanduser()
    # if not null_annotation_file.exists():
    #     raise FileNotFoundError(
    #         f"Null annotation file not found: {null_annotation_file}"
    #     )
    # if not null_annotation_file.is_file():
    #     raise NotADirectoryError(
    #         f"Null annotation file is not a file: {null_annotation_file}"
    #     )

    # null_annotation_from_file = pd.read_excel(null_annotation_file)
    # null_annotation = annotation[annotation["Situação"] == -1]
    # null_annotation = pd.concat(
    #     [null_annotation_from_file, null_annotation], ignore_index=True
    # )
    # null_annotation.to_excel(null_annotation_file, index=False)
    pass
