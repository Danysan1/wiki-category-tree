"""
Functions to scrape the category tree of Wikimedia Commons starting from a root category
"""

from hashlib import sha256
from os import mkdir, rename
from os.path import isfile, isdir, join
import json
import networkx as nx
#import matplotlib.pyplot as plt
import requests
#from pyvis.network import Network

CACHE_DIR_NAME = '.cache'
MAX_SUBCATEGORIES = 500 # 500 = max ( https://www.mediawiki.org/wiki/API:Categorymembers )

def query_wikimedia_api(params:dict, api_endpoint:str):
    """
    Executes the query to the specified Wikimedia API with the specified parameters
    """
    params_hash = sha256(json.dumps(params, sort_keys=True).encode('utf-8')).hexdigest()
    legacy_file_path = join(CACHE_DIR_NAME, f'{params_hash}.json')
    dir_path = join(CACHE_DIR_NAME, params_hash[:2])
    file_path = join(dir_path, f'{params_hash}.json')

    if not isdir(dir_path):
        mkdir(dir_path)

    if isfile(legacy_file_path): # Move legacy cache files to the new directory structure
        rename(legacy_file_path, file_path)

    if isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as f:
            out = json.loads(f.read())
    else:
        out = None

    if out is None:
        print("Fetching and saving to cache file: ", file_path)
        resp = requests.get(url=api_endpoint, params=params, timeout=30)

        out = resp.json()
        if "error" in out:
            print(resp.text)
            raise Exception("Error in response");
    
        with open(file_path, mode='w', encoding='utf-8') as f:
            f.write(resp.text)
    else:
        print("Found response in cache: ", file_path)

    return out

def fetch_members(category: list, api_endpoint:str):
    """
    Fetch the subcategories of the cateogry whose name is in the input parameter

    Docs: https://www.mediawiki.org/wiki/API:Categorymembers
    Example URL: https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&list=categorymembers&cmtype=subcat&cmtitle=Category:Certosa%20(Bologna)
    Other example URL, not used here: https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&gcmtitle=Category:Certosa%20(Bologna)&generator=categorymembers&prop=info
    """
    params = {
        'action': 'query',
        'format': 'json',
        'formatversion': '2',
        'list': 'categorymembers',
        #'cmtype': 'subcat',
        'cmlimit': MAX_SUBCATEGORIES,
        'cmtitle': category
    }
    out = query_wikimedia_api(params, api_endpoint)
    if out["batchcomplete"] is False and "continue" in out:
        print("!!!!! Too many subcategories, TODO implement pagination !!!!!") # TODO https://www.mediawiki.org/wiki/API:Continue
    return out["query"]["categorymembers"]

def fetch_details(names: list, api_endpoint:str):
    """
    Fetch the details of the categories/files whose names are in the input list

    # Docs: https://www.mediawiki.org/wiki/API:Properties
    Example URL: https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&prop=info&titles=Category:Certosa%20(Bologna)
    """
    names.sort() # Sort to prevent cache misses
    params = {
        "action": 'query',
        "format": 'json',
        "formatversion": '2',
        "prop": "info|categories",
        "titles": '|'.join(names)
    }
    return query_wikimedia_api(params, api_endpoint)["query"]["pages"]

def fetch_content(names: list, api_endpoint:str):
    """
    Fetch the details of the categories/files whose names are in the input list

    # Docs: https://www.mediawiki.org/wiki/API:Revisions
    Example URL: https://commons.wikimedia.org/w/api.php?action=query&prop=revisions&titles=Category:Certosa%20(Bologna)&rvslots=*&rvprop=timestamp|user|comment|content
    """
    names.sort() # Sort to prevent cache misses
    params = {
        "action": 'query',
        "prop": "revisions",
        "format": 'json',
        "formatversion": '1',
        "rvslots": "*",
        "rvprop": "timestamp|user|comment|content",
        "titles": '|'.join(names)
    }
    return query_wikimedia_api(params, api_endpoint)["query"]["pages"]

def split_in_batches(iterable, n=1):
    """
    https://stackoverflow.com/a/8290508/2347196
    """
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

explored_categories = set()

def explore_category(category: list, g: nx.Graph, api_endpoint: str):
    """
    Recursive depth first exploration of the category graph
    """
    if category in explored_categories:
        return # Prevent infinite loops in case of cycles

    members = fetch_members(category, api_endpoint)
    for batch in split_in_batches(members, 50):
        print("Found ", len(members), "members in ", category, ", fetching content for batch")
        member_contents = fetch_content([member["title"] for member in batch], api_endpoint)
        explored_categories.add(category) # Prevent loops
        for member in batch:
            member_content = member_contents[str(member["pageid"])]["revisions"][0]["slots"]["main"]
            # https://networkx.org/documentation/stable/reference/classes/generated/networkx.DiGraph.add_node.html#digraph-add-node
            g.add_node(member["title"], content=member_content)
            # https://networkx.org/documentation/stable/reference/classes/generated/networkx.DiGraph.add_edge.html#digraph-add-edge
            g.add_edge(category, member["title"])
            if member["title"].startswith("Category:"):
                explore_category(member["title"], g, api_endpoint)

def scrape(root_category: str, api_endpoint = "https://commons.wikimedia.org/w/api.php") -> nx.DiGraph:
    """
    Scrape the Wikipedia category tree starting from the root category
    """
    g = nx.DiGraph()
    explore_category(root_category, g, api_endpoint)
    return g

if __name__ == "__main__":
    graph = scrape('Category:Certosa (Bologna)', 'https://commons.wikimedia.org/w/api.php')

    nx.write_adjlist(graph, "certosa_adj.tsv", delimiter='\t')
    nx.write_edgelist(graph, "certosa_edge.tsv", delimiter='\t')

    # plt.figure(figsize=(200, 200))
    # nx.draw_networkx(graph, with_labels=False)
    # plt.savefig("certosa.svg")

    # nt = Network('500px', '500px')
    # nt.from_nx(nx)
    # nt.show('nx.html')

    print("Done!")
