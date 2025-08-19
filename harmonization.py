from typing import final
import streamlit as st
import pandas as pd
import re
from datetime import datetime
import mysql.connector

required_columns = [
    "Tube Barcode", "Concentration Units", "Single or Double Spun", "Processing Method", "Freeze Thaw Status", "Project",
    "Matched FFPE Available", "Surgery Type", "Tumor Tissue Type", "Other Sample Notes", "Collection Site", "Histology",
    "Sample Timepoint", "Sample Timepoint Description", "Detailed Anatomical Location", "Grade", "Tumor Size", "TNM", "Stage",
    "Stage_detailed", "Morphology Code", "Description of Morphology Code", "Metastatic Sites", "Vehicle Control", "Media Conditions",
    "Additional Supplements to Media", "Protocols for Harvesting Cell Lines", "Menopausal Status", "HER2 IHC", "HER2", "FISH",
    "HER2 Change from Previous Sample", "ER", "ER Notes", "ER Status Change From Previous Sample", "PR", "PR Notes",
    "PR Status Change From Previous Sample", "AR Notes", "AR Status Change From Previous Sample", "ROS", "ALK", "EGFR",
    "EGFR Allele Information", "PDL1", "KRAS", "PIK3CA", "ESR1", "BRCA1", "BRCA2", "FOLR1", "Biomarker Notes", "Country",
    "Gender", "Race", "SmokingHistory"
]

def load_mapping(conn, table_name, std_col="standard_value"):
    query = f"SELECT {std_col}, synonym FROM {table_name}"
    df = pd.read_sql(query, conn)
    mapping = {}
    for _, row in df.iterrows():
        mapping.setdefault(row[std_col], []).append(str(row["synonym"]).lower())
    return mapping

def make_cleaner(mapping_dict):
    lookup = {}
    for standard_val, raw_options in mapping_dict.items():
        for raw_val in raw_options:
            lookup[str(raw_val).strip().lower()] = standard_val

    def cleaner(val):
        if pd.isna(val):
            return pd.NA
        val_str = str(val).strip().lower()
        return lookup.get(val_str, pd.NA)

    return cleaner

def extract_menopause_status(val_str, menopause_mapping):
    val_str = val_str.lower()
    for clean_val, options in menopause_mapping.items():
        for opt in options:
            if opt in val_str:
                return clean_val
    return pd.NA

def clean_date(val):
    if pd.isna(val):
        return pd.NA
    try:
        return pd.to_datetime(val).strftime("%Y-%B-%d")
    except:
        return pd.NA

def clean_time(val):
    if pd.isna(val):
        return pd.NA
    try:
        return pd.to_datetime(val).strftime("%I:%M:%S %p")
    except:
        return pd.NA

def calculate_age(birth_val, collection_date):
    if pd.isna(birth_val) or pd.isna(collection_date):
        return pd.NA
    try:
        birth_str = str(birth_val).strip()
        if len(birth_str) == 4 and birth_str.isdigit():
            birth_date = pd.to_datetime(f"{birth_str}-01-01")
        else:
            birth_date = pd.to_datetime(birth_str, errors="coerce")
        collection_dt = pd.to_datetime(collection_date, errors="coerce")
        return (collection_dt - birth_date).days // 365
    except:
        return pd.NA

def calculate_elapsed_days(row, start_col, end_col):
    start_val = row.get(start_col)
    end_val = row.get(end_col)
    if pd.isna(start_val) or pd.isna(end_val):
        return pd.NA
    try:
        start_date = pd.to_datetime(start_val, errors="coerce")
        end_date = pd.to_datetime(end_val, errors="coerce")
        if pd.isna(start_date) or pd.isna(end_date):
            return pd.NA
        delta = (end_date - start_date).days
        return delta if delta >= 0 else pd.NA
    except:
        return pd.NA

def calculate_bmi(weight, height):
    weight = pd.to_numeric(weight, errors="coerce")
    height = pd.to_numeric(height, errors="coerce")
    if pd.isna(weight) or pd.isna(height) or height == 0:
        return pd.NA
    try:
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        return round(bmi, 2)
    except:
        return pd.NA
    
def parse_age_smart(val, collection_date):
    try:
        val_str = str(val).strip()
        if not val_str or pd.isna(val):
            return pd.NA
        numeric_val = pd.to_numeric(val_str, errors="coerce")

        if not pd.isna(numeric_val):
            if 1000 <= numeric_val <= 2100:
                collection_dt = pd.to_datetime(collection_date, errors="coerce")
                if not pd.isna(collection_dt):
                    return int(collection_dt.year - numeric_val)
                else:
                    return pd.NA
            if 0 <= numeric_val <= 120:
                return int(numeric_val)
        
        birth_date = pd.to_datetime(val_str, errors="coerce")
        collection_dt = pd.to_datetime(collection_date, errors="coerce")
        if not pd.isna(birth_date) and not pd.isna(collection_dt):
            return int((collection_dt - birth_date).days // 365)

    except:
        pass

    return pd.NA



def extract_biomarkers_from_blob(blob, biomarker_lookup, pos_neg_mapping, her2_ihc_mapping):
    results = {}
    blob = blob.replace("=", " = ")
    blob = re.sub(r'\s+', ' ', blob).strip().lower()
    biomarker_keys = sorted(
        [re.escape(v.lower()) for variants in biomarker_lookup.values() for v in variants],
        key=len, reverse=True
    )
    lookahead_pattern = r'(?=\s+\b(?:' + '|'.join(biomarker_keys) + r')\b\s*=|$)'
    fish_match = re.search(r'\bfish\b\s*=\s*([^\s=]+)', blob)
    fish_val = fish_match.group(1).strip() if fish_match else None
    for template_col, variants in biomarker_lookup.items():
        for variant in variants:
            variant = variant.lower()
            pattern = rf'\b{re.escape(variant)}\b\s*=\s*(.*?){lookahead_pattern}'
            match = re.search(pattern, blob)
            if match:
                raw_val = match.group(1).strip()
                if template_col == "HER2":
                    her2_match = re.search(r'(0|1\+|2\+|3\+)', raw_val)
                    if her2_match:
                        her2_score = her2_match.group(1)
                        if her2_score in ["0", "1+"]:
                            mapped = "negative"
                        elif her2_score == "3+":
                            mapped = "positive"
                        elif her2_score == "2+":
                            if fish_val in pos_neg_mapping.get("positive", []):
                                mapped = "positive"
                            elif fish_val in pos_neg_mapping.get("negative", []):
                                mapped = "negative"
                            else:
                                mapped = "HER2 2+ (FISH/ISH missing)"
                        else:
                            mapped = pd.NA
                        for mapped_ihc, variants in her2_ihc_mapping.items():
                            if raw_val in variants:
                                results['HER2 IHC'] = mapped_ihc
                                break
                        else:
                            results['HER2 IHC'] = raw_val
                    else:
                        mapped = raw_val
                else:
                    mapped = None
                    for label, values in pos_neg_mapping.items():
                        if raw_val in values:
                            mapped = label
                            break
                    if mapped is None:
                        mapped = raw_val
                results[f"{template_col} Value"] = raw_val
                results[template_col] = mapped
                break
    return results

def call_calculation_functions(final_df, raw_df, mapping_dict):
    for new_col, (col1, col2) in mapping_dict.items():
        final_df[new_col] = raw_df.apply(
            lambda row: calculate_elapsed_days(row, col1, col2), axis=1
        )
    return final_df

def height_weight_conversion(height_truth, weight_truth):
    if height_truth== "cm":
        height_conversion = 1
    elif height_truth == "inches":
        height_conversion = 2.54
    elif height_truth == "meters":
        height_conversion = 100
    else:
        height_conversion = 1

    if weight_truth == "kg":
        weight_conversion = 1
    elif weight_truth == "lbs":
        weight_conversion = 0.453592
    else:
        weight_conversion = 1

    weight= lambda x: x * weight_conversion if pd.notna(x) else pd.NA
    height = lambda x: x * height_conversion if pd.notna(x) else pd.NA

    return weight, height

def process_raw_to_template(template, raw, shipping_manifest, column_mapping, fixed_values, biomarker_cols, calculation_functions, biomarker_mapping, pos_neg_mapping, her2_ihc_mapping, menopause_mapping, extract_menopause_from_biomarker=True, transformations=None, height_truth="cm", weight_truth="kg", raw_col_merge=None, ship_col_merge=None):
    final = pd.DataFrame(index=raw.index, columns=template.columns)
    raw['biomarker_blob'] = raw[biomarker_cols].astype(str).replace('nan', '').agg(' '.join, axis=1).str.replace(r'\s+', ' ', regex=True).str.strip()


    if shipping_manifest is not None and raw_col_merge and ship_col_merge:
        raw= pd.merge(raw,shipping_manifest, left_on=raw_col_merge, right_on=ship_col_merge, how="left")
    biomarker_data = raw['biomarker_blob'].apply(
        lambda row: extract_biomarkers_from_blob(row, biomarker_mapping, pos_neg_mapping, her2_ihc_mapping)).to_dict()
    for idx, result in biomarker_data.items():
        for biomarker, val in result.items():
            final.at[idx, biomarker] = val
    if extract_menopause_from_biomarker:
        final['Menopausal Status'] = raw['biomarker_blob'].apply(lambda val: extract_menopause_status(val, menopause_mapping))
    call_calculation_functions(final, raw, calculation_functions)

    age_col = column_mapping.get("AgeAtCollection")
    collection_col = column_mapping.get("Date of Blood Draw/Cell Collection")

    final["AgeAtCollection"] = raw.apply(
        lambda row: parse_age_smart(
            row.get(age_col) if age_col else None,
            row.get(collection_col) if collection_col else None
        ),
        axis=1
    )

    special_fields = {"AgeAtCollection"}
    
    height_col = column_mapping.get("Height")
    weight_col = column_mapping.get("Weight")


    convert_weight, convert_height = height_weight_conversion(height_truth, weight_truth)

    if height_col in raw.columns:
        raw[height_col] = raw[height_col].apply(convert_height)

    if weight_col in raw.columns:
        raw[weight_col] = raw[weight_col].apply(convert_weight)

    final["Height"] = raw[height_col] if height_col in raw.columns else pd.NA
    final["Weight"] = raw[weight_col] if weight_col in raw.columns else pd.NA


    if weight_col in raw.columns and height_col in raw.columns:
        final["BMI"] = raw.apply(
            lambda row: calculate_bmi(row.get(weight_col), row.get(height_col)), axis=1
        )
    else:
        final["BMI"] = pd.NA

    

    
    for col, val in fixed_values.items():
        if col in final.columns:
            final[col] = val
    for template_col in column_mapping:
        if template_col in special_fields:
            continue
        raw_col = column_mapping[template_col]
        if raw_col in raw.columns:
            if template_col in transformations:
                final[template_col] = raw[raw_col].apply(transformations[template_col])
            else:
                final[template_col] = raw[raw_col]
    
    for col in template.columns:
        if column_mapping.get(col) == "fixed" and col in fixed_values:
            final[col] = fixed_values[col]

    # Fill required columns with "not received" if missing
    for col in final.columns:
        if col in required_columns:
            final[col] = final[col].fillna("not received")
    return final

def build_transformations(conn):
    clean_stabilizer = make_cleaner(load_mapping(conn, "stabilizer_mappings"))
    clean_gender = make_cleaner(load_mapping(conn, "gender_mappings"))
    clean_single_double = make_cleaner(load_mapping(conn, "single_double_mappings"))
    clean_sample_timepoint = make_cleaner(load_mapping(conn, "sample_timepoint_mappings"))
    clean_stage = make_cleaner(load_mapping(conn, "stage_mappings"))
    clean_hemolysis = make_cleaner(load_mapping(conn, "hemolysis_mappings"))

    return {
        "Date of Blood Draw/Cell Collection": clean_date,
        "Time of Draw": clean_time,
        "Stabilizer": clean_stabilizer,
        "Gender": clean_gender,
        "Single or Double Spun": clean_single_double,
        "Sample Timepoint": clean_sample_timepoint,
        "Stage": clean_stage,
        "Hemolysis": clean_hemolysis
    }



if __name__ == "__main__":
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_new_password',
        database='mappings_db'
    )

    menopause_mapping = load_mapping(conn, "menopause_mappings", std_col="standard_term")
    biomarker_mapping = load_mapping(conn, "biomarker_mappings", std_col="standard_name")
    pos_neg_mapping = load_mapping(conn, "pos_neg_mappings")
    her2_ihc_mapping = load_mapping(conn, "her2_ihc_mappings")
    stabilizer_mapping = load_mapping(conn, "stabilizer_mappings")
    gender_mapping = load_mapping(conn, "gender_mappings")
    stage_mapping = load_mapping(conn, "stage_mappings")
    single_double_mapping = load_mapping(conn, "single_double_mappings")
    sample_timepoint_mapping = load_mapping(conn, "sample_timepoint_mappings")
    hemolysis_mapping = load_mapping(conn, "hemolysis_mappings")
    clean_biomarker = make_cleaner(biomarker_mapping)
    clean_gender = make_cleaner(gender_mapping)
    clean_stage = make_cleaner(stage_mapping)
    clean_hemolysis = make_cleaner(hemolysis_mapping)
    clean_stabilizer = make_cleaner(stabilizer_mapping)
    clean_single_double = make_cleaner(single_double_mapping)
    clean_sample_timepoint = make_cleaner(sample_timepoint_mapping)
    clean_pos_neg = make_cleaner(pos_neg_mapping)
    clean_her2_ihc = make_cleaner(her2_ihc_mapping)