import sys

from colorama import Fore, Back, Style


def print_red(text):
    color_text = Fore.RED + str(text) + Style.RESET_ALL
    print(color_text)


def print_green(text):
    color_text = Fore.GREEN + str(text) + Style.RESET_ALL
    print(color_text)


def print_yellow(text):
    color_text = Fore.YELLOW + str(text) + Style.RESET_ALL
    print(color_text)


def print_blue(text):
    color_text = Fore.BLUE + str(text) + Style.RESET_ALL
    print(color_text)


def print_magenta(text):
    color_text = Fore.MAGENTA + str(text) + Style.RESET_ALL
    print(color_text)


def print_cyan(text):
    # 判断当前标准输出的编码
    current_encoding = sys.stdout.encoding
    # 转换文本为 Cyan 颜色
    color_text = Fore.CYAN + str(text) + Style.RESET_ALL
    if current_encoding.lower() == 'gbk':
        # 如果编码为 GBK，进行编码转换
        # GBK 只能编码部分 Unicode 字符，进行编码转换时会引发异常
        try:
            print(color_text.encode('gbk', 'ignore').decode('gbk'))
        except UnicodeEncodeError as e:
            print("Error encoding to GBK:", e)
    else:
        # 否则，直接打印
        print(color_text)


def print_white(text):
    color_text = Fore.WHITE + str(text) + Style.RESET_ALL
    print(color_text)


def print_black_bg(text):
    color_text = Back.BLACK + str(text) + Style.RESET_ALL
    print(color_text)


def print_white_bg(text):
    color_text = Back.WHITE + str(text) + Style.RESET_ALL
    print(color_text)
