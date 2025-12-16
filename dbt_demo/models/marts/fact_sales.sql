{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('stg_tpch_orders') }}
),

lineitem as (
    select * from {{ ref('stg_line_items') }}
),

customer as (
    select * from {{ ref('dim_customers') }}
)

select
    o.order_id,
    o.order_date,
    o.order_status,
    o.order_priority,

    c.customer_id,
    c.customer_name,
    c.market_segment,
    c.nation_name,
    c.region_name,

    l.part_id,
    l.supplier_id,
    l.line_number,

    l.quantity,
    l.extended_price,
    l.discount,
    l.tax,
    l.net_price,
    l.gross_price
from orders o
join lineitem l
    on o.order_id = l.order_id
left join customer c
    on o.customer_id = c.customer_id
