from itertools import chain, ifilter, imap
from operator import itemgetter

def SELECT_DISTINCT(COLUMNS, FROM, WHERE=None):
  """Deduplicate selected rows. See also SELECT.

  Return an iterable of rows, each row as a tuple.
  """
  table = SELECT(COLUMNS, FROM, WHERE)
  seen = set()
  for row in table:
    row = tuple(row)
    if row not in seen:
      seen.add(row)
      yield row

def SELECT(COLUMNS, FROM, WHERE=None):
  """Similarily to SQL, select and project all rows from a table matching the constraints.
  
  Return an iterable of rows.
  Constraints are given as column specs. A column spec is
  - a dictionary that maps column names to expected values and test functions, or
  - a complex spec built with NOT, AND, and OR.
  WHERE=some_dict is short for WHERE=AND(some_dict)
  
  Arguments:
  COLUMNS -- a list of columns to project to, '*', (), and None are short for all columns
  FROM -- a table given as an iterable of rows (tuples, lists), first row is the table head
  
  Keyword arguments:
  WHERE -- a column spec built from dictionaries using NOT, AND, and OR (default: None)
  """
  table = select_rows(FROM, WHERE) if WHERE else FROM
  if COLUMNS in ['*', (), None]:
    return table
  return project_columns(table, COLUMNS)

def NOT(column_specs):
  """Negate a column_spec and return a binding function."""
  if callable(column_specs):
    # indices -> row -> boolean
    return lambda indices: not_matcher(column_specs, indices)
  else:
    # dict
    return NOT(AND(column_specs))

def AND(*column_specs):
  """Apply logical AND to a list of column specs and return a binding function."""
  bind_matchers = as_binding_functions(column_specs)
  return lambda indices: and_matcher(bind_matchers, indices)

def OR(*column_specs):
  """Apply logical OR to a list of column specs and return a binding function."""
  bind_matchers = as_binding_functions(column_specs)
  return lambda indices: or_matcher(bind_matchers, indices)

def project_columns(table, columns):
  """Project the table to the specified columns."""
  rows = iter(table)
  head = rows.next()
  indices = column_indices(head);
  getter = itemgetter(*(indices[col] for col in columns))
  return imap(getter, chain([head], rows))

def select_rows(table, column_spec):
  """Select all rows which entries match the column spec."""
  if isinstance(column_spec, dict):
    return select_rows(table, AND(column_spec))
  bind_matchers = column_spec
  rows = iter(table)
  head = rows.next()
  
  # 1. resolve column indices
  indices = column_indices(head)  
  # 2. bind matchers
  matchers = bind_matchers(indices) if bind_matchers else (lambda row: True)
  # 3. filter
  return chain([head], ifilter(matchers, rows))

def column_indices(head):
  """Build a dictionary of the column indices."""
  return {head[index] : index for index in xrange(0, len(head))}

def not_matcher(bind_matchers, indices):
  matcher = bind_matchers(indices) # bind column indices
  return lambda row: not matcher(row)

def and_matcher(bind_matchers, indices):
  matchers = tuple(bind_matcher(indices) for bind_matcher in bind_matchers)  # bind column indices
  return lambda row: all(matcher(row) for matcher in matchers);

def or_matcher(bind_matchers, indices):
  matchers = tuple(bind_matcher(indices) for bind_matcher in bind_matchers)  # bind column indices
  return lambda row: any(matcher(row) for matcher in matchers);

def as_binding_functions(column_specs):
  return chain(*([spec] if callable(spec) else all_curry_bind_matcher(all_as_matcher(spec)) for spec in column_specs))

def all_curry_bind_matcher(column_matchers):
  return (curry_bind_matcher(col, matcher) for col, matcher in column_matchers.iteritems())

def curry_bind_matcher(col, matcher):
  return lambda indices: bind_matcher(col, matcher, indices)

def bind_matcher(col, column_matcher, indices):
  index = indices[col];
  return lambda row: column_matcher(row[index])

def all_as_matcher(column_specs):
  return {col : as_matcher(spec) for col, spec in column_specs.iteritems()}

def as_matcher(func_or_value):
  if callable(func_or_value):
    return func_or_value
  else:
    return lambda val: val == func_or_value

def examples():
  persons = (('id', 'name', 'age', 'sex'),\
             (1, 'Paul', 10, 'male'),\
             (2, 'Paula', 12, 'female'),\
             (3, 'Martin', 10, 'male'),\
             (4, 'Franz', 13, 'male'),\
             (5, 'Ursula', 14, 'female'))

  result = SELECT('*', FROM=persons, WHERE={'sex': 'female'})
  for row in result:
    print row
  print
  
  result = SELECT(('name', 'id'), FROM=persons, WHERE=AND({'age': lambda age: age>10}, NOT({'sex': 'female'})))
  for row in result:
    print row
  print

if __name__ == "__main__":
  examples()