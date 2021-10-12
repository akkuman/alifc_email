# alifc_email

## 主要特性

利用阿里的云函数发送电子邮件

## 使用场景

hw中的钓鱼邮件发送，一些邮服会解析出邮件的来源ip（此来源ip并不是邮服的ip，而是从客户端发送邮件时，邮服自动带上的客户端ip），对于这些来源ip可能会做一些风控。

本项目利用云函数出口ip较多来绕过这些风控

## 使用方法

首先根据[阿里云的文档](https://github.com/aliyun/fun/blob/master/docs/usage/installation-zh.md)进行 `fun` 的安装

clone 本仓库，然后使用 `fun local start` 进行本地测试

然后可以按照下面的说明部署到阿里云的函数计算

```
# 文档参考: https://github.com/alibaba/funcraft/blob/master/docs/usage/getting_started-zh.md
fun deploy
```

### 接口调用

```shell
curl --location --request POST 'http://localhost:8000/2016-08-15/proxy/emailsrv/sendmail/' \
--header 'Content-Type: application/json' \
--data-raw '{
	"host": "smtp.163.com",
	"username": "xxxx@163.com",
	"password": "xxx123",
	"mail_to": "test@qq.com",
	"subject": "我的测试邮件",
	"relay_to": "xxxx@163.com",
	"relay_name": "xxxx",
	"mail_body": "测试测试",
	"files": {
		"test.zip": "UEsDBBQAAAAIAEJzTFOHsYinhi8AAGwyAAAOABwAd25oZ3FxcXBzeS5"
	}
}'
```

### 参数说明

| 字段名称       | 字段说明                                                                    | 可选 |
|------------|-------------------------------------------------------------------------|----|
| host       | 邮服地址                                                                    | 否  |
| username   | 邮服用户名                                                                   | 否  |
| password   | 邮服密码                                                                    | 否  |
| mail_to    | 收件人邮箱                                                                   | 否  |
| subject    | 邮件主题                                                                    | 否  |
| relay_to   | 代发邮箱，一般留空，将会自动填充username的值，如果填写与username不同的邮箱，一些邮件软件将会显示由xx代发，会增大垃圾邮件概率 | 是  |
| relay_name | 发件人姓名                                                                   | 是  |
| mail_body  | 邮件内容，html或纯文本均可                                                         | 是  |
| files      | 附件列表，以文件名为键，base64后的文件内容为值                                              | 是  |
