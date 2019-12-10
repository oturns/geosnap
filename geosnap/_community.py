"""A Community is a thin wrapper around a long-form time-series geodataframe."""
from warnings import warn

import geopandas as gpd
import pandas as pd

from ._data import _Map, datasets
from .analyze import cluster as _cluster
from .analyze import cluster_spatial as _cluster_spatial
from .analyze import sequence as _sequence
from .analyze import transition as _transition
from .harmonize import harmonize as _harmonize
from .io import _fips_filter, _fipstable, _from_db, get_lehd


class Community:
    """Spatial and tabular data for a collection of "neighborhoods" over time.

       A community is a collection of "neighborhoods" represented by spatial
       boundaries (e.g. census tracts, or blocks in the US), and tabular data
       which describe the composition of each neighborhood (e.g. data from
       surveys, sensors, or geocoded misc.). A Community can be large (e.g. a
       metropolitan region), or small (e.g. a handfull of census tracts) and
       may have data pertaining to multiple discrete points in time.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe that holds spatial and tabular data.
    harmonized : bool
        Whether neighborhood boundaries have been harmonized into a set of
        time-consistent units
    **kwargs


    Attributes
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe that stores neighborhood-level attributes
        and geometries for one or more time periods
    harmonized : bool
        Whether neighborhood boundaries have been harmonized into
        consistent units over time
    models : dict
        Dictionary of model instances that have been fitted on the community.
        The model name is the key and the value is a named tuple that stores the input matrix,
        the columns used to fit the model, the cluster labels, and the spatial weights matrix
        if necessary. For cluster models, the model name will match a column on the Community.gdf.

    """

    def __init__(self, gdf=None, harmonized=None, **kwargs):
        """Initialize a new Community.

        Parameters
        ----------
        gdf : geopandas.GeoDataFrame
            long-form geodataframe that stores neighborhood-level attributes
            and geometries for one or more time periods
        harmonized : bool
            Whether neighborhood boundaries have been harmonized into
            consistent units over time
        **kwargs : kwargs
            extra keyword arguments `**kwargs`.

        """
        self.gdf = gdf
        self.harmonized = harmonized
        self.models = _Map()

    def harmonize(
        self,
        target_year=None,
        weights_method="area",
        extensive_variables=None,
        intensive_variables=None,
        allocate_total=True,
        raster="nlcd_2011",
        codes="developed",
        force_crs_match=True,
    ):
        """Standardize inconsistent boundaries into time-static ones.

        Parameters
        ----------
        target_year: int
            Polygons from this year will become the target boundaries for
            spatial interpolation.
        weights_method : string
            The method that the harmonization will be conducted. This can be
            set to:
                * "area"                          : harmonization according to area weights.
                * "land_type_area"                : harmonization according to the Land Types considered 'populated' areas.
                * "land_type_Poisson_regression"  : NOT YET INTRODUCED.
                * "land_type_Gaussian_regression" : NOT YET INTRODUCED.
        extensive_variables : list
            extensive variables to be used in interpolation.
        intensive_variables : type
            intensive variables to be used in interpolation.
        allocate_total : boolean
            True if total value of source area should be allocated.
            False if denominator is area of i. Note that the two cases
            would be identical when the area of the source polygon is
            exhausted by intersections. See (3) in Notes for more details
        raster_path : str
            path to the raster image that has the types of each pixel in the
            spatial context. Only taken into consideration for harmonization
            raster based.
        codes : list of ints
            pixel values that should be included in the regression (the default "developed" includes [21, 22, 23, 24]).
        force_crs_match : bool
            whether source and target dataframes should be reprojected to match (the default is True).

        Returns
        -------
        None
            New data are added to the input Community

        """
        # convert the long-form into a list of dataframes
        # data = [x[1] for x in self.gdf.groupby("year")]
        if codes == "developed":
            codes = [21, 22, 23, 24]
        gdf = _harmonize(
            self.gdf,
            target_year=target_year,
            weights_method=weights_method,
            extensive_variables=extensive_variables,
            intensive_variables=intensive_variables,
            allocate_total=allocate_total,
            raster=raster,
            codes=codes,
            force_crs_match=force_crs_match,
        )
        return Community(gdf, harmonized=True)

    def cluster(
        self,
        n_clusters=6,
        method=None,
        best_model=False,
        columns=None,
        verbose=False,
        scaler="std",
        pooling="fixed",
        **kwargs,
    ):
        """Create a geodemographic typology by running a cluster analysis on the study area's neighborhood attributes.

        Parameters
        ----------
        n_clusters : int, required
            the number of clusters to model. The default is 6).
        method : str in ['kmeans', 'ward', 'affinity_propagation', 'spectral', 'gaussian_mixture', 'hdbscan'], required
            the clustering algorithm used to identify neighborhood types
        best_model : bool, optional
            if using a gaussian mixture model, use BIC to choose the best
            n_clusters. (the default is False).
        columns : array-like, required
            subset of columns on which to apply the clustering
        verbose : bool, optional
            whether to print warning messages (the default is False).
        scaler : None or scaler from sklearn.preprocessing, optional
            a scikit-learn preprocessing class that will be used to rescale the
            data. Defaults to sklearn.preprocessing.StandardScaler
        pooling : ["fixed", "pooled", "unique"], optional (default='fixed')
            How to treat temporal data when applying scaling. Options include:

            * fixed : scaling is fixed to each time period
            * pooled : data are pooled across all time periods
            * unique : if scaling, apply the scaler to each time period, then generate clusters unique to each time period.

        Returns
        -------
        geosnap.Community
            a copy of input Community with neighborhood cluster labels appended
            as a new column. If the cluster is already present, the name will be incremented

        """
        harmonized = self.harmonized
        gdf, model, model_name = _cluster(
            gdf=self.gdf.copy(),
            n_clusters=n_clusters,
            method=method,
            best_model=best_model,
            columns=columns,
            verbose=verbose,
            scaler=scaler,
            pooling=pooling,
            **kwargs,
        )

        comm = Community(gdf, harmonized=harmonized)
        comm.models.update(
            self.models
        )  # keep any existing models in the input Community
        comm.models[model_name] = model
        return comm

    def cluster_spatial(
        self,
        n_clusters=6,
        spatial_weights="rook",
        method=None,
        best_model=False,
        columns=None,
        threshold_variable="count",
        threshold=10,
        return_model=False,
        scaler=None,
        weights_kwargs=None,
        **kwargs,
    ):
        """Create a *spatial* geodemographic typology by running a cluster analysis on the metro area's neighborhood attributes and including a contiguity constraint.

        Parameters
        ----------
        n_clusters : int, required
            the number of clusters to model. The default is 6).
        spatial_weights : str ('queen' or 'rook') or libpysal.weights.W instance, optional
            spatial weights matrix specification` (the default is "rook"). If 'rook' or 'queen'
            then contiguity weights will be constructed internally, otherwise pass a
            libpysal.weights.W with additional arguments specified in weights_kwargs
        weights_kwargs : dict, optional
            If passing a libpysal.weights.W instance to spatial_weights, these additional
            keyword arguments that will be passed to the weights constructor
        method : str in ['ward_spatial', 'spenc', 'skater', 'azp', 'max_p'], required
            the clustering algorithm used to identify neighborhood types
        columns : array-like, required
            subset of columns on which to apply the clustering
        threshold_variable : str, required if using max-p, optional otherwise
            for max-p, which variable should define `p`. The default is "count",
            which will grow regions until the threshold number of polygons have
            been aggregated
        threshold : numeric, optional
            threshold to use for max-p clustering (the default is 10).
        scaler : None or scaler from sklearn.preprocessing, optional
            a scikit-learn preprocessing class that will be used to rescale the
            data. Defaults to sklearn.preprocessing.StandardScaler

        Returns
        -------
        geosnap.Community
            a copy of input Community with neighborhood cluster labels appended
            as a new column. If the cluster is already present, the name will be incremented


        """
        harmonized = self.harmonized

        gdf, model, model_name = _cluster_spatial(
            gdf=self.gdf.copy(),
            n_clusters=n_clusters,
            spatial_weights=spatial_weights,
            method=method,
            best_model=best_model,
            columns=columns,
            threshold_variable=threshold_variable,
            threshold=threshold,
            return_model=return_model,
            scaler=scaler,
            weights_kwargs=weights_kwargs,
            **kwargs,
        )

        comm = Community(gdf, harmonized=harmonized)
        comm.models.update(
            self.models
        )  # keep any existing models in the input Community
        comm.models[model_name] = model
        return comm

    def transition(
        self, cluster_col, time_var="year", id_var="geoid", w_type=None, permutations=0
    ):
        """
        (Spatial) Markov approach to transitional dynamics of neighborhoods.

        The transitional dynamics approach should be adopted after
        neighborhood segmentation since the column name of neighborhood
        labels is a required input.

        Parameters
        ----------
        cluster_col     : string or int
                          Column name for the neighborhood segmentation, such as
                          "ward", "kmeans", etc.
        time_var        : string, optional
                          Column defining time and or sequencing of the long-form data.
                          Default is "year".
        id_var          : string, optional
                          Column identifying the unique id of spatial units.
                          Default is "geoid".
        w_type          : string, optional
                          Type of spatial weights type ("rook", "queen", "knn" or
                          "kernel") to be used for spatial structure. Default is
                          None, if non-spatial Markov transition rates are desired.
        permutations    : int, optional
                          number of permutations for use in randomization based
                          inference (the default is 0).


        Returns
        ---------
        mar             : giddy.markov.Markov or giddy.markov.Spatial_Markov
                          if w_type=None, return a classic Markov instance;
                          if w_type is given, return a Spatial_Markov instance

        """
        mar = _transition(
            self.gdf,
            cluster_col,
            time_var=time_var,
            id_var=id_var,
            w_type=w_type,
            permutations=permutations,
        )
        return mar

    def sequence(
        self,
        cluster_col,
        seq_clusters=5,
        subs_mat=None,
        dist_type=None,
        indel=None,
        time_var="year",
        id_var="geoid",
    ):
        """
        Pairwise sequence analysis to evaluate the distance/dissimilarity
        between every two neighborhood sequences.

        The sequence approach should be adopted after
        neighborhood segmentation since the column name of neighborhood
        labels is a required input.

        Parameters
        ----------
        cluster_col     : string or int
                          Column name for the neighborhood segmentation, such as
                          "ward", "kmeans", etc.
        seq_clusters    : int, optional
                          Number of neighborhood sequence clusters. Agglomerative
                          Clustering with Ward linkage is now used for clustering
                          the sequences. Default is 5.
        subs_mat        : array
                          (k,k), substitution cost matrix. Should be hollow (
                          0 cost between the same type), symmetric and non-negative.
        dist_type       : string
                          "hamming": hamming distance (substitution only
                          and its cost is constant 1) from sklearn.metrics;
                          "markov": utilize empirical transition
                          probabilities to define substitution costs;
                          "interval": differences between states are used
                          to define substitution costs, and indel=k-1;
                          "arbitrary": arbitrary distance if there is not a
                          strong theory guidance: substitution=0.5, indel=1.
                          "tran": transition-oriented optimal matching. Sequence of
                          transitions. Based on :cite:`Biemann:2011`.
        indel           : float, optional
                          insertion/deletion cost.
        time_var        : string, optional
                          Column defining time and or sequencing of the long-form data.
                          Default is "year".
        id_var          : string, optional
                          Column identifying the unique id of spatial units.
                          Default is "geoid".

        Returns
        -------
        gdf_new         : Community instance
                          New Community instance with attribute "gdf" having
                          a new column for sequence labels.
        df_wide         : pandas.DataFrame
                          Wide-form DataFrame with k (k is the number of periods)
                          columns of neighborhood types and 1 column of sequence
                          labels.
        seq_dis_mat     : array
                          (n,n), distance/dissimilarity matrix for each pair of
                          sequences

        """
        gdf_temp, df_wide, seq_dis_mat = _sequence(
            self.gdf,
            cluster_col,
            seq_clusters=seq_clusters,
            subs_mat=subs_mat,
            dist_type=dist_type,
            indel=indel,
            time_var=time_var,
            id_var=id_var,
        )
        gdf_new = Community(gdf_temp)
        return gdf_new, df_wide, seq_dis_mat

    @classmethod
    def from_ltdb(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years="all",
    ):
        """Create a new Community from LTDB data.

           Instiantiate a new Community from pre-harmonized LTDB data. To use
           you must first download and register LTDB data with geosnap using
           the `store_ltdb` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : list or str
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary : geopandas.GeoDataFrame
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list of ints
            list of years (decades) to include in the study data
            (the default "all" is [1970, 1980, 1990, 2000, 2010]).

        Returns
        -------
        Community
            Community with LTDB data


        """
        if years == "all":
            years = [1970, 1980, 1990, 2000, 2010]
        if isinstance(boundary, gpd.GeoDataFrame):
            tracts = datasets.tracts_2010()[["geoid", "geometry"]]
            ltdb = datasets.ltdb().reset_index()
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]
            gdf = ltdb[ltdb["geoid"].isin(tracts["geoid"])]
            gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"))

        else:
            gdf = _from_db(
                data=datasets.ltdb(),
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                years=years,
            )

        return cls(gdf=gdf.reset_index(), harmonized=True)

    @classmethod
    def from_ncdb(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years="all",
    ):
        """Create a new Community from NCDB data.

           Instiantiate a new Community from pre-harmonized NCDB data. To use
           you must first download and register LTDB data with geosnap using
           the `store_ncdb` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : list or str
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary : geopandas.GeoDataFrame
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list of ints
            list of years (decades) to include in the study data
            (the default is all available [1970, 1980, 1990, 2000, 2010]).

        Returns
        -------
        Community
            Community with NCDB data

        """
        if years == "all":
            years = [1970, 1980, 1990, 2000, 2010]
        if isinstance(boundary, gpd.GeoDataFrame):
            tracts = datasets.tracts_2010()[["geoid", "geometry"]]
            ncdb = datasets.ncdb().reset_index()
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]
            gdf = ncdb[ncdb["geoid"].isin(tracts["geoid"])]
            gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"))

        else:
            gdf = _from_db(
                data=datasets.ncdb(),
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                years=years,
            )

        return cls(gdf=gdf.reset_index(), harmonized=True)

    @classmethod
    def from_census(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years="all",
    ):
        """Create a new Community from original vintage US Census data.

           Instiantiate a new Community from . To use
           you must first download and register census data with geosnap using
           the `store_census` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str, optional
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str, optional
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : list or str, optional
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : list or str, optional
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary : geopandas.GeoDataFrame, optional
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list of ints, required
            list of years to include in the study data
            (the default is [1990, 2000, 2010]).

        Returns
        -------
        Community
            Community with unharmonized census data

        """
        if years == "all":
            years = [1990, 2000, 2010]
        if isinstance(years, (str, int)):
            years = [years]

        msa_states = []
        if msa_fips:
            msa_states += datasets.msa_definitions()[
                datasets.msa_definitions()["CBSA Code"] == msa_fips
            ]["stcofips"].tolist()
        msa_states = [i[:2] for i in msa_states]

        # build a list of states in the dataset
        allfips = []
        for i in [state_fips, county_fips, fips, msa_states]:
            if i:
                if isinstance(i, (str,)):
                    i = [i]
                for each in i:
                    allfips.append(each[:2])
        states = list(set(allfips))

        # if using a boundary there will be no fips, so reset states to None
        if len(states) == 0:
            states = None

        df_dict = {
            1990: datasets.tracts_1990(states=states),
            2000: datasets.tracts_2000(states=states),
            2010: datasets.tracts_2010(states=states),
        }

        tracts = []
        for year in years:
            tracts.append(df_dict[year])
        tracts = pd.concat(tracts, sort=False)

        if isinstance(boundary, gpd.GeoDataFrame):
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]
            gdf = tracts.copy()

        else:

            gdf = _fips_filter(
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                data=tracts,
            )

        return cls(gdf=gdf, harmonized=False)

    @classmethod
    def from_lodes(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years=2015,
        dataset="wac",
    ):
        """Create a new Community from Census LEHD/LODES data.

           Instiantiate a new Community from LODES data.
           Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str, optional
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str, optional
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : list or str, optional
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : list or str, optional
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary : geopandas.GeoDataFrame, optional
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list of ints, required
            list of years to include in the study data
            (the default is 2015).
        dataset : str, required
            which LODES dataset should be used to create the Community.
            Options are 'wac' for workplace area characteristics or 'rac' for
            residence area characteristics. The default is "wac" for workplace.

        Returns
        -------
        Community
            Community with LODES data

        """
        if isinstance(years, (str,)):
            years = int(years)
        if isinstance(years, (int,)):
            years = [years]
        years = list(set(years))

        if msa_fips:
            msa_counties = datasets.msa_definitions()[
                datasets.msa_definitions()["CBSA Code"] == msa_fips
            ]["stcofips"].tolist()

        else:
            msa_counties = None

        # build a list of states in the dataset
        allfips = []
        stateset = []
        for i in [state_fips, county_fips, msa_counties, fips]:
            if i:
                if isinstance(i, (str,)):
                    i = [i]
                for each in i:
                    allfips.append(each)
                    stateset.append(each[:2])
            states = list(set(stateset))

        if any(year < 2010 for year in years):
            gdf00 = datasets.blocks_2000(states=states, fips=(tuple(allfips)))
            gdf00 = gdf00.drop(columns=["year"])
            gdf00 = _fips_filter(
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                data=gdf00,
            )
            if isinstance(boundary, gpd.GeoDataFrame):
                if boundary.crs != gdf00.crs:
                    warn(
                        "Unable to determine whether boundary CRS is WGS84 "
                        "if this produces unexpected results, try reprojecting"
                    )
                gdf00 = gdf00[gdf00.representative_point().intersects(boundary.unary_union)]

        gdf = datasets.blocks_2010(states=states, fips=(tuple(allfips)))
        gdf = gdf.drop(columns=["year"])
        gdf = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=gdf,
        )
        if isinstance(boundary, gpd.GeoDataFrame):
            if boundary.crs != gdf.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            gdf = gdf[gdf.representative_point().intersects(boundary.unary_union)]

        # grab state abbreviations
        names = (
            _fipstable[_fipstable["FIPS Code"].isin(states)]["State Abbreviation"]
            .str.lower()
            .tolist()
        )
        if isinstance(names, str):
            names = [names]

        dfs = []
        for name in names:
            for year in years:
                try:
                    df = get_lehd(dataset=dataset, year=year, state=name)
                    df["year"] = year
                    if year < 2010:
                        df = gdf00.merge(df, on="geoid", how="inner")
                    else:
                        df = gdf.merge(df, on="geoid", how="inner")
                    df = df.set_index(["geoid", "year"])
                    dfs.append(df)
                except ValueError:
                    warn(f"{name.upper()} {year} not found!")
                    pass
        out = pd.concat(dfs, sort=True)
        out = out[~out.index.duplicated(keep="first")]
        out = out.reset_index()

        return cls(gdf=out, harmonized=False)

    @classmethod
    def from_geodataframes(cls, gdfs=None):
        """Create a new Community from a list of geodataframes.

        Parameters
        ----------
        gdfs : list-like of geopandas.GeoDataFrames
            list of geodataframes that hold attribute and geometry data for
            a study area. Each geodataframe must have neighborhood
            attribute data, geometry data, and a time column that defines
            how the geodataframes are sequenced. The geometries may be
            stable over time (in which case the dataset is harmonized) or
            may be unique for each time. If the data are harmonized, the
            dataframes must also have an ID variable that indexes
            neighborhood units over time.

        """
        gdf = pd.concat(gdfs, sort=True)
        return cls(gdf=gdf)
