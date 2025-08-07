import streamlit as st
import pandas as pd
from script import process_raw_to_template




st.title("🧬 Raw to Template Harmonization🧬")

st.subheader("Step 1: Upload Files")

template_file = st.file_uploader("Upload Template File (.xlsx)", type="xlsx")
raw_file = st.file_uploader("Upload Raw Clinical File (.xlsx)", type="xlsx")
shipping_file = st.file_uploader("Upload Shipping Manifest (.xlsx)", type="xlsx")

st.subheader("Step 2: Configuration")

sheet_name_raw = st.text_input("Sheet name for raw file", value="Clinical Data")
sheet_name_shipping = st.text_input("Sheet name for shipping manifest", value="Template")

raw_header = st.number_input("Header row index (raw file)", value=1, step=1)
template_header = st.number_input("Header row index (template file)", value=1, step=1)
shipping_header = st.number_input("Header row index (shipping manifest)", value=10, step=1)


dataset = st.text_input("Dataset name (used for output file name)", value="PRB_LB_0325")


biomarker_cols_text = st.text_area(
    "Biomarker column names (comma-separated)",
    value="Biomarker 1, Biomarker 2, Biomarker 3, Biomarker 4, Biomarker 5, Biomarker 6"
)
biomarker_cols = [col.strip() for col in biomarker_cols_text.split(",") if col.strip()]


st.subheader("Column Mapping (Template → Raw)")
template_fields = [
    "ExternalId", "TubeBarcode", "Stabilizer", "Single or Double Spun",
    "Hemolysis", "SpecimenType", "Date of Blood Draw/Cell Collection",
    "Time of Draw", "Gender", "Height", "Sample Timepoint", "TNM",
    "Stage", "Morphology Code", "Description of Morphology Code",
    "ExPatientId", "ExSpecimenId", "Weight"
]

column_mapping = {}
for field in template_fields:
    column_mapping[field] = st.text_input(f"Raw column for '{field}'", key=f"mapping_{field}")


st.subheader("Fixed Values")
fixed_fields = [
    "ContainerType", "Organism", "Project", "Data Transformer",
    "Date of Transformation", "Condition", "Diagnostic Condition",
    "RNA-Sequencing Available", "Source", "Country"
]

fixed_values = {}
for field in fixed_fields:
    fixed_values[field] = st.text_input(f"Value for '{field}'", key=f"fixed_{field}")


st.subheader("Calculation Columns")
calc_1 = st.text_input("Start date column (e.g. Date of cancer diagnosis)", key="calc_start_1")
calc_2 = st.text_input("End date column (e.g. Date of blood collection)", key="calc_end_1")
calc_label = st.text_input("Label for this calculation", value="Duration between Cancer Diagnosis and Blood Draw (days)")

calculation_functions = {}
if calc_1 and calc_2 and calc_label:
    calculation_functions[calc_label] = [calc_1, calc_2]


extract_menopause_from_biomarker = st.checkbox(
    "Extract Menopausal Status from Biomarker Columns?", value=True
)


if st.button("Run Harmonization"):
    raw = pd.read_excel(raw_file, sheet_name=sheet_name_raw, header=raw_header)
    template = pd.read_excel(template_file, header=template_header)
    shipping = pd.read_excel(shipping_file, sheet_name=sheet_name_shipping, header=shipping_header)

    final_df = process_raw_to_template(
        template=template,
        raw=raw,
        shipping_manifest=shipping,
        dataset=dataset,
        transformer=fixed_values["Data Transformer"],
        transform_date=fixed_values["Date of Transformation"],
        column_mapping=column_mapping,
        fixed_values=fixed_values,
        biomarker_cols=biomarker_cols,
        calculation_functions=calculation_functions,
        extract_menopause_from_biomarker=extract_menopause_from_biomarker
    )

    st.success("Done!")
    st.dataframe(final_df.head())


