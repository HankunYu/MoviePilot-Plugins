    
from app.log import logger

try:
    from openai import OpenAI
except ImportError:
    logger.error("OpenAI导入失败")
    
try:
    import openai
    logger.info("openai导入成功,版本: " + openai.__version__)
except ImportError:
    logger.error("openai导入失败")
class GPT():
    client = None
    gpt_token = None
    chat_start = [
                {"role": "system", "content": "用傲娇的口吻和我说话，可以使用一些颜文字。"},
            ]
    chat_history = chat_start
    def __init__(self, token = None):
        self.gpt_token = token
        if(self.gpt_token == None):
            logger.error(f"未设置OpenAI token")
            return
        self.client = OpenAI(api_key=self.gpt_token)
        logger.info("GPT 初始化完成")

    def clear_chat_history(self):
        self.chat_history = self.chat_start

    # 生成回复,并添加到chat_history
    def generate_reply(self,message):
        if(self.gpt_token == None):
            return f"未设置OpenAI token"
        # chat_history 添加用户输入
        self.chat_history.append({"role": "user", "content": message})

        chat = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = self.chat_history,
            )
        # chat_history 添加助手回复
        self.chat_history.append({"role": "assistant", "content": chat.choices[0].message.content})

        return chat.choices[0].message.content
