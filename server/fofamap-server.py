import requests
from flask import Flask, request, jsonify, abort
import configparser
import fofa
import logging
from logging import handlers


class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }  # 日志级别关系映射

    def __init__(self, filename, level='info', when='D', backCount=3,
                 fmt='%(asctime)s - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)  # 设置日志格式
        self.logger.setLevel(self.level_relations.get(level))  # 设置日志级别
        sh = logging.StreamHandler()  # 往屏幕上输出
        sh.setFormatter(format_str)  # 设置屏幕上显示的格式
        th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backCount,
                                               encoding='utf-8')  # 往文件里写入#指定间隔时间自动生成文件的处理器
        # 实例化TimedRotatingFileHandler
        # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒
        # M 分
        # H 小时、
        # D 天、
        # W 每星期（interval==0时代表星期一）
        # midnight 每天凌晨
        th.setFormatter(format_str)  # 设置文件里写入的格式
        self.logger.addHandler(sh)  # 把对象加到logger里
        self.logger.addHandler(th)


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
log = Logger('server.log', level='debug')


# 主api接口
@app.route("/api", methods=['GET', 'POST'], endpoint='api')
def api():
    query_str = request.values.get('query_str')
    ip = request.remote_addr
    log.logger.info('[+]ip: {} - query_str: {} '.format(ip, query_str))
    key = request.values.get('key')
    server_key = config.get("CouldServer", "key")
    if key != server_key:
        abort(403)
    # 生成一个fofa客户端实例
    client = fofa.Client()
    start_page = request.values.get('start_page')
    end_page = request.values.get('end_page')
    fields = request.values.get('fields')  # 获取查询参数
    size = request.values.get('size')
    full = request.values.get('full')
    host_merge = request.values.get('host_merge')
    if host_merge == "True":
        url = "https://fofa.info/api/v1/host/{}?detail=true&email={}&key={}".format(query_str, email, user_key
                                                                                    , timeout=30)
        print(url)
        res = requests.get(url)
        database = res.json()
    else:
        if not size:
            size = 100
        if not full:
            full = False
        database = []
        for page in range(int(start_page), int(end_page)):  # 从第1页查到第N页
            try:
                data = client.get_data(query_str, page=page, fields=fields, size=size, full=full)  # 查询第page页数据
            except Exception as e:
                fields = "Error"
                data = {"results": ["{}".format(e)]}
            database = database + data["results"]
    print(database)
    return jsonify(database)


if __name__ == '__main__':
    print("+---------------------+")
    print("|Fofamap-Server-V1.1.3|")
    print("+---------------------+")
    config = configparser.ConfigParser()
    # 读取配置文件
    config.read('fofa.ini', encoding="utf-8")
    ip = config.get("CouldServer", "ip")
    port = config.get("CouldServer", "port")
    email = config.get("userinfo", "email")
    user_key = config.get("userinfo", "key")
    app.run(host=ip, port=port)
