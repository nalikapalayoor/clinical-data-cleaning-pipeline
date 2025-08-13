import streamlit as st
import pandas as pd
from script import process_raw_to_template
import io

st.title("Raw to Template Harmonization")

st.subheader("Upload Files")

template_file = st.file_uploader("Upload Template File (.xlsx)", type="xlsx")
raw_file = st.file_uploader("Upload Raw Clinical File (.xlsx)", type="xlsx")
shipping_file = st.file_uploader("Upload Shipping Manifest (.xlsx)", type="xlsx")

st.subheader("Configuration")
sheet_name_raw = st.text_input("Sheet name for raw file", value="Clinical Data")
sheet_name_template = st.text_input("Sheet name for template file", value=None)
sheet_name_shipping = st.text_input("Sheet name for shipping manifest", value="Template")

raw_header = st.number_input("Header row for raw file (0-indexed)", value=1, step=1)
template_header = st.number_input("Header row for template file (0-indexed)", value=1, step=1)
shipping_header = st.number_input("Header row for shipping manifest (0-indexed)", value=10, step=1)

dataset = st.text_input("Dataset name (used for output file name)", value="PRB_LB_0325")

# Load raw and shipping previews
raw_preview = None
shipping_preview = None
all_column_options = []

if raw_file and sheet_name_raw:
    try:
        raw_preview = pd.read_excel(raw_file, sheet_name=sheet_name_raw, header=raw_header)
        st.subheader("Raw File Preview")
        st.dataframe(raw_preview.head(5))
        all_column_options.extend(raw_preview.columns.tolist())
    except Exception as e:
        st.warning(f"Could not preview raw file: {e}")

if shipping_file and sheet_name_shipping:
    try:
        shipping_preview = pd.read_excel(shipping_file, sheet_name=sheet_name_shipping, header=shipping_header)
        st.subheader("Shipping Manifest Preview")
        st.dataframe(shipping_preview.head(5))
        all_column_options.extend(shipping_preview.columns.tolist())
    except Exception as e:
        st.warning(f"Could not preview shipping manifest: {e}")

# Guided Column Mapping
st.subheader("Guided Column Mapping")
template_fields = [
    "ExternalId", "Received Date", "ContainerType", "Volume_uL", "TubeBarcode",
    "Concentration", "ConcentrationUnits", "Organism", "Stabilizer", "Single or Double Spun",
    "Processing Method", "Processing Time(hrs)", "Freeze Thaw Status", "Hemolysis", "Project",
    "Matched FFPE Available", "Date of Blood Draw/Cell Collection", "Time of Draw", "Block Size",
    "Tissue Size", "Tissue Weight (mg)", "% Tumor", "% Necrosis", "Surgery Type",
    "Tumor Tissue Type", "Data Transformer", "Date of Transformation", "Other Sample Notes",
    "ExSpecimenId", "Collection Site", "SpecimenType", "Condition", "Diagnostic Condition",
    "Histology", "Height", "Weight", "BMI",
    "Duration between Cancer Diagnosis and Blood Draw (days)",
    "Duration between Metastatic Diagnosis and Blood Draw (days)",
    "Sample Timepoint", "Sample Timepoint Description", "AgeAtCollection",
    "Detailed Anatomical Location", "Grade", "Tumor Size", "TNM",
    "Duration between TNM Staging and Blood Draw (days)", "Stage", "Stage Detailed",
    "Morphology Code", "Description of Morphology Code", "Metastatic Sites",
    "Vehicle Control", "Media Conditions", "Additional Supplements to Media",
    "Protocols for Harvesting Cell Lines", "Blood collection date (days from birth)",
    "Number of lines of metastatic therapy at time of blood draw",
    "Number of lines of chemotherapy at time of blood draw",
    "Number of lines of anti-HER2 therapy at time of blood draw",
    "Number of lines of endocrine therapy at time of blood draw", "Overall Survival(months)",
    "Treatment Data", "Progression Free Survival(months)", "Gestational Age at Collection",
    "Fetus Sex", "Menopausal Status", "Blood Type", "RNA-Sequencing Available",
    "ExPatientId", "Source", "Country", "Gender", "Race", "MedicalHistory",
    "FamilyHistory", "AlcoholHistory", "SmokingHistory", "Number of years smoked or smoking",
    "Smoking Notes", "Donor Notes"
]

column_mapping = {}
fixed_values = {}
calculation_functions = {}

# Define which fields can be calculated
calculated_fields = [
    "Duration between Cancer Diagnosis and Blood Draw (days)",
    "Duration between TNM Staging and Blood Draw (days)",
    "Duration between Metastatic Diagnosis and Blood Draw (days)"
]

if all_column_options:
    for field in template_fields:
        st.markdown(f"### {field}")

        use_not_received = st.checkbox(f"Mark '{field}' as Not Received", key=f"not_received_{field}")
        use_fixed_value = st.checkbox(f"Fill '{field}' with a constant value", key=f"use_fixed_value_{field}")
        use_calculated = field in calculated_fields and st.checkbox(f"Calculate '{field}' from two columns", key=f"use_calculated_{field}")

        if use_not_received:
            column_mapping[field] = "not received"

        elif use_fixed_value:
            fixed_val = st.text_input(f"Enter constant value for '{field}':", key=f"fixed_value_{field}")
            if fixed_val:
                fixed_values[field] = fixed_val
                column_mapping[field] = "fixed"
            else:
                column_mapping[field] = "not received"

        elif use_calculated:
            start_col = st.selectbox(f"Start column for '{field}'", options=all_column_options, key=f"calc_start_{field}")
            end_col = st.selectbox(f"End column for '{field}'", options=all_column_options, key=f"calc_end_{field}")
            if start_col and end_col:
                calculation_functions[field] = [start_col, end_col]
                column_mapping[field] = "calculated"

        else:
            column_mapping[field] = st.selectbox(
                f"Select the raw or shipping column to map to template field '{field}':",
                options=[""] + all_column_options,
                key=f"map_{field}"
            )
else:
    st.info("Please upload and configure the raw file and/or shipping manifest to proceed with mapping.")


# Menopause extraction checkbox
extract_menopause_from_biomarker = st.checkbox(
    "Extract Menopausal Status from Biomarker Columns?", value=True
)

# Harmonization trigger
if st.button("Run Harmonization"):
    raw = pd.read_excel(raw_file, sheet_name=sheet_name_raw, header=raw_header)
    template = pd.read_excel(template_file, header=template_header)
    shipping = pd.read_excel(shipping_file, sheet_name=sheet_name_shipping, header=shipping_header) if shipping_file else pd.DataFrame()

    final_df = process_raw_to_template(
        template=template,
        raw=raw,
        shipping_manifest=shipping,
        dataset=dataset,
        transformer="",
        transform_date="",
        column_mapping=column_mapping,
        fixed_values=fixed_values,
        biomarker_cols=[],
        calculation_functions=calculation_functions,
        extract_menopause_from_biomarker=extract_menopause_from_biomarker
    )

    st.success("✅ Harmonization Complete!")
    st.dataframe(final_df.head())

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
