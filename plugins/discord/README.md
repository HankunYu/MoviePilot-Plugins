### 配置

目前只支持webhook的方式，需要在discord服务器中创建一个webhook，然后将webhook的url填入插件配置中。
站点地址可以自行填写，也可以留空。如果填写了站点地址，那么在discord中点击消息时会跳转到相应页面。

跟原版一样支持各类消息通知开关。

新增discord bot，需要自行注册一个bot并获取token然后添加到自己服务器上。
步骤可参考 https://hackmd.io/@lio2619/B1PB2yB2c
需要注意添加以下权限：
- bot
- messages.read
- application.commands
嫌麻烦可以都勾上

目前指令支持：
- 下载 /download
- 搜索 /search
- 订阅 /subscribe

直接@bot会使用GPT进行聊天

### Todo

- [X] 添加discord bot支持
- [X] 支持使用GPT聊天以及交互
- [X] 支持从discord直接发送命令