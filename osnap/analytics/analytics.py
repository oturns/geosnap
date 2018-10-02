"""
Tools for the spatial analysis of neighborhood change
"""

from exceptions import TypeError

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import pandas as pd
from libpysal import attach_islands
from libpysal.weights.Contiguity import Queen, Rook
from libpysal.weights.Distance import KNN

from .cluster import (
    affinity_propagation,
    gaussian_mixture,
    kmeans,
    max_p,
    skater,
    spectral,
    spenc,
    ward,
    ward_spatial,
)

store = pd.HDFStore("oslnap/data/us_geo.h5", "r")

states = store["states"]
states = gpd.GeoDataFrame(states)
states[~states.geoid.isin(["60", "66", "69", "72", "78"])]
states.crs = {"init": "epsg:4326"}
states = states.set_index("geoid")

counties = store["counties"]
counties = gpd.GeoDataFrame(counties)
counties.crs = {"init": "epsg:4326"}
counties = counties.set_index("geoid")

tracts = store["tracts"]
tracts = gpd.GeoDataFrame(tracts)
tracts.crs = {"init": "epsg:4326"}
tracts = tracts.set_index("geoid")

data = pd.HDFStore("oslnap/data/data.h5", "r")
if dataset.isin(["ltdb", "ncdb", "nhgis"]):
    df = data[dataset]
elif dataset == "external":
    df = dataset
else:
    raise ValueError("dataset must be one of 'ltdb', 'ncdb', 'nhgis', 'external'")


class Metro(object):

    """
    A class that stores neighborhood data and analytics for a metropolitan
    region
    """

    def __init__(self, name, boundary):

        self.name = name
        self.boundary = boundary
        self.tracts = tracts[
            tracts.set_geometry("point").within(self.boundary.unary_union)
        ]
        self.tracts = ox.project_gdf(self.tracts)
        self.counties = ox.project_gdf(
            counties[counties.index.isin(np.unique(self.tracts.index.str[0:5]))]
        )
        self.states = ox.project_gdf(
            states[states.index.isin(np.unique(self.tracts.index.str[0:2]))]
        )
        self.data = df[df.index.isin(self.tracts.index)]

    def plot(self, column=None, year=2015, ax=None, plot_counties=True, **kwargs):
        """
        convenience function for plotting tracts in the metro area
        """
        if ax is not None:
            ax = ax
        else:
            fig, ax = plt.subplots(figsize=(15, 15))
            colname = column.replace("_", " ")
            colname = colname.title()
            plt.title(self.name + ": " + colname + ", " + str(year), fontsize=20)
            plt.axis("off")

        ax.set_aspect("equal")
        plotme = self.tracts.join(self.data[self.data.year == year], how="left")
        plotme = plotme.dropna(subset=[column])
        plotme.plot(column=column, alpha=0.8, ax=ax, **kwargs)

        if plot_counties is True:
            self.counties.plot(
                edgecolor="#5c5353", linewidth=0.8, facecolor="none", ax=ax, **kwargs
            )

        return ax

    def cluster(
        self,
        n_clusters=6,
        method=None,
        best_model=False,
        columns=None,
        preference=-1000,
        damping=0.8,
        verbose=False,
        **kwargs
    ):
        """
        Create a geodemographic typology by running a cluster analysis on the
        metro area's neighborhood attributes

         Parameters
        ----------
        n_clusters : int
            the number of clusters to derive
        method : str
            the clustering algorithm used to identify neighborhood types
        columns : list-like
            subset of columns on which to apply the clustering

        Returns
        -------
        DataFrame

        """
        data = self.data.copy()
        allcols = columns + ["year"]
        data = data[allcols]
        data.dropna(inplace=True)
        data[columns] = data.groupby("year")[columns].apply(
            lambda x: (x - x.mean()) / x.std(ddof=0)
        )
        data
        # option to autoscale the data w/ mix-max or zscore?
        specification = {
            "ward": ward,
            "kmeans": kmeans,
            "ap": affinity_propagation,
            "gm": gaussian_mixture,
            "spectral": spectral,
        }
        model = specification[method](
            data.drop(columns="year"),
            n_clusters=n_clusters,
            preference=preference,
            damping=damping,
            best_model=best_model,
            verbose=verbose,
            **kwargs
        )
        labels = model.labels_.astype(str)
        clusters = pd.DataFrame(
            {method: labels, "year": data.year, "geoid": data.index}
        )
        clusters["joinkey"] = clusters.index + clusters.year.astype(str)
        clusters = clusters.drop(columns="year")
        geoid = self.data.index
        self.data["joinkey"] = self.data.index + self.data.year.astype(str)
        if method in self.data.columns:
            self.data.drop(columns=method, inplace=True)
        self.data = self.data.merge(clusters, on="joinkey", how="left")
        self.data["geoid"] = geoid
        self.data.set_index("geoid", inplace=True)

    def cluster_spatial(
        self,
        n_clusters=6,
        weights_type="rook",
        method=None,
        best_model=False,
        columns=None,
        threshold_variable=None,
        threshold=10,
        **kwargs
    ):
        """
        Create a *spatial* geodemographic typology by running a cluster
        analysis on the metro area's neighborhood attributes and including a
        contiguity constraint

         Parameters
        ----------
        n_clusters : int
            the number of clusters to derive
        weights_type : str 'queen' or 'rook'
            spatial weights matrix specification
        method : str
            the clustering algorithm used to identify neighborhood types
        columns : list-like
            subset of columns on which to apply the clustering

        Returns
        -------
        DataFrame

        """

        if threshold_variable == "count":
            allcols = columns + ["year"]
            data = self.data[allcols].copy()
            data = data.dropna(how="any")
            data[columns] = data.groupby("year")[columns].apply(
                lambda x: (x - x.mean()) / x.std(ddof=0)
            )

        elif threshold_variable is not None:
            threshold_var = data[threshold_variable]
            allcols = list(columns).remove(threshold_variable) + ["year"]
            data = self.data[allcols].copy()
            data = data.dropna(how="any")
            data[columns] = data.groupby("year")[columns].apply(
                lambda x: (x - x.mean()) / x.std(ddof=0)
            )

        else:
            allcols = columns + ["year"]
            data = self.data[allcols].copy()
            data = data.dropna(how="any")
            data[columns] = data.groupby("year")[columns].apply(
                lambda x: (x - x.mean()) / x.std(ddof=0)
            )

        tracts = self.tracts.copy()

        def _build_data(data, tracts, year, weights_type):
            df = data.loc[data.year == year].copy()
            tracts = tracts.copy()[tracts.index.isin(df.index)]
            weights = {"queen": Queen, "rook": Rook}
            w = weights[weights_type].from_dataframe(
                tracts.reset_index(), idVariable="geoid"
            )
            # drop islands from dataset and rebuild weights
            df.drop(index=w.islands, inplace=True)
            tracts.drop(index=w.islands, inplace=True)
            w = weights[weights_type].from_dataframe(
                tracts.reset_index(), idVariable="geoid"
            )
            knnw = KNN.from_dataframe(tracts, k=1)

            return df, w, knnw

        years = [1980, 1990, 2000, 2010, 2015]
        annual = []
        for year in years:
            df, w, knnw = _build_data(data, tracts, year, weights_type)
            annual.append([df, w, knnw])

        datasets = dict(zip(years, annual))

        specification = {
            "spenc": spenc,
            "ward_spatial": ward_spatial,
            "skater": skater,
            "max_p": max_p,
        }

        clusters = []
        for key, val in datasets.items():
            if threshold_variable == "count":
                threshold_var = np.ones(len(val[0]))
                val[1] = attach_islands(val[1], val[2])
            elif threshold_variable is not None:
                threshold_var = threshold_var[threshold.index.isin(val[0].index)].values
                val[1] = attach_islands(val[1], val[2])
            else:
                threshold_var = None
            model = specification[method](
                val[0].drop(columns="year"),
                w=val[1],
                n_clusters=n_clusters,
                threshold_variable=threshold_var,
                threshold=threshold,
                **kwargs
            )
            labels = model.labels_.astype(str)
            labels = pd.DataFrame(
                {method: labels, "year": val[0].year, "geoid": val[0].index}
            )
            clusters.append(labels)

        clusters = pd.concat(clusters)
        clusters.set_index("geoid")
        clusters["joinkey"] = clusters.index + clusters.year.astype(str)
        clusters = clusters.drop(columns="year")
        geoid = self.data.index
        self.data["joinkey"] = self.data.index + self.data.year.astype(str)
        if method in self.data.columns:
            self.data.drop(columns=method, inplace=True)
        self.data = self.data.merge(clusters, on="joinkey", how="left")
        self.data["geoid"] = geoid
        self.data.set_index("geoid", inplace=True)
