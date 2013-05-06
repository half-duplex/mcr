#!/usr/bin/env python3

import os
import pwd
import time
import struct
import socket
import asyncore
import subprocess

dc = '|'  #delimiter character - eventually: '\n'
ec = '\n' #end character       - eventually: '\0'
work_path = '/run/mcd/'
servers = []

def srv_allow(uid,server):
    if server == 'a' or server == 'b':
        if uid == 1000:
            return True
    if server == 'c':
        if uid == 0:
            return True
    return False

class server_job(asyncore.dispatcher_with_send):
    def __init__(self,server_name,uid,gid):
        global servers
        if not srv_allow(uid,server_name):
            raise Exception('User not allowed to start server')
        if not os.path.exists(work_path + str(uid)):
            os.makedirs(work_path + str(uid))
        os.chown(work_path + str(uid),uid,gid)
        os.chmod(work_path + str(uid),448)
        socket_path = work_path + str(uid) + '/' + server_name
        new_cmd = ['/usr/bin/sudo']
        new_cmd.append('-u#'+str(uid))
        new_cmd.append('-g#'+str(gid))
        new_cmd.append('-n')
        new_cmd.append('--')
        new_cmd.append('dtach')
        new_cmd.append('-n')
        new_cmd.append(socket_path)
        new_cmd.append('java')
        new_cmd.append('-Xmx2G')
        new_cmd.append('-XX:+DisableExplicitGC')
        new_cmd.append('-XX:+AggressiveOpts')
        new_cmd.append('-jar')
        new_cmd.append('server.jar')
        subprocess.call(new_cmd, shell=False, cwd='/')
        new_sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        new_sock.connect(socket_path)
        asyncore.dispatcher_with_send.__init__(self,new_sock)
        self.log = []
        self.read_in = ''
        self.clients = []
        self.server_name = server_name
        servers.append(self)
        self.send((chr(1)+chr(3)+(chr(0)*8)).encode("utf-8"))
    def handle_read(self):
        data = self.recv(512)
        if data:
            self.read_in += data.decode("utf-8")
            read_find = self.read_in.find('\n')
            while read_find > -1:
                self.process_line(self.read_in[:read_find])
                self.read_in = self.read_in[read_find+1:]
                read_find = self.read_in.find('\n')
    def process_line(self,gotline):
        gotline = str(int(time.time()*1000*1000)) + dc + gotline
        self.log.append(gotline)
        del(self.log[32768:])
        for i in reversed(range(len(self.clients))):
            try:
                self.clients[i].send_line('msg' + dc + self.server_name + dc + gotline)
            except:
                del(self.clients[i])
    def handle_close(self):
        global servers
        for i in reversed(range(len(servers))):
            if servers[i] == self:
                del(servers[i])
        self.close()

class client_job(asyncore.dispatcher_with_send):
    read_in = ''
    def __init__(self,sock):
        asyncore.dispatcher_with_send.__init__(self,sock)
        self.pid, self.uid, self.gid = struct.unpack('3i', sock.getsockopt(socket.SOL_SOCKET, 17, struct.calcsize('3i')))
    def handle_read(self):
        data = self.recv(512)
        if data:
            self.read_in += data.decode("utf-8")
            read_find = self.read_in.find(dc)
            while read_find > -1:
                self.process_line(self.read_in[:read_find])
                self.read_in = self.read_in[read_find+1:]
                read_find = self.read_in.find(dc)
    def process_line(self,gotline):
        global servers
        cmd = gotline.split(dc)
        if len(cmd) == 1:
            if cmd[0] == "daemon_quit":
                if self.uid == 0:
                    exit(0)
            if cmd[0] == "quit":
                self.close()
            if cmd[0] == "show":
                return_list = 'serverlist'
                for i in servers:
                    return_list += dc + i.server_name
                self.send_line(return_list)
        if len(cmd) == 2:
            if cmd[0] == "start" and cmd[1].isalnum():
                for i in servers:
                    if i.server_name == cmd[1]:
                        self.send_line('start' + dc + 'already_running' + dc + cmd[1])
                        return 1
                try:
                    new_server = server_job(cmd[1],self.uid,self.gid)
                    self.send_line('start' + dc + 'done' + dc + cmd[1])
                except:
                    self.send_line('start' + dc + 'error' + dc + cmd[1])
            if cmd[0] == "detach":
                for i in servers:
                    for j in reversed(range(len(i.clients))):
                        if i.clients[j] == self:
                            del(i.clients[j])
                            self.send_line('detach' + dc + 'done' + dc + cmd[1])
                            return 0
                self.send_line('detach' + dc + 'not_attached' + dc + cmd[1])
            if cmd[0] == "attach":
                for i in servers:
                    if i.server_name == cmd[1]:
                        i.clients.append(self)
            if cmd[0] == "stop":
                for i in servers:
                    if i.server_name == cmd[1]:
                        i.send((chr(0)+chr(1)+chr(3)+(chr(0)*7)).encode("utf-8"))
        if len(cmd) == 3:
            if cmd[0] == "get_lines":
                try:
                    for i in servers:
                        if i.server_name == cmd[1]:
                            return_list = 'log' + dc + cmd[1] + dc + 'ok'
                            for j in reversed(range(min(len(i.log),int(cmd[2])))):
                                return_list += dc + i.log[j]
                            self.send_line(return_list)
                            return
                except:
                    self.send_line('log' + dc + cmd[1] + dc + 'error')
            if cmd[0] == "get_after":
                try:
                    for i in servers:
                        if i.server_name == cmd[1]:
                            return_list_tmp = []
                            for j in reversed(i.log):
                                if int(j.split(dc)[0]) > int(cmd[2]):
                                    return_list_tmp.append(i.log[j])
                                else:
                                    break
                            return_list = 'log' + dc + cmd[1] + dc + 'ok'
                            for j in reversed(return_list_tmp):
                                return_list += dc + j
                            self.send_line(return_list)
                            return
                except:
                    self.send_line('log' + dc + cmd[1] + dc + 'error')
    def send_line(self,sendline):
        self.send((sendline + ec).encode("utf-8"))

class client_listen(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(work_path + 'daemon')
        os.chmod(work_path + 'daemon',511)
        self.listen(5)
    def handle_accepted(self, sock, addr):
        client_job(sock)

if os.path.exists(work_path):
    if os.path.exists(work_path + 'daemon'):
        sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        try:
            sock.connect(work_path + 'daemon')
            sock.send(('daemon_quit' + ec).encode("utf-8"))
        except:
            pass
        sock.close()
        del(sock)
        os.unlink(work_path + 'daemon')
else:
    os.makedirs(work_path)

client_listen()
asyncore.loop()
