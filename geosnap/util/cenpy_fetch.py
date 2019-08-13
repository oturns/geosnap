"""Utility functions for downloading Census data."""

import pandas
import sys
from tqdm.auto import tqdm


def main():
    from geosnap.data import data_store
    from cenpy import products

    def fetch_acs(level="tract", state="all", year=2017):
        """Collect the variables defined in `geosnap.data.data_store.codebook` from the Census API.

        Parameters
        ----------
        level : str
            Census geographic tabulation unit e.g. "block", "tract", or "county"
            (the default is 'tract').
        state : str
            State for which data should be collected, e.g. "Maryland".
            if 'all' (default) the function will loop through each state and return
            a combined dataframe.
        year : int
            ACS release year to query (the default is 2017).

        Returns
        -------
        type
            pandas.DataFrame

        Examples
        -------
        >>> dc = fetch_acs('District of Columbia', year=2015)

        """
        states = data_store.states()

        _variables = data_store.codebook.copy()

        acsvars = process_columns(_variables["acs"].dropna())

        evalcols = [
            normalize_relation(rel) for rel in _variables["acs"].dropna().tolist()
        ]

        varnames = _variables.dropna(subset=["acs"])["variable"]
        evals = [parts[0] + "=" + parts[1] for parts in zip(varnames, evalcols)]

        if state == "all":
            dfs = []
            with tqdm(total=len(states()), file=sys.stdout) as pbar:
                for state in states().sort_values(by="name").name.tolist():
                    try:
                        df = products.ACS(year).from_state(
                            state, level=level, variables=acsvars.copy()
                        )
                        dfs.append(df)
                        pbar.update(1)
                    except:
                        tqdm.write("{state} failed".format(state=state))
                        pbar.update(1)
            df = pandas.concat(dfs)
        else:
            df = products.ACS(year).from_state(
                name=state, level=level, variables=acsvars.copy()
            )

        df.set_index("GEOID", inplace=True)
        df = df.apply(lambda x: pandas.to_numeric(x, errors="coerce"), axis=1)
        # compute additional variables from lookup table
        for row in evals:
            try:
                df.eval(row, inplace=True, engine="python")
            except Exception as e:
                print(row + " " + str(e))
        for row in _variables["formula"].dropna().tolist():
            try:
                df.eval(row, inplace=True, engine="python")
            except Exception as e:
                print(str(row) + " " + str(e))
        keeps = [col for col in df.columns if col in _variables.variable.tolist()]
        df = df[keeps]
        return df

    def process_columns(input_columns):
        # prepare by taking all sum-of-columns as lists
        outcols_processing = [s.replace("+", ",") for s in input_columns]
        outcols = []
        while outcols_processing:  # stack
            col = outcols_processing.pop()
            col = col.replace("-", ",").replace("(", "").replace(")", "")
            col = [c.strip() for c in col.split(",")]  # get each part
            if len(col) > 1:  # if there are many parts
                col, *rest = col  # put the rest back
                for r in rest:
                    outcols_processing.insert(0, r)
            else:
                col = col[0]
            if ":" in col:  # if a part is a range
                start, stop = col.split(":")  # split the range
                stem = start[:-3]
                start = int(start[-3:])
                stop = int(stop)
                # and expand the range
                cols = [stem + str(col).rjust(3, "0") for col in range(start, stop + 1)]
                outcols.extend(cols)
            else:
                outcols.append(col)
        return outcols

    def normalize_relation(relation):
        parts = relation.split("+")
        if len(parts) == 1:
            if ":" not in relation:
                return relation
            else:
                relation = parts[0]
        else:
            relation = "+".join([normalize_relation(rel.strip()) for rel in parts])
        if ":" in relation:
            start, stop = relation.split(":")
            stem = start[:-3]
            start = int(start[-3:])
            stop = int(stop)
            # and expand the range
            cols = [stem + str(col).rjust(3, "0") for col in range(start, stop + 1)]
            return "+".join(cols)
        return relation


if __name__ == "__main__":
    main()
