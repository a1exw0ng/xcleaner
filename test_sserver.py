import asyncio
import base64
import platform
import subprocess
import time
import inspect

import redis
import requests
from aiohttp import ClientSession
from aiosocks.connector import ProxyConnector, ProxyClientRequest


def get_cur_time():
    if platform.system() == 'Windows':
        return time.clock()
    else:
        return time.time()


def run_in_event_loop(func):
    def wrapper(*args, **kwargs):
        start = get_cur_time()
        if inspect.iscoroutinefunction(func):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(func(*args, **kwargs))
        else:
            result = func(*args, **kwargs)
        end = get_cur_time()
        return result, end - start

    return wrapper


@run_in_event_loop
async def test_access(shared_session):
    try:
        async with shared_session.get('https://www.google.com', proxy='socks5://127.0.0.1:1080', timeout=5) as resp:
            return resp.status
    except:
        return -1


@run_in_event_loop
def test_access_2():
    import urllib
    import socks
    from sockshandler import SocksiPyHandler

    try:
        opener = urllib.request.build_opener(SocksiPyHandler(socks.SOCKS5, "127.0.0.1", 1080))
        x = opener.open("http://www.google.com/", timeout=5)
        return x.getcode()
    except:
        return -1


def del_server(xserver_ip, server):
    requests.get('http://{}/admin?action=del->{}'.format(xserver_ip, server))


def get_server_info(xserver_ip, server):
    try:
        resp = requests.get('http://{}/admin?action=get->{}'.format(xserver_ip, server))
        server_info = resp.json()[0].get('get->{}'.format(server))
        return server_info
    except:
        return {}


def get_servers(xserver_ip):
    try:
        resp = requests.get('http://{}/admin?action=getall'.format(xserver_ip))
        keys = resp.json()[0].get('getall').get('keys')
        return keys
    except:
        return []


def flush_config_db(xserver_ip):
    r = redis.Redis(host=xserver_ip, port=6379, db=0, password='njust2006')
    r.flushdb()


def set_config_row(xserver_ip, server, config):
    r = redis.Redis(host=xserver_ip, port=6379, db=0, password='njust2006')
    r.set(server, config)


def test_single_server(shared_session, server_info, xserver_ip):
    server = server_info.get('server')
    port = server_info.get('server_port')
    try:
        password = base64.b64decode(server_info.get('password')).decode('utf-8')
    except:
        password = server_info.get('password')
    method = server_info.get('method')

    cmd = 'sslocal -s %s -p %s -l 1080 -k "%s" -m %s' % (server, port, password, method)
    _process = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.5)
    try:
        sum_duration = 0
        deleted = False
        for _ in range(10):
            status, duration = test_access_2()
            sum_duration += duration
            if status != 200:
                del_server(xserver_ip, server)
                print('cannot access, delete: ', server)
                deleted = True
                break
        if not deleted:
            print("%-18s %.3f" % (server, sum_duration / 10))
            if sum_duration / 10 > 1:
                del_server(xserver_ip, server)
                print('high delay, delete: ', server)
    except Exception as e:
        print(e)
    finally:
        _process.terminate()
        kill_f_process()
        time.sleep(0.5)


def kill_f_process():
    if platform.system() == 'Windows':
        cmd = "for /f \"tokens=5\" %a in ('netstat -aon ^| find \"1080\" ^| find \"LISTENING\"') do taskkill /f /pid %a"
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        p.wait()
    else:
        cmd0 = "netstat -nlp | grep :1080 | awk '{print $7}' | awk -F\"/\" '{ print $1 }'"
        out_bytes = subprocess.check_output(cmd0, shell=True)
        if out_bytes:
            pid = out_bytes.decode('utf-8')
            print("pid: {} killed.".format(pid))
            cmd = "kill -9 {}".format(pid)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            p.wait()


def test_all(xserver_ip):
    conn = ProxyConnector(remote_resolve=True)
    shared_session = ClientSession(connector=conn, request_class=ProxyClientRequest)

    for key in get_servers(xserver_ip):
        server_info = get_server_info(xserver_ip, key)
        test_single_server(shared_session, server_info, xserver_ip)
        print('*******************************************')
    shared_session.close()


if __name__ == '__main__':
    test_all('106.14.224.61')
