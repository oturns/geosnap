import cenpy
import pandas
import os

filepath = os.path.dirname(__file__)
variable_file = os.path.join(filepath, 'variables.csv')
variables = pandas.read_csv(variable_file)

c2000sf1 = cenpy.base.Connection('2000sf1')
c2000sf3 = cenpy.base.Connection('2000sf3')

by_form = variables.groupby('census_2000_form')
column_relations = by_form.census_2000_table_column.agg(list)

# What is left:
# 0. concatenate san_diego_sf1_processed/san_diego_sf3_processed along axis=1
# 1. pull the applicable ltdb names from `variables`
#    and make them the column names of the right
#    elements of `san_diego_sf*`
# 2. Concatenate the `*_processed` dataframes alongside the metadata columns
#    [col for col in san_diego_sf1.columns if col not in sf1cols]
# 3. merge this new concatenated data together between sf1 and sf3.


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


sf1cols = process_columns(column_relations.loc['SF1'])
sf3cols = process_columns(column_relations.loc['SF3'])

san_diego_sf1 = c2000sf1.query(
    ['NAME'] + sf1cols,
    geo_unit='tract',
    geo_filter=dict(state='06', county='073'))
san_diego_sf3 = c2000sf3.query(
    ['NAME'] + sf3cols,
    geo_unit='tract',
    geo_filter=dict(state='06', county='073'))

san_diego_sf1_processed = [
    san_diego_sf1[sf1cols].astype(float).eval(normalize_relation(rel))
    for rel in column_relations.loc['SF1']
]
san_diego_sf3_processed = [
    san_diego_sf3[sf3cols].astype(float).eval(normalize_relation(rel))
    for rel in column_relations.loc['SF3']
]
