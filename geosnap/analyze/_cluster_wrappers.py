"""Wrappers for multivariate clustering algorithms."""

from warnings import warn

import numpy as np
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
    except ImportError as e:
        raise ImportError(
            f"You must have the {name} package installed to use this clusterer "
            "but it could not be imported."
        ) from e


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
    algorithm="lloyd",
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
            verbose=0,
            random_state=random_state,
            copy_x=copy_x,
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
    random_state=None,
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
    random_state : int, RandomState instance or None, default=None
        Pseudo-random number generator to control the starting state. Use an int for reproducible results across function calls.

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
        random_state=random_state,
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
        Number of eigenvectors to use for the spectral embedding
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
    random_state : int, RandomState instance or None, default=None
        Pseudo-random number generator to control the starting state. Use an int for reproducible results across function calls.
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
    random_state : int, RandomState instance or None, default=None
        Pseudo-random number generator to control the starting state. Use an int for reproducible results across function calls.
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
        lowest_bic = np.inf
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
