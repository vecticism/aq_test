import streamlit as st
from unidecode import unidecode
import pandas as pd
from io import BytesIO
import nltk

nltk.download('punkt')

# Apply Alphanumeric Qabbala
def alphanumeric_qabbala_sum(text):
    qabbala_values = {chr(i + 96): i + 9 for i in range(1, 27)}
    qabbala_values.update({str(i): i for i in range(10)})
    text = unidecode(text)  # Normalize the text to replace accented characters
    standardized_text = ''.join(char.lower() for char in text if char.isalnum())  # Standardize text: remove non-alphanumeric and convert to lowercase
    return sum(qabbala_values[char] for char in standardized_text)

# Sanitize text for Excel
def sanitize_text(text):
    # Remove characters not allowed in Excel cells
    return ''.join(char for char in text if char not in ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0B', '\x0C', '\x0E', '\x0F', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1A', '\x1B', '\x1C', '\x1D', '\x1E', '\x1F'])

# Process text and calculate AQ values
def process_text(input_text, mode, incremental):
    results = []
    if mode == 'Prose':
        sentences = nltk.sent_tokenize(input_text)
        for sentence in sentences:
            sanitized_sentence = sanitize_text(sentence)
            if sanitized_sentence:
                if incremental:
                    results.extend(incremental_aq_values(sanitized_sentence))
                else:
                    aq_value = alphanumeric_qabbala_sum(sanitized_sentence)
                    results.append((sanitized_sentence, aq_value))
    else:  # Poetry
        lines = input_text.split('\n')
        for line in lines:
            sanitized_line = sanitize_text(line)
            if sanitized_line:
                if incremental:
                    results.extend(incremental_aq_values(sanitized_line))
                else:
                    aq_value = alphanumeric_qabbala_sum(sanitized_line)
                    results.append((sanitized_line, aq_value))
    return results

# Calculate incremental AQ values
def incremental_aq_values(text):
    words = text.split()
    incremental_results = []
    for i in range(1, len(words) + 1):
        partial_text = ' '.join(words[:i])
        aq_value = alphanumeric_qabbala_sum(partial_text)
        incremental_results.append((partial_text, aq_value))
    return incremental_results

# Save results to Excel
def save_to_excel(results):
    df = pd.DataFrame(results, columns=['Line/Sentence', 'AQ Value'])
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()
    buffer.seek(0)
    return buffer

# Save results to plain text
def save_to_text(results):
    text_output = "\n".join(f"{line} | AQ Value: {aq_value}" for line, aq_value in results)
    return text_output.encode()

# Streamlit UI
st.set_page_config(page_title="AQ Calc")

st.title("Alphanumeric Qabbala Calculator")

st.markdown('<small>For more tools and information see: <a href="https://alektryon.github.io/gematro/" target="_blank">https://alektryon.github.io/gematro/</a></small>', unsafe_allow_html=True)

# Add a toggle button for prose or poetry
mode = st.radio("Select mode:", ('Poetry (calculates by line breaks)', 'Prose (calculates by end of sentence)'))

# Add a toggle button for incremental calculation
incremental = st.checkbox("Calculate incremental AQ values (word by word)")

# Initialize session state for text input
if 'text' not in st.session_state:
    st.session_state['text'] = ""

def clear_text():
    st.session_state['text'] = ""
    st.experimental_rerun()

# Text input area
text_input = st.text_area("Enter text:", height=300, key="text_input")

# Buttons to calculate AQ values and clear text
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Calculate AQ Values"):
        st.session_state['text'] = st.session_state['text_input']
        results = process_text(st.session_state['text'], 'Prose' if 'Prose' in mode else 'Poetry', incremental)
        st.session_state['results'] = results

with col2:
    if st.button("Clear Text"):
        clear_text()

# Add search and sort functionality
if 'results' in st.session_state:
    st.write("Results:")

    df = pd.DataFrame(st.session_state['results'], columns=['Line/Sentence', 'AQ Value'])

    # Search functionality
    search_values = st.text_input("Search AQ values (separate multiple values with commas):", "")
    if search_values:
        search_values = [int(value.strip()) for value in search_values.split(",") if value.strip().isdigit()]
        df = df[df['AQ Value'].isin(search_values)]

    # Sortable table
    st.dataframe(df, width=700)

    st.write("Download Options:")

    # Create download buttons for Excel and Text files
    col3, col4 = st.columns([1, 1])
    with col3:
        excel_data = save_to_excel(st.session_state['results'])
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name='aq_values.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    with col4:
        text_data = save_to_text(st.session_state['results'])
        st.download_button(
            label="Download Text",
            data=text_data,
            file_name='aq_values.txt',
            mime='text/plain'
        )
