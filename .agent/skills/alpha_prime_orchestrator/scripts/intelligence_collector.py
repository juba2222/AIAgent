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

    # حفظ البيانات في ملف JSON
    output_file = "alpha_prime_intelligence_db.json"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(context_json)

    print("\n" + "="*60)
    print(f"✅ تم تجميع البيانات بنجاح!")
    print(f"📄 الملف الناتج: {output_file}")
    print("="*60)

if __name__ == "__main__":
    collect_all_intelligence()
