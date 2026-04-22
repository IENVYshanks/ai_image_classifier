import os

import requests
import streamlit as st
from streamlit_google_picker import google_picker


@st.cache_data(show_spinner=False)
def get_drive_file_metadata(file_id: str, token: str) -> dict:
    response = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"fields": "id,name,parents"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def build_drive_directory(file_id: str, token: str, parents: list[str] | None = None) -> str:
    if parents is None:
        metadata = get_drive_file_metadata(file_id, token)
        parents = metadata.get("parents", [])

    if not parents:
        return "My Drive"

    parts: list[str] = []
    current_parent = parents[0]

    while current_parent:
        folder_metadata = get_drive_file_metadata(current_parent, token)
        parts.append(folder_metadata.get("name", current_parent))
        next_parents = folder_metadata.get("parents", [])
        current_parent = next_parents[0] if next_parents else ""

    return " / ".join(reversed(parts))


st.title("AI Image Classifier")

if not st.user.is_logged_in:
    st.write("Sign in with Google to continue.")
    if st.button("Authenticate with Google"):
        st.login("google")
else:
    st.success(f"Signed in as {st.user.email}.")
    st.write("Authentication successful! You can now use the AI Image Classifier.")

    access_token = st.user.tokens.get("access")
    if access_token:
        st.session_state["token"] = {"access_token": access_token}

    token_state = st.session_state.get("token", {})
    token = token_state.get("access_token")
    client_id = os.environ.get("GOOGLE_CLIENT_ID") or st.secrets["auth"]["google"]["client_id"]
    api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets["google_picker"]["api_key"]
    app_id = client_id.split("-")[0] if client_id else ""

    if not token:
        st.warning(
            "Google Drive access token is not available. Sign out and sign in again after updating the OAuth consent settings."
        )
    elif not client_id or not api_key or not app_id:
        st.warning(
            "Set `GOOGLE_CLIENT_ID` and `GOOGLE_API_KEY`, or provide them through Streamlit secrets, to enable the Google file picker."
        )
    else:
        st.subheader("Google Drive")
        st.caption(
            "Use Google Picker to choose the specific Drive files this app can access."
        )

        uploaded_files = google_picker(
            label="Pick files from Google Drive",
            token=token,
            apiKey=api_key,
            appId=app_id,
            accept_multiple_files=True,
            type=["pdf", "png", "jpg"],
            allow_folders=True,
            nav_hidden=False,
            key="google_picker",
        )

        if uploaded_files:
            st.success(f"Selected {len(uploaded_files)} file(s) from Google Drive.")
            selected_rows = []
            for uploaded_file in uploaded_files:
                size_bytes = uploaded_file.size if uploaded_file.size is not None else "unknown"
                parent_ids = uploaded_file.metadata.get("parents", [])
                directory = build_drive_directory(uploaded_file.id, token, parent_ids)
                selected_rows.append(
                    {
                        "filename": uploaded_file.name,
                        "directory": directory,
                        "size_bytes": size_bytes,
                    }
                )
                st.write(f"Filename: {uploaded_file.name}")
                st.write(f"Directory: {directory}")
                st.write(f"Size: {size_bytes}")
                data = uploaded_file.read()
                st.write(f"Bytes: {len(data)}")

            st.dataframe(selected_rows, use_container_width=True)

    if st.button("Log out"):
        st.logout()
