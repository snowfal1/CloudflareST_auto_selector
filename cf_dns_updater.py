import os
import re
import io
import csv
import requests
import json
import subprocess
import zipfile
from config.config import email, global_api_key, zone_id
from datetime import datetime

# 清除代理环境变量
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

# 在全局作用域编译正则表达式
IPV4_PATTERN = re.compile(
    r'^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
    r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
    r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
    r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$'
)

# 判断是否为有效的ipv4地址
def is_valid_ipv4(ip):
    return bool(IPV4_PATTERN.match(ip))

# 读取固定IP列表
def get_fixed_ips(): 
    with open ("./config/fixed_ips.txt","r",encoding="utf-8") as file:
        ip_list= [ip.strip() for ip in file.readlines()]
        ip_list=filter(is_valid_ipv4,ip_list)
        return list(ip_list)

# 下载并生成3ip.txt
def fetch_ips():
    print("开始下载并生成中转IP列表...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    session = requests.Session()
    try:
        response = session.get("https://zip.baipiao.eu.org/", headers=headers)
        response.raise_for_status()  # 抛出异常
    except requests.exceptions.RequestException as e:
        print(f"网络请求异常: {e}")
        return
    except Exception as e:
        print(f"下载ZIP文件时发生错误: {e}")
        return

    # 处理ZIP文件内容
    zip_data = io.BytesIO(response.content)
    valid_ips = set(get_fixed_ips())  # 初始化为固定IP列表

    try:
        with zipfile.ZipFile(zip_data, 'r') as archive:
            for file_name in archive.namelist():
                if file_name.endswith('.txt'):
                    with archive.open(file_name) as file:
                        for line in file:
                            ip = line.decode('utf-8').strip()
                            if is_valid_ipv4(ip):
                                valid_ips.add(ip)
    except zipfile.BadZipFile:
        print("下载的文件不是有效的ZIP文件")
        return

    # 写入最终的IP文件
    final_ip_path = '3ip.txt'
    with open(final_ip_path, 'w') as outfile:
        outfile.write('\n'.join(valid_ips))

    print(f"IP列表已保存到 {final_ip_path}，共获取 {len(valid_ips)} 个有效IP")

    # 清理会话
    session.close()

# 筛选并生成result.csv
def run_cloudflare_speedtest():
    print("测速并生成result.csv...")
    with open('./config/cmd.txt', 'r') as file:
        cmd = file.readline().strip().split()
    cmd.extend(['-p', '0'])
    subprocess.run(cmd)

    print("测速完成，生成result.csv文件")

# 读取result.csv文件中的IP地址
def get_ips():  
    ips = []
    with open("result.csv", "r",encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # skip header
        for row in csvreader:
            ips.append(row[0])
        return ips

# 获取Cloudflare DNS记录
def fetch_cloudflare_records():
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?page=1&per_page=20&order=type&direction=asc"
    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": global_api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return {}

    domains_details = response.json()
    results = domains_details.get("result", [])

    try:
        with open("./config/domains.txt", "r", encoding="utf-8") as file:
            domains_list = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("domains.txt文件不存在")
        return {}
    except Exception as e:
        print(f"读取domains.txt时发生错误: {e}")
        return {}
    
    record_ids = {result["name"]: result["id"] for result in results if result["name"] in domains_list}
    print(f"已获取 {len(record_ids)} 个Cloudflare DNS记录")

    return record_ids

# 获取config
def load_config_and_records():
    # 确保所有必要的配置项都存在
    if not email or not global_api_key or not zone_id:
        print("错误: 缺少必要的配置信息！")
        exit()

    return email, global_api_key, zone_id, fetch_cloudflare_records()

# 更新Cloudflare DNS记录
def update_cloudflare_dns(email, global_api_key, zone_id, domains):
    print("更新Cloudflare DNS记录...")
    ips = get_ips()
    if len(ips)>10: 
        return domains
    res_domains=domains.copy() #复制domains字典
    for idx, (domain, record_id) in enumerate(domains.items()):
        if idx >= len(ips):
            print(f"可用ip数量不足，截至域名: {domain}")
            #将剩余domains字典中的域名添加到not_updated_domains字典中
            break

        ip = ips[idx]
        print(f"Processing Domain[{idx + 1}] : {domain} with IP: {ip}")

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": global_api_key,
            "Content-Type": "application/json"
        }
        data = {
            "type": "A",
            "name": domain,
            "content": ip,
            "ttl": 60,
            "proxied": False
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        response = requests.put(url, headers=headers, data=json.dumps(data))
        res_domains.pop(domain, None)  # 从domains字典中删除已更新的域名
        print(response.json())
    return res_domains  # 返回未更新的域名

# 主函数
def main():
    fetch_ips()  # 下载并生成3ip.txt文件
    print("中转IP下载完成，开始筛选...")
    run_cloudflare_speedtest()  # 生成result.csv文件

    email, global_api_key, zone_id, domains = load_config_and_records() # 读取config.json文件
    domains = update_cloudflare_dns(email, global_api_key, zone_id, domains)
    while domains:
        print("未更新的域名: ", domains)
        print("\n")
        print("正在重新测速并更新剩余的域名...")
        run_cloudflare_speedtest()  # 重新生成result.csv文件
        domains = update_cloudflare_dns(email, global_api_key, zone_id, domains)
    
# 程序入口
if __name__=="__main__":
    main()
    print("3秒后自动退出程序")
    exit(3)
    
