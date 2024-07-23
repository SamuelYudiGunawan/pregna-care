import streamlit as st
import requests
import time
from dotenv import load_dotenv
import os
import plotly.graph_objects as go
import pandas as pd
import numpy as np

load_dotenv()

# API URLs
predict_url = os.getenv("PREDICT_URL")
upload_url = os.getenv("UPLOAD_URL")
get_all_data_url = os.getenv("GET_ALL_DATA_URL")
get_5min_data_url = os.getenv("GET_5MIN_DATA_URL")
get_avg_data_url = os.getenv("GET_AVG_DATA_URL")
get_latest_data_url = os.getenv("GET_LATEST_DATA_URL")
chat_url = os.getenv("AI_CHAT_URL")


# Function to fetch the latest data
def fetch_data():
    response = requests.get(get_all_data_url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: Unable to fetch data {response}")
        return None


# Function to create a gauge chart with conditional coloring
def create_gauge(title, value, min_value, max_value, threshold):
    color = "green" if value < threshold else "red"

    fig = go.Figure(
        go.Indicator(
            domain={"x": [0, 1], "y": [0, 1]},
            value=value,
            mode="gauge+number",
            title={"text": title},
            gauge={"axis": {"range": [min_value, max_value]}, "bar": {"color": color}},
        )
    )
    return fig


st.markdown(
    """
        <style>
        [data-testid="stMetricValue-small"] {
            font-size: 20px;
        }
        .metric-label {
            font-size: 12px;
            color: gray;
        }
        .metric-value {
            font-size: 20px;
        }
        .icon-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 15px;
            height: 100%;
        }
        .icon {
            font-size: 50px;
        }
        .metric-container{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
        </style>
        """,
    unsafe_allow_html=True,
)

def display_data(data, label, metric):
    # Display min, max, avg, and line chart for each data
    min_value = min(data)
    max_value = max(data)
    avg_value = np.mean(data)
    latest_value = data[-1]

    pad, icon, met = st.columns([0.1, 0.2, 0.7])
    with pad:
        st.write(" ")
    with icon:
        if(label == "Body Temperature"):
            st.markdown(f"<div class='icon-container'><div class='icon'>🌡️</div></div>", unsafe_allow_html=True)
        elif(label == "SPO2"):
            st.markdown(f"<div class='icon-container'><div class='icon'>🩸</div></div>", unsafe_allow_html=True)
        elif(label == "Heart Rate"):
            st.markdown(f"<div class='icon-container'><div class='icon'>💓</div></div>", unsafe_allow_html=True)
        elif(label == "Blood Sugar"):
            st.markdown(f"<div class='icon-container'><div class='icon'>🍭</div></div>", unsafe_allow_html=True)
    with met:
        st.metric(label, value=f"{latest_value:.2f} {metric}", delta=f"{(latest_value - data[-2]):.2f} {metric}", delta_color="normal")
    
    info1, info2, info3 = st.columns(3)
    info1.markdown(
        f"<div class='metric-label'>Min</div><div class='metric-value'>{min_value:.1f} {metric}</div>",
        unsafe_allow_html=True,
    )
    info2.markdown(
        f"<div class='metric-label'>Max</div><div class='metric-value'>{max_value:.1f} {metric}</div>",
        unsafe_allow_html=True,
    )
    info3.markdown(
        f"<div class='metric-label'>Avg</div><div class='metric-value'>{avg_value:.1f} {metric}</div>",
        unsafe_allow_html=True,
    )

def spacer(len):
    for i in range(len):
        st.write("")

def summary_section(df):
    col1, col2 = st.columns(2)
    with col1:
        display_data(list(df["body_temperature"]), "Body Temperature", "°F")
    with col2:
        display_data(list(df['spo2']), "SPO2", "%")
    spacer(3)
    col3, col4 = st.columns(2)
    with col3:
        display_data(list(df['heart_rate']), "Heart Rate", "bpm")
    with col4:
        display_data(list(df['bs']), "Blood Sugar", "mg/dL") 

def display_risk():
    # risk_level = requests.post(predict_url, json={"age": st.session_state.age}).json()['risk_level']
    risk_level = "Low Risk"
    color_map = {
        "Low Risk": "#00cc44",  # Green
        "Medium Risk": "#ffcc00",  # Yellow
        "High Risk": "#ff3333"  # Red
    }
    
    icon_map = {
        "Low Risk": "🟢",
        "Medium Risk": "🟡",
        "High Risk": "🔴"
    }

    st.markdown(
        f"""
        <style>
        .risk-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            border: 2px solid {color_map[risk_level]};
            border-radius: 10px;
            padding: 20px;
            margin: 10px;
        }}
        .risk-category {{
            font-size: 30px;
            font-weight: bold;
            color: {color_map[risk_level]};
        }}
        .risk-icon {{
            font-size: 60px;
        }}
        .risk-probability {{
            font-size: 20px;
            color: gray;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="risk-container">
            <div class="risk-icon">{icon_map[risk_level]}</div>
            <div class="risk-category">{risk_level}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def stream_generator(prompt):
    response = requests.post(chat_url, json={"prompt": prompt}).json()["response"]
    # Change \n to <br> for HTML rendering
    response = response.replace("\n", "<br>")
    yield response

def chatbot():
    st.title("Chatbot")
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        response_content = ""
        with st.chat_message("assistant"):
            for word in stream_generator(prompt):
                response_content += word
            st.markdown(response_content.replace("<br>", "  \n"), unsafe_allow_html=True)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response_content.replace("<br>", "  \n")})

# Maternal Risk Detection
def main(age):
    st.title("Maternal Risk Detection 🤰")
    with st.expander("About"):
        st.write(
            """
            This application is built to help detect the risk level of maternal health. 
            It uses the data from the sensors to predict the risk level of the patient. 
            The risk level is classified into three categories: Low Risk, Medium Risk, and High Risk.
            
            Chatbot is available on the sidebar to help you with any questions related to maternal health.
            """
        )
    with st.sidebar:
        chatbot()
    while True:
        data = fetch_data()
        data = pd.DataFrame(data)
        if len(data) == 0:
            st.write("No data available. Please check the sensor connection.")
        else:
            display_risk()
            spacer(3)
            summary_section(data)
            spacer(3)

        time.sleep(3)
        st.rerun()


if __name__ == "__main__":
    if "age" not in st.session_state:
        st.session_state.age = None

    if st.session_state.age is None:
        st.title("Welcome to Maternal Risk Detection")
        st.write("Please enter your age to continue.")
        age = st.number_input("Age:", min_value=1, max_value=120, step=1)
        if st.button("Submit"):
            st.session_state.age = age
            st.rerun()  # Rerun to update the state and proceed to main app
    else:
        main(st.session_state.age)
