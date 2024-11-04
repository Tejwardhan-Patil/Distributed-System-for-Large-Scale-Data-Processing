package compute.tests

import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._
import org.apache.spark.sql.streaming.OutputMode
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.apache.spark.sql.types._

class TestSparkJobs extends AnyFunSuite with BeforeAndAfterAll {

  var spark: SparkSession = _

  override def beforeAll(): Unit = {
    spark = SparkSession.builder()
      .appName("Test Spark Jobs")
      .master("local[*]")
      .getOrCreate()
  }

  override def afterAll(): Unit = {
    if (spark != null) {
      spark.stop()
    }
  }

  test("Batch Processing Job - Verify Data Transformation") {
    val data = Seq(
      ("Nate", 29),
      ("Paul", 35),
      ("Max", 28),
      ("David", 45)
    )

    val schema = new StructType()
      .add("name", StringType)
      .add("age", IntegerType)

    val df = spark.createDataFrame(
      spark.sparkContext.parallelize(data.map(Row.fromTuple)),
      schema
    )

    val transformedDf = df.withColumn("age_group", when(col("age") >= 30, "Senior").otherwise("Junior"))

    val expectedData = Seq(
      ("Nate", 29, "Junior"),
      ("Paul", 35, "Senior"),
      ("Max", 28, "Junior"),
      ("David", 45, "Senior")
    )

    val expectedDf = spark.createDataFrame(
      spark.sparkContext.parallelize(expectedData.map(Row.fromTuple)),
      new StructType()
        .add("name", StringType)
        .add("age", IntegerType)
        .add("age_group", StringType)
    )

    assert(transformedDf.collect() === expectedDf.collect())
  }

  test("Batch Processing Job - Check Aggregation") {
    val data = Seq(
      ("Nate", 1000),
      ("Paul", 500),
      ("Nate", 200),
      ("Paul", 300),
      ("Max", 800)
    )

    val df = spark.createDataFrame(
      spark.sparkContext.parallelize(data.map(Row.fromTuple)),
      new StructType()
        .add("name", StringType)
        .add("amount", IntegerType)
    )

    val aggDf = df.groupBy("name").agg(sum("amount").as("total_amount"))

    val expectedData = Seq(
      ("Nate", 1200),
      ("Paul", 800),
      ("Max", 800)
    )

    val expectedDf = spark.createDataFrame(
      spark.sparkContext.parallelize(expectedData.map(Row.fromTuple)),
      new StructType()
        .add("name", StringType)
        .add("total_amount", IntegerType)
    )

    assert(aggDf.collect() === expectedDf.collect())
  }

  test("Streaming Job - Validate Streaming Data Processing") {
    val data = Seq(
      ("Nate", "2024-06-15 12:00:00", 20),
      ("Paul", "2024-06-15 12:06:00", 15),
      ("Max", "2024-06-15 12:10:00", 25)
    )

    val schema = new StructType()
      .add("name", StringType)
      .add("timestamp", StringType)
      .add("score", IntegerType)

    val inputDf = spark.createDataFrame(
      spark.sparkContext.parallelize(data.map(Row.fromTuple)),
      schema
    )

    val streamingDf = inputDf
      .withColumn("timestamp", to_timestamp(col("timestamp")))

    val query = streamingDf.writeStream
      .format("memory")
      .queryName("testTable")
      .outputMode(OutputMode.Append())
      .start()

    query.processAllAvailable()

    val resultDf = spark.sql("select * from testTable")
    assert(resultDf.count() == 3)

    query.stop()
  }

  test("Streaming Job - Check Sliding Window Aggregation") {
    val data = Seq(
      ("Nate", "2024-06-15 12:00:00", 20),
      ("Paul", "2024-06-15 12:05:00", 15),
      ("Nate", "2024-06-15 12:10:00", 30),
      ("Paul", "2024-06-15 12:15:00", 25)
    )

    val schema = new StructType()
      .add("name", StringType)
      .add("timestamp", StringType)
      .add("score", IntegerType)

    val inputDf = spark.createDataFrame(
      spark.sparkContext.parallelize(data.map(Row.fromTuple)),
      schema
    ).withColumn("timestamp", to_timestamp(col("timestamp")))

    val windowedDf = inputDf
      .groupBy(window(col("timestamp"), "10 minutes"), col("name"))
      .agg(sum("score").as("total_score"))

    val query = windowedDf.writeStream
      .format("memory")
      .queryName("windowedTable")
      .outputMode(OutputMode.Complete())
      .start()

    query.processAllAvailable()

    val resultDf = spark.sql("select * from windowedTable")
    assert(resultDf.count() > 0)

    query.stop()
  }

  test("Batch Processing Job - Data Join Operation") {
    val data1 = Seq(
      ("Nate", 1),
      ("Paul", 2),
      ("Max", 3)
    )

    val data2 = Seq(
      (1, "New York"),
      (2, "San Francisco"),
      (3, "Chicago")
    )

    val df1 = spark.createDataFrame(
      spark.sparkContext.parallelize(data1.map(Row.fromTuple)),
      new StructType()
        .add("name", StringType)
        .add("id", IntegerType)
    )

    val df2 = spark.createDataFrame(
      spark.sparkContext.parallelize(data2.map(Row.fromTuple)),
      new StructType()
        .add("id", IntegerType)
        .add("city", StringType)
    )

    val joinedDf = df1.join(df2, "id")

    val expectedData = Seq(
      ("Nate", 1, "New York"),
      ("Paul", 2, "San Francisco"),
      ("Max", 3, "Chicago")
    )

    val expectedDf = spark.createDataFrame(
      spark.sparkContext.parallelize(expectedData.map(Row.fromTuple)),
      new StructType()
        .add("name", StringType)
        .add("id", IntegerType)
        .add("city", StringType)
    )

    assert(joinedDf.collect() === expectedDf.collect())
  }

  test("Batch Processing Job - Validate Null Handling") {
    val data = Seq(
      ("Nate", Some(1)),
      ("Paul", None),
      ("Max", Some(3))
    )

    val df = spark.createDataFrame(
      spark.sparkContext.parallelize(data.map {
        case (name, id) => Row(name, id.getOrElse(null))
      }),
      new StructType()
        .add("name", StringType)
        .add("id", IntegerType)
    )

    val nonNullDf = df.na.fill(Map("id" -> 0))

    val expectedData = Seq(
      ("Nate", 1),
      ("Paul", 0),
      ("Max", 3)
    )

    val expectedDf = spark.createDataFrame(
      spark.sparkContext.parallelize(expectedData.map(Row.fromTuple)),
      new StructType()
        .add("name", StringType)
        .add("id", IntegerType)
    )

    assert(nonNullDf.collect() === expectedDf.collect())
  }

}