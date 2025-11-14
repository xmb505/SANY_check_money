#!/bin/bash

# 读取配置文件并执行命令的守护进程脚本

# 配置文件路径
CONFIG_FILE="./config/daemon.ini"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 配置文件 $CONFIG_FILE 不存在"
    exit 1
fi

# 从配置文件中读取参数
REC_TIME=$(grep "rec_time" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')
COMMAND=$(grep "command" "$CONFIG_FILE" | cut -d'=' -f2 | sed 's/^ *//' | sed 's/"//g' | sed "s/'//g")

# 检查是否成功读取到参数
if [ -z "$REC_TIME" ] || [ -z "$COMMAND" ]; then
    echo "错误: 无法从配置文件中读取必要的参数"
    exit 1
fi

echo "守护进程启动"
echo "重复时间: $REC_TIME 秒"
echo "执行命令: $COMMAND"
echo "按 Ctrl+C 停止守护进程"
echo "----------------------------------------"

# 无限循环执行命令
while true; do
    echo "$(date): 执行命令: $COMMAND"
    
    # 执行配置文件中的命令
    eval "$COMMAND"
    
    # 检查命令执行结果
    if [ $? -eq 0 ]; then
        echo "$(date): 命令执行成功"
    else
        echo "$(date): 命令执行失败"
    fi
    
    echo "$(date): 等待 $REC_TIME 秒后再次执行..."
    echo "----------------------------------------"
    
    # 等待指定的时间
    sleep "$REC_TIME"
done