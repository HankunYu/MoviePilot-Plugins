## Infuse nfo 简介修复

CDATA标签是XML中的一种特殊标签，用于包含不需要转义的文本内容。但是不清楚什么原因，infuse无法正确读取nfo中的CDATA标签，导致媒体简介空白。

### 配置

启用后将根据每次入库事件自动触发脚本，去除nfo中的CDATA标签。
也可以配置全媒体库nfo修复目录，开启运行一次后将对输入的路径下所有nfo文件进行CDATA标签去除。

### 已知BUG

- 当MP因为更新重启后，Discord插件会无法载入，需要再手动重启一次MP。
- 未设置GPT回应对应用户/频道，导致bot一直跟webhook消息聊天。
- GPT对话过长未处理，导致消息发送失败。
- 莫名其妙错误导致GPT对话无法使用（在长时间开启对话后，大约一个礼拜？）

