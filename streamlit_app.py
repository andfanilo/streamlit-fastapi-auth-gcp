import html
from datetime import datetime

import requests
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

st.title("Hello world")
st.sidebar.write(st.context.headers)
st.sidebar.write(st.context.cookies)


def st_redirect(url):
    source = f"location.href = '{url}'"
    wrapped_source = f"(async () => {{{source}}})()"
    st.markdown(
        f"""
        <div style="display:none" id="stredirect">
            <iframe src="javascript: \
                var script = document.createElement('script'); \
                script.type = 'text/javascript'; \
                script.text = {html.escape(repr(wrapped_source))}; \
                var thisDiv = window.parent.document.getElementById('stredirect'); \
                var rootDiv = window.parent.parent.parent.parent.document.getElementById('root'); \
                rootDiv.appendChild(script); \
                thisDiv.parentElement.parentElement.parentElement.style.display = 'none'; \
            "/>
        </div>
        """,
        unsafe_allow_html=True,
    )


# First, look for token cookies
if "__streamlit_session" not in st.context.cookies:
    if st.button("🔑 Login with Google", type="primary"):
        with st.spinner("Creating new session"):
            r = requests.post("https://fastapi.example.test/session")
            r.raise_for_status()
            resp = r.json()
        st_redirect(resp["auth_url"])
    st.stop()


# Tokens are in cookies
st.write(st.context.cookies)
credentials = Credentials(
    st.context.cookies["__streamlit_access_token"],
    # refresh_token=st.context.cookies["__streamlit_refresh_token"],
    # token_uri="token_uri",
    # client_id=st.secrets["client_id"],
    # client_secret=st.secrets["client_secret"],
)

id_info = id_token.verify_token(
    st.context.cookies["__streamlit_id_token"],
    Request(),
)
st.header(f"Hello {id_info['given_name']}")
st.image(id_info["picture"])

with st.expander("Upcoming Events in Google Calendar"):
    try:
        service = build("calendar", "v3", credentials=credentials)

        # Call the Calendar API for the next 10 events
        now = datetime.now().isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            st.info("No upcoming events found", icon="ℹ️")
            st.stop()

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            st.markdown(f":blue[{start}] - **{event['summary']}**")

    except HttpError as error:
        st.error(f"An error occurred: {error}")
