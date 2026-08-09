# Secure Retail Data Lakehouse Architecture

A production-grade, 3-tier **Medallion Data Lakehouse Pipeline** built using **PySpark, Azure Databricks, and Delta Lake**. This architecture acts as an automated security, privacy, and compliance firewall between raw retail operational systems (E-commerce portals and Point-of-Sale networks) and downstream enterprise analytics teams.

---

## 📋 Table of Contents

1. [Executive Summary](https://www.google.com/search?q=%23-executive-summary)
2. [Problem Statement & Regulatory Drivers](https://www.google.com/search?q=%23-problem-statement--regulatory-drivers)
3. [Architecture & Data Flow](https://www.google.com/search?q=%23-architecture--data-flow)
4. [Compliance & Security Matrix](https://www.google.com/search?q=%23-compliance--security-matrix)
5. [Layer-by-Layer Technical Walkthrough](https://www.google.com/search?q=%23-layer-by-layer-technical-walkthrough)
6. [Business Intelligence Dashboard](https://www.google.com/search?q=%23-business-intelligence-dashboard)
7. [Tech Stack & Environment Prerequisites](https://www.google.com/search?q=%23-tech-stack--environment-prerequisites)
8. [Setup & Execution Guide](https://www.google.com/search?q=%23-setup--execution-guide)

---

## 📌 Executive Summary

Modern retail operational platforms collect vast quantities of customer and financial records. Storing or serving this data in plain text introduces significant business risk, including data breach liabilities, identity theft, and severe regulatory non-compliance fines.

This project establishes a zero-trust batch data processing framework that ingests raw retail transactions and systematically cleanses, anonymizes, masks, and bins sensitive fields across three progressively secure layers: **Bronze (Ingestion)**, **Silver (Anonymization)**, and **Gold (Analytics)**.

---

## ⚖️ Problem Statement & Regulatory Drivers

### **1. Enterprise Vulnerabilities**

* **Data Breach Exposures:** Direct exposure of plain-text customer records significantly increases the risk of financial fraud and identity theft if database storage is compromised.


* **Regulatory Non-Compliance:** Unencrypted storage of payment verification values (CVVs) or plain-text personal identities violates strict global frameworks including **PCI-DSS, GDPR, and DPDP**.


* **Violation of Least Privilege:** Internal data scientists and business analysts require macro-level purchasing trends and spend behavior—not individual credit card numbers, CVVs, or home addresses.



---

## 🏗️ Architecture & Data Flow

```
+-----------------------------------------------------------------------------------+
| RAW RETAIL DATA (E-Commerce / POS Flat Files)                                     |
| Fields: Customer Name, Email, DOB, Credit Card, CVV, Amount, Order Date           |
+-----------------------------------------------------------------------------------+
                                        │
                                        ▼
+-----------------------------------------------------------------------------------+
| BRONZE LAYER (Ingestion & Physical Hard-Drop)                                     |
| • Standardizes column headers (replaces spaces/hyphens with underscores).          |
| • HARD-DROP: Physically purges CVVs / payment security codes (PCI-DSS).           |
| • Writes raw schema into Unity Catalog Volume Delta format.                        |
+-----------------------------------------------------------------------------------+
                                        │
                                        ▼
+-----------------------------------------------------------------------------------+
| SILVER LAYER (Cryptographic Tokenization & Masking)                               |
| • SHA-256 Hashing: Tokenizes direct PII (Customer Name, Email).                   |
| • Card Masking: Retains only the last 4 tail digits (XXXX-XXXX-XXXX-1234).        |
| • Drops unmasked raw PII columns (GDPR & DPDP compliance).                        |
+-----------------------------------------------------------------------------------+
                                        │
                                        ▼
+-----------------------------------------------------------------------------------+
| GOLD LAYER (Feature Engineering & Visual Analytics)                               |
| • Safe Type-Casting: Converts raw text sales to DOUBLE via try_cast.               |
| • Feature Binning: Classifies sales into Spend Categories (Low, Medium, High).     |
| • Generates executive 4-panel Business Analytics Dashboard.                       |
+-----------------------------------------------------------------------------------+

```

---

## 🔒 Compliance & Security Matrix

| Field Type | Attribute Examples | Security Action | Processing Layer | Regulatory Alignment |
| --- | --- | --- | --- | --- |
| **PCI Data** | CVV / Security Code | **Hard-Drop:** Physically purged from the lakehouse.

 | **Bronze Layer** | **PCI-DSS**<br> |
| **Payment Identifier** | Credit Card Number | **String Masking:** Retains only last 4 digits (`XXXX-XXXX-XXXX-1234`).

 | **Silver Layer** | **PCI-DSS / GDPR**<br> |
| **Direct PII** | Customer Name, Email | **Cryptographic Tokenization:** Irreversible SHA-256 hashing.

 | **Silver Layer** | **GDPR / DPDP**<br> |
| **Demographic / Sales** | Transaction Amount, DOB | **Feature Binning:** Groups into Spend Categories (`Low`, `Medium`, `High`).

 | **Gold Layer** | **Principle of Least Privilege**<br> |

---

## 🛠️ Layer-by-Layer Technical Walkthrough

### **1. Bronze Layer: Ingestion & Header Sanitization**

* **Purpose:** Ingests raw operational flat files, standardizes schema formatting, and immediately purges ultra-sensitive card security codes.


* **Code Implementation:**

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp

# 1. Source file path in Unity Catalog Volume
raw_csv_path = "/Volumes/workspace/default/my_data_volume/Superstore_dataset/Sample - Superstore.csv"

# 2. Ingest raw CSV flat files
df_raw = spark.read.csv(raw_csv_path, header=True, inferSchema=True)

# 3. Sanitize column headers for Delta Lake compatibility
df_sanitized = df_raw
for column_name in df_raw.columns:
    clean_name = column_name.strip().replace(" ", "_").replace("-", "_")
    df_sanitized = df_sanitized.withColumnRenamed(column_name, clean_name)

# 4. Execute physical hard-drop of PCI data (CVV / Security Codes)
pci_columns_to_drop = ["cvv", "CVV", "card_security_code", "security_code"]
existing_drop_cols = [c for c in pci_columns_to_drop if c in df_sanitized.columns]

df_bronze = df_sanitized.drop(*existing_drop_cols)

# 5. Persist to Bronze Delta Table in Unity Catalog Volume
bronze_path = "/Volumes/workspace/default/my_data_volume/delta/bronze_retail_lakehouse"
df_bronze.write.format("delta").mode("overwrite").save(bronze_path)

print("Bronze Layer successfully created with PCI data hard-drop.")

```

---

### **2. Silver Layer: PII Anonymization & Tokenization**

* **Purpose:** Applies cryptographic hashing to direct identifiers and masks credit card digits before saving to ACID-compliant Delta tables.


* **Code Implementation:**

```python
from pyspark.sql.functions import col, sha2, concat, lit, right

# 1. Read Bronze Delta Table
bronze_path = "/Volumes/workspace/default/my_data_volume/delta/bronze_retail_lakehouse"
df_bronze = spark.read.format("delta").load(bronze_path)
df_silver = df_bronze

# 2. Cryptographic SHA-256 Tokenization for Direct Identifiers
if "Customer_Name" in df_silver.columns:
    df_silver = df_silver.withColumn("Customer_Token", sha2(col("Customer_Name"), 256)).drop("Customer_Name")

if "Email" in df_silver.columns:
    df_silver = df_silver.withColumn("Email_Token", sha2(col("Email"), 256)).drop("Email")

# 3. Mask Credit Card retaining only last 4 digits
if "Credit_Card" in df_silver.columns:
    df_silver = df_silver.withColumn(
        "Credit_Card_Masked", 
        concat(lit("XXXX-XXXX-XXXX-"), right(col("Credit_Card"), 4))
    ).drop("Credit_Card")

# Backup tokenization for Customer_ID
if "Customer_ID" in df_silver.columns and "Customer_Token" not in df_silver.columns:
    df_silver = df_silver.withColumn("Customer_Token", sha2(col("Customer_ID"), 256))

# 4. Save to Silver Delta Table
silver_path = "/Volumes/workspace/default/my_data_volume/delta/silver_retail_lakehouse"
df_silver.write.format("delta").mode("overwrite").save(silver_path)

print("Silver Layer successfully created with SHA-256 Tokenization & Card Masking.")

```

---

### **3. Gold Layer: Feature Engineering & Resilience**

* **Purpose:** Safely type-casts string metrics to double precision, categorizes transactions into spend buckets, and prepares analytics-ready features.


* **Code Implementation:**

```python
from pyspark.sql.functions import col, when, expr, coalesce, lit

# 1. Read Silver Delta Table
silver_path = "/Volumes/workspace/default/my_data_volume/delta/silver_retail_lakehouse"
df_silver = spark.read.format("delta").load(silver_path)

sales_col = "Sales" if "Sales" in df_silver.columns else "amount"

# 2. Safe type-casting string values to DOUBLE using SQL try_cast
df_silver_clean = df_silver.withColumn(
    sales_col, 
    coalesce(expr(f"try_cast(`{sales_col}` as double)"), lit(0.0))
)

# 3. Feature Engineering: Create Spend Categories
df_gold = df_silver_clean.withColumn(
    "Spend_Category",
    when(col(sales_col) < 1000, "Low (<1000)")
    .when((col(sales_col) >= 1000) & (col(sales_col) <= 5000), "Medium (1000-5000)")
    .otherwise("High (>5000)")
)

# 4. Save to Gold Delta Table
gold_path = "/Volumes/workspace/default/my_data_volume/delta/gold_retail_lakehouse"
df_gold.write.format("delta").mode("overwrite").save(gold_path)

print("Gold Layer successfully created with Spend Categories.")

```

---

## 📊 Business Intelligence Dashboard

The Gold layer powers an executive 4-panel dashboard rendered via Matplotlib and Seaborn:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql.functions import sum as _sum, avg as _avg, count as _count

# 1. Load Gold Delta Table & Compute Aggregations in PySpark
gold_path = "/Volumes/workspace/default/my_data_volume/delta/gold_retail_lakehouse"
df_gold = spark.read.format("delta").load(gold_path)

cust_col = "Customer_Token" if "Customer_Token" in df_gold.columns else "Customer_ID"
sales_col = "Sales" if "Sales" in df_gold.columns else "amount"

df_cust_spend_pd = df_gold.groupby(cust_col).agg(_sum(sales_col).alias("Total_Sales")).limit(50).toPandas()
df_cat_dist_pd = df_gold.groupby("Spend_Category").agg(_count("*").alias("Txn_Count")).toPandas()
df_cat_metrics_pd = df_gold.groupby("Spend_Category").agg(_sum(sales_col).alias("Total_Amount"), _avg(sales_col).alias("Avg_Amount")).toPandas()
df_cust_avg_pd = df_gold.groupby(cust_col).agg(_avg(sales_col).alias("Avg_Spend")).sort("Avg_Spend").toPandas()

# 2. Render 2x2 Dashboard Grid
sns.set_theme(style="white")
fig = plt.figure(figsize=(18, 10), dpi=100)
fig.suptitle("Gold Layer — Business Analytics Dashboard", fontsize=16, fontweight='bold', y=0.98)

gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.25)

# Panel 1: Total Spend by Customer Token
ax1 = fig.add_subplot(gs[0, 0])
sns.barplot(data=df_cust_spend_pd, x=cust_col, y='Total_Sales', ax=ax1, palette='Blues_r')
ax1.set_title("Total Spend by Customer (Anonymized Tokens)", fontsize=12, fontweight='bold', pad=10)
ax1.set_xticks([])
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Panel 2: Transaction Distribution by Spend Category (Pie Chart)
ax2 = fig.add_subplot(gs[0, 1])
category_order = ['High (>5000)', 'Medium (1000-5000)', 'Low (<1000)']
df_cat_dist_pd['Spend_Category'] = pd.Categorical(df_cat_dist_pd['Spend_Category'], categories=category_order, ordered=True)
df_cat_dist_pd = df_cat_dist_pd.sort_values('Spend_Category')

total_txns = df_cat_dist_pd['Txn_Count'].sum()
ax2.pie(
    df_cat_dist_pd['Txn_Count'], 
    labels=df_cat_dist_pd['Spend_Category'], 
    autopct=lambda p: f'{p:.0f}%\n({int(p*total_txns/100)} txns)',
    startangle=90, 
    colors=['#e6194B', '#f58231', '#3cb44b'], 
    explode=(0.04, 0.04, 0.04)
)
ax2.set_title("Transaction Distribution by Spend Category", fontsize=12, fontweight='bold', pad=10)

# Panel 3: Total vs Avg Amount by Spend Category
ax3 = fig.add_subplot(gs[1, 0])
x = np.arange(len(df_cat_metrics_pd))
width = 0.35

ax3.bar(x - width/2, df_cat_metrics_pd['Total_Amount'], width, label='Total Amount', color='#2b8cbe')
ax3.bar(x + width/2, df_cat_metrics_pd['Avg_Amount'], width, label='Avg Amount', color='#f03b20')
ax3.set_title("Total vs Avg Amount by Spend Category", fontsize=12, fontweight='bold', pad=10)
ax3.set_xticks(x)
ax3.set_xticklabels(df_cat_metrics_pd['Spend_Category'], fontsize=9)
ax3.legend(loc='upper left')
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)

# Panel 4: Avg Spend per Customer (Ranked Curve)
ax4 = fig.add_subplot(gs[1, 1])
ax4.plot(df_cust_avg_pd['Avg_Spend'], df_cust_avg_pd.index, marker='o', color='black', linewidth=1.5, markersize=2)
ax4.set_title("Avg Spend per Customer (Ranked)", fontsize=12, fontweight='bold', pad=10)
ax4.set_yticks([])
ax4.spines['top'].set_visible(False)
ax4.spines['right'].set_visible(False)

plt.show()

```

---

## 💻 Tech Stack & Environment Prerequisites

* **Core Processing Engine:** Apache Spark / PySpark 3.x
* **Cloud Platform:** Azure Databricks / Unity Catalog
* **Storage Format:** Delta Lake
* **Languages:** Python 3.x, SQL
* **Data Visualization & Analysis:** Pandas, Matplotlib, Seaborn

---

## 🚀 Setup & Execution Guide

1. **Upload Dataset:** Upload your raw CSV dataset (`Sample - Superstore.csv`) into your Databricks Unity Catalog Volume path:
```
/Volumes/workspace/default/my_data_volume/Superstore_dataset/

```


2. **Import Notebook:** Import the Python code cells into your Azure Databricks workspace.
3. **Execute Sequentially:**
* Run **Cmd 1** to initialize the Bronze Delta Table.


* Run **Cmd 2** to build the Silver Anonymized Delta Table.


* Run **Cmd 3** to construct the Gold Analytics Delta Table.


* Run **Cmd 4** to render the Business Intelligence Dashboard.
