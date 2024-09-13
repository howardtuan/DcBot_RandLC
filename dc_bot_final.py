import discord
import random
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# GraphQL 查詢隨機題目
def get_all_titles():
    url = "https://leetcode.com/api/problems/all/"
    slugs = []
    try:
        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        r_json = response.json()
        for slug in r_json["stat_status_pairs"]:
            slugs.append(slug["stat"]["question__title_slug"])
    return slugs

def get_quest_info(title):
    query = """
    query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    boundTopicId\n    title\n    titleSlug\n    content\n    translatedTitle\n    translatedContent\n    isPaidOnly\n    difficulty\n    likes\n    dislikes\n    isLiked\n    similarQuestions\n    contributors {\n      username\n      profileUrl\n      avatarUrl\n      __typename\n    }\n    langToValidPlayground\n    topicTags {\n      name\n      slug\n      translatedName\n      __typename\n    }\n    companyTagStats\n    codeSnippets {\n      lang\n      langSlug\n      code\n      __typename\n    }\n    stats\n    hints\n    solution {\n      id\n      canSeeDetail\n      __typename\n    }\n    status\n    sampleTestCase\n    metaData\n    judgerAvailable\n    judgeType\n    mysqlSchemas\n    enableRunCode\n    enableTestMode\n    envInfo\n    libraryUrl\n    __typename\n  }\n}\n
    """
    body = {"operationName":"questionData",
            "variables":{"titleSlug":title},
            "query":query}

    url = "https://leetcode.com/graphql"
    try:
        response = requests.post(url, json=body)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        r_json = response.json()
        return r_json["data"]["question"]

def parseContent(content):
    if content is None:
        return None
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text()

def parseTags(tags):
    return ", ".join([tag['name'] for tag in tags])

# 取得隨機 LeetCode 題目的詳細信息
def get_random_leetcode_question():
    slugs = get_all_titles()
    if not slugs:
        return None

    random_slug = random.choice(slugs)
    quest_json = get_quest_info(random_slug)
    
    if quest_json:
        id = quest_json['questionFrontendId']
        title = quest_json['title']
        titleSlug = quest_json['titleSlug']
        content = parseContent(quest_json['content'])
        isPaidOnly = quest_json['isPaidOnly']
        difficulty = quest_json['difficulty']
        likes = quest_json['likes']
        dislikes = quest_json['dislikes']
        tags = parseTags(quest_json['topicTags'])
        question_url = f"https://leetcode.com/problems/{titleSlug}/description/"
        return {
            "id": id,
            "title": title,
            "content": content,
            "isPaidOnly": isPaidOnly,
            "difficulty": difficulty,
            "likes": likes,
            "dislikes": dislikes,
            "tags": tags,
            "question_url": question_url
        }
    else:
        return None

# 根據難易度返回顏色
def get_difficulty_color(difficulty):
    if difficulty == "Easy":
        return 0x00FF00  # 綠色
    elif difficulty == "Medium":
        return 0xFFFF00  # 黃色
    elif difficulty == "Hard":
        return 0xFF0000  # 紅色
    else:
        return 0xFFFFFF  # 預設為白色

@client.event
async def on_ready():
    print('目前登入身份：', client.user)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 如果訊息內容是 "抽"
    if message.content == '抽':
        question_data = get_random_leetcode_question()
        
        if question_data:
            # 根據難度設置顏色
            embed_color = get_difficulty_color(question_data['difficulty'])

            # 建立嵌入訊息
            embed = discord.Embed(
                title=f"LeetCode 隨機抽題：{question_data['title']}",
                url=question_data['question_url'],
                description=f"ID: {question_data['id']}",
                color=embed_color  # 使用設置好的顏色
            )

            embed.add_field(name="難度", value=question_data['difficulty'], inline=True)
            embed.add_field(name="是否付費題", value="是" if question_data['isPaidOnly'] else "否", inline=True)
            embed.add_field(name="喜歡", value=question_data['likes'], inline=True)
            embed.add_field(name="不喜歡", value=question_data['dislikes'], inline=True)
            embed.add_field(name="Tags", value=question_data['tags'], inline=False)
            embed.add_field(name="題目內容", value=(question_data['content'][:500] + "...") if len(question_data['content']) > 500 else question_data['content'], inline=False)

            await message.channel.send(embed=embed)
        else:
            await message.channel.send("抱歉，無法獲取題目。請稍後再試！")

# 請替換為你自己的 Discord Bot Token
client.run('你的 Discord Bot Token')
