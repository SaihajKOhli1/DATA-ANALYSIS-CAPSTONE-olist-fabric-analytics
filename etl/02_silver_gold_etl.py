# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Silver & Gold Layer ETL
# MAGIC Transforms `olist_ecommerce.bronze.*` into cleaned/deduplicated
# MAGIC `olist_ecommerce.silver.*` tables, then aggregates those into
# MAGIC `olist_ecommerce.gold.*` fact tables per `specs/02-silver-gold-etl.md`.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

CATALOG = "olist_ecommerce"
BRONZE = f"{CATALOG}.bronze"
SILVER = f"{CATALOG}.silver"
GOLD = f"{CATALOG}.gold"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {GOLD}")


def write_table(df, full_table_name):
    df.write.mode("overwrite").format("delta").saveAsTable(full_table_name)
    count = spark.table(full_table_name).count()
    print(f"{full_table_name}: {count} rows")


# COMMAND ----------

# MAGIC %md
# MAGIC ## SILVER LAYER

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. silver.orders
# MAGIC Dedup key: order_id. Cast timestamp columns.

# COMMAND ----------

bronze_orders = spark.table(f"{BRONZE}.orders")

silver_orders = (
    bronze_orders
    .dropDuplicates()
    .dropDuplicates(["order_id"])
    .withColumn("order_purchase_timestamp", F.col("order_purchase_timestamp").cast("timestamp"))
    .withColumn("order_approved_at", F.col("order_approved_at").cast("timestamp"))
    .withColumn("order_delivered_carrier_date", F.col("order_delivered_carrier_date").cast("timestamp"))
    .withColumn("order_delivered_customer_date", F.col("order_delivered_customer_date").cast("timestamp"))
    .withColumn("order_estimated_delivery_date", F.col("order_estimated_delivery_date").cast("timestamp"))
)

write_table(silver_orders, f"{SILVER}.orders")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. silver.order_items
# MAGIC Dedup key: (order_id, order_item_id). Cast price/freight to double, shipping_limit_date to timestamp.

# COMMAND ----------

bronze_order_items = spark.table(f"{BRONZE}.order_items")

silver_order_items = (
    bronze_order_items
    .dropDuplicates(["order_id", "order_item_id"])
    .withColumn("price", F.col("price").cast("double"))
    .withColumn("freight_value", F.col("freight_value").cast("double"))
    .withColumn("shipping_limit_date", F.col("shipping_limit_date").cast("timestamp"))
)

write_table(silver_order_items, f"{SILVER}.order_items")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3. silver.order_payments
# MAGIC Dedup key: (order_id, payment_sequential). Cast payment_value to double.

# COMMAND ----------

bronze_order_payments = spark.table(f"{BRONZE}.order_payments")

silver_order_payments = (
    bronze_order_payments
    .dropDuplicates(["order_id", "payment_sequential"])
    .withColumn("payment_value", F.col("payment_value").cast("double"))
)

write_table(silver_order_payments, f"{SILVER}.order_payments")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4. silver.order_reviews
# MAGIC Dedup rule (CONFIRMED - Option A): per order_id, keep the row with the
# MAGIC latest review_creation_date, tie-broken by latest review_answer_timestamp.

# COMMAND ----------

bronze_order_reviews = spark.table(f"{BRONZE}.order_reviews")

order_reviews_typed = (
    bronze_order_reviews
    .withColumn("review_creation_date", F.col("review_creation_date").cast("timestamp"))
    .withColumn("review_answer_timestamp", F.col("review_answer_timestamp").cast("timestamp"))
    .withColumn("review_score", F.col("review_score").cast("integer"))
)

review_dedup_window = Window.partitionBy("order_id").orderBy(
    F.col("review_creation_date").desc(), F.col("review_answer_timestamp").desc()
)

silver_order_reviews = (
    order_reviews_typed
    .withColumn("_rn", F.row_number().over(review_dedup_window))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

write_table(silver_order_reviews, f"{SILVER}.order_reviews")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5. silver.customers
# MAGIC Dedup key: customer_id. Zip prefix kept as string (leading zeros).

# COMMAND ----------

bronze_customers = spark.table(f"{BRONZE}.customers")

silver_customers = (
    bronze_customers
    .dropDuplicates(["customer_id"])
    .withColumn("customer_zip_code_prefix", F.col("customer_zip_code_prefix").cast("string"))
)

write_table(silver_customers, f"{SILVER}.customers")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6. silver.sellers
# MAGIC Dedup key: seller_id. Zip prefix kept as string (leading zeros).

# COMMAND ----------

bronze_sellers = spark.table(f"{BRONZE}.sellers")

silver_sellers = (
    bronze_sellers
    .dropDuplicates(["seller_id"])
    .withColumn("seller_zip_code_prefix", F.col("seller_zip_code_prefix").cast("string"))
)

write_table(silver_sellers, f"{SILVER}.sellers")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 7. silver.products
# MAGIC Left join category_translation for the English category name; drop the
# MAGIC Portuguese-only column; cast dimension/weight columns to double.

# COMMAND ----------

bronze_products = spark.table(f"{BRONZE}.products")
bronze_category_translation = spark.table(f"{BRONZE}.category_translation")

silver_products = (
    bronze_products
    .dropDuplicates(["product_id"])
    .join(bronze_category_translation, on="product_category_name", how="left")
    .drop("product_category_name")
    .withColumn("product_weight_g", F.col("product_weight_g").cast("double"))
    .withColumn("product_length_cm", F.col("product_length_cm").cast("double"))
    .withColumn("product_height_cm", F.col("product_height_cm").cast("double"))
    .withColumn("product_width_cm", F.col("product_width_cm").cast("double"))
)

write_table(silver_products, f"{SILVER}.products")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 8. silver.geolocation
# MAGIC Dedup rule (CONFIRMED): one row per geolocation_zip_code_prefix, using
# MAGIC average lat/lng and the mode (most frequent) city/state for that prefix.

# COMMAND ----------

bronze_geolocation = spark.table(f"{BRONZE}.geolocation")

geo_avg_latlng = bronze_geolocation.groupBy("geolocation_zip_code_prefix").agg(
    F.avg("geolocation_lat").alias("geolocation_lat"),
    F.avg("geolocation_lng").alias("geolocation_lng"),
)

city_mode_window = Window.partitionBy("geolocation_zip_code_prefix").orderBy(
    F.col("cnt").desc(), F.col("geolocation_city").asc()
)
geo_city_mode = (
    bronze_geolocation.groupBy("geolocation_zip_code_prefix", "geolocation_city")
    .agg(F.count(F.lit(1)).alias("cnt"))
    .withColumn("_rn", F.row_number().over(city_mode_window))
    .filter(F.col("_rn") == 1)
    .select("geolocation_zip_code_prefix", "geolocation_city")
)

state_mode_window = Window.partitionBy("geolocation_zip_code_prefix").orderBy(
    F.col("cnt").desc(), F.col("geolocation_state").asc()
)
geo_state_mode = (
    bronze_geolocation.groupBy("geolocation_zip_code_prefix", "geolocation_state")
    .agg(F.count(F.lit(1)).alias("cnt"))
    .withColumn("_rn", F.row_number().over(state_mode_window))
    .filter(F.col("_rn") == 1)
    .select("geolocation_zip_code_prefix", "geolocation_state")
)

silver_geolocation = (
    geo_avg_latlng
    .join(geo_city_mode, on="geolocation_zip_code_prefix", how="left")
    .join(geo_state_mode, on="geolocation_zip_code_prefix", how="left")
    .withColumn("geolocation_zip_code_prefix", F.col("geolocation_zip_code_prefix").cast("string"))
)

write_table(silver_geolocation, f"{SILVER}.geolocation")

# COMMAND ----------

# MAGIC %md
# MAGIC ## GOLD LAYER

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. gold.daily_sales_by_region
# MAGIC Grain: one row per (order_date, customer_state).

# COMMAND ----------

silver_orders_tbl = spark.table(f"{SILVER}.orders")
silver_order_items_tbl = spark.table(f"{SILVER}.order_items")
silver_customers_tbl = spark.table(f"{SILVER}.customers")

orders_with_date = silver_orders_tbl.withColumn(
    "order_date", F.to_date("order_purchase_timestamp")
)

daily_sales_base = (
    orders_with_date
    .join(silver_order_items_tbl, on="order_id", how="inner")
    .join(silver_customers_tbl, on="customer_id", how="inner")
)

gold_daily_sales_by_region = (
    daily_sales_base
    .groupBy("order_date", "customer_state")
    .agg(
        F.sum(F.col("price") + F.col("freight_value")).alias("revenue"),
        F.countDistinct("order_id").alias("order_count"),
    )
)

write_table(gold_daily_sales_by_region, f"{GOLD}.daily_sales_by_region")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. gold.seller_performance
# MAGIC Grain: one row per seller_id.

# COMMAND ----------

silver_sellers_tbl = spark.table(f"{SILVER}.sellers")
silver_order_reviews_tbl = spark.table(f"{SILVER}.order_reviews")

seller_revenue = silver_order_items_tbl.groupBy("seller_id").agg(
    F.sum(F.col("price") + F.col("freight_value")).alias("total_revenue"),
    F.countDistinct("order_id").alias("order_count"),
)

seller_orders_distinct = silver_order_items_tbl.select("seller_id", "order_id").distinct()

seller_review_scores = seller_orders_distinct.join(
    silver_order_reviews_tbl.select("order_id", "review_score"), on="order_id", how="left"
)

seller_avg_review = seller_review_scores.groupBy("seller_id").agg(
    F.avg("review_score").alias("avg_review_score")
)

gold_seller_performance = (
    seller_revenue
    .join(seller_avg_review, on="seller_id", how="left")
    .join(silver_sellers_tbl, on="seller_id", how="left")
)

write_table(gold_seller_performance, f"{GOLD}.seller_performance")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3. gold.delivery_sla
# MAGIC Grain: one row per delivered order_id. Orders never delivered are excluded.

# COMMAND ----------

gold_delivery_sla = (
    silver_orders_tbl
    .filter(F.col("order_delivered_customer_date").isNotNull())
    .withColumn("estimated_delivery_date", F.col("order_estimated_delivery_date"))
    .withColumn("actual_delivery_date", F.col("order_delivered_customer_date"))
    .withColumn(
        "delivery_delta_days",
        F.datediff(F.col("actual_delivery_date"), F.col("estimated_delivery_date")),
    )
    .withColumn(
        "on_time_flag",
        F.when(F.col("delivery_delta_days") <= 0, F.lit(1)).otherwise(F.lit(0)),
    )
    .select(
        "order_id",
        "estimated_delivery_date",
        "actual_delivery_date",
        "delivery_delta_days",
        "on_time_flag",
    )
)

write_table(gold_delivery_sla, f"{GOLD}.delivery_sla")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4. gold.customer_rfm
# MAGIC Grain: one row per customer_unique_id. Simple tertile-based RFM
# MAGIC segmentation (recency, frequency, monetary) - no scoring model beyond
# MAGIC ntile(3) per dimension.

# COMMAND ----------

orders_customers = silver_orders_tbl.join(
    silver_customers_tbl.select("customer_id", "customer_unique_id"),
    on="customer_id",
    how="inner",
)

max_order_date = orders_customers.agg(
    F.max("order_purchase_timestamp").alias("max_order_date")
).collect()[0]["max_order_date"]

customer_recency_frequency = (
    orders_customers.groupBy("customer_unique_id")
    .agg(
        F.max("order_purchase_timestamp").alias("last_order_timestamp"),
        F.countDistinct("order_id").alias("frequency"),
    )
    .withColumn(
        "recency_days",
        F.datediff(F.lit(max_order_date), F.col("last_order_timestamp")),
    )
)

customer_monetary = (
    orders_customers
    .join(silver_order_items_tbl, on="order_id", how="inner")
    .groupBy("customer_unique_id")
    .agg(F.sum(F.col("price") + F.col("freight_value")).alias("monetary"))
)

customer_rfm_base = customer_recency_frequency.join(
    customer_monetary, on="customer_unique_id", how="inner"
).select("customer_unique_id", "recency_days", "frequency", "monetary")

recency_window = Window.orderBy(F.col("recency_days").asc())
frequency_window = Window.orderBy(F.col("frequency").desc())
monetary_window = Window.orderBy(F.col("monetary").desc())

customer_rfm_scored = (
    customer_rfm_base
    .withColumn("recency_score", F.ntile(3).over(recency_window))
    .withColumn("frequency_score", F.ntile(3).over(frequency_window))
    .withColumn("monetary_score", F.ntile(3).over(monetary_window))
    .withColumn(
        "combined_score",
        F.col("recency_score") + F.col("frequency_score") + F.col("monetary_score"),
    )
    .withColumn(
        "rfm_segment",
        F.when(F.col("combined_score") <= 4, F.lit("High"))
        .when(F.col("combined_score") <= 6, F.lit("Medium"))
        .otherwise(F.lit("Low")),
    )
)

gold_customer_rfm = customer_rfm_scored.select(
    "customer_unique_id", "recency_days", "frequency", "monetary", "rfm_segment"
)

write_table(gold_customer_rfm, f"{GOLD}.customer_rfm")
