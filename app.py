import streamlit as st

def main():
    # Set page config
    st.set_page_config(
        page_title="My Streamlit App",
        page_icon="🚀",
        layout="wide"
    )
    
    # Main page header
    st.title("Welcome to My Streamlit App")
    st.sidebar.success("Select a page above.")
    
    # Main page content
    st.markdown("""
    ### 👋 Welcome to our multi-page app!
    
    Select different pages from the sidebar to explore various features:
    
    - 📊 **Data Analysis**: Explore and visualize data
    - 🤖 **ML Models**: Try out machine learning models
    - ℹ️ **About**: Learn more about the project
    - 📁 **Uploaded Files**: View and manage uploaded files
    - 🔄 **Synthetic Data**: Generate synthetic data from uploaded files
    - 📋 **Metadata Manager**: Detect and manage metadata
    """)

if __name__ == "__main__":
    main()
