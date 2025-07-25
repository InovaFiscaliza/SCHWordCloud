import logging
from time import sleep

from config import load_config_file
from datamanager import DataManager
from websearch import GoogleSearch

logger = logging.getLogger(__name__)

SEARCH_RETRIES = 3
SEARCH_ATTEMPT_INTERVAL_TIMEOUT = 5


class SCHWordCloud:
    """
    SCHWordCloud is a class for generating word clouds based on search results.
    It utilizes the Google Search API to retrieve search results and generates word clouds using the WordCloud library.
    """

    def __init__(self, config_file: str = None):

        if isinstance(config_file, str):
            config_file = config_file.strip()
            
        self.config = load_config_file(config_file)
        self.dm = DataManager(self.config)
        self.gs = GoogleSearch(self.config["api_credentials"]["google_search"])

    def _generate_wordcloud(self, search_term: str):
        """
        Generate a word cloud based on the given search term.
        """
        for attempt in range(SEARCH_RETRIES):
            try:
                result = self.gs.request_wordcloud(search_term)
                result_status_code = result["status_code"]
                assert result_status_code == 200
                # add result and format annotation
                if result["wordcloud"]["cloudOfWords"] == "":
                    logger.info(f"Empty wordcloud for '{search_term}'")
                else:
                    logger.info(f"Wordcloud sucessfully generated for '{search_term}'")
                self.dm.add_result(result)
                self.dm.items_to_search.remove(search_term)
                return result_status_code
            except AssertionError as e:
                if attempt < SEARCH_RETRIES - 1:
                    logger.info(
                        f"Attempt {attempt + 1} failed for {search_term}. Response code: {result_status_code}. Retrying..."
                    )
                    sleep(SEARCH_ATTEMPT_INTERVAL_TIMEOUT)
                else:
                    logger.error(
                        f"Could not generate wordcloud for '{search_term}' after {SEARCH_RETRIES} attempts. Stopping wordcloud generation."
                    )
                    return result_status_code

    def generate_wordcloud(self):
        """
        Run the SCHWordCloud.
        """
        logger.info("Starting generating wordclouds...")
        for item in self.dm.items_to_search:
            if self._generate_wordcloud(item) != 200:
                break
        logger.info("Stoped generating wordclouds...")
        self.dm.save_annotation()
        self.dm.save_search_results()
