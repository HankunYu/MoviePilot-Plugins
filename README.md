# MoviePilot-Plugins
MoviePilot官方插件市场：https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/main/

### 使用

添加 https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins/main/ 到 PLUGIN_MARKET

请别使用版本0.x开头的插件，还在开发中...

---

### [Discord 消息推送插件](plugins/discord/README.md)

通过discord webhook推送MoviePilot的消息到discord频道中。
使用discord bot发送命令，加入OpenAI token后，可以使用GPT-3.5进行对话。

</br>

### [Infuse nfo 简介修复](plugins/rmcdata/README.md)

通过去除nfo中的CDATA标签修复infuse无法读取nfo内容导致媒体简介空白的问题。

</br>

### [Bangumi 同步](plugins/bangumi/README.md)

同步MoviePilot的观看记录到 Bangumi 收藏中。
自动订阅/下载 Bangumi 收藏的"想看"条目。
更改本地动漫 NFO文件评分为Bangumi评分。
更改订阅页面的评分为Bangumi评分。

需要申请Bangumi API Key，申请地址：https://next.bgm.tv/demo/access-token

</br>

### [弹幕刮削](plugins/danmu/README.md)

自动刮削新入库文件，可以全局文件刮削。
使用弹弹Play弹幕库刮削弹幕到本地转为ass文件。
.danmu为刮削出来的纯弹幕，.withDanmu为原生字幕与弹幕合并后的文件。方便不支持双字幕的播放器使用。

由于平台api改版，正在申请中……目前插件无法使用。
