# -*- coding: utf-8 -*-
import argparse
import configparser
import colorama
import xlsxwriter
from urllib.parse import urlparse
from prettytable import PrettyTable
import nuclei
import os
import sys
import time
import re
import requests
import codecs
import mmh3


# 当前软件版本信息
def banner():
    colorama.init(autoreset=True)
    print(colorama.Fore.LIGHTGREEN_EX + """
 _____      __       __  __   [*]云查询版           
|  ___|__  / _| __ _|  \/  | __ _ _ __  
| |_ / _ \| |_ / _` | |\/| |/ _` | '_ \ 
|  _| (_) |  _| (_| | |  | | (_| | |_) |
|_|  \___/|_|  \__,_|_|  |_|\__,_| .__/ 
                                 |_|   V1.1.3  
#Coded By Hx0战队  Update:2023.02.19""")
    logger_sw = config.get("logger", "logger")
    full_sw = config.get("full", "full")
    print(colorama.Fore.RED + "======基础配置=======")
    if logger_sw == "on":
        print(colorama.Fore.GREEN + "[*]日志状态:开启")
        sys.stdout = Logger("fofamap.log")
    else:
        print(colorama.Fore.RED + "[*]日志状态:关闭")
    if not query_host and not bat_host_file:
        if full_sw == "false":
            print(colorama.Fore.GREEN + "[*]搜索范围:一年内数据")
        else:
            print(colorama.Fore.RED + "[*]搜索范围:全部数据")
        print(colorama.Fore.GREEN + "[*]每页查询数量:{}条/页".format(config.getint("size", "size")))


# 查询域名信息
def search_domain(query_str, fields, no):
    start_page = 1
    end_page = 2
    print(colorama.Fore.GREEN + "[+] 正在查询第{}个目标：{}".format(no, query_str))
    database = get_api(query_str, start_page, end_page, fields)
    return database


# 打印信息
def print_domain():
    fields = 'ip,port,host,domain,icp,province,city'
    key_list = []
    pattern = "[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?"  # 匹配域名
    with open("scan_result.txt", "r+", encoding="utf-8") as f:
        data_lib = f.readlines()
    for data in data_lib:
        key = re.search(pattern, data)
        if key:
            key_list.append(key.group())
    key_list = set(key_list)
    database = []
    print(colorama.Fore.RED + "======域名查询=======")
    print(colorama.Fore.GREEN + "[+] 本次待查询任务数为{}，预计耗时{}s".format(len(key_list), len(key_list) * 1.5))
    no = 1
    for key in key_list:
        if re.search(r"(?<![\.\d])(?:\d{1,3}\.){3}\d{1,3}(?![\.\d])", key):  # 匹配IP
            query_str = 'ip="{}"'.format(key)
        else:
            query_str = '{}'.format(key)
        database = database + search_domain(query_str, fields, no)
        no += 1
        time.sleep(1.5)
    set_database = []
    for data in database:
        if data not in set_database:
            set_database.append(data)
    id = 1
    field = fields.split(",")
    field.insert(0, 'ID')
    field.insert(len(field), 'domain_screenshot')
    table = PrettyTable(field)
    table.padding_width = 1
    table.header_style = "title"
    table.align = "c"
    table.valign = "m"
    for item in set_database:
        if item[field.index("domain") - 1] != '':
            item.insert(0, id)
            item.insert(len(field), 'https://icp.chinaz.com/home/info?host={}'.format(item[field.index("domain")]))
            table.add_row(item)
            id += 1
    print(colorama.Fore.GREEN + '[+] 共计发现{}条域名信息'.format(id - 1))
    print(colorama.Fore.GREEN + '{}'.format(table))  # 打印查询表格


# 统计关键词出现频率
def word_count(word, file):
    a = file.split(word)
    return len(a) - 1


# 输出nuclei扫描统计结果
def result_count():
    with open("scan_result.txt", "r", encoding="utf-8") as f:
        file = f.readlines()
    file = "{}".format(file)
    critical = word_count("[critical]", file)
    high = word_count("[high]", file)
    medium = word_count("[medium]", file)
    low = word_count("[low]", file)
    info = word_count("[info]", file)
    print(colorama.Fore.RED + "======结果统计=======")
    print(colorama.Fore.GREEN + "本次共计扫描{}个目标，发现目标的严重程度如下：".format(aim))
    print(colorama.Fore.LIGHTRED_EX + "[+] [critical]:{}".format(critical))
    print(colorama.Fore.LIGHTYELLOW_EX + "[+] [high]:{}".format(high))
    print(colorama.Fore.LIGHTCYAN_EX + "[+] [medium]:{}".format(medium))
    print(colorama.Fore.LIGHTGREEN_EX + "[+] [low:]{}".format(low))
    print(colorama.Fore.LIGHTBLUE_EX + "[+] [info]:{}".format(info))


# 手动更新nuclei
def nuclei_update():
    print(colorama.Fore.RED + "====一键更新Nuclei=====")
    scan = nuclei.Scan()
    cmd = scan.update()
    print(colorama.Fore.GREEN + "[+] 更新命令[{}]".format(cmd))
    os.system(cmd)


# 调用nuclie进行扫描
def nuclie_scan(filename):
    print(colorama.Fore.RED + "=====Nuclei扫描======")
    scan = nuclei.Scan()
    print(colorama.Fore.GREEN + "[+] 即将启动nuclei对目标进行扫描")
    print(colorama.Fore.GREEN + "[+] 扫描引擎路径[{}]".format(scan.path))
    filename = "{}".format(filename).split(".")[0] + ".txt"
    print(colorama.Fore.GREEN + "[-] nuclie默认使用全扫描，是否改用自定义扫描功能？[Y/N][温馨提示：若要修改扫描目标，可在此时手动修改{}文件内容]".format(filename))
    switch = input()
    if switch == "Y" or switch == "y":
        print(colorama.Fore.GREEN + "[+] 正在调用nuclei对目标进行自定义扫描")
        print(colorama.Fore.GREEN + "[-] 请输入要使用的过滤器[1.tags 2.severity 3.author 4.templates 5.customize]")
        mode = input()
        if mode == "1":
            mode_v = "tags"
        elif mode == "2":
            mode_v = "severity"
        elif mode == "3":
            mode_v = "author"
        elif mode == "4":
            mode_v = "templates"
        else:
            mode_v = "customize"
        print(colorama.Fore.GREEN + "[+] 已选择[{}]过滤器".format(mode_v))
        if mode_v == "customize":
            print(colorama.Fore.GREEN + "[-] 请输入完整的自定义命令内容[例如：-tags cve -severity critical,high -author geeknik]")
            customize_cmd = input()
            cmd = scan.customize_cmd(filename, customize_cmd)
            print(colorama.Fore.GREEN + "[+] 本次扫描语句[{}]".format(cmd))
        else:
            print(colorama.Fore.GREEN + "[-] 请输入过滤器的内容[如：tech、cve、cms、fuzz、templates-path等]")
            value = input()
            print(colorama.Fore.GREEN + "[+] 过滤器内容为[{}]".format(value))
            cmd = scan.keyword_multi_target(filename, mode_v, value)
            print(colorama.Fore.GREEN + "[+] 本次扫描语句[{}]".format(cmd))
    else:
        print(colorama.Fore.GREEN + "[+] 正在调用nuclei对目标进行全扫描")
        cmd = scan.multi_target(filename)
        print(colorama.Fore.GREEN + "[+] 本次扫描语句：{}".format(cmd))
    time.sleep(1)
    os.system(cmd)
    print(colorama.Fore.GREEN + "[+]扫描完成，扫描结果保存为：scan_result.txt")
    result_count()  # 统计扫描结果
    print_domain()  # 查找拥有域名的IP


# 输出扫描目标
def out_file_scan(filename, database):
    scan_list = []
    for target in database:
        if "http" in target[1]:
            if target[1] == "http":
                scan_list.append("http://{}\n".format(target[0]))
            else:
                scan_list.append("{}\n".format(target[0]))
    scan_list = set(scan_list)
    print(colorama.Fore.GREEN + "[+] 已自动对结果做去重处理".format(filename))
    filename = "{}".format(filename).split(".")[0] + ".txt"
    with open(filename, "w+", encoding="utf-8") as f:
        for value in scan_list:
            f.write(value)
    print(colorama.Fore.GREEN + "[+] 文档输出成功！文件名为：{}".format(filename))
    global aim
    aim = len(scan_list)


# 输出excel表格结果
def out_file_excel(filename, database, scan_format):
    print(colorama.Fore.RED + "======文档输出=======")
    if scan_format:
        # 输出扫描格式文档
        out_file_scan(filename, database)
    else:
        field = config.get("fields", "fields").split(",")  # 获取查询参数
        column_lib = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L',
                      13: 'M', 14: 'N', 15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 21: 'U', 22: 'V', 23: 'W',
                      24: 'X', 25: 'Y', 26: 'Z'}
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:{}'.format(column_lib[len(field)]), 30)
        title_format = workbook.add_format(
            {'font_size': 14, 'border': 1, 'bold': True, 'font_color': 'white', 'bg_color': '#4BACC6',
             'align': 'center',
             'valign': 'center', 'text_wrap': True})
        content_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        i = 1
        row = 1
        col = 0
        for column in field:
            worksheet.write('{}1'.format(column_lib[i]), column, title_format)
            i += 1
        for item in database:
            for n in range(len(field)):
                worksheet.write(row, col + n, item[n], content_format)
            row = row + 1
        workbook.close()
        print(colorama.Fore.GREEN + "[+] 文档输出成功！文件名为：{}".format(filename))


# 调用fofa_api进行数据查询
def get_search(query_str, scan_format):
    start_page = config.getint("page", "start_page")
    end_page = config.getint("page", "end_page")
    size = config.get("size", "size")
    full = config.get("full", "full")
    if scan_format:
        fields = "host,protocol"  # 获取查询参数
    else:
        fields = config.get("fields", "fields")  # 获取查询参数
    print(colorama.Fore.RED + "======查询内容=======")
    print(colorama.Fore.GREEN + "[+] 查询语句：{}".format(query_str))
    print(colorama.Fore.GREEN + "[+] 查询参数：{}".format(fields))
    print(colorama.Fore.GREEN + "[+] 查询页数：{}-{}".format(start_page, end_page))
    print(colorama.Fore.YELLOW + "[-] 正在进行云查询，请稍后······")
    database = get_api(query_str, start_page, end_page, fields, size, full)
    if len(database) > 0 and '"error":true' in database[0]:
        fields = "Error"
    set_database = []
    for data in database:
        if data not in set_database:
            set_database.append(data)
    return set_database, fields


# 打印查询结果
def print_result(database, fields, scan_format):
    print(colorama.Fore.RED + "======查询结果=======")
    if scan_format:
        scan_list = []
        for target in database:
            if "http" in target[1]:
                if target[1] == "http":
                    scan_list.append(colorama.Fore.GREEN + "http://{}".format(target[0]))
                else:
                    scan_list.append(colorama.Fore.GREEN + "{}".format(target[0]))
        scan_list = set(scan_list)
        for value in scan_list:
            print(value)
    else:
        id = 1
        field = fields.split(",")
        field.insert(0, 'ID')
        table = PrettyTable(field)
        table.padding_width = 1
        table.header_style = "title"
        table.align = "c"
        table.valign = "m"
        for item in database:
            if type(item) == str:
                item = [item]
            if "title" in fields:
                title = "{}".format(item[field.index("title") - 1]).strip()
                if len(title) > 20:
                    title = title[:20] + "......"
                item[field.index("title") - 1] = title
            item.insert(0, id)
            table.add_row(item)
            id += 1
        print(colorama.Fore.GREEN + '{}'.format(table))  # 打印查询表格


# 批量查询
def bat_query(bat_query_file, scan_format):
    with open(bat_query_file, "r+", encoding="utf-8") as f:
        bat_str = f.readlines()
    id = 1
    total = len(bat_str)
    for query_str in bat_str:
        print(colorama.Fore.RED + "======批量查询=======")
        print(colorama.Fore.GREEN + "[+] 任务文件：{}".format(bat_query_file))
        print(colorama.Fore.GREEN + "[+] 任务总数：{}".format(total))
        print(colorama.Fore.GREEN + "[+] 当前任务：task-{}".format(id))
        query_str = "{}".format(query_str).replace("\n", "")
        database, fields = get_search(query_str, scan_format)
        # 输出excel文档
        filename = "task-{}.xlsx".format(id)
        out_file_excel(filename, database, scan_format)
        # 打印结果
        print_result(database, fields, scan_format)
        id += 1


# 调用云api进行数据查询
def get_api(query_str, start_page=1, end_page=2, fields="protocol,ip,port,title,host,domain,icp", size=100, full=False,
            host_merge=False):
    ip = config.get("CouldServer", "ip")
    port = config.get("CouldServer", "port")
    client_key = config.get("CouldServer", "key")
    data = {
        "query_str": query_str,
        "key": client_key,
        "start_page": start_page,
        "end_page": end_page,
        "fields": fields,
        "size": size,
        "full": full,
        "host_merge": host_merge
    }
    res = requests.post("http://{}:{}/api".format(ip, port), data=data)
    if res.status_code == 403:
        print(colorama.Fore.RED + "[!] 查询失败，请检查CouldServer的key是否正确")
        sys.exit(0)
    try:
        data = res.json()
        return data
    except:
        print(colorama.Fore.RED + "[!] 查询失败，可能服务端的FOFA-API-KEY错误或过期，请联系服务端管理员处理")
        sys.exit(0)


# 美化端口详情
def merge_port_detail(ports):
    set_database = []
    for port_info in ports:
        products = []
        for product in port_info['products']:
            products.append(product['product'])
        item = [port_info['port'], port_info['protocol'], ",".join(products)]
        set_database.append(item)
    table = PrettyTable(["id", "port", "protocol", "products"])
    table.padding_width = 1
    table.header_style = "title"
    table.align = "c"
    table.valign = "m"
    id = 1
    for item in set_database:
        item.insert(0, id)
        table.add_row(item)
        id += 1
    return table


# host聚合查询
def host_merge(query_host):
    try:
        data = get_api(query_str=query_host, host_merge=True)
        print(colorama.Fore.GREEN + "[+] 主机名:{}".format(data["host"]))
        print(colorama.Fore.GREEN + "[+] IP地址:{}".format(data["ip"]))
        print(colorama.Fore.GREEN + "[+] asn编号:{}".format(data["asn"]))
        print(colorama.Fore.GREEN + "[+] asn组织:{}".format(data["org"]))
        print(colorama.Fore.GREEN + "[+] 国家名:{}".format(data["country_name"]))
        print(colorama.Fore.GREEN + "[+] 国家代码:{}".format(data["country_code"]))
        print(colorama.Fore.GREEN + '[+] 端口详情:\n{}'.format(merge_port_detail(data["ports"])))  # 打印port聚合表格
        print(colorama.Fore.GREEN + "[+] 数据更新时间:{}".format(data["update_time"]))
    except Exception as e:
        print(colorama.Fore.RED + "[!] 错误:{}".format(e))


#  批量host聚合查询
def bat_host_query(bat_host_file):
    with open(bat_host_file, "r+", encoding="utf-8") as f:
        bat_host = f.readlines()
    id = 1
    total = len(bat_host)
    print(colorama.Fore.RED + "====批量Host查询=====")
    print(colorama.Fore.GREEN + "[+] 任务文件：{}".format(bat_host_file))
    print(colorama.Fore.GREEN + "[+] 任务总数：{}".format(total))
    for query_host in bat_host:
        print(colorama.Fore.YELLOW + "=======任务-{}========".format(id))
        host_merge(query_host.strip("\n"))
        id += 1
        time.sleep(0.1)


# 网站图标查询
def get_icon_hash(ico):
    obj = urlparse(ico)
    ico = "{}://{}".format(obj.scheme, obj.hostname)
    res = requests.get(url=ico, verify=False, timeout=30)
    res.encoding = res.apparent_encoding
    html = res.text
    ico_path = re.findall('rel="icon" href="(.*?)"', html, re.S)
    if ico_path:
        ico_url = "{}/{}".format(ico, ico_path[0])
    else:
        ico_url = "{}/favicon.ico".format(ico)
    res = requests.get(ico_url, verify=False, timeout=30)
    if res.status_code == 200:
        favicon = res.content
        icon_hash = mmh3.hash(
            codecs.lookup('base64').encode(favicon)[0])
        return 'icon_hash="{}"'.format(icon_hash)
    else:
        print(colorama.Fore.RED + "[-] 抱歉，系统暂时未找到该网站图标")
        exit(0)


# 日志功能
class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w+", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(
            "{}".format(message).replace("\033[91m", "").replace("\033[92m", "").replace("\033[93m", "").replace(
                "\033[94m", "").replace("\033[96m", "").replace("\033[31m", "").replace("\033[32m", "").replace(
                "\033[33m", "").replace(
                "\033[36m", "").replace(
                "\033[34m", "").replace("\033[0m", ""))

    def flush(self):
        pass


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    # 获取版本信息
    colorama.init(autoreset=True)
    # 初始化参数
    config = configparser.ConfigParser()
    # 读取配置文件
    config.read('fofa.ini', encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="SearchMap (A fofa API information collection tool)")
    parser.add_argument('-q', '--query', help='Fofa Query Statement')
    parser.add_argument('-hq', '--host_query', help='Host Merge Query')
    parser.add_argument('-bq', '--bat_query', help='Fofa Batch Query')
    parser.add_argument('-bhq', '--bat_host_query', help='Fofa Batch Host Query')
    parser.add_argument('-ico', '--icon_query', help='Fofa Favorites Icon Query')
    parser.add_argument('-s', '--scan_format', help='Output Scan Format', action='store_true')
    parser.add_argument('-o', '--outfile', default="fofa.xlsx", help='File Save Name')
    parser.add_argument('-n', '--nuclie', help='Use Nuclie To Scan Targets', action='store_true')
    parser.add_argument('-up', '--update', help='OneKey Update Nuclie-engine And Nuclei-templates', action='store_true')
    args = parser.parse_args()
    query_str = args.query
    query_host = args.host_query
    bat_query_file = args.bat_query
    bat_host_file = args.bat_host_query
    filename = args.outfile
    scan_format = args.scan_format
    is_scan = args.nuclie
    update = args.update
    ico = args.icon_query
    banner()
    if query_host:
        print(colorama.Fore.RED + "======Host聚合=======")
        host_merge(query_host)
    if bat_host_file:
        bat_host_query(bat_host_file)
    if query_str or bat_query_file or ico:
        if bat_query_file:
            bat_query(bat_query_file, scan_format)
        else:
            if ico:
                query_str = get_icon_hash(ico)
            # 获得查询结果
            database, fields = get_search(query_str, scan_format)
            # 输出excel文档
            out_file_excel(filename, database, scan_format)
            # 打印结果
            print_result(database, fields, scan_format)
        if update:
            nuclei_update()
        if scan_format and is_scan:
            nuclie_scan(filename)
