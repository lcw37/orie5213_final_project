import taxicab as tc
from taxicab.plot import plot_graph_route
from osmnx.plot import _save_and_show
import networkx as nx

def plot_graph_routes(G, routes, route_colors="r", route_linewidths=4, **pgr_kwargs):
    """
    Plot several routes along a graph.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    routes : list
        routes as a list of lists of node IDs
    route_colors : string or list
        if string, 1 color for all routes. if list, the colors for each route.
    route_linewidths : int or list
        if int, 1 linewidth for all routes. if list, the linewidth for each route.
    pgr_kwargs
        keyword arguments to pass to plot_graph_route

    Returns
    -------
    fig, ax : tuple
        matplotlib figure, axis
    """
    # check for valid arguments
    # if not all(isinstance(r, list) for r in routes):  # pragma: no cover
    #     raise ValueError("routes must be a list of route lists")
    if not all(isinstance(r, tuple) for r in routes):  # pragma: no cover
        raise ValueError("routes must be a list of route tuples")
    
    if len(routes) < 2:  # pragma: no cover
        raise ValueError("You must pass more than 1 route")
    if isinstance(route_colors, str):
        route_colors = [route_colors] * len(routes)
    if len(routes) != len(route_colors):  # pragma: no cover
        raise ValueError("route_colors list must have same length as routes")
    if isinstance(route_linewidths, int):
        route_linewidths = [route_linewidths] * len(routes)
    if len(routes) != len(route_linewidths):  # pragma: no cover
        raise ValueError("route_linewidths list must have same length as routes")

    # plot the graph and the first route
    override = {"route", "route_color", "route_linewidth", "show", "save", "close"}
    kwargs = {k: v for k, v in pgr_kwargs.items() if k not in override}
    fig, ax = plot_graph_route(
        G,
        route=routes[0],
        route_color=route_colors[0],
        route_linewidth=route_linewidths[0],
        show=False,
        save=False,
        close=False,
        **kwargs,
    )

    # plot the subsequent routes on top of existing ax
    override.update({"ax"})
    kwargs = {k: v for k, v in pgr_kwargs.items() if k not in override}
    r_rc_rlw = zip(routes[1:], route_colors[1:], route_linewidths[1:])
    for route, route_color, route_linewidth in r_rc_rlw:
        fig, ax = plot_graph_route(
            G,
            route=route,
            route_color=route_color,
            route_linewidth=route_linewidth,
            show=False,
            save=False,
            close=False,
            ax=ax,
            **kwargs,
        )

    # save and show the figure as specified, passing relevant kwargs
    sas_kwargs = {"save", "show", "close", "filepath", "file_format", "dpi"}
    kwargs = {k: v for k, v in pgr_kwargs.items() if k in sas_kwargs}
    fig, ax = _save_and_show(fig, ax, show=False, **kwargs)
    return fig, ax



def plot_our_route(G, route):
    
    route_pairs = list(zip(route[:-1], route[1:]))

    # get shortest path between route nodes
    route_legs = []
    for orig, dest in route_pairs:
        try:
            leg = tc.distance.shortest_path(G, orig, dest)
        # if no path exists between two points:
        except nx.NetworkXNoPath: 
            return None, None
        route_legs.append(leg)
        
    # assign alternating colors to route legs
    colors = ['r', 'orange', 'yellow']
    route_colors = []
    for i in range(len(route_legs)):
        route_colors.append(colors[i % len(colors)])
        
    # plot route
    fig, ax = plot_graph_routes(G, route_legs, route_colors)
    return fig, ax



def plot_our_routes(G, routes):
    print('Plotting routes...')
    figs = []
    for route in routes:
        
        # initial check
        if not all(isinstance(r, tuple) for r in route):
            continue
        
        fig, ax = plot_our_route(G, route) # returns None, None if no path exists
        # for n in route:
            # ax.scatter(n[1], n[0], c='blue', s=100)
            # print(n)
        if fig is not None:
            figs.append(fig)
    return figs