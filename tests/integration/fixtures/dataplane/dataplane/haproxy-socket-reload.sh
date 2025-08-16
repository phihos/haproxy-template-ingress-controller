#!/usr/bin/env bash

echo reload | socat stdio unix-connect:/etc/haproxy/haproxy-master.sock
