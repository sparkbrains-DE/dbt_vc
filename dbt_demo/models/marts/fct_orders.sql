{{ config(materialized='table',
alias='fact_orders_tbl2'
) }}

with orders as (
    select * from {{ ref('stg_tpch_orders') }}
),

customers as (
    select
        c_custkey     as customer_id,
        c_name        as customer_name,
        c_nationkey   as nation_id,
        c_acctbal     as account_balance,
        c_mktsegment  as market_segment
    from TEMP_DB.TEMP_SCHEMA.TEMP_CUSTOMER
)

select
    o.order_id,
    o.order_date,
    o.order_status,
    o.order_priority,
    o.customer_id,
    c.customer_name,
    c.market_segment,
    o.total_price
from orders o
left join customers c
    on o.customer_id = c.customer_id
