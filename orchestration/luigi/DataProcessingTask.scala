import luigi.{ExternalTask, LocalTarget, Task}
import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.functions._
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

// Task for handling preprocessing of data
class DataPreprocessingTask(inputPath: String, outputPath: String) extends Task {

  // Output target where the task results will be stored
  override def output(): LocalTarget = new LocalTarget(outputPath)

  // Preprocessing logic
  override def run(): Unit = {
    val spark = SparkSession.builder()
      .appName("DataPreprocessingTask")
      .master("yarn")
      .config("spark.sql.shuffle.partitions", "50")
      .getOrCreate()

    try {
      // Load input data
      val rawData: DataFrame = loadData(spark, inputPath)

      // Clean the data
      val cleanedData: DataFrame = cleanData(rawData)

      // Save cleaned data
      saveData(cleanedData, outputPath)

    } finally {
      spark.stop()
    }
  }

  def loadData(spark: SparkSession, path: String): DataFrame = {
    spark.read
      .option("header", "true")
      .option("inferSchema", "true")
      .csv(path)
  }

  def cleanData(df: DataFrame): DataFrame = {
    df.filter(col("value").isNotNull) // Filter null values
      .dropDuplicates("id")           // Drop duplicates based on the unique ID
  }

  def saveData(df: DataFrame, path: String): Unit = {
    df.write
      .mode("overwrite")
      .option("header", "true")
      .csv(path)
  }
}

// Task for handling transformation logic
class DataTransformationTask(inputPath: String, outputPath: String) extends Task {

  // Output target where the task results will be stored
  override def output(): LocalTarget = new LocalTarget(outputPath)

  // Transformation logic
  override def run(): Unit = {
    val spark = SparkSession.builder()
      .appName("DataTransformationTask")
      .master("yarn")
      .config("spark.sql.shuffle.partitions", "50")
      .getOrCreate()

    try {
      // Load preprocessed data
      val preprocessedData: DataFrame = loadData(spark, inputPath)

      // Transform the data
      val transformedData: DataFrame = transformData(preprocessedData)

      // Save transformed data
      saveData(transformedData, outputPath)

    } finally {
      spark.stop()
    }
  }

  def loadData(spark: SparkSession, path: String): DataFrame = {
    spark.read
      .option("header", "true")
      .option("inferSchema", "true")
      .csv(path)
  }

  def transformData(df: DataFrame): DataFrame = {
    df.withColumn("transformed_value", col("value") * 2) // Transformation logic
      .withColumn("transformed_date", current_date())     // Add transformation date
  }

  def saveData(df: DataFrame, path: String): Unit = {
    df.write
      .mode("overwrite")
      .option("header", "true")
      .csv(path)
  }
}

// Final Task for Aggregation
class DataAggregationTask(inputPath: String, outputPath: String) extends Task {

  // Output target for storing aggregated results
  override def output(): LocalTarget = new LocalTarget(outputPath)

  override def run(): Unit = {
    val spark = SparkSession.builder()
      .appName("DataAggregationTask")
      .master("yarn")
      .config("spark.sql.shuffle.partitions", "50")
      .getOrCreate()

    try {
      // Load transformed data
      val transformedData: DataFrame = loadData(spark, inputPath)

      // Perform aggregation
      val aggregatedData: DataFrame = aggregateData(transformedData)

      // Save aggregated data
      saveData(aggregatedData, outputPath)

    } finally {
      spark.stop()
    }
  }

  def loadData(spark: SparkSession, path: String): DataFrame = {
    spark.read
      .option("header", "true")
      .option("inferSchema", "true")
      .csv(path)
  }

  def aggregateData(df: DataFrame): DataFrame = {
    df.groupBy("category") // Aggregating by category
      .agg(
        count("id").as("count"),
        sum("transformed_value").as("total_value")
      )
      .withColumn("aggregation_date", current_date()) // Add aggregation date
  }

  def saveData(df: DataFrame, path: String): Unit = {
    df.write
      .mode("overwrite")
      .option("header", "true")
      .csv(path)
  }
}

// ExternalTask defining dependencies on external datasets
class ExternalDataSourceTask extends ExternalTask {
  override def output(): LocalTarget = new LocalTarget("hdfs://namenode:8020/user/data/external/input")
}

// Orchestrating the full data pipeline
class FullDataProcessingPipeline extends Task {

  // Output target for the final step of the pipeline
  override def output(): LocalTarget = new LocalTarget("hdfs://namenode:8020/user/data/final/output")

  // Define task dependencies
  override def requires(): Seq[Task] = {
    Seq(
      new DataPreprocessingTask("hdfs://namenode:8020/user/data/raw", "hdfs://namenode:8020/user/data/clean"),
      new DataTransformationTask("hdfs://namenode:8020/user/data/clean", "hdfs://namenode:8020/user/data/transformed"),
      new DataAggregationTask("hdfs://namenode:8020/user/data/transformed", "hdfs://namenode:8020/user/data/aggregated")
    )
  }

  // Task logic for final stage
  override def run(): Unit = {
    val spark = SparkSession.builder()
      .appName("FullDataProcessingPipeline")
      .master("yarn")
      .config("spark.sql.shuffle.partitions", "50")
      .getOrCreate()

    try {
      // Load the final aggregated data
      val finalData: DataFrame = loadData(spark, "hdfs://namenode:8020/user/data/aggregated")

      // Further processing or analytics
      val analyzedData: DataFrame = analyzeData(finalData)

      // Save final result
      saveData(analyzedData, "hdfs://namenode:8020/user/data/final/output")

    } finally {
      spark.stop()
    }
  }

  def loadData(spark: SparkSession, path: String): DataFrame = {
    spark.read
      .option("header", "true")
      .option("inferSchema", "true")
      .csv(path)
  }

  def analyzeData(df: DataFrame): DataFrame = {
    // Analytics logic
    df.withColumn("analyzed_value", col("total_value") / col("count"))
      .withColumn("analysis_timestamp", lit(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))))
  }

  def saveData(df: DataFrame, path: String): Unit = {
    df.write
      .mode("overwrite")
      .option("header", "true")
      .csv(path)
  }
}

// Main entry point for running the workflow
object DataProcessingOrchestrator {
  def main(args: Array[String]): Unit = {
    val task = new FullDataProcessingPipeline()
    luigi.build(task)
  }
}