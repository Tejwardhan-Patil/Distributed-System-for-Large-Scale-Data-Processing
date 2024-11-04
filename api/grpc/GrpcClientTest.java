package api.grpc;

import com.website.api.grpc.GrpcServiceProto.DataServiceGrpc;
import com.website.api.grpc.GrpcServiceProto.FetchRequest;
import com.website.api.grpc.GrpcServiceProto.FetchResponse;
import com.website.api.grpc.GrpcServiceProto.SubmitRequest;
import com.website.api.grpc.GrpcServiceProto.SubmitResponse;
import com.website.api.grpc.GrpcServiceProto.UpdateRequest;
import com.website.api.grpc.GrpcServiceProto.UpdateResponse;
import com.website.api.grpc.GrpcServiceProto.DeleteRequest;
import com.website.api.grpc.GrpcServiceProto.DeleteResponse;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;
import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import java.util.concurrent.TimeUnit;

public class GrpcClientTest {

    private ManagedChannel channel;
    private DataServiceGrpc.DataServiceBlockingStub blockingStub;

    private static final String HOST = "localhost";
    private static final int PORT = 50051;

    @Before
    public void setUp() {
        channel = ManagedChannelBuilder.forAddress(HOST, PORT)
                .usePlaintext()
                .build();
        blockingStub = DataServiceGrpc.newBlockingStub(channel);
    }

    @After
    public void tearDown() throws InterruptedException {
        if (channel != null) {
            channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
        }
    }

    @Test
    public void testFetchData() {
        FetchRequest request = FetchRequest.newBuilder()
                .setDataId("data123")
                .build();

        try {
            FetchResponse response = blockingStub.fetchData(request);
            Assert.assertNotNull(response);
            Assert.assertEquals("data123", response.getDataId());
            Assert.assertEquals("Sample content", response.getDataContent());
        } catch (StatusRuntimeException e) {
            Assert.fail("RPC failed: " + e.getStatus());
        }
    }

    @Test
    public void testSubmitData() {
        SubmitRequest request = SubmitRequest.newBuilder()
                .setDataContent("New data content")
                .build();

        try {
            SubmitResponse response = blockingStub.submitData(request);
            Assert.assertNotNull(response);
            Assert.assertNotNull(response.getDataId());
        } catch (StatusRuntimeException e) {
            Assert.fail("RPC failed: " + e.getStatus());
        }
    }

    @Test
    public void testUpdateData() {
        UpdateRequest request = UpdateRequest.newBuilder()
                .setDataId("data123")
                .setNewDataContent("Updated content")
                .build();

        try {
            UpdateResponse response = blockingStub.updateData(request);
            Assert.assertNotNull(response);
            Assert.assertTrue(response.getSuccess());
        } catch (StatusRuntimeException e) {
            Assert.fail("RPC failed: " + e.getStatus());
        }
    }

    @Test
    public void testDeleteData() {
        DeleteRequest request = DeleteRequest.newBuilder()
                .setDataId("data123")
                .build();

        try {
            DeleteResponse response = blockingStub.deleteData(request);
            Assert.assertNotNull(response);
            Assert.assertTrue(response.getSuccess());
        } catch (StatusRuntimeException e) {
            Assert.fail("RPC failed: " + e.getStatus());
        }
    }
}