#!/bin/bash
# 每日科技新闻摘要 - 完整版
# 包含：RSS、YouTube、Twitter、GitHub、B站

set -e

# ============================================
# 配置
# ============================================
WORKSPACE=/home/ubuntu/.openclaw/workspace
SKILL_DIR=$WORKSPACE/skills/tech-news-digest
CONFIG_DIR=$WORKSPACE/config
ARCHIVE_DIR=$WORKSPACE/archive/daily-digest
SCRIPTS_DIR=$WORKSPACE/scripts
DATE=$(date +%Y%m%d)
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')

# 输出文件
RSS_OUTPUT=/tmp/daily-rss-$DATE.json
YOUTUBE_OUTPUT=/tmp/daily-youtube-$DATE.json
MERGED_OUTPUT=/tmp/daily-merged-$DATE.json
SUMMARY_OUTPUT=/tmp/daily-summary-$DATE.md

# ============================================
# 日志函数
# ============================================
log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

log_section() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

# ============================================
# 1. RSS 抓取（tech-news-digest）
# ============================================
fetch_rss() {
    log_section "📊 RSS 数据收集"
    
    cd $SKILL_DIR
    
    # 创建归档目录
    mkdir -p $ARCHIVE_DIR
    
    # 运行 RSS + Twitter + GitHub 抓取
    python3 scripts/run-pipeline.py \
        --defaults config/defaults \
        --config $CONFIG_DIR \
        --hours 24 \
        --freshness pd \
        --archive-dir $ARCHIVE_DIR \
        --output $RSS_OUTPUT \
        --verbose \
        --force
    
    if [ $? -eq 0 ]; then
        log "✅ RSS 数据收集成功"
        if [ -f $RSS_OUTPUT ]; then
            ARTICLES=$(python3 -c "import json; data=json.load(open('$RSS_OUTPUT')); print(len(data.get('articles', [])))" 2>/dev/null || echo "0")
            log "📈 收集文章数: $ARTICLES"
        fi
    else
        log "⚠️ RSS 数据收集部分失败，继续其他任务..."
    fi
}

# ============================================
# 2. YouTube 频道监控（Supadata API）
# ============================================
fetch_youtube() {
    log_section "🎬 YouTube 频道监控"
    
    cd $WORKSPACE
    
    # 检查配置文件
    if [ ! -f $CONFIG_DIR/supadata-config.json ]; then
        log "⚠️ Supadata 配置文件不存在，跳过 YouTube 监控"
        return
    fi
    
    # 运行 YouTube 监控脚本
    if [ -f $SCRIPTS_DIR/fetch-youtube.py ]; then
        python3 $SCRIPTS_DIR/fetch-youtube.py \
            --config $CONFIG_DIR/supadata-config.json \
            --channels $CONFIG_DIR/youtube-channels.json \
            --hours 24 \
            --output $YOUTUBE_OUTPUT
        
        if [ $? -eq 0 ]; then
            log "✅ YouTube 监控成功"
        else
            log "⚠️ YouTube 监控失败，继续其他任务..."
        fi
    else
        log "⚠️ YouTube 监控脚本不存在，跳过"
    fi
}

# ============================================
# 3. 合并数据源
# ============================================
merge_sources() {
    log_section "🔄 合并数据源"
    
    cd $WORKSPACE
    
    # 创建合并脚本（如果不存在）
    if [ ! -f $SCRIPTS_DIR/merge-daily-sources.py ]; then
        log "⚠️ 合并脚本不存在，跳过合并"
        # 直接使用 RSS 输出
        if [ -f $RSS_OUTPUT ]; then
            cp $RSS_OUTPUT $MERGED_OUTPUT
            log "✅ 使用 RSS 数据作为主要来源"
        fi
        return
    fi
    
    python3 $SCRIPTS_DIR/merge-daily-sources.py \
        --rss $RSS_OUTPUT \
        --youtube $YOUTUBE_OUTPUT \
        --output $MERGED_OUTPUT
    
    if [ $? -eq 0 ]; then
        log "✅ 数据合并成功"
    else
        log "⚠️ 数据合并失败，使用 RSS 数据"
        if [ -f $RSS_OUTPUT ]; then
            cp $RSS_OUTPUT $MERGED_OUTPUT
        fi
    fi
}

# ============================================
# 4. 生成中文摘要（GLM-4-Flash）
# ============================================
generate_summary() {
    log_section "📝 生成中文摘要"
    
    cd $WORKSPACE
    
    if [ ! -f $MERGED_OUTPUT ]; then
        log "❌ 没有数据可生成摘要"
        return 1
    fi
    
    # 使用 GLM-4-Flash 翻译为中文
    if [ -f $SCRIPTS_DIR/translate-digest.py ]; then
        log "🔄 调用 GLM-4-Flash 翻译..."
        python3 $SCRIPTS_DIR/translate-digest.py \
            $MERGED_OUTPUT \
            --output $SUMMARY_OUTPUT \
            --format markdown
        
        if [ $? -eq 0 ]; then
            log "✅ 中文摘要生成成功"
            log "📄 摘要文件: $SUMMARY_OUTPUT"
        else
            log "⚠️ 翻译失败，使用英文版"
            cp $MERGED_OUTPUT $SUMMARY_OUTPUT
        fi
    else
        log "⚠️ 翻译脚本不存在，使用原始数据"
        cp $MERGED_OUTPUT $SUMMARY_OUTPUT
    fi
}

# ============================================
# 5. 推送到飞书
# ============================================
push_to_feishu() {
    log_section "📤 推送到飞书"

    cd $WORKSPACE

    # 检查推送脚本
    if [ ! -f $SCRIPTS_DIR/send-feishu.py ]; then
        log "❌ 飞书推送脚本不存在"
        log "请创建 $SCRIPTS_DIR/send-feishu.py"
        return 1
    fi

    # 读取Webhook配置
    WEBHOOK_CONFIG=$CONFIG_DIR/feishu-webhook.json
    if [ ! -f $WEBHOOK_CONFIG ]; then
        log "⚠️ 飞书Webhook配置不存在"
        log "请创建 $WEBHOOK_CONFIG 并配置webhook_url"
        log "运行: cat $WEBHOOK_CONFIG 查看模板"
        return 1
    fi

    # 提取webhook URL
    WEBHOOK_URL=$(python3 -c "import json; print(json.load(open('$WEBHOOK_CONFIG')).get('webhook_url', ''))" 2>/dev/null)

    if [ -z "$WEBHOOK_URL" ] || [ "$WEBHOOK_URL" = "YOUR_WEBHOOK_URL_HERE" ]; then
        log "⚠️ Webhook URL未配置"
        log "请编辑 $WEBHOOK_CONFIG 设置webhook_url"
        return 1
    fi

    # 推送摘要或原始数据
    if [ -f $SUMMARY_OUTPUT ]; then
        log "📤 推送摘要数据..."
        python3 $SCRIPTS_DIR/send-feishu.py \
            $SUMMARY_OUTPUT \
            --type json \
            --webhook "$WEBHOOK_URL" \
            --format simple
    elif [ -f $MERGED_OUTPUT ]; then
        log "📤 推送合并数据..."
        python3 $SCRIPTS_DIR/send-feishu.py \
            $MERGED_OUTPUT \
            --type json \
            --webhook "$WEBHOOK_URL" \
            --format simple
    else
        log "❌ 没有数据可推送"
        return 1
    fi
    
    if [ $? -eq 0 ]; then
        log "✅ 飞书推送成功"
    else
        log "❌ 飞书推送失败"
        return 1
    fi
}

# ============================================
# 主流程
# ============================================
main() {
    log_section "🚀 每日科技新闻摘要 - $DATETIME"
    
    # 创建必要的目录
    mkdir -p $ARCHIVE_DIR
    mkdir -p $SCRIPTS_DIR
    
    # 执行各阶段
    fetch_rss
    fetch_youtube
    merge_sources
    generate_summary
    push_to_feishu
    
    log_section "✅ 任务完成 - $(date '+%Y-%m-%d %H:%M:%S')"
}

# 运行主流程
main
