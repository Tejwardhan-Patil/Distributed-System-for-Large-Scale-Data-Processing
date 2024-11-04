package ingestion_pipelines

import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.functions._
import org.apache.hadoop.fs.{FileSystem, Path}
import org.apache.spark.sql.types._
import java.io.File
import scala.util.{Failure, Success, Try}
import org.yaml.snakeyaml.Yaml
import java.io.FileInputStream

object BatchIngestion {

  case class IngestionConfig(
    inputPath: String,
    outputPath: String,
    checkpointPath: String,
    format: String,
    repartition: Int
  )

  def main(args: Array[String]): Unit = {

    val spark = SparkSession.builder()
      .appName("Batch Ingestion Pipeline")
      .config("spark.master", "local[*]")
      .getOrCreate()

    val configPath = args(0)
    val config = loadConfig(configPath)

    config match {
      case Success(conf) =>
        runBatchIngestion(spark, conf)
      case Failure(ex) =>
        println(s"Failed to load configuration: ${ex.getMessage}")
        System.exit(1)
    }
  }

  def loadConfig(configPath: String): Try[IngestionConfig] = Try {
    val yaml = new Yaml()
    val input = new FileInputStream(new File(configPath))
    val configMap = yaml.load(input).asInstanceOf[java.util.Map[String, Object]]
    
    IngestionConfig(
      inputPath = configMap.get("inputPath").toString,
      outputPath = configMap.get("outputPath").toString,
      checkpointPath = configMap.get("checkpointPath").toString,
      format = configMap.get("format").toString,
      repartition = configMap.get("repartition").toString.toInt
    )
  }

  def runBatchIngestion(spark: SparkSession, config: IngestionConfig): Unit = {
    val inputData = loadInputData(spark, config.inputPath, config.format)

    val transformedData = processData(inputData)

    writeData(transformedData, config)

    validateOutput(config.outputPath, spark)
  }

  def loadInputData(spark: SparkSession, path: String, format: String): DataFrame = {
    spark.read
      .format(format)
      .load(path)
  }

  def processData(df: DataFrame): DataFrame = {
    df.withColumn("ingestion_timestamp", current_timestamp())
      .filter(col("isValid") === true)
      .select("id", "name", "value", "ingestion_timestamp")
  }

  def writeData(df: DataFrame, config: IngestionConfig): Unit = {
    df.repartition(config.repartition)
      .write
      .mode("overwrite")
      .format(config.format)
      .save(config.outputPath)
  }

  def validateOutput(outputPath: String, spark: SparkSession): Unit = {
    val fs = FileSystem.get(spark.sparkContext.hadoopConfiguration)
    if (fs.exists(new Path(outputPath))) {
      println(s"Data successfully written to $outputPath")
    } else {
      throw new Exception(s"Data write failed to $outputPath")
    }
  }

  def checkDirectory(path: String, spark: SparkSession): Boolean = {
    val fs = FileSystem.get(spark.sparkContext.hadoopConfiguration)
    fs.exists(new Path(path))
  }

  def moveToCheckpoint(fs: FileSystem, checkpointDir: String, outputDir: String): Unit = {
    if (fs.exists(new Path(outputDir))) {
      val timestamp = System.currentTimeMillis()
      val checkpointPath = new Path(s"$checkpointDir/checkpoint_$timestamp")
      fs.rename(new Path(outputDir), checkpointPath)
    } else {
      throw new Exception(s"Output directory $outputDir not found.")
    }
  }

  def clearOldCheckpoint(fs: FileSystem, checkpointDir: String, retentionPeriod: Int): Unit = {
    val checkpointPath = new Path(checkpointDir)
    if (fs.exists(checkpointPath)) {
      val files = fs.listStatus(checkpointPath)
      files.foreach { fileStatus =>
        val age = System.currentTimeMillis() - fileStatus.getModificationTime
        if (age > retentionPeriod) {
          fs.delete(fileStatus.getPath, true)
        }
      }
    }
  }

  def logErrors(df: DataFrame, errorPath: String): Unit = {
    val errorDF = df.filter(col("isValid") === false)
    errorDF.write.mode("overwrite").json(errorPath)
  }

  def handleErrors(inputPath: String, errorPath: String, fs: FileSystem): Unit = {
    if (fs.exists(new Path(inputPath))) {
      fs.copyToLocalFile(new Path(inputPath), new Path(errorPath))
    } else {
      println(s"No errors found at $inputPath")
    }
  }

  def archiveData(outputPath: String, archivePath: String, fs: FileSystem): Unit = {
    if (fs.exists(new Path(outputPath))) {
      fs.rename(new Path(outputPath), new Path(archivePath))
      println(s"Data archived to $archivePath")
    } else {
      throw new Exception(s"Output directory $outputPath does not exist")
    }
  }

  def compressOutput(outputPath: String, spark: SparkSession): Unit = {
    val df = spark.read.format("parquet").load(outputPath)
    df.repartition(1)
      .write
      .mode("overwrite")
      .option("compression", "gzip")
      .parquet(outputPath)
  }

  def reportMetrics(spark: SparkSession, outputPath: String): Unit = {
    val df = spark.read.format("parquet").load(outputPath)
    val recordCount = df.count()
    println(s"Total records ingested: $recordCount")
  }

  def applyDataQualityChecks(df: DataFrame): DataFrame = {
    val checks = Seq(
      df.filter(col("value").isNotNull),
      df.filter(length(col("name")) > 0)
    )
    checks.reduce(_ intersect _)
  }
  
  def notifySuccess(outputPath: String): Unit = {
    println(s"Batch ingestion successful for data at $outputPath")
  }

  def sendFailureAlert(errorPath: String): Unit = {
    println(s"Batch ingestion failed. Errors logged at $errorPath")
  }

  def monitorJobExecution(config: IngestionConfig): Unit = {
    println(s"Monitoring batch job for input: ${config.inputPath}")
    
    // Create Prometheus metrics
    val registry = new CollectorRegistry()
    
    // Counter to track the number of successful batch ingestions
    val ingestionSuccessCounter = Counter.build()
        .name("batch_ingestion_success_total")
        .help("Total number of successful batch ingestions")
        .register(registry)
    
    // Counter to track the number of failed batch ingestions
    val ingestionFailureCounter = Counter.build()
        .name("batch_ingestion_failure_total")
        .help("Total number of failed batch ingestions")
        .register(registry)
    
    // Gauge to monitor the duration of the batch job
    val ingestionDurationGauge = Gauge.build()
        .name("batch_ingestion_duration_seconds")
        .help("Time taken to complete the batch ingestion in seconds")
        .register(registry)
    
    // Start Prometheus HTTP server on port 9091 to expose metrics
    val server = new HTTPServer(9091)

    // Usage
    try {
        val startTime = System.nanoTime()
        
        // Simulate batch ingestion process
        println("Running batch ingestion...")
        Thread.sleep(2000) 
        
        // Ingestion success
        ingestionSuccessCounter.inc()
        println("Batch ingestion successful.")
        
        val duration = (System.nanoTime() - startTime) / 1e9
        ingestionDurationGauge.set(duration)
        println(s"Batch ingestion took $duration seconds.")

    } catch {
        case ex: Exception =>
        ingestionFailureCounter.inc()
        println(s"Batch ingestion failed: ${ex.getMessage}")
    }
  }

}