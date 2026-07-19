import streamlit as st
import log_parser
import analyzer
import visualizer
st.title("AI Log Intelligence Platform")
uploaded_file = st.file_uploader(
    "Upload your log file", type=["log", "txt"]
)

st.write("Waiting for the log file to be uploaded...")

if uploaded_file is not None:
    logs = uploaded_file.read().decode("utf-8")
    st.success("Log file uploaded successfully!")
    
    parsed_logs_df = log_parser.parse_logs(logs)
    st.write(f"Total Parsed Logs: {len(parsed_logs_df)}")
    st.dataframe(parsed_logs_df.head(50), width="stretch")

    analysis_stats = analyzer.analyze_log(parsed_logs_df)
    st.data_editor(analysis_stats, use_container_width=True)

    fig1 = visualizer.plot_process_distribution(parsed_logs_df)
    fig2 = visualizer.plot_host_distribution(parsed_logs_df)
    fig3 = visualizer.plot_message_distribution(parsed_logs_df)

    st.plotly_chart(fig1)
    st.plotly_chart(fig2)
    st.plotly_chart(fig3)