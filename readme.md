# 微信聊天记录分析
## 1 原始素材路径
### txt_folder_path  #由留痕（MemoTrace）导出的微信聊天记录txt文件
### stop_word_path  # 停用词，例如“的”、“我”等，不计入统计
### custom_dict_path  # 自定义词组
### font_path  # 所需字体

## 2 导出路径
### content_folder_path  # 按发言人分类存放发言内容到json文件
### trace_data_folder_path  # 按天统计的trace bar data，用于app.flourish.studio上绘制动态条形图
### word_cloud_folder_path  # 高频词汇统计

## 3 过程控制
### content_save_mode # 是否保存群聊成员个人发言json文件
### trace_data_save_mode # 是否保存用于绘制动态条形图的excel文件
### word_cloud_save_mode # 是否保存高频词汇统计的词云jpg图片