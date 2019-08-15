echo 'Test 1 -- WHERE and AND'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "count how many users where name is lucas and score is greater than 70"

echo '\n\nTest 2 -- AGGREGATORS'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "what is the average score from users"

echo '\n\nTest 3 -- AGGREGATORS II'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "what is the greatest score from users"

echo '\n\nTest 4 -- JOIN'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "what are the id from enrollments from users where score is less than 0"

echo '\n\nTest 5 -- GROUP and ORDER'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "count how many users where name is similar to lucas ordered by score grouped by name"

echo '\n\nTest 6 -- BETWEEN'
python3 -m ln2sql.main -d database_store/schema.sql -l lang_store/english.csv -j output.json -i "how many users have contracts in month april"

echo '\n\nTest x -- JOIN no banco dele'
python3 -m ln2sql.main -d database_store/city.sql -l lang_store/english.csv -j output.json -i "What is the cityName and the score of the emp whose name is rupinder"
