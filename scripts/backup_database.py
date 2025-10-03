#!/usr/bin/env python3
import shutil
import os
from datetime import datetime

# Backup database daily
source = '/app/data/course_access.db'
backup_dir = '/app/data/backups'
os.makedirs(backup_dir, exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
destination = f'{backup_dir}/course_access_{timestamp}.db'

shutil.copy2(source, destination)
print(f"Backup created: {destination}")

# Keep only last 30 backups
backups = sorted(os.listdir(backup_dir))
if len(backups) > 30:
    for old_backup in backups[:-30]:
        os.remove(os.path.join(backup_dir, old_backup))