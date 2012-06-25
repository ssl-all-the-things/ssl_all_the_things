package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"flag"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"net/url"
	"time"
	"strings"
)

// Configure the flags
var nworkers = flag.Int("n", 256, "The number of concurrent connections.")
var serverinfo = "ssl.iskansloos.nl"

type WorkTodo struct {
	Host   string
	Bucket int
}

type WorkMessage struct {
	Id	 int
	C, D int
}

type ptr map[string]string

func fill_workqueue(queue chan WorkTodo, host string) (int, int) {
	target := fmt.Sprintf("http://%s/get/", host)
	resp, err := http.Get(target)
	if err != nil {
		fmt.Println(fmt.Sprintf("Error fetching worklist: %s", err))
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
			if (a == 172) && (b > 15) && (b < 32) {
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

func handle_cert(cert *x509.Certificate, host string) {
	block := pem.Block{Type: "CERTIFICATE", Bytes: cert.Raw}
	pemdata := string(pem.EncodeToMemory(&block))
	formdata := url.Values{}
	formdata.Set("commonname", cert.Subject.CommonName)
	formdata.Set("pem", pemdata)
	formdata.Set("endpoint", host)
	target := fmt.Sprintf("http://%s/post/", serverinfo)
	_, err := http.PostForm(target, formdata)
	if err != nil {
		fmt.Println(fmt.Sprintf("ERROR posting cert: %s", err))
	}
}

func handle_hostname(hostnames ptr) (ptr) {
	if len(hostnames) > 0 {
		target := fmt.Sprintf("http://%s/hostname/", serverinfo)

		formdata := url.Values{}
		c := 0
		for i, v := range hostnames {
			varname := fmt.Sprintf("hostname[%d]", c)
			value := fmt.Sprintf("%s:%s", i, v)
			fmt.Println(varname, value)
			formdata.Set(varname,value)
			c++
		}
		_, err := http.PostForm(target, formdata)
		if err != nil {
			fmt.Println(fmt.Sprintf("ERROR posting hostname: %s", err))
			return hostnames
		}
	}

	return ptr {}
}

// Report block as finished and break
func update_block_done(host string, id int) {
	target := fmt.Sprintf("http://%s/done/%d/", host, id)
	_, err := http.Get(target)
	if err != nil {
	    fmt.Println("Error setting worklist as done ", err)
	}
}

// Worker function
func getcert(in chan WorkTodo) {
	config := tls.Config{InsecureSkipVerify: true}
	var done = ptr{ }
	// Keep waiting for work
	for {
		target := <-in
		ip := strings.Split(target.Host, ":")
		hostname, err := net.LookupAddr(ip[0])
		if err == nil {
			done[hostname[0]] = ip[0]
		}

		tcpconn, err := net.DialTimeout("tcp", target.Host, 2*time.Second)
		if err != nil {
			continue
		}
		conn := tls.Client(tcpconn, &config)
		err = conn.Handshake()
		if err != nil {
			continue
		}
		err = conn.Handshake()
		if err != nil {
			continue
		}
		state := conn.ConnectionState()
		// TODO: store certificate
		for _, cert := range state.PeerCertificates {
			handle_cert(cert, target.Host)
			done = handle_hostname(done)
		}
		conn.Close()
	}
}

func main() {
	// Make the worker chanels
	in := make(chan WorkTodo, 256*256)

	//	Start the workers
	for i := 0; i < *nworkers; i++ {
		go getcert(in)
	}

	// Don't update on the first run
	update := false

	// Main loop getting and handling work
	for {
		if len(in) == 0 {
			total, id := fill_workqueue(in, serverinfo)
			fmt.Println("Bucketid", id, "contains", total, "ip's")

			update = true

			if update {
				update_block_done(serverinfo, id)
			}
		}

		time.Sleep(1 * time.Second)
		fmt.Println("Done:", len(in)/cap(in), "%")
	}

}
