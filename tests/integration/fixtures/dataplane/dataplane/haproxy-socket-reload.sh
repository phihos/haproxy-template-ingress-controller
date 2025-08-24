#!/bin/sh

echo reload | nc local:/etc/haproxy/haproxy-master.sock
