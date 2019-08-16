import argparse

from .ln2sql import Ln2sql

cached_queries = {
    "quantos alunos nós temos atualmente?": '''select count(distinct(user_id)) from contratos where valid_to >= now()::date and is_deleted=False and payment_confirmed=True and valid_from <= (now() + interval '1 day')::date;''',
    "quantas aulas gravadas nós temos?": ''' select count(id) from modulos where lesson_type in ('Practice', 'Learn') ''',
    "qual a disciplina mais consumida?": ''' select discipline, count(distinct distinct_id) from aula_consumida where time > '2019-01-01' group by 1 order by 2 desc limit 1 ''',
}


def main():
    arg_parser = argparse.ArgumentParser(description='A Utility to convert Natural Language to SQL query')
    arg_parser.add_argument('-d', '--database', help='Path to SQL dump file', default='database_store/schema3.sql')
    arg_parser.add_argument('-l', '--language', help='Path to language configuration file', default='lang_store/portuguese.csv')
    arg_parser.add_argument('-i', '--sentence', help='Input sentence to parse', required=True)
    arg_parser.add_argument('-j', '--json_output', help='path to JSON output file', default=None)
    arg_parser.add_argument('-t', '--thesaurus', help='path to thesaurus file', default=None)
    arg_parser.add_argument('-s', '--stopwords', help='path to stopwords file', default=None)
    arg_parser.add_argument('-e', '--execute', help='should we execute the query', default=True)

    args = arg_parser.parse_args()
    if args.sentence in cached_queries:
        query_to_execute = cached_queries[args.sentence]
        print(query_to_execute)
        ln2sql = Ln2sql(
            database_path=args.database,
            language_path=args.language,
            json_output_path=args.json_output,
            thesaurus_path=args.thesaurus,
            stopwords_path=args.stopwords,
        ).execute_query(query_to_execute)

    else:
        ln2sql = Ln2sql(
            database_path=args.database,
            language_path=args.language,
            json_output_path=args.json_output,
            thesaurus_path=args.thesaurus,
            stopwords_path=args.stopwords,
        ).get_query(args.sentence,args.execute)

if __name__ == '__main__':
    main()
