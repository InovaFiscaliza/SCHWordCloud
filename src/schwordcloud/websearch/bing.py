import requests

from .base import BaseSearch


class BingSearch(BaseSearch):
    """
    Bing Search API wrapper for extracting search results.

    Parameters
    ----------
    credentials : dict
        Dictionary containing the Google Search API credentials. Must include:
        - bing_search_api_key: The API key for Google Search API.
        - bing_search_endpoint: The endpoint URL for Google Search API.

    """

    def __init__(self, credentials):
        self._api_key = credentials.get("bing_search_api_key", None)
        self._endpoint = credentials.get("bing_search_endpoint", None)


        if not all([self._api_key, self._endpoint]):
            raise ValueError("Missing required Bing Search credentials.")

    @property
    def _source(self):
        # Define the source name for Google Search
        return "BING"

    @property
    def _results_key(self):
        # Define the key for the search results in the response
        return "value"

    @property
    def _fields_of_interest(self):
        # Define the words of interest for Google Search
        return ["name", "snippet"]
    
    

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
        headers = {'Ocp-Apim-Subscription-Key': self._api_key}
        params = {
            "q": query,
            # A 2-character country code of the country where the results come from.
            'cc': 'BR',
            # The number of search results to return in the response. 
            # The default is 10 and the maximum value is 50. 
            # the actual number delivered may be less than requested.
            'count': count,
            # The market where the results come from.
            'mkt': 'pt-BR',
            # A comma-delimited list of answers to include in the response.
            'responseFilter': 'Webpages',
        }

        # execute query
        try:
            response = requests.get(self._endpoint, headers=headers, params=params)
            response.raise_for_status()
            content = response.json()
        except Exception:
            content = None
        status_code = response.status_code

        fields = []
        text = ""
        if status_code == 200:
            if items := content.get(self._results_key,[]):
                fields, text = self._extract_text(items)

        search_result = {
            "query": query,
            "status_code": response.status_code,
            "fields": fields,
            "text": text,
            "raw_contents": content,
        }

        return search_result