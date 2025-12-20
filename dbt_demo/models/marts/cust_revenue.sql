{{ config(materialized='table',
alais="customer_revenue") }}

with sales as (
    select * from {{ ref('fact_sales') }}
)

select
    customer_id,
    customer_name,
    market_segment,
    nation_name,
    region_name,

    date_trunc('month', order_date) as order_month,

    count(distinct order_id) as total_orders,
    sum(quantity) as total_quantity,
    sum(net_price) as total_net_revenue,
    sum(gross_price) as total_gross_revenue,
    avg(discount) as avg_discount
from sales
group by
    customer_id,
    customer_name,
    market_segment,
    nation_name,
    region_name,
    order_month
