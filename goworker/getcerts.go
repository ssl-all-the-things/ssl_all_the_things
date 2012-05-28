package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"time"
)

// Configure the flags
var nworkers = flag.Int("n", 256, "The number of concurrent connections.")

type WorkTodo struct {
	Host   string
	Bucket int
}

type WorkMessage struct {
	Id   int
	C, D int
}

func fill_workqueue(queue chan WorkTodo, host string) (int, int) {
	target := fmt.Sprintf("%s/get/", host)
	resp, err := http.Get(target)
	if err != nil {
        fmt.Println("Error fetching worklist")
		return 0, 0
	}
	// Decode json
	var m WorkMessage
	body, err := ioutil.ReadAll(resp.Body)
	err = json.Unmarshal(body, &m)
    
    resp.Body.Close()

	// List all IP's in block
	total := 0
	for a := 0; a < 256; a++ {
		if a == 10 {
			continue // RFC 1918
		}
		for b := 0; b <= 255; b++ {
			if (a == 127) && (b > 15) && (b < 32) {
				continue // RFC 1918
			}
			if (a == 192) && (b == 168) {
				continue // RFC 1918
			}
			total++
			queue <- WorkTodo{fmt.Sprintf("%d.%d.%d.%d:443", a, b, m.C, m.D), m.Id}
		}
	}
	return total, m.Id
}

func handle_cert(cert *x509.Certificate) {
	fmt.Println(cert.Subject.CommonName)
}

// Worker function
func getcert(in chan WorkTodo, out chan int) {
	config := tls.Config{InsecureSkipVerify: true}
	// Keep waiting for work
	for {
		target := <-in
        tcpconn, err := net.DialTimeout("tcp", target.Host, 2*time.Second)
		if err != nil {
            out <- 1
			continue
		}
		conn := tls.Client(tcpconn, &config)
		err = conn.Handshake()
		if err != nil {
            out <- 1
			continue
		}
		err = conn.Handshake()
		if err != nil {
            out <- 1
			continue
		}
		state := conn.ConnectionState()
		// TODO: store certificate
		for _, cert := range state.PeerCertificates {
			handle_cert(cert)
		}
		conn.Close()
        out <- 1
	}
}

func main() {
	// Parse the commandline flags
	flag.Parse()
	if flag.NArg() != 1 {
		fmt.Println("Expected hostname")
		return
	}
	host := flag.Arg(0)

	// Make the worker chanels
	in := make(chan WorkTodo, 256*256)
	out := make(chan int, 256*256)

	//  Start the workers
    for i := 0; i < *nworkers; i++ {
		go getcert(in, out)
	}

	// Main loop getting and handling work
	for {
		total, id := fill_workqueue(in, host)
        fmt.Println("Bucketid", id, "contains", total, "ip's")
		// get results
		for {
			<-out
			total--
			if total == 0 {
				// Report block as finished and break
				target := fmt.Sprintf("%s/done/%d/", host, id)
                _, err := http.Get(target)
                if err != nil {
                    fmt.Println("Error setting worklist as done")
                }

                // TODO: report block as finished

				break // Break and get a new block
			}
		}
	}

}
