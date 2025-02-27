import streamlit as st 
from streamlit_option_menu import option_menu
from streamlit.components.v1 import html
import os 
from dotenv import load_dotenv
import time
from PyPDF2 import PdfReader
load_dotenv()


if "user_info" not in st.session_state:
    st.session_state.user_info = {}

if "greeting_shown" not in st.session_state:
     st.session_state.greeting_shown = False

    

def typing_effect(text, speed = 0.1):
    placeholder = st.empty()
    output_text = ""
    for char in text:
        output_text += char 
        placeholder.markdown(f"<h1 style='text-align: center;'>{output_text}</h1>", unsafe_allow_html=True)
        time.sleep(speed)


if not st.session_state.greeting_shown:
    text = "Welcome to Study Buddy 🚀 "
    typing_effect(text,speed=0.05)    



def nav_page(page_name, timeout_secs=3):
    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)


st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")

disabled = True

category = st.selectbox("Please Select Your Category ", ["Grade 1","Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8","Grade 9","Grade 10","Grade 11","Grade 12","University Student", "Working Professional"])
topic = st.text_input("Select topic struggling with")


if category != "" and topic != "":
    disabled = False


st.session_state.user_info.update({
     "category" : category,
     "topic" : topic,
})


col1,col2,col3,col4 = st.columns([1,1,1,1], gap = "large")

st.write("")
st.write("")
st.write("")
st.write("")
with col4:
    col4_1,col4_2 = st.columns([1,2], gap = "small")
    with col4_2:
            button = st.button("Next 👉", disabled=disabled)

if button:
     nav_page("prompting_page")


