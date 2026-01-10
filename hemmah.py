#!/usr/bin/env python3
"""
Hemmah Campaign Manager - Campaign Management System
"""

import sys
import os
import subprocess
import random
from pathlib import Path
from datetime import datetime, timedelta

# ═══════════════════════════════════════
# Language Settings
# ═══════════════════════════════════════

KEYS = {
    'number': 'number',
    'name': 'name',
    'description': 'description',
    'start': 'start',
    'end': 'end',
    'recovery_end': 'recovery-end',
    'milestones': 'milestones',
    'status': 'status',
    'rate': 'rate',
    'links': 'links&drafts'
}

# ═══════════════════════════════════════
# File Settings
# ═══════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent

CAMPAIGNS_FILE = Path.home() / "Documents/Hemmah/campaigns.md"
WIKI_FILE = SCRIPT_DIR / "wiki.pdf"
WIKI_VIEWER = "zathura"
MOTIVATE_FILE = SCRIPT_DIR / "quotes.md"
YOURSELF_FILE = SCRIPT_DIR / "yourself.md"
YOURSELF_VIEWER = "less"  # less, cat, nvim
EDITOR = os.environ.get('EDITOR', 'nvim')

# ═══════════════════════════════════════
# Custom Parser - File Reading
# ═══════════════════════════════════════

def remove_comment(line):
    """Remove comments from line (everything after #)"""
    if '#' in line:
        return line.split('#')[0]
    return line

def parse_campaigns_file():
    """Read campaigns file"""
    if not CAMPAIGNS_FILE.exists():
        return []

    content = CAMPAIGNS_FILE.read_text()
    campaigns = []

    # Split by ---
    blocks = content.split('---\n')

    for block in blocks:
        block = block.strip()
        if not block or '###TEMPLATE###' in block:
            continue

        campaign = {}
        current_key = None
        current_list = []

        for line in block.split('\n'):
            # Remove comments first
            line = remove_comment(line)
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Check if line contains :
            if ':' in line and not line_stripped.startswith('-'):
                # Save previous list if exists
                if current_key and current_list:
                    campaign[current_key] = current_list
                    current_list = []

                # Read key and value
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                current_key = key

                # If value is empty, we expect a list
                if not value:
                    current_list = []
                else:
                    campaign[key] = value
                    current_key = None

            # List item (preserve line with tabs)
            elif line_stripped.startswith('-') and current_key:
                current_list.append(line.rstrip())

        # Save last list
        if current_key and current_list:
            campaign[current_key] = current_list

        # Add campaign if it contains a number
        if KEYS['number'] in campaign:
            campaigns.append(campaign)

    return campaigns

# ═══════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════

def count_indentation_level(line):
    """Calculate indentation level (tabs or spaces)
    - Each tab = one level
    - Each 4 spaces = one level (or less)
    """
    indent = 0
    i = 0
    while i < len(line):
        if line[i] == '\t':
            indent += 1
            i += 1
        elif line[i] == ' ':
            # Count consecutive spaces
            spaces = 0
            while i < len(line) and line[i] == ' ':
                spaces += 1
                i += 1
            # Each 2-4 spaces = one level
            indent += max(1, spaces // 3)
        else:
            break
    return indent

def find_active_campaign():
    """Find active or recovery phase campaign"""
    campaigns = parse_campaigns_file()
    if not campaigns:
        return None

    today = datetime.now().date()

    for campaign in campaigns:
        try:
            start_str = campaign.get(KEYS['start'], '')
            end_str = campaign.get(KEYS['end'], '')

            if not start_str or not end_str:
                continue

            start = datetime.strptime(start_str, '%Y-%m-%d').date()
            end = datetime.strptime(end_str, '%Y-%m-%d').date()

            # Calculate recovery end date
            recovery_end_str = campaign.get(KEYS['recovery_end'], '').strip()
            if recovery_end_str:
                recovery_end = datetime.strptime(recovery_end_str, '%Y-%m-%d').date()
            else:
                recovery_end = None

            # Check status
            if start <= today <= end:
                # Campaign is active
                return {
                    'data': campaign,
                    'start': start,
                    'end': end,
                    'recovery_end': recovery_end,
                    'phase': 'active'
                }
            elif today > end:
                # After campaign end
                if recovery_end is None:
                    # No recovery date set
                    return {
                        'data': campaign,
                        'start': start,
                        'end': end,
                        'recovery_end': None,
                        'phase': 'no_recovery_date'
                    }
                elif today <= recovery_end:
                    # In recovery period
                    return {
                        'data': campaign,
                        'start': start,
                        'end': end,
                        'recovery_end': recovery_end,
                        'phase': 'recovery'
                    }
                # else: recovery period ended - continue to next campaign
        except:
            continue

    return None

def calculate_week(start, today):
    """Calculate current week"""
    days_passed = (today - start).days
    week = (days_passed // 7) + 1
    return min(week, 6)

def get_current_milestone(campaign_data):
    """Get current milestone with subtasks"""
    milestones = campaign_data.get(KEYS['milestones'], [])

    for i, milestone in enumerate(milestones):
        # Remove comments
        milestone_clean = remove_comment(milestone)
        milestone_stripped = milestone_clean.strip()

        if not milestone_stripped or not milestone_stripped.startswith('- ['):
            continue

        # Calculate indentation level
        indent_level = count_indentation_level(milestone)

        # main task = level 1 (one tab or 3-4 spaces)
        if indent_level == 1:
            if '[ ]' in milestone_stripped:
                # Found pending main task
                text = milestone_stripped.split('[ ]', 1)[1].strip()

                # Look for pending subtask below it
                for j in range(i + 1, len(milestones)):
                    sub_milestone = milestones[j]
                    sub_clean = remove_comment(sub_milestone)
                    sub_stripped = sub_clean.strip()
                    sub_indent = count_indentation_level(sub_milestone)

                    # If we found another main task (level 1), stop
                    if sub_indent == 1 and sub_stripped.startswith('- ['):
                        break

                    # If we found pending subtask (level > 1), return it
                    if sub_indent > 1 and sub_stripped.startswith('- [') and '[ ]' in sub_stripped:
                        sub_text = sub_stripped.split('[ ]', 1)[1].strip()
                        return i + 1, text, sub_text, len(milestones)

                # No pending subtasks, return main task only
                return i + 1, text, None, len(milestones)

    # Nothing pending
    return None, None, None, len(milestones)

def count_completed_milestones(campaign_data):
    """Count completed milestones (main tasks only - level 1)"""
    milestones = campaign_data.get(KEYS['milestones'], [])
    completed = 0
    total = 0

    for milestone in milestones:
        # Remove comments
        milestone_clean = remove_comment(milestone)
        milestone_stripped = milestone_clean.strip()

        # Skip empty lines
        if not milestone_stripped:
            continue

        # Calculate indentation level
        indent_level = count_indentation_level(milestone)

        # main task = level 1 only
        if indent_level == 1 and milestone_stripped.startswith('- ['):
            total += 1
            if '[x]' in milestone_stripped or '[X]' in milestone_stripped:
                completed += 1

    return completed, total

# ═══════════════════════════════════════
# Commands
# ═══════════════════════════════════════

def cmd_help():
    """Display help"""
    print("""
الأوامر المتاحة:

  help          عرض هذه المساعدة
  info          عرض معلومات الحملة الحالية
  current       عرض المهمة الحالية والتقدم
  edit          تعديل ملف الحملات
  wiki          فتح ملف الويكي
  motivate      مقولة تحفيزية عشوائية
  yourself      فتح ملف "عن نفسك"

الاستخدام:
  python3 hemmah.py <command>

مثال:
  python3 hemmah.py info
  python3 hemmah.py current
""")

def cmd_info():
    """Display current campaign information"""
    campaign = find_active_campaign()

    if not campaign:
        print("لا توجد حملة نشطة")
        print("أنشئ واحدة: python3 hemmah.py edit")
        return

    data = campaign['data']
    name = data.get(KEYS['name'], 'غير محدد')
    description = data.get(KEYS['description'], '')
    start = campaign['start']
    phase = campaign['phase']

    print()
    print(f"Name: {name}")
    print(f"Start date: {start.strftime('%d %B %Y')}")
    if description:
        print(f"Description: {description}")
    
    if phase == 'recovery':
        recovery_end = campaign['recovery_end']
        days_left = (recovery_end - datetime.now().date()).days
        print(f"\nأنت في فترة الاستشفاء")
        print(f"باقي {days_left} يوم (حتى {recovery_end.strftime('%d %B %Y')})")
    elif phase == 'no_recovery_date':
        print(f"\nالحملة انتهت - يرجى تحديد تاريخ الاستشفاء")
        print(f"استخدم: python3 hemmah.py edit")
    
    print()

def cmd_current():
    """Display current task and progress"""
    campaign = find_active_campaign()

    if not campaign:
        print("لا توجد حملة نشطة")
        print("أنشئ حملة جديدة: python3 hemmah.py edit")
        return

    phase = campaign['phase']
    
    # Handle post-campaign phases
    if phase == 'recovery':
        recovery_end = campaign['recovery_end']
        days_left = (recovery_end - datetime.now().date()).days
        print(f"أنت في فترة الاستشفاء - باقي {days_left} يوم")
        print(f"استرخي واستعد للحملة القادمة!")
        return
    
    if phase == 'no_recovery_date':
        print("الحملة انتهت - يرجى تحديد تاريخ الاستشفاء")
        print("   استخدم: python3 hemmah.py edit")
        print(f"   أضف سطر: {KEYS['recovery_end']}: YYYY-MM-DD")
        return

    # Campaign is active - show tasks
    data = campaign['data']
    completed, total = count_completed_milestones(data)
    milestone_num, parent_text, subtask_text, _ = get_current_milestone(data)

    if parent_text:
        if subtask_text:
            # We have parent and subtask
            print(f"[{completed}/{total}] {parent_text} → {subtask_text}")
        else:
            # We have parent only without pending subtasks
            print(f"[{completed}/{total}] {parent_text}")
    else:
        print(f"[{completed}/{total}] جميع المهام منجزة!")

def cmd_edit():
    """Open campaigns file for editing"""
    # Create file if it doesn't exist
    if not CAMPAIGNS_FILE.exists():
        CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        template = f"""---
{KEYS['number']}: 0
{KEYS['name']}: حملتي الأولى
{KEYS['description']}: 
{KEYS['start']}: {datetime.now().strftime('%Y-%m-%d')}
{KEYS['end']}: {(datetime.now() + timedelta(days=42)).strftime('%Y-%m-%d')}
{KEYS['recovery_end']}: 
{KEYS['milestones']}:
	- [ ] مهمة 1
	- [ ] مهمة 2
		- [ ] subtask 2.1
		- [ ] subtask 2.2
	- [ ] مهمة 3 # هذا تعليق - البرنامج يتجاهله
{KEYS['status']}: 
{KEYS['rate']}: 
{KEYS['links']}:
	- 
---

---
###TEMPLATE (tasks hirarchy uses tabs) ###
{KEYS['number']}: 
{KEYS['name']}: 
{KEYS['description']}: 
{KEYS['start']}:
{KEYS['end']}:
{KEYS['recovery_end']}:
{KEYS['milestones']}:
	- [x] مثال منجز
		- [x] subtask منجز
		- [ ] subtask معلق
	- [-] مثال ملغي # تعليق
	- [ ] مثال معلق
{KEYS['status']}: 
{KEYS['rate']}: 
{KEYS['links']}:
	-
---
"""
        CAMPAIGNS_FILE.write_text(template)
        print(f"تم إنشاء ملف جديد: {CAMPAIGNS_FILE}")

    # Open file in editor
    subprocess.run([EDITOR, str(CAMPAIGNS_FILE)])

def cmd_wiki():
    """Open wiki file"""
    if not WIKI_FILE.exists():
        print(f"الملف غير موجود: {WIKI_FILE}")
        print(f"عدّل المسار في الكود: WIKI_FILE")
        return

    try:
        subprocess.Popen([WIKI_VIEWER, str(WIKI_FILE)], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        print(f"فتح الويكي في {WIKI_VIEWER}")
    except FileNotFoundError:
        print(f"البرنامج غير موجود: {WIKI_VIEWER}")
        print(f"عدّل في الكود: WIKI_VIEWER")

def cmd_motivate():
    """Random motivational quote"""
    if not MOTIVATE_FILE.exists():
        print(f"الملف غير موجود: {MOTIVATE_FILE}")
        print(f"أنشئ ملف {MOTIVATE_FILE} وضع كل مقولة في سطر")
        return

    lines = MOTIVATE_FILE.read_text().strip().split('\n')
    lines = [l.strip() for l in lines if l.strip()]

    if not lines:
        print("الملف فارغ!")
        return

    quote = random.choice(lines)
    print()
    print(f"  {quote}")
    print()

def cmd_yourself():
    """Open 'about yourself' file"""
    if not YOURSELF_FILE.exists():
        print(f"الملف غير موجود: {YOURSELF_FILE}")
        print(f"أنشئ ملف {YOURSELF_FILE}")
        return

    try:
        subprocess.run([YOURSELF_VIEWER, str(YOURSELF_FILE)])
    except FileNotFoundError:
        print(f"البرنامج غير موجود: {YOURSELF_VIEWER}")
        print(f"عدّل في الكود: YOURSELF_VIEWER")

# ═══════════════════════════════════════
# Main
# ═══════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    commands = {
        'help': cmd_help,
        'info': cmd_info,
        'current': cmd_current,
        'edit': cmd_edit,
        'wiki': cmd_wiki,
        'motivate': cmd_motivate,
        'yourself': cmd_yourself,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"أمر غير معروف: {command}")
        print()
        cmd_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
