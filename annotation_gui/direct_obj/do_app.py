import configparser
import pandas as pd
from pathlib import Path
import streamlit as st
import uuid  # For generating unique identifiers

from annotation_gui.stats.helper import (
    calc_z_value,
    is_stop_criterion_met,
    calc_p_hat,
    calc_curr_moe,
)
from annotation_gui.utils import create_model_fp_dict, create_dataset_fp_dict

# Initialize session state for tracking the current example
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

meta_config = configparser.ConfigParser()
meta_config.read("config.ini")

do_confg = configparser.ConfigParser()
do_confg.read("direct_obj/do_config.ini")

st.title("Direct Object -- Human Assessment")

model_dict = create_model_fp_dict(
    f"{meta_config['paths']['dataset_dir_path']}/direct_obj"
)

model_choice = st.selectbox(
    "Select a model to annotate:", options=list(model_dict.keys())
)

data_dict = create_dataset_fp_dict(model_dict[model_choice])

data_choice = st.selectbox(
    "Select a file to annotate by first selecting a dataset:",
    options=list(data_dict.keys()),
)
data_path = data_dict[data_choice]

annotator_name = st.text_input("Enter your name:", value="STUDENT")
results_csv_path = f"{meta_config['paths']['results_dir']}/direct_obj/{model_choice}/{data_choice}/{annotator_name}_annotations.csv"

# Create the directory structure if it doesn't exist
results_dir = Path(results_csv_path).parent
results_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(data_path, usecols=["full_prompt", "direct_objects", "verbs"])

# Shuffle the dataset and add a unique identifier
if "unique_id" not in df.columns:
    df["unique_id"] = [str(uuid.uuid4()) for _ in range(len(df))]  # Add unique IDs
    df = df.sample(frac=1, random_state=42).reset_index(
        drop=True
    )  # Shuffle the dataset

if "annotation_quality" not in df.columns:
    df["annotation_quality"] = None

if Path(results_csv_path).exists():
    annotated_df = pd.read_csv(results_csv_path)
    df.update(annotated_df)

labeled_df = df.dropna(subset=["annotation_quality"])

z_value = calc_z_value(
    meta_config.getfloat("stat-stopping-critiera", "confidence_level")
)
n_labeled = len(labeled_df)
min_n_samples = meta_config.getfloat("stat-stopping-critiera", "minimum_annos_req")
n_bad = (labeled_df["annotation_quality"] == "bad").sum()
moe_threshold = meta_config.getfloat("stat-stopping-critiera", "margin_of_error")
p_hat = calc_p_hat(n_bad, n_labeled)

st.subheader("Statistics Overview:")
st.write(f"Total Labeled: **{n_labeled}**")
st.write(f"Proportion of Bad Responses: **{p_hat:.2%}**")
st.write(f"Margin of Error: **{calc_curr_moe(z_value, p_hat, n_labeled):.2%}**")

if is_stop_criterion_met(n_labeled, min_n_samples, n_bad, z_value, moe_threshold):
    st.success("✨ Stopping Criterion Met! No more annotations are required. ✨")
    st.stop()

# Get the current example index from session state
current_index = st.session_state.current_index

# Ensure the current index is within bounds
if current_index >= len(df):
    current_index = len(df) - 1
if current_index < 0:
    current_index = 0

# Display the current example
st.subheader("Annotate Example")
st.write(f"**Prompt:** {df.loc[current_index, 'full_prompt']}")
st.write(f"**Direct Objects:** {df.loc[current_index, 'direct_objects']}")
st.write(f"**Verbs:** {df.loc[current_index, 'verbs']}")

# Annotation buttons
col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
with col1:
    if st.button("⏪ Prev"):
        st.session_state.current_index -= 1
        st.rerun()
with col4:
    if st.button("Good! ✅"):
        df.loc[current_index, "annotation_quality"] = "good"
        df.to_csv(results_csv_path, index=False)
        st.session_state.current_index += 1
        st.rerun()
with col3:
    if st.button("Bad! ❌"):
        df.loc[current_index, "annotation_quality"] = "bad"
        df.to_csv(results_csv_path, index=False)
        st.session_state.current_index += 1
        st.rerun()
with col6:
    if st.button("Next ⏩"):
        st.session_state.current_index += 1
        st.rerun()

# Display the current example number
st.write(f"**Example {current_index + 1} of {len(df)}**")

# If all examples are annotated
if df["annotation_quality"].notna().all():
    st.success(f"🎉 All examples in '{data_choice}' are annotated! 🎉")
    st.write(df)
