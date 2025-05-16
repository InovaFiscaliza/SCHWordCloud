import logging
import os
import shutil
import time
import warnings
from datetime import datetime
from os import makedirs
from os.path import exists, getmtime, isdir, join
from tempfile import NamedTemporaryFile
from urllib.error import URLError
from urllib.request import urlretrieve

import pandas as pd

logger = logging.getLogger(__name__)

REMOTE_SCH_DATASET = {
    "url": "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/certificacao_de_produtos",
    "filename": "produtos_certificados.zip",
}


def _download_sch_database(
    target_dir: str,
    n_retries: int = 3,
    delay: int = 1,
) -> str:
    """Helper function to download SCH remote dataset.

    Fetches the SCH dataset from a remote URL and saves it to a specified target directory.
    Implements a robust download process with retry logic for handling network-related errors.

    Handles:
    - Creating target directory if it doesn't exist
    - Downloading file with configurable retry attempts
    - Temporary file management during download
    - Atomic file renaming
    - Error handling for download failures

    Parameters
    ----------
    target_dir : path-like.
        Directory to save the file to. The path to data directory.

    n_retries : int, default=3
        Number of retries when HTTP errors are encountered.

    delay : int, default=1
        Number of seconds between retries.

    Returns
    -------
    local_sch_file_path: str
        Full path of the created file.

    Raises
    ------
    OSError: If file download fails after all retry attempts.
    """

    makedirs(target_dir, exist_ok=True)
    local_sch_file_path = join(target_dir, REMOTE_SCH_DATASET["filename"])

    temp_file = NamedTemporaryFile(
        prefix=REMOTE_SCH_DATASET["filename"] + ".part_", dir=target_dir, delete=False
    )
    temp_file.close()

    try:
        temp_file_path = temp_file.name
        while True:
            try:
                url = REMOTE_SCH_DATASET["url"] + "/" + REMOTE_SCH_DATASET["filename"]
                logger.info(f"Downloading SCH database from {url}.")
                urlretrieve(url, temp_file_path)
                break
            except (URLError, TimeoutError):
                if n_retries == 0:
                    # If no more retries are left, re-raise the caught exception.
                    logger.info(
                        f"Retry downloading from url: {url}"
                    )
                else:
                    logger.error("Error downloading SCH Database file.")
                    raise OSError("Error downloading SCH Database file.")
                n_retries -= 1
                time.sleep(delay)
    except (Exception, KeyboardInterrupt):
        os.unlink(temp_file_path)
        raise

    # The following renaming is atomic whenever temp_file_path and
    # file_path are on the same filesystem. This should be the case most of
    # the time, but we still use shutil.move instead of os.rename in case
    # they are not.
    shutil.move(temp_file_path, local_sch_file_path)
    if not exists(local_sch_file_path):
        logger.error("Error downloading SCH Database file.")
        raise OSError("Error downloading SCH Database file.")

    return local_sch_file_path


"""Load data from SCH dataset, downloading it if necessary.

Retrieves the SCH dataset from a local directory or downloads it if conditions are met.
Supports configurable download behavior, file age tracking, and forced re-downloads.

Parameters
----------
sch_data_home : str or path-like
    Directory path where the SCH dataset is stored or will be downloaded.
download_if_missing : bool, default=True
    If False, raises an error if the dataset is not locally available.
download_grace_period : int, default=180
    Number of days after which the dataset will be automatically re-downloaded.
force_download : bool, default=False
    If True, forces re-downloading the dataset regardless of its age.
n_retries : int, default=3
    Number of download retry attempts in case of network errors.
delay : float, default=1.0
    Delay in seconds between download retry attempts.

Returns
-------
pd.DataFrame
    SCH dataset with 21 columns containing homologation and certification details,
    with date columns converted to datetime and rows with missing homologation numbers removed.

Raises
------
FileNotFoundError
    If the specified data home directory does not exist.
OSError
    If the data home is not a directory or the dataset cannot be downloaded.
"""


def fetch_sch_database(
    sch_data_home: str,
    download_if_missing: bool = True,
    download_grace_period: int = 180,
    force_download: bool = False,
    n_retries: int = 3,
    delay: float = 1.0,
) -> pd.DataFrame:
    """Load data from SCH dataset, downloading it if necessary.

    Retrieves the SCH dataset from a local directory or downloads it if conditions are met.
    Supports configurable download behavior, file age tracking, and forced re-downloads.

    Parameters
    ----------
    sch_data_home : str or path-like
        Specify a download and cache folder for the SCH dataset.

    download_if_missing : bool, default=True
        If False, raise an OSError if the data is not locally available
        instead of trying to download the data from the source site.

    download_grace_period : int, default=180
        Specify the number of days that must pass before re-download
        the file from the internet.

    force_download : bool, default=False
        If True, re-download the file from the internet.

    n_retries : int, default=3
        Number of retries when HTTP errors are encountered.

    delay : float, default=1.0
        Number of seconds between retries.

    Returns
    -------
    frame : DataFrame of shape (n, 21)
        #   columns
        ==  ===========================================
         0  Data da Homologação
         1  Número de Homologação
         2  Nome do Solicitante
         3  CNPJ do Solicitante
         4  Certificado de Conformidade Técnica
         5  Data do Certificado de Conformidade Técnica
         6  Data de Validade do Certificado
         7  Código de Situação do Certificado
         8  Situação do Certificado
         9  Código de Situação do Requerimento
        10  Situação do Requerimento
        11  Nome do Fabricante
        12  Modelo
        13  Nome Comercial
        14  Categoria do Produto
        15  Tipo do Produto
        16  IC_ANTENA
        17  IC_ATIVO
        18  País do Fabricante
        19  CodUIT
        20  CodISO
        ==  ===========================================

    Raises
    ------
    FileNotFoundError
        If the specified data home directory does not exist.
    OSError
        If the data home is not a directory or the dataset cannot be downloaded.
    """

    if not exists(sch_data_home):
        logger.error(f"Local SCH folder not found: {sch_data_home}")
        raise FileNotFoundError(f"Local SCH folder not found: {sch_data_home}")
    if not isdir(sch_data_home):
        logger.error(f"Local SCH folder is not a directory: {sch_data_home}")
        raise OSError(f"Local SCH folder is not a directory: {sch_data_home}")

    local_sch_file_path = join(sch_data_home, REMOTE_SCH_DATASET["filename"])

    if exists(local_sch_file_path):
        # Check if the file is older than the grace period
        sch_file_ctime = datetime.fromtimestamp(getmtime(local_sch_file_path))
        sch_file_age = datetime.now() - sch_file_ctime
        if sch_file_age.days > download_grace_period:
            logger.info(
                f"File {local_sch_file_path} is older than {download_grace_period} days. "
                "Re-downloading the file..."
            )
            _download_sch_database(sch_data_home, n_retries=n_retries, delay=delay)
        elif force_download:
            # If the file is not older than the grace period and force_download is True, download it
            logger.info(
                f"File {local_sch_file_path} is not older than {download_grace_period} days. "
                "Re-downloading the file (forced)..."
            )
            _download_sch_database(sch_data_home, n_retries=n_retries, delay=delay)
            logger.info("Download complete.")
    elif download_if_missing:
        # If the file does not exist and download_if_missing is True, download it
        logger.info(
            f"File {local_sch_file_path} does not exist. Downloading the file..."
        )
        _download_sch_database(sch_data_home, n_retries=n_retries, delay=delay)
        logger.info("Download complete.")
    else:
        # If the file does not exist and download_if_missing is False, raise an error
        logger.error(
            f"File {local_sch_file_path} does not exist. Set download_if_missing=True to download it."
        )
        raise OSError(
            f"File {local_sch_file_path} does not exist. Set download_if_missing=True to download it."
        )

    # Read the file into a DataFrame
    dtype = {
        "Número de Homologação": str,
        "CNPJ do Solicitante": str,
    }
    frame = pd.read_csv(local_sch_file_path, sep=";", dtype=dtype)

    # Convert the date columns to datetime
    frame["Data da Homologação"] = pd.to_datetime(
        frame["Data da Homologação"], format="%d/%m/%Y", errors="coerce"
    )
    frame["Data do Certificado de Conformidade Técnica"] = pd.to_datetime(
        frame["Data do Certificado de Conformidade Técnica"],
        format="%d/%m/%Y",
        errors="coerce",
    )
    frame["Data de Validade do Certificado"] = pd.to_datetime(
        frame["Data de Validade do Certificado"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce",
    )

    # remove rows with null values in the 'Número de Homologação' column
    frame = frame.dropna(subset=["Número de Homologação"])

    return frame
