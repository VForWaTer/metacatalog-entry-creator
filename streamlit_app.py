import os
import json
from datetime import datetime as dt
import time

import streamlit as st
import pandas as pd


# load the BASE_DATA
with open(os.path.join(os.path.dirname(__file__), 'BASE_DATA.json')) as f:
    BASE_DATA = json.load(f)


# build the main application
st.set_page_config(page_title='Metacatalog Entry Creator', layout='wide')
st.title('Metacatalog Entry Creator')

# add the edit options
if st.session_state.get('edit_phase', False) != 'main':
    go_back = st.sidebar.button('BACK TO MAIN FORM')
else:
    go_back = None
add_author = st.sidebar.button('ADD NEW AUTHOR')
add_variable = st.sidebar.button('ADD NEW VARIABLE')
add_unit = st.sidebar.button('ADD NEW UNIT')

if go_back:
    st.session_state.edit_phase = 'main'
if add_author:
    st.session_state.edit_phase = 'author'
if add_variable:
    st.session_state.edit_phase = 'variable'
if add_unit:
    st.session_state.edit_phase = 'unit'

# check what the user is doing right now
edit_phase = st.session_state.get('edit_phase', 'main')

# EDIT AUTHOR
if edit_phase == 'author':
    st.markdown('## ADD NEW AUTHOR')
    with st.form('AUTHOR'):
        st.info('To save the author permanently, you need to save the full entry. Otherwise the author will be lost at the end of the session')

        first_name = st.text_input('FIRST NAME')
        last_name = st.text_input('LAST NAME')
        affiliation = st.text_input('AFFILIATION', help="The affiliation is the full organisation name, including the department and group if applicable")
        organisation_name = st.text_input('ORGANISATION', help="Only the affiliated organisation, without department and group")
        done = st.form_submit_button('SAVE NEW AUTHOR')

        if done:
            # add to the session
            if not 'author' in st.session_state:
                st.session_state.author = []
            st.session_state.author.append({
                'first_name': first_name,
                'last_name': last_name,
                'affiliation': affiliation,
                'organisation_name': organisation_name,
                'label': f'{first_name} {last_name}'
            })

            st.session_state.edit_phase = 'main'
            st.experimental_rerun()

# EDIT UNIT
elif edit_phase == 'unit':
    st.markdown('## ADD NEW UNIT')
    with st.form('UNIT'):
        st.info('To save the unit permanently, you need to save the full entry. Otherwise the unit will be lost at the end of the session')

        name = st.text_input('NAME', help="Please provide the full name of this unit.")
        symbol = st.text_input('SYMBOL', help="Abbreviate the unit with a commonly used symbol.")
        si = st.text_input('SI', help="If possible, give the SI version of this unit")
        done = st.form_submit_button('SAVE NEW UNIT')

        if done:
            # add to the session
            if not 'unit' in st.session_state:
                st.session_state.unit = []
            st.session_state.unit.append({
                'name': name,
                'symbol': symbol,
                'si': si,
                'label': f'{name} [{symbol}]'
            })

            st.session_state.edit_phase = 'main'
            st.experimental_rerun()

# EDIT VARIABLE
elif edit_phase == 'variable':
    st.markdown('## ADD NEW VARIABLE')
    with st.form('VARIABLE'):
        st.info('To save the variable permanently, you need to save the full entry. Otherwise the variable will be lost at the end of the session')

        name = st.text_input('NAME', help="Please provide the full name of this variable.")
        symbol = st.text_input('SYMBOL', help="Abbreviate the variable with a commonly used symbol.")
        column_name = st.text_input('COLUMN NAME', help="The column name of the variable(s) on export. Please separate by comma")
        
        UNIT = [*BASE_DATA.get('unit', []), *st.session_state.get('unit', [])]
        unit_label = st.selectbox('UNIT', options=[u['label'] for u in UNIT])
        done = st.form_submit_button('SAVE NEW VARIABLE')

        if done:
            # add to the session
            if not 'variable' in st.session_state:
                st.session_state.variable = []
            
            # extract the unit
            u = [u for u in UNIT if u['label'] == unit_label][0]
            if 'id' in u:
                unit = u['id']
            else:
                unit = {k:v for k,v in u.items() if k != 'label'}
            
            st.session_state.variable.append({
                'name': name,
                'symbol': symbol,
                'column_names': column_name.split(','),
                'unit': unit,
                'label': f'{name} [{symbol}]'
            })

            st.session_state.edit_phase = 'main'
            st.experimental_rerun()

# MAIN AREA
elif edit_phase == 'main':
    st.markdown("""
    Use the form below to create a Metacatalog Entry to be used in V-FOR-WaTer.

    The application will create a JSON file containing all necessary metadata. 
    """)
    st.info("Direct upload is not yet possible, please mail us the JSON for now.")

    # create the form
    # form = st.form('Entry')
    form = st.container()
    # form, json_preview = st.columns((6,4))
    title = form.text_input('TITLE', help="A title should be short, but uniquely indentifying your dataset.")

    entry_info = form.expander('BASE INFO', expanded=True)

    # add author
    AUTHOR = [*BASE_DATA.get('author',  []), *st.session_state.get('author', [])]
    author_label = entry_info.selectbox("FIRST AUTHOR", options=[a['label'] for a in AUTHOR])
    coauthors_labels = entry_info.multiselect('CO-AUTHORS', options=[a['label'] for a in AUTHOR if a['label'] != author_label])

    # add variable
    VARIABLE = [*BASE_DATA.get('variable', []), *st.session_state.get('variable', [])]
    variable_label = entry_info.selectbox("VARIABLE", options=[v['label'] for v in VARIABLE])

    # add license
    LICENSE = {l['id']: l['label'] for l in BASE_DATA.get('license', [])}
    license_id = entry_info.selectbox("LICENSE", options=list(LICENSE.keys()), format_func=lambda k: LICENSE[k])

    external_id = entry_info.text_input('EXTERNAL ID', help="If you have any kind of ID identifying your dataset in another repository, you can add it here for reference.")
    abstract = entry_info.text_area('ABSTRACT', help="Please provide any information that helps to understand your dataset.")
    entry_info.markdown('###### Location\nRight now you need to specify the WGS84 coordinate by hand.')
    c_l, c_r = entry_info.columns(2)

    lon = c_l.number_input('LONGITUDE', min_value=-180.0, max_value=180.0, step=1e-3, format='%.6f', value=8.415447)
    lat = c_r.number_input('LATITUDE', min_value=-90.0, max_value=90.0, step=1e-3, format='%.6f', value=49.010113)
    entry_info.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=12)
    embargo = entry_info.checkbox('Embargo this dataset for 2 years', help="The embargo will prevent public access to the data for 2 years.")

    # keywords
    keywords_expander = form.expander('CONTROLLED DICTIONARY / KEYWORDS', expanded=False)
    keywords_expander.info('Currently only GCMD keywords are supported. The keyword associated to the variable is added automatically')
    KW = BASE_DATA.get('keywords', {})
    if len(KW) > 0:
        keywords = keywords_expander.multiselect('KEYWORDS', options=list(KW.keys()), format_func=lambda k: KW[k])
    else:
        keywords = []

    # DETAILS
    detail_expander = form.expander('DETAILS', expanded=False)
    detail_expander.info('You can add arbitrary key-value pairs to the metadata set. These should be useful for working with the data')
    
    d_b_l, d_b_r, _ = detail_expander.columns((1,1,5))
    add_row = d_b_l.button('ADD NEW ROW')
    if add_row:
        if not 'details' in st.session_state:
            st.session_state.details = []
        
        st.session_state.details.append({'key': '', 'value': ''})

    # go through the details
    details = st.session_state.get('details', [])

    if len(details) > 0:
        remove_details = d_b_r.button('REMOVE DETAILS')
        if remove_details:
            st.session_state.details = []
            st.experimental_rerun()

        for i, d in enumerate(details):
            # add the input
            d_l,d_t, d_r = detail_expander.columns(3)
            details[i]['key'] = d_l.text_input('KEY', value=d['key'], key=f'detail_key_{i}')
            _type = d_t.selectbox('TYPE', options=['string', 'float', 'integer', 'date', 'boolean'], key=f'detail_type_{i}')
            if _type == 'boolean':
                details[i]['value'] = d_r.checkbox('VALUE', value=d['value'] if isinstance(d['value'], bool) else False, key=f'detail_value_{i}')
            elif _type == 'float':
                details[i]['value'] = d_r.number_input('VALUE', value=d['value'] if isinstance(d['value'], float) else 42.5, key=f'detail_value_{i}')
            elif _type == 'integer':
                details[i]['value'] = d_r.number_input('VALUE', value=d['value'] if isinstance(d['value'], int) else 42, key=f'detail_value_{i}')
            elif _type == 'date':
                details[i]['value'] = d_r.date_input('VALUE', value=d['value'] if isinstance(d['value'], dt) else dt.now(), key=f'detail_value_{i}')
            else:
                details[i]['value'] = d_r.text_input('VALUE', value=d['value'] if isinstance(d['value'], str) else str(d['value']), key=f'detail_value_{i}')

            # add back
            st.session_state.details = details    
    
    # TODO only show if the base data is available
    submit = form.button('CREATE')

    if submit:
        # todo - add to session - rerun and present in a clean page?

        data = dict(
            title=title,
            abstract=abstract,
            external_id=external_id,
            location=f'SRID=4326;POINT ({lon} {lat})',
            embargo=embargo,
            license={'id': license_id},
            keywords=keywords
        )

        # handle author
        _author = [a for a in AUTHOR if a['label']==author_label][0]
        if 'id' in _author:
            data['author'] = _author['id']
        else:
            data['author'] = {k: v for k,v in _author.items() if k != 'label'}
        
        # handle co-authors
        _coauthors = [a for a in AUTHOR if a['label'] in coauthors_labels]
        if len(_coauthors) > 0:
            data['coauthors'] = []
            for a in _coauthors:
                if 'id' in a:
                    data['coauthors'].append({'id': a['id']})
                else:
                    data['coauthors'].append({k: v for k,v in a.items() if k!='label'})
        
        # handle variable
        _variable = [v for v in VARIABLE if v['label']==variable_label][0]
        if 'id' in _variable:
            data['variable'] = _variable['id']
        else:
            data['variable'] = {k: v for k,v in _variable.items() if k != 'label'}
        
        # handle details
        if len(details) > 0:
            data['details'] = []
            for d in details:
                data['details'].append({'key': d['key'], 'value': d['value']})

        # handle saving
        st.session_state.data = data
        st.session_state.edit_phase = 'finishing'
        st.experimental_rerun() 

elif edit_phase == 'finishing': 
    data = st.session_state.get('data')

    if data is None:
        st.error("Your data got lost in the session. Don't know why.")
    
    # show the preview
    st.markdown("This is a preview of the data created. It can be used by the metacatalog Python API to create the `Entry` in the database.")
    opts, preview = st.columns((3,7))
        
    fmt = opts.radio('Format', options=['JSON', 'Python code'])

    if fmt == 'JSON':
        preview.json(data)
    elif fmt == 'Python code':
        code = f"""from metacatalog import api\
        \rfrom metacatalog.models import Entry\
        \rimport json
        \rsession = api.connect_database()
        \rjson_content = json.loads(\"\"\"{json.dumps(data)}\"\"\")\
        \rentry = Entry.from_json(json_content, session=session)
        """
        st.info("The `Entry.from_json` is still under development and might not yet be available.")
        st.code(code)

else:
    st.error('APPLICATION is in an undefined state.')