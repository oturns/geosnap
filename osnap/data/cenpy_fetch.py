import cenpy
import pandas
import os
import numpy as np

filepath = os.path.dirname(__file__)
variable_file = os.path.join(filepath, 'variables.csv')
variables = pandas.read_csv(variable_file)

c2000sf1 = cenpy.base.Connection(
    'DecennialSF11990')
c2000sf3 = cenpy.base.Connection(
    'DecennialSF31990')

by_form = variables.groupby('census_1990_form')
column_relations = by_form.census_1990_table_column.agg(list)


def fetch(unit='tract', state=None, filter=None):
    """
    use Cenpy to collect the necessary variables from the Census API
    """

    sf1cols = process_columns(column_relations.loc['SF1'])
    sf3cols = process_columns(column_relations.loc['SF3'])

    evalcols = [
        normalize_relation(rel)
        for rel in variables['census_1990_table_column'].dropna().tolist()
    ]

    varnames = variables.dropna(
        subset=['census_1990_table_column'])['variable']
    evals = [parts[0] + "=" + parts[1] for parts in zip(varnames, evalcols)]
    _sf1 = cenpy.tools.national_to_tract(c2000sf1, sf1cols, wait_by_county=0.5)
    #_sf1 = c2000sf1.query(sf1cols, geo_unit=unit, geo_filter=filter)
    _sf1['geoid'] = _sf1.state + _sf1.county + _sf1.tract

    _sf3 = cenpy.tools.national_to_tract(c2000sf3, sf3cols, wait_by_county=0.5)
    #_sf3 = c2000sf3.query(sf3cols, geo_unit=unit, geo_filter=filter)
    _sf3['geoid'] = _sf3.state + _sf3.county + _sf3.tract

    df = _sf1.merge(_sf3, on='geoid')
    df.set_index('geoid', inplace=True)
    df = df.apply(lambda x: pandas.to_numeric(x, errors='coerce'), axis=1)
    # compute additional variables from lookup table
    for row in evals:
        try:
            df.eval(row, inplace=True, engine='python')
        except Exception as e:
            print(row + ' ' + str(e))
    df = df.replace('nan', np.nan)
    for row in variables['formula'].dropna().tolist():
        try:
            df.eval(row, inplace=True, engine='python')
        except Exception as e:
            print(str(row) + ' ' + str(e))
    keeps = [col for col in df.columns if col in variables.variable.tolist()]
    df = df[keeps].round(2)
    return df


def process_columns(input_columns):
    # prepare by taking all sum-of-columns as lists
    outcols_processing = [s.replace('+', ',') for s in input_columns]
    outcols = []
    while outcols_processing:  # stack
        col = outcols_processing.pop()
        col = col.replace('-', ',').replace('(', '').replace(')', '')
        col = [c.strip() for c in col.split(',')]  # get each part
        if len(col) > 1:  # if there are many parts
            col, *rest = col  # put the rest back
            for r in rest:
                outcols_processing.insert(0, r)
        else:
            col = col[0]
        if ":" in col:  # if a part is a range
            start, stop = col.split(':')  # split the range
            stem = start[:-3]
            start = int(start[-3:])
            stop = int(stop)
            # and expand the range
            cols = [
                stem + str(col).rjust(3, '0')
                for col in range(start, stop + 1)
            ]
            outcols.extend(cols)
        else:
            outcols.append(col)
    return outcols


def normalize_relation(relation):
    parts = relation.split('+')
    if len(parts) == 1:
        if ':' not in relation:
            return relation
        else:
            relation = parts[0]
    else:
        relation = '+'.join([normalize_relation(rel.strip()) for rel in parts])
    if ":" in relation:
        start, stop = relation.split(':')
        stem = start[:-3]
        start = int(start[-3:])
        stop = int(stop)
        # and expand the range
        cols = [
            stem + str(col).rjust(3, '0') for col in range(start, stop + 1)
        ]
        return '+'.join(cols)
    return relation


df = fetch()

df.to_csv('census_1990.csv')
