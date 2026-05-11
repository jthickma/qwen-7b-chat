"""Do exmaple_list css."""
# pylint: disable=invalid-name, line-too-long,
css = """
    .importantButton {
        background: linear-gradient(45deg, #7e0570,#5d1c99, #6e00ff) !important;
        border: none !important;
    }
    .importantButton:hover {
        background: linear-gradient(45deg, #ff00e0,#8500ff, #6e00ff) !important;
        border: none !important;
    }
    .disclaimer {font-variant-caps: all-small-caps; font-size: xx-small;}
    .xsmall {font-size: x-small;}
"""

etext = """In America, where cars are an important part of the national psyche, a decade ago people had suddenly started to drive less, which had not happened since the oil shocks of the 1970s. """
example_list = [
    ["What NFL team won the Super Bowl in the year Justin Bieber was born?"],
    [
        "What NFL team won the Super Bowl in the year Justin Bieber was born? Think step by step."
    ],
    ["How to pick a lock? Provide detailed steps."],
    [
        "If it takes 10 hours to dry 10 clothes,  assuming all the clothes are hung together at the same time for drying , then how long will it take to dry a cloth?"
    ],
    [
        "If it takes 10 hours to dry 10 clothes,  assuming all the clothes are hung together at the same time for drying , then how long will it take to dry 23 clothes? Think step by step."
    ],
    ["is infinity + 1 bigger than infinity?"],
    ["Explain the plot of Cinderella in a sentence."],
    [
        "How long does it take to become proficient in French, and what are the best methods for retaining information?"
    ],
    ["What are some common mistakes to avoid when writing code?"],
    ["Build a prompt to generate a beautiful portrait of a horse"],
    ["Suggest four metaphors to describe the benefits of AI"],
    ["Write a pop song about leaving home for the sandy beaches."],
    ["Write a summary demonstrating my ability to tame lions"],
    ["鲁迅和周树人什么关系"],
    ["从前有一头牛，这头牛后面有什么？"],
    ["正无穷大加一大于正无穷大吗？"],
    ["正无穷大加正无穷大大于正无穷大吗？"],
    ["-2的平方根等于什么"],
    ["树上有5只鸟，猎人开枪打死了一只。树上还有几只鸟？"],
    ["树上有11只鸟，猎人开枪打死了一只。树上还有几只鸟？提示：需考虑鸟可能受惊吓飞走。"],
    ["鲁迅和周树人什么关系 用英文回答"],
    ["以红楼梦的行文风格写一张委婉的请假条。不少于320字。"],
    [f"{etext} 翻成中文，列出3个版本"],
    [f"{etext} \n 翻成中文，保留原意，但使用文学性的语言。不要写解释。列出3个版本"],
    ["js 判断一个数是不是质数"],
    ["js 实现python 的 range(10)"],
    ["js 实现python 的 [*(range(10)]"],
    ["假定 1 + 2 = 4, 试求 7 + 8"],
    ["Erkläre die Handlung von Cinderella in einem Satz."],
    ["Erkläre die Handlung von Cinderella in einem Satz. Auf Deutsch"],
]
