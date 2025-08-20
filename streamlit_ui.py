import streamlit as st
import tempfile
import subprocess
import requests
import os

# Streamlit app title
st.title("Collator UI")
st.set_page_config(page_title="Collator")

# Create a form for CLI parameters
with st.form("cli_form"):
    param_algo = st.selectbox("CollateX algorithm (collator --algorithm)", ["dekker", "needleman-wunsch"])
    param_comparator = st.selectbox("Token Comparator (collator --comparator)", ["jaccard", "levenshtein", "levenshteinNormalized", "equality"])
    param_distance = st.number_input("Token Comparator Distance (collator --distance)", min_value=0., max_value=1., step=0.1)
    param_interpunction = st.checkbox("Delete interpunction (collator --interpunction)", value=False)

    # File uploader for multiple XML files
    uploaded_files = st.file_uploader("Upload XML files", type="xml", accept_multiple_files=True)

    # Text area for remote URLs
    url_input = st.text_area("Enter remote URLs of input files (one per line)")

    file_normalization = st.file_uploader("Upload additional normalization mapping (CSV with 'in' and 'out' columns)", type="csv", accept_multiple_files=False)

    lines_normalization = st.text_area("Additional normalizations (one per line, separated by comma, order: in,out")

    # Submit button
    submitted = st.form_submit_button("Run collator")

if submitted:

    param_dict = {
        "algorithm": param_algo,
        "comparator": param_comparator,
        "distance": param_distance,
    }

    # XML INPUT
    #we merge all input file sources, either from file drop or remote URL
    temp_file_paths = []

    # Handle uploaded files
    for uploaded_file in uploaded_files:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        temp_file.write(uploaded_file.read())
        temp_file.close()
        temp_file_paths.append(temp_file.name)

    # Handle remote URLs
    urls = url_input.strip().splitlines()
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
            temp_file.write(response.content)
            temp_file.close()
            temp_file_paths.append(temp_file.name)
        except Exception as e:
            st.error(f"Failed to download {url}: {e}")

    # NORMALIZATION INPUT

    temp_norm_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w")
    temp_file_lines = ["in,out"]
    if file_normalization is not None:
        file_content = file_normalization.getvalue().decode("utf-8")
        if not file_content.endswith("\n"):
            file_content += "\n"
    else:
        file_content = "in,out\n"

    #if we also have plain text mappings:
    if lines_normalization is not None:
        header = file_content.split("\n")[0]
        if "in,out" in header.strip():
            #append lines as is
            for l in lines_normalization.strip().splitlines():
                file_content += l + "\n"
        if "out,in" in header.strip():
            #reverse lines
            for l in lines_normalization.strip().splitlines():
                reversed = ",".join(reversed(l.split(",")))
                file_content += reversed + "\n"

    print(file_content)

    #write to norm file
    temp_norm_file.write(file_content)
    temp_norm_file.close()

    # Construct CLI command

    if file_content and len(file_content.split("\n")) > 1:
        param_dict["normalizations"] = temp_norm_file.name

    param_strings = []
    for k, v in param_dict.items():
        param_strings.append("--" + k)
        param_strings.append(str(v))
    if param_interpunction: param_strings.append("--interpunction")

    cli_command = ["./collator.py"]
    cli_command += param_strings
    cli_command += temp_file_paths

    print("Running ", " ".join(cli_command))

    # Run the CLI command
    try:
        result = subprocess.run(cli_command, capture_output=True, text=True)
        st.text("CLI Output:")
        #st.text(result.stdout)
        if result.returncode != 0:
            st.text(result.stderr)
        else:
            st.download_button("Download XML output", "output.xml", file_name="collationresult.xml", on_click="ignore")
            st.html("output.html")
            # we assume the collator ran successfully
            #with open("output.xml", "r") as xml_out:


    except Exception as e:
        st.error(f"Error running CLI script: {e}")

    # Clean up temp files
    for path in temp_file_paths:
        os.remove(path)
    os.remove(temp_norm_file.name)