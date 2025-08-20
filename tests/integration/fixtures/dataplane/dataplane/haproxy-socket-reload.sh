#!/bin/sh

echo reload | socat stdio unix-connect:/etc/haproxy/haproxy-master.sock
