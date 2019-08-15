#!/usr/bin/env python

import argparse
import csv
import sys
from ast import literal_eval
from collections import Sequence
from inspect import getargspec
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
  head, data = head_tail(table)
  indices = column_indices(head);
  getter = project(*(indices[col] for col in columns))
  return imap(getter, chain([head], data))

def project(*items):
  if len(items) == 1:
    item = items[0]
    return lambda object : (object[item],) 
  else:
    return itemgetter(*items)

def select_rows(table, column_spec):
  """Select all rows which entries match the column spec."""
  if isinstance(column_spec, dict):
    return select_rows(table, AND(column_spec))
  bind_matchers = column_spec
  head, data = head_tail(table)

  # 1. resolve column indices
  indices = column_indices(head)  
  # 2. bind matchers
  matchers = bind_matchers(indices) if bind_matchers else (lambda row: True)
  # 3. filter
  return chain([head], ifilter(matchers, data))

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
  if isinstance(col, basestring):
    return lambda row: column_matcher(row[indices[col]])
  else:
    get_cols = project(*(indices[c] for c in col))
    return lambda row: column_matcher(*get_cols(row))

def all_as_matcher(column_specs):
  return {col : as_matcher(col, spec) for col, spec in column_specs.iteritems()}

def as_matcher(col, func_or_value):
  col = (col, ) if isinstance(col, basestring) else col
  if callable(func_or_value):
    argspec = getargspec(func_or_value)
    assert len(col) <= len(argspec.args) + (float('infinity') if argspec.varargs else 0)
    return func_or_value
  else:
    if len(col) == 1:
      return lambda val: val == func_or_value
    else:
      return lambda *vals: equals(func_or_value, *vals)

def equals(*vals):
  return vals and (vals[0], )*len(vals) == vals

def head_tail(iterable):
  if isinstance(iterable, Sequence):
    return iterable[0], iterable[1:]
  else:
    iterator = iter(iterable)
    return iterator.next(), iterator

class PrintExamples(argparse.Action):

  def __init__(self,
               option_strings,
               dest=argparse.SUPPRESS,
               default=argparse.SUPPRESS,
               help=None):
      super(PrintExamples, self).__init__(
          option_strings=option_strings,
          dest=dest,
          default=default,
          nargs=0,
          help=help)

  def __call__(self, parser, namespace, values, option_string=None):
    persons = (('id', 'first_name', 'last_name', 'age', 'sex'),\
               (1, 'Paul', 'Paul', 10, 'male'),\
               (2, 'Paula', 'Meier', 12, 'female'),\
               (3, 'Martin', None, 10, 'male'),\
               (4, 'Franz', 'Franz', 13, 'male'),\
               (5, 'Ursula', 'Leine', 14, 'female'))

    print 'persons = ['
    for row in persons:
      print str(row) + ','
    print ']\n'

    print "SELECT('*', FROM=persons, WHERE={'sex': 'female'})"
    result = SELECT('*', FROM=persons, WHERE={'sex': 'female'})
    for row in result:
      print row
    print

    print "SELECT(('first_name', 'id'), FROM=persons, WHERE={('first_name', 'last_name') : 'Paul'})"
    result = SELECT(('first_name', 'id'), FROM=persons, WHERE={('first_name', 'last_name') : 'Paul'})
    for row in result:
      print row
    print

    print "SELECT(('first_name', 'id'), FROM=persons, WHERE={('first_name', 'last_name') : lambda f, l: f==l})"
    result = SELECT(('first_name', 'id'), FROM=persons, WHERE={('first_name', 'last_name') : lambda f, l: f==l})
    for row in result:
      print row
    print

    print "SELECT(('first_name', 'id'), FROM=persons, WHERE=AND({'age': lambda age: age>10}, NOT({'sex': 'female'})))"
    result = SELECT(('first_name', 'id'), FROM=persons, WHERE=AND({'age': lambda age: age>10}, NOT({'sex': 'female'})))
    for row in result:
      print row

    parser.exit()

def parse_literal(string):
  try:
    return literal_eval(string)
  except ValueError:
    return string

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Execute an SQList query on CSV data from stdin', epilog='Available commands:\n  SELECT, SELECT_DISTINCT, NOT, AND, and OR\nOmit FROM keyword in query:\n  SELECT("*", WHERE=NOT({"col_1" : "None"}))', formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('query', metavar='<query>', type=str, help='an SQList query expression')
  parser.add_argument('-e', '--examples', action=PrintExamples, help='print example queries')
  parser.add_argument('-d', '--delimiter', metavar='<char>', help='delimiter in CSV input')
  parser.add_argument('-l', '--literals', action='store_true', help='parse values as python literals')
  parser.add_argument('-o', '--output', metavar='<file>', type=argparse.FileType('w'), default=sys.stdout, help='output file')
  args = parser.parse_args()

  reader = csv.reader(sys.stdin) if args.delimiter is None else csv.reader(sys.stdin, delimiter=args.delimiter)
  writer = csv.writer(args.output) if args.delimiter is None else csv.writer(args.output, delimiter=args.delimiter)

  csv = ([parse_literal(val) for val in row] for row in reader) if args.literals else reader

  bindings = {'SELECT'          : lambda COLUMNS, WHERE=None : SELECT(COLUMNS, csv, WHERE), \
              'SELECT_DISTINCT' : lambda COLUMNS, WHERE=None : SELECT_DISTINCT(COLUMNS, csv, WHERE), \
              'NOT'             : NOT, \
              'AND'             : AND, \
              'OR'              : OR}

  for row in eval(args.query, bindings):
    writer.writerow(row)
