import org.apache.spark.sql.{SparkSession, DataFrame, Row}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._
import org.apache.spark.sql.expressions.Window
import org.apache.log4j.{Level, Logger}

object BatchProcessing {

  // Set log level to warn to reduce noise in the console output
  Logger.getLogger("org").setLevel(Level.WARN)

  def main(args: Array[String]): Unit = {

    // Initialize Spark Session
    val spark = SparkSession.builder
      .appName("BatchProcessingJob")
      .config("spark.master", "local[*]")  
      .getOrCreate()

    // Read configuration parameters (input/output paths)
    val inputPath1 = "hdfs://namenode:9000/input/data1"
    val inputPath2 = "hdfs://namenode:9000/input/data2"
    val outputPath = "hdfs://namenode:9000/output/processed_data"
    val s3OutputPath = "s3a://bucket/output/processed_data"

    // Schema definition for input data1
    val schema1 = new StructType()
      .add("id", IntegerType, nullable = true)
      .add("timestamp", StringType, nullable = true)
      .add("value", DoubleType, nullable = true)

    // Schema definition for input data2
    val schema2 = new StructType()
      .add("id", IntegerType, nullable = true)
      .add("category", StringType, nullable = true)

    // Read datasets from HDFS
    val data1 = loadData(spark, inputPath1, schema1)
    val data2 = loadData(spark, inputPath2, schema2)

    // Perform data transformations and aggregations
    val transformedData = processAndJoinData(data1, data2)

    // Save the transformed data back to HDFS and S3
    saveData(transformedData, outputPath)
    saveData(transformedData, s3OutputPath)

    // Stop the Spark session
    spark.stop()
  }

  def loadData(spark: SparkSession, path: String, schema: StructType): DataFrame = {
    // Read data in CSV format, handle null values
    spark.read
      .option("header", "true")
      .schema(schema)
      .csv(path)
      .na.fill(0.0) // Fill missing numerical values with 0
      .na.fill("unknown") // Fill missing categorical values with "unknown"
  }

  def processAndJoinData(data1: DataFrame, data2: DataFrame): DataFrame = {

    // Convert timestamp to date format and filter rows based on some condition
    val filteredData = data1
      .withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
      .filter(col("value") > 0.0)

    // Create a window for calculating running totals
    val windowSpec = Window.partitionBy("id").orderBy("timestamp")

    // Calculate running sum and row number
    val withRunningSum = filteredData
      .withColumn("running_sum", sum("value").over(windowSpec))
      .withColumn("row_number", row_number().over(windowSpec))

    // Join with the second dataset based on "id" column
    val joinedData = withRunningSum
      .join(data2, Seq("id"), "left_outer") // Left join to preserve all rows from data1

    // Add a new column using a custom UDF to categorize the values
    val categorizedData = joinedData.withColumn("value_category", categorizeValue(col("value")))

    // Perform aggregation by category and date
    val aggregatedData = categorizedData
      .groupBy(window(col("timestamp"), "1 day"), col("category"))
      .agg(
        avg("value").as("avg_value"),
        max("running_sum").as("max_running_sum")
      )

    // Transformation: adding a new column with the current processing time
    val transformedData = aggregatedData
      .withColumn("processing_time", current_timestamp())

    transformedData
  }

  // Define a custom UDF to categorize the value
  def categorizeValue = udf((value: Double) => {
    if (value > 100) "High"
    else if (value > 50) "Medium"
    else "Low"
  })

  def saveData(data: DataFrame, path: String): Unit = {
    // Save data in Parquet format with partitioning by date
    data.write
      .mode("overwrite")
      .partitionBy("window")
      .parquet(path)
  }

  def logStatistics(data: DataFrame): Unit = {
    // Log some statistics about the DataFrame
    println(s"DataFrame has ${data.count()} rows")
    data.describe("value").show()
  }

  def validateData(data: DataFrame): Boolean = {
    // Validate data (checking for nulls or negative values)
    val invalidRows = data.filter(col("value") < 0).count()
    if (invalidRows > 0) {
      println(s"Data contains $invalidRows invalid rows with negative values")
      false
    } else {
      true
    }
  }
}

// Helper functions
object Helpers {

  def convertToJSON(df: DataFrame): String = {
    // Convert DataFrame to JSON string
    import org.apache.spark.sql.functions.{to_json, struct}
    df.withColumn("json", to_json(struct(df.columns.map(col): _*)))
      .select("json")
      .collect()
      .map(_.getString(0))
      .mkString("\n")
  }

  def saveMetrics(df: DataFrame, outputPath: String): Unit = {
    // Save metrics (like avg, min, max values) to an external system or file
    val metrics = df.describe("value")
    metrics.write.mode("overwrite").csv(outputPath)
  }

  def enrichDataWithLookup(df: DataFrame, lookupTable: DataFrame): DataFrame = {
    // Enrich the original DataFrame by joining with a lookup table
    df.join(lookupTable, Seq("id"), "left_outer")
  }
}

// UDF
object UDFs {
  
  def cleanString = udf((str: String) => {
    str.trim.toLowerCase.replaceAll("[^a-zA-Z0-9]", "_")
  })
  
  def createUniqueId = udf((id: Int, timestamp: String) => {
    s"$id-${timestamp.replaceAll("[-: ]", "")}"
  })
}