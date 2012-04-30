package main

import (
    "fmt"
    "crypto/tls"
)

const NWORKERS = 64

type Status struct {
    host    string
    succes  bool
}

func getcert(in chan string,  out chan Status) {
    config := tls.Config{InsecureSkipVerify: true}
    // Keep waiting for work
    for {
        target := <- in
        conn, err := tls.Dial("tcp", target, &config)
        if err != nil {
            out <- Status{target, false}
            continue
        }
        err = conn.Handshake()
        if err != nil {
            out <- Status{target, false}
            continue
        }
        state := conn.ConnectionState()
        // TODO: store certificates
        if state.HandshakeComplete {
            out <- Status{target, true}
        } else {
            out <- Status{target, true}
        }
        conn.Close()
    }
}


func main() {
    in := make(chan string, 256)
    out := make(chan Status, 256)
    //  Start the workers
    for i := 0; i < NWORKERS; i++ {
        go getcert(in, out)
    }
    // Push the work
    for i := 0; i < 256; i++ {
        in <- fmt.Sprintf("69.171.229.%d:443", i)
    }
    // Wait for results
    for i := 0; i < 256; i++ {
        res := <- out
        if res.succes {
            fmt.Printf("OK: %s\n", res.host)
        } else {
            fmt.Printf("FAILED: %s\n", res.host)
        }
    }


}
