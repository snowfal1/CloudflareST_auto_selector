## 项目概述

**项目名称**: CloudflareSpeedTest_Auto_Selector

**描述**: 简单的自动优选第三方反代IP的工具，配合定时任务实现Windows平台上的自动优选第三方反代IP。该项目利用 [XIU2](https://github.com/XIU2) 大佬的开源项目 [CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest) ，自动从一个第三方资源下载中转IP，筛选出活跃的IP，然后自动更新到Cloudflare上解析的DNS记录。

---

### 准备:

- Python
- `requests` 库
- [CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest/releases)
- 在 `Cloudflare`上解析好的域名

### 安装:

1. 克隆项目到本地。
2. 使用pip安装所需的Python库: `pip install requests`
3. 确保 `CloudflareST.exe` 在项目的根目录或在系统PATH中，请通过 [CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest/releases) 下载合适的版本

---

## 使用教程

#### config文件夹配置:

1. 配置 `config.py` 文件前，请在Cloudflare上创建一定数量的域名解析(10个以下)，并将域名按行排列复制到 `domains.txt` 文件中，**注意不要开启域名代理服务(小云朵）！**
2. `config.json` 中，`email`为你的Cloudflare账户邮箱，`global_api_key` 可在Cloudflare官网的  [用户API 令牌](https://dash.cloudflare.com/profile/api-tokens)  界面查看并复制，`zone_id` 在**对应域名管理概述页面的右下角**找到区域 ID复制到。
3. `cmd.txt` 中存放默认的  `CloudflareST.exe` 执行指令，需注意 `-f 3ip.txt -p 0` 指令为必须存在的指令，分别指向了IP文件与程序结束指令，其中-url 后面的参数可自行替换为自己常用的测速地址。默认的 `-dn 5 -tl 200 -sl 10` 指令意味着只筛选5个最终ip(`-dn 5`)，延迟取200以下(`-tl 200`)，下载速度取10 MB/S 以上(`-sl 10`)，可根据需求自行更改添加，相关文档  [CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest?tab=readme-ov-file#-%E8%BF%9B%E9%98%B6%E4%BD%BF%E7%94%A8)
4. (可选)`fixed_ips.txt` 为额外固定的IP，可自行添加，程序每次运行都会使用你设置的IP。

#### 使用:

1. 在项目根目录下运行 `python cf_dns_updater.py`。
2. 程序将自动下载中转IP、筛选IP、测速，并更新DNS记录。
3. 如果使用打包版本，配置好`config.py`与`domains.txt`之后，直接运行`cf_dns_updater.exe` 。

---

## 第三方工具说明

该项目使用了 `CloudflareST.exe`，一个开源的Cloudflare CDN节点测速筛选工具。该工具提供了测速并将结果输出到CSV文件的功能。

**相关链接**: [CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest)

感谢大佬提供的第三方反代IP

**第三方中转节点来源**: https://zip.baipiao.eu.org

---

## 常见问题 (FAQ)

**Q**: 如何实现自动优选？

**A**: 配置好所有内容后打包 `cf_dns_updater.py` 为可执行文件，或者设置一个bat批处理文件执行python脚本，然后在Windows的任务计划程序中添加定时/开机运行任务，或者借助一些第三方定时运行程序的工具实现此目的。

**Q**: 程序执行时出现错误怎么办?

**A**: 请检查你的 `config.py`是否已按照文档中的说明进行了正确配置。

**Q**: `CloudflareST.exe`程序应该怎么放置?

**A**: 放置在根目录即可，仅需要 `CloudflareST.exe` 一个可执行文件即可。
