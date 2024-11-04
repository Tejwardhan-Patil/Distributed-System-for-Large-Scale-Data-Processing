import org.apache.spark.SparkConf
import org.apache.spark.streaming.{Seconds, StreamingContext}
import org.apache.spark.streaming.kafka010._
import org.apache.kafka.clients.consumer.ConsumerConfig
import org.apache.kafka.common.serialization.StringDeserializer
import org.apache.spark.streaming.dstream.DStream
import org.apache.spark.sql.{SQLContext, SparkSession}
import org.apache.spark.sql.functions._
import org.apache.spark.streaming.kafka010.LocationStrategies.PreferConsistent
import org.apache.spark.streaming.kafka010.ConsumerStrategies.Subscribe
import org.apache.log4j.{Level, Logger}

object StreamProcessing {

  def createStreamingContext(): StreamingContext = {

    // Create Spark Configuration
    val conf = new SparkConf().setAppName("RealTimeStreamProcessing").setMaster("local[*]")

    // Set log level to avoid too much logging
    Logger.getLogger("org").setLevel(Level.ERROR)

    // Create Streaming Context with a batch interval of 10 seconds
    val ssc = new StreamingContext(conf, Seconds(10))

    // Enable checkpointing for stateful operations
    ssc.checkpoint("hdfs://namenode:9000/stream_checkpoint")

    // Kafka parameters
    val kafkaParams = Map[String, Object](
      ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG -> "localhost:9092",
      ConsumerConfig.GROUP_ID_CONFIG -> "streaming_group",
      ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG -> classOf[StringDeserializer],
      ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG -> classOf[StringDeserializer]
    )

    // Subscribe to Kafka topic
    val topics = Array("streaming_topic")
    val stream = KafkaUtils.createDirectStream[String, String](
      ssc,
      PreferConsistent,
      Subscribe[String, String](topics, kafkaParams)
    )

    // Parse incoming stream data as (key, value)
    val parsedStream: DStream[(String, String)] = stream.map(record => (record.key, record.value))

    // Processing Pipeline
    processStream(parsedStream, ssc)

    // Return Streaming Context
    ssc
  }

  def processStream(stream: DStream[(String, String)], ssc: StreamingContext): Unit = {
    // Error handling for stream data
    val validStream = stream.filter { case (_, value) =>
      try {
        value != null && value.nonEmpty
      } catch {
        case e: Exception =>
          println(s"Error processing message: ${e.getMessage}")
          false
      }
    }

    // Data Transformation: Convert values to uppercase
    val transformedStream = validStream.map { case (key, value) =>
      (key, value.toUpperCase)
    }

    // Word Count with Windowing
    val wordCounts = transformedStream.flatMap { case (_, value) =>
      value.split(" ")
    }
    .map(word => (word, 1))
    .reduceByKeyAndWindow(_ + _, _ - _, Seconds(30), Seconds(10))

    // Log word counts for inspection
    wordCounts.foreachRDD { rdd =>
      rdd.collect().foreach { case (word, count) =>
        println(s"Word: $word, Count: $count")
      }
    }

    // Checkpoint stateful RDDs
    wordCounts.checkpoint(Seconds(30))

    // Sliding window computation (last 60 seconds of data, sliding every 20 seconds)
    val slidingWindowWordCounts = wordCounts.window(Seconds(60), Seconds(20))
    
    // SQL Transformation: Convert DStream to DataFrame and run SQL queries
    slidingWindowWordCounts.foreachRDD { rdd =>
      if (!rdd.isEmpty()) {
        val spark = SparkSession.builder.config(rdd.sparkContext.getConf).getOrCreate()
        import spark.implicits._

        // Convert RDD to DataFrame
        val wordCountDF = rdd.toDF("word", "count")

        // Register DataFrame as Temp Table
        wordCountDF.createOrReplaceTempView("words")

        // Run SQL Query to find top words
        val topWords = spark.sql("SELECT word, count FROM words WHERE count > 1 ORDER BY count DESC LIMIT 10")
        topWords.show() // Show top 10 words

        // Persist top words to external storage (HDFS)
        topWords.write.mode("append").parquet("hdfs://namenode:9000/stream_output/top_words")
      }
    }

    // Save full word counts to external storage (HDFS, S3)
    wordCounts.foreachRDD { rdd =>
      if (!rdd.isEmpty()) {
        rdd.saveAsTextFile("hdfs://namenode:9000/stream_output/word_counts")
      }
    }
  }

  def main(args: Array[String]): Unit = {

    // Create or retrieve Streaming Context with checkpointing
    val checkpointDirectory = "hdfs://namenode:9000/stream_checkpoint"
    val ssc = StreamingContext.getOrCreate(checkpointDirectory, createStreamingContext)

    // Start the Streaming Context
    ssc.start()

    // Await termination
    ssc.awaitTermination()
  }
}