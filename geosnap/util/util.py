"""Utility functions."""

import os
import re
from pathlib import PurePath

import matplotlib.pyplot as plt
from matplotlib.animation import ArtistAnimation, PillowWriter


def gif_from_path(
    path=None,
    figsize=(10, 10),
    fps=0.5,
    interval=500,
    repeat_delay=1000,
    filename=None,
    dpi=400,
):
    """
    Create an animated gif from a director of image files.

    Parameters
    ----------
    path :str, required
        path to directory of images
    figsize : tuple, optional
        output figure size passed to matplotlib.pyplot
    fps : float, optional
        frames per second
    interval : int, optional
        interval between frames in miliseconds, default 500
    repeat_delay : int, optional
        time before animation repeats in miliseconds, default 1000
    filename : str, required
        output file name
    dpi : int, optional
        image dpi passed to matplotlib writer
    """
    assert filename, "You must provide an output filename ending in .gif"
    imgs = os.listdir(path)
    imgs.sort(key=lambda var:[int(x) if x.isdigit() else x for x in re.findall(r'[^0-9]|[0-9]+', var)])

    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    ims = []

    for i in imgs:
        c = plt.imread(str(PurePath(path, i)))
        im = plt.imshow(c, animated=True)
        ims.append([im])

    writer = PillowWriter(fps=fps)

    ani = ArtistAnimation(
        fig, ims, interval=interval, blit=True, repeat_delay=repeat_delay
    )

    plt.tight_layout()
    ani.save(filename, writer=writer, dpi=dpi)
