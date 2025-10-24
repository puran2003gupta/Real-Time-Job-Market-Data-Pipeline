CREATE OR REPLACE STORAGE INTEGRATION s3_int_snowflake
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::8167XXXXXX:role/Snowflake-Integration'
  STORAGE_ALLOWED_LOCATIONS = ('s3://your-pipeline-name-puran/transformed/job_data/');

CREATE OR REPLACE STAGE job_data_ext_stage
  URL = 's3://your-pipeline-name-puran/transformed/job_data/'
  STORAGE_INTEGRATION = s3_int_snowflake
  FILE_FORMAT = (TYPE = PARQUET);

list @job_data_ext_stage

CREATE OR REPLACE PIPE job_data_analytics_pipe
  AUTO_INGEST = TRUE
  AS
  COPY INTO job_data_alalytics
  FROM @job_data_ext_stage
  FILE_FORMAT = (TYPE = PARQUET)
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

  show pipes

