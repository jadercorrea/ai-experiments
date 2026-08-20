package main

import (
	"io"
	"net"
	"os"
	"path/filepath"
	"testing"
)

func TestRelayConnectsTCPToUnixSocket(t *testing.T) {
	t.Parallel()

	temporaryDirectory, err := os.MkdirTemp("/tmp", "relay-")
	if err != nil {
		t.Fatalf("create temporary directory: %v", err)
	}
	t.Cleanup(func() {
		if err := os.RemoveAll(temporaryDirectory); err != nil {
			t.Errorf("remove temporary directory: %v", err)
		}
	})
	socketPath := filepath.Join(temporaryDirectory, "gateway.sock")
	unixListener, err := net.Listen("unix", socketPath)
	if err != nil {
		t.Fatalf("listen Unix socket: %v", err)
	}
	defer unixListener.Close()

	tcpListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen TCP socket: %v", err)
	}
	defer tcpListener.Close()

	errCh := make(chan error, 2)
	go func() { errCh <- serveOne(tcpListener, socketPath) }()
	go func() {
		connection, acceptErr := unixListener.Accept()
		if acceptErr != nil {
			errCh <- acceptErr
			return
		}
		defer connection.Close()
		message, readErr := io.ReadAll(connection)
		if readErr != nil {
			errCh <- readErr
			return
		}
		_, writeErr := connection.Write([]byte("reply:" + string(message)))
		errCh <- writeErr
	}()

	client, err := net.Dial("tcp", tcpListener.Addr().String())
	if err != nil {
		t.Fatalf("dial relay: %v", err)
	}
	if _, err := client.Write([]byte("request")); err != nil {
		t.Fatalf("write request: %v", err)
	}
	if err := client.(*net.TCPConn).CloseWrite(); err != nil {
		t.Fatalf("close request: %v", err)
	}
	response, err := io.ReadAll(client)
	client.Close()
	if err != nil {
		t.Fatalf("read response: %v", err)
	}
	if got, want := string(response), "reply:request"; got != want {
		t.Fatalf("response = %q, want %q", got, want)
	}
	for range 2 {
		if err := <-errCh; err != nil {
			t.Fatalf("relay: %v", err)
		}
	}
}
