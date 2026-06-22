# Shopping Analysis

This Assignment demonstrates a simple data analysis workflow using Python and Pandas on a shopping/e-commerce dataset. The goal is to explore the data, clean missing values, remove duplicates, create useful insights, and save a cleaned version of the dataset for further analysis.

Project Structure

```text
shopping-analysis/
│── data/
│   ├── combined_dataset.csv   # Raw dataset
│   └── cleaned_dataset.csv    # Cleaned dataset generated after analysis
│── notebook/
│   └── analysis.ipynb         # Jupyter Notebook containing the analysis
│── README.md
```

## What This Project Does

The notebook performs the following steps:

1. Loads the shopping dataset into a Pandas DataFrame.
2. Explores the dataset by checking its size, columns, data types, and sample records.
3. Handles missing values in important columns such as ratings, seller names, and product descriptions.
4. Filters highly rated products and selects key columns for easier analysis.
5. Removes duplicate products based on their product ID.
6. Creates a new column called `total_amount` by multiplying the product price and quantity.
7. Saves the cleaned dataset for future use.

## Running the Project

Open the notebook and run all cells:

```bash
cd notebook
jupyter notebook analysis.ipynb
```

Or execute it directly:

```bash
jupyter nbconvert --to notebook --execute notebook/analysis.ipynb
```

## Dataset Information

The dataset used in this project follows the same structure as the original shopping dataset available on Kaggle.

If you want to use the original dataset, simply replace the existing `combined_dataset.csv` file with the downloaded version. No code changes are required.

## Notes

* Product prices are stored as text with currency symbols (₹), so they are cleaned and converted into numeric values before calculations.
* Since the dataset does not contain an actual quantity column, a random quantity between 1 and 5 is generated for demonstration purposes.
* The generated `total_amount` values are only for practice and analysis; they do not represent real customer transactions.
* Only selected columns are cleaned for missing values. Additional cleaning steps can be added if required.

## Outcome

By the end of this project, you will have a cleaned dataset and a better understanding of how to perform data cleaning, transformation, and basic exploratory data analysis using Pandas.
