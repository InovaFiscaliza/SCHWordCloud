from .config import load_config_file
from .datamanager import DataManager
from .websearch import GoogleSearch


class SCHWordCloud:
    """
    SCHWordCloud is a class for generating word clouds based on search results.
    It utilizes the Google Search API to retrieve search results and generates word clouds using the WordCloud library.
    """

    def __init__(self, config_file: str = None):
        self.config = load_config_file(config_file)
        self.dm = DataManager(self.config)
        self.gs = GoogleSearch(
            self.config["api_credentials"]["google_search"]["maxwelfreitas"]
        )
