from openai import OpenAI
import plugins.discord.tokenes as tokenes

client = OpenAI(
    # This is the default and can be omitted
    api_key=tokenes.gpt_token,
)
chat_history = [
            {"role": "system", "content": "你是一个智能助手,请用中文回复我"}
        ]
chat_start = [
            {"role": "system", "content": "你是一个智能助手,请用中文回复我"}
        ]

def clear_chat_history():
    chat_history = chat_start

    
# 生成回复,并添加到chat_history
def generate_reply(message):
    # chat_history 添加用户输入
    chat_history.append({"role": "user", "content": message})

    chat = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages = chat_history,
        )
    # print(chat)
    print(chat.choices[0].message.content)
    # chat_history 添加助手回复
    chat_history.append({"role": "assistant", "content": chat.choices[0].message.content})

    return chat.choices[0].message.content
