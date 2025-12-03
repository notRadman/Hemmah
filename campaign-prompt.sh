#!/bin/bash
# Campaign Prompt - عرض حالة الحملة في الـprompt
# أسرع من Python - يُنفذ مع كل command

# ═══════════════════════════════════════
# إعدادات
# ═══════════════════════════════════════

CAMPAIGNS_FILE="$HOME/Documents/campaigno/campaigns.md"

# مفاتيح اللغة
KEY_NUMBER="number"
KEY_START="start"
KEY_END="end"
KEY_RECOVERY="recovery-end"

# ═══════════════════════════════════════
# الكود
# ═══════════════════════════════════════

# التحقق من وجود الملف
if [ ! -f "$CAMPAIGNS_FILE" ]; then
    exit 0
fi

TODAY=$(date +%s)

# قراءة الحملات
while IFS= read -r line; do
    # تخطي الـtemplate
    if [[ "$line" == *"###TEMPLATE###"* ]]; then
        break
    fi
    
    # قراءة الحقول
    if [[ "$line" =~ ^$KEY_NUMBER:\ *(.+)$ ]]; then
        NUMBER="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^$KEY_START:\ *([0-9]{4}-[0-9]{2}-[0-9]{2})$ ]]; then
        START="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^$KEY_END:\ *([0-9]{4}-[0-9]{2}-[0-9]{2})$ ]]; then
        END="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^$KEY_RECOVERY:\ *([0-9]{4}-[0-9]{2}-[0-9]{2})$ ]]; then
        RECOVERY_END="${BASH_REMATCH[1]}"
    fi
    
    # عند نهاية block (---)
    if [[ "$line" == "---" ]] && [ -n "$NUMBER" ] && [ -n "$START" ] && [ -n "$END" ]; then
        # حساب recovery_end إذا لم يكن محدداً
        if [ -z "$RECOVERY_END" ]; then
            END_EPOCH=$(date -d "$END" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$END" +%s 2>/dev/null)
            RECOVERY_END_EPOCH=$((END_EPOCH + 14 * 86400))
        else
            RECOVERY_END_EPOCH=$(date -d "$RECOVERY_END" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$RECOVERY_END" +%s 2>/dev/null)
        fi
        
        START_EPOCH=$(date -d "$START" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$START" +%s 2>/dev/null)
        END_EPOCH=$(date -d "$END" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$END" +%s 2>/dev/null)
        
        # التحقق إذا كانت الحملة نشطة
        if [ $TODAY -ge $START_EPOCH ] && [ $TODAY -le $RECOVERY_END_EPOCH ]; then
            # حساب الأسبوع
            DAYS_PASSED=$(( (TODAY - START_EPOCH) / 86400 ))
            WEEK=$(( DAYS_PASSED / 7 + 1 ))
            [ $WEEK -gt 6 ] && WEEK=6
            
            if [ $TODAY -le $END_EPOCH ]; then
                # في الحملة
                DAYS_LEFT=$(( (END_EPOCH - TODAY) / 86400 ))
                echo -n " [C${NUMBER}•W${WEEK}•${DAYS_LEFT}d]"
            else
                # في الاستشفاء
                DAYS_TO_END=$(( (RECOVERY_END_EPOCH - TODAY) / 86400 ))
                
                if [ $DAYS_TO_END -le 2 ]; then
                    # قبل يومين من النهاية
                    NEXT_NUMBER=$((NUMBER + 1))
                    echo -n " [Plan C${NEXT_NUMBER}→${DAYS_TO_END}d]"
                else
                    # استشفاء عادي
                    RECOVERY_DATE=$(date -d "@$RECOVERY_END_EPOCH" +"%b %d" 2>/dev/null || date -j -f "%s" "$RECOVERY_END_EPOCH" +"%b %d" 2>/dev/null)
                    echo -n " [R→${RECOVERY_DATE}]"
                fi
            fi
            
            exit 0
        fi
        
        # إعادة تعيين المتغيرات للحملة التالية
        NUMBER=""
        START=""
        END=""
        RECOVERY_END=""
    fi
done < "$CAMPAIGNS_FILE"
