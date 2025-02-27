import re
import string
import sys
import unicodedata
import functools
from threading import Thread

from .parsingException import ParsingException
from .query import *


class SelectParser(Thread):
    def __init__(self, columns_of_select, tables_of_from, phrase, count_keywords, sum_keywords, average_keywords,
                 max_keywords, min_keywords, distinct_keywords, database_dico, database_object):
        Thread.__init__(self)
        self.select_objects = []
        self.columns_of_select = columns_of_select
        self.tables_of_from = tables_of_from
        self.phrase = phrase
        self.count_keywords = count_keywords
        self.sum_keywords = sum_keywords
        self.average_keywords = average_keywords
        self.max_keywords = max_keywords
        self.min_keywords = min_keywords
        self.distinct_keywords = distinct_keywords
        self.database_dico = database_dico
        self.database_object = database_object

    def get_tables_of_column(self, column):
        tmp_table = []
        for table in self.database_dico:
            if column in self.database_dico[table]:
                tmp_table.append(table)
        return tmp_table

    def get_column_name_with_alias_table(self, column, table_of_from):
        one_table_of_column = self.get_tables_of_column(column)[0]
        tables_of_column = self.get_tables_of_column(column)
        if table_of_from in tables_of_column:
            return str(table_of_from) + '.' + str(column)
        else:
            return str(one_table_of_column) + '.' + str(column)

    def uniquify(self, list):
        already = []
        for element in list:
            if element not in already:
                already.append(element)
        return already

    def run(self):
        for table_of_from in self.tables_of_from:  # for each query
            self.select_object = Select()
            is_count = False
            self.columns_of_select = self.uniquify(self.columns_of_select)
            number_of_select_column = len(self.columns_of_select)

            if number_of_select_column == 0:
                select_type = []
                for count_keyword in self.count_keywords:
                    # if count_keyword in (word.lower() for word in self.phrase):
                    # so that it matches multiple words too in keyword synonymn in .lang rather than just single word for COUNT
                    # (e.g. QUERY-> "how many city there are in which the employe name is aman ?" )
                    lower_self_phrase = ' '.join(word.lower() for word in self.phrase)
                    if count_keyword in lower_self_phrase:
                        select_type.append('COUNT')

                self.select_object.add_column(None, self.uniquify(select_type))
            else:
                select_phrases = []
                previous_index = 0

                for i in range(0, len(self.phrase)):
                    for column_name in self.columns_of_select:
                        if (self.phrase[i] == column_name) or (
                                    self.phrase[i] in self.database_object.get_column_with_this_name(column_name).equivalences):
                            select_phrases.append(self.phrase[previous_index:i + 1])
                            previous_index = i + 1

                select_phrases.append(self.phrase[previous_index:])

                for i in range(0, len(select_phrases)):  # for each select phrase (i.e. column processing)
                    select_type = []

                    phrase = [word.lower() for word in select_phrases[i]]

                    for keyword in self.average_keywords:
                        if keyword in phrase:
                            select_type.append('AVG')
                    for keyword in self.count_keywords:
                        if keyword in phrase:
                            select_type.append('COUNT')
                    for keyword in self.max_keywords:
                        if keyword in phrase:
                            select_type.append('MAX')
                    for keyword in self.min_keywords:
                        if keyword in phrase:
                            select_type.append('MIN')
                    for keyword in self.sum_keywords:
                        if keyword in phrase:
                            select_type.append('SUM')
                    for keyword in self.distinct_keywords:
                        if keyword in phrase:
                            select_type.append('DISTINCT')

                    if (i != len(select_phrases) - 1):
                        column = self.get_column_name_with_alias_table(self.columns_of_select[i], table_of_from)
                        self.select_object.add_column(column, self.uniquify(select_type))

            self.select_objects.append(self.select_object)

    def join(self):
        Thread.join(self)
        return self.select_objects


class FromParser(Thread):
    def __init__(self, tables_of_from, columns_of_select, columns_of_where, database_object):
        Thread.__init__(self)
        self.queries = []
        self.tables_of_from = tables_of_from
        self.columns_of_select = columns_of_select
        self.columns_of_where = columns_of_where

        self.database_object = database_object
        self.database_dico = self.database_object.get_tables_into_dictionary()

    def get_tables_of_column(self, column):
        tmp_table = []
        for table in self.database_dico:
            if column in self.database_dico[table]:
                tmp_table.append(table)
        return tmp_table

    def intersect(self, a, b):
        return list(set(a) & set(b))

    def difference(self, a, b):
        differences = []
        for _list in a:
            if _list not in b:
                differences.append(_list)
        return differences

    def is_direct_join_is_possible(self, table_src, table_trg):
        fk_column_of_src_table = self.database_object.get_foreign_keys_of_table(table_src)
        fk_column_of_trg_table = self.database_object.get_foreign_keys_of_table(table_trg)

        for column in fk_column_of_src_table:
            if column.is_foreign()['foreign_table'] == table_trg:
                return [(table_src, column.name), (table_trg, column.is_foreign()['foreign_column'])]

        for column in fk_column_of_trg_table:
            if column.is_foreign()['foreign_table'] == table_src:
                return [(table_src, column.is_foreign()['foreign_column']), (table_trg, column.name)]

                # pk_table_src = self.database_object.get_primary_key_names_of_table(table_src)
                # pk_table_trg = self.database_object.get_primary_key_names_of_table(table_trg)
                # match_pk_table_src_with_table_trg = self.intersect(pk_table_src, self.database_dico[table_trg])
                # match_pk_table_trg_with_table_src = self.intersect(pk_table_trg, self.database_dico[table_src])

                # if len(match_pk_table_src_with_table_trg) >= 1:
                #     return [(table_trg, match_pk_table_src_with_table_trg[0]), (table_src, match_pk_table_src_with_table_trg[0])]
                # elif len(match_pk_table_trg_with_table_src) >= 1:
                # return [(table_trg, match_pk_table_trg_with_table_src[0]),
                # (table_src, match_pk_table_trg_with_table_src[0])]

    def get_all_direct_linked_tables_of_a_table(self, table_src):
        links = []
        for table_trg in self.database_dico:
            if table_trg != table_src:
                link = self.is_direct_join_is_possible(table_src, table_trg)
                if link is not None:
                    links.append(link)
        return links

    def is_join(self, historic, table_src, table_trg):
        historic = historic
        links = self.get_all_direct_linked_tables_of_a_table(table_src)

        differences = []
        for join in links:
            if join[0][0] not in historic:
                differences.append(join)
        links = differences

        for join in links:
            if join[1][0] == table_trg:
                return [0, join]

        path = []
        historic.append(table_src)

        for join in links:
            result = [1, self.is_join(historic, join[1][0], table_trg)]
            if result[1] != []:
                if result[0] == 0:
                    path.append(result[1])
                    path.append(join)
                else:
                    path = result[1]
                    path.append(join)
        return path

    def get_link(self, table_src, table_trg):
        path = self.is_join([], table_src, table_trg)
        if len(path) > 0:
            path.pop(0)
            path.reverse()
        return path

    def unique(self, _list):
        return [list(x) for x in set(tuple(x) for x in _list)]

    def unique_ordered(self, _list):
        frequency = []
        for element in _list:
            if element not in frequency:
                frequency.append(element)
        return frequency

    def run(self):
        self.queries = []

        for table_of_from in self.tables_of_from:
            links = []
            query = Query()
            query.set_from(From(table_of_from))
            join_object = Join()

            for column in self.columns_of_select:
                if column not in self.database_dico[table_of_from]:
                    foreign_table = self.get_tables_of_column(column)[0]
                    join_object.add_table(foreign_table)
                    link = self.get_link(table_of_from, foreign_table)

                    if not link:
                        self.queries = ParsingException(
                            "There is at least column `" + column + "` that is unreachable from table `" + table_of_from.upper() + "`!")
                        return
                    else:
                        links.extend(link)

            for column in self.columns_of_where:
                if column not in self.database_dico[table_of_from]:
                    foreign_table = self.get_tables_of_column(column)[0]
                    join_object.add_table(foreign_table)
                    link = self.get_link(table_of_from, foreign_table)

                    if not link:
                        self.queries = ParsingException(
                            "There is at least column `" + column + "` that is unreachable from table `" + table_of_from.upper() + "`!")
                        return
                    else:
                        links.extend(link)

            join_object.set_links(self.unique_ordered(links))
            query.set_join(join_object)
            self.queries.append(query)

    def join(self):
        Thread.join(self)
        return self.queries


class WhereParser(Thread):
    def __init__(self, phrases, tables_of_from, columns_of_values_of_where, count_keywords, sum_keywords,
                 average_keywords, max_keywords, min_keywords, greater_keywords, less_keywords, between_keywords,
                 negation_keywords, junction_keywords, disjunction_keywords, like_keywords, distinct_keywords,
                 database_dico, database_object):
        Thread.__init__(self)
        self.where_objects = []
        self.phrases = phrases
        self.tables_of_from = tables_of_from
        self.columns_of_values_of_where = columns_of_values_of_where
        self.count_keywords = count_keywords
        self.sum_keywords = sum_keywords
        self.average_keywords = average_keywords
        self.max_keywords = max_keywords
        self.min_keywords = min_keywords
        self.greater_keywords = greater_keywords
        self.less_keywords = less_keywords
        self.between_keywords = between_keywords
        self.negation_keywords = negation_keywords
        self.junction_keywords = junction_keywords
        self.disjunction_keywords = disjunction_keywords
        self.like_keywords = like_keywords
        self.distinct_keywords = distinct_keywords
        self.database_dico = database_dico
        self.database_object = database_object

    def get_tables_of_column(self, column):
        tmp_table = []
        for table in self.database_dico:
            if column in self.database_dico[table]:
                tmp_table.append(table)
        return tmp_table

    def get_column_name_with_alias_table(self, column, table_of_from):
        one_table_of_column = self.get_tables_of_column(column)[0]
        tables_of_column = self.get_tables_of_column(column)
        if table_of_from in tables_of_column:
            return str(table_of_from) + '.' + str(column)
        else:
            return str(one_table_of_column) + '.' + str(column)

    def intersect(self, a, b):
        return list(set(a) & set(b))

    def predict_operation_type(self, previous_column_offset, current_column_offset):
        interval_offset = list(range(previous_column_offset, current_column_offset))
        if (len(self.intersect(interval_offset, self.count_keyword_offset)) >= 1):
            return 'COUNT'
        elif (len(self.intersect(interval_offset, self.sum_keyword_offset)) >= 1):
            return 'SUM'
        elif (len(self.intersect(interval_offset, self.average_keyword_offset)) >= 1):
            return 'AVG'
        elif (len(self.intersect(interval_offset, self.max_keyword_offset)) >= 1):
            return 'MAX'
        elif (len(self.intersect(interval_offset, self.min_keyword_offset)) >= 1):
            return 'MIN'
        else:
            return None

    def predict_operator(self, current_column_offset, next_column_offset):
        interval_offset = list(range(current_column_offset, next_column_offset))

        if (len(self.intersect(interval_offset, self.negation_keyword_offset)) >= 1) and (
                    len(self.intersect(interval_offset, self.greater_keyword_offset)) >= 1):
            return '<'
        elif (len(self.intersect(interval_offset, self.negation_keyword_offset)) >= 1) and (
                    len(self.intersect(interval_offset, self.less_keyword_offset)) >= 1):
            return '>'
        if (len(self.intersect(interval_offset, self.less_keyword_offset)) >= 1):
            return '<'
        elif (len(self.intersect(interval_offset, self.greater_keyword_offset)) >= 1):
            return '>'
        elif (len(self.intersect(interval_offset, self.between_keyword_offset)) >= 1):
            return 'BETWEEN'
        elif (len(self.intersect(interval_offset, self.negation_keyword_offset)) >= 1):
            return '!='
        elif (len(self.intersect(interval_offset, self.like_keyword_offset)) >= 1):
            return 'ILIKE'
        else:
            return '='

    def predict_junction(self, previous_column_offset, current_column_offset):
        interval_offset = list(range(previous_column_offset, current_column_offset))
        junction = 'AND'
        if (len(self.intersect(interval_offset, self.disjunction_keyword_offset)) >= 1):
            return 'OR'
        elif (len(self.intersect(interval_offset, self.junction_keyword_offset)) >= 1):
            return 'AND'

        first_encountered_junction_offset = -1
        first_encountered_disjunction_offset = -1

        for offset in self.junction_keyword_offset:
            if offset >= current_column_offset:
                first_encountered_junction_offset = offset
                break

        for offset in self.disjunction_keyword_offset:
            if offset >= current_column_offset:
                first_encountered_disjunction_offset = offset
                break

        if first_encountered_junction_offset >= first_encountered_disjunction_offset:
            return 'AND'
        else:
            return 'OR'

    def uniquify(self, list):
        already = []
        for element in list:
            if element not in already:
                already.append(element)
        return already

    def run(self):
        number_of_where_columns = 0
        columns_of_where = []
        offset_of = {}
        column_offset = []
        self.count_keyword_offset = []
        self.sum_keyword_offset = []
        self.average_keyword_offset = []
        self.max_keyword_offset = []
        self.min_keyword_offset = []
        self.greater_keyword_offset = []
        self.less_keyword_offset = []
        self.between_keyword_offset = []
        self.junction_keyword_offset = []
        self.disjunction_keyword_offset = []
        self.negation_keyword_offset = []
        self.like_keyword_offset = []

        for phrase in self.phrases:
            phrase_offset_string = ''
            for i in range(0, len(phrase)):
                for table_name in self.database_dico:
                    columns = self.database_object.get_table_by_name(table_name).get_columns()
                    for column in columns:
                        if (phrase[i] == column.name) or (phrase[i] in column.equivalences):
                            number_of_where_columns += 1
                            columns_of_where.append(column.name)
                            offset_of[phrase[i]] = i
                            column_offset.append(i)
                            break
                    else:
                        continue
                    break

                phrase_keyword = str(phrase[i]).lower()  # for robust keyword matching
                phrase_offset_string += phrase_keyword + " "

                for keyword in self.count_keywords:
                    if keyword in phrase_offset_string :    # before the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.count_keyword_offset.append(i)

                for keyword in self.sum_keywords:
                    if keyword in phrase_offset_string :    # before the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.sum_keyword_offset.append(i)

                for keyword in self.average_keywords:
                    if keyword in phrase_offset_string :    # before the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.average_keyword_offset.append(i)

                for keyword in self.max_keywords:
                    if keyword in phrase_offset_string :    # before the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.max_keyword_offset.append(i)

                for keyword in self.min_keywords:
                    if keyword in phrase_offset_string :    # before the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.min_keyword_offset.append(i)

                for keyword in self.greater_keywords:
                    if keyword in phrase_offset_string :    # after the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.greater_keyword_offset.append(i)

                for keyword in self.less_keywords:
                    if keyword in phrase_offset_string :    # after the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.less_keyword_offset.append(i)

                for keyword in self.between_keywords:
                    if keyword in phrase_offset_string :    # after the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.between_keyword_offset.append(i)

                for keyword in self.junction_keywords:
                    if keyword in phrase_offset_string :    # after the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.junction_keyword_offset.append(i)

                for keyword in self.disjunction_keywords:
                    if keyword in phrase_offset_string :    # after the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.disjunction_keyword_offset.append(i)

                for keyword in self.negation_keywords:
                    if keyword in phrase_offset_string :
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.negation_keyword_offset.append(i)

                for keyword in self.like_keywords:
                    if keyword in phrase_offset_string :    # after the column
                        if (phrase_offset_string.find(keyword) + len(keyword) + 1 == len(phrase_offset_string) ) :
                            self.like_keyword_offset.append(i)


        for table_of_from in self.tables_of_from:
            where_object = Where()
            for i in range(0, len(column_offset)):
                current = column_offset[i]

                if i == 0:
                    previous = 0
                else:
                    previous = column_offset[i - 1]

                if i == (len(column_offset) - 1):
                    _next = 999
                else:
                    _next = column_offset[i + 1]

                junction = self.predict_junction(previous, current)
                column = self.get_column_name_with_alias_table(columns_of_where[i], table_of_from)
                operation_type = self.predict_operation_type(previous, current)

                if len(self.columns_of_values_of_where) > i:
                    value = self.columns_of_values_of_where[
                        len(self.columns_of_values_of_where) - len(columns_of_where) + i]
                else:
                    value = 'OOV'  # Out Of Vocabulary: default value

                operator = self.predict_operator(current, _next)
                where_object.add_condition(junction, Condition(column, operation_type, operator, value))
            self.where_objects.append(where_object)

    def join(self):
        Thread.join(self)
        return self.where_objects


class GroupByParser(Thread):
    def __init__(self, phrases, tables_of_from, database_dico, database_object):
        Thread.__init__(self)
        self.group_by_objects = []
        self.phrases = phrases
        self.tables_of_from = tables_of_from
        self.database_dico = database_dico
        self.database_object = database_object

    def get_tables_of_column(self, column):
        tmp_table = []
        for table in self.database_dico:
            if column in self.database_dico[table]:
                tmp_table.append(table)
        return tmp_table

    def get_column_name_with_alias_table(self, column, table_of_from):
        one_table_of_column = self.get_tables_of_column(column)[0]
        tables_of_column = self.get_tables_of_column(column)
        if table_of_from in tables_of_column:
            return str(table_of_from) + '.' + str(column)
        else:
            return str(one_table_of_column) + '.' + str(column)

    def run(self):
        for table_of_from in self.tables_of_from:
            group_by_object = GroupBy()
            for phrase in self.phrases:
                for i in range(0, len(phrase)):
                    for table_name in self.database_dico:
                        columns = self.database_object.get_table_by_name(table_name).get_columns()
                        for column in columns:
                            if (phrase[i] == column.name) or (phrase[i] in column.equivalences):
                                column_with_alias = self.get_column_name_with_alias_table(column.name, table_of_from)
                                group_by_object.set_column(column_with_alias)
            self.group_by_objects.append(group_by_object)

    def join(self):
        Thread.join(self)
        return self.group_by_objects


class OrderByParser(Thread):
    def __init__(self, phrases, tables_of_from, asc_keywords, desc_keywords, database_dico, database_object):
        Thread.__init__(self)
        self.order_by_objects = []
        self.phrases = phrases
        self.tables_of_from = tables_of_from
        self.asc_keywords = asc_keywords
        self.desc_keywords = desc_keywords
        self.database_dico = database_dico
        self.database_object = database_object

    def get_tables_of_column(self, column):
        tmp_table = []
        for table in self.database_dico:
            if column in self.database_dico[table]:
                tmp_table.append(table)
        return tmp_table

    def get_column_name_with_alias_table(self, column, table_of_from):
        one_table_of_column = self.get_tables_of_column(column)[0]
        tables_of_column = self.get_tables_of_column(column)
        if table_of_from in tables_of_column:
            return str(table_of_from) + '.' + str(column)
        else:
            return str(one_table_of_column) + '.' + str(column)

    def intersect(self, a, b):
        return list(set(a) & set(b))

    def predict_order(self, phrase):
        if (len(self.intersect(phrase, self.desc_keywords)) >= 1):
            return 'DESC'
        else:
            return 'ASC'

    def run(self):
        for table_of_from in self.tables_of_from:
            order_by_object = OrderBy()
            for phrase in self.phrases:
                for i in range(0, len(phrase)):
                    for table_name in self.database_dico:
                        columns = self.database_object.get_table_by_name(table_name).get_columns()
                        for column in columns:
                            if (phrase[i] == column.name) or (phrase[i] in column.equivalences):
                                column_with_alias = self.get_column_name_with_alias_table(column.name, table_of_from)
                                order_by_object.add_column(column_with_alias, self.predict_order(phrase))
            self.order_by_objects.append(order_by_object)

    def join(self):
        Thread.join(self)
        return self.order_by_objects


class Parser:
    database_object = None
    database_dico = None

    count_keywords = []
    sum_keywords = []
    average_keywords = []
    max_keywords = []
    min_keywords = []
    junction_keywords = []
    disjunction_keywords = []
    greater_keywords = []
    less_keywords = []
    between_keywords = []
    order_by_keywords = []
    asc_keywords = []
    desc_keywords = []
    group_by_keywords = []
    negation_keywords = []
    equal_keywords = []
    like_keywords = []

    def __init__(self, database, config):
        self.database_object = database
        self.database_dico = self.database_object.get_tables_into_dictionary()

        self.count_keywords = config.get_count_keywords()
        self.sum_keywords = config.get_sum_keywords()
        self.average_keywords = config.get_avg_keywords()
        self.max_keywords = config.get_max_keywords()
        self.min_keywords = config.get_min_keywords()
        self.junction_keywords = config.get_junction_keywords()
        self.disjunction_keywords = config.get_disjunction_keywords()
        self.greater_keywords = config.get_greater_keywords()
        self.less_keywords = config.get_less_keywords()
        self.between_keywords = config.get_between_keywords()
        self.order_by_keywords = config.get_order_by_keywords()
        self.asc_keywords = config.get_asc_keywords()
        self.desc_keywords = config.get_desc_keywords()
        self.group_by_keywords = config.get_group_by_keywords()
        self.negation_keywords = config.get_negation_keywords()
        self.equal_keywords = config.get_equal_keywords()
        self.like_keywords = config.get_like_keywords()
        self.distinct_keywords = config.get_distinct_keywords()

    @staticmethod
    def _myCmp(s1,s2):
        if len(s1.split()) == len(s2.split()) :
            if len(s1) >= len(s2) :
                return 1
            else:
                return -1
        else:
            if len(s1.split()) >= len(s2.split()):
                return 1
            else:
                return -1


    @classmethod
    def transformation_sort(cls,transition_list):
        # Sort on basis of two keys split length and then token lengths in the respective priority.
        return sorted(transition_list, key=functools.cmp_to_key(cls._myCmp),reverse=True)


    def remove_accents(self, string):
        nkfd_form = unicodedata.normalize('NFKD', str(string))
        return "".join([c for c in nkfd_form if not unicodedata.combining(c)])

    def parse_sentence(self, sentence, stopwordsFilter=None):
        sys.tracebacklimit = 0  # Remove traceback from Exception

        number_of_table = 0
        number_of_select_column = 0
        number_of_where_column = 0
        last_table_position = 0
        columns_of_select = []
        columns_of_where = []

        if stopwordsFilter is not None:
            sentence = stopwordsFilter.filter(sentence)

        input_for_finding_value = sentence.rstrip(string.punctuation.replace('"', '').replace("'", ""))
        columns_of_values_of_where = []

        filter_list = [",", "!"]

        for filter_element in filter_list:
            input_for_finding_value = input_for_finding_value.replace(filter_element, " ")

        input_word_list = input_for_finding_value.split()

        number_of_where_column_temp = 0
        number_of_table_temp = 0
        last_table_position_temp = 0
        start_phrase = ''
        med_phrase = ''

        # TODO: merge this part of the algorithm (detection of values of where)
        #  in the rest of the parsing algorithm (about line 725) '''

        for i in range(0, len(input_word_list)):
            for table_name in self.database_dico:
                equivalences = self.database_object.get_table_by_name(table_name).equivalences or [table_name]
                if (input_word_list[i] == table_name) or (
                            input_word_list[i] in equivalences):
                    if number_of_table_temp == 0:
                        start_phrase = input_word_list[:i]
                    number_of_table_temp += 1
                    last_table_position_temp = i

                columns = self.database_object.get_table_by_name(table_name).get_columns()
                for column in columns:
                    if (input_word_list[i] == column.name) or (input_word_list[i] in column.equivalences):
                        if number_of_where_column_temp == 0:
                            med_phrase = input_word_list[len(start_phrase):last_table_position_temp + 1]
                        number_of_where_column_temp += 1
                        break
                    else:
                        if (number_of_table_temp != 0) and (number_of_where_column_temp == 0) and (
                                    i == (len(input_word_list) - 1)):
                            med_phrase = input_word_list[len(start_phrase):]
                else:
                    continue
                break

        end_phrase = input_word_list[len(start_phrase) + len(med_phrase):]

        irext = ' '.join(end_phrase)

        ''' @todo set this part of the algorithm (detection of values of where) in the WhereParser thread '''

        if irext:
            irext = self.remove_accents(irext.lower())

            filter_list = [",", "!"]

            for filter_element in filter_list:
                irext = irext.replace(filter_element, " ")

            assignment_list = self.equal_keywords + self.like_keywords + self.greater_keywords + self.less_keywords + self.negation_keywords
            # As these words can also be part of assigners

            # custom operators added as they can be possibilities
            assignment_list.append(':')
            assignment_list.append('=')

            # Algorithmic logic for best substitution for extraction of values with the help of assigners.
            assignment_list = self.transformation_sort(assignment_list)

            maverickjoy_general_assigner = "*res*@3#>>*"
            maverickjoy_like_assigner = "*like*@3#>>*"

            for idx, assigner in enumerate(assignment_list):
                if assigner in self.like_keywords:
                    assigner = str(" " + assigner + " ")
                    irext = irext.replace(assigner, str(" " + maverickjoy_like_assigner + " "))
                else:
                    assigner = str(" " + assigner + " ")
                    # Reason for adding " " these is according to the LOGIC implemented assigner operators help us extract the value,
                    # hence they should be independent entities not part of some other big entity else logic will fail.
                    # for eg -> "show data for city where cityName where I like to risk my life  is Pune" will end up extacting ,
                    # 'k' and '1' both. I know its a lame sentence but something like this could be a problem.

                    irext = irext.replace(assigner, str(" " + maverickjoy_general_assigner + " "))

            # replace all spaces from values to <_> for proper value assignment in SQL
            # eg. (where name is 'abc def') -> (where name is abc<_>def)
            for i in re.findall("(['\"].*?['\"])", irext):
                irext = irext.replace(i, i.replace(' ', '<_>').replace("'", '').replace('"', ''))

            irext_list = irext.split()

            for idx, x in enumerate(irext_list):
                index = idx + 1
                if x == maverickjoy_like_assigner:
                    if index < len(irext_list) and irext_list[index] != maverickjoy_like_assigner and irext_list[index] !=\
                            maverickjoy_general_assigner:
                        # replace back <_> to spaces from the values assigned
                        columns_of_values_of_where.append(str("'%" + str(irext_list[index]).replace('<_>', ' ') + "%'"))

                if x == maverickjoy_general_assigner:
                    if index < len(irext_list) and irext_list[index] != maverickjoy_like_assigner and irext_list[index] != \
                            maverickjoy_general_assigner:
                        # replace back <_> to spaces from the values assigned
                        columns_of_values_of_where.append(str("'" + str(irext_list[index]).replace('<_>', ' ') + "'"))

        ''' ----------------------------------------------------------------------------------------------------------- '''

        tables_of_from = []
        select_phrase = ''
        from_phrase = ''
        where_phrase = ''

        words = re.findall(r"[\w]+", self.remove_accents(sentence))

        for i in range(0, len(words)):
            for table_name in self.database_dico:
                equivalences = self.database_object.get_table_by_name(table_name).equivalences or [table_name]
                if (words[i] == table_name) or (
                            words[i] in equivalences):
                    if number_of_table == 0:
                        select_phrase = words[:i]
                    tables_of_from.append(table_name)
                    number_of_table += 1
                    last_table_position = i

                columns = self.database_object.get_table_by_name(table_name).get_columns()
                for column in columns:
                    if (words[i] == column.name) or (words[i] in column.equivalences):
                        if number_of_table == 0:
                            columns_of_select.append(column.name)
                            number_of_select_column += 1
                        else:
                            if number_of_where_column == 0:
                                from_phrase = words[len(select_phrase):last_table_position + 1]
                            columns_of_where.append(column.name)
                            number_of_where_column += 1
                        break
                    else:
                        if (number_of_table != 0) and (number_of_where_column == 0) and (i == (len(words) - 1)):
                            from_phrase = words[len(select_phrase):]

        where_phrase = words[len(select_phrase) + len(from_phrase):]

        if (number_of_select_column + number_of_table + number_of_where_column) == 0:
            raise ParsingException("No keyword found in sentence!")

        if len(tables_of_from) > 0:
            from_phrases = []
            previous_index = 0
            for i in range(0, len(from_phrase)):
                for table in tables_of_from:
                    if (from_phrase[i] == table) or (
                                from_phrase[i] in self.database_object.get_table_by_name(table).equivalences):
                        from_phrases.append(from_phrase[previous_index:i + 1])
                        previous_index = i + 1

            last_junction_word_index = -1

            for i in range(0, len(from_phrases)):
                number_of_junction_words = 0
                number_of_disjunction_words = 0

                for word in from_phrases[i]:
                    if word in self.junction_keywords:
                        number_of_junction_words += 1
                    if word in self.disjunction_keywords:
                        number_of_disjunction_words += 1

                if (number_of_junction_words + number_of_disjunction_words) > 0:
                    last_junction_word_index = i

            if last_junction_word_index == -1:
                from_phrase = sum(from_phrases[:1], [])
                where_phrase = sum(from_phrases[1:], []) + where_phrase
            else:
                from_phrase = sum(from_phrases[:last_junction_word_index + 1], [])
                where_phrase = sum(from_phrases[last_junction_word_index + 1:], []) + where_phrase

        real_tables_of_from = []

        for word in from_phrase:
            for table in tables_of_from:
                if (word == table) or (word in self.database_object.get_table_by_name(table).equivalences):
                    real_tables_of_from.append(table)

        tables_of_from = real_tables_of_from

        if len(tables_of_from) == 0:
            raise ParsingException("No table name found in sentence!")

        group_by_phrase = []
        order_by_phrase = []
        new_where_phrase = []
        previous_index = 0
        previous_phrase_type = 0
        yet_where = 0

        for i in range(0, len(where_phrase)):
            if where_phrase[i] in self.order_by_keywords:
                if yet_where > 0:
                    if previous_phrase_type == 1:
                        order_by_phrase.append(where_phrase[previous_index:i])
                    elif previous_phrase_type == 2:
                        group_by_phrase.append(where_phrase[previous_index:i])
                else:
                    new_where_phrase.append(where_phrase[previous_index:i])
                previous_index = i
                previous_phrase_type = 1
                yet_where += 1
            if where_phrase[i] in self.group_by_keywords:
                if yet_where > 0:
                    if previous_phrase_type == 1:
                        order_by_phrase.append(where_phrase[previous_index:i])
                    elif previous_phrase_type == 2:
                        group_by_phrase.append(where_phrase[previous_index:i])
                else:
                    new_where_phrase.append(where_phrase[previous_index:i])
                previous_index = i
                previous_phrase_type = 2
                yet_where += 1

        if previous_phrase_type == 1:
            order_by_phrase.append(where_phrase[previous_index:])
        elif previous_phrase_type == 2:
            group_by_phrase.append(where_phrase[previous_index:])
        else:
            new_where_phrase.append(where_phrase)

        try:
            select_parser = SelectParser(columns_of_select, tables_of_from, select_phrase, self.count_keywords,
                                         self.sum_keywords, self.average_keywords, self.max_keywords, self.min_keywords,
                                         self.distinct_keywords, self.database_dico, self.database_object)
            from_parser = FromParser(tables_of_from, columns_of_select, columns_of_where, self.database_object)
            where_parser = WhereParser(new_where_phrase, tables_of_from, columns_of_values_of_where,
                                       self.count_keywords, self.sum_keywords, self.average_keywords, self.max_keywords,
                                       self.min_keywords, self.greater_keywords, self.less_keywords,
                                       self.between_keywords, self.negation_keywords, self.junction_keywords,
                                       self.disjunction_keywords, self.like_keywords, self.distinct_keywords,
                                       self.database_dico, self.database_object)
            group_by_parser = GroupByParser(group_by_phrase, tables_of_from, self.database_dico, self.database_object)
            order_by_parser = OrderByParser(order_by_phrase, tables_of_from, self.asc_keywords, self.desc_keywords,
                                            self.database_dico, self.database_object)

            select_parser.start()
            from_parser.start()
            where_parser.start()
            group_by_parser.start()
            order_by_parser.start()

            queries = from_parser.join()
        except:
            raise ParsingException("Parsing error occured in thread!")

        if isinstance(queries, ParsingException):
            raise queries

        try:
            select_objects = select_parser.join()
            where_objects = where_parser.join()
            group_by_objects = group_by_parser.join()
            order_by_objects = order_by_parser.join()
        except:
            raise ParsingException("Parsing error occured in thread!")

        for i in range(0, len(queries)):
            query = queries[i]
            query.set_select(select_objects[i])
            query.set_where(where_objects[i])
            query.set_group_by(group_by_objects[i])
            query.set_order_by(order_by_objects[i])

        return queries
