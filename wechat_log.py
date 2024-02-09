import json
import os
import jieba
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from tqdm import tqdm
from time import sleep
from collections import Counter
from wordcloud import WordCloud


def create_folder(folder_path):
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        # 如果不存在，则创建文件夹
        os.makedirs(folder_path)
        print(f"文件夹创建成功: {folder_path}")
    else:
        print(f"文件夹已存在: {folder_path}")


def count_top_words(text, stop_word_path, custom_dict_path, top_n=30):
    # 使用jieba分词
    words = jieba.cut(text, HMM=True)
    stop_words = [' ', '[', ']', '【', '】', '(', ')', '（', '）']
    jieba.load_userdict(custom_dict_path)

    # 自定义停用词列表，可以根据需要扩展
    with open(stop_word_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        stop_words.append(line.strip())

    # 过滤停用词
    filtered_words = [word for word in words if word not in stop_words]

    # 使用Counter统计词频
    word_counter = Counter(filtered_words)

    # 获取最常见的top_n词语及其次数
    top_words = word_counter.most_common(top_n)

    return top_words


def get_file_names_in_folder(folder_path):
    # 使用 os.listdir 获取文件夹下所有文件和子文件夹的名称
    files = os.listdir(folder_path)

    # 过滤出文件的名称（排除子文件夹）
    file_names = [file for file in files if os.path.isfile(os.path.join(folder_path, file))]

    return file_names


def read_txt(txt_folder_path, stop_word_path, custom_dict_path,
             content_folder_path, trace_data_folder_path, word_cloud_folder_path,
             content_save_mode, trace_data_save_mode, word_cloud_save_mode, font_path):
    txt_file_list = get_file_names_in_folder(txt_folder_path)  # 读取文件夹下所有的txt文件
    for txt_file_name in tqdm(txt_file_list):  # 对于每一个聊天导出的txt
        sleep(0.1)
        print(f'\nnow:{txt_file_name}\n')

        txt_file_path = txt_folder_path + '/' + txt_file_name  # 合并原始文件夹路径和txt文件名，组成文件路径
        room_name = txt_file_name[:-4]  # 除去最后“.txt”四个字符就是群聊或联系人名称

        # 统计这个群聊有哪些人，在哪些日期有发言
        name_list = []  # 待提取的群聊成员名称列表
        date_list = []  # 待提取的有聊天记录的日期

        with open(txt_file_path, 'r', encoding='utf-8') as file:
            data = file.read()
            parts = data.split('\n\n202')  # 按“换行+202”为标志，将txt文件切分为parts，每一part为一个人发的一条消息
            for index, part in enumerate(parts):  # 对于某一条消息，一共有两行，第一行是日期、时间、名字的基础信息，第二行是文本，第三行偶尔出现，为引用内容
                lines = part.split('\n')  # 按换行切割每一行
                if index == 0:  # 第一条消息的“202”没有被切割，正常划分日期、名字
                    date = lines[0][:10]
                    name = lines[0][20:]
                else:  # 其余消息需要补上“202”
                    date = '202' + lines[0][:7]
                    name = lines[0][17:]
                if date not in date_list:  # 如果本条消息的发送者不在成员名称列表里，就加上
                    date_list.append(date)
                if name not in name_list:  # 如果本条消息的发送日期不在日期列表里，就加上
                    name_list.append(name)

        content_data = {}  # 创建一个字典用来存放每个人说了什么，key是人名，value是他在这个群里说过的所有的话
        trace_data = [['Name']]
        for date in date_list:
            trace_data[0].append(date)
        for name in name_list:
            content_data[name] = ''
            trace_data.append([name])
            for _ in range(len(date_list)):
                trace_data[name_list.index(name)+1].append(0)

        # 正式统计每个人，每天说了什么
        with open(txt_file_path, 'r', encoding='utf-8') as file:
            data = file.read()
            parts = data.split('\n\n202')
            print(f'\nfind trace_data\n')
            for index, part in tqdm(enumerate(parts)):
                lines = part.split('\n')
                # 第一行是日期、时间、名字
                if index == 0:
                    date = lines[0][:10]
                    name = lines[0][20:]
                else:
                    date = '202' + lines[0][:7]
                    name = lines[0][17:]
                # 第二行是文本
                context = lines[1]
                content_data[name] += context  # 将本条消息的文本，累加到发消息人的记录里
                trace_data[name_list.index(name) + 1][date_list.index(date) + 1] += len(context)

        if content_save_mode:
            content_file_path = content_folder_path + '/' + room_name + '.json'
            with open(content_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(content_data, json_file, ensure_ascii=False)

        if trace_data_save_mode:
            for i in range(len(name_list)):
                for j in range(len(date_list)):
                    if j > 0:
                        trace_data[i+1][j+1] += trace_data[i+1][j]

            df = pd.DataFrame(trace_data[1:], columns=trace_data[0])
            trace_file_path = trace_data_folder_path + '/' + room_name + '.xlsx'
            df.to_excel(trace_file_path, index=False)

        if word_cloud_save_mode:
            word_cloud_room_path = word_cloud_folder_path + '/' + room_name
            create_folder(word_cloud_room_path)

            for key, value in content_data.items():  # 对于每个人说过的话
                if len(value) > 10:  # 累计发言大于十个字才进行统计
                    # 设置每张图片的保存路径
                    word_cloud_file_path = word_cloud_room_path + '/' + key + '.png'

                    # 调用wordcloud绘制词云
                    wordcloud = WordCloud(width=1900, height=800, background_color='white',
                                          font_path=font_path).generate(value)

                    # 调用自己写的函数统计高频词
                    top_words = count_top_words(value, stop_word_path, custom_dict_path)
                    content_title = f'{key}在【{room_name}】中的高频词汇:\n（统计区间为{date_list[0]}-{date_list[-1]}）\n'
                    # 将词语和频次分别存进categories和values列表里，以便绘图
                    categories = []
                    values = []
                    for word, count in top_words:
                        if word != ' ' and word != '':
                            categories.append(word)
                            values.append(count)
                    # 绘制柱状图
                    paint(categories, values, content_title, word_cloud_file_path, wordcloud)


def paint(categories, values, content_title, word_cloud_file_path, wordcloud):
    rcParams["font.family"] = 'Microsoft YaHei'
    rcParams["font.size"] = 25
    plt.figure(figsize=(20, 20))

    # 添加第一个子图：词云
    plt.subplot(2, 1, 1)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  # 不显示坐标轴
    plt.title(content_title)

    # 添加第二个子图：条形图
    plt.subplot(2, 1, 2)
    plt.bar(categories, values, color='blue')
    for a, b, i in zip(categories, values, range(len(categories))):  # zip 函数
        plt.text(a, b + 0.01, "%d" % values[i], ha='center', fontsize=20)
    plt.xticks(rotation=300)
    plt.xlabel('words')
    plt.ylabel('count')
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)

    # 调整布局
    plt.tight_layout()

    # 保存到本地文件（png格式，也可以选择其他格式如pdf、svg等）
    plt.savefig(word_cloud_file_path)
    plt.close()


def bar(num, total):
    text = ''
    total_length = 20
    bar_length = round(num / total * total_length)
    for _ in range(bar_length):
        text += '>'
    return text


def main():
    # 原始素材路径
    txt_folder_path = './1_wechat_log_txt'
    stop_word_path = './2_support/cn_stopwords.txt'  # 停用词，例如“的”、“我”等，不计入统计
    custom_dict_path = './2_support/custom_dict.txt'  # 自定义词组
    font_path = './2_support/微软雅黑.ttf'

    # 导出路径
    content_folder_path = './3_out_content'  # 按发言人分类存放发言内容到json文件
    trace_data_folder_path = './4_out_trace_data'  # 按天统计的trace bar data
    word_cloud_folder_path = './5_out_word_cloud'  # 高频词汇统计
    create_folder(content_folder_path)
    create_folder(trace_data_folder_path)
    create_folder(word_cloud_folder_path)

    # 过程控制
    content_save_mode = True
    trace_data_save_mode = True
    word_cloud_save_mode = True

    read_txt(txt_folder_path, stop_word_path, custom_dict_path,
             content_folder_path, trace_data_folder_path, word_cloud_folder_path,
             content_save_mode, trace_data_save_mode, word_cloud_save_mode, font_path)


if __name__ == '__main__':
    main()
