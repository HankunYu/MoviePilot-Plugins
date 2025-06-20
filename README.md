# MoviePilot-Plugins
MoviePilot官方插件市场：https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/main/

### 使用

添加 https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins/main/ 到 PLUGIN_MARKET


---

### [Discord 消息推送插件](plugins.v2/discord/README.md)

通过discord webhook推送MoviePilot的消息到discord频道中。
支持Discord Bot功能，可以直接在Discord中发送下载、搜索、订阅等命令。
加入OpenAI token后，可以使用GPT-3.5进行对话。

支持命令：
- 下载 /download
- 搜索 /search  
- 订阅 /subscribe

</br>

### [Bangumi 同步](plugins.v2/bangumi/README.md)

同步MoviePilot的观看记录到 Bangumi 收藏中。
自动订阅/下载 Bangumi 收藏的"想看"条目。
更改本地动漫 NFO文件评分为Bangumi评分。
更改订阅页面的评分为Bangumi评分。

需要申请Bangumi API Key，申请地址：https://next.bgm.tv/demo/access-token

支持自定义识别词替换，用于识别 Bangumi 标题与 TMDB 标题的互相识别。

</br>

### [弹幕刮削](plugins.v2/danmu/README.md)

自动刮削新入库文件，可以全局文件刮削。
使用弹弹Play弹幕库刮削弹幕到本地转为ass文件。
.danmu为刮削出来的纯弹幕，.withDanmu为原生字幕与弹幕合并后的文件。方便不支持双字幕的播放器使用。

支持UI手动刮削，根据文件路径进行弹幕刮削。
支持文件hash和TMDB ID匹配，提高识别准确率。

</br>

### [自定义识别词助手](plugins.v2/identifierhelper/README.md)

可视化管理自定义识别词，支持标签分类。
支持分类管理和子分类创建，方便整理不同类型的识别词。

</br>

### [BD Remuxer](plugins.v2/bdremuxer/README.md)

BD重新封装工具。

**注意：此插件吃性能，不建议在低性能设备上使用。**

</br>

### [Infuse nfo 简介修复](plugins/rmcdata/README.md)

通过去除nfo中的CDATA标签修复infuse无法读取nfo内容导致媒体简介空白的问题。

启用后将根据每次入库事件自动触发脚本，去除nfo中的CDATA标签。
也可以配置全媒体库nfo修复目录，开启运行一次后将对输入的路径下所有nfo文件进行CDATA标签去除。
