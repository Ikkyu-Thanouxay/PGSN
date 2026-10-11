"""Summarize saved validation samples; OLS fits use per-size medians in ms."""
import csv
from pathlib import Path
from statistics import mean
import sys


def analyze(path):
    rows = list(csv.DictReader(Path(path).open()))
    successful = [row for row in rows if row['status'] == 'ok']
    print('| n | Current median | mean | SD | IQR | CEK median | mean | SD | IQR |')
    print('|---:|' + '---:|' * 8)
    for row in successful:
        values = [row[f'{ev}_{stat}'] for ev in ('current', 'cek')
                  for stat in ('ms', 'mean_ms', 'stdev_ms', 'iqr_ms')]
        print('| ' + row['size'] + ' | ' + ' | '.join(f'{float(v):.6f}' for v in values) + ' |')
    for ev in ('current', 'cek'):
        xs = [int(row['size']) for row in successful]
        ys = [float(row[f'{ev}_ms']) for row in successful]
        xm, ym = mean(xs), mean(ys)
        a = sum((x-xm)*(y-ym) for x,y in zip(xs,ys)) / sum((x-xm)**2 for x in xs)
        b = ym-a*xm
        residuals = [y-(a*x+b) for x,y in zip(xs,ys)]
        r2 = 1-sum(r*r for r in residuals)/sum((y-ym)**2 for y in ys)
        print(f'\n{ev}: slope={a:.9f} ms/n; intercept={b:.9f} ms; R²={r2:.9f}')
        print('Residuals (n: ms): ' + ', '.join(f'{x}: {r:+.6f}' for x,r in zip(xs,residuals)))
        print(f'Max absolute residual: {max(map(abs,residuals)):.6f} ms')
    old = {10: (.847,.226), 20:(1.614,.429), 50:(3.958,1.028),
           100:(7.957,2.076), 150:(11.824,3.126)}
    print('\nOld comparison: n, Current change %, CEK change %')
    for row in successful:
        n = int(row['size'])
        if n in old:
            print(n, *(f'{100*(float(row[f"{ev}_ms"])/previous-1):+.2f}%'
                       for ev, previous in zip(('current','cek'),old[n])))
    for row in rows:
        if row['status'] != 'ok':
            print('Preparation/evaluation failure:', row['size'], row['status'])


if __name__ == '__main__':
    analyze(sys.argv[1])
