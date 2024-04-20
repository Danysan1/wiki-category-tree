from hashlib import sha256
from os import mkdir
from os.path import isfile, isdir, join
import json
import networkx as nx
import matplotlib.pyplot as plt
import requests

CACHE_DIR_NAME = '.cache'

def query_wikimedia_api(params:dict, api_endpoint:str):
    """
    Executes the query to the specified Wikimedia API with the specified parameters
    """
    params_hash = sha256(json.dumps(params, sort_keys=True).encode('utf-8'))
    dir_path = CACHE_DIR_NAME
    file_path = join(dir_path, f'{params_hash.hexdigest()}.json')

    if isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as f:
            out = json.loads(f.read())
    elif isdir(dir_path):
        out = None
    else:
        mkdir(dir_path)
        out = None
    
    if out is None:
        print("Fetching and saving to cache file: ", file_path)
        resp = requests.get(url=api_endpoint, params=params, timeout=30)

        out = resp.json()
        if("error" in out):
            print(resp.text)
            raise Exception("Error in response");
    
        with open(file_path, mode='w', encoding='utf-8') as f:
            f.write(resp.text)
    else:
        print("Found response in cache: ", file_path)

    return out

def fetch_subcategories(category: list, api_endpoint:str):
    """
    Fetch the subcategories of the cateogry whose name is in the input parameter

    Example URL: https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&list=categorymembers&cmtype=subcat&cmtitle=Category:Certosa%20(Bologna)
    Other example URL, not used here: https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&gcmtitle=Category:Certosa%20(Bologna)&generator=categorymembers&prop=info
    """
    params = dict(
        action='query',
        format='json',
        formatversion='2',
        list='categorymembers',
        cmtype='subcat',
        cmlimit='500', # 500 = max
        cmtitle=category
    )
    return query_wikimedia_api(params, api_endpoint)["query"]["categorymembers"]

def fetch_category_details(names: list, api_endpoint:str):
    """
    Fetch the details of the categories whose names are in the input list

    Example URL: https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&prop=info&titles=Category:Certosa%20(Bologna)
    """
    params = dict(
        action='query',
        format='json',
        formatversion='2',
        prop="info|categories", # https://www.mediawiki.org/wiki/API:Properties
        titles='|'.join(names)
    )
    return query_wikimedia_api(params, api_endpoint)["query"]["pages"]

def fetch_articles(articles: list, api_endpoint:str):
    """
    Fetch the details of the articles whose names are in the input list 
    """
    # TODO

explored_categories = set()

def explore_category(category: list, g: nx.Graph, api_endpoint: str):
    """
    Recursive depth first exploration of the category graph
    """
    if(category in explored_categories):
        return
    
    print("Exploring category: ", category)
    subcategories = fetch_subcategories(category, api_endpoint)
    explored_categories.add(category)
    for subcategory in subcategories:
        # https://networkx.org/documentation/stable/reference/classes/generated/networkx.DiGraph.add_node.html#digraph-add-node
        # https://networkx.org/documentation/stable/reference/classes/generated/networkx.DiGraph.add_edge.html#digraph-add-edge
        g.add_edge(subcategory["title"], category)
        explore_category(subcategory["title"], g, api_endpoint)

def scrape(root_category: str, api_endpoint = "https://commons.wikimedia.org/w/api.php") -> nx.DiGraph:
    """
    Scrape the Wikipedia category tree starting from the root category
    """
    g = nx.DiGraph()
    explore_category(root_category, g, api_endpoint)
    return g

if __name__ == "__main__":
    graph = scrape('Category:Certosa (Bologna)', 'https://commons.wikimedia.org/w/api.php')

    plt.figure(figsize=(100, 100))
    nx.draw_networkx(graph, with_labels=False)
    plt.savefig("certosa.svg")

    nx.write_adjlist(graph, "certosa.tsv", delimiter='\t')

    print("Done!")
