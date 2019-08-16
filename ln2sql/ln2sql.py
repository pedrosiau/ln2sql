#!/usr/bin/python3
import argparse
import os

import sqlalchemy as sa
import pandas as pd
import re

from .database import Database
from .langConfig import LangConfig
from .parser import Parser
from .stopwordFilter import StopwordFilter
from .thesaurus import Thesaurus
from .constants import Color, without_color

class Ln2sql:
    def __init__(
            self,
            database_path,
            language_path,
            json_output_path=None,
            thesaurus_path=None,
            stopwords_path=None,
            color=False
    ):
        if color == False:
            without_color()

        database = Database()
        self.stopwordsFilter = None

        if thesaurus_path:
            thesaurus = Thesaurus()
            thesaurus.load(thesaurus_path)
            database.set_thesaurus(thesaurus)

        if stopwords_path:
            self.stopwordsFilter = StopwordFilter()
            self.stopwordsFilter.load(stopwords_path)

        database.load(database_path)
        # database.print_me()

        config = LangConfig()
        config.load(language_path)

        self.parser = Parser(database, config)
        self.json_output_path = json_output_path

    def get_query(self, input_sentence):
        queries = self.parser.parse_sentence(input_sentence, self.stopwordsFilter)

        if self.json_output_path:
            self.remove_json(self.json_output_path)
            for query in queries:
                query.print_json(self.json_output_path)

        full_query = ''

        for query in queries:
            full_query += str(query)

        print(full_query)

        result = self.execute_query(full_query)
        print('size of result: ', result.size)
        if (result.empty):
            print('There is no row :/')
        elif result.size == 1:
            print('The result is %s' % result.values[0][0])
        else:
            print(result)

        return result

    def remove_json(self, filename="output.json"):
        if os.path.exists(filename):
            os.remove(filename)

    def execute_query(self, query):
        conn_string = 'postgresql://:@localhost:5432/dex_development'
        engine_prod = sa.create_engine(conn_string)

        query = re.sub(r"\%", "%%", query)

        return pd.read_sql(query, params ={}, con=engine_prod)

