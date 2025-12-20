{{ config(materialized='table',
            enabled=true,
            database="snowflake_learning_db",
            schema="DIMENSIONS",
            alias="cust_dim_1",
            post_hook="GRANT SELECT ON {{ this }} TO ROLE analyst_tem"
            

) }}

with customer as (
    select
        c_custkey     as customer_id,
        c_name        as customer_name,
        c_nationkey   as nation_id,
        c_acctbal     as account_balance,
        c_mktsegment  as market_segment
    from {{ source('tpch', 'temp_customer') }}
),

nation as (
    select
        n_nationkey as nation_id,
        n_name      as nation_name,
        n_regionkey as region_id
    from {{ source('tpch', 'temp_nation') }}
),

region as (
    select
        r_regionkey as region_id,
        r_name      as region_name
    from {{ source('tpch', 'temp_region') }}
)

select
    c.customer_id,
    c.customer_name,
    c.market_segment,
    c.account_balance,
    n.nation_name,
    r.region_name
from customer c
left join nation n
    on c.nation_id = n.nation_id
left join region r
    on n.region_id = r.region_id
