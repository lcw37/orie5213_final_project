import route_variables
import travel_times
from app_generate_plots import *

import streamlit as st


def _setup():
    if "n_students" not in st.session_state:
        get_random_n_students()
    if "n_schools" not in st.session_state:
        get_random_n_schools()
    pass
        




def main():
    
    ### page config
    st.set_page_config(page_title='Bus Route Builder',
                       page_icon=':bus',
                       layout='centered',
                       menu_items={
                        #    'Get Help': ''  TODO add our emails to the app
                        'About': 'Use this app to generate artificial bus routes.'
                                  }
                       )
    
    st.title('Bus Route Generation')
    
    # ======================================
    ### 1 Route Variables:
    st.divider()
    st.header('1 Route Variables', 'route_vars')
    
    ## number of students and randomize button
    c1, c2 = st.columns(2, gap='medium')
    n_students = c1.number_input('Number of students (2-20):', 1, 20, st.session_state.n_students)
    c2.markdown('#') # vertical spacer on right side
    c2.button('Randomize number of students', on_click=get_random_n_students)

    ## number of schools and randomize button
    c1, c2 = st.columns(2, gap='medium')
    n_schools = c1.number_input('Number of schools (1-7):', 1, 7, st.session_state.n_schools)
    c2.markdown('#') # vertical spacer on right side
    c2.button('Randomize number of schools', on_click=get_random_n_schools)
    
    # ======================================
    ### 2 Set Location
    st.divider()
    st.header('2 Set Location', 'location')
    
    ## select input mode
    bbox_bool = st.checkbox('Boundary Box?')
    
    ## input location by name
    col1, col2 = st.columns(2, gap='medium')
    with col1:
        l_form = st.form('l_form')
        l_form.caption('Location Name')
        # user inputs for location and distance
        location = l_form.text_input('Location:', 'Greenpoint, New York', disabled=bbox_bool)
        distance = l_form.slider('Distance (meters):', 1000, 5000, 2000, disabled=bbox_bool)
        l_form.form_submit_button(label='Update', disabled=bbox_bool)
    
    ## input location by bbox
    with col2:
        b_form = st.form('b_form')
        b_form.caption('Boundary Box')
        mincol, maxcol = b_form.columns(2)
        # user inputs for bbox coords
        xmin = mincol.number_input('xmin:', value=travel_times.xmin, disabled=(not bbox_bool))
        ymin = mincol.number_input('ymin:', value=travel_times.ymin, disabled=(not bbox_bool))
        xmax = maxcol.number_input('xmax:', value=travel_times.xmax, disabled=(not bbox_bool))
        ymax = maxcol.number_input('ymax:', value=travel_times.ymax, disabled=(not bbox_bool))
        b_form.form_submit_button(label='Update', disabled=(not bbox_bool))

    ## set location data mode based on whether location name or bbox was given
    if not bbox_bool:
        mode = 'name'
        location_data = (location, distance)
    else:
        mode = 'bbox'
        location_data = (ymax, ymin, xmin, xmax)
        
    # ======================================
    ### 3 Generate Points
    st.divider()
    st.header('3 Generate Points', 'points')
        
    points = st.button('Generate points')
    points_container = st.empty()
    if points:
        with st.spinner(f'Generating graph with {n_students} students and {n_schools} schools...'):
            generate_points(n_students, n_schools, mode, location_data, points_container) # need to save this to session_state

    # ======================================
    ### 4 Generate Routes
    st.divider()
    st.header('4 Generate Routes', 'routes')

    ## generate routes and plots
    plots_container = st.container() # TODO st.empty()?
    max_routes = plots_container.number_input('Max routes to generate:', 1, value=5)
    generate = plots_container.button('Generate routes')
    if generate:
        if 'coords' in st.session_state: # check that coordinates have been generated first
            plot_points(G=st.session_state.G,
                        coords=st.session_state.coords,
                        color_mapping=st.session_state.color_mapping, 
                        container=points_container)
            routes, start_time_solutions = generate_routes(G=st.session_state.G, 
                                                        n_students=n_students, 
                                                        n_schools=n_schools, 
                                                        coords=st.session_state.coords, 
                                                        max_routes=max_routes, 
                                                        container=plots_container)
        else:
            plots_container.write('Generate points first!')
    
        # st.write(result[0])
        # st.write(result[1])



if __name__ == '__main__':
    _setup()
    main()
