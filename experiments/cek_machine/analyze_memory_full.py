"""Recompute full-memory summaries and make a standalone comparison graph."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import median, quantiles
import sys

from benchmark_memory import write_json
from benchmark_memory_full import FAMILIES, SIZES, MEMORY_FIELDS, verify


def summarize(rows):
    summaries = []
    for family in FAMILIES:
        for size in SIZES:
            for mode in ('current', 'cek', 'control'):
                selected = [r for r in rows if (r['family'], r['size'], r['evaluator']) == (family, size, mode)]
                successful = [r for r in selected if r['status']=='ok']
                row = dict(family=family, size=size, evaluator=mode,
                           observations=len(selected), successful=len(successful), errors=len(selected)-len(successful))
                for field in MEMORY_FIELDS:
                    values = [r[field] for r in successful]
                    if values:
                        q1, _, q3 = quantiles(values, n=4, method='inclusive') if len(values)>1 else (values[0],)*3
                        stats = dict(median=median(values), q1=q1, q3=q3, iqr=q3-q1, min=min(values), max=max(values))
                    else:
                        stats = dict.fromkeys(('median','q1','q3','iqr','min','max'))
                    row.update({field.removesuffix('_bytes')+'_'+key+'_bytes': value for key,value in stats.items()})
                summaries.append(row)
    return summaries


def csv_rows(rows):
    return [{k: '' if v is None else str(v) for k,v in row.items()} for row in rows]


def verify_analysis(directory):
    validation = verify(directory)
    expected = summarize(json.loads((directory/'raw_samples.json').read_text()))
    if list(csv.DictReader((directory/'summary.csv').open())) != csv_rows(expected):
        raise ValueError('Saved summary differs from raw samples')
    meta = json.loads((directory/'analysis_metadata.json').read_text())
    for name,digest in meta['artifact_sha256'].items():
        if hashlib.sha256((directory/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Analysis artifact changed: '+name)
    return dict(**validation, summary_rows=len(expected), analysis='passed')


def generate(directory):
    validation = verify(directory)
    targets = ['summary.csv', 'peak_growth.png', 'peak_growth.svg', 'README.md', 'analysis_metadata.json']
    if any((directory/name).exists() for name in targets):
        raise FileExistsError('Analysis outputs already exist; verification is read-only')
    rows = json.loads((directory/'raw_samples.json').read_text())
    summaries = summarize(rows)
    with (directory/'summary.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(summaries)
    # Imported only for post-run plotting, never in measurement workers.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, family in zip(axes, FAMILIES):
        for mode,label,color in [('current','Current PGSN','#1f77b4'),('cek','Strict-CBV CEK','#2ca02c'),('control','No-evaluation control','#777777')]:
            selected = [r for r in summaries if r['family']==family and r['evaluator']==mode]
            ys = [r['peak_growth_median_bytes']/1024 for r in selected]
            lower = [max(0, r['peak_growth_median_bytes']-r['peak_growth_q1_bytes'])/1024 for r in selected]
            upper = [max(0, r['peak_growth_q3_bytes']-r['peak_growth_median_bytes'])/1024 for r in selected]
            ax.errorbar(SIZES, ys, yerr=[lower,upper], color=color, marker='o',
                        linestyle='--' if mode=='control' else '-', capsize=4, label=label)
        ax.set_title(family.capitalize())
        ax.set_xlabel('Input size n')
        ax.set_xticks(SIZES)
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.25)
    axes[0].set_ylabel('Peak traced-memory growth (KiB; 1 KiB = 1024 bytes)')
    axes[0].legend(fontsize=8)
    fig.suptitle('First-evaluation Python memory: medians of 10 fresh processes')
    fig.text(0.5,0.01,'Bars: interquartile range (may be zero). Not total process memory; controls not subtracted.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,0.05,1,0.92))
    fig.savefig(directory/'peak_growth.png',dpi=180)
    fig.savefig(directory/'peak_growth.svg')
    plt.close(fig)
    meta = json.loads((directory/'metadata.json').read_text())
    environments = sorted({(r['python'],r['platform']) for r in rows if r['status']=='ok'})
    lines = ['# Full cold traced-memory experiment', '',
             'This run measures traced live Python blocks, not total process memory, RSS, or cumulative allocation volume.', '',
             f"Source commit: `{meta['source_commit']}`. Clean implementation at launch; exact source and earlier-evidence hashes are in [metadata.json](metadata.json).", '',
             'Command: `'+ ' '.join(meta['command'])+'`.', '',
             'Worker environment: '+repr(environments)+'.', '',
             'Identity and Captured at n=10,100,200; 10 observations per evaluator/size (120), plus 10 separate controls per family/size (60).',
             'Each observation executes a fresh interpreter with a freshly built nameless term; Current/CEK order alternates by repetition.',
             'No evaluator warmups, timing measurements, RSS, or counter instrumentation. Automatic GC stays enabled, with one explicit collection before baseline.',
             'The unchanged pilot worker measures complete fully_eval(steps=10000) or complete CEK evaluate(), including initial-state creation and loop.',
             'Tracing starts before construction with one traceback frame. Input/expected/result are retained through the final measurement; correctness is checked afterward.', '',
             'Raw B (baseline), P (absolute peak), E (ending), P-B (peak growth), and E-B (end growth) are retained in bytes.',
             'Baseline includes prepared inputs; cold means first evaluator call, not a cold interpreter or cold OS cache.', '',
             '| Input | n | Current median / IQR / min–max (bytes) | CEK median / IQR / min–max (bytes) | Control median (bytes) |',
             '|---|---:|---:|---:|---:|']
    for family in FAMILIES:
        for size in SIZES:
            selected = {r['evaluator']:r for r in summaries if r['family']==family and r['size']==size}
            values = [f"{selected[m]['peak_growth_median_bytes']:g} / {selected[m]['peak_growth_iqr_bytes']:g} / {selected[m]['peak_growth_min_bytes']:g}–{selected[m]['peak_growth_max_bytes']:g}" for m in ('current','cek')]
            lines.append(f"| {family} | {size} | {values[0]} | {values[1]} | {selected['control']['peak_growth_median_bytes']:g} |")
    lines += ['', 'All five memory metrics have median, inclusive q1/q3, IQR, min and max in [summary.csv](summary.csv). No outliers were removed.',
              'Correctness/coverage: `'+json.dumps(validation)+'`. Errors are separately retained in [errors.json](errors.json).', '',
              'Graph: [PNG](peak_growth.png), [SVG](peak_growth.svg). Blue = Current PGSN; green = CEK. Numeric input-size axis; IQR bars.', '',
              'These results describe two shared synthetic workloads on one machine/session. Tracing and measurement bookkeeping have overhead.',
              'Controls are shown separately and not subtracted. End growth alone is not evidence of a leak. Zero IQR does not prove zero uncertainty.',
              'Do not infer general evaluator memory superiority or asymptotic complexity from these six configurations.', '',
              'Verify raw data with benchmark_memory_full.py --verify-only --output this-directory.',
              'Verify summaries/artifact hashes with analyze_memory_full.py --verify-only --output this-directory.',
              'Earlier evidence preservation is checked against all hashes captured at launch.', '']
    with (directory/'README.md').open('x') as stream:
        stream.write('\n'.join(lines))
    write_json(directory/'analysis_metadata.json',dict(
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        command=[sys.executable,*sys.argv], python=sys.version, matplotlib=matplotlib.__version__,
        plotting_separate_from_measurements=True, summary_units='bytes', graph_units='KiB',
        quartiles='statistics.quantiles(n=4, method="inclusive")',
        artifact_sha256={name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in targets[:-1]}))
    return verify_analysis(directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    print(json.dumps(verify_analysis(args.output) if args.verify_only else generate(args.output)))


if __name__=='__main__':
    main()
