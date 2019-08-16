import argparse

from .ln2sql import Ln2sql

cached_queries = {
    "quantos alunos nos temos atualmente?": '''select count(distinct("UserId")) from descomplica."Contracts" where "ValidTo" >= now()::date and "IsDeleted"=False and "PaymentConfirmed"=True and "ValidFrom" <= (now() + interval '1 day')::date;'''
}


def main():
    arg_parser = argparse.ArgumentParser(description='A Utility to convert Natural Language to SQL query')
    arg_parser.add_argument('-d', '--database', help='Path to SQL dump file', required=True)
    arg_parser.add_argument('-l', '--language', help='Path to language configuration file', required=True)
    arg_parser.add_argument('-i', '--sentence', help='Input sentence to parse', required=True)
    arg_parser.add_argument('-j', '--json_output', help='path to JSON output file', default=None)
    arg_parser.add_argument('-t', '--thesaurus', help='path to thesaurus file', default=None)
    arg_parser.add_argument('-s', '--stopwords', help='path to stopwords file', default=None)
    arg_parser.add_argument('-e', '--execute', help='should we execute the query', default=False)

    args = arg_parser.parse_args()
    if args.sentence in cached_queries:
        print(cached_queries[args.sentence])

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
