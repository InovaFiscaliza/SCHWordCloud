import logging
import tomllib
from os import environ, makedirs
from os.path import dirname, exists, expanduser, isdir, join

import nltk

logger = logging.getLogger(__name__)


def _get_local_data_home(data_home=None) -> dict:
    """Determine and create local data home directories for schwordcloud datasets.

    Sets up the local directory structure for storing schwordcloud-related data files,
    with configurable base directory and automatic directory creation as ilustrated:

    schwordcloud/                           # The main folder for the schwordcloud data_home
    └── datasets/                           # The data home folder -> data_home
        ├── annotation/                     # Contains the .xlsx annotation files -> annotation_data_home
        |   ├── Annotation.xlsx             # A copy of the cloud annotation file fetched from the cloud -> local_annotation_file
        |   └── AnnotationNull.xlsx         # The null annotation file generated by the user -> null_annotation_file
        ├── sch/                            # Contains the SCH database file fetched from the internet -> sch_data_home
        |   └── produtos_certificados.zip   # SCH database file fetched from the internet -> local_sch_file
        └── search_results/                 # Contains the JSON files with search results data -> search_results_data_home

    The function supports setting the data home via environment variable, explicit path,
    or using default system-specific locations. It ensures required subdirectories exist
    for annotations, SCH database, and search results.

    By default the data directory is set to a folder named 'schwordcloud/datasets' in the
    user home folder.
    Alternatively, it can be set by the 'SCH_DATAHOME' environment variable
    or programmatically by giving an explicit folder path.
    The '~' symbol is expanded to the user home folder.

    If the folders does not already exist, it is automatically created.

    Parameters
    ----------
    data_home : str or path-like, default=None
        The path to data directory. If `None`, the default path
        is `%LOCALAPPDATA%/schwordcloud/datasets` or `~/schwordcloud/datasets`.

    Returns
    -------
    local_data_home: Dictionary of strings containing the paths to the data directories.

        local_data_home = {
            "data_home": str = data_home,
            "annotation_data_home": str = annotation_data_home,
            "local_annotation_file": str = local_annotation_file,
            "null_annotation_file": str = null_annotation_file,
            "sch_data_home": str = sch_data_home,
            "local_sch_file": str = local_sch_file,
            "search_results_data_home": str = search_results_data_home,
        }

    """
    default_data_home = join(
        environ.get("LOCALAPPDATA", "~"), "schwordcloud", "datasets"
    )
    if data_home is None:
        data_home = environ.get("SCH_DATAHOME", default_data_home)
    
    makedirs(data_home, exist_ok=True)

    if not exists(data_home):
        logger.error(f"Data home not found: {data_home}")
        raise FileNotFoundError(f"Data home not found: {data_home}")
    if not isdir(data_home):
        logger.error(f"Data home is not a directory: {data_home}")
        raise NotADirectoryError(f"Data home is not a directory: {data_home}")

    data_home = expanduser(data_home)
    annotation_data_home = join(data_home, "annotation")
    sch_data_home = join(data_home, "sch")
    search_results_data_home = join(data_home, "search_results")

    # Create the directories if they do not exist
    makedirs(annotation_data_home, exist_ok=True)
    makedirs(sch_data_home, exist_ok=True)
    makedirs(search_results_data_home, exist_ok=True)

    logger.info("Local data home setup: %s", data_home)
    logger.info("Annotation data home: %s", annotation_data_home)
    logger.info("SCH data home: %s", sch_data_home)
    logger.info("Search results data home: %s", search_results_data_home)

    return {
        "data_home": data_home,
        "annotation_data_home": annotation_data_home,
        "sch_data_home": sch_data_home,
        "search_results_data_home": search_results_data_home,
    }


def _get_cloud_data_home(config_file: str = None) -> dict:
    """Setup cloud datasets folders from a TOML file.

    Cloud datasets folders are used to fetch current annotations and post new annotations for further consolidation.
    If the folders path provided in the config file do not exist, a FileNotFoundError is raised.

    Parameters
    ----------
    config_file: str, default = None
        Path to the TOML configuration file. If `None`, a FileNotFoundError is raised.
        The folders shold be set in the config file a form of a table (collections of key/value pairs):

        [cloud]
        cloud_annotation_get_folder = "path/to/cloud/annotation/get/folder"
        cloud_annotation_post_folder = "path/to/cloud/annotation/post/folder"

    Returns
    -------
    cloud_data_home: Dictionary of strings containing the paths to the data directories.

        cloud_data_home = {
            "cloud_annotation_get_folder": str = cloud_annotation_get_folder,
            "cloud_annotation_post_folder": str: = cloud_annotation_post_folder,
        }

    """

    # open the config file and load the cloud configuration
    if config_file is None:
        logger.error("Config file is not provided.")
        raise ValueError("Config file is not provided.")
    config_file = expanduser(config_file)

    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    # check if the config file has the required keys
    if config.get("cloud", None) is None:
        logger.error("Cloud configuration is missing in the config file.")
        raise ValueError("Cloud configuration is missing in the config file.")
    cloud_annotation_get_folder = config["cloud"].get(
        "cloud_annotation_get_folder", None
    )
    cloud_annotation_post_folder = config["cloud"].get(
        "cloud_annotation_post_folder", None
    )

    if not all([cloud_annotation_get_folder, cloud_annotation_post_folder]):
        logger.error("GET/POST cloud configuration is missing in the config file.")
        raise ValueError("GET/POST cloud configuration is missing in the config file.")
    if not all(
        [
            exists(cloud_annotation_get_folder),
            exists(cloud_annotation_post_folder),
        ]
    ):
        logger.error(
            "GET/POST cloud configuration folders not found. Check config file."
        )
        raise FileNotFoundError(
            "GET/POST cloud configuration folders not found. Check config file."
        )
    logger.info("Cloud annotation folders found.")
    logger.info(f"Cloud annotation get folder: {cloud_annotation_get_folder}")
    logger.info(f"Cloud annotation post folder: {cloud_annotation_post_folder}")

    return {
        "cloud_annotation_get_folder": cloud_annotation_get_folder,
        "cloud_annotation_post_folder": cloud_annotation_post_folder,
    }


def _get_api_credentiails(config_file: str = None) -> dict:
    """Load API credentials from a TOML file.

    Parameters
    ----------
    config_file: str, default = None
        Path to the TOML configuration file. If `None`, a FileNotFoundError is raised.

        The credentials file path should be set in the config file a form of a table (collections of key/value pairs):

        [credentials]
        credentials_file = "path/to/credentials/file"

        If the credentials table is not provided, the default credentials file path is `~/credentials.toml`.
        The credentials file should be a well formated TOML document.

    Returns
    -------
    dict
        Dictionary containing the API credentials as designed in credentials TOML document.
    """

    # open the config file and load the cloud configuration
    if config_file is None:
        logger.error("Config file was not provided.")
        raise ValueError("Config file was not provided.")
    config_file = expanduser(config_file)

    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    credentials_file = config.get("credentials_file", None)
    
    if credentials_file is None:
        credentials_file = join("~", "credentials.toml")
    credentials_file = expanduser(credentials_file)

    if not exists(credentials_file):
        logger.error(f"Credentials file not found: {credentials_file}")
        raise FileNotFoundError(f"Credentials file not found: {credentials_file}")

    logger.info(f"Credentials file found: {credentials_file}")
    with open(credentials_file, "rb") as f:
        _credentials = tomllib.load(f)

    credentials = _credentials.get("credentials")
    if not credentials:
        logger.error(f"Credentials section not found in file: {credentials_file}")
        raise KeyError(f"Credentials section not found in file: {credentials_file}")

    return credentials


def load_config_file(config_file: str = None) -> dict:
    """
    Load configuration from a TOML file.

    Parameters
    ----------
    config_file : str, default = None
        Path to the TOML configuration file. If `None`, the default config_file
        is `./config.toml`.

    The config file should contain the path for local data home folder, cloud annotation folder
    and credentials files in the following format:

        data_home = "path/to/data/home/folder"

        [cloud]
        cloud_annotation_get_folder = "path/to/cloud/annotation/get/folder"
        cloud_annotation_post_folder = "path/to/cloud/annotation/post/folder"

        [credentials]
        credentials_file = "path/to/credentials/file"

    Returns
    -------
    dict
        Dictionary containing the configuration data.
    """

    if config_file is None:
        config_file = join(dirname(__file__), "config.toml")

    if not exists(config_file.strip()):
        logger.error(f"Config file not found: {config_file}")
        raise FileNotFoundError(f"Config file not found: {config_file}")
    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    # load configuration
    data_home = config.get("data_home", None)

    # load search parameters
    search_params = config.get("search_params", None)

    # download NLTK data if not available
    nltk.download("stopwords", quiet=True)

    return {
        "local_data_home": _get_local_data_home(data_home),
        "cloud_data_home": _get_cloud_data_home(config_file),
        "api_credentials": _get_api_credentiails(config_file),
        "search_params": search_params,
    }
