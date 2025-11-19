#!/usr/bin/env python3
"""
Campaign Daily Notification - إشعار يومي عن الحملة
"""

import yaml
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

CAMPAIGNS_DIR = Path.home() / "Campaigns"

# للتحقق إذا كان يعمل من venv
SCRIPT_DIR = Path(__file__).parent if '__file__' in globals() else Path.cwd()

def find_active_campaign():
    """البحث عن الحملة النشطة"""
    if not CAMPAIGNS_DIR.exists():
        return None
    
    today = datetime.now().date()
    
    for folder in CAMPAIGNS_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith("_"):
            continue
        
        campaign_file = folder / "campaign.md"
        if not campaign_file.exists():
            continue
        
        try:
            content = campaign_file.read_text()
            if content.startswith("---"):
                yaml_end = content.find("---", 3)
                yaml_content = content[3:yaml_end]
                data = yaml.safe_load(yaml_content)
                
                status = data.get('status', 'active')
                
                if status in ['active', 'rest']:
                    start_date = datetime.strptime(data['start'], '%Y-%m-%d').date()
                    end_date = datetime.strptime(data['end'], '%Y-%m-%d').date()
                    
                    recovery_end_str = data.get('recovery_end', '').strip()
                    if recovery_end_str:
                        recovery_end = datetime.strptime(recovery_end_str, '%Y-%m-%d').date()
                    else:
                        recovery_end = end_date + timedelta(days=14)
                    
                    if start_date <= today <= recovery_end:
                        # حساب الـmilestones
                        milestones_total = content.count("- [ ]") + content.count("- [x]") + content.count("- [-]")
                        milestones_done = content.count("- [x]")
                        
                        return {
                            'data': data,
                            'file': campaign_file,
                            'end_date': end_date,
                            'recovery_end': recovery_end,
                            'milestones_total': milestones_total,
                            'milestones_done': milestones_done
                        }
        except:
            continue
    
    return None

def send_notification(title, message):
    """إرسال notification"""
    subprocess.run(['notify-send', '-u', 'normal', '-t', '10000', title, message])

def main():
    campaign = find_active_campaign()
    
    if not campaign:
        return
    
    data = campaign['data']
    today = datetime.now().date()
    end_date = campaign['end_date']
    recovery_end = campaign['recovery_end']
    
    if today <= end_date:
        # في الحملة - عرض معلومات الحملة
        days_left = (end_date - today).days
        week = data.get('current_week', 1)
        
        title = f"📊 Campaign: {data['name']}"
        message = (
            f"Week {week}/6 • {days_left} days left\n"
            f"✓ {campaign['milestones_done']}/{campaign['milestones_total']} milestones completed"
        )
        
        send_notification(title, message)
    else:
        # في الاستشفاء - عرض معلومات الاستشفاء
        days_left = (recovery_end - today).days
        
        title = "🌴 Recovery Period"
        message = (
            f"Ends: {recovery_end.strftime('%B %d, %Y')} ({days_left} days)\n"
            f"Rest well, you deserve it!"
        )
        
        send_notification(title, message)

if __name__ == "__main__":
    main()
