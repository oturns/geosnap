"""Wrappers for multivariate clustering algorithms."""

from warnings import warn

import numpy as np
from region.max_p_regions.heuristics import MaxPRegionsHeu
from region.p_regions.azp import AZP
from region.skater.skater import Spanning_Forest
from sklearn.cluster import (
    AffinityPropagation,
    AgglomerativeClustering,
    KMeans,
    MiniBatchKMeans,
    SpectralClustering,
)
from sklearn.mixture import GaussianMixture


def _import_tryer(package, func, name):
    try:
        return exec(f"from {package} import {func}", globals(), globals())
    except ImportError:
        raise ImportError(
            f"You must have the {name} package installed to use this clusterer "
            "but it could not be imported."
        )


# Sklearn a-spatial models


def ward(X, n_clusters=5, **kwargs):
    """Agglomerative clustering using Ward linkage.

    Parameters
    ----------
    X  : array-like
        n x k attribute data
    n_clusters : int, optional, default: 8
        The number of clusters to form.


    Returns
    -------
    fitted model : sklearn.cluster.AgglomerativeClustering instance

    """
    model = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")
    model.fit(X)
    return model


def kmeans(
    X,
    n_clusters,
    init="k-means++",
    n_init=10,
    max_iter=300,
    tol=0.0001,
    verbose=0,
    random_state=None,
    copy_x=True,
    n_jobs=None,
    algorithm="auto",
    precompute_distances="auto",
    **kwargs,
):
    """K-Means clustering.

    Parameters
    ----------
    X  : array-like
         n x k attribute data
    n_clusters : int, optional, default: 8
        The number of clusters to form as well as the number of centroids to
        generate.

    Returns
    -------
    fitted model : sklearn.cluster.KMeans instance

    """
    if X.shape[0] > 12000:
        model = MiniBatchKMeans(
            n_clusters=n_clusters,
            init=init,
            n_init=n_init,
            max_iter=max_iter,
            tol=tol,
            verbose=verbose,
            random_state=random_state,
        )
    else:
        model = KMeans(
            n_clusters=n_clusters,
            init="k-means++",
            n_init=n_init,
            max_iter=max_iter,
            tol=tol,
            precompute_distances=precompute_distances,
            verbose=0,
            random_state=random_state,
            copy_x=copy_x,
            n_jobs=n_jobs,
            algorithm=algorithm,
        )

    model.fit(X)
    return model


def affinity_propagation(
    X,
    damping=0.8,
    preference=-1000,
    max_iter=500,
    convergence_iter=15,
    copy=True,
    affinity="euclidean",
    verbose=False,
    **kwargs,
):
    """Clustering with Affinity Propagation.

    Parameters
    ----------
    X  : array-like
         n x k attribute data
    preference :  array-like, shape (n_samples,) or float, optional, default: None
        The preference parameter passed to scikit-learn's affinity propagation
        algorithm
    damping : float, optional, default: 0.8
        The damping parameter passed to scikit-learn's affinity propagation
        algorithm
    max_iter : int, optional, default: 1000
        Maximum number of iterations

    Returns
    -------
    fitted cluster instance : sklearn.cluster.AffinityPropagation

    """
    model = AffinityPropagation(
        preference=preference,
        damping=damping,
        max_iter=max_iter,
        convergence_iter=convergence_iter,
        copy=copy,
        affinity=affinity,
        verbose=verbose,
    )
    model.fit(X)
    return model


def spectral(
    X,
    n_clusters,
    eigen_solver=None,
    random_state=None,
    n_init=10,
    gamma=1.0,
    affinity="rbf",
    n_neighbors=10,
    eigen_tol=0.0,
    assign_labels="kmeans",
    degree=3,
    coef0=1,
    kernel_params=None,
    n_jobs=-1,
    **kwargs,
):
    """Spectral Clustering.

    Parameters
    ----------
    X : array-like
        n x k attribute data
    n_clusters : int
        The number of clusters to form as well as the number of centroids to
        generate.
    eigen_solver : {None, ‘arpack’, ‘lobpcg’, or ‘amg’}
        The eigenvalue decomposition strategy to use. AMG requires pyamg to be installed. It can be
        faster on very large, sparse problems, but may also lead to instabilities.
    n_components : integer, optional, default=n_clusters
        Number of eigen vectors to use for the spectral embedding
    random_state : int, RandomState instance or None (default)
        A pseudo random number generator used for the initialization of the lobpcg eigen vectors
        decomposition when eigen_solver='amg' and by the K-Means initialization. Use an int to make
        the randomness deterministic. See Glossary.
    n_init : int, optional, default: 10
        Number of time the k-means algorithm will be run with different centroid seeds. The final
        results will be the best output of n_init consecutive runs in terms of inertia.
    gamma : float, default=1.0
        Kernel coefficient for rbf, poly, sigmoid, laplacian and chi2 kernels. Ignored for
        affinity='nearest_neighbors'.
    affinity : string or callable, default ‘rbf’
        How to construct the affinity matrix.
    n_neighbors : integer
        Number of neighbors to use when constructing the affinity matrix using the nearest neighbors
        method. Ignored for affinity='rbf'.
    eigen_tol : float, optional, default: 0.0
        Stopping criterion for eigendecomposition of the Laplacian matrix when eigen_solver='arpack'.
    degree : float, default=3
        Degree of the polynomial kernel. Ignored by other kernels.
    coef0 : float, default=1
        Zero coefficient for polynomial and sigmoid kernels. Ignored by other kernels.
    n_jobs : int or None, optional (default=None)
        The number of parallel jobs to run. None means 1 unless in a joblib.parallel_backend context.
        -1 means using all processors. See Glossary for more details.
    **kwargs : dict
        additional wkargs.

    Returns
    -------
    fitted cluster instance : sklearn.cluster.SpectralClustering

    """
    model = SpectralClustering(
        n_clusters=n_clusters,
        eigen_solver=eigen_solver,
        random_state=random_state,
        n_init=n_init,
        gamma=gamma,
        affinity=affinity,
        n_neighbors=n_neighbors,
        eigen_tol=eigen_tol,
        assign_labels=assign_labels,
        degree=degree,
        coef0=coef0,
        kernel_params=kernel_params,
        n_jobs=n_jobs,
    )
    model.fit(X)
    return model


def gaussian_mixture(
    X,
    n_clusters=5,
    covariance_type="full",
    best_model=False,
    max_clusters=10,
    random_state=None,
    **kwargs,
):
    """Clustering with Gaussian Mixture Model.

    Parameters
    ----------
    X  : array-like
        n x k attribute data
    n_clusters : int, optional, default: 5
        The number of clusters to form.
    covariance_type: str, optional, default: "full""
        The covariance parameter passed to scikit-learn's GaussianMixture
        algorithm
    best_model: bool, optional, default: False
        Option for finding endogenous K according to Bayesian Information
        Criterion
    max_clusters: int, optional, default:10
        The max number of clusters to test if using `best_model` option
    random_state: int, optional, default: None
        The seed used to generate replicable results
    kwargs

    Returns
    -------
    fitted cluster instance: sklearn.mixture.GaussianMixture

    """
    if random_state is None:
        warn(
            "Note: Gaussian Mixture Clustering is probabilistic--"
            "cluster labels may be different for different runs. If you need consistency, "
            "you should set the `random_state` parameter"
        )

    if best_model is True:

        # selection routine from
        # https://plot.ly/scikit-learn/plot-gmm-selection/
        lowest_bic = np.infty
        bic = []
        maxn = max_clusters + 1
        n_components_range = range(1, maxn)
        cv_types = ["spherical", "tied", "diag", "full"]
        for cv_type in cv_types:
            for n_components in n_components_range:
                # Fit a Gaussian mixture with EM
                gmm = GaussianMixture(
                    n_components=n_components,
                    random_state=random_state,
                    covariance_type=cv_type,
                )
                gmm.fit(X)
                bic.append(gmm.bic(X))
                if bic[-1] < lowest_bic:
                    lowest_bic = bic[-1]
                    best_gmm = gmm

        bic = np.array(bic)
        model = best_gmm

    else:
        model = GaussianMixture(
            n_components=n_clusters,
            random_state=random_state,
            covariance_type=covariance_type,
        )
    model.fit(X)
    model.labels_ = model.predict(X)
    return model


def hdbscan(X, min_cluster_size=5, gen_min_span_tree=True, **kwargs):
    """Clustering with Hierarchical DBSCAN.

    Parameters
    ----------
    X : array-like
         n x k attribute data
    min_cluster_size : int, default: 5
        the minimum number of points necessary to generate a cluster
    gen_min_span_tree : bool
        Description of parameter `gen_min_span_tree` (the default is True).
    kwargs

    Returns
    -------
    fitted cluster instance: hdbscan.hdbscan.HDBSCAN

    """
    _import_tryer("hdbscan", "HDBSCAN", "`hdbscan`")
    model = HDBSCAN(min_cluster_size=min_cluster_size)
    model.fit(X)
    return model


# Spatially Explicit/Encouraged Methods


def ward_spatial(X, w, n_clusters=5, **kwargs):
    """Agglomerative clustering using Ward linkage with a spatial connectivity constraint.

    Parameters
    ----------
    X : array-like
         n x k attribute data
    w : libpywal.weights.W instance
        spatial weights matrix
    n_clusters : int, optional, default: 5
        The number of clusters to form.

    Returns
    -------
    fitted cluster instance: sklearn.cluster.AgglomerativeClustering

    """
    model = AgglomerativeClustering(
        n_clusters=n_clusters, connectivity=w.sparse, linkage="ward"
    )
    model.fit(X)
    return model


def spenc(X, w, n_clusters=5, gamma=1, **kwargs):
    """Spatially encouraged spectral clustering.

    :cite:`wolf2018`

    Parameters
    ----------
    X : array-like
         n x k attribute data
    w : libpysal.weights.W instance
        spatial weights matrix
    n_clusters : int, optional, default: 5
        The number of clusters to form.
    gamma : int, default:1
        TODO.

    Returns
    -------
    fitted cluster instance: spenc.SPENC

    """
    _import_tryer("spenc", "SPENC", "spenc")

    model = SPENC(n_clusters=n_clusters, gamma=gamma)

    model.fit(X, w.sparse)
    return model


def skater(
    X, w, n_clusters=5, floor=-np.inf, trace=False, islands="increase", **kwargs
):
    """SKATER spatial clustering algorithm.

    Parameters
    ----------
    X : array-like
         n x k attribute data
    w : libpysal.weights.W instance
        spatial weights matrix
    n_clusters : int, optional, default: 5
        The number of clusters to form.
    floor : type
        TODO.
    trace : type
        TODO.
    islands : type
        TODO.

    Returns
    -------
    fitted cluster instance: region.skater.skater.Spanning_Forest

    """
    model = Spanning_Forest()
    model.fit(n_clusters, w, data=X.values, quorum=floor, trace=trace)
    model.labels_ = model.current_labels_
    return model


def azp(X, w, n_clusters=5, **kwargs):
    """AZP clustering algorithm.

    Parameters
    ----------
    X : array-like
         n x k attribute data
    w : libpysal.weights.W instance
        spatial weights matrix
    n_clusters : int, optional, default: 5
        The number of clusters to form.

    Returns
    -------
    fitted cluster instance: region.p_regions.azp.AZP

    """
    model = AZP()
    model.fit_from_w(attr=X.values, w=w, n_regions=n_clusters)
    return model


def max_p(X, w, threshold_variable="count", threshold=10, **kwargs):
    """Max-p clustering algorithm :cite:`Duque2012`.

    Parameters
    ----------
    X : array-like
         n x k attribute data
    w : libpysal.weights.W instance
        spatial weights matrix
    threshold_variable : str, default:"count"
        attribute variable to use as floor when calculate
    threshold : int, default:10
        integer that defines the upper limit of a variable that can be grouped
        into a single region

    Returns
    -------
    fitted cluster instance: region.p_regions.heuristics.MaxPRegionsHeu

    """
    model = MaxPRegionsHeu()
    model.fit_from_w(w, X.values, threshold_variable, threshold)
    return model
