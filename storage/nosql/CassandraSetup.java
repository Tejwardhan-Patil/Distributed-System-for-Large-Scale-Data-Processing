package storage.nosql;

import com.datastax.oss.driver.api.core.CqlSession;
import com.datastax.oss.driver.api.core.CqlIdentifier;
import com.datastax.oss.driver.api.core.cql.ResultSet;
import com.datastax.oss.driver.api.core.cql.Row;
import com.datastax.oss.driver.api.core.cql.SimpleStatement;
import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class CassandraSetup {

    private static final String KEYSPACE = "large_scale_data";
    private static final String TABLE = "data_storage";
    
    private CqlSession session;

    public void connect(String node, int port) {
        session = CqlSession.builder()
                .addContactPoint(new InetSocketAddress(node, port))
                .withLocalDatacenter("datacenter1")
                .build();
        System.out.println("Connected to Cassandra Cluster.");
    }

    public void createKeyspace() {
        String query = "CREATE KEYSPACE IF NOT EXISTS " + KEYSPACE + " WITH replication = "
                + "{'class':'SimpleStrategy', 'replication_factor':3};";
        session.execute(query);
        System.out.println("Keyspace created: " + KEYSPACE);
    }

    public void useKeyspace() {
        session.execute("USE " + KEYSPACE);
        System.out.println("Switched to Keyspace: " + KEYSPACE);
    }

    public void createTable() {
        String query = "CREATE TABLE IF NOT EXISTS " + TABLE + " ("
                + "id UUID PRIMARY KEY, "
                + "name text, "
                + "timestamp timestamp"
                + ");";
        session.execute(query);
        System.out.println("Table created: " + TABLE);
    }

    public void insertData(UUID id, String name, long timestamp) {
        String query = "INSERT INTO " + TABLE + " (id, name, timestamp) "
                + "VALUES (" + id + ", '" + name + "', " + timestamp + ");";
        session.execute(query);
        System.out.println("Inserted data into table: " + TABLE);
    }

    public List<String> selectAllData() {
        String query = "SELECT * FROM " + TABLE + ";";
        ResultSet rs = session.execute(query);
        List<String> results = new ArrayList<>();
        for (Row row : rs) {
            results.add(row.getUUID("id").toString() + " | " +
                        row.getString("name") + " | " +
                        row.getLong("timestamp"));
        }
        return results;
    }

    public void deleteData(UUID id) {
        String query = "DELETE FROM " + TABLE + " WHERE id = " + id + ";";
        session.execute(query);
        System.out.println("Deleted data from table: " + TABLE);
    }

    public void updateData(UUID id, String newName) {
        String query = "UPDATE " + TABLE + " SET name = '" + newName + "' WHERE id = " + id + ";";
        session.execute(query);
        System.out.println("Updated data in table: " + TABLE);
    }

    public void close() {
        session.close();
        System.out.println("Session closed.");
    }

    public static void main(String[] args) {
        CassandraSetup cassandra = new CassandraSetup();

        // Connect to Cassandra cluster
        cassandra.connect("127.0.0.1", 9042);

        // Create and switch to keyspace
        cassandra.createKeyspace();
        cassandra.useKeyspace();

        // Create table in the keyspace
        cassandra.createTable();

        // Insert data into the table
        UUID id1 = UUID.randomUUID();
        UUID id2 = UUID.randomUUID();
        cassandra.insertData(id1, "DataEntry1", System.currentTimeMillis());
        cassandra.insertData(id2, "DataEntry2", System.currentTimeMillis());

        // Fetch all data from the table
        List<String> results = cassandra.selectAllData();
        for (String result : results) {
            System.out.println(result);
        }

        // Update data in the table
        cassandra.updateData(id1, "UpdatedEntry1");

        // Delete data from the table
        cassandra.deleteData(id2);

        // Fetch data after deletion
        List<String> updatedResults = cassandra.selectAllData();
        for (String result : updatedResults) {
            System.out.println(result);
        }

        // Close connection to the cluster
        cassandra.close();
    }
}