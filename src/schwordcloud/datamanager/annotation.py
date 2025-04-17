from pathlib import Path
from shutil import copyfile

import pandas as pd


def fetch_annotation(
    cloud_annotation_file: str, local_annotation_folder: str = None
) -> Path:
    """Fetch the annotation file from the specified path.

    Parameters
    ----------
    cloud_annotation_file : str
        The path to the annotation file in the cloud.

    local_annotation_folder : str, default=None
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
    cloud_annotation_file = Path(cloud_annotation_file).expanduser()
    if not cloud_annotation_file.exists():
        raise FileNotFoundError(f"Annotation file not found: {cloud_annotation_file}")

    if local_annotation_folder is not None:
        local_annotation_folder = Path(local_annotation_folder).expanduser()
        if not local_annotation_folder.exists():
            raise FileNotFoundError(
                f"Local annotation folder not found: {local_annotation_folder}"
            )
        if not local_annotation_folder.is_dir():
            raise NotADirectoryError(
                f"Local annotation folder is not a directory: {local_annotation_folder}"
            )

        local_annotation_file =local_annotation_folder / cloud_annotation_file.name
        copyfile(cloud_annotation_file, local_annotation_file)
        if not local_annotation_file.exists():
            raise OSError(f"Error fetching annotation file: {cloud_annotation_file}")
        else:
            frame = pd.read_excel(local_annotation_file)
    else:
        frame = pd.read_excel(cloud_annotation_file)

    return frame
