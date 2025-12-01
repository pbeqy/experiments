import sys
from typing import List, Tuple, Dict

class Production:
    def __init__(self, left: str, right: List[str], pid: int):
        self.left = left
        self.right = right
        self.id = pid

def read_grammar(filename: str) -> Tuple[List[Production], str]:
    with open(filename, encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    i = 0
    int(lines[i]); i += 1
    non_terms = lines[i].split(); i += 1
    int(lines[i]); i += 1
    terms = lines[i].split(); i += 1
    prod_cnt = int(lines[i]); i += 1

    prods = []
    for pid in range(prod_cnt):
        line = lines[i].replace("->", " ").replace("→", " ")
        parts = line.split()
        left = parts[0]
        right = parts[1:] if len(parts) > 1 else []
        prods.append(Production(left, right, pid + 1))
        i += 1

    start_symbol = lines[i].strip()
    prods.insert(0, Production("S'", [start_symbol], 0))  # 增广
    return prods, start_symbol

def read_lrtable(filename: str) -> Tuple[Dict[Tuple[int, str], str], Dict[Tuple[int, str], int]]:
    with open(filename, encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    i = 0
    action_count = int(lines[i]); i += 1
    action = {}
    for _ in range(action_count):
        parts = lines[i].split()
        state, sym, act = int(parts[0]), parts[1], parts[2]
        action[(state, sym)] = act
        i += 1

    goto_count = int(lines[i]); i += 1
    goto = {}
    for _ in range(goto_count):
        parts = lines[i].split()
        state, sym, target = int(parts[0]), parts[1], int(parts[2])
        goto[(state, sym)] = target
        i += 1

    return action, goto

def analyze_one_string(sentence: str, prods: List[Production], action: dict, goto: dict, test_id: int):
    tokens = sentence.split() if sentence.strip() else []
    tokens.append("#")
    ip = 0
    state_stack = [0]
    symbol_stack: List[str] = []
    step = 1

    print(f"\n========== 测试用例 {test_id}: {' '.join(tokens[:-1]) or 'ε'} ==========")
    print(f"{'步数':<4} {'状态栈':<25} {'符号栈':<20} {'剩余输入':<25} {'动作'}")
    print(f"{step:<4} {' '.join(map(str, state_stack)):<25} {''.join(symbol_stack):<20} "
          f"{' '.join(tokens[ip:]):<25} {'初始状态'}")

    while True:
        step += 1
        s = state_stack[-1]
        a = tokens[ip]

        key = (s, a)
        if key not in action:
            print(f"{step:<4} {' '.join(map(str, state_stack)):<25} {''.join(symbol_stack):<20} "
                  f"{' '.join(tokens[ip:]):<25} **ERROR: 无动作**")
            print(f"××× 分析失败！在状态 {s} 上遇到符号 '{a}' 无对应动作")
            return False

        act = action[key]

        if act == "acc":
            print(f"{step:<4} {' '.join(map(str, state_stack)):<25} {''.join(symbol_stack):<20} "
                  f"{' '.join(tokens[ip:]):<25} acc")
            print("√√√ 分析成功！该句子属于文法\n")
            return True

        elif act.startswith('s'):
            t = int(act[1:])
            state_stack.append(t)
            symbol_stack.append(a)
            ip += 1
            print(f"{step:<4} {' '.join(map(str, state_stack)):<25} {''.join(symbol_stack):<20} "
                  f"{' '.join(tokens[ip:]):<25} {act} (移进)")

        elif act.startswith('r'):
            rid = int(act[1:])
            prod = prods[rid]
            beta_len = len(prod.right)

            # 弹出 |β| 个符号和状态
            for _ in range(beta_len):
                if state_stack: state_stack.pop()
                if symbol_stack: symbol_stack.pop()

            symbol_stack.append(prod.left)
            prev_state = state_stack[-1]
            gkey = (prev_state, prod.left)

            if gkey not in goto:
                print(f"ERROR: GOTO[{prev_state},{prod.left}] 未定义！")
                return False

            new_state = goto[gkey]
            state_stack.append(new_state)

            prod_str = f"{prod.left} -> {' '.join(prod.right) if prod.right else 'ε'}"
            print(f"{step:<4} {' '.join(map(str, state_stack)):<25} {''.join(symbol_stack):<20} "
                  f"{' '.join(tokens[ip:]):<25} reduce by {rid}: {prod_str}")

def main():
    if len(sys.argv) != 4:
        print("用法: python exp9.py <文法文件> <分析表.lrtbl> <输入文件(支持多行)>")
        print("示例: python exp9.py exp7_grammer.txt exp7_grammer.lrtbl input.txt")
        return

    grammar_file, table_file, input_file = sys.argv[1], sys.argv[2], sys.argv[3]

    prods, _ = read_grammar(grammar_file)
    action, goto = read_lrtable(table_file)

    with open(input_file, encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        print("输入文件为空！")
        return

    print(f"正在分析 {len(lines)} 个输入串...\n")

    for idx, line in enumerate(lines, 1):
        analyze_one_string(line, prods, action, goto, idx)

if __name__ == "__main__":
    main()