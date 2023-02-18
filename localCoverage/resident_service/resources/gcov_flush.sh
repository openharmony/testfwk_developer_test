#!/bin/sh
SERVER_NAME=$1

# pid=`pgrep -l $SERVER_NAME |awk '{print $1}'`
ip_addrs=`pgrep -f $SERVER_NAME`
echo $ip_addrs
kill -SIGUSR2 $ip_addrs