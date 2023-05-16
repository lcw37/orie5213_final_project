import osmnx as ox
import folium
import streamlit as st
from streamlit_folium import st_folium
import route_variables
import travel_times
import plot2
import MIP


def __init__():
    if "n_students" not in st.session_state:
        st.session_state["n_students"] = route_variables.random_n_students()
        

def display_map(location, distance, n_students, n_schools):
    G, coords = generate_locations(n_students, n_schools)
    # st.write(coords)
    # G = ox.graph_from_address(location, dist=distance, network_type='drive')
    fig, ax = ox.plot_graph(G, show=False, close=False)
    
    for id in coords:
        ax.scatter(coords[id][1], coords[id][0], c='red', s=100)
    
    return fig
    # map = folium.Map(location=ox.geocode(location), tiles='cartodbpositron')
    # st_map = st_folium(map, width=700, height=700)



def generate_locations(n_students, n_schools):
    G = travel_times.generate_G()
    coords = travel_times.generate_random_coords(G, n_students, n_schools)
    return G, coords
    

    
    ################
    
    
    
    
    
def get_random_n_students():
    """ Randomly draws a new value for n_students """
    st.session_state["n_students"] = route_variables.random_n_students()
    return

def generate_routes(n_students, n_schools, mode, location_data, container):
    routes, G = MIP.get_feasible_routes(n_students, n_schools, None, mode, location_data)
    plots = plot2.plot_our_routes(G, routes)
    container.write('number of routes generated:')
    container.write(len(plots))
    for p in plots:
        container.pyplot(p)
        # container.write(p)



def main():
    # page title
    st.title('Plot Points on a Map')
    
    col1, col2 = st.columns(2, gap='medium')
    
    # user inputs for number of students and schools
    with col1:
        n_students = st.number_input('Number of students (2-20):', 1, 20, st.session_state.n_students)
        rand_n_students = st.button('Randomize number of students', on_click=get_random_n_students)
    with col2:
        n_schools = st.number_input('Number of schools (1-7):', 1, 7, 2)
    
    st.divider()
    
    # select input mode
    # mode = st.selectbox('Location mode', ['name', 'bbox'])
    mode = st.checkbox('Boundary Box?')
    
    col1, col2 = st.columns(2, gap='medium')
    
    with col1:
        l_form = st.form('l_form')
        l_form.caption('Location Name')
        # user inputs for location and distance
        location = l_form.text_input('Location:', 'Queens, New York', disabled=mode)
        distance = l_form.slider('Distance (meters):', 1000, 5000, 2000, disabled=mode)
        submit = l_form.form_submit_button(label='Update', disabled=mode)
        
    with col2:
        # user inputs for bbox coords
        b_form = st.form('b_form')
        b_form.caption('Boundary Box')
        mincol, maxcol = b_form.columns(2)
        xmin = mincol.number_input('xmin:', value=travel_times.xmin, disabled=(not mode))
        ymin = mincol.number_input('ymin:', value=travel_times.xmax, disabled=(not mode))
        xmax = maxcol.number_input('xmax:', value=travel_times.ymin, disabled=(not mode))
        ymax = maxcol.number_input('ymax:', value=travel_times.ymax, disabled=(not mode))
        submit = b_form.form_submit_button(label='Update', disabled=(not mode))

    if not mode:
        location_data = (location, distance)
        mode = 'name'
    else:
        location_data = (40.708213, 40.662075, -73.961004, -73.906759)
        mode = 'bbox'
   
   
    # generate locations and plot on map
    plots_container = st.container()
    generate = plots_container.button('Generate routes', 
                        on_click=generate_routes, 
                        args=(n_students, n_schools, mode, location_data, plots_container)
                        )
    



if __name__ == '__main__':
    __init__()
    main()
