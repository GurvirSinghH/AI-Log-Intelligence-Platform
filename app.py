import streamlit as st

st.title("AI Log Intelligence Platform")
uploaded_file = st.file_uploader(
    "Upload your log file", type=["log", "txt"]
)

st.write("Waiting for the log file to be uploaded...")

if uploaded_file is not None:
    logs = uploaded_file.read().decode("utf-8")
    st.success("Log file uploaded successfully!")
    st.text(logs)