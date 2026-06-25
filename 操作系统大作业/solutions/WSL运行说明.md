# 操作系统大作业 WSL 运行说明

## 1. 轮次公平哲学家进餐

```bash
cd /mnt/d/桌面/操作系统大作业
gcc solutions/philosopher_round.c -o solutions/philosopher_round -pthread
./solutions/philosopher_round
```

预期现象：每一轮中 5 个哲学家都恰好进餐一次，然后才进入下一轮。

## 2. 生成进程上下文切换记录表

如果输入文件名是 `a(1).txt`：

```bash
cd /mnt/d/桌面/操作系统大作业
chmod +x solutions/parse_switch.sh
./solutions/parse_switch.sh "a(1).txt" "进程上下文切换记录表.csv"
```

如果已将输入文件改名为 `a.txt`：

```bash
./solutions/parse_switch.sh a.txt "进程上下文切换记录表.csv"
```

生成的 CSV 文件可以用 Excel、WPS 或 LibreOffice Calc 打开。

## 3. rCore 内核运行

```bash
cd /mnt/d/桌面/操作系统大作业/rCore-Tutorial-v3-ch3\(1\)/rCore-Tutorial-v3-ch3/os
make run
```

如果 WSL 中安装的是 Ubuntu 20.04，`apt` 默认安装的 QEMU 可能是 `4.2.1`。本项目原检查脚本要求 QEMU 主版本号不低于 7，但本实验使用的 `virt` 机器和 RustSBI 启动方式在 QEMU 4.2.1 下也可运行，因此可将 `os/scripts/qemu-ver-check.sh` 中的 `MINIMUM_MAJOR_VERSION` 调整为 `4`。

运行输出中应能看到 `Switch #1`、`Switch #2` 等进程切换记录块。  
如果需要保存日志：

```bash
make run > ../../../../rCore运行结果.txt
```

保存后的日志可以继续作为第 2 题脚本输入：

```bash
cd /mnt/d/桌面/操作系统大作业
./solutions/parse_switch.sh rCore运行结果.txt "进程上下文切换记录表.csv"
```
