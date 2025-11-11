#!/bin/bash

# 设置下载目录
#DOWNLOAD_DIR="/d/LLM_models_storage/ModelScope"
#DOWNLOAD_DIR="/e"
#DOWNLOAD_DIR="/g"
DOWNLOAD_DIR="/d/models"

# 创建日志目录
mkdir -p "$DOWNLOAD_DIR/logs"
LOG_FILE="$DOWNLOAD_DIR/logs/download_$(date +%Y%m%d_%H%M%S).log"

# 取消代理
git config --global http.proxy http://proxyuser:proxypwd@proxy.server.com:8080
git config --global --unset http.proxy
git config --global --unset https.proxy
git config --global --unset-all http.proxy
git config --global --unset-all https.proxy
#git config --global --unset socks5_proxy

# 模型列表
MODELS=(
#QWEN-CODER
   
    #"Qwen3"-https://www.modelscope.cn/collections/Qwen3-9743180bdc6b48
    "Qwen/Qwen3-0.6B"
    "Qwen/Qwen3-1.7B"
    "Qwen/Qwen3-4B"
    #"Qwen/Qwen3-8B"
    #...
    #"DS-r1"-https://www.modelscope.cn/collections/DeepSeek-R1-c8e86ac66ed943
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    #"deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    #"..."

)

# 格式化文件大小的函数
format_size() {
    local size=$1
    if ((size < 1024)); then
        echo "$size B"
    elif ((size < 1024*1024)); then
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1024}") KB"
    elif ((size < 1024*1024*1024)); then
        echo "$(awk "BEGIN {printf \"%.2f\", $size/(1024*1024)}") MB"
    else
        echo "$(awk "BEGIN {printf \"%.2f\", $size/(1024*1024*1024)}") GB"
    fi
}

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取目录大小的函数
get_dir_size() {
    local dir=$1
    if [ -d "$dir" ]; then
        local size=$(du -sb "$dir" | cut -f1)
        format_size $size
    else
        echo "N/A"
    fi
}

# 确保git-lfs已安装
if ! command -v git-lfs &> /dev/null; then
    log "Error: git-lfs is not installed. Please install it first."
    exit 1
fi

# 安装/初始化git-lfs
git lfs install

# 切换到下载目录
cd "$DOWNLOAD_DIR" || {
    log "Error: Could not change to download directory $DOWNLOAD_DIR"
    exit 1
}

# 下载每个模型
for model in "${MODELS[@]}"; do
    log "======================================"
    log "Starting download of $model"
    start_time=$(date +%s)
    
    # 检查是否已经存在该目录
    model_dir=$(basename "$model")
    initial_size=$(get_dir_size "$model_dir")
    
    if [ -d "$model_dir" ]; then
        log "Directory $model_dir already exists. Attempting to update..."
        log "Initial size: $initial_size"
        cd "$model_dir"
        git pull
        git lfs pull
        cd ..
    else
        # 克隆新仓库
        # git clone https://www.modelscope.cn/Qwen/Qwen2.5-Coder-0.5B.git
        if git clone "https://www.modelscope.cn/$model"; then
        
            log "Successfully cloned $model"
        else
            log "Error: Failed to clone $model"
            continue
        fi
    fi
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    final_size=$(get_dir_size "$model_dir")
    
    # 计算时间格式
    hours=$((duration / 3600))
    minutes=$(( (duration % 3600) / 60 ))
    seconds=$((duration % 60))
    
    log "Download Statistics for $model:"
    log "- Time taken: ${hours}h ${minutes}m ${seconds}s"
    [ "$initial_size" != "N/A" ] && log "- Initial size: $initial_size"
    log "- Final size: $final_size"
    
    # 如果是新下载，计算下载速度
    if [ "$initial_size" = "N/A" ] && [ $duration -gt 0 ]; then
        size_bytes=$(du -sb "$model_dir" | cut -f1)
        speed=$(( size_bytes / duration ))
        speed_formatted=$(format_size $speed)
        log "- Average download speed: $speed_formatted/s"
    fi
    
    log "Completed processing $model"
    echo "----------------------------------------"
done

# 输出总结信息
total_size=$(get_dir_size "$DOWNLOAD_DIR")
log "All downloads completed"
log "Total size of all models: $total_size"


