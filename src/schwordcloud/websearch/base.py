# -*- coding: utf-8 -*-
import json
import re
from collections import Counter
from datetime import datetime

import flatdict
from nltk.corpus import stopwords

# number of words to extract for the word cloud
N_WORDS = 25
# pattern to match words with at least two characters
TOKEN_PATTERN = re.compile(r"\b\w\w+\b")
# version of the word cloud generator
WORD_CLOUD_VERSION = 1
# mode for the word cloud generator
WORD_CLOUD_MODE = "API"
# time format for wordcloud
WORDCLOUD_TS_FORMAT = "%d/%m/%Y %H:%M:%S"


class BaseSearch:
    @property
    def _source(self):
        """
        Return the name of the search engine.
        """
        raise NotImplementedError("Subclasses should implement this property.")

    @property
    def _fields_of_interest(self):
        raise NotImplementedError("Subclasses should implement this property.")

    def _request_search(self, query, count=50):
        """
        Perform a search using the specified query and return the results.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def _extract_text(self, items):
        """Helper function to extract the relevant text from the search results content.

        Parameters
        ----------
        items : list.
            List containing the requested search results from a search engine, eg.:
            customsearch["items"], for Google Custom Search API; or
            searchresponse["webPages"]["value"], for Bing Search API.

        Returns
        -------
        text: str
            Text extracted from the search results target keys.
        """

        flat_content = flatdict.FlatterDict(items, delimiter="__")
        target_keys = [
            key
            for key in flat_content.keys()
            for word in self._fields_of_interest
            if word in key
        ]

        text = []
        fields = []
        for key in target_keys:
            if _text := flat_content.get(key, None):
                text.append(_text)
                fields.append(key.split("__")[-1])

        # remove duplicates
        fields = list(set(fields))

        text = " ".join(text)

        return fields, text

    def _extract_word_counts(self, text=None, n_words=N_WORDS):
        """
        Extracts the most common words from a given text and returns them as a JSON string.

        Parameters
        ----------
        text : str
            The input text from which to extract words.
        n_words : int, optional, default=25
            The number of most common words to extract.

        Returns
        -------
        wordcloud string
            A JSON string containing the most common words and their counts.
        """

        # Check if the text is empty or None
        if not text:
            return ""

        # Remove punctuation and convert to lowercase
        tokens = [
            token for token in TOKEN_PATTERN.findall(text.lower()) if token.isalpha()
        ]
        # Remove stop words
        stop_words = stopwords.words('english') + stopwords.words('portuguese')
        tokens = [token for token in tokens if token not in stop_words]

        # Split the text into words and count occurrences
        words_counter = Counter(tokens)

        # Get the n most common words
        common_words = words_counter.most_common(n_words)
        wordcloud = dict(common_words)
        wordcloud = json.dumps(wordcloud, ensure_ascii=False)

        return wordcloud

    def request_wordcloud(self, query, file=None):
        """
        Perform a search using the specified query and return the results.
        """

        response = self._request_search(query)

        if response["status_code"] == 200:
            text = response["text"]
            word_counts = self._extract_word_counts(text)
        else:
            word_counts = ""

        wordcloud = {
            "metaData": {
                "Version": WORD_CLOUD_VERSION,
                "Source": self._source,
                "Mode": WORD_CLOUD_MODE,
                "Fields": response["fields"],
                "n_words": N_WORDS,
            },
            "searchedWord": query,
            "cloudOfWords": word_counts,
        }

        wordcloud_result = {
            "query": query,
            "status_code": response["status_code"],
            "wordcloud": wordcloud,
            "date_time": datetime.now().strftime(WORDCLOUD_TS_FORMAT),
            "raw_contents": response["raw_contents"],
        }

        return wordcloud_result
