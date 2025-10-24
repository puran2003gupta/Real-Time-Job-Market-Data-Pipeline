
import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.sql.functions import col, year, month, lower, trim, explode, size, split, array_contains

# Initialize Glue job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read the JSON file (single object with 'results' array)
#input_path = "s3://job-market-pipeline-puran/raw/job_data/adzuna_job_data.json"
input_path = "s3://job-market-pipeline-puran/raw/job_data/"
df_raw = spark.read.option("multiLine", True).json(input_path)

# Explode the 'results' array
df = df_raw.select(explode(col("results")).alias("job")).select("job.*")

# Flatten nested fields
df_flat = df.select(
    col("id"),
    col("title"),
    col("company.display_name").alias("company_name"),
    col("location.area").getItem(0).alias("country"),
    col("location.area").getItem(1).alias("state"),
    col("location.area").getItem(2).alias("city"),
    col("created"),
    col("category.label").alias("job_category"),
    col("description")
)

# Clean: Remove nulls
df_clean = df_flat.na.drop(subset=["title", "company_name"])

# Deduplicate
df_dedup = df_clean.dropDuplicates(["id"])

# Add derived columns
df_final = df_dedup.withColumn("year", year(col("created"))) \
                   .withColumn("month", month(col("created"))) \
                   .withColumn("title_normalized", trim(lower(col("title"))))

# Extract skills from description
skill_keywords = ["python", "sql", "spark", "hadoop", "aws", "azure", "gcp", "airflow", "databricks", "snowflake"]
for skill in skill_keywords:
    df_final = df_final.withColumn(f"skill_{skill}", col("description").rlike(f"(?i)\\b{skill}\\b").cast("int"))

# Count of jobs per company
jobs_per_company = df_final.groupBy("company_name").count().withColumnRenamed("count", "job_count_per_company")

# Count of jobs per skill (flattened)
from functools import reduce
from pyspark.sql import DataFrame

skill_counts = []
for skill in skill_keywords:
    skill_df = df_final.filter(col(f"skill_{skill}") == 1).groupBy().count().withColumn("skill", col("count").cast("string")).withColumnRenamed("count", "job_count").withColumn("skill", col("skill").substr(1, 100))
    skill_counts.append(skill_df)

# Count of jobs per city and month
jobs_per_city_month = df_final.groupBy("city", "year", "month").count().withColumnRenamed("count", "job_count_city_month")

# Join city-month job counts back to main DataFrame
df_enriched = df_final.join(jobs_per_city_month, on=["city", "year", "month"], how="left")

# Write final enriched data to S3 in Parquet format
output_path = "s3://job-market-pipeline-puran/transformed/job_data/"
df_enriched.write.mode("overwrite").parquet(output_path)

job.commit()