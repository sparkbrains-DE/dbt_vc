{{ config(materialized='table',
enabled=true,
            database="snowflake_learning_db",
            schema="DIMENSIONS",
            alias="temp"
) }}

  with source_data as (
      select 1 as id
      union all
      select null as id
  )

  select *
  from source_data