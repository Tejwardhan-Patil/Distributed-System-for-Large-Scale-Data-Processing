package ingestion_pipelines;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import org.bson.Document;

public class DbConnector {
    
    private Connection sqlConnection;
    private MongoClient mongoClient;
    private String dbType;

    public DbConnector(String dbType) {
        this.dbType = dbType;
    }

    // SQL Connection Setup
    public void connectToSqlDb(String url, String user, String password) throws SQLException {
        sqlConnection = DriverManager.getConnection(url, user, password);
        System.out.println("Connected to SQL Database.");
    }

    // MongoDB Connection Setup
    public void connectToMongoDb(String uri) {
        MongoClientURI connectionString = new MongoClientURI(uri);
        mongoClient = new MongoClient(connectionString);
        System.out.println("Connected to MongoDB.");
    }

    // Closing SQL Connection
    public void closeSqlConnection() throws SQLException {
        if (sqlConnection != null) {
            sqlConnection.close();
            System.out.println("SQL connection closed.");
        }
    }

    // Closing MongoDB Connection
    public void closeMongoConnection() {
        if (mongoClient != null) {
            mongoClient.close();
            System.out.println("MongoDB connection closed.");
        }
    }

    // Insert Data into SQL Database
    public void insertDataToSql(String table, String[] columns, String[] values) throws SQLException {
        if (sqlConnection == null) {
            throw new SQLException("SQL Connection not established.");
        }

        StringBuilder query = new StringBuilder("INSERT INTO ").append(table).append("(");
        for (int i = 0; i < columns.length; i++) {
            query.append(columns[i]);
            if (i < columns.length - 1) query.append(", ");
        }
        query.append(") VALUES(");
        for (int i = 0; i < values.length; i++) {
            query.append("?");
            if (i < values.length - 1) query.append(", ");
        }
        query.append(");");

        PreparedStatement stmt = sqlConnection.prepareStatement(query.toString());
        for (int i = 0; i < values.length; i++) {
            stmt.setString(i + 1, values[i]);
        }
        stmt.executeUpdate();
        System.out.println("Data inserted into SQL table: " + table);
    }

    // Insert Data into MongoDB
    public void insertDataToMongo(String dbName, String collectionName, Document document) {
        if (mongoClient == null) {
            throw new IllegalStateException("MongoDB connection not established.");
        }
        MongoDatabase database = mongoClient.getDatabase(dbName);
        MongoCollection<Document> collection = database.getCollection(collectionName);
        collection.insertOne(document);
        System.out.println("Data inserted into MongoDB collection: " + collectionName);
    }

    // SQL Query Execution
    public ResultSet executeSqlQuery(String query) throws SQLException {
        if (sqlConnection == null) {
            throw new SQLException("SQL Connection not established.");
        }

        PreparedStatement stmt = sqlConnection.prepareStatement(query);
        return stmt.executeQuery();
    }

    // MongoDB Query Execution
    public void executeMongoQuery(String dbName, String collectionName, Document query) {
        if (mongoClient == null) {
            throw new IllegalStateException("MongoDB connection not established.");
        }

        MongoDatabase database = mongoClient.getDatabase(dbName);
        MongoCollection<Document> collection = database.getCollection(collectionName);
        for (Document doc : collection.find(query)) {
            System.out.println(doc.toJson());
        }
    }

    // Main method for ingestion
    public static void main(String[] args) {
        DbConnector connector = new DbConnector("SQL");

        // SQL Ingestion
        try {
            connector.connectToSqlDb("jdbc:mysql://localhost:3306/mydb", "user", "password");

            String[] columns = {"name", "age", "email"};
            String[] values = {"Phil", "29", "phil@website.com"};
            connector.insertDataToSql("users", columns, values);

            ResultSet rs = connector.executeSqlQuery("SELECT * FROM users;");
            while (rs.next()) {
                System.out.println("User: " + rs.getString("name") + ", Age: " + rs.getInt("age") + ", Email: " + rs.getString("email"));
            }

            connector.closeSqlConnection();
        } catch (SQLException e) {
            System.err.println("SQL Exception: " + e.getMessage());
        }

        // MongoDB Ingestion
        connector = new DbConnector("MongoDB");
        connector.connectToMongoDb("mongodb://localhost:27017");

        Document doc = new Document("name", "Jack").append("age", 28).append("email", "jack@website.com");
        connector.insertDataToMongo("mydatabase", "users", doc);

        Document query = new Document("name", "Jack");
        connector.executeMongoQuery("mydatabase", "users", query);

        connector.closeMongoConnection();
    }
}