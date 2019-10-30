import pandas as pd
from geosnap.visualize import indexplot_seq
import matplotlib.pyplot as plt
df_LA = pd.read_csv("../../examples/data/LA_sequences.csv", converters={'GEO2010': lambda x: str(x)})
indexplot_seq(df_LA, clustering="seqC1", palette="pastel", ncols=3)
plt.show()
