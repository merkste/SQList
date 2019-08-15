# SQList

A small Python-Library to query tables with SQL-like commands.
Tables are just iterables of lists or tuples, e.g., obtained from reading a CSV-file.
Processing happens lazy which allows to handle huge data sets or even infinite sources.

## Example
First we create a table as nested tuples.
```
  persons = (('id', 'first_name', 'last_name', 'age', 'sex'),\
             (1,    'Paul',       'Paul',      10,    'male'),\
             (2,    'Paula',      'Meier',     12,    'female'),\
             (3,    'Martin',      None,       10,    'male'),\
             (4,    'Franz',      'Franz',     13,    'male'),\
             (5,    'Ursula',     'Leine',     14,    'female'))
```

We use the function `SELECT` to retrieve all females from the table `persons`.
```
  SELECT('*', FROM=persons, WHERE={'sex': 'female'})
```
The first argument is either a tuple of column names or the wildcard `'*'` to get all columns.
The keyword argument `FROM` expects an iterable of lists or tuples.
The keyword argument `WHERE` expects a _column specification_.
The basic case is a dictionary that assigns expected values to columns.
In the example above, the column `sex` has to contain the string `'female'`.

A tuple of column names as dictionary key requires multiple columns to hold the same value:
```
  SELECT(('first_name', 'id'), FROM=persons, WHERE={('first_name', 'last_name') : 'Paul'})`
```

Instead of plain values, a _boolean function_ can be used.
For example, to match all rows where two columns hold the same value, we write:
```
  SELECT(('first_name', 'id'), FROM=persons, WHERE={('first_name', 'last_name') : lambda f, l: f==l})
```

More complex column specifications are composed using the _logic operators_ `NOT`, `AND`, and `OR`.
```
  SELECT(('first_name', 'id'), FROM=persons, WHERE=AND({'age': lambda age: age>10}, NOT({'sex': 'female'})))
```

## Command Line Interface
SQList offers a cmdl interface to query CSV data from stdin and write to stdout.
Suppose the persons table is stored in a .csv file.
```
  python sqlist.py "SELECT('*', WHERE={'sex': 'female'})" < persons.csv
```
See `python sqlist.py -h` for available options.
