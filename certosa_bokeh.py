"""
Scrape Category:Certosa (Bologna) and visualize it using Bokeh
Docs: https://docs.bokeh.org/en/2.4.1/docs/user_guide/graph.html#networkx-integration
"""

from wiki_category_tree import scrape
import networkx as nx
from bokeh.io import output_file, show
from bokeh.plotting import figure, from_networkx

graph = scrape('Category:Certosa (Bologna)', True, 'https://commons.wikimedia.org/w/api.php')

plot = figure(title="Networkx Integration Demonstration",
              x_range=(-10,10),
              y_range=(-10,10),
              tools="",
              toolbar_location=None)

bokeh_graph = from_networkx(graph, nx.spring_layout, scale=2, center=(0,0))
plot.renderers.append(bokeh_graph)

output_file("bokeh_graph.html")
show(plot)

print("Done!")