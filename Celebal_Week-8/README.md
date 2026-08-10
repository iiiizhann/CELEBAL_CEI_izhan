# 📊 E-Commerce Analytics System

An end-to-end data analytics project that processes and analyzes e-commerce order data using **Python, Pandas, SQLite, and SQL**. The system generates realistic synthetic datasets with intentional inconsistencies, performs data cleaning and validation, loads cleaned data into a relational database, executes advanced SQL analytics, and provides business reports through a command-line interface.

---

## 🚀 Project Objective

The objective of this project is to build a complete data analytics pipeline that:

- Generates realistic e-commerce datasets.
- Introduces intentional data quality issues.
- Cleans and validates data using Pandas.
- Maintains referential integrity across multiple tables.
- Loads cleaned data into a relational SQL database.
- Performs advanced SQL analytics.
- Generates business insights through a CLI reporting tool.
- Handles edge cases to ensure robustness and reliability.

---

## 📁 Project Structure

```
ecommerce-analytics-system/
│
├── data/
│   ├── raw/
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   ├── orders.csv
│   │   └── order_items.csv
│   │
│   ├── cleaned/
│   │   ├── customers_clean.csv
│   │   ├── products_clean.csv
│   │   ├── orders_clean.csv
│   │   ├── order_items_clean.csv
│   │   └── validation_report.json
│   │
│   └── ecommerce.db
│
├── scripts/
│   ├── generate_data.py
│   ├── clean_data.py
│   ├── load_db.py
│   └── report_cli.py
│
├── sql/
│   ├── schema.sql
│   ├── aggregations.sql
│   ├── window_functions.sql
│   └── cohort_analysis.sql
│
├── output/
│   └── sample_reports/
│
├── requirements.txt
├── run_all.py
└── README.md
```

---

# 🛠 Technologies Used

- Python 3.x
- Pandas
- NumPy
- Faker
- SQLite
- SQL
- Tabulate
- argparse

---

# 📦 Installation

Clone the repository

```bash
git clone https://github.com/nikhilkhot1014/ecommerce-analytics-system.git

cd ecommerce-analytics-system
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Project

Run the complete pipeline

```bash
python run_all.py
```

Or execute each step individually

### Step 1 – Generate Dataset

```bash
python scripts/generate_data.py
```

### Step 2 – Clean Data

```bash
python scripts/clean_data.py
```

### Step 3 – Load Database

```bash
python scripts/load_db.py
```

### Step 4 – Generate Reports

```bash
python scripts/report_cli.py --report overview
```

---

# 📊 Features

## Dataset Generation

Generates realistic datasets for:

- Customers
- Products
- Orders
- Order Items

Injects intentional inconsistencies including:

- Missing values
- Duplicate records
- Invalid emails
- Negative prices
- Future dates
- Invalid IDs
- Incorrect order status

---

## Data Cleaning

Using Pandas:

- Remove duplicates
- Handle missing values
- Validate emails
- Correct invalid dates
- Standardize formats
- Remove orphan records
- Validate foreign keys
- Generate validation report

---

## SQL Database

Implements:

- Primary Keys
- Foreign Keys
- NOT NULL constraints
- CHECK constraints
- Indexes

---

# 📈 SQL Analytics

The project includes advanced SQL queries using:

## Joins

- Customer Orders
- Product Sales
- Revenue Analysis

## Aggregations

- Total Revenue
- Monthly Revenue
- Revenue by Category
- Average Order Value
- Product Sales

## Window Functions

- RANK()
- DENSE_RANK()
- LAG()
- LEAD()
- SUM() OVER()
- AVG() OVER()

## Common Table Expressions (CTEs)

Used for:

- Revenue Growth
- Customer Lifetime Value
- Monthly Trends

## Cohort Analysis

- Customer Cohorts
- Monthly Retention
- Repeat Customers
- Churn Analysis

---

# 👥 Customer Segmentation

Customers are segmented into:

- One-Time Customers
- Occasional Customers
- Loyal Customers
- High Value Customers
- Medium Value Customers
- Low Value Customers

RFM Analysis includes:

- Recency
- Frequency
- Monetary Value

---

# 💻 Command Line Reports

Example commands

Overview

```bash
python scripts/report_cli.py --report overview
```

Revenue

```bash
python scripts/report_cli.py --report revenue
```

Top Customers

```bash
python scripts/report_cli.py --report top_customers
```

Top Products

```bash
python scripts/report_cli.py --report top_products
```

Retention

```bash
python scripts/report_cli.py --report retention
```

Customer Segmentation

```bash
python scripts/report_cli.py --report rfm
```

Churn Report

```bash
python scripts/report_cli.py --report churn
```

---

# 📋 Business Insights

The analytics module provides:

- Monthly Revenue Trends
- Top Customers
- Best Selling Products
- Category Performance
- Customer Lifetime Value
- Revenue Growth
- Customer Retention
- Churn Analysis
- RFM Segmentation

---

# ⚠️ Edge Case Handling

The system handles:

- Empty datasets
- Missing files
- Invalid CLI inputs
- Missing database
- Invalid IDs
- Duplicate records
- Future dates
- Database connection errors
- Division by zero
- Null values

---

# 📄 Validation Report

A validation report is automatically generated after cleaning.

Example:

```
data/cleaned/validation_report.json
```

The report contains:

- Duplicate records removed
- Missing values handled
- Invalid emails corrected
- Future dates fixed
- Orphan records removed

---

# 📌 Sample Output

```
Overview Report

Customers      : 2500
Products       : 180
Orders         : 11897
Order Items    : 35799

Total Revenue  : $32.6M

Top Category   : Clothing

Top Customer   : Customer 1045
```

---

# 📚 Learning Outcomes

This project demonstrates:

- Python Programming
- Data Cleaning
- Data Validation
- Data Engineering
- SQL Development
- Window Functions
- CTEs
- Cohort Analysis
- Customer Segmentation
- Business Intelligence
- Command Line Application Development

---

# 👨‍💻 Author

**Nikhil Khot**

M.Sc. Computer Science  
MIT World Peace University

---

# 📜 License

This project is developed for educational and learning purposes.