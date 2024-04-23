"""
Scrape Category:Certosa (Bologna) and visualize it using Pyvis
Docs: https://pyvis.readthedocs.io/en/latest/tutorial.html#networkx-integration
"""

from wiki_category_tree import scrape
from pyvis.network import Network

graph = scrape('Category:Certosa (Bologna)', True, 'https://commons.wikimedia.org/w/api.php')

nw = Network('1200px', '800px')
nw.from_nx(graph)
nw.toggle_physics(True)
nw.show('pyvis_graph.html')

print("Done!")