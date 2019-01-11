from warnings import warn

import numpy as np
from hdbscan import HDBSCAN
from region.max_p_regions.heuristics import MaxPRegionsHeu
from region.p_regions.azp import AZP
from region.skater.skater import Spanning_Forest
from sklearn.cluster import (AffinityPropagation, AgglomerativeClustering,
                             KMeans, MiniBatchKMeans, SpectralClustering)
from sklearn.mixture import GaussianMixture
from spenc import SPENC

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
    model: sklearn AgglomerativeClustering instance

    """
    model = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
    model.fit(X)
    return model


def kmeans(X,
           n_clusters,
           init='k-means++',
           n_init=10,
           max_iter=300,
           tol=0.0001,
           verbose=0,
           random_state=None,
           copy_x=True,
           n_jobs=None,
           algorithm='auto',
           precompute_distances='auto',
           **kwargs):
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
    model: sklearn KMeans instance

    """
    if X.shape[0] > 12000:
        model = MiniBatchKMeans(
            n_clusters=n_clusters,
            init=init,
            n_init=n_init,
            max_iter=max_iter,
            tol=tol,
            verbose=verbose,
            random_state=random_state)
    else:
        model = KMeans(
            n_clusters=n_clusters,
            init='k-means++',
            n_init=n_init,
            max_iter=max_iter,
            tol=tol,
            precompute_distances=precompute_distances,
            verbose=0,
            random_state=random_state,
            copy_x=copy_x,
            n_jobs=n_jobs,
            algorithm=algorithm)

    model.fit(X)
    return model


def affinity_propagation(X,
                         damping=0.8,
                         preference=-1000,
                         max_iter=500,
                         convergence_iter=15,
                         copy=True,
                         affinity='euclidean',
                         verbose=False,
                         **kwargs):
    """Clustering with Affinity Propagation.

    Parameters
    ----------
    X  : array-like
         n x k attribute data

    preference :  array-like, shape (n_samples,) or float, optional,
                  default: None
        The preference parameter passed to scikit-learn's affinity propagation
        algorithm

    damping: float, optional, default: 0.8
        The damping parameter passed to scikit-learn's affinity propagation
        algorithm

    max_iter : int, optional, default: 1000
        Maximum number of iterations


    Returns
    -------
    model: sklearn AffinityPropagation instance

    """
    model = AffinityPropagation(
        preference=preference,
        damping=damping,
        max_iter=max_iter,
        convergence_iter=convergence_iter,
        copy=copy,
        affinity=affinity,
        verbose=verbose)
    model.fit(X)
    return model


def spectral(X,
             n_clusters,
             eigen_solver=None,
             random_state=None,
             n_init=10,
             gamma=1.0,
             affinity='rbf',
             n_neighbors=10,
             eigen_tol=0.0,
             assign_labels='kmeans',
             degree=3,
             coef0=1,
             kernel_params=None,
             n_jobs=-1,
             **kwargs):
    """Short summary.

    Parameters
    ----------
    X : arral-like
        n x k attribute data
    n_clusters : type
        The number of clusters to form as well as the number of centroids to
        generate.
    eigen_solver : type
        Description of parameter `eigen_solver` (the default is None).
    random_state : type
        Description of parameter `random_state` (the default is None).
    n_init : type
        Description of parameter `n_init` (the default is 10).
    gamma : type
        Description of parameter `gamma` (the default is 1.0).
    affinity : type
        Description of parameter `affinity` (the default is 'rbf').
    n_neighbors : type
        Description of parameter `n_neighbors` (the default is 10).
    eigen_tol : type
        Description of parameter `eigen_tol` (the default is 0.0).
    assign_labels : type
        Description of parameter `assign_labels` (the default is 'kmeans').
    degree : type
        Description of parameter `degree` (the default is 3).
    coef0 : type
        Description of parameter `coef0` (the default is 1).
    kernel_params : type
        Description of parameter `kernel_params` (the default is None).
    n_jobs : type
        Description of parameter `n_jobs` (the default is -1).
    **kwargs : type
        Description of parameter `**kwargs`.

    Returns
    -------
    model: sklearn SpectralClustering instance

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
        n_jobs=n_jobs)
    model.fit(X)
    return model


def gaussian_mixture(X,
                     n_clusters=5,
                     covariance_type="full",
                     best_model=False,
                     max_clusters=10,
                     random_state=None,
                     **kwargs):
    """Clustering with Gaussian Mixture Model


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

    Returns
    -------

    model: sklearn GaussianMixture instance

    """
    if random_state is None:
        warn("Note: Gaussian Mixture Clustering is probabilistic--\
cluster labels may be different for different runs. If you need consistency,\
you should set the `random_state` parameter")

    if best_model is True:

        # selection routine from
        # https://plot.ly/scikit-learn/plot-gmm-selection/
        lowest_bic = np.infty
        bic = []
        maxn = max_clusters + 1
        n_components_range = range(1, maxn)
        cv_types = ['spherical', 'tied', 'diag', 'full']
        for cv_type in cv_types:
            for n_components in n_components_range:
                # Fit a Gaussian mixture with EM
                gmm = GaussianMixture(
                    n_components=n_components,
                    random_state=random_state,
                    covariance_type=cv_type)
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
            covariance_type=covariance_type)
    model.fit(X)
    model.labels_ = model.predict(X)
    return model


def hdbscan(X, min_cluster_size=5, gen_min_span_tree=True, **kwargs):
    """Clustering with Hierarchical DBSCAN

    Parameters
    ----------
    X : array-like
         n x k attribute data

    min_cluster_size : int, default: 5
        the minimum number of points necessary to generate a cluster

    gen_min_span_tree : bool
        Description of parameter `gen_min_span_tree` (the default is True).

    Returns
    -------
    model: hdbscan HDBSCAN instance

    """

    model = HDBSCAN(min_cluster_size=min_cluster_size)
    model.fit(X)
    return model


# Spatially Explicit/Encouraged Methods


def ward_spatial(X, w, n_clusters=5, **kwargs):
    """Agglomerative clustering using Ward linkage with a spatial connectivity
       constraint

    Parameters
    ----------
    X : array-like
         n x k attribute data

    w : PySAL W instance
        spatial weights matrix

    n_clusters : int, optional, default: 5
        The number of clusters to form.


    Returns
    -------
    model: sklearn AgglomerativeClustering instance

    """

    model = AgglomerativeClustering(
        n_clusters=n_clusters, connectivity=w.sparse, linkage='ward')
    model.fit(X)
    return model


def spenc(X, w, n_clusters=5, gamma=1, **kwargs):
    """Spatially encouraged spectral clustering

    :cite:`wolf2018`

    Parameters
    ----------
    X : array-like
         n x k attribute data

    w : PySAL W instance
        spatial weights matrix

    n_clusters : int, optional, default: 5
        The number of clusters to form.

    gamma : int, default:1
        TODO.


    Returns
    -------
    model: spenc SPENC instance

    """
    model = SPENC(n_clusters=n_clusters, gamma=gamma)

    model.fit(X, w.sparse)
    return model


def skater(X,
           w,
           n_clusters=5,
           floor=-np.inf,
           trace=False,
           islands='increase',
           **kwargs):
    """SKATER spatial clustering algorithm.

    Parameters
    ----------
    X : array-like
         n x k attribute data

    w : PySAL W instance
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

    model: skater SKATER instance

    """

    model = Spanning_Forest()
    model.fit(n_clusters, w, data=X.values, quorum=floor, trace=trace)
    model.labels_ = model.current_labels_
    return model


def azp(X, w, n_clusters=5, **kwargs):
    """AZP clustering algorithm

    Parameters
    ----------
    X : array-like
         n x k attribute data

    w : PySAL W instance
        spatial weights matrix

    n_clusters : int, optional, default: 5
        The number of clusters to form.


    Returns
    -------
    model: region AZP instance

    """

    model = AZP()
    model.fit_from_w(attr=X.values, w=w, n_regions=n_clusters)
    return model


def max_p(X, w, threshold_variable="count", threshold=10, **kwargs):
    """Max-p clustering algorithm
    :cite:`Duque2012`

    Parameters
    ----------
    X : array-like
         n x k attribute data

    w : PySAL W instance
        spatial weights matrix

    threshold_variable : str, default:"count"
        attribute variable to use as floor when calculate

    threshold : int, default:10
        integer that defines the upper limit of a variable that can be grouped
        into a single region


    Returns
    -------
    model: region MaxPRegionsHeu instance

    """
    model = MaxPRegionsHeu()
    model.fit_from_w(w, X.values, threshold_variable, threshold)
    return model
