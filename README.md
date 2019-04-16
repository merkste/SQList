# SQList

A small Python-Library to query tables, e.g., read from CSV files, with SQL-like commands.

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

We use function `SELECT` to retrieve all females from the `persons` table.
```
  SELECT('*', FROM=persons, WHERE={'sex': 'female'})
```
Select takes a tuple of column names as first argument or the wildcard `'*'` to indicate all columns.
The keyword argument `FROM` expects an iterable of rows, which are just lists or tuples.
The keyword argument `WHERE` expects a _column specification_.
The simplest case is a dictionary which assigns values to columns.
Here, the column `sex` must contain the string `'female'`.

It is also possible to expect multiple columns to hold the same value by providing a tuples of column names as dictionary keys:
```
  SELECT(('first_name', 'id'), FROM=persons, WHERE={('first_name', 'last_name') : 'Paul'})`
```

Instead of plain values, an _boolean function_ can be used in the column specification.
For example to match rows where two columns hold the same value:
```
  SELECT(('first_name', 'id'), FROM=persons, WHERE={('first_name', 'last_name') : lambda f, l: f==l})
```

We build more complex column specifications by combining them with the _logic operators_ `NOT`, `AND`, and `OR`.
```
  SELECT(('first_name', 'id'), FROM=persons, WHERE=AND({'age': lambda age: age>10}, NOT({'sex': 'female'})))
```
