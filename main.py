import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64

# Function to load data
@st.cache_data
def load_data():
    return pd.read_json("contacttracing_data.json", lines=True)

# Function to get infected names
def get_infected_names(df, input_name):
    epsilon = 0.0018288  # 6ft in km
    model = DBSCAN(eps=epsilon, min_samples=2, metric='haversine').fit(df[['Latitude', 'Longitude']])
    df['cluster'] = model.labels_
    
    input_name_clusters = df.loc[df['User'] == input_name, 'cluster'].unique()
    
    infected_names = []
    for cluster in input_name_clusters:
        if cluster != -1:
            ids_in_cluster = df.loc[df['cluster'] == cluster, 'User']
            for member_id in ids_in_cluster:
                if member_id not in infected_names and member_id != input_name:
                    infected_names.append(member_id)
    
    return infected_names

# Function to send email alerts
def send_email_alerts(email_list, infected_person):
    # Email credentials
    EMAIL_ID = 'YOUR_MAIL_ID_@gmail.com'
    EMAIL_PASS = 'YOUR_PASSWORD'
    
    # SMTP server configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # Port for STARTTLS

    sent_emails = set()  # Track sent emails to avoid duplicates

    for recipient_email in email_list:
        if recipient_email not in sent_emails:
            # Create the email content
            message = MIMEMultipart()
            message['From'] = EMAIL_ID
            message['To'] = recipient_email
            message['Subject'] = "Health Contact Alert"
            
            body = (f"Dear User,\n\nYou have been identified as a close contact of {infected_person} "
                    "who has been affected by the flu virus. Please take necessary precautions and stay alert.\n\nStay safe!")
            message.attach(MIMEText(body, 'plain'))
            
            # Connect to the SMTP server and send the email
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as s:
                    s.starttls()  # Upgrade connection to TLS
                    s.login(EMAIL_ID, EMAIL_PASS)
                    s.send_message(message)
                st.success(f"Email sent to {recipient_email}")
                sent_emails.add(recipient_email)  # Mark email as sent
            except Exception as e:
                st.error(f"Failed to send email to {recipient_email}. Error: {e}")

# Function to add custom CSS for background
def add_custom_css(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded_string}");
            background-size: cover;
        }}
        .main {{
            background-color: rgba(255, 255, 255, 0.3);
            padding: 2rem;
            border-radius: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Add custom CSS for background
add_custom_css("virus.jpg")  # Replace with your image path

# Load data
df = load_data().copy()

# Streamlit UI
st.title("Contact Tracing using DBSCAN")

# User input
input_name = st.text_input("Enter infected person's name:")

if st.button("Get Details & Send Alert"):
    if input_name:
        infected_names = get_infected_names(df, input_name)
        if infected_names:
            st.success(f"Contacted Persons: {', '.join(infected_names)}")

            # Collect email addresses (assuming email addresses are in the dataframe)
            email_list = df.loc[df['User'].isin(infected_names), 'Email'].tolist()
            if email_list:
                send_email_alerts(email_list, input_name)
            else:
                st.info("No email addresses found for the contacted persons.")
        else:
            st.info("No contacts found.")
    else:
        st.error("Please enter a valid name.")
    
    # Display scatter plots
    st.write("### Scatter Plots")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 30))

    # First scatter plot
    sns.scatterplot(x='Latitude', y='Longitude', data=df, hue='User', ax=ax1, alpha=0.5)
    ax1.legend(bbox_to_anchor=[1, 0.8])
    ax1.set_title("Scatter Plot of Users")

    # DBSCAN clustering and second scatter plot
    model = DBSCAN(eps=0.0018288, min_samples=2, metric="haversine").fit(df[['Latitude', 'Longitude']])
    df['cluster'] = model.labels_
    sns.scatterplot(data=df, x='Latitude', y='Longitude', hue=['cluster-{}'.format(x) for x in model.labels_], ax=ax2, alpha=0.5)
    ax2.legend(bbox_to_anchor=[1, 1])
    ax2.set_title("DBSCAN Clustering")

    st.pyplot(fig)
