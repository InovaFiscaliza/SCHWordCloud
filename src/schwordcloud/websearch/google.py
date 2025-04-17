import requests

from .base import BaseSearch


class GoogleSearch(BaseSearch):
    """
    Google Search API wrapper for extracting search results.

    Parameters
    ----------
    credentials : dict
        Dictionary containing the Google Search API credentials. Must include:
        - google_search_api_key: The API key for Google Search API.
        - google_search_endpoint: The endpoint URL for Google Search API.
        - google_search_engine_id: The search engine ID for Google Custom Search.

    """

    def __init__(self, credentials):
        self._api_key = credentials.get("google_search_api_key", None)
        self._endpoint = credentials.get("google_search_endpoint", None)
        self._engine_id = credentials.get("google_search_engine_id", None)

        if not all([self._api_key, self._endpoint, self._engine_id]):
            raise ValueError("Missing required Google Search credentials.")

    @property
    def _source(self):
        # Define the source name for Google Search
        return "GOOGLE"

    @property
    def _fields_of_interest(self):
        # Define the words of interest for Google Search
        return ["title", "snippet", "og:title", "og:description"]

    def _request_search(self, query, count=50):
        """
        Perform a search using the specified query and return the results.

        Parameters
        ----------
        query : str
            The search query.
        count : int, optional, default=50
            The maximum number of search results to retrieve.
        file : str, optional, default=None
            The file path to the search query results file.

        Returns
        -------     
        search_results : dict
            Dictionary containing the search results, including the query itself, 
            status code, extracted text, and raw content.
        """
        
        params = {
            "q": query,
            "key": self._api_key,
            "cx": self._engine_id,
            "count": count,
            "cr": "countryBR",
            "lr": "lang_pt",
        }

        # execute query
        try:
            response = requests.get(self._endpoint, params=params)
            response.raise_for_status()
            content = response.json()
            status_code = response.status_code
        except Exception:
            content = None

        text = ""
        if status_code == 200:
            if items := content.get("items"):
                text = self._extract_text(items)

        search_results = {
            "query": query,
            "status_code": response.status_code,
            "text": text,
            "raw_contents": content,
        }

        return search_results