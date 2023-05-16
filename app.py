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
        

def get_random_n_students():
    """ Randomly draws a new value for n_students """
    st.session_state["n_students"] = route_variables.random_n_students()
    return


def generate_routes(n_students, n_schools, mode, location_data, max_routes, container):
    
    progress_value = 0
    progress_text = "Generating graph..."
    my_bar = container.progress(progress_value, text=progress_text)
    G = travel_times.generate_G(mode, location_data)
    
    progress_value += 10
    progress_text = 'Calculating travel times... (this may take a while!)'
    my_bar.progress(progress_value, text=progress_text)
    travel_time_table, coords = travel_times.calculate_travel_times(G, n_students, n_schools)
    
    progress_value += 40
    progress_text = 'Getting feasible routes...'
    my_bar.progress(progress_value, text=progress_text)
    routes = MIP.get_feasible_routes(n_students, n_schools, None, travel_time_table, coords, max_routes)
    
    progress_value += 20
    progress_text = 'Plotting routes...'
    my_bar.progress(progress_value, text=progress_text)
    plots = plot2.plot_our_routes(G, routes)
    
    progress_value += 30
    progress_text = 'Done!'
    my_bar.progress(progress_value, text=progress_text)
    
    if len(plots) > 0:
        container.write('Number of routes generated:')
        container.write(len(plots))
        for p in plots:
            container.pyplot(p)
            # container.write(p)
    else:
        container.write('No feasible routes found.')
        
    return coords, routes


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
    max_routes = plots_container.number_input('Max routes to generate:', 1, value=5)
    # generate = plots_container.button('Generate routes', 
    #                     on_click=generate_routes, 
    #                     args=(n_students, n_schools, mode, location_data, max_routes, plots_container)
    #                     )
    generate = plots_container.button('Generate routes')
    if generate:
        result = generate_routes(n_students, n_schools, mode, location_data, max_routes, plots_container)
    
        # st.write(result[0])
        # st.write(result[1])



if __name__ == '__main__':
    __init__()
    main()
