import re

with open('src/core/orchestrator.py', 'r') as f:
    content = f.read()

# Fix corrupted try-except blocks
# 1. remove double pass/mess
content = re.sub(r'except: pass\n\s+pass', 'except: pass', content)
content = re.sub(r'except: pass\n\s+self\.payload', 'except: pass\n            self.payload', content)

with open('src/core/orchestrator.py', 'w') as f:
    f.write(content)
