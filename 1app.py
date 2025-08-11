import streamlit as st
import pandas as pd
from script import process_raw_to_template
import io




st.title("🧬 Raw to Template Harmonization")

st.subheader("Upload Files")

template_file = st.file_uploader("Upload Template File (.xlsx)", type="xlsx")
raw_file = st.file_uploader("Upload Raw Clinical File (.xlsx)", type="xlsx")
shipping_file = st.file_uploader("Upload Shipping Manifest (.xlsx)", type="xlsx")

st.subheader("Configuration")

sheet_name_raw = st.text_input("Sheet name for raw file", value="Clinical Data")
sheet_name_shipping = st.text_input("Sheet name for shipping manifest", value="Template")

raw_header = st.number_input("What row is the header for the raw file?", value=1, step=1)
template_header = st.number_input("What row is the header for the template file?", value=1, step=1)
shipping_header = st.number_input("What row is the header for the shipping manifest?", value=10, step=1)


dataset = st.text_input("Dataset name (used for output file name)", value="PRB_LB_0325")


biomarker_cols_text = st.text_area(
    "Biomarker column names (comma-separated)",
    value="Biomarker 1, Biomarker 2, Biomarker 3, Biomarker 4, Biomarker 5, Biomarker 6"
)
biomarker_cols = [col.strip() for col in biomarker_cols_text.split(",") if col.strip()]


st.subheader("Column Mapping")
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

# Predefined labels you want users to pick from
label_options = [
    "Duration between Cancer Diagnosis and Blood Draw (days)",
    "Duration between TNM Staging and Blood Draw (days)",
    "Duration between Metastatic Diagnosis and Blood Draw (days)",
]

# Number of calculation blocks to show
num_calculations = st.number_input(
    "How many time difference calculations?", min_value=0, max_value=10, step=1, value=1
)

calculation_functions = {}

for i in range(num_calculations):
    st.markdown(f"**Calculation {i+1}**")
    
    start_col = st.text_input(f"Start date column for calculation {i+1}", key=f"calc_start_{i}")
    end_col = st.text_input(f"End date column for calculation {i+1}", key=f"calc_end_{i}")
    
    label = st.selectbox(
        f"Label for this calculation {i+1}",
        label_options,
        key=f"calc_label_{i}"
    )

    if start_col and end_col and label:
        calculation_functions[label] = [start_col, end_col]

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

    # Convert to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False)
    output.seek(0)

    st.download_button(
        label="📥 Download Harmonized Excel",
        data=output,
        file_name=f"{dataset}_formatted_auto.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


