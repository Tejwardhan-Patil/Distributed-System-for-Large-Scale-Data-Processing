package com.website.data_ingestion.preprocessing

import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._

object DataTransformation {

  // Entry point for the transformation job
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder()
      .appName("DataTransformation")
      .getOrCreate()

    // Read input data 
    val inputPath = args(0)
    val transformedData = transformData(spark, inputPath)

    // Write the transformed data to output
    val outputPath = args(1)
    writeData(transformedData, outputPath)

    spark.stop()
  }

  // Function to read data from a source
  def readData(spark: SparkSession, path: String): DataFrame = {
    spark.read
      .option("header", "true")
      .csv(path) 
  }

  // Function to write data to a destination
  def writeData(data: DataFrame, path: String): Unit = {
    data.write
      .mode("overwrite")
      .parquet(path) 
  }

  // Transformation function to apply various data operations
  def transformData(spark: SparkSession, inputPath: String): DataFrame = {
    val rawData = readData(spark, inputPath)

    // Define transformations
    val cleanedData = cleanData(rawData)
    val normalizedData = normalizeData(cleanedData)
    val enrichedData = enrichData(normalizedData)
    val finalData = aggregateData(enrichedData)

    finalData
  }

  // Function to clean data by handling missing values and invalid records
  def cleanData(df: DataFrame): DataFrame = {
    df.filter("value IS NOT NULL") 
      .na.fill("Unknown", Seq("category")) 
      .filter(row => row.getAs[String]("status").matches("valid|verified")) 
  }

  // Function to normalize data by applying consistent formats
  def normalizeData(df: DataFrame): DataFrame = {
    df.withColumn("date", to_date(col("date"), "yyyy-MM-dd"))
      .withColumn("amount", col("amount").cast(DoubleType)) 
      .withColumn("name", initcap(col("name"))) 
      .withColumn("country", upper(col("country")))
  }

  // Function to enrich data by adding derived columns
  def enrichData(df: DataFrame): DataFrame = {
    df.withColumn("year", year(col("date")))
      .withColumn("month", month(col("date")))
      .withColumn("day", dayofmonth(col("date")))
      .withColumn("category_group", categorize(col("category")))
  }

  // Function to aggregate data based on some criteria
  def aggregateData(df: DataFrame): DataFrame = {
    df.groupBy("year", "category_group")
      .agg(
        count("id").as("transaction_count"),
        sum("amount").as("total_amount"),
        avg("amount").as("average_amount")
      )
      .orderBy("year", "category_group")
  }

  // Custom UDF for categorizing data
  def categorize = udf((category: String) => category match {
    case "Electronics" | "Appliances" => "Tech"
    case "Books" | "Magazines" => "Reading"
    case "Clothes" | "Shoes" => "Fashion"
    case _ => "Others"
  })

  // Function to validate the data schema
  def validateSchema(df: DataFrame): Boolean = {
    val expectedSchema = StructType(Seq(
      StructField("id", StringType, nullable = false),
      StructField("name", StringType, nullable = true),
      StructField("amount", DoubleType, nullable = true),
      StructField("date", StringType, nullable = true),
      StructField("category", StringType, nullable = true),
      StructField("status", StringType, nullable = true),
      StructField("country", StringType, nullable = true)
    ))

    df.schema == expectedSchema
  }

  // Function to apply custom business rules
  def applyBusinessRules(df: DataFrame): DataFrame = {
    df.filter(col("amount") > 100) 
  }

  // Function to detect and remove duplicate records
  def removeDuplicates(df: DataFrame): DataFrame = {
    df.dropDuplicates("id")
  }

  // Function to handle outliers in the data
  def handleOutliers(df: DataFrame): DataFrame = {
    val quantiles = df.stat.approxQuantile("amount", Array(0.25, 0.75), 0.0)
    val lowerBound = quantiles(0) - 1.5 * (quantiles(1) - quantiles(0))
    val upperBound = quantiles(1) + 1.5 * (quantiles(1) - quantiles(0))

    df.filter(col("amount").between(lowerBound, upperBound))
  }

  // Function to log data transformation stats
  def logTransformationStats(df: DataFrame): Unit = {
    val recordCount = df.count()
    val transactionSum = df.agg(sum("amount")).first().getDouble(0)

    println(s"Total records: $recordCount")
    println(s"Total transaction amount: $transactionSum")
  }

  // Function to anonymize sensitive data
  def anonymizeData(df: DataFrame): DataFrame = {
    df.withColumn("name", lit("REDACTED"))
  }

  // Function to validate business rules
  def validateBusinessRules(df: DataFrame): Boolean = {
    val invalidRecords = df.filter("amount <= 100").count()
    invalidRecords == 0
  }
  
  // Function to handle schema evolution
  def handleSchemaEvolution(df: DataFrame): DataFrame = {
    df.withColumnRenamed("old_column", "new_column")
  }

  // Function to monitor and report transformation progress
  def reportProgress(stage: String): Unit = {
    println(s"Transformation progress: $stage completed.")
  }
}