import tomllib
from os import environ, makedirs
from os.path import exists, expanduser, join
from pathlib import Path


def _get_data_home(data_home=None) -> str:
    """Return the path of the data directory.

    By default the data directory is set to a folder named 'sch_database' in the
    user home folder.

    Alternatively, it can be set by the 'SCH_DATAHOME' environment
    variable or programmatically by giving an explicit folder path.
    The '~' symbol is expanded to the user home folder.

    If the folder does not already exist, it is automatically created.

    Parameters
    ----------
    data_home : str or path-like, default=None
        The path to data directory. If `None`, the default path
        is `%LOCALAPPDATA%/Local/schwordcloud/datasets` or `~/schwordcloud/datasets`.

    Returns
    -------
    data_home: Dictionary of strings containing the paths to the data directories.

    """
    default_data_home = join(environ.get("LOCALAPPDATA", "~"), "schwordcloud", "datasets")
    if data_home is None:
        data_home = environ.get("SCH_DATAHOME", default_data_home)
    data_home = Path(data_home).expanduser()
    if not exists(data_home):
        raise FileNotFoundError(f"Data home not found: {data_home}")
    if not data_home.is_dir():      
        raise NotADirectoryError(f"Data home is not a directory: {data_home}")

    sch_data_home = data_home / "sch"
    search_results_data_home = data_home / "search_results"
    annotation_data_home = data_home / "annotation"

    # Create the directories if they do not exist
    makedirs(sch_data_home, exist_ok=True)
    makedirs(search_results_data_home, exist_ok=True)
    makedirs(annotation_data_home, exist_ok=True)

    # Return the data home path
    return {
        "data_home": str(data_home),
        "sch_data_home": str(sch_data_home),
        "search_results_data_home": str(search_results_data_home),
        "annotation_data_home": str(annotation_data_home),
    }

def _load_api_credentiails(creds_file: str = None) -> dict:
    """
    Load API credentials from a TOML file.

    Parameters
    ----------
    creds_file : str, default = None
        Path to the TOML credentials file. If `None`, the default creds_file
        is `~/creds.ini`.

    Returns
    -------
    dict
        Dictionary containing the API credentials.
    """

    if creds_file is None:
        creds_file = join("~", "creds.ini")
    creds_file = expanduser(creds_file)

    if not exists(creds_file):
        raise FileNotFoundError(f"Credentials file not found: {creds_file}")
    else:
        with open(creds_file, "rb") as f:
            creds = tomllib.load(f)

    return creds

def load_config_file(config_file: str = None) -> dict:
    """
    Load configuration from a TOML file.

    Parameters
    ----------
    config_file : str, default = None
        Path to the TOML configuration file. If `None`, the default config_file
        is `./config.toml`.

    Returns
    -------
    dict
        Dictionary containing the configuration data.
    """

    if config_file is None:
        config_file = join(Path(__file__).parent, "config.toml")

    if not exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)

    # check if the config file has the required keys
    if config.get("cloud", None) is None:
        raise ValueError("Cloud configuration is missing in the config file.")
    else:
        cloud_annotation_get_folder = config["cloud"].get(
            "cloud_annotation_get_folder", None
        )
        cloud_annotation_post_folder = config["cloud"].get(
            "cloud_annotation_post_folder", None
        )
        if not all([cloud_annotation_get_folder, cloud_annotation_post_folder]):
            raise ValueError(
                "GET/POST cloud configuration is missing in the config file."
            )
        else:
            if not all(
                [
                    exists(cloud_annotation_get_folder),
                    exists(cloud_annotation_post_folder),
                ]
            ):
                raise FileNotFoundError(
                    "GET/POST cloud configuration folders not found. Check config file."
                )

    config["datasets"] = _get_data_home(config.get("datasets", None))

    if credentials := config.get("credentials", None):
        creds_file = credentials.get("creds_file", None)
    else:
        creds_file = None
    creds = _load_api_credentiails(creds_file)
    config["credentials"] = creds

    return config
