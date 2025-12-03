import argparse
import time
parser = argparse.ArgumentParser(description="Python Server")
parser.add_argument("--id", type=str, default='', help="The id number.")
args = parser.parse_args()

def log_info(id, info):
    with open(f"../taskLogs/{id}.log", 'a', encoding='utf-8') as f:
        f.write(f'{info}\n')

if __name__ == "__main__":
    start = time.time()
    # 循环在运行 5 秒后自动退出
    while time.time() - start < 5:
        time.sleep(1)
        log_info(args.id, f'{time.strftime("%Y-%m-%d %H:%M:%S")} main')
