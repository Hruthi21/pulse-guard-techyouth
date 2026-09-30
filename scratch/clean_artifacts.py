for fname in ['templates/diet.html', 'templates/emergency.html', 'templates/lifestyle.html']:
    with open(fname, 'r', encoding='utf-8') as f:
        c = f.read()
    if '`n' in c:
        c = c.replace('`n', ' ')
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(c)
        print('Cleaned', fname)
