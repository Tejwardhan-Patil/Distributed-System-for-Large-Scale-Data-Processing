import ingestion_pipelines.DbConnector;
import org.junit.jupiter.api.*;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import static org.junit.jupiter.api.Assertions.*;

@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public class TestDbConnector {

    private DbConnector dbConnector;
    private Connection connection;

    @BeforeAll
    public void setUp() {
        dbConnector = new DbConnector();
        connection = dbConnector.getConnection();
        assertNotNull(connection, "Database connection should not be null");
    }

    @Test
    @DisplayName("Test database connection validity")
    public void testConnectionValidity() throws SQLException {
        assertTrue(connection.isValid(5), "Connection should be valid within 5 seconds.");
    }

    @Test
    @DisplayName("Test database can execute simple query")
    public void testSimpleQueryExecution() throws SQLException {
        String query = "SELECT 1";
        try (Statement stmt = connection.createStatement(); ResultSet rs = stmt.executeQuery(query)) {
            assertTrue(rs.next(), "Query should return a result.");
            assertEquals(1, rs.getInt(1), "Result of the query should be 1.");
        }
    }

    @Test
    @DisplayName("Test database can execute data insertion")
    public void testInsertData() throws SQLException {
        String insertSQL = "INSERT INTO test_table (id, name) VALUES (1, 'Max')";
        try (Statement stmt = connection.createStatement()) {
            int rowsAffected = stmt.executeUpdate(insertSQL);
            assertEquals(1, rowsAffected, "One row should be inserted.");
        }
    }

    @Test
    @DisplayName("Test database can execute data retrieval")
    public void testRetrieveData() throws SQLException {
        String query = "SELECT name FROM test_table WHERE id = 1";
        try (Statement stmt = connection.createStatement(); ResultSet rs = stmt.executeQuery(query)) {
            assertTrue(rs.next(), "Query should return a result.");
            assertEquals("Max", rs.getString("name"), "Retrieved name should be 'Max'.");
        }
    }

    @Test
    @DisplayName("Test database can execute data update")
    public void testUpdateData() throws SQLException {
        String updateSQL = "UPDATE test_table SET name = 'Kyle' WHERE id = 1";
        try (Statement stmt = connection.createStatement()) {
            int rowsAffected = stmt.executeUpdate(updateSQL);
            assertEquals(1, rowsAffected, "One row should be updated.");
        }

        String query = "SELECT name FROM test_table WHERE id = 1";
        try (Statement stmt = connection.createStatement(); ResultSet rs = stmt.executeQuery(query)) {
            assertTrue(rs.next(), "Query should return a result.");
            assertEquals("Kyle", rs.getString("name"), "Retrieved name should be 'Kyle'.");
        }
    }

    @Test
    @DisplayName("Test database can execute data deletion")
    public void testDeleteData() throws SQLException {
        String deleteSQL = "DELETE FROM test_table WHERE id = 1";
        try (Statement stmt = connection.createStatement()) {
            int rowsAffected = stmt.executeUpdate(deleteSQL);
            assertEquals(1, rowsAffected, "One row should be deleted.");
        }

        String query = "SELECT name FROM test_table WHERE id = 1";
        try (Statement stmt = connection.createStatement(); ResultSet rs = stmt.executeQuery(query)) {
            assertFalse(rs.next(), "Query should return no result after deletion.");
        }
    }

    @Test
    @DisplayName("Test invalid SQL query throws SQLException")
    public void testInvalidQuery() {
        String invalidSQL = "SELECT * FROM non_existing_table";
        SQLException thrown = assertThrows(SQLException.class, () -> {
            try (Statement stmt = connection.createStatement()) {
                stmt.executeQuery(invalidSQL);
            }
        }, "Expected SQLException for invalid SQL query.");
        assertTrue(thrown.getMessage().contains("non_existing_table"), "Exception message should contain 'non_existing_table'.");
    }

    @Test
    @DisplayName("Test database supports transactions")
    public void testTransaction() throws SQLException {
        connection.setAutoCommit(false);
        try {
            String insertSQL = "INSERT INTO test_table (id, name) VALUES (2, 'Kyle')";
            try (Statement stmt = connection.createStatement()) {
                stmt.executeUpdate(insertSQL);
            }

            String query = "SELECT name FROM test_table WHERE id = 2";
            try (Statement stmt = connection.createStatement(); ResultSet rs = stmt.executeQuery(query)) {
                assertTrue(rs.next(), "Query should return a result.");
                assertEquals("Kyle", rs.getString("name"), "Name should be 'Kyle'.");
            }

            connection.rollback();
            try (Statement stmt = connection.createStatement(); ResultSet rs = stmt.executeQuery(query)) {
                assertFalse(rs.next(), "Query should return no result after rollback.");
            }
        } finally {
            connection.setAutoCommit(true);
        }
    }

    @Test
    @DisplayName("Test database handles large data insertions")
    public void testBulkInsert() throws SQLException {
        connection.setAutoCommit(false);
        try (Statement stmt = connection.createStatement()) {
            for (int i = 0; i < 1000; i++) {
                String insertSQL = String.format("INSERT INTO test_table (id, name) VALUES (%d, 'User%d')", i + 3, i);
                stmt.executeUpdate(insertSQL);
            }
        }
        connection.commit();

        String query = "SELECT COUNT(*) FROM test_table";
        try (Statement stmt = connection.createStatement(); ResultSet rs = stmt.executeQuery(query)) {
            assertTrue(rs.next(), "Query should return a result.");
            assertEquals(1002, rs.getInt(1), "Table should contain 1002 rows.");
        }
    }

    @AfterAll
    public void tearDown() throws SQLException {
        if (connection != null) {
            connection.close();
        }
    }
}