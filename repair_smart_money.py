with open('src/core/orchestrator.py', 'r') as f:
    lines = f.readlines()

start = -1
end = -1
for i, line in enumerate(lines):
    if 'def fetch_layer_4_smart_money(self):' in line:
        start = i
    if start != -1 and 'self.payload["layer_4_smart_money"] = smart_money_data' in line and i > start + 20:
        end = i + 1
        break

if start != -1 and end != -1:
    new_func = [
        '    def fetch_layer_4_smart_money(self):\n',
        '        print(f"Fetching Layer 4: Smart Money (OSINT & QuiverQuant Fallback)...")\n',
        '        smart_money_data = {\n',
        '            "status": "Searching OSINT sources (HouseStockWatcher, SenateStockWatcher, QuiverQuant)",\n',
        '            "congress_trades": "N/A",\n',
        '            "insider_trades": "N/A"\n',
        '        }\n',
        '\n',
        '        if self.search_tools:\n',
        '            try:\n',
        '                clean_ticker = self.target_asset.split(\'-\')[0].split(\'=\')[0].split(\'.\')[0]\n',
        '                q_data = self.search_tools.search(f"site:quiverquant.com OR site:housestockwatcher.com OR site:senatestockwatcher.com {clean_ticker} latest stock trades")\n',
        '                smart_money_data["congress_trades_osint"] = q_data\n',
        '                b_data = self.search_tools.search("Warren Buffett Berkshire Hathaway latest 13F filings May 2026 portfolio changes")\n',
        '                smart_money_data["buffett_13f_summary"] = b_data\n',
        '                inst_data = self.search_tools.search(f"{clean_ticker} institutional ownership and dark pool activity latest news")\n',
        '                smart_money_data["institutional_flow_summary"] = inst_data\n',
        '            except: pass\n',
        '\n',
        '        if not self.quiver_key:\n',
        '            self.payload["layer_4_smart_money"] = smart_money_data\n',
        '            return\n'
    ]
    lines[start:end] = new_func
    with open('src/core/orchestrator.py', 'w') as f:
        f.writelines(lines)
    print("Function repaired.")
else:
    print(f"Could not find function bounds: start={start}, end={end}")
