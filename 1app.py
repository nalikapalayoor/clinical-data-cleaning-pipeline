import streamlit as st

tab1, tab2 = st.tabs(["Harmonization", "Add to or view Synonym Mappings"])

with tab1:
    import pandas as pd
    from harmonization import process_raw_to_template
    from harmonization import build_transformations
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
            with st.sidebar.expander("Raw File Preview", expanded=True):
                st.dataframe(raw_preview.head(5).reset_index(drop=True), height=200, hide_index=True)
            all_column_options.extend(raw_preview.columns.tolist())
        except Exception as e:
            st.sidebar.warning(f"Could not preview raw file: {e}")
    if shipping_file and sheet_name_shipping:
        try:
            shipping_preview = pd.read_excel(shipping_file, sheet_name=sheet_name_shipping, header=shipping_header)
            with st.sidebar.expander("Shipping Manifest Preview", expanded=True):
                st.dataframe(shipping_preview.head(5).reset_index(drop=True), height=200, hide_index=True)
            all_column_options.extend(shipping_preview.columns.tolist())
        except Exception as e:
            st.sidebar.warning(f"Could not preview shipping manifest: {e}")

    # Guided Column Mapping
    st.subheader("Guided Column Mapping")
    template_fields = {
        "ExternalId":{"allowed":"","definition":"Sample ID received from site"},
        "Received Date":{"allowed":"","definition":"Must be in format XX-MON-YYYY (e.g. 01-JAN-2023)"},
        "ContainerType":{"allowed":"Slide, Tube, Plate, FFPE Block","definition":""},
        "Volume_uL":{"allowed":"","definition":""},
        "TubeBarcode":{"allowed":"","definition":""},
        "Concentration":{"allowed":"","definition":""},
        "ConcentrationUnits":{"allowed":"","definition":""},
        "Organism":{"allowed":"Human, Mouse, Mouse PDX","definition":""},
        "Stabilizer":{"allowed":"Streck, Accucyte, EDTA, PAXgene ccfDNA","definition":""},
        "Single or Double Spun":{"allowed":"Single, Double","definition":""},
        "Processing Method":{"allowed":"","definition":""},
        "Processing Time(hrs)":{"allowed":"","definition":""},
        "Freeze Thaw Status":{"allowed":"0,1,2,3,4,4, Unknown","definition":"Number of freeze-thaw cycles the sample has undergone."},
        "Hemolysis":{"allowed":"no hemolysis, light hemolysis, strong hemolysis, hemolysis","definition":"Documentation for quality of plasma (leave blank for non-plasma samples)"},
        "Project":{"allowed":"","definition":""},
        "Matched FFPE Available":{"allowed":"Yes, No","definition":"Add for plasma samples (not for FFPE samples themselves)"},
        "Date of Blood Draw/Cell Collection":{"allowed":"","definition":"Must be in format XX-MON-YYYY (e.g. 01-JAN-2023)"},
        "Time of Draw":{"allowed":"","definition":"Must be in format HH:MM (e.g. 14:30)"},
        "Block Size":{"allowed":"","definition":""},
        "Tissue Size":{"allowed":"","definition":""},
        "Tissue Weight (mg)":{"allowed":"","definition":""},
        "% Tumor":{"allowed":"","definition":""},
        "% Necrosis":{"allowed":"","definition":""},
        "Surgery Type":{"allowed":"biopsy, resection","definition":""},
        "Tumor Tissue Type":{"allowed":"primary, metastasis","definition":""},
        "Data Transformer":{"allowed":"","definition":"Your name"},
        "Date of Transformation":{"allowed":"","definition":"Must be in format XX-MON-YYYY (e.g. 01-JAN-2023)"},
        "Other Sample Notes":{"allowed":"","definition":""},
        "ExSpecimenId":{"allowed":"","definition":""},
        "Collection Site":{"allowed":"","definition":""},
        "SpecimenType":{"allowed":"Cell Line, Blood","definition":""},
        "Condition":{"allowed":"cancer, autoimmune, pregnancy, healthy","definition":""},
        "Diagnostic Condition":{"allowed":"breast cancer, colorectal cancer, lung cancer, gastroesophageal cancer, multiple sclerosis, osteosarcoma, ovarian cancer","definition":""},
        "Histology":{"allowed":"adenocarcinoma, carcinoma, epithelial tumor, endometrioid carcinoma, mucinous adenocarcinoma, infiltrating ductal carcinoma, infiltrating lobular carcinoma, large cell neuroendocrine carcinoma, large cell carcinoma, lobular carcinoma in situ, ductal carcinoma in situ, non-small cell lung cancer NOS, phylloides tumor, secretory carcinoma, small cell carcinoma, squamous cell carcinoma, signet ring cell carcinoma, neuroendocrine carcinoma, NOS, metastatic castration-resistant prostate cancer (mCRPC), invasive carcinoma NOS, acinar adenocarcinoma, pleomorphic carcinoma, lepidic adenocarcinoma, papillary adenocarcinoma,metaplastic carcinoma, serous carcinoma, not applicable, not received, SPMS, RRMS, PPMS,","definition":""},
        "Height":{"allowed":"","definition":""},
        "Weight":{"allowed":"","definition":""},
        "Duration between Cancer Diagnosis and Blood Draw (days)":{"allowed":"","definition":""},
        "Duration between Metastatic Diagnosis and Blood Draw (days)":{"allowed":"","definition":""},
        "Sample Timepoint":{"allowed":"","definition":""},
        "Sample Timepoint Description":{"allowed":"treatment-naïve, undergoing treatment, progression, study termination","definition":""},
        "AgeAtCollection":{"allowed":"","definition":""},
        "Detailed Anatomical Location":{"allowed":"","definition":""},
        "Grade":{"allowed":"","definition":""},
        "Tumor Size":{"allowed":"","definition":""},
        "TNM":{"allowed":"","definition":""},
        "Duration between TNM Staging and Blood Draw (days)":{"allowed":"","definition":""},
        "Stage":{"allowed":" I, II, III, IV","definition":""},
        "Stage Detailed":{"allowed":"","definition":""},
        "Morphology Code":{"allowed":"","definition":""},
        "Description of Morphology Code":{"allowed":"","definition":""},
        "Metastatic Sites":{"allowed":"","definition":"Organs the cancer has metastasized to, e.g. liver, lung, bone, brain"},
        "Vehicle Control":{"allowed":"","definition":""},
        "Media Conditions":{"allowed":"","definition":""},
        "Additional Supplements to Media":{"allowed":"","definition":""},
        "Protocols for Harvesting Cell Lines":{"allowed":"","definition":""},
        "Blood collection date (days from birth)":{"allowed":"","definition":""},
        "Number of lines of metastatic therapy at time of blood draw":{"allowed":"","definition":""},
        "Number of lines of chemotherapy at time of blood draw":{"allowed":"","definition":""},
        "Number of lines of anti-HER2 therapy at time of blood draw":{"allowed":"","definition":""},
        "Number of lines of endocrine therapy at time of blood draw":{"allowed":"","definition":""},
        "Overall Survival(months)":{"allowed":"","definition":""},
        "Treatment Data":{"allowed":"","definition":""},
        "Progression Free Survival(months)":{"allowed":"","definition":""},
        "Gestational Age at Collection":{"allowed":"","definition":""},
        "Fetus Sex":{"allowed":"","definition":""},
        "Menopausal Status":{"allowed":"premenopause, perimenopause, menopause, postmenopause","definition":""},
        "Blood Type":{"allowed":"","definition":""},
        "RNA-Sequencing Available":{"allowed":"Yes, No","definition":""},
        "ExPatientId":{"allowed":"","definition":""},
        "Source":{"allowed":"AstraZeneca, Biomedica CRO Inc., DxBio, ATCC, Biometas, Menarini, Coriell, Precision for Medicine, BMS, Discovery Life Sciences, Rarecyte, Proteo, AMSBIO, UPMC, Indivumed GmbH, Research Blood Components, Garner Biosolutions Inc, Genentech, Genentech-UCSF, MD Anderson, MT Group, MGH Klempner, Other, OHSU, DFCI, UCSF, Turku, Duke, EMD Serono, Novartis, Tyra, Duke, MD Anderson, Menarini, AstraZeneca, EMD Serono","definition":"Vendor or Academic partner where samples were sourced from"},
        "Country":{"allowed":"","definition":""},
        "Gender":{"allowed":"Male, Female, Unknown","definition":""},
        "Race":{"allowed":"American Indian or Alaska Native, Asian, Black or African American, Hispanic or Latino, Native Hawaiian or Other Pacific Islander, White","definition":""},
        "MedicalHistory":{"allowed":"","definition":""},
        "FamilyHistory":{"allowed":"","definition":""},
        "AlcoholHistory":{"allowed":"","definition":""},
        "SmokingHistory":{"allowed":"Current Smoker, Former Smoker, Never Smoked, not received, not applicable, Smoking History Present","definition":""},
        "Number of years smoked or smoking":{"allowed":"","definition":""},
        "Smoking Notes":{"allowed":"","definition":"Number of packs, ect."},
        "Donor Notes":{"allowed":"","definition":"Any other info not captured above"}
    }

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

        mapped_fields = 0
        total_fields = len(template_fields)

        # Create placeholder for progress bar
        st.sidebar.markdown("### 📝 Mapping Progress")
        progress_bar = st.sidebar.progress(0)

        for field,meta in template_fields.items():
            st.markdown(f"### {field}")

            if meta["definition"]:
                st.caption(f"📘 {meta['definition']}")

            if meta["allowed"]:
                st.markdown(f"**Allowed values**: `{meta['allowed']}`")

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

            mapped_val = column_mapping.get(field)
            if mapped_val not in ["", None]:
                mapped_fields += 1

            progress_pct = int((mapped_fields / total_fields) * 100)
            progress_bar.progress(progress_pct)

    else:
        st.info("Please upload and configure the raw file and/or shipping manifest to proceed with mapping.")


    # Menopause extraction checkbox
    extract_menopause_from_biomarker = st.checkbox(
        "Extract Menopausal Status from Biomarker Columns?", value=True
    )

    import mysql.connector
    from harmonization import load_mapping  # or `from script import load_mapping` if you didn't rename

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_new_password",  # replace with your actual password
        database="mappings_db"
    )

    biomarker_mapping = load_mapping(conn, "biomarker_mappings", std_col="standard_name")
    pos_neg_mapping = load_mapping(conn, "pos_neg_mappings")
    her2_ihc_mapping = load_mapping(conn, "her2_ihc_mappings")
    menopause_mapping = load_mapping(conn, "menopause_mappings", std_col="standard_term")

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_new_password",
        database="mappings_db"
    )

    transformations = build_transformations(conn)


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
            extract_menopause_from_biomarker=extract_menopause_from_biomarker,
            biomarker_mapping=biomarker_mapping,
            pos_neg_mapping=pos_neg_mapping,
            her2_ihc_mapping=her2_ihc_mapping,
            menopause_mapping=menopause_mapping,
            transformations=transformations

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

with tab2:
    st.header("Synonym Mapping Management")

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_new_password",
        database="mappings_db"
    )

    mapping_tables = {
    "Biomarkers": ("biomarker_mappings", "standard_name"),
    "Positive/Negative Values": ("pos_neg_mappings", "standard_value"),
    "HER2 IHC Scores": ("her2_ihc_mappings", "standard_value"),
    "Menopause Status": ("menopause_mappings", "standard_term"),
    "Stabilizers": ("stabilizer_mappings", "standard_value"),
    "Gender": ("gender_mappings", "standard_value"),
    "Single/Double Spun": ("single_double_mappings", "standard_value"),
    "Sample Timepoints": ("sample_timepoint_mappings", "standard_value"),
    "Stage": ("stage_mappings", "standard_value"),
    "Hemolysis": ("hemolysis_mappings", "standard_value"),
    "Diagnostics": ("diagnostic_mappings", "standard_value"),
    "Race": ("race_mappings", "standard_value"),
    "Smoking History": ("smoking_history_mappings", "standard_value")
    }


    table_display_name = st.selectbox("Select mapping table to view/edit:", list(mapping_tables.keys()))
    table_name, standard_col = mapping_tables[table_display_name]

    st.subheader(f"Existing Mappings in {table_display_name}")
    mapping_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    mapping_df = mapping_df.drop(columns=["id"])
    st.dataframe(mapping_df)

    st.markdown("### Add a new synonym")

    # Fetch existing standard values from the DB
    existing_standards_df = pd.read_sql(f"SELECT DISTINCT {standard_col} FROM {table_name}", conn)
    standard_options = sorted(existing_standards_df[standard_col].dropna().unique().tolist())

    # Add an extra option to create a new one
    standard_options.append("➕ Create new...")

    # Dropdown with extra option
    selected_option = st.selectbox("Select or create a standard value", options=standard_options)

    # If they choose "create new", show a text input
    if selected_option == "➕ Create new...":
        new_standard = st.text_input("Enter new standard value")
    else:
        new_standard = selected_option


    new_synonym = st.text_input("Synonym value")

    if st.button("Add Synonym"):
        if new_standard and new_synonym:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {table_name} ({standard_col}, synonym) VALUES (%s, %s)",
                (new_standard.strip(), new_synonym.strip())
        )
            conn.commit()
            st.success("✅ Synonym added!")
        else:
            st.warning("Please fill out both fields to add a new synonym.")
