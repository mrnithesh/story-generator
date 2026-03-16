import hmac
import os
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()


def get_login_credentials():
    try:
        username = st.secrets.get("APP_USERNAME")
        password = st.secrets.get("APP_PASSWORD")
    except StreamlitSecretNotFoundError:
        username = None
        password = None

    username = username or os.environ.get("APP_USERNAME")
    password = password or os.environ.get("APP_PASSWORD")
    return username, password


def verify_login(username, password):
    configured_username, configured_password = get_login_credentials()
    if not configured_username or not configured_password:
        return False, "Login credentials are not configured. Set APP_USERNAME and APP_PASSWORD in your environment or Streamlit secrets."

    is_valid = hmac.compare_digest(username, configured_username) and hmac.compare_digest(password, configured_password)
    if not is_valid:
        return False, "Invalid username or password."

    return True, ""


def render_login_page():
    st.title("🔐 Login")
    st.write("Sign in to access the AI Story Generator.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        is_valid, error_message = verify_login(username, password)
        if is_valid:
            st.session_state["authenticated"] = True
            st.session_state["authenticated_user"] = username
            st.rerun()

        st.error(error_message)


def render_story_generator():
    st.title("📚 AI Story Generator")
    st.write("Create personalized stories with artificial intelligence!")

    with st.sidebar:
        st.success(f"Signed in as {st.session_state.get('authenticated_user', 'user')}")
        if st.button("Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state.pop("authenticated_user", None)
            st.rerun()

def generate(theme, age_group, length, custom_prompt=""):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    base_prompt = f"""Create a {length}-word story suitable for {age_group} age group with the theme of {theme}."""
    
    if custom_prompt:
        base_prompt += f"\nIncorporate the following elements: {custom_prompt}"

    prompt = base_prompt

    model = "gemini-flash-lite-latest"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text="Generate an engaging story that is appropriate for the specified age group."),
        ],
    )

    story = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        story += chunk.text
    return story

def main():
    st.set_page_config(page_title="Story Generator", page_icon="📚", layout="wide")
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    # Apply custom CSS
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .story-container {
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            background: #f7f9fc;
            border: 1px solid #dbe4f0;
        }
        </style>
    """, unsafe_allow_html=True)

    if not st.session_state["authenticated"]:
        render_login_page()
        return

    render_story_generator()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Story Settings")
        theme = st.selectbox(
            "Choose your story theme",
            ["Adventure", "Fantasy", "Science Fiction","Romance", "Moral Story", "Fairy Tale", "Mystery", 
             "Educational", "Historical", "Comedy", "Animal Story"]
        )

        age_group = st.radio(
            "Target age group",
            ["3-6 years", "7-12 years", "13-16 years", "16+ years"],
            horizontal=True
        )

    with col2:
        st.markdown("### Story Length")
        length = st.number_input(
            "Approximate word count",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            help="Choose the approximate length of your story in words"
        )

    st.markdown("### Customize Your Story")
    custom_prompt = st.text_area(
        "Add your creative elements (optional)",
        placeholder="Example: Include a brave princess, a magical forest, and talking animals",
        help="Add specific elements you'd like to include in your story"
    )

    if st.button("✨ Generate Story", use_container_width=True):
        with st.spinner("Crafting your magical story..."):
            story = generate(theme, age_group, length, custom_prompt)
            st.markdown("### 📖 Your Story")
            st.markdown(
                f"""<div class="story-container">{story}</div>""", 
                unsafe_allow_html=True
            )
            
            # Add download button
            st.download_button(
                label="Download Story",
                data=story,
                file_name=f"{theme.lower()}_story.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
