package main

import (
    "flag"
    "fmt"
    "encoding/json"
    "net/http"
    "crypto/tls"
    "crypto/x509"
    "time"
    "io/ioutil"
)

// Configure the flags
var nworkers = flag.Int("n", 256, "The number of concurrent connections.")

// Struct for returning the status of a connection to a given host.
type Status struct {
    host    string
    succes  bool

}

type WorkTodo struct {
    target string
    bucket_id int
}

type WorkMessage struct {
    Id int
    Targets []int
}


func fill_workqueue(queue chan WorkTodo, host string) {
    target := fmt.Sprintf("%s/get/", host)
    fmt.Println(target)
    for { // Keep getting new blocks
        resp, err := http.Get(target)
        if err != nil {
            // Sleep on error before retry
            time.Sleep(10 * time.Second)
            continue
        }
        // Decode json
        var m WorkMessage
        body, err := ioutil.ReadAll(resp.Body)
        err = json.Unmarshal(body, &m)
        // List all IP's in block
        a := m.Targets[0]
        b := m.Targets[1]
        for c := m.Targets[2]; c < m.Targets[2]+16; c++ {
            for d := 0; d < 256; d++ {
                queue <- WorkTodo{fmt.Sprintf("%d.%d.%d.%d:443", a, b, c, d), m.Id}
            }
        }
        resp.Body.Close()
    }
} 



func handle_cert(cert *x509.Certificate) {
    fmt.Println(cert.Subject.CommonName)
}


// Worker function
func getcert(in chan WorkTodo,  out chan Status) {
    config := tls.Config{InsecureSkipVerify: true}
    // Keep waiting for work
    for {
        target := <- in
        conn, err := tls.Dial("tcp", target.target, &config)
        if err != nil {
            out <- Status{target.target, false}
            continue
        }
        err = conn.Handshake()
        if err != nil {
            out <- Status{target.target, false}
            continue
        }
        state := conn.ConnectionState()
        // TODO: store certificate
        for _, cert := range state.PeerCertificates {
            handle_cert(cert)
        }
        if state.HandshakeComplete {
            out <- Status{target.target, true}
        } else {
            out <- Status{target.target, true}
        }
        conn.Close()
    }
}


func main() {
    // Parse the commandline flags
    flag.Parse()
    fmt.Println(flag.NArg())
    if flag.NArg() != 1 {
        fmt.Println("Expected hostname")
        return
    }
    host := flag.Arg(0)

    // Make the worker chanels
    in := make(chan WorkTodo, 2 * *nworkers)
    out := make(chan Status, *nworkers)

    // Keep the work queue filled
    go fill_workqueue(in, host)

    //  Start the workers
    for i := 0; i < *nworkers; i++ {
        go getcert(in, out)
    }
    // Wait for results
    for {
        res := <- out
        if res.succes {
            fmt.Printf("OK: %s\n", res.host)
        }
    }


}
