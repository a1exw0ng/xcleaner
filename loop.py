from time import strftime, sleep, localtime

import redis
import requests

from test_sserver import test_all

xserver_ip = '106.14.224.61'


class _list(list):
    def foreach(self, func):
        for element in self:
            func(element)
        return self

    def map(self, func):
        return _list([func(element) for element in self])

    def select(self, func):
        return _list(filter(func, self))

    def count(self, func):
        return len(list(filter(func, self)))


def get_server_cnt():
    resp = requests.get('http://{}/admin?action=getall'.format(xserver_ip))
    if resp:
        json = resp.json()
        getall = json[0].get('getall')
        if getall and isinstance(getall, dict):
            return getall.get('count')
        else:
            return -1
    return -1


def put_right_time():
    rmd = int(strftime('%M')) % 10
    rmd == 0 or sleep(60 * (10 - rmd) - int(strftime('%S')))


def each_loop():
    print('[{}] check started: ######'.format(strftime("%Y-%m-%d %H:%M:%S", localtime())))

    try:
        # _thread.start_new_thread(hb_check_loop, ())
        cnt0 = get_server_cnt()
        while 1:
            if cnt0 == 0:
                requests.get('http://{}/servers'.format(xserver_ip),
                             headers={'access-token': 'b25seS1mb3ItZmV3LXBlcnNvbnMtdGhhdC1yZWFsbHktbmVlZA'})
            sleep(0.1)
            cnt1 = get_server_cnt()
            if cnt1 == cnt0:
                if cnt1 >= 3:
                    test_all(xserver_ip)
                    break
                else:
                    requests.get('http://{}/admin?action=flushdb'.format(xserver_ip))
                    requests.get('http://{}/servers'.format(xserver_ip),
                                 headers={'access-token': 'b25seS1mb3ItZmV3LXBlcnNvbnMtdGhhdC1yZWFsbHktbmVlZA'})
            else:
                cnt0 = cnt1
    except Exception as e:
        print(str(e))
    finally:
        print('[{}] check finished: #####\n'.format(strftime("%Y-%m-%d %H:%M:%S", localtime())))
        rmd = int(strftime('%M')) % 10
        rmd != 0 or sleep(62 - int(strftime('%S')))


def hb_check_loop():
    import datetime
    c2 = redis.Redis(host='52.69.4.86', port=6379, db=1, password='njust2006')
    c3 = redis.Redis(host='52.69.4.86', port=6379, db=2, password='njust2006')

    to_del = _list(c3.keys()).map(lambda key: (key, c3.get(key.decode('utf-8')).decode('utf-8'))).select(
        lambda item: (
                         datetime.datetime.utcnow() - datetime.datetime.strptime(item[1],
                                                                                 '%Y-%m-%d %H:%M:%S')).seconds > 360)

    to_del.foreach(lambda k: c2.delete(k[0].decode('utf-8')))


def main():
    while 1:
        put_right_time()
        each_loop()


if __name__ == '__main__':
    main()
    # hb_check_loop()
