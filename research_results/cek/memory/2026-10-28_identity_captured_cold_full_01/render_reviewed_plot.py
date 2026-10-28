"""Post-run visual correction: set shared y limits after plotting both panels.

Raw observations, summaries, original graph and committed analysis code are unchanged.
Run from the repository root using the separate plotting Python environment.
"""
from pathlib import Path
import hashlib
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
sys.path.insert(0, str(ROOT/'experiments/cek_machine'))
from analyze_memory_full import summarize, verify_analysis

verify_analysis(RUN)
outputs = ['peak_growth_reviewed.png','peak_growth_reviewed.svg',
           'README_initial.md','analysis_metadata_initial.json','plot_review.json']
if any((RUN/name).exists() for name in outputs):
    raise FileExistsError('Reviewed plot outputs already exist')
rows=summarize(json.loads((RUN/'raw_samples.json').read_text()))
fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
for ax,family in zip(axes,('identity','captured')):
    for mode,label,color in [('current','Current PGSN','#1f77b4'),('cek','Strict-CBV CEK','#2ca02c'),('control','No-evaluation control','#777777')]:
        selected=[r for r in rows if r['family']==family and r['evaluator']==mode]
        xs=[r['size'] for r in selected]
        ys=[r['peak_growth_median_bytes']/1024 for r in selected]
        low=[(r['peak_growth_median_bytes']-r['peak_growth_q1_bytes'])/1024 for r in selected]
        high=[(r['peak_growth_q3_bytes']-r['peak_growth_median_bytes'])/1024 for r in selected]
        ax.errorbar(xs,ys,yerr=[low,high],color=color,marker='o',capsize=4,
                    linestyle='--' if mode=='control' else '-',label=label)
    ax.set_title(family.capitalize())
    ax.set_xticks([10,100,200])
    ax.set_xlabel('Input size n')
    ax.grid(alpha=.25)
# Crucially set limits after all data are added to both shared axes.
top=max(r['peak_growth_q3_bytes'] for r in rows)/1024*1.12
for ax in axes:
    ax.set_ylim(0,top)
axes[0].set_ylabel('Peak traced-memory growth (KiB)')
axes[0].legend(fontsize=8)
fig.suptitle('First-evaluation Python memory: medians of 10 fresh processes',fontsize=13)
fig.text(.5,.02,'Bars: IQR (zero here). 1 KiB = 1024 bytes. Not total process memory; controls not subtracted.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.07,1,.94))
fig.savefig(RUN/'peak_growth_reviewed.png',dpi=180)
fig.savefig(RUN/'peak_growth_reviewed.svg')
plt.close(fig)
for old,backup in [('README.md','README_initial.md'),('analysis_metadata.json','analysis_metadata_initial.json')]:
    with (RUN/backup).open('xb') as stream:
        stream.write((RUN/old).read_bytes())
report=(RUN/'README.md').read_text().replace('[PNG](peak_growth.png), [SVG](peak_growth.svg)',
                                         '[reviewed PNG](peak_growth_reviewed.png), [reviewed SVG](peak_growth_reviewed.svg)')
report+='''\n## Plot review and observations

Visual inspection caught a shared-axis limit in the first rendering that clipped
Captured CEK n=200. The reviewed plots set the common upper limit after adding
both panels, so all points are visible. The initial PNG/SVG, report, and analysis
metadata are retained alongside the reviewed files. Raw data and summaries were
not changed. The retained render_reviewed_plot.py reproduces this correction.

Peak-growth IQR is zero in all 18 evaluator/control conditions; all ten observed
values in each condition are identical. This reproducibility in byte counts does
not remove uncertainty about tracing coverage or broader workloads. Current
Identity peak growth is unchanged between n=100 and n=200; CEK peak growth rises
over the tested range. The cause of this pattern was not isolated and it is not
a proof of complexity or general memory superiority. The control peak growth is
176 bytes for every configuration; it is recorded separately, not subtracted.

Post-run Matplotlib emitted font-cache permission warnings in the sandbox. The
plots were successfully generated and visually reviewed; this did not occur in
measurement workers or affect the raw measurements.
'''
(RUN/'README.md').write_text(report)
review=dict(reason='shared axis in initial rendering clipped largest Captured point',
            command=[sys.executable,'-B',str(Path(__file__).relative_to(ROOT))],
            matplotlib=matplotlib.__version__,python=sys.version,
            raw_data_unchanged=True,summary_unchanged=True,
            y_limits_kib=[0,top],all_values_visible=True)
with (RUN/'plot_review.json').open('x') as stream:json.dump(review,stream,indent=2)
meta=json.loads((RUN/'analysis_metadata.json').read_text())
meta['visual_review']=review
for name in ['README.md',*outputs,'render_reviewed_plot.py']:
    meta['artifact_sha256'][name]=hashlib.sha256((RUN/name).read_bytes()).hexdigest()
# Self-reference is intentionally excluded: analysis_metadata.json hashes artifacts.
(RUN/'analysis_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(verify_analysis(RUN)))
