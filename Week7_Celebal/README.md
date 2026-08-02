# Delta Lake Incremental Processing Assignment

## Objective
This project demonstrates incremental data processing using Delta Lake with Apache Spark (PySpark). It includes data cleaning, Delta table creation, MERGE operations, and validation.

## Technologies Used
- Python
- Apache Spark (PySpark)
- Delta Lake
- Databricks
- GitHub

## Project Structure

delta-lake-assignment/
├── data/
├── notebooks/
├── screenshots/
├── report/
├── README.md
└── requirements.txt

## Steps Performed
1. Created the employee master dataset.
2. Removed null values and duplicate records.
3. Stored the cleaned data in a Delta table.
4. Created an incremental dataset.
5. Performed the Delta MERGE operation.
6. Validated the final dataset.
7. Displayed the updated Delta table.

## Expected Output
- Existing employee records are updated.
- New employee records are inserted.
- Duplicate records are removed.
- The final Delta table is validated successfully.

