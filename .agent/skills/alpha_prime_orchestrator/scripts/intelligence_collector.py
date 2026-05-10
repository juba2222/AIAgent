import json
import os
from alpha_prime_executor import AlphaPrimeExecutor
from datetime import datetime

def collect_all_intelligence():
    print("="*60)
    print(f"🚀 البدء في تجميع قاعدة البيانات الاستخباراتية الشاملة - {datetime.now().strftime('%Y-%m-%d')}")
    print("="*60)

    # استخدام الذهب كأصل مرجعي لبدء التجميع الشامل
    executor = AlphaPrimeExecutor("XAU=F")
    context_json = executor.generate_context_json()

    # حفظ البيانات في ملف JSON (النسخة الموحدة + نسخة مؤرخة)
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)

    # 1. النسخة الموحدة (للاستخدام البرمجي)
    master_file = os.path.join(output_dir, "alpha_prime_intelligence_db.json")
    with open(master_file, "w", encoding="utf-8") as f:
        f.write(context_json)

    # 2. نسخة الختم الزمني (للمراجعة البشرية والتاريخية)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file = os.path.join(output_dir, f"intelligence_snapshot_{timestamp}.json")
    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(context_json)

    print("\n" + "="*60)
    print(f"✅ تم تجميع البيانات بنجاح!")
    print(f"📄 ملف الاستخدام: {master_file}")
    print(f"📁 نسخة الأرشيف: {archive_file}")
    print("="*60)

if __name__ == "__main__":
    collect_all_intelligence()
