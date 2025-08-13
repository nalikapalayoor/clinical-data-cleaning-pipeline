import pandas as pd
import re
from datetime import datetime



required_columns= [
    "Tube Barcode","Concentration Units","Single or Double Spun","Processing Method","Freeze Thaw Status","Project",
    "Matched FFPE Available","Surgery Type","Tumor Tissue Type","Other Sample Notes","Collection Site","Histology",
    "Sample Timepoint","Sample Timepoint Description","Detailed Anatomical Location","Grade","Tumor Size","TNM","Stage",
    "Stage_detailed","Morphology Code","Description of Morphology Code","Metastatic Sites","Vehicle Control","Media Conditions",
    "Additional Supplements to Media","Protocols for Harvesting Cell Lines","Menopausal Status","HER2 IHC","HER2","FISH",
    "HER2 Change from Previous Sample","ER","ER Notes","ER Status Change From Previous Sample","PR","PR Notes",
    "PR Status Change From Previous Sample","AR Notes","AR Status Change From Previous Sample","ROS","ALK","EGFR",
    "EGFR Allele Information","PDL1","KRAS","PIK3CA", "ESR1","BRCA1","BRCA2","FOLR1","Biomarker Notes","Country",
    "Gender","Race","SmokingHistory"
]




# If there are new synonyms found in the raw data, don't delete the old ones, just add to the lists below

menopause_mapping= {
    "premenopause": ["pre menopause"],
    "postmenopause": ["post menopause"],
    "perimenopause": ["peri menopause"],
    "not applicable": ["irrelevant"],
    "menopause": ["menopause"]
}

biomarker_lookup = {
    "HER2": ["her2"],
    "ER": ["er", "estrogen receptor"],
    "PR": ["pr", "progesterone receptor"],
    "HER2 FISH": ["fish"],
    "PDL1": ["pdl1"],
    "ALK": ["alk"],
    "ROS": ["ros"],
    "EGFR": ["egfr"],
    "KRAS": ["kras"],
    "PIK3CA": ["pik3ca"],
    "ESR1": ["esr1"],
    "AR": ["ar"],
    "BRCA1": ["BRCA1"],
    "BRCA2": ["BRCA2"],
    "Menopausal Status": ['menopause status']

}

pos_neg_mapping = {
    "positive": ["Positive","positive", "strong positive", "weak positive", "moderately positive", "2+", "3+", "1", "2","3","4","5","6","7","8","9","10","11","12"],
    "negative": ["Negative","negative", "0", "none", "not detected", "1+"],
    "mutated": ["mutated", "mutation detected", "mutation", "mut"],
    "not mutated": ["not mutated", "no mutation detected", "wild type", "wt", "no mutation", "no mut"]
}

her2_ihc_mapping= {
    "3+": ["3+", "3", "3+ (strong)", "3+ (moderate)", "3+ (weak)"],
    "2+/ISH-": ["2+ (negative fish/cish)"],
    "2+/ISH+": ["2+ (positive fish/cish)"],
    "1+": ["1+", "1", "1+ (strong)", "1+ (moderate)", "1+ (weak)"],
    "0": ["0", "negative", "not detected", "no expression"]
}


# function factory for basic mapping cleaning
def make_cleaner(mapping_dict):
    """
    Given a mapping dictionary, returns a cleaning function that maps raw values to the standard values
    Parameters:
        mapping_dict (dict): dictionary where keys are standard values and values are lists of raw value options
    Returns: 
        function: takes a single value and returns the cleaned value or pd.NA if not found
    """
    lookup= {}
    for standard_val, raw_options in mapping_dict.items():
        for raw_val in raw_options:
            lookup[str(raw_val).strip().lower()]= standard_val
    def cleaner(val):
        if pd.isna(val):
            return pd.NA
        val_str= str(val).strip().lower()
        return lookup.get(val_str, pd.NA)
    return cleaner

# create functions from function factory (add to dictionaries as you find new synonyms in the raw data)
clean_stabilizer= make_cleaner({
    "Streck": ["Streck Cell-Free DNA BCT"]
})

clean_gender= make_cleaner({
    "Male": ['m', 'male', 'M', 'Male'],
    "Female": ['f', 'female', 'F', 'Female']
})

clean_single_double= make_cleaner({
    "Single": ['single', 'Single','1'],
    "Double": ['double', 'Double','2']
})

clean_sample_timepoint= make_cleaner({
    "treatment-naïve": ["Initial-0"]
})

clean_stage= make_cleaner({
    "I": ["I", "IA", "IB"],
    "II": ["II", "IIA", "IIB"],
    "III": ["III", "IIIA", "IIIB"],
    "IV": ["IV", "IVA", "IVB"]
})

clean_hemolysis= make_cleaner({
    "no hemolysis": ["No"],
    "light hemolysis": ["Light Hemolysis"],
    "hemolysis": [" Hemolysis"],
    "strong hemolysis": ["Strong Hemolysis"]
})

# calls the calculation functions for elapsed days
def call_calculation_functions(final_df, raw_df, mapping_dict):
    for new_col, (col1, col2) in mapping_dict.items():
        final_df[new_col] = raw_df.apply(
            lambda row: calculate_elapsed_days(row, col1, col2), axis=1
        )
    return final_df

# functions to put the date and time in the correct format
def clean_date(val):
    """
    Cleans and formats a date string.
    Parameters:
        val (str): raw date string
    Returns:
        str or pd.NA: cleaned date string in "YYYY-MON-DD" format or pd.NA if not found
    """
    if pd.isna(val):
        return pd.NA

    try:
        return pd.to_datetime(val).strftime("%Y-%B-%d")
    except:
        return pd.NA

def clean_time(val):
    """
    Cleans and formats a time string.
    Parameters:
        val (str): raw time string
    Returns:
        str or pd.NA: cleaned time string in "HH:MM:SS AM/PM" format or pd.NA if not found
    """
    if pd.isna(val):
        return pd.NA

    try:
        return pd.to_datetime(val).strftime("%I:%M:%S %p")
    except: 
        return pd.NA

# functions for columns that need to be calculated
def calculate_age(birth_val, collection_date):
    """
    Calculates age in years given birth date (or year) and collection date. If only year is given for birth date, assumes Jan 1 of that year.
    Parameters:
        birth_val (str): raw birth date string
        collection_date (str): raw collection date string
    Returns:
        int or pd.NA: age in years or pd.NA if not calculable
    """
    if pd.isna(birth_val) or pd.isna(collection_date):
        return pd.NA
    try:
        birth_str= str(birth_val).strip()
        if len(birth_str)== 4 and birth_str.isdigit():
            birth_date= pd.to_datetime(f"{birth_str}-01-01")
        else:
            birth_date= pd.to_datetime(birth_str, errors= "coerce")
        collection_dt= pd.to_datetime(collection_date, errors= "coerce")

        age= (collection_dt-birth_date).days // 365
        return age
    except:
        return pd.NA

def calculate_elapsed_days(row, start_col, end_col):
    """
    Calculates elapsed days between two date columns in a row.
    Parameters:
        row (pd.Series): a row of the dataframe containing date information
        start_col (str): name of the column with the start date
        end_col (str): name of the column with the end date
    Returns:
        int or pd.NA: number of elapsed days or pd.NA if not calculable
    """
    start_val= row.get(start_col)
    end_val= row.get(end_col)

    if pd.isna(start_val):
        return pd.NA
    if pd.isna(end_val):
        return pd.NA
    try:
        start_date= pd.to_datetime(start_val, errors= "coerce")
        end_date= pd.to_datetime(end_val, errors= "coerce")

        if pd.isna(start_date) or pd.isna(end_date):
            return pd.NA

        delta= (end_date-start_date).days
        return delta if delta >= 0 else pd.NA
    except:
        return pd.NA
    
def calculate_bmi(weight, height):
    """
    Calculates BMI given weight in kg and height in cm.
    Parameters:
        weight (float): weight in kg
        height (float): height in cm
    Returns:
        float or pd.NA: BMI value or pd.NA if not calculable
    """
    weight = pd.to_numeric(weight, errors="coerce")
    height = pd.to_numeric(height, errors="coerce")

    if pd.isna(weight) or pd.isna(height) or height == 0:
        return 'noooo'
    try:
        height_m= height / 100
        bmi= weight / (height_m ** 2)
        return round(bmi, 2)
    except:
        return 'helpppp'
    
# function to extract biomarker data from blob text (blob is all biomarker columns concatenated)
def extract_biomarkers_from_blob(blob, biomarker_lookup, pos_neg_mapping, her2_ihc_mapping):
    '''
    Extracts biomarker data from a concatenated blob of text.
    Parameters:
        blob (str): concatenated biomarker text
        biomarker_lookup (dict): dictionary mapping template columns to lists of raw biomarker variants
        pos_neg_mapping (dict): dictionary mapping positive/negative labels to lists of raw values
    Returns:
        dict: extracted biomarker values mapped to template columns
    '''
    results= {}
    blob= blob.replace("=", " = ")
    blob= re.sub(r'\s+', ' ', blob).strip().lower()

    biomarker_keys= sorted(
        [re.escape(v.lower()) for variants in biomarker_lookup.values() for v in variants],
        key= len,
        reverse= True
    )
    lookahead_pattern= r'(?=\s+\b(?:' + '|'.join(biomarker_keys) + r')\b\s*=|$)'

    fish_match= re.search(r'\bfish\b\s*=\s*([^\s=]+)', blob)
    fish_val= fish_match.group(1).strip() if fish_match else None

    for template_col, variants in biomarker_lookup.items():
        for variant in variants:
            variant= variant.lower()
            pattern= rf'\b{re.escape(variant)}\b\s*=\s*(.*?){lookahead_pattern}'
            match= re.search(pattern, blob)
            if match:
                raw_val= match.group(1).strip()

                if template_col== "HER2":
                    her2_match= re.search(r'(0|1\+|2\+|3\+)', raw_val)
                    if her2_match:
                        her2_score= her2_match.group(1)
                        if her2_score in ["0", "1+"]:
                            mapped= "negative"
                        elif her2_score== "3+":
                            mapped= "positive"
                        elif her2_score== "2+":
                            if fish_val in pos_neg_mapping.get("positive", []):
                                mapped= "positive"
                            elif fish_val in pos_neg_mapping.get("negative", []):
                                mapped= "negative"
                            else:
                                mapped= "HER2 2+ (FISH/ISH missing)"
                        else:
                            mapped= pd.NA

                        for mapped_ihc, variants in her2_ihc_mapping.items():
                            if raw_val in variants:
                                results['HER2 IHC'] = mapped_ihc
                                break
                        else:
                            results['HER2 IHC'] = raw_val
                    else:
                        mapped= raw_val
                else:
                    mapped= None
                    for label, values in pos_neg_mapping.items():
                        if raw_val in values:
                            mapped= label
                            break
                    if mapped is None:
                        mapped= raw_val

                results[f"{template_col} Value"] = raw_val
                results[template_col]= mapped
                break

    return results

def extract_menopause_status(val_str):
    '''
    Extracts menopause status from a given string.
    Parameters:
        val_str (str): input string potentially containing menopause status
    Returns:
        str: mapped menopause status or pd.NA if not found
    '''
    val_str= val_str.lower()
    
    for clean_val, options in menopause_mapping.items():
        for opt in options:
            if opt in val_str:
                return clean_val
    return pd.NA



# transformation registry (key: template column, value: cleaning function)
# add a new row to the dictionary for each new function you create or use
transformations= {
    "Date of Blood Draw/Cell Collection": clean_date,
    "Time of Draw": clean_time,
    "Stabilizer": clean_stabilizer,
    "Gender": clean_gender,
    "Single or Double Spun": clean_single_double,
    "Sample Timepoint": clean_sample_timepoint,
    "Stage": clean_stage,
    "Hemolysis": clean_hemolysis
}



# load in the data


def process_raw_to_template(
    template,
    raw,
    shipping_manifest,
    dataset,
    transformer,
    transform_date,
    column_mapping,
    fixed_values,
    biomarker_cols,
    calculation_functions,
    extract_menopause_from_biomarker=True
):
    final = pd.DataFrame(index=raw.index, columns=template.columns)

    # create the biomarker blob
    raw['biomarker_blob'] = raw[biomarker_cols]\
        .astype(str)\
        .replace('nan', '')\
        .agg(' '.join, axis=1)\
        .str.replace(r'\s+', ' ', regex=True)\
        .str.strip()

    # merge raw with shipping
    raw = pd.merge(raw, shipping_manifest, left_on='Patient ID\nconsecutive',
                   right_on='Patient ID consecutive', how="left")

    # Extract biomarkers
    biomarker_data = raw['biomarker_blob'].apply(
        lambda row: extract_biomarkers_from_blob(row, biomarker_lookup, pos_neg_mapping, her2_ihc_mapping)).to_dict()
    for idx, result in biomarker_data.items():
        for biomarker, val in result.items():
            final.at[idx, biomarker] = val

    # Extract menopause
    if extract_menopause_from_biomarker:
        final['Menopausal Status'] = raw['biomarker_blob'].apply(extract_menopause_status)

    # Call calculation functions
    call_calculation_functions(final, raw, calculation_functions)

    # Age
    final["AgeAtCollection"] = raw.apply(
        lambda row: calculate_age(row.get("Year of birth"), row.get("Date of blood collection [yyyy-mm-dd]")), axis=1)

    # BMI
    final["BMI"] = raw.apply(
        lambda row: calculate_bmi(row.get("Maximum weight [kg] "), row.get("Body height [cm]")), axis=1)

    # Fixed values
    for col, val in fixed_values.items():
        if col in final.columns:
            final[col] = val

    # Map values from raw to template
    for template_col in column_mapping:
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
