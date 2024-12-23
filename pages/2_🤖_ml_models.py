import streamlit as st

st.title("Machine Learning Models")

st.markdown("""
### ML Models Page

Select a model and make predictions:
""")

model_option = st.selectbox(
    'Choose a model',
    ('Linear Regression', 'Random Forest', 'Neural Network')
)

if st.button('Run Model'):
    st.info(f"Running {model_option} model...") 