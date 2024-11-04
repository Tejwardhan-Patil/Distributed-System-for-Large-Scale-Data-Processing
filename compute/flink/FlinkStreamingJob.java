package compute.flink;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.java.utils.ParameterTool;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer;
import org.apache.flink.util.Collector;
import java.time.Duration;
import java.util.Properties;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.api.common.functions.ReduceFunction;
import org.apache.flink.api.java.tuple.Tuple2;

public class FlinkStreamingJob {

    public static void main(String[] args) throws Exception {
        // Set up the streaming execution environment
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Load configuration parameters
        ParameterTool parameters = ParameterTool.fromArgs(args);
        String kafkaSourceTopic = parameters.get("input-topic", "inputTopic");
        String kafkaSinkTopic = parameters.get("output-topic", "outputTopic");
        String kafkaBootstrapServers = parameters.get("bootstrap.servers", "localhost:9092");

        // Set Kafka properties
        Properties kafkaProperties = new Properties();
        kafkaProperties.setProperty("bootstrap.servers", kafkaBootstrapServers);
        kafkaProperties.setProperty("group.id", "flink_group");

        // Define Kafka consumer
        FlinkKafkaConsumer<String> kafkaSource = new FlinkKafkaConsumer<>(
            kafkaSourceTopic,
            new SimpleStringSchema(),
            kafkaProperties
        );

        kafkaSource.setStartFromEarliest();

        // Define Kafka producer
        FlinkKafkaProducer<String> kafkaSink = new FlinkKafkaProducer<>(
            kafkaSinkTopic,
            new SimpleStringSchema(),
            kafkaProperties
        );

        // Define the stream processing logic
        DataStream<String> inputStream = env
            .addSource(kafkaSource)
            .name("Kafka Source")
            .assignTimestampsAndWatermarks(
                WatermarkStrategy
                    .forBoundedOutOfOrderness(Duration.ofSeconds(5))
                    .withIdleness(Duration.ofMinutes(1))
            );

        // Transform the input stream by tokenizing it and calculating word counts
        DataStream<Tuple2<String, Integer>> wordCounts = inputStream
            .flatMap(new Tokenizer())
            .keyBy(value -> value.f0)
            .reduce(new WordCountReducer());

        // Transform the result into a string and write it to the Kafka sink
        wordCounts
            .map(new MapFunction<Tuple2<String, Integer>, String>() {
                @Override
                public String map(Tuple2<String, Integer> value) {
                    return value.f0 + ": " + value.f1;
                }
            })
            .addSink(kafkaSink)
            .name("Kafka Sink");

        // Execute the Flink job
        env.execute("Flink Streaming WordCount");
    }

    /**
     * Tokenizer function to split lines of input into words.
     */
    public static final class Tokenizer implements FlatMapFunction<String, Tuple2<String, Integer>> {
        @Override
        public void flatMap(String value, Collector<Tuple2<String, Integer>> out) {
            String[] tokens = value.toLowerCase().split("\\W+");
            for (String token : tokens) {
                if (token.length() > 0) {
                    out.collect(new Tuple2<>(token, 1));
                }
            }
        }
    }

    /**
     * Reducer function that sums the word counts.
     */
    public static final class WordCountReducer implements ReduceFunction<Tuple2<String, Integer>> {
        @Override
        public Tuple2<String, Integer> reduce(Tuple2<String, Integer> value1, Tuple2<String, Integer> value2) {
            return new Tuple2<>(value1.f0, value1.f1 + value2.f1);
        }
    }
}