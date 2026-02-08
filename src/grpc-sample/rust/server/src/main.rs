use tonic::{transport::Server, Request, Response, Status};
use hello::hello_world_server::{HelloWorld, HelloWorldServer};
use hello::{HelloRequest, HelloResponse};
use tokio::net::UnixListener;
use tokio_stream::wrappers::UnixListenerStream;
use std::net::SocketAddr;

pub mod hello {
    tonic::include_proto!("hello");
}

#[derive(Default, Clone)]
pub struct MyHelloWorld;

#[tonic::async_trait]
impl HelloWorld for MyHelloWorld {
    async fn say_hello(
        &self,
        request: Request<HelloRequest>,
    ) -> Result<Response<HelloResponse>, Status> {
        let reply = HelloResponse {
            message: format!("Hello, {}!", request.into_inner().name),
        };
        Ok(Response::new(reply))
    }
}

const TCP_PORT: u16 = 50051;
const TCP_IPV6_WILDCARD: &str = "[::]";
const UDS_SOCKET_PATH: &str = "/tmp/hello_world.sock";

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let tcp_server_address = format!("{}:{}", TCP_IPV6_WILDCARD, TCP_PORT);
    let tcp_server = create_tcp_server(&tcp_server_address);
    let uds_server = create_uds_server(UDS_SOCKET_PATH.to_string());
    
    tokio::try_join!(tcp_server, uds_server)?;

    Ok(())
}

async fn create_tcp_server(tcp_address: &str) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let tcp_socket_address: SocketAddr = tcp_address.parse()?;
    let service = MyHelloWorld;

    Server::builder()
        .add_service(HelloWorldServer::new(service))
        .serve(tcp_socket_address)
        .await?;

    Ok(())
}

async fn create_uds_server(
    uds_socket_path: String,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let _ = std::fs::remove_file(&uds_socket_path);
    let uds_listener = UnixListener::bind(&uds_socket_path)?;
    let uds_incoming = UnixListenerStream::new(uds_listener);
    let service = MyHelloWorld;

    Server::builder()
        .add_service(HelloWorldServer::new(service))
        .serve_with_incoming(uds_incoming)
        .await?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use hello::hello_world_client::HelloWorldClient;
    use hello::HelloRequest;
    use tokio::time::{sleep, Duration};
    use tonic::transport::Endpoint;
    use tokio::net::UnixStream;
    use hyper::service::Service;
    use hyper::http::Uri;
    use std::pin::Pin;
    use std::task::{Context, Poll};
    use std::future::Future;
    use std::io;
    
    const TCP_IPV6_LOOPBACK: &str = "[::1]";

    struct UnixDomainConnector {
        socket_path: String,
    }

    impl UnixDomainConnector {
        fn new(path: String) -> Self {
            UnixDomainConnector { socket_path: path }
        }
    }

    impl Service<Uri> for UnixDomainConnector {
        type Response = UnixStream;
        type Error = io::Error;
        type Future = Pin<Box<dyn Future<Output = Result<Self::Response, Self::Error>> + Send>>;

        fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
            Poll::Ready(Ok(()))
        }

        fn call(&mut self, _req: Uri) -> Self::Future {
            let path = self.socket_path.clone();
            Box::pin(UnixStream::connect(path))
        }
    }

    #[tokio::test]
    async fn tcp_loopback_hello_world_returns_correct_response() {
        let tcp_port = 50052;
        let server_tcp_address = format!("{}:{}", TCP_IPV6_LOOPBACK, tcp_port);
        let server_handle = tokio::spawn(async move {
            create_tcp_server(&server_tcp_address).await.unwrap();
        });

        sleep(Duration::from_secs(1)).await;

        let client_tcp_address = format!("http://{}:{}", TCP_IPV6_LOOPBACK, tcp_port);
        let mut client = HelloWorldClient::connect(client_tcp_address).await.unwrap();
        let request = tonic::Request::new(HelloRequest {
            name: "World".into(),
        });
        let response = client.say_hello(request).await.unwrap();
        assert_eq!(response.into_inner().message, "Hello, World!");

        server_handle.abort();
    }

    #[tokio::test]
    async fn uds_hello_world_returns_correct_response() {
        let uds_path = "/tmp/hello_world_test_1.sock".to_string();
        
        let server_uds_path = uds_path.clone();
        let server_handle = tokio::spawn(async move {
            create_uds_server(server_uds_path).await.unwrap();
        });

        sleep(Duration::from_secs(1)).await;

        let connector_uds_path = uds_path.clone();
        let connector = UnixDomainConnector::new(connector_uds_path);
        let server_tcp_address = format!("http://{}", TCP_IPV6_LOOPBACK);
        let endpoint = Endpoint::try_from(server_tcp_address).unwrap();
        let channel = endpoint
            .connect_with_connector(connector)
            .await
            .expect("Failed to connect via UDS");

        let mut client = HelloWorldClient::new(channel);
        let request = tonic::Request::new(HelloRequest {
            name: "World".into(),
        });
        let response = client.say_hello(request).await.unwrap();
        assert_eq!(response.into_inner().message, "Hello, World!");

        server_handle.abort();
    }
    
    #[tokio::test]
    async fn tcp_loopback_hello_world_latency_less_than_2_millisecond() {
        let tcp_port = 50053;
        let tcp_address = format!("{}:{}", TCP_IPV6_LOOPBACK, tcp_port);
        let server_tcp_address = tcp_address.clone();
        let server_handle = tokio::spawn(async move {
            create_tcp_server(&server_tcp_address).await.unwrap();
        });
        
        tokio::time::sleep(std::time::Duration::from_secs(1)).await;
    
        let client_tcp_address = format!("http://{}:{}", TCP_IPV6_LOOPBACK, tcp_port);
        let mut client = HelloWorldClient::connect(client_tcp_address).await.unwrap();
    
        for _ in 0..10 {
            let warmup_req = tonic::Request::new(HelloRequest {
                name: "TCP".into(),
            });
            let _ = client.say_hello(warmup_req).await.unwrap();
        }
    
        let mut latencies = Vec::with_capacity(1000);
        for _ in 0..1000 {
            let request = tonic::Request::new(HelloRequest {
                name: "World".into(),
            });
            let start = std::time::Instant::now();
            let _response = client.say_hello(request).await.unwrap();
            latencies.push(start.elapsed());
        }
    
        latencies.sort();
        let p50 = latencies[latencies.len() / 2];
        let p80 = latencies[latencies.len() * 80 / 100];
        let p99 = latencies[latencies.len() * 99 / 100];
        
        let server_tcp_address = tcp_address.clone();
        println!("TCP p50: {:?}, p80: {:?}, p99: {:?}, ({})", p50, p80, p99, &server_tcp_address);
        assert!(
            p99.as_micros() < 2000,
            "TCP p99 latency is higher than expected: {:?}",
            p99
        );
    
        server_handle.abort();
    }
    
    #[tokio::test]
    async fn uds_hello_world_latency_less_than_2_millisecond() {
        let uds_path = "/tmp/hello_world_test_2.sock".to_string();
        
        let server_uds_path = uds_path.clone();
        let server_handle = tokio::spawn(async move {
            create_uds_server(server_uds_path).await.unwrap();
        });

        sleep(Duration::from_secs(1)).await;

        let connector_uds_path = uds_path.clone();
        let connector = UnixDomainConnector::new(connector_uds_path);
        let server_tcp_address = format!("http://{}", TCP_IPV6_LOOPBACK);
        let endpoint = Endpoint::try_from(server_tcp_address).unwrap();
        let channel = endpoint
            .connect_with_connector(connector)
            .await
            .expect("Failed to connect via UDS");
        let mut client = HelloWorldClient::new(channel);
    
        for _ in 0..10 {
            let warmup_req = tonic::Request::new(HelloRequest {
                name: "UDS".into(),
            });
            let _ = client.say_hello(warmup_req).await.unwrap();
        }
    
        let mut latencies = Vec::with_capacity(1000);
        for _ in 0..1000 {
            let request = tonic::Request::new(HelloRequest {
                name: "World".into(),
            });
            let start = std::time::Instant::now();
            let _response = client.say_hello(request).await.unwrap();
            latencies.push(start.elapsed());
        }
    
        latencies.sort();
        let p50 = latencies[latencies.len() / 2];
        let p80 = latencies[latencies.len() * 80 / 100];
        let p99 = latencies[latencies.len() * 99 / 100];
    
        println!("UDS p50: {:?}, p80: {:?}, p99: {:?}", p50, p80, p99);
        assert!(
            p99.as_micros() < 2000,
            "UDS p99 latency is higher than expected: {:?}",
            p99
        );
    
        server_handle.abort();
    }    
}
