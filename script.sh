echo 'Test 1 -- WHERE and AND'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "what is the name of the users where name is similar to Lucas and score is greater than 70"

echo '\n\nTest 2 -- AGGREGATORS'
python3 -m ln2sql.main -d database_store/schema3.sql -l lang_store/english.csv -j output.json -i "what is the average score from users"

echo '\n\nTest 3 -- AGGREGATORS II'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "what is the greatest score from users"

echo '\n\nTest 4 -- JOIN'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "what are the name and id from enrollments from users where score is less than 10"

echo '\n\nTest 5 -- GROUP and ORDER'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "count how many users where name is similar to lucas ordered by score grouped by name and score"

# echo '\n\nTest 6 -- BETWEEN'
# python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "what are the name of the users that have contracts have date in april"

# echo '\n\nTest 7 -- Tricky question'
# python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "how many users do we have now"

# echo '\n\nTest x -- JOIN no banco dele'
# python3 -m ln2sql.main -d database_store/city.sql -l lang_store/english.csv -j output.json -i "What is the cityName and the score of the emp whose name is rupinder"

python3 -m ln2sql.main -d database_store/schema3.sql -l lang_store/portuguese.csv -j output.json -i "qual é a média  do timestamp de contratos"

python3 -m ln2sql.main -d database_store/schema3.sql -l lang_store/portuguese.csv -j output.json -i "quantos alunos nos temos atualmente?"

python3 -m ln2sql.main -d database_store/schema3.sql -l lang_store/portuguese.csv -j output.json -i "quantos usuarios nós temos na base?" -e True