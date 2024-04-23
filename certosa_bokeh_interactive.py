"""
Scrape Category:Certosa (Bologna) and visualize it interactively using Bokeh
Docs: https://docs.bokeh.org/en/2.4.1/docs/user_guide/graph.html#interaction-policies
"""

from wiki_category_tree import scrape
import networkx as nx
from bokeh.io import output_file, show
from bokeh.models import (BoxZoomTool, Circle, HoverTool,
                          MultiLine, Plot, Range1d, ResetTool)
from bokeh.palettes import Spectral4
from bokeh.plotting import from_networkx

graph = scrape('Category:Certosa (Bologna)', True, 'https://commons.wikimedia.org/w/api.php')

nx.write_edgelist(graph, "certosa_edge.tsv", delimiter='\t')

plot = Plot(width=1400,
            height=700,
            x_range=Range1d(-5,5),
            y_range=Range1d(-5,5))
plot.title.text = "Graph Interaction Demonstration"

node_hover_tool = HoverTool(tooltips=[("title", "@index"), ("content", "@content")])
plot.add_tools(node_hover_tool, BoxZoomTool(), ResetTool())

graph_renderer = from_networkx(graph, nx.spring_layout, scale=1, center=(0, 0))

graph_renderer.node_renderer.glyph = Circle(radius=0.001, fill_color=Spectral4[0])
#graph_renderer.edge_renderer.glyph = MultiLine(line_alpha=0.8, line_width=1)
plot.renderers.append(graph_renderer)

output_file("bokeh_interactive_graph.html")
show(plot)

print("Done!")