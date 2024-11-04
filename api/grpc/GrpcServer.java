package api.grpc;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

public class GrpcServer {

    private static final Logger logger = Logger.getLogger(GrpcServer.class.getName());

    private Server server;

    // In-memory data store
    private static Map<String, String> dataStore = new HashMap<>();

    private void start() throws IOException {
        int port = 50051;
        server = ServerBuilder.forPort(port)
                .addService(new DataServiceImpl())
                .build()
                .start();
        logger.info("Server started, listening on " + port);
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.err.println("*** shutting down gRPC server since JVM is shutting down");
            GrpcServer.this.stop();
            System.err.println("*** server shut down");
        }));
    }

    private void stop() {
        if (server != null) {
            server.shutdown();
        }
    }

    private void blockUntilShutdown() throws InterruptedException {
        if (server != null) {
            server.awaitTermination();
        }
    }

    // Implementing the DataService defined in service.proto
    static class DataServiceImpl extends DataServiceGrpc.DataServiceImplBase {

        @Override
        public void fetchData(FetchRequest request, StreamObserver<FetchResponse> responseObserver) {
            logger.info("Fetching data for ID: " + request.getDataId());
            String data = dataStore.getOrDefault(request.getDataId(), "Data not found");

            FetchResponse response = FetchResponse.newBuilder()
                    .setDataId(request.getDataId())
                    .setDataContent(data)
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();
        }

        @Override
        public void submitData(SubmitRequest request, StreamObserver<SubmitResponse> responseObserver) {
            String newDataId = "ID_" + System.currentTimeMillis();
            logger.info("Submitting new data with content: " + request.getDataContent());

            dataStore.put(newDataId, request.getDataContent());

            SubmitResponse response = SubmitResponse.newBuilder()
                    .setDataId(newDataId)
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();
        }

        @Override
        public void updateData(UpdateRequest request, StreamObserver<UpdateResponse> responseObserver) {
            logger.info("Updating data for ID: " + request.getDataId());
            boolean success = dataStore.containsKey(request.getDataId());

            if (success) {
                dataStore.put(request.getDataId(), request.getNewDataContent());
            }

            UpdateResponse response = UpdateResponse.newBuilder()
                    .setDataId(request.getDataId())
                    .setSuccess(success)
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();
        }

        @Override
        public void deleteData(DeleteRequest request, StreamObserver<DeleteResponse> responseObserver) {
            logger.info("Deleting data for ID: " + request.getDataId());
            boolean success = dataStore.remove(request.getDataId()) != null;

            DeleteResponse response = DeleteResponse.newBuilder()
                    .setSuccess(success)
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();
        }
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        final GrpcServer server = new GrpcServer();
        server.start();
        server.blockUntilShutdown();
    }
}