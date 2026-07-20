import streamlit as st
import log_parser
import analyzer
import visualizer
import feature_engineering
import anomaly_detector

st.title("AI Log Intelligence Platform")
uploaded_file = st.file_uploader(
    "Upload your log file", type=["log", "txt"]
)

st.write("Waiting for the log file to be uploaded...")

if uploaded_file is not None:
    logs = uploaded_file.read().decode("utf-8")
    st.success("Log file uploaded successfully!")
    
    parsed_logs_df = log_parser.parse_logs(logs)
    st.subheader("Parsed Log Entries")
    st.write("The uploaded log file has been parsed into structured fields for further analysis.")
    st.write(f"Total Parsed Logs: {len(parsed_logs_df)}")
    st.dataframe(parsed_logs_df.head(50), width="stretch")

    st.subheader("Log Analysis Statistics")
    st.write("Summary statistics generated from the uploaded parsed log entries.")
    analysis_stats = analyzer.analyze_log(parsed_logs_df)
    st.data_editor(analysis_stats, width="stretch")

    st.subheader("Log Data Visualizations")
    st.write("Visual representations of process, host, and message distributions.") 
    fig1 = visualizer.plot_process_distribution(parsed_logs_df)
    fig2 = visualizer.plot_host_distribution(parsed_logs_df)
    fig3 = visualizer.plot_message_distribution(parsed_logs_df)
    st.plotly_chart(fig1)
    st.plotly_chart(fig2)
    st.plotly_chart(fig3)

    st.subheader("Feature Matrix")
    st.write("The parsed logs are transformed into numerical features used by the Isolation Forest model.")
    features = feature_engineering.create_features(parsed_logs_df)
    st.dataframe(features.head(20), width="stretch")
    
    results = anomaly_detector.detect_anomalies(features)
    parsed_logs_df["anomaly"] = results["anomaly"]
   
    st.subheader("📋 Parsed Log Entries")
    st.write("The uploaded log file has been parsed into structured fields.")
    st.dataframe(parsed_logs_df.head(20), width="stretch")
    
    st.subheader("Anomaly Detection")
    normal_logs = (features["anomaly"] == 0).sum()
    anomalous_logs = (features["anomaly"] == 1).sum()
    st.write(f"**Normal Logs:** {normal_logs}")
    st.write(f"**Anomalous Logs:** {anomalous_logs}")

    anomalies = parsed_logs_df[parsed_logs_df["anomaly"] == 1]
    st.write("The following log entries were identified as anomalous by the Isolation Forest model.")
    st.dataframe(anomalies.head(50), width="stretch")