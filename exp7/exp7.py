# exp7.py —— 编译原理实验七：LR(0) 分析器生成器（绝对可以通过！）
import sys
from typing import List, Set, Dict

# ==================== 数据结构定义 ====================
class Production:
    """表示一条产生式：左部 → 右部"""
    def __init__(self, left: str, right: List[str], pid: int):
        self.left = left          # 产生式左部（非终结符）
        self.right = right        # 产生式右部（符号列表，可能为空）
        self.id = pid             # 产生式编号（增广产生式为 0）


class Item:
    """LR(0) 项目：表示一个带圆点的位置，如 A → α·β"""
    def __init__(self, prod_id: int, dot: int):
        self.prod_id = prod_id    # 属于哪条产生式
        self.dot = dot            # 圆点位置（0 表示在最前面）

    def __eq__(self, other):
        return isinstance(other, Item) and self.prod_id == other.prod_id and self.dot == other.dot

    def __hash__(self):
        return hash((self.prod_id, self.dot))  # 支持放进 set 和 dict


class LR0State:
    """一个 LR(0) 状态 = 一组项目（项目集）"""
    def __init__(self, items: Set[Item]):
        self.items = frozenset(items)        # 用 frozenset 冻结，便于去重和哈希
        self.transitions: Dict[str, int] = {} # 转移函数：符号 → 目标状态编号
        self.id = -1                          # 状态编号（从 0 开始）

    def __hash__(self):
        return hash(self.items)

    def __eq__(self, other):
        return isinstance(other, LR0State) and self.items == other.items


# ==================== 读取文法文件（超级健壮版） ====================
def read_grammar(filename: str):
    """读取标准格式的文法文件，支持空产生式、多种箭头符号"""
    with open(filename, encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]  # 过滤空行

    i = 0
    non_cnt = int(lines[i]); i += 1
    non_terms = set(lines[i].split()); i += 1                  # 非终结符集合

    term_cnt = int(lines[i]); i += 1
    terms = set(lines[i].split()); i += 1                      # 终结符集合

    prod_cnt = int(lines[i]); i += 1
    prods = []

    # 读取每条产生式
    for _ in range(prod_cnt):
        line = lines[i]
        # 统一处理 -> 和 → 箭头
        line = line.replace("->", " ").replace("→", " ")
        parts = line.split()
        left = parts[0]
        right = parts[1:] if len(parts) > 1 else []            # 支持空产生式
        prods.append(Production(left, right, len(prods)))
        i += 1

    start_symbol = lines[i].strip()                            # 原开始符号

    # 自动增广文法：添加 S' → 原开始符号
    prods.insert(0, Production("S'", [start_symbol], 0))
    for j in range(1, len(prods)):
        prods[j].id = j                                        # 重新编号（增广后调整）

    return prods, non_terms, terms


# ==================== LR(0) 核心算法：闭包与转移 ====================
def closure(items: Set[Item], prods: List[Production], non_terms: Set[str]) -> Set[Item]:
    """计算项目集的闭包：如果圆点后是非终结符 B，加入所有 B → ·γ"""
    items = set(items)
    changed = True
    while changed:
        changed = False
        curr = list(items)  # 避免在迭代时修改集合
        for item in curr:
            r = prods[item.prod_id].right
            if item.dot >= len(r):
                continue                            # 圆点已在末尾
            B = r[item.dot]
            if B not in non_terms:
                continue                            # 不是非终结符，不扩展
            for p in prods:
                if p.left == B:
                    new_item = Item(p.id, 0)
                    if new_item not in items:
                        items.add(new_item)
                        changed = True
    return items


def goto(items: Set[Item], X: str, prods: List[Production], non_terms: Set[str]) -> Set[Item]:
    """计算 goto(I, X)：将圆点跨过 X 后求闭包"""
    moved = set()
    for item in items:
        r = prods[item.prod_id].right
        if item.dot < len(r) and r[item.dot] == X:
            moved.add(Item(item.prod_id, item.dot + 1))  # 圆点右移
    return closure(moved, prods, non_terms)


def build_lr0_states(prods: List[Production], non_terms: Set[str], terms: Set[str]) -> List[LR0State]:
    """构造 LR(0) 项目集规范族（所有状态）"""
    # 初始状态：包含 S' → .S 的闭包
    I0 = closure({Item(0, 0)}, prods, non_terms)

    states: List[LR0State] = []
    state_id_map: Dict[frozenset[Item], int] = {}   # 项目集 → 状态编号（用于去重）

    # 创建状态 0
    s0 = LR0State(I0)
    s0.id = 0
    states.append(s0)
    state_id_map[frozenset(I0)] = 0

    queue = [s0]  # BFS 队列

    while queue:
        cur = queue.pop(0)  # 取出当前状态

        # 收集当前状态中所有圆点后面的符号（可转移符号）
        symbols = set()
        for item in cur.items:
            r = prods[item.prod_id].right
            if item.dot < len(r):
                symbols.add(r[item.dot])

        # 对每个符号 X 计算 goto
        for X in symbols:
            next_set = goto(set(cur.items), X, prods, non_terms)
            if not next_set:
                continue

            frozen = frozenset(next_set)
            if frozen not in state_id_map:
                # 新状态：加入列表、队列，并建立转移
                new_state = LR0State(next_set)
                new_state.id = len(states)
                states.append(new_state)
                state_id_map[frozen] = new_state.id
                queue.append(new_state)
                cur.transitions[X] = new_state.id
            else:
                # 已存在：直接建立转移
                cur.transitions[X] = state_id_map[frozen]

    return states


# ==================== 判断是否为 LR(0) 文法 ====================
def is_lr0(states: List[LR0State], prods: List[Production], terms: Set[str]) -> bool:
    """检测是否存在移进-归约或归约-归约冲突"""
    for s in states:
        reduce_prod = None
        for item in s.items:
            if item.dot == len(prods[item.prod_id].right):  # 是归约项
                if reduce_prod is not None and reduce_prod != item.prod_id:
                    return False                            # 归约-归约冲突
                reduce_prod = item.prod_id

        if reduce_prod is not None:
            # 若有归约项，同时又对终结符有转移 → 移进-归约冲突
            for sym in s.transitions:
                if sym in terms:
                    return False
    return True


# ==================== 输出函数 ====================
def print_item_sets(states: List[LR0State], prods: List[Production]):
    """打印所有状态的项目集（美观格式）"""
    print("[LR(0) item set cluster]")
    for s in states:
        print(f"  I{s.id} :")
        sorted_items = sorted(s.items, key=lambda x: (x.prod_id, x.dot))
        for item in sorted_items:
            p = prods[item.prod_id]
            print("        " + p.left + " ->", end=" ")
            for j, sym in enumerate(p.right):
                if j == item.dot:
                    print(". ", end="")
                print(sym, end=" ")
            if item.dot == len(p.right):
                print(". ", end="")
            print()
        print()


def print_transitions(states: List[LR0State]):
    """打印状态转移函数"""
    print("[LR(0) state tran function]")
    trans = []
    for s in states:
        for sym in sorted(s.transitions):
            trans.append((s.id, sym, s.transitions[sym]))
    trans.sort()
    for src, sym, dst in trans:
        print(f"  {src} ,  {sym:<8} -> {dst}")
    print()


def write_lrtbl(states: List[LR0State], prods: List[Production], terms: Set[str], filename: str):
    """生成实验要求的 .lrtbl 分析表文件（即使不是LR(0)也生成，并给出警告）"""
    if not is_lr0(states, prods, terms):
        print("警告: 文法不是LR(0)文法，生成的分析表可能存在冲突！")

    out_name = filename.rsplit(".", 1)[0] + ".lrtbl"
    action = []
    goto = []

    for s in states:
        # Shift 动作（对终结符）
        for sym, tgt in s.transitions.items():
            if sym in terms:
                action.append((s.id, sym, f"s{tgt}"))

        # Reduce 和 Accept
        reduce_ids = []
        for item in s.items:
            if item.dot == len(prods[item.prod_id].right):
                if item.prod_id == 0:                     # S' → S .
                    action.append((s.id, "#", "acc"))
                else:
                    reduce_ids.append(item.prod_id)

        # 即使有多个归约项也输出（便于观察冲突）
        for reduce_id in reduce_ids:
            for t in terms:
                action.append((s.id, t, f"r{reduce_id}"))
            action.append((s.id, "#", f"r{reduce_id}"))

        # Goto 动作（对非终结符）
        for sym, tgt in s.transitions.items():
            if sym not in terms:
                goto.append((s.id, sym, tgt))

    # 排序保证输出顺序稳定
    action.sort(key=lambda x: (x[0], x[1]))
    goto.sort(key=lambda x: (x[0], x[1]))

    # 写入文件
    with open(out_name, "w", encoding="utf-8") as f:
        f.write(f"{len(action)}\n")
        for sid, sym, act in action:
            f.write(f"  {sid}   {sym}  {act}\n")
        f.write(f"{len(goto)}\n")
        for sid, sym, tgt in goto:
            f.write(f"  {sid}   {sym}   {tgt}\n")
    print(f"分析表已输出到文件: {out_name}")


# ==================== 主函数（增强健壮性） ====================
def main():
    if len(sys.argv) != 2:
        default_file = "exp7_grammer.txt"
        print(f"用法: python {sys.argv[0]} <文法文件>")
        print(f"未提供参数，尝试使用默认文件: {default_file}")
        filename = default_file
    else:
        filename = sys.argv[1]

    try:
        prods, non_terms, terms = read_grammar(filename)
        states = build_lr0_states(prods, non_terms, terms)

        print_item_sets(states, prods)
        print_transitions(states)
        print("文法是 LR(0) 文法！" if is_lr0(states, prods, terms) else "文法不是 LR(0) 文法！")
        print()
        write_lrtbl(states, prods, terms, filename)

    except FileNotFoundError:
        print(f"错误: 找不到文件 {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"运行出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()