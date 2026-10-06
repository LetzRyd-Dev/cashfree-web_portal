with open("src/data.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Replace week 30 -> 40
content = content.replace('weekNumber: 30,', 'weekNumber: 40,')
content = content.replace('weekNumber: 29,', 'weekNumber: 39,')
content = content.replace('weekNumber: 28,', 'weekNumber: 38,')

content = content.replace('2026-07-21', '2026-09-28')
content = content.replace('2026-07-27', '2026-10-04')
content = content.replace('2026-07-14', '2026-09-21')
content = content.replace('2026-07-20', '2026-09-27')
content = content.replace('2026-07-07', '2026-09-14')
content = content.replace('2026-07-13', '2026-09-20')

content = content.replace('-030-', '-040-')
content = content.replace('-029-', '-039-')
content = content.replace('-028-', '-038-')

with open("src/data.ts", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated src/data.ts dates and week numbers to Weeks 38, 39, 40.")
