from datetime import datetime
from pathlib import Path
from shutil import copyfile

import pandas as pd

# time format for annotation file
ANOTATION_FILE_TS_FORMAT = '%Y.%m.%d_T%H.%M.%S'

def fetch_annotation(
    cloud_annotation_file: str | Path, 
    null_annotation_file: str | Path = None, 
    local_annotation_folder: str | Path = None
) -> Path:
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
    cloud_annotation_file = Path(cloud_annotation_file).expanduser()
    if not cloud_annotation_file.exists():
        raise FileNotFoundError(f"Annotation file not found: {cloud_annotation_file}")
    
    if null_annotation_file is not None:
        if not Path(null_annotation_file).exists():
            raise FileNotFoundError(f"Null annotation file not found: {null_annotation_file}")
        if not Path(null_annotation_file).is_file():  
            raise NotADirectoryError(f"Null annotation file is not a file: {null_annotation_file}")
   

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

        local_annotation_file = local_annotation_folder / cloud_annotation_file.name
        copyfile(cloud_annotation_file, local_annotation_file)
        if not local_annotation_file.exists():
            raise OSError(f"Error fetching annotation file: {cloud_annotation_file}")
        else:
            frame = pd.read_excel(local_annotation_file)
    else:
        frame = pd.read_excel(cloud_annotation_file)
    
    if null_annotation_file is not None:
        null_frame = pd.read_excel(null_annotation_file)
        null_frame["Scarab Post Order"] = -1
        frame = pd.concat([frame, null_frame], ignore_index=True)

    frame = frame[frame["Atributo"] == "WordCloud"].reset_index(drop=True)

    return frame

def save_annotation(wordcloud: list, annotation_folder: str | Path) -> Path:
    """Save the annotation file to the specified path.

    Parameters
    ----------
    wordcloud : list of dict
        The wordcloud data to be saved.

    annotation_folder : str or Path
        The path of the folder where the annotation file will be stored.

    Returns
    -------
    local_annotation_file : Path
        The path of the saved annotation file.
    """
    annotation_folder = Path(annotation_folder).expanduser()
    if not annotation_folder.exists():
        raise FileNotFoundError(
            f"Annotation folder not found: {annotation_folder}"
        )
    if not annotation_folder.is_dir():
        raise NotADirectoryError(
            f"Annotation folder is not a directory: {annotation_folder}"
        )
    

    frame = pd.DataFrame(wordcloud)
    annotation_ts = datetime.now().strftime(ANOTATION_FILE_TS_FORMAT)
    annotation_file = f'Annotation_{annotation_ts}.xlsx'
    frame.to_excel(annotation_file, index=False)

    return 
