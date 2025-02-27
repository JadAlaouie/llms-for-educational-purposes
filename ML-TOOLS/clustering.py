import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from sklearn.cluster import KMeans

def display_scatter(data, clusters=None, k=None, title="Cluster Analysis"):
    if data.shape[1] < 2:
        st.error("Dataset must have at least two columns for plotting.")
        return
    
    x_col, y_col = data.columns[:2]
    
    fig, ax = plt.subplots()

    if clusters is None:
        ax.scatter(data[x_col], data[y_col], s=200, edgecolors="k")
    else:
        scatter = ax.scatter(data[x_col], data[y_col], s=200, c=clusters, cmap="viridis", edgecolors="k")

        if k is not None:
            cluster_colors = [scatter.cmap(scatter.norm(i)) for i in range(k)]
            legend_circles = [
                mlines.Line2D([], [], marker='o', linestyle='None', color='w', 
                              markerfacecolor=color, markersize=10, label=f'Cluster {i+1}')
                for i, color in enumerate(cluster_colors)
            ]
            ax.legend(handles=legend_circles, frameon=False)  

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title)

    st.pyplot(fig)

st.title("K-MEANS Clustering 📊")

if "data" not in st.session_state:
    st.session_state.data = None 

if "running" not in st.session_state:
    st.session_state.running = False 

with st.sidebar:
    uploaded_document = st.file_uploader("Upload CSV File", type="csv")
    number_of_clusters = st.text_input("Number of Clusters (default = 2)", value="2")
    run = st.button("Run K-Means Algorithm")

if uploaded_document:
    st.session_state.running = True
    st.session_state.data = pd.read_csv(uploaded_document)
    st.dataframe(st.session_state.data, width=600)
    
    if st.session_state.data.shape[1] >= 2:
        x_col, y_col = st.session_state.data.columns[:2]
        title_before = f"{x_col} vs {y_col}"
    else:
        title_before = "Scatter Plot"

    display_scatter(st.session_state.data, title=title_before)

if run and st.session_state.data is not None:
    try:
        k = int(number_of_clusters)
        
        num_cols = st.session_state.data.select_dtypes(include=["number"]).columns[:2]
        if len(num_cols) < 2:
            st.error("Dataset must have at least two numeric columns for clustering.")
        else:
            X = st.session_state.data[num_cols]
            kmeans = KMeans(n_clusters=k, random_state=42)
            clusters = kmeans.fit_predict(X)

            display_scatter(X, clusters, k, title="Cluster Analysis")

    except ValueError:
        st.error("Please enter a valid number for clusters.")
