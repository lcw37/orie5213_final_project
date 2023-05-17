import route_variables
import travel_times
import plot2
import MIP

import streamlit as st
import osmnx as ox
import numpy as np




def get_random_n_students():
    """ Randomly draws a new value for n_students """
    st.session_state["n_students"] = route_variables.random_n_students()
    return

def get_random_n_schools(max_schools):
    """ Randomly draws a new value for n_schools """
    max_schools = min(7, st.session_state.n_students) # number of schools cannot exceed number of students, up to max of 7 schools
    st.session_state["n_schools"] = np.random.randint(1, max_schools+1)
    return

def generate_points(n_students, n_schools, mode, location_data, container):
    # spinner
    with st.spinner():
        # generate graph and coordinates
        G = travel_times.generate_G(mode, location_data)
        coords = travel_times.generate_random_coords(G, n_students, n_schools, depot_coords=(40.7283, -73.94060)) # (y, x)
        # save graph and coordinates to st.session_state
        st.session_state['coords'] = coords
        st.session_state['G'] = G
        # plot graph and coordinates
        plot_points(G, coords, container)
    return

def plot_points(G, coords, container):
    fig, ax = ox.plot_graph(G)
    for node in coords:
        y, x = coords[node]
        ax.scatter(x=x, y=y, s=200, c='r')#color_mapping[(y, x)]) TODO map these points to colors
    # save the coordinate graph to session_state
    st.session_state['points_fig'] = fig
    container.pyplot(st.session_state.points_fig)
    return


def generate_routes(G, n_students, n_schools, coords, max_routes, container):
    progress_value = 0
    progress_text = "Generating graph..."
    my_bar = container.progress(progress_value, text=progress_text)
    progress_value += 10
    
    progress_text = 'Calculating travel times... (this may take a while!)'
    my_bar.progress(progress_value, text=progress_text)
    travel_time_table = travel_times.calculate_travel_times(G, n_students, n_schools, coords)
    progress_value += 40

    progress_text = 'Getting start times...'
    my_bar.progress(progress_value, text=progress_text)
    starting_times = MIP.generate_start_times(n_schools)
    progress_value += 10
    
    progress_text = 'Getting feasible routes...'
    my_bar.progress(progress_value, text=progress_text)
    routes, start_time_solutions  = MIP.get_feasible_routes(n_students, n_schools, starting_times, travel_time_table, coords, max_routes)
    progress_value += 20

    progress_text = 'Plotting routes...'
    my_bar.progress(progress_value, text=progress_text)
    plots = plot2.plot_our_routes(G, routes, coords, n_students, n_schools)
    progress_value += 20
    
    progress_text = 'Done!'
    my_bar.progress(progress_value, text=progress_text)
    
    if len(plots) > 0:
        container.write('Number of routes generated:')
        container.write(len(plots))
        for i in range(len(plots)):
            container.pyplot(plots[i])
            container.write(routes[i])
            container.write(start_time_solutions[i])
            # container.write(p)
    else:
        container.write('No feasible routes found.')
        
    return routes, start_time_solutions
