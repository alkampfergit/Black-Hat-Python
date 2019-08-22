#original file is in https://github.com/paramiko/paramiko/blob/master/demos/forward.py
import getpass
import os
import socket
import select
import sys
import threading
import paramiko
from optparse import OptionParser

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

SSH_PORT = 22
DEFAULT_PORT = 4000

HELP = """\
Set up a reverse forwarding tunnel across an SSH server, using paramiko. A
port on the localhost machine (given with -l) is forwarded across an SSH session
back to a remote machine:port specified with parameter -r.

Example call to reach in remote desktop remotemachine from sshserver in localhost:9000

C:\Python27\python.exe .\rforward2.py -u username -p ****** -r remotemachine:3389 -l 9000 sshserver
"""

def parse_options():
    global g_verbose

    parser = OptionParser(usage='usage: %prog [options] <ssh-server>[:<server-port>]',
                          version='%prog 1.0', description=HELP)
    parser.add_option('-l', '--local-port', action='store', type='int', dest='local_port',
                       default=DEFAULT_PORT,
                       help='local port where to setup forwarding (default %s)' % DEFAULT_PORT)
    parser.add_option('-u', '--user', action='store', type='string', dest='user',
                      default=getpass.getuser(),
                      help='username for SSH authentication (default: %s)' % getpass.getuser())
    parser.add_option('', '--no-key', action='store_false', dest='look_for_keys', default=True,
                      help='don\'t look for or use a private key file')
    parser.add_option('-p', '--password', action='store', dest='password', default=False,
                      help='password to connect to the host')
    parser.add_option('-r', '--remote', action='store', type='string', dest='remote', default=None, metavar='host:port',
                      help='remote host and port to forward to')
    options, args = parser.parse_args()

    if len(args) != 1:
        parser.error('Incorrect number of arguments.' + str(args))
    if options.remote is None:
        parser.error('Remote address required (-r).')

    g_verbose = True
    server_host, server_port = get_host_port(args[0], SSH_PORT)
    remote_host, remote_port = get_host_port(options.remote, SSH_PORT)
    return options, (server_host, server_port), (remote_host, remote_port)

def get_host_port(spec, default_port):
    "parse 'hostname:22' into a host and port, with the port optional"
    args = (spec.split(':', 1) + [default_port])[:2]
    args[1] = int(args[1])
    return args[0], args[1]

class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

class Handler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel(
                "direct-tcpip",
                (self.chain_host, self.chain_port),
                self.request.getpeername(),
            )
        except Exception as e:
            verbose(
                "Incoming request to %s:%d failed: %s"
                % (self.chain_host, self.chain_port, repr(e))
            )
            return
        if chan is None:
            verbose(
                "Incoming request to %s:%d was rejected by the SSH server."
                % (self.chain_host, self.chain_port)
            )
            return

        verbose(
            "Connected!  Tunnel open %r -> %r -> %r"
            % (
                self.request.getpeername(),
                chan.getpeername(),
                (self.chain_host, self.chain_port),
            )
        )
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)

        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        verbose("Tunnel closed from %r" % (peername,))

def verbose(s):
    if g_verbose:
        print(s)

def forward_tunnel(local_port, remote_host, remote_port, transport):
    # this is a little convoluted, but lets me configure things for the Handler
    # object.  (SocketServer doesn't give Handlers any way to access the outer
    # server normally.)
    class SubHander(Handler):
        chain_host = remote_host
        chain_port = remote_port
        ssh_transport = transport

    ForwardServer(("", local_port), SubHander).serve_forever()

def main():
    options, server, remote = parse_options()
    print('Connecting to ssh host %s:%d' % (server[0], server[1]))

    try:
        print('Creating transport to %s:%d' % (server[0], server[1]))      
        transport = paramiko.Transport((server[0], server[1]))

        # Command for paramiko-1.7.7.1
        print('connecting transport to %s:%d with username %s' % (server[0], server[1], options.user))    
        transport.connect(hostkey  = None,
            username = options.user,
            password = options.password,
            pkey     = None)
        print('Connection successfully')
    except Exception, e:
        print('Forwarding request to %s:%d failed: %s' % (server[0], server[1], e))
        return

    try:
        print('Forwarding local port %s to remote %s:%d' % (options.local_port, remote[0], remote[1]))
        forward_tunnel(options.local_port, remote[0], remote[1], transport)
    except KeyboardInterrupt:
        print ('Port forwarding stopped.')
        sys.exit(0)

if __name__ == '__main__':
    main()
    
    