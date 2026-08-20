// Command socket-relay exposes an HTTP-capable Unix socket on loopback TCP.
package main

import (
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
)

func copyAndCloseWrite(destination, source net.Conn) error {
	_, copyErr := io.Copy(destination, source)
	type closeWriter interface {
		CloseWrite() error
	}
	var closeErr error
	if connection, ok := destination.(closeWriter); ok {
		closeErr = connection.CloseWrite()
	}
	return errors.Join(copyErr, closeErr)
}

func relay(tcpConnection net.Conn, socketPath string) error {
	defer tcpConnection.Close()
	unixConnection, err := net.Dial("unix", socketPath)
	if err != nil {
		return fmt.Errorf("dial Unix socket: %w", err)
	}
	defer unixConnection.Close()

	errorsCh := make(chan error, 2)
	go func() { errorsCh <- copyAndCloseWrite(unixConnection, tcpConnection) }()
	go func() { errorsCh <- copyAndCloseWrite(tcpConnection, unixConnection) }()
	return errors.Join(<-errorsCh, <-errorsCh)
}

func serveOne(listener net.Listener, socketPath string) error {
	connection, err := listener.Accept()
	if err != nil {
		return fmt.Errorf("accept TCP connection: %w", err)
	}
	return relay(connection, socketPath)
}

func serve(listener net.Listener, socketPath string) error {
	for {
		connection, err := listener.Accept()
		if err != nil {
			return fmt.Errorf("accept TCP connection: %w", err)
		}
		go func() {
			if err := relay(connection, socketPath); err != nil {
				log.Printf("relay connection: %v", err)
			}
		}()
	}
}

func main() {
	listenAddress := flag.String("listen", "127.0.0.1:8080", "loopback TCP address")
	socketPath := flag.String("socket", "/gateway/gateway.sock", "gateway Unix socket")
	flag.Parse()

	listener, err := net.Listen("tcp", *listenAddress)
	if err != nil {
		log.Fatalf("listen on %s: %v", *listenAddress, err)
	}
	defer listener.Close()
	if err := serve(listener, *socketPath); err != nil {
		log.Fatal(err)
	}
}
