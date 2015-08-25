from itertools import chain, ifilter, imap
from operator import itemgetter

# SELECT('*', FROM=persons, WHERE={id: 1, age:2})
# SELECT('*', FROM=persons, WHERE=(OR(NOT({id: 1, age:2}), {age: (lambda age: <=2))}))
def SELECT(COLUMNS, FROM, WHERE=None):
  """Similarily to SQL, select and project all rows from a table matching the constraints."""
  table = select_rows(FROM, WHERE) if WHERE else FROM
  if COLUMNS in ['*', (), None]:
    return table
  return project_columns(table, COLUMNS)

# NOT: dict -> indices -> (indices -> row -> boolean)
# NOT: (indices -> row -> boolean) -> (indices -> row -> boolean)
def NOT(column_specs):
  """Negate a column_spec and return a binding function."""
  if callable(column_specs):
    # indices -> row -> boolean
    return lambda indices: not_matcher(column_specs, indices)
  else:
    # dict
    return NOT(AND(column_specs))

# AND: (indices -> row -> boolean)+ -> (indices -> row -> boolean)
# AND: dict+ -> (indices -> row -> boolean)
def AND(*column_specs):
  """Apply logical AND to a list of column_specs and return a binding function."""
  bind_matchers = as_binding_functions(column_specs)
  return lambda indices: and_matcher(bind_matchers, indices)

# OR: (indices -> row -> boolean)+ -> (indices -> row -> boolean)
# OR: dict+ -> (indices -> row -> boolean)
def OR(*column_specs):
  """Apply logical OR to a list of column_specs and return a binding function."""
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
  """Select all rows which entries match the column_spec."""
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
  if all(callable(spec) for spec in column_specs):
    # (indices -> row -> boolean)+
    return column_tests
  else:
    # dict+
    return chain(*(all_curry_bind_matcher(all_as_matcher(spec)) for spec in column_specs))

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

persons = (('id', 'name', 'age', 'sex'),\
           (1, 'Paul', 10, 'male'),\
           (2, 'Paula', 12, 'female'),\
           (3, 'Marcus', 10, 'male'))

result = SELECT(None, FROM=persons, WHERE=NOT({'age': lambda age: age>10}))
for row in result:
  print row