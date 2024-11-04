#!/bin/bash

# HDFS Setup Script for Hadoop Cluster

# Define Hadoop and Java paths
HADOOP_HOME="/usr/local/hadoop"
HADOOP_CONF_DIR="$HADOOP_HOME/hadoop"
JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"

# Set Java home in hadoop-env.sh
echo "Setting JAVA_HOME in hadoop-env.sh"
sed -i "s|^# export JAVA_HOME=.*|export JAVA_HOME=${JAVA_HOME}|" $HADOOP_CONF_DIR/hadoop-env.sh

# Create necessary HDFS directories
echo "Creating necessary HDFS directories"
mkdir -p /hadoop/hdfs/namenode
mkdir -p /hadoop/hdfs/datanode
mkdir -p /hadoop/hdfs/secondarynamenode

# Update core-site.xml
echo "Configuring core-site.xml"
cat > $HADOOP_CONF_DIR/core-site.xml <<EOL
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/tmp/hadoop-\${user.name}</value>
        <description>A base for other temporary directories.</description>
    </property>
</configuration>
EOL

# Update hdfs-site.xml
echo "Configuring hdfs-site.xml"
cat > $HADOOP_CONF_DIR/hdfs-site.xml <<EOL
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>3</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///hadoop/hdfs/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///hadoop/hdfs/datanode</value>
    </property>
    <property>
        <name>dfs.secondary.http.address</name>
        <value>0.0.0.0:50090</value>
    </property>
</configuration>
EOL

# Update mapred-site.xml
echo "Configuring mapred-site.xml"
cat > $HADOOP_CONF_DIR/mapred-site.xml <<EOL
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
</configuration>
EOL

# Update yarn-site.xml
echo "Configuring yarn-site.xml"
cat > $HADOOP_CONF_DIR/yarn-site.xml <<EOL
<configuration>
    <property>
        <name>yarn.resourcemanager.hostname</name>
        <value>localhost</value>
    </property>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.aux-services.mapreduce.shuffle.class</name>
        <value>org.apache.hadoop.mapred.ShuffleHandler</value>
    </property>
</configuration>
EOL

# Format the Namenode
echo "Formatting Namenode"
hdfs namenode -format

# Start HDFS Services
echo "Starting HDFS Namenode and Datanode services"
$HADOOP_HOME/sbin/start-dfs.sh

# Verify the services are running
echo "Verifying HDFS services"
jps

# Start YARN ResourceManager and NodeManager
echo "Starting YARN ResourceManager and NodeManager"
$HADOOP_HOME/sbin/start-yarn.sh

# Check Hadoop filesystem
echo "Checking Hadoop filesystem"
hdfs dfsadmin -report

# Create HDFS directories for input/output
echo "Creating HDFS directories"
hdfs dfs -mkdir -p /user/hadoop/input
hdfs dfs -mkdir -p /user/hadoop/output

# Set HDFS permissions
echo "Setting HDFS permissions"
hdfs dfs -chmod -R 755 /user/hadoop

# Load data into HDFS
echo "Loading data into HDFS"
echo "Sample data for HDFS testing" > /tmp/testdata.txt
hdfs dfs -put /tmp/testdata.txt /user/hadoop/input

# Run a MapReduce job for verification
echo "Running MapReduce job for verification"
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar wordcount /user/hadoop/input /user/hadoop/output

# Display the result of the MapReduce job
echo "Displaying MapReduce job output"
hdfs dfs -cat /user/hadoop/output/part-r-00000

# Clean up HDFS output directory
echo "Cleaning up HDFS output directory"
hdfs dfs -rm -r /user/hadoop/output

# Stopping Hadoop services
echo "Stopping HDFS services"
$HADOOP_HOME/sbin/stop-dfs.sh

echo "Stopping YARN services"
$HADOOP_HOME/sbin/stop-yarn.sh

echo "HDFS setup completed successfully!"