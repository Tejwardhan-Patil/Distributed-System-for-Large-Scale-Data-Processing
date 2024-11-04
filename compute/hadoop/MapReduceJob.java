package compute.hadoop;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

import java.io.IOException;
import java.util.StringTokenizer;

// Main class for MapReduce job
public class MapReduceJob {

    public static class TokenizerMapper extends Mapper<LongWritable, Text, Text, IntWritable> {

        private final static IntWritable one = new IntWritable(1);
        private Text word = new Text();

        // Map function to tokenize input text
        public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            StringTokenizer itr = new StringTokenizer(value.toString());
            while (itr.hasMoreTokens()) {
                word.set(itr.nextToken());
                context.write(word, one);
            }
        }
    }

    public static class IntSumReducer extends Reducer<Text, IntWritable, Text, IntWritable> {

        private IntWritable result = new IntWritable();

        // Reduce function to aggregate word counts
        public void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
            int sum = 0;
            for (IntWritable val : values) {
                sum += val.get();
            }
            result.set(sum);
            context.write(key, result);
        }
    }

    // Method to set up and run the Hadoop job
    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "word count");

        job.setJarByClass(MapReduceJob.class);
        job.setMapperClass(TokenizerMapper.class);
        job.setCombinerClass(IntSumReducer.class);
        job.setReducerClass(IntSumReducer.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}

// Classes and utilities for complex processing

class FilterMapper extends Mapper<LongWritable, Text, Text, IntWritable> {

    private final static IntWritable one = new IntWritable(1);
    private Text filteredWord = new Text();

    // Map function to filter words by length
    public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
        String line = value.toString();
        for (String word : line.split("\\s+")) {
            if (word.length() > 5) { // Filter words longer than 5 characters
                filteredWord.set(word);
                context.write(filteredWord, one);
            }
        }
    }
}

class AverageReducer extends Reducer<Text, IntWritable, Text, IntWritable> {

    private IntWritable result = new IntWritable();

    // Reduce function to calculate average word length
    public void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
        int sum = 0;
        int count = 0;
        for (IntWritable val : values) {
            sum += val.get();
            count++;
        }
        if (count > 0) {
            result.set(sum / count);
            context.write(key, result);
        }
    }
}

class CompositeKeyMapper extends Mapper<LongWritable, Text, CompositeKey, IntWritable> {

    private final static IntWritable one = new IntWritable(1);

    // Map function with custom composite key
    public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
        String[] fields = value.toString().split(",");
        if (fields.length > 2) {
            CompositeKey compositeKey = new CompositeKey(fields[0], fields[1]); // Using first two fields as composite key
            context.write(compositeKey, one);
        }
    }
}

class CompositeKeyReducer extends Reducer<CompositeKey, IntWritable, CompositeKey, IntWritable> {

    private IntWritable result = new IntWritable();

    // Reduce function for composite key aggregation
    public void reduce(CompositeKey key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
        int sum = 0;
        for (IntWritable val : values) {
            sum += val.get();
        }
        result.set(sum);
        context.write(key, result);
    }
}

// CompositeKey class for custom key type
class CompositeKey implements WritableComparable<CompositeKey> {

    private String keyPart1;
    private String keyPart2;

    public CompositeKey() {}

    public CompositeKey(String keyPart1, String keyPart2) {
        this.keyPart1 = keyPart1;
        this.keyPart2 = keyPart2;
    }

    public void write(DataOutput out) throws IOException {
        out.writeUTF(keyPart1);
        out.writeUTF(keyPart2);
    }

    public void readFields(DataInput in) throws IOException {
        keyPart1 = in.readUTF();
        keyPart2 = in.readUTF();
    }

    public int compareTo(CompositeKey o) {
        int result = keyPart1.compareTo(o.keyPart1);
        if (result == 0) {
            result = keyPart2.compareTo(o.keyPart2);
        }
        return result;
    }

    @Override
    public String toString() {
        return keyPart1 + "," + keyPart2;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;

        CompositeKey that = (CompositeKey) o;

        if (!keyPart1.equals(that.keyPart1)) return false;
        return keyPart2.equals(that.keyPart2);
    }

    @Override
    public int hashCode() {
        int result = keyPart1.hashCode();
        result = 31 * result + keyPart2.hashCode();
        return result;
    }
}