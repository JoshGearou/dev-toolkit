use hello::hello_world_client::HelloWorldClient;
use hello::HelloRequest;
use tonic::transport::Endpoint;
use get_if_addrs::get_if_addrs;
use std::io;
use std::net::IpAddr;

pub mod hello {
    tonic::include_proto!("hello");
}

const TCP_PORT : u16 = 50051;
const TCP_LOOPBACK_ADDRESS: &str = "http://[::]";
const UDS_PATH: &str = "/tmp/hello_world.sock";

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let tcp_loopback_address = format!("{}:{}", TCP_LOOPBACK_ADDRESS, TCP_PORT);
    tcp_call(&tcp_loopback_address).await?;
    
    let ip_address = get_ip_address()?.ok_or("No non-loopback IP address found")?;
    let tcp_address = format!("http://[{}]:{}", ip_address, TCP_PORT);
    tcp_call(&tcp_address).await?;

    let tcp_loopback_address = format!("{}:{}", TCP_LOOPBACK_ADDRESS, TCP_PORT);
    uds_call(&tcp_loopback_address).await?;
    Ok(())
}

fn get_ip_address() -> io::Result<Option<IpAddr>> {
    Ok(get_if_addrs()?
        .into_iter()
        .find(|iface| !iface.addr.ip().is_loopback())
        .map(|iface| iface.addr.ip()))
}

async fn tcp_call(tcp_address: &str) -> Result<(), Box<dyn std::error::Error>> {
    let mut tcp_client = HelloWorldClient::connect(tcp_address.to_string()).await?;
    let tcp_request = tonic::Request::new(HelloRequest {
        name: "TCP".into(),
    });
    let tcp_response = tcp_client.say_hello(tcp_request).await?;
    println!("TCP Response: {:?}", tcp_response.into_inner().message);
    Ok(())
}

async fn uds_call(tcp_address: &str) -> Result<(), Box<dyn std::error::Error>> {
    let uds_endpoint = Endpoint::from_shared(tcp_address.to_string())?
        .connect_with_connector(tower::service_fn(|_: tonic::transport::Uri| {
            tokio::net::UnixStream::connect(UDS_PATH)
        }))
        .await?;

    let mut uds_client = HelloWorldClient::new(uds_endpoint);
    let uds_response = uds_client.say_hello(tonic::Request::new(HelloRequest {
        name: "UDS".into(),
    })).await?;

    println!("UDS Response: {:?}", uds_response.into_inner().message);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::runtime::Runtime;

    #[test]
    fn tcp_loopback_hello_world_returns_correct_response() {
        let rt = Runtime::new().unwrap();
        rt.block_on(async {
            let tcp_loopback_address = format!("{}:{}", TCP_LOOPBACK_ADDRESS, TCP_PORT);
            let uri: tonic::transport::Uri = tcp_loopback_address.parse().unwrap();
            let mut client = HelloWorldClient::connect(uri).await.unwrap();
            let request = tonic::Request::new(HelloRequest {
                name: "TCP".into(),
            });
            let response = client.say_hello(request).await.unwrap();
            assert_eq!(response.into_inner().message, "Hello, TCP!");
        });
    }
    
    #[test]
    fn tcp_non_loopback_hello_world_returns_correct_response() {
        let rt = Runtime::new().unwrap();
        rt.block_on(async {
            let result: Result<(), Box<dyn std::error::Error>> = async {
                let ip_address = get_ip_address()?.ok_or("No non-loopback IP address found")?;
                let tcp_address = format!("http://{}:{}", ip_address, TCP_PORT);
                let uri: tonic::transport::Uri = tcp_address.parse()?;
                let mut client = HelloWorldClient::connect(uri).await.unwrap();
                let request = tonic::Request::new(HelloRequest {
                    name: "TCP".into(),
                });
                let response = client.say_hello(request).await.unwrap();
                assert_eq!(response.into_inner().message, "Hello, TCP!");
                Ok(())
            }.await;
            result.unwrap();
        });
    }

    #[test]
    fn uds_hello_world_returns_correct_response() {
        let rt = Runtime::new().unwrap();
        rt.block_on(async {
            let tcp_loopback_address = format!("{}:{}", TCP_LOOPBACK_ADDRESS, TCP_PORT);
            let uds_endpoint = Endpoint::from_shared(tcp_loopback_address)
                .unwrap()
                .connect_with_connector(tower::service_fn(|_: tonic::transport::Uri| {
                    tokio::net::UnixStream::connect(UDS_PATH)
                }))
                .await
                .unwrap();

            let mut client = HelloWorldClient::new(uds_endpoint);
            let request = tonic::Request::new(HelloRequest {
                name: "UDS".into(),
            });
            let response = client.say_hello(request).await.unwrap();
            assert_eq!(response.into_inner().message, "Hello, UDS!");
        });
    }

    #[test]
    fn tcp_loopback_hello_world_latency_less_than_2_millisecond() {
        let rt = Runtime::new().unwrap();
        rt.block_on(async {
            let tcp_loopback_address = format!("{}:{}", TCP_LOOPBACK_ADDRESS, TCP_PORT);
            let uri: tonic::transport::Uri = tcp_loopback_address.parse().unwrap();
            let mut client = HelloWorldClient::connect(uri).await.unwrap();

            for _ in 0..10 {
                let warmup_req = tonic::Request::new(HelloRequest {
                    name: "TCP".into(),
                });
                let _ = client.say_hello(warmup_req).await.unwrap();
            }

            let mut latencies = Vec::with_capacity(1000);
            for _ in 0..1000 {
                let request = tonic::Request::new(HelloRequest {
                    name: "TCP".into(),
                });
                let start = std::time::Instant::now();
                let _response = client.say_hello(request).await.unwrap();
                latencies.push(start.elapsed());
            }

            latencies.sort();
            let p50 = latencies[latencies.len() / 2];
            let p80 = latencies[latencies.len() * 80 / 100];
            let p99 = latencies[latencies.len() * 99 / 100];
            println!("TCP p50: {:?}, p80: {:?}, p99: {:?}, ({})", p50, p80, p99, tcp_loopback_address);
            assert!(
                p99.as_micros() < 2000,
                "TCP p99 latency is higher than expected: {:?}",
                p99
            );
        });
    }
    
    #[test]
    fn tcp_non_loopback_hello_world_latency_less_than_2_millisecond() {
        let rt = Runtime::new().unwrap();
        let result = rt.block_on(async {
            let ip_address = get_ip_address()?.ok_or("No non-loopback IP address found")?;
            let tcp_address = format!("http://{}:{}", ip_address, TCP_PORT);
            let uri: tonic::transport::Uri = tcp_address.parse()?;
            let mut client = HelloWorldClient::connect(uri).await?;

            for _ in 0..10 {
                let warmup_req = tonic::Request::new(HelloRequest {
                    name: "TCP".into(),
                });
                let _ = client.say_hello(warmup_req).await?;
            }

            let mut latencies = Vec::with_capacity(1000);
            for _ in 0..1000 {
                let request = tonic::Request::new(HelloRequest {
                    name: "TCP".into(),
                });
                let start = std::time::Instant::now();
                let _response = client.say_hello(request).await?;
                latencies.push(start.elapsed());
            }

            latencies.sort();
            let p50 = latencies[latencies.len() / 2];
            let p80 = latencies[latencies.len() * 80 / 100];
            let p99 = latencies[latencies.len() * 99 / 100];
            println!("TCP p50: {:?}, p80: {:?}, p99: {:?}, ({})", p50, p80, p99, tcp_address);
            assert!(
                p99.as_micros() < 2000,
                "TCP p99 latency is higher than expected: {:?}",
                p99
            );

            Ok::<(), Box<dyn std::error::Error>>(()) // ✅ Ensure the async block returns Result
        });

        result.unwrap(); // ✅ Unwrap outside `block_on`
    }

    
    #[test]
    fn uds_hello_world_latency_less_than_2_millisecond() {
        let rt = Runtime::new().unwrap();
        rt.block_on(async {
            let tcp_loopback_address = format!("{}:{}", TCP_LOOPBACK_ADDRESS, TCP_PORT);
            let uds_endpoint = Endpoint::from_shared(tcp_loopback_address)
                .expect("Failed to create gRPC endpoint") // ✅ Unwrap before calling `connect_with_connector`
                .connect_with_connector(tower::service_fn(|_| {
                    tokio::net::UnixStream::connect(UDS_PATH)
                }))
                .await
                .unwrap();

            let mut client = HelloWorldClient::new(uds_endpoint);
    
            for _ in 0..10 {
                let warmup_req = tonic::Request::new(HelloRequest {
                    name: "UDS".into(),
                });
                let _ = client.say_hello(warmup_req).await.unwrap();
            }
    
            let mut latencies = Vec::with_capacity(1000);
            for _ in 0..1000 {
                let request = tonic::Request::new(HelloRequest {
                    name: "UDS".into(),
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
        });
    }    
}
