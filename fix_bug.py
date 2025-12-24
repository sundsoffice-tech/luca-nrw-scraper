with open('scriptname.py', 'r', encoding='utf-8') as f:
    content = f. read()

old = 'and ActiveLearningEngine is not None:'
new = 'and globals().get("ActiveLearningEngine") is not None:'

content = content.replace(old, new)

with open('scriptname.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fix angewendet!')
