import configparser
import pandas as pd
from pathlib import Path
import streamlit as st

from annotation_gui.stats.helper import calc_z_value, is_stop_criterion_met, calc_p_hat, calc_curr_moe
from annotation_gui.utils import create_model_fp_dict, create_dataset_fp_dict

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

# TODO Shuffle data and add unique ids

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
    st.success("Stopping Criterion Met! No more annotations are required.")
    st.stop()

row_idx = df[df["annotation_quality"].isna()].index.min()
if row_idx is not None and not pd.isna(row_idx):
    st.subheader("Annotate Example")
    st.write(f"**Prompt:** {df.loc[row_idx, 'full_prompt']}")
    st.write(f"**Direct Objects:** {df.loc[row_idx, 'direct_objects']}")
    st.write(f"**Verbs:** {df.loc[row_idx, 'verbs']}")

    # Annotation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Good!"):
            df.loc[row_idx, "annotation_quality"] = "good"
            df.to_csv(results_csv_path, index=False)
            st.rerun()
    with col2:
        if st.button("Bad!"):
            df.loc[row_idx, "annotation_quality"] = "bad"
            df.to_csv(results_csv_path, index=False)
            st.rerun()
else:
    st.success(f"All examples in '{data_choice}' are annotated!")
    st.write(df)