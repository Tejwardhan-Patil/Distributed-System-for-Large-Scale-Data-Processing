#!/bin/bash

# ELK Stack setup for distributed system logging and monitoring
# Elasticsearch, Logstash, Kibana setup using Docker Compose

# Define environment variables
ELK_VERSION="7.15.2"  # Set the ELK Stack version
ES_MEMORY_LIMIT="2g"  # Set Elasticsearch memory limit

# Create directories for Elasticsearch, Logstash, and Kibana
mkdir -p /opt/elk/elasticsearch /opt/elk/logstash /opt/elk/kibana

# Elasticsearch Configuration
cat > /opt/elk/elasticsearch/elasticsearch.yml <<EOL
cluster.name: "elk-cluster"
node.name: "elk-node-1"
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node
EOL

# Logstash Configuration
cat > /opt/elk/logstash/logstash.conf <<EOL
input {
  beats {
    port => 5044
  }
}

filter {
  if [type] == "syslog" {
    grok {
      match => { "message" => "%{SYSLOGLINE}" }
    }
    date {
      match => [ "timestamp", "MMM  d HH:mm:ss", "MMM dd HH:mm:ss" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "%{[@metadata][beat]}-%{+YYYY.MM.dd}"
  }
  stdout { codec => rubydebug }
}
EOL

# Kibana Configuration
cat > /opt/elk/kibana/kibana.yml <<EOL
server.name: kibana
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://elasticsearch:9200"]
EOL

# Docker Compose Configuration for ELK Stack
cat > /opt/elk/docker-compose.yml <<EOL
version: '3'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:$ELK_VERSION
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms$ES_MEMORY_LIMIT -Xmx$ES_MEMORY_LIMIT
    volumes:
      - /opt/elk/elasticsearch:/usr/share/elasticsearch/config
    ports:
      - "9200:9200"
      - "9300:9300"
    networks:
      - elk

  logstash:
    image: docker.elastic.co/logstash/logstash:$ELK_VERSION
    container_name: logstash
    volumes:
      - /opt/elk/logstash:/usr/share/logstash/config
    ports:
      - "5044:5044"
      - "5000:5000"
      - "9600:9600"
    networks:
      - elk

  kibana:
    image: docker.elastic.co/kibana/kibana:$ELK_VERSION
    container_name: kibana
    volumes:
      - /opt/elk/kibana:/usr/share/kibana/config
    ports:
      - "5601:5601"
    networks:
      - elk

networks:
  elk:
    driver: bridge
EOL

# Start the ELK Stack
cd /opt/elk
docker-compose up -d

# Check if ELK stack is running
echo "Waiting for Elasticsearch to start..."
while ! curl -s http://localhost:9200 > /dev/null; do
  sleep 5
done

echo "Elasticsearch is up and running at http://localhost:9200"

# Check if Kibana is running
echo "Waiting for Kibana to start..."
while ! curl -s http://localhost:5601 > /dev/null; do
  sleep 5
done

echo "Kibana is up and running at http://localhost:5601"

# Install Filebeat for log forwarding
echo "Installing Filebeat for log collection..."
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-$ELK_VERSION-linux-x86_64.tar.gz
tar xzvf filebeat-$ELK_VERSION-linux-x86_64.tar.gz
cd filebeat-$ELK_VERSION-linux-x86_64/

# Filebeat configuration for Logstash
cat > filebeat.yml <<EOL
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/*.log

output.logstash:
  hosts: ["localhost:5044"]
EOL

# Start Filebeat
./filebeat -e &

# Health check for Elasticsearch and Kibana
curl -X GET "localhost:9200/_cluster/health?pretty"
curl -X GET "localhost:5601/api/status"

echo "ELK Stack setup is complete. Elasticsearch is available at http://localhost:9200 and Kibana is available at http://localhost:5601."