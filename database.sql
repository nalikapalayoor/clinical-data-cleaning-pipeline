CREATE DATABASE IF NOT EXISTS mappings_db;
USE mappings_db;

CREATE TABLE IF NOT EXISTS biomarker_mappings(
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_name VARCHAR(255) NOT NULL,
    synonym VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS pos_neg_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS her2_ihc_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS menopause_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_term VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS stabilizer_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS gender_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS single_double_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS sample_timepoint_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS stage_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);



CREATE TABLE IF NOT EXISTS hemolysis_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS diagnostic_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS race_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS smoking_history_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    standard_value VARCHAR(255),
    synonym VARCHAR(255)
);

/*
INSERT INTO biomarker_mappings (standard_name, synonym) VALUES
('HER2', 'her2'),
('ER', 'er'),
('ER', 'estrogen receptor'),
('PR', 'pr'),
('PR', 'progesterone receptor'),
('HER2 FISH', 'fish'),
('PDL1', 'pdl1'),
('ALK', 'alk'),
('ROS', 'ros'),
('EGFR', 'egfr'),
('KRAS', 'kras'),
('PIK3CA', 'pik3ca'),
('ESR1', 'esr1'),
('AR', 'ar'),
('BRCA1', 'BRCA1'),
('BRCA2', 'BRCA2'),
('Menopausal Status', 'menopause status');

INSERT INTO pos_neg_mappings (standard_value, synonym) VALUES
('positive', 'Positive'),
('positive', 'positive'),
('positive', 'strong positive'),
('positive', 'weak positive'),
('positive', 'moderately positive'),
('positive', '2+'),
('positive', '3+'),
('positive', '1'),
('positive', '2'),
('positive', '3'),
('positive', '4'),
('positive', '5'),
('positive', '6'),
('positive', '7'),
('positive', '8'),
('positive', '9'),
('positive', '10'),
('positive', '11'),
('positive', '12'),
('negative', 'Negative'),
('negative', 'negative'),
('negative', '0'),
('negative', 'none'),
('negative', 'not detected'),
('negative', '1+'),
('mutated', 'mutated'),
('mutated', 'mutation detected'),
('mutated', 'mutation'),
('mutated', 'mut'),
('not mutated', 'not mutated'),
('not mutated', 'no mutation detected'),
('not mutated', 'wild type'),
('not mutated', 'wt'),
('not mutated', 'no mutation'),
('not mutated', 'no mut');

INSERT INTO her2_ihc_mappings (standard_value, synonym) VALUES
('3+', '3+'),
('3+', '3'),
('3+', '3+ (strong)'),
('3+', '3+ (moderate)'),
('3+', '3+ (weak)'),
('2+/ISH-', '2+ (negative fish/cish)'),
('2+/ISH+', '2+ (positive fish/cish)'),
('1+', '1+'),
('1+', '1'),
('1+', '1+ (strong)'),
('1+', '1+ (moderate)'),
('1+', '1+ (weak)'),
('0', '0'),
('0', 'negative'),
('0', 'not detected'),
('0', 'no expression');


INSERT INTO menopause_mappings (standard_term, synonym) VALUES
('premenopause', 'pre menopause'),
('postmenopause', 'post menopause'),
('perimenopause', 'peri menopause'),
('not applicable', 'irrelevant'),
('menopause', 'menopause');


INSERT INTO stabilizer_mappings (standard_value, synonym) VALUES
('Streck', 'Streck Cell-Free DNA BCT');

INSERT INTO gender_mappings (standard_value, synonym) VALUES
('Male', 'm'),
('Male', 'male'),
('Male', 'M'),
('Male', 'Male'),
('Female', 'f'),
('Female', 'female'),
('Female', 'F'),
('Female', 'Female');

INSERT INTO single_double_mappings (standard_value, synonym) VALUES
('Single', 'single'),
('Single', 'Single'),
('Single', '1'),
('Double', 'double'),
('Double', 'Double'),
('Double', '2');

INSERT INTO sample_timepoint_mappings (standard_value, synonym) VALUES
('treatment-naïve', 'Initial-0');

INSERT INTO stage_mappings (standard_value, synonym) VALUES
('I', 'I'),
('I', 'IA'),
('I', 'IB'),
('II', 'II'),
('II', 'IIA'),
('II', 'IIB'),
('III', 'III'),
('III', 'IIIA'),
('III', 'IIIB'),
('IV', 'IV'),
('IV', 'IVA'),
('IV', 'IVB');

INSERT INTO hemolysis_mappings (standard_value, synonym) VALUES
('no hemolysis', 'No'),
('light hemolysis', 'Light Hemolysis'),
('hemolysis', ' Hemolysis'),
('strong hemolysis', 'Strong Hemolysis');
*/

