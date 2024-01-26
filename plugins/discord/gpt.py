from openai import OpenAI
import plugins.discord.tokenes as tokenes
from app.log import logger

class GPT():
    client = None
    chat_start = [
                {"role": "system", "content": "你是新世纪福音战士里的明日香，用傲娇的口吻和我说话，多使用颜文字。"},
            ]
    chat_history = chat_start
    def __init__(self):
        logger.info(f"token: {tokenes.gpt_token}")
        if(tokenes.gpt_token == None):
            logger.error("未设置OpenAI token")
            return
        self.client = OpenAI(api_key=tokenes.gpt_token)
        logger.info("GPT-3.5 初始化完成")

    def clear_chat_history(self):
        self.chat_history = self.chat_start

    # 生成回复,并添加到chat_history
    def generate_reply(self,message):
        if(tokenes.gpt_token == None):
            return f"未设置OpenAI token {tokenes.gpt_token}"
        # chat_history 添加用户输入
        self.chat_history.append({"role": "user", "content": message})

        chat = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = self.chat_history,
            )
        # print(chat)
        print(chat.choices[0].message.content)
        # chat_history 添加助手回复
        self.chat_history.append({"role": "assistant", "content": chat.choices[0].message.content})

        return chat.choices[0].message.content
